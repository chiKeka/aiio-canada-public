"""Predeclared component ablations over the unchanged retrospective folds."""
from __future__ import annotations

import copy
import csv
import json
from decimal import Decimal
from pathlib import Path

from .full_schedule_proxy import CONTRACT, CSV_OUTPUT, LEDGER_OUTPUT, REPORT_OUTPUT, amount, load_contract, money
from .planning_benchmark import (
    CONTRACT as OLD_CONTRACT, OUTPUT as OLD_OUTPUT, _check_manifest, _load,
    _stable_numbers, digest, evaluate, metrics, quarter,
)
from .schemas import ValidationError

OUTPUT = "data/model-runs/full_schedule_proxy_comparison_v0.2.json"
ARMS = ("baseline_only", "project_only", "permit_only", "combined")


def component_series(original, proxy_rows, settings, arm):
    if arm not in ARMS:
        raise ValidationError("undeclared comparison arm")
    cells = {(r["geography_id"], quarter(r["quarter"])): r for r in proxy_rows}
    if len(cells) != len(proxy_rows):
        raise ValidationError("duplicate v0.2 market-quarter rows")
    result = copy.deepcopy(original)
    for (geography, _asset), series in result.items():
        for q, observation in series.items():
            cell = cells.get((geography, q))
            if cell is None:
                raise ValidationError("missing v0.2 market-quarter exposure")
            for case in ("low", "central", "high"):
                project = amount(cell["project_schedule_proxy_cad"]) * amount(settings["project_realization"][case])
                permit = amount(cell["permit_activity_proxy_cad"]) * amount(settings["permit_realization"][case])
                if arm == "combined":
                    value = project + permit
                    if money(value) != cell[f"reconstructed_proxy_{case}_cad"]:
                        raise ValidationError("combined exposure does not reconcile to components")
                else:
                    value = project if arm == "project_only" else permit if arm == "permit_only" else Decimal(0)
                observation[case] = float(money(value))
    return result


def _subgroups(rows):
    keys = sorted({(r["geography_id"], r["asset_class"]) for r in rows})
    return [{"geography_id": g, "asset_class": a, **metrics([r for r in rows if (r["geography_id"], r["asset_class"]) == (g, a)])} for g, a in keys]


def _same_baseline(rows, frozen):
    if len(rows) != len(frozen):
        raise ValidationError("comparison changed held-out row count")
    before = {(r["geography_id"], r["asset_class"], r["target_quarter"]): r for r in frozen}
    for row in rows:
        key = (row["geography_id"], row["asset_class"], row["target_quarter"])
        if key not in before:
            raise ValidationError("comparison changed held-out keys")
        prior = before[key]
        for field in ("information_cutoff", "training_end", "training_quarter_count", "forecast_origin"):
            if row[field] != prior[field]:
                raise ValidationError("comparison changed frozen folds")
        for field in ("actual_yoy_pp", "baseline_yoy_pp"):
            if abs(row[field] - prior[field]) > 1e-8:
                raise ValidationError("comparison changed baseline or outcome")


def run_full_schedule_comparison(root: Path, output: Path | None = None):
    contract, _ = load_contract(root)
    old_contract = json.loads((root / OLD_CONTRACT).read_text())
    if tuple(contract["arms"]) != ARMS:
        raise ValidationError("v0.2 requires all four predeclared arms")
    for field in ("scope", "design", "acceptance_criteria"):
        if contract[field] != old_contract[field]:
            raise ValidationError("timing comparison cannot change frozen benchmark settings")
    frozen = json.loads((root / OLD_OUTPUT).read_text())
    proxy_report = json.loads((root / REPORT_OUTPUT).read_text())
    if proxy_report["contract_sha256"] != digest(root / CONTRACT) or any(proxy_report["publication_boundary"].values()):
        raise ValidationError("v0.2 reconstruction contract mismatch or authorization")
    if set(proxy_report["output_manifest"]) != {CSV_OUTPUT, LEDGER_OUTPUT} or proxy_report["input_manifest"] != contract["input_manifest"] or proxy_report["reconstruction"] != contract["reconstruction"]:
        raise ValidationError("v0.2 reconstruction receipt has incomplete or changed lineage")
    _check_manifest(root, proxy_report["output_manifest"])
    _check_manifest(root, proxy_report["implementation_manifest"])
    with (root / CSV_OUTPUT).open(newline="") as handle:
        proxy_rows = list(csv.DictReader(handle))
    original = _load(root, old_contract)
    design, acceptance = contract["design"], contract["acceptance_criteria"]
    arms, sensitivity = {}, []
    for arm in ARMS:
        series = component_series(original, proxy_rows, contract["reconstruction"], arm)
        predictions = evaluate(series, design, design["primary_proxy_case"], design["information_lag_quarters"])
        _same_baseline(predictions, frozen["predictions"])
        if arm == "baseline_only" and any(abs(r["proxy_yoy_pp"] - r["baseline_yoy_pp"]) > 1e-10 for r in predictions):
            raise ValidationError("zero-exposure arm must reproduce baseline")
        overall, subgroups = metrics(predictions), _subgroups(predictions)
        checks = {
            "minimum_test_quarters": len({r["target_quarter"] for r in predictions}) >= acceptance["minimum_test_quarters"],
            "primary_mae": overall["proxy"]["mae_pp"] <= acceptance["maximum_primary_mae_pp"],
            "improvement_over_baseline": overall["mae_improvement_fraction"] is not None and overall["mae_improvement_fraction"] >= acceptance["minimum_mae_improvement_fraction"],
            "subgroup_noninferiority": all(r["proxy"]["mae_pp"] <= r["baseline"]["mae_pp"] * acceptance["maximum_subgroup_mae_ratio_to_baseline"] for r in subgroups),
        }
        arms[arm] = {"role": "primary" if arm == "combined" else "reference" if arm == "baseline_only" else "diagnostic",
                     "metrics": overall, "subgroups": subgroups, "point_error_checks": checks, "predictions": predictions}
        if arm == "baseline_only":
            continue
        for case in design["sensitivity_proxy_cases"]:
            for lag in design["sensitivity_information_lags"]:
                item = {"arm": arm, "proxy_case": case, "information_lag_quarters": lag}
                try:
                    item.update(status="evaluated", metrics=metrics(evaluate(series, design, case, lag)))
                except ValidationError as exc:
                    if str(exc) != "insufficient training quarters for frozen benchmark":
                        raise
                    item.update(status="insufficient_data", reason=str(exc))
                sensitivity.append(item)
    combined = arms["combined"]["metrics"]["proxy"]["mae_pp"]
    prior = frozen["metrics"]["proxy"]["mae_pp"]
    report = {
        "run_id": "AIIO_FULL_SCHEDULE_PROXY_COMPARISON_0_2", "status": "comparison_complete_validation_withheld",
        "contract_sha256": digest(root / CONTRACT), "protocol_boundary": contract["protocol_boundary"],
        "design": design, "scope": contract["scope"], "selection_policy": contract["selection_policy"],
        "arms": arms, "sensitivity": sensitivity,
        "historical_comparison": {"frozen_v0_1_combined_mae_pp": prior, "v0_2_combined_mae_pp": combined,
                                  "mae_change_pp": combined - prior,
                                  "mae_improvement_fraction": 1 - combined / prior if prior else None,
                                  "interpretation": "Reconstruction/model difference on reused test quarters, not an AI effect or independent validation."},
        "coverage": frozen["coverage"], "project_reconciliation": proxy_report["project_reconciliation"],
        "unassessed_requirements": ["historical publication vintages", "independent scope and facility linkage review", "individual permit/work-package sensitivity", "predictive intervals", "independent planning review", "fresh prospective validation"],
        "publication_boundary": contract["publication_boundary"],
        "limitations": ["All arms reuse the same observed outcomes and fold definitions. Prior v0.1 results were known before this follow-up protocol.",
                        "Source ablation is a diagnostic comparison, not a measured contribution to construction costs.",
                        "Current dollar components occupy different markets. Project-only and permit-only results must not be added as independent effects.",
                        "Existing annual schedule and realization assumptions remain unvalidated. Full-schedule arithmetic does not establish actual timing.",
                        "No arm is automatically selected or promoted, even if point-error thresholds pass."],
        "input_manifest": {**contract["input_manifest"], REPORT_OUTPUT: digest(root / REPORT_OUTPUT), **proxy_report["output_manifest"]},
        "implementation_manifest": {p: digest(root / p) for p in ("research/src/aiio/full_schedule_comparison.py", "research/src/aiio/full_schedule_proxy.py", "research/src/aiio/planning_benchmark.py")},
    }
    report = _stable_numbers(report)
    if output is not None:
        if output.resolve() in {(root / name).resolve() for name in report["input_manifest"]}:
            raise ValidationError("output would overwrite frozen input")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return report
