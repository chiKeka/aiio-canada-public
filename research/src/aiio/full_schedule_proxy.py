"""Versioned timing correction; preserve allocation outside the observed window."""
from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from .planning_benchmark import _check_manifest, digest, quarter, quarter_label
from .proxy_treatment import FIELDS, _project_geography
from .schemas import ValidationError

CONTRACT = "data/model/full_schedule_proxy_comparison_contract_v0.2.json"
OLD_PROXY = "data/processed/ai_construction_proxy_alberta_v0.1.csv"
OLD_REPORT = "data/model-runs/ai_construction_proxy_alberta_v0.1.json"
PROJECTS = "data/processed/alberta_ai_projects.csv"
CSV_OUTPUT = "data/processed/ai_construction_proxy_alberta_v0.2.csv"
LEDGER_OUTPUT = "data/processed/ai_construction_project_allocations_alberta_v0.2.csv"
REPORT_OUTPUT = "data/model-runs/ai_construction_proxy_alberta_v0.2.json"
LEDGER_FIELDS = ["project_id", "geography_id", "quarter", "allocation_cad", "window_position", "evidence_status"]


def amount(value):
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValidationError("allocation requires a numeric amount") from exc
    if not number.is_finite() or number < 0:
        raise ValidationError("allocation requires finite nonnegative amounts")
    return number


def money(value):
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def full_schedule(cost, start_year, end_year):
    """Exact integer weights equivalent to v0.1's symmetric quadratic profile."""
    cost = amount(cost)
    if cost <= 0 or cost * 100 != (cost * 100).to_integral_value():
        raise ValidationError("project cost must be positive whole cents")
    first, last = quarter(f"{start_year}-Q1"), quarter(f"{end_year}-Q4")
    count = last - first + 1
    if not 1 <= count <= 400:
        raise ValidationError("invalid or excessive project schedule")
    weights = [count * count + (2 * i + 1) * (2 * count - 2 * i - 1) for i in range(count)]
    denominator, cents = sum(weights), int(cost * 100)
    allocated = [cents * w // denominator for w in weights]
    remaining = cents - sum(allocated)
    order = sorted(range(count), key=lambda i: (-(cents * weights[i] % denominator), i))
    for i in order[:remaining]:
        allocated[i] += 1
    return {quarter_label(first + i): Decimal(value) / 100 for i, value in enumerate(allocated)}


def load_contract(root):
    contract = json.loads((root / CONTRACT).read_text())
    if contract["contract_id"] != "AIIO_FULL_SCHEDULE_PROXY_COMPARISON_0_2" or any(contract["publication_boundary"].values()):
        raise ValidationError("unsupported or authorizing full-schedule contract")
    _check_manifest(root, contract["input_manifest"])
    old = json.loads((root / OLD_REPORT).read_text())
    _check_manifest(root, old["input_manifest"])
    _check_manifest(root, {OLD_PROXY: old["output_sha256"]})
    # This version changes timing only, never source selection or realization ratios.
    if contract["reconstruction"]["project_realization"] != old["assumptions"]["project_reported_cost_realization_share"] or contract["reconstruction"]["permit_realization"] != old["assumptions"]["permit_estimate_realization_share"]:
        raise ValidationError("timing-only correction cannot change realization assumptions")
    return contract, old


def _csv_text(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def reconstruct(projects, old_rows, settings):
    first, last = quarter(settings["window_start"]), quarter(settings["window_end"])
    expected = {(g, quarter_label(q)) for g in ("CMA_825", "CMA_835") for q in range(first, last + 1)}
    keys = [(r["geography_id"], r["quarter"]) for r in old_rows]
    if len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValidationError("v0.1 proxy must cover the exact locked window once")
    if len({r["project_id"] for r in projects}) != len(projects):
        raise ValidationError("duplicate project identifiers")
    project_cells = defaultdict(Decimal)
    active_cells = defaultdict(int)
    ledger, reconciliations = [], []
    for project in sorted(projects, key=lambda r: r["project_id"]):
        geography = _project_geography(project["municipality"])
        if project["ai_relevance"] != "core_data_centre" or project["stage"] != "Under Construction" or geography is None:
            continue
        if not all(project[k] for k in ("start_year", "end_year", "estimated_cost_cad")):
            continue
        schedule = full_schedule(project["estimated_cost_cad"], project["start_year"], project["end_year"])
        totals = {"before": Decimal(0), "inside": Decimal(0), "after": Decimal(0)}
        for period, value in schedule.items():
            q = quarter(period)
            position = "before" if q < first else "after" if q > last else "inside"
            totals[position] += value
            ledger.append({"project_id": project["project_id"], "geography_id": geography, "quarter": period,
                           "allocation_cad": money(value), "window_position": position,
                           "evidence_status": "assumed_schedule_allocation_not_observed_spend"})
            if position == "inside":
                project_cells[(geography, period)] += value
                active_cells[(geography, period)] += 1
        cost = amount(project["estimated_cost_cad"])
        if sum(totals.values()) != cost:
            raise ValidationError("full schedule fails cost conservation")
        reconciliations.append({"project_id": project["project_id"], "reported_cost_cad": money(cost),
                                "full_schedule_quarters": len(schedule),
                                **{f"{name}_window_cad": money(value) for name, value in totals.items()},
                                "reconciles_to_reported_cost": True})
    rows = []
    for old in sorted(old_rows, key=lambda r: (r["geography_id"], r["quarter"])):
        key = (old["geography_id"], old["quarter"])
        if active_cells[key] != int(old["active_costed_project_count"]):
            raise ValidationError("timing correction changed included project coverage")
        project_value, permit = project_cells[key], amount(old["permit_activity_proxy_cad"])
        row = {**old, "project_schedule_proxy_cad": money(project_value),
               "quality_flags": old["quality_flags"] + "|full_schedule_denominator|out_of_window_allocation_retained"}
        for case in ("low", "central", "high"):
            value = project_value * amount(settings["project_realization"][case]) + permit * amount(settings["permit_realization"][case])
            row[f"reconstructed_proxy_{case}_cad"] = money(value)
        rows.append(row)
    return rows, ledger, reconciliations


def build_full_schedule_proxy(root: Path, output_dir: Path | None = None):
    contract, old = load_contract(root)
    with (root / OLD_PROXY).open(newline="") as handle:
        old_rows = list(csv.DictReader(handle))
    with (root / PROJECTS).open(newline="") as handle:
        projects = list(csv.DictReader(handle))
    rows, ledger, reconciliations = reconstruct(projects, old_rows, contract["reconstruction"])
    if len(reconciliations) != old["costed_project_count"]:
        raise ValidationError("costed project count changed")
    csv_text, ledger_text = _csv_text(rows, FIELDS), _csv_text(ledger, LEDGER_FIELDS)
    import hashlib
    hashes = {CSV_OUTPUT: "sha256:" + hashlib.sha256(csv_text.encode()).hexdigest(),
              LEDGER_OUTPUT: "sha256:" + hashlib.sha256(ledger_text.encode()).hexdigest()}
    report = {
        "model_id": "AIIO_E2_RECONSTRUCTED_AI_CONSTRUCTION_PROXY_0_2", "status": "timing_corrected_research_proxy_not_validated",
        "predecessor_model_id": old["model_id"], "contract_sha256": digest(root / CONTRACT),
        "row_count": len(rows), "costed_project_count": len(reconciliations), "permit_candidate_count": old["permit_candidate_count"],
        "reconstruction": contract["reconstruction"], "project_reconciliation": reconciliations,
        "project_allocation_totals_cad": {position: money(sum((amount(r[f"{position}_window_cad"]) for r in reconciliations), Decimal(0))) for position in ("before", "inside", "after")},
        "output_manifest": hashes, "input_manifest": contract["input_manifest"],
        "implementation_manifest": {p: digest(root / p) for p in ("research/src/aiio/full_schedule_proxy.py", "research/src/aiio/proxy_treatment.py")},
        "publication_boundary": contract["publication_boundary"],
        "limitations": ["Allocation uses the current reported start/end years and an assumed within-year profile; no realized spending or historical publication availability is established.",
                        "Outside-window ledger rows preserve assumed allocation, not observations or approved forecasts.",
                        "Permit scope and linkage remain unreviewed; no draft exclusions or deduplication are applied.",
                        "The immutable v0.1 proxy and benchmark are not overwritten."],
    }
    if output_dir is not None:
        for path, content in ((CSV_OUTPUT, csv_text), (LEDGER_OUTPUT, ledger_text), (REPORT_OUTPUT, json.dumps(report, indent=2, sort_keys=True) + "\n")):
            target = output_dir / path
            if target.resolve() in {(root / name).resolve() for name in contract["input_manifest"]}:
                raise ValidationError("output would overwrite a frozen input")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    return report, rows, ledger
