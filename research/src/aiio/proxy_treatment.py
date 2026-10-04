from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .schemas import ValidationError


MODEL_ID = "AIIO_E2_RECONSTRUCTED_AI_CONSTRUCTION_PROXY_0_1"
PROJECT_REALIZATION = {"low": 0.45, "central": 0.65, "high": 0.80}
PERMIT_REALIZATION = {"low": 0.35, "central": 0.60, "high": 0.85}
FIELDS = [
    "geography_id", "quarter", "period_start", "period_end",
    "active_costed_project_count", "active_uncosted_project_count",
    "explicit_data_centre_permit_count", "project_schedule_proxy_cad",
    "permit_activity_proxy_cad", "reconstructed_proxy_low_cad",
    "reconstructed_proxy_central_cad", "reconstructed_proxy_high_cad",
    "evidence_status", "quality_flags",
]


def build_reconstructed_treatment_proxy(
    root: Path,
    projects_path: Path,
    permits_path: Path,
    project_report_path: Path,
    permit_report_path: Path,
    output_csv_path: Path,
    output_json_path: Path,
) -> dict[str, Any]:
    projects = _csv(projects_path)
    permits = _csv(permits_path)
    project_report = _object(project_report_path)
    permit_report = _object(permit_report_path)
    if project_report.get("publication_boundary", {}).get("realized_construction_treatment_authorized") is not False:
        raise ValidationError("project ledger boundary must remain non-authorizing")
    if permit_report.get("publication_boundary", {}).get("realized_ai_construction_treatment_authorized") is not False:
        raise ValidationError("permit boundary must remain non-authorizing")

    periods = _quarters("2017-01-01", "2026-06-30")
    cells: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    project_ids: set[str] = set()
    uncosted_ids: set[str] = set()
    for row in projects:
        if row["ai_relevance"] != "core_data_centre" or row["stage"] != "Under Construction":
            continue
        geography_id = _project_geography(row["municipality"])
        if geography_id is None: continue
        if not row["start_year"] or not row["end_year"] or not row["estimated_cost_cad"]:
            uncosted_ids.add(row["project_id"])
            for quarter in periods:
                if row["start_year"] and quarter[:4] == row["start_year"]:
                    cells[(geography_id, quarter)]["uncosted"] += 1
            continue
        start_year, end_year = int(row["start_year"]), int(row["end_year"])
        active = [quarter for quarter in periods if start_year <= int(quarter[:4]) <= end_year]
        weights = _schedule_weights(len(active))
        cost = float(row["estimated_cost_cad"])
        project_ids.add(row["project_id"])
        for quarter, weight in zip(active, weights, strict=True):
            cell = cells[(geography_id, quarter)]
            cell["active"] += 1
            cell["project"] += cost * weight

    permit_ids: set[str] = set()
    for row in permits:
        if row["classification"] != "explicit_data_centre_reference" or "DEMOLITION" in row["work_type"].upper():
            continue
        if not row["reported_estimated_construction_value_cad"] or row["issue_year"] < "2017": continue
        quarter = _date_quarter(row["issue_date"])
        if quarter not in periods: continue
        permit_ids.add(row["permit_proxy_id"])
        cell = cells[("CMA_835", quarter)]
        cell["permits"] += 1
        cell["permit"] += float(row["reported_estimated_construction_value_cad"])

    output_rows: list[dict[str, str]] = []
    for geography_id in ("CMA_825", "CMA_835"):
        for quarter in periods:
            cell = cells[(geography_id, quarter)]
            project = cell["project"]; permit = cell["permit"]
            low = project * PROJECT_REALIZATION["low"] + permit * PERMIT_REALIZATION["low"]
            central = project * PROJECT_REALIZATION["central"] + permit * PERMIT_REALIZATION["central"]
            high = project * PROJECT_REALIZATION["high"] + permit * PERMIT_REALIZATION["high"]
            start, end = _boundaries(quarter)
            output_rows.append({
                "geography_id": geography_id, "quarter": quarter, "period_start": start, "period_end": end,
                "active_costed_project_count": str(int(cell["active"])), "active_uncosted_project_count": str(int(cell["uncosted"])),
                "explicit_data_centre_permit_count": str(int(cell["permits"])),
                "project_schedule_proxy_cad": _format(project), "permit_activity_proxy_cad": _format(permit),
                "reconstructed_proxy_low_cad": _format(low), "reconstructed_proxy_central_cad": _format(central), "reconstructed_proxy_high_cad": _format(high),
                "evidence_status": "reconstructed_non_authorizing_proxy",
                "quality_flags": "estimated_cost_s_curve|assumed_realization_ratio|permit_project_overlap_not_linked|not_realized_spend_or_labour_hours",
            })
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(output_rows)
    report = {
        "schema_version": "1.0.0", "model_id": MODEL_ID, "status": "reconstructed_proxy_only",
        "row_count": len(output_rows), "quarter_count": len(periods), "geography_count": 2,
        "costed_project_count": len(project_ids), "uncosted_under_construction_project_count": len(uncosted_ids), "permit_candidate_count": len(permit_ids),
        "assumptions": {"project_reported_cost_realization_share": PROJECT_REALIZATION, "permit_estimate_realization_share": PERMIT_REALIZATION, "project_timing_profile": "normalized symmetric construction S-curve over reported start/end years"},
        "input_manifest": {str(path.relative_to(root)): "sha256:" + _sha(path) for path in [projects_path, permits_path, project_report_path, permit_report_path]},
        "output_path": "data/processed/ai_construction_proxy_alberta_v0.1.csv", "output_sha256": "sha256:" + _sha(output_csv_path),
        "limitations": [
            "Reported project cost is allocated through an assumed schedule profile and is not observed expenditure.",
            "Permit value is an estimate of permitted work, not realized spend, and explicit data-centre text does not establish AI use.",
            "Permit and major-project records are not project-linked; their components remain separately reported to expose possible overlap.",
            "Under-construction projects without both cost and schedule remain activity counts and receive no imputed dollar dose.",
        ],
        "publication_boundary": {"proxy_exposure_authorized": True, "association_analysis_authorized": True, "realized_treatment_authorized": False, "causal_effect_authorized": False, "reason": "The reconstruction supports transparent proxy and sensitivity analysis only."},
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _schedule_weights(count: int) -> list[float]:
    raw = [0.25 + ((index + 0.5) / count) * (1 - (index + 0.5) / count) for index in range(count)]
    total = sum(raw); return [item / total for item in raw]


def _project_geography(value: str) -> str | None:
    names = {item.strip() for item in value.split("|")}
    if names & {"Calgary", "Rocky View County", "Chestermere", "Foothills No. 31"}: return "CMA_825"
    if names & {"Edmonton", "Sturgeon County", "Leduc County", "Parkland County"}: return "CMA_835"
    return None


def _quarters(start: str, end: str) -> list[str]:
    start_year = int(start[:4]); end_year = int(end[:4]); result = []
    for year in range(start_year, end_year + 1):
        for quarter in range(1, 5):
            key = f"{year}-Q{quarter}"
            if _boundaries(key)[0] >= start and _boundaries(key)[1] <= end: result.append(key)
    return result


def _boundaries(quarter: str) -> tuple[str, str]:
    year = int(quarter[:4]); q = int(quarter[-1]); month = 1 + (q - 1) * 3
    end_month = month + 2
    next_month = date(year + (end_month == 12), 1 if end_month == 12 else end_month + 1, 1)
    end_day = (next_month - date.resolution).day
    return f"{year}-{month:02d}-01", f"{year}-{end_month:02d}-{end_day:02d}"


def _date_quarter(value: str) -> str:
    return f"{value[:4]}-Q{(int(value[5:7]) - 1) // 3 + 1}"


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle: rows = list(csv.DictReader(handle))
    if not rows: raise ValidationError(f"proxy treatment input is empty: {path}")
    return rows


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValidationError(f"expected JSON object: {path}")
    return value


def _format(value: float) -> str: return f"{value:.2f}"
def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
