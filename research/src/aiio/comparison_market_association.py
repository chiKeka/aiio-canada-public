from __future__ import annotations

import csv, hashlib, json, math
from pathlib import Path
from typing import Any

from .proxy_association import _ols_hc1
from .schemas import ValidationError

RUN_ID = "AIIO_E2_COMPARISON_MARKET_PROXY_ASSOCIATION_0_1"


def run_comparison_market_association(panel_path: Path, panel_report_path: Path, output_path: Path) -> dict[str, Any]:
    report = json.loads(panel_report_path.read_text(encoding="utf-8"))
    if report.get("output_sha256") != "sha256:" + hashlib.sha256(panel_path.read_bytes()).hexdigest(): raise ValidationError("comparison panel hash mismatch")
    with panel_path.open(encoding="utf-8", newline="") as handle: rows = [row for row in csv.DictReader(handle) if row["bcpi_yoy_percent"]]
    markets = sorted({row["market"] for row in rows}); assets = sorted({row["asset_class"] for row in rows}); quarters = sorted({row["quarter"] for row in rows})
    x = [[1.0, math.log1p(float(row["data_centre_permit_count"])), *[float(row["market"] == item) for item in markets[1:]], *[float(row["asset_class"] == item) for item in assets[1:]], *[float(row["quarter"] == item) for item in quarters[1:]]] for row in rows]
    y = [float(row["bcpi_yoy_percent"]) for row in rows]
    beta, se, r2 = _ols_hc1(x, y); coefficient, stderr = beta[1], se[1]
    output = {"schema_version": "1.0.0", "run_id": RUN_ID, "status": "descriptive_proxy_association", "design": "Pooled Vancouver-Toronto-Montreal market-quarter-asset panel with market, quarter and asset fixed effects", "exposure": "log(1 + classified data-centre permit records issued in market-quarter)", "outcome": "BCPI year-over-year percent change", "result": {"coefficient": round(coefficient, 6), "robust_standard_error": round(stderr, 6), "confidence_interval_95": [round(coefficient - 1.96 * stderr, 6), round(coefficient + 1.96 * stderr, 6)], "observation_count": len(rows), "r_squared": round(r2, 6)}, "input_manifest": {"panel_sha256": "sha256:" + hashlib.sha256(panel_path.read_bytes()).hexdigest(), "panel_report_sha256": "sha256:" + hashlib.sha256(panel_report_path.read_bytes()).hexdigest()}, "limitations": ["Permit records are administrative proxies and may duplicate underlying projects across trades or revisions.", "Toronto is cleared-permit only and therefore right-censored relative to Vancouver and Montreal issued-permit feeds.", "A three-market observational association cannot establish an AI-attributable causal effect.", "Repeated asset rows share one market-quarter exposure; robust errors do not solve the small number of markets."], "publication_boundary": {"descriptive_association_authorized": True, "causal_interpretation_authorized": False, "executive_calibration_authorized": False, "ai_attributable_effect": None}}
    output_path.parent.mkdir(parents=True, exist_ok=True); output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"); return output
