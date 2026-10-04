"""Retrospective, time-blocked Alberta planning diagnostics; never authorization."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

from .proxy_association import _inverse
from .schemas import ValidationError

CONTRACT = "data/model/alberta_quarterly_planning_benchmark_contract_v0.1.json"
OUTPUT = "data/model-runs/alberta_quarterly_planning_benchmark_v0.1.json"
PANEL = "data/processed/ai_attribution_empirical_covariate_panel_v0.1.csv"
PANEL_REPORT = "data/model-runs/ai_attribution_empirical_covariate_panel_v0.1.json"
PROXY_REPORT = "data/model-runs/ai_construction_proxy_alberta_v0.1.json"


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def quarter(value: str) -> int:
    if not re.fullmatch(r"\d{4}-Q[1-4]", value):
        raise ValidationError(f"invalid benchmark quarter: {value}")
    return int(value[:4]) * 4 + int(value[-1]) - 1


def quarter_label(value: int) -> str:
    return f"{value // 4}-Q{value % 4 + 1}"


def _check_manifest(root: Path, manifest: dict) -> None:
    for name, expected in manifest.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or digest(path) != expected:
            raise ValidationError(f"benchmark input missing or hash drift: {name}")


def _load(root: Path, contract: dict) -> dict:
    _check_manifest(root, contract["input_manifest"])
    receipt = json.loads((root / PANEL_REPORT).read_text())
    _check_manifest(root, receipt["input_manifest"])
    if digest(root / PANEL) != receipt["output_sha256"]:
        raise ValidationError("benchmark panel receipt mismatch")
    proxy = json.loads((root / PROXY_REPORT).read_text())
    _check_manifest(root, proxy["input_manifest"])
    _check_manifest(root, {proxy["output_path"]: proxy["output_sha256"]})
    scope = contract["scope"]
    series = defaultdict(dict)
    with (root / PANEL).open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["geography_id"] not in scope["geographies"] or row["asset_class"] not in scope["assets"]:
                continue
            key, q = (row["geography_id"], row["asset_class"]), quarter(row["quarter"])
            if q in series[key]:
                raise ValidationError("duplicate market/asset/quarter")
            values = {"y": float(row[scope["outcome"]]) if row[scope["outcome"]] else None}
            for case in ("low", "central", "high"):
                values[case] = float(row[f"reconstructed_ai_construction_proxy_{case}_cad"])
                if not math.isfinite(values[case]) or values[case] < 0:
                    raise ValidationError("invalid reconstructed proxy")
            if values["y"] is not None and not math.isfinite(values["y"]):
                raise ValidationError("nonfinite benchmark outcome")
            if not values["low"] <= values["central"] <= values["high"]:
                raise ValidationError("unordered proxy cases")
            series[key][q] = values
    expected = {(g, a) for g in scope["geographies"] for a in scope["assets"]}
    if set(series) != expected:
        raise ValidationError("missing benchmark market/asset series")
    periods = [set(rows) for rows in series.values()]
    if any(p != periods[0] for p in periods) or periods[0] != set(range(min(periods[0]), max(periods[0]) + 1)):
        raise ValidationError("benchmark panel must have common contiguous quarters")
    return dict(series)


def ridge_predict(x: list[list[float]], y: list[float], target: list[float], penalty: float) -> float:
    """Fit scaling on training rows only; constant exposure contributes zero."""
    means = [statistics.mean(col) for col in zip(*x)]
    scales = [statistics.pstdev(col) or 1.0 for col in zip(*x)]
    design = [[1.0, *[(v - m) / s for v, m, s in zip(row, means, scales)]] for row in x]
    k = len(design[0])
    gram = [[sum(row[i] * row[j] for row in design) + (penalty if i == j and i else 0) for j in range(k)] for i in range(k)]
    rhs = [sum(row[i] * value for row, value in zip(design, y)) for i in range(k)]
    inverse = _inverse(gram)
    beta = [sum(inverse[i][j] * rhs[j] for j in range(k)) for i in range(k)]
    prediction = beta[0] + sum(b * (v - m) / s for b, v, m, s in zip(beta[1:], target, means, scales))
    if not math.isfinite(prediction):
        raise ValidationError("nonfinite benchmark prediction")
    return prediction


def evaluate(series: dict, design: dict, case: str, lag: int) -> list[dict]:
    if lag < 2:
        raise ValidationError("benchmark requires at least two quarters of information lag")
    predictions = []
    for target in range(quarter(design["first_test_quarter"]), quarter(design["last_test_quarter"]) + 1):
        cutoff = target - lag
        for (geography, asset), rows in sorted(series.items()):
            def features(q):
                return [rows[q - lag]["y"], math.log1p(rows[q - lag][case] / 1e9)]

            train = [q for q in sorted(rows) if q <= cutoff and rows[q]["y"] is not None
                     and q - lag in rows and rows[q - lag]["y"] is not None]
            if len(train) < design["minimum_training_quarters"]:
                raise ValidationError("insufficient training quarters for frozen benchmark")
            if target not in rows or rows[target]["y"] is None or cutoff not in rows or rows[cutoff]["y"] is None:
                raise ValidationError("missing held-out outcome or lagged predictor")
            x, y = [features(q) for q in train], [rows[q]["y"] for q in train]
            forecast = features(target)
            penalty = design["ridge_penalty"]
            predictions.append({
                "geography_id": geography, "asset_class": asset, "target_quarter": quarter_label(target),
                "forecast_origin": quarter_label(target - 1),
                "information_cutoff": quarter_label(cutoff), "training_end": quarter_label(max(train)),
                "training_quarter_count": len(train), "actual_yoy_pp": rows[target]["y"],
                "baseline_yoy_pp": ridge_predict([row[:1] for row in x], y, forecast[:1], penalty),
                "proxy_yoy_pp": ridge_predict(x, y, forecast, penalty),
            })
    return predictions


def metrics(rows: list[dict]) -> dict:
    result = {}
    for model in ("baseline", "proxy"):
        # Equal weight for each market-quarter; repeated asset rows are averaged first.
        errors = defaultdict(list)
        for row in rows:
            errors[(row["geography_id"], row["target_quarter"])].append(row[f"{model}_yoy_pp"] - row["actual_yoy_pp"])
        result[model] = {
            "mae_pp": statistics.mean(statistics.mean(abs(e) for e in cell) for cell in errors.values()),
            "rmse_pp": math.sqrt(statistics.mean(statistics.mean(e * e for e in cell) for cell in errors.values())),
        }
    baseline = result["baseline"]["mae_pp"]
    result["mae_improvement_fraction"] = 1 - result["proxy"]["mae_pp"] / baseline if baseline else None
    return result


def _stable_numbers(value):
    """Retain practical precision without platform-specific last-bit receipts."""
    if isinstance(value, float):
        return round(value, 10)
    if isinstance(value, dict):
        return {key: _stable_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stable_numbers(item) for item in value]
    return value


def run_planning_benchmark(root: Path, output: Path | None = None) -> dict:
    contract = json.loads((root / CONTRACT).read_text())
    if contract["contract_id"] != "AIIO_ALBERTA_QUARTERLY_PLANNING_BENCHMARK_0_1":
        raise ValidationError("unsupported planning benchmark contract")
    if any(contract["publication_boundary"].values()):
        raise ValidationError("exploratory benchmark cannot authorize estimates")
    design, acceptance = contract["design"], contract["acceptance_criteria"]
    if design["information_lag_quarters"] < 2 or design["ridge_penalty"] <= 0 or design["minimum_training_quarters"] < 20:
        raise ValidationError("unsafe benchmark training design")
    series = _load(root, contract)
    primary = evaluate(series, design, design["primary_proxy_case"], design["information_lag_quarters"])
    overall = metrics(primary)
    subgroups = [{"geography_id": g, "asset_class": a, **metrics([r for r in primary if (r["geography_id"], r["asset_class"]) == (g, a)])} for g, a in sorted(series)]
    sensitivity = []
    for case in design["sensitivity_proxy_cases"]:
        for lag in design["sensitivity_information_lags"]:
            try:
                result = metrics(evaluate(series, design, case, lag))
                sensitivity.append({"case": case, "information_lag_quarters": lag, "status": "evaluated", **result})
            except ValidationError as exc:
                sensitivity.append({"case": case, "information_lag_quarters": lag, "status": "insufficient_data", "reason": str(exc)})
    proxy = json.loads((root / PROXY_REPORT).read_text())
    quarters = len({r["target_quarter"] for r in primary})
    checks = {
        "minimum_test_quarters": quarters >= acceptance["minimum_test_quarters"],
        "primary_mae": overall["proxy"]["mae_pp"] <= acceptance["maximum_primary_mae_pp"],
        "improvement_over_baseline": overall["mae_improvement_fraction"] is not None and overall["mae_improvement_fraction"] >= acceptance["minimum_mae_improvement_fraction"],
        "subgroup_noninferiority": all(s["proxy"]["mae_pp"] <= s["baseline"]["mae_pp"] * acceptance["maximum_subgroup_mae_ratio_to_baseline"] for s in subgroups),
    }
    report = {
        "run_id": "AIIO_ALBERTA_QUARTERLY_PLANNING_BENCHMARK_0_1",
        "status": "retrospective_benchmark_complete_validation_withheld",
        "contract_sha256": digest(root / CONTRACT), "design": design, "scope": contract["scope"],
        "coverage": {"asset_rows": len(primary), "held_out_quarters": quarters,
                     "distinct_outcome_series": len({tuple((q, row["y"]) for q, row in sorted(rows.items())) for rows in series.values()}),
                     "market_quarter_cells": len({(r["geography_id"], r["target_quarter"]) for r in primary}),
                     "costed_project_records": proxy["costed_project_count"], "permit_candidate_records": proxy["permit_candidate_count"],
                     "independently_linked_events": None,
                     "note": "Neither repeated asset rows, market-quarter cells nor source-record counts establish independent events."},
        "metrics": overall, "subgroups": subgroups, "sensitivity": sensitivity,
        "point_error_checks": checks, "unassessed_requirements": contract["unassessed_requirements"],
        "predictive_intervals": {"status": "withheld", "reason": "No frozen predictive interval implementation with sufficient prior out-of-sample calibration quarters; low/high exposure cases are not prediction intervals."},
        "predictions": primary,
        "limitations": [design["vintage_boundary"], "Two markets and correlated YoY outcomes do not provide independent treatment events.",
                        "Training-only preprocessing prevents fold leakage but cannot remove retrospective reconstruction or source-revision look-ahead.",
                        "Error thresholds are provisional research criteria; no metric automatically promotes a model.",
                        "Proxy minus baseline predictions are model differences, never an AI causal effect or additive project-cost increment."],
        "publication_boundary": contract["publication_boundary"],
        "input_manifest": contract["input_manifest"],
        "implementation_manifest": {p: digest(root / p) for p in ("research/src/aiio/planning_benchmark.py", "research/src/aiio/proxy_association.py", "research/tests/test_planning_benchmark.py")},
    }
    report = _stable_numbers(report)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return report
