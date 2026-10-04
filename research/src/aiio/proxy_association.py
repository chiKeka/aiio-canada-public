from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from .schemas import ValidationError


RUN_ID = "AIIO_E2_ALBERTA_PROXY_ASSOCIATION_0_1"
CASES = ("low", "central", "high")


def run_proxy_association(panel_path: Path, panel_report_path: Path, output_path: Path) -> dict[str, Any]:
    report = json.loads(panel_report_path.read_text(encoding="utf-8"))
    if report.get("output_sha256") != "sha256:" + hashlib.sha256(panel_path.read_bytes()).hexdigest():
        raise ValidationError("proxy association panel hash mismatch")
    with panel_path.open(encoding="utf-8", newline="") as handle: rows = list(csv.DictReader(handle))
    by_key = {(row["geography_id"], row["asset_class"], row["quarter"]): row for row in rows}
    pairs: list[dict[str, float | str]] = []
    for row in rows:
        if row["geography_id"] != "CMA_825" or not row["market_price_yoy_percent"]: continue
        peer = by_key.get(("CMA_835", row["asset_class"], row["quarter"]))
        if peer is None or not peer["market_price_yoy_percent"]: continue
        pairs.append({
            "asset": row["asset_class"], "quarter": row["quarter"],
            "outcome": float(row["market_price_yoy_percent"]) - float(peer["market_price_yoy_percent"]),
            "investment": (float(row["non_residential_building_investment_constant_cad"]) - float(peer["non_residential_building_investment_constant_cad"])) / 1_000_000_000,
            **{case: (float(row[f"reconstructed_ai_construction_proxy_{case}_cad"]) - float(peer[f"reconstructed_ai_construction_proxy_{case}_cad"])) / 1_000_000_000 for case in CASES},
        })
    if len(pairs) < 30: raise ValidationError("proxy association has insufficient paired Alberta observations")
    assets = sorted({str(row["asset"]) for row in pairs})
    results = []
    for case in CASES:
        x = [[1.0, float(row[case]), float(row["investment"]), *[1.0 if row["asset"] == asset else 0.0 for asset in assets[1:]]] for row in pairs]
        y = [float(row["outcome"]) for row in pairs]
        beta, se, r_squared = _ols_hc1(x, y)
        results.append({
            "proxy_case": case, "coefficient_unit": "Calgary-minus-Edmonton BCPI year-over-year percentage points per CAD 1B reconstructed quarterly exposure difference",
            "coefficient": _round(beta[1]), "robust_standard_error": _round(se[1]),
            "confidence_interval_95": [_round(beta[1] - 1.96 * se[1]), _round(beta[1] + 1.96 * se[1])],
            "r_squared": _round(r_squared), "observation_count": len(y),
        })
    output = {
        "schema_version": "1.0.0", "run_id": RUN_ID, "status": "descriptive_proxy_association",
        "design": "Calgary-minus-Edmonton paired quarter/asset differences with asset fixed effects and non-residential investment difference control",
        "outcome": "BCPI year-over-year percentage-point difference; market bid-price proxy, not project cost outturn",
        "results": results,
        "input_manifest": {"panel_sha256": "sha256:" + hashlib.sha256(panel_path.read_bytes()).hexdigest(), "panel_report_sha256": "sha256:" + hashlib.sha256(panel_report_path.read_bytes()).hexdigest()},
        "limitations": [
            "The exposure is reconstructed from one costed under-construction project and a small set of permit candidates.",
            "The design has two Alberta markets, cannot establish parallel counterfactual trends, and may reflect unobserved Calgary-Edmonton differences.",
            "Repeated asset rows share the same market-quarter exposure and do not represent independent treatment events.",
            "Coefficients are sensitivity diagnostics and must not populate the executive calibrated forecast.",
        ],
        "publication_boundary": {"descriptive_association_authorized": True, "causal_interpretation_authorized": False, "executive_calibration_authorized": False, "ai_attributable_effect": None},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def _ols_hc1(x: list[list[float]], y: list[float]) -> tuple[list[float], list[float], float]:
    n, k = len(x), len(x[0])
    xtx = [[sum(x[r][i] * x[r][j] for r in range(n)) for j in range(k)] for i in range(k)]
    xty = [sum(x[r][i] * y[r] for r in range(n)) for i in range(k)]
    inv = _inverse(xtx); beta = [sum(inv[i][j] * xty[j] for j in range(k)) for i in range(k)]
    residuals = [y[r] - sum(x[r][j] * beta[j] for j in range(k)) for r in range(n)]
    meat = [[sum(residuals[r] ** 2 * x[r][i] * x[r][j] for r in range(n)) for j in range(k)] for i in range(k)]
    covariance = _multiply(_multiply(inv, meat), inv)
    scale = n / (n - k)
    se = [math.sqrt(max(0.0, covariance[i][i] * scale)) for i in range(k)]
    mean_y = sum(y) / n; sst = sum((item - mean_y) ** 2 for item in y); sse = sum(item ** 2 for item in residuals)
    return beta, se, 1 - sse / sst if sst else 0.0


def _inverse(matrix: list[list[float]]) -> list[list[float]]:
    n = len(matrix); augmented = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12: raise ValidationError("proxy association design matrix is singular")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]; augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(n):
            if row == column: continue
            factor = augmented[row][column]; augmented[row] = [augmented[row][j] - factor * augmented[column][j] for j in range(2 * n)]
    return [row[n:] for row in augmented]


def _multiply(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[i][m] * b[m][j] for m in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def _round(value: float) -> float: return round(value, 6)
