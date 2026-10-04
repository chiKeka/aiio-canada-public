from __future__ import annotations

import csv, hashlib, json, math, statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .schemas import ValidationError

MODEL_ID = "AIIO_E2_COMPARISON_MARKET_PANEL_0_1"
MARKETS = {"vancouver": "CMA_933", "toronto": "CMA_535", "montreal": "CMA_462"}
FIELDS = ("geography_id", "market", "quarter", "period_start", "period_end", "asset_class", "bcpi_index", "bcpi_yoy_percent", "data_centre_permit_count", "reported_permit_value_cad", "reported_permit_value_status", "median_issue_to_completion_days", "completion_duration_count", "permit_source_scope", "evidence_status", "quality_flags")


def build_comparison_market_panel(root: Path, bcpi_path: Path, permit_paths: dict[str, Path], permit_report_paths: dict[str, Path], output_csv: Path, output_json: Path) -> dict[str, Any]:
    bcpi = _csv(bcpi_path); reports = {city: _obj(path) for city, path in permit_report_paths.items()}
    for city, report in reports.items():
        if report.get("publication_boundary", {}).get("realized_ai_construction_treatment_authorized") is not False: raise ValidationError(f"{city} permit boundary must remain non-authorizing")
        if report.get("output_sha256") != _sha(permit_paths[city]): raise ValidationError(f"{city} permit artifact hash mismatch")
    permit_cells: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {"count": 0, "value": 0.0, "value_n": 0, "durations": []})
    for city, path in permit_paths.items():
        for row in _csv(path):
            if row["candidate_status"] != "data_centre_candidate" or not row["issue_date"]: continue
            cell = permit_cells[(city, _quarter(row["issue_date"]))]; cell["count"] += 1
            if row["reported_estimated_construction_value_cad"]: cell["value"] += float(row["reported_estimated_construction_value_cad"]); cell["value_n"] += 1
            if row.get("issue_to_completion_days"): cell["durations"].append(int(row["issue_to_completion_days"]))
    series: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in bcpi: series[(row["geography_id"], row["indicator_id"])].append(row)
    output_rows = []
    for (geo, indicator), observations in series.items():
        city = next((name for name, code in MARKETS.items() if code == geo), None)
        if city is None: continue
        ordered = sorted(observations, key=lambda row: row["period_start"]); values = [float(row["value"]) for row in ordered]
        for index, row in enumerate(ordered):
            if row["period_start"] < "2017-01-01" or row["period_end"] > "2026-06-30": continue
            quarter = _quarter(row["period_start"]); cell = permit_cells[(city, quarter)]; durations = cell["durations"]
            yoy = (values[index] / values[index - 4] - 1) * 100 if index >= 4 and values[index - 4] else None
            output_rows.append({"geography_id": geo, "market": city, "quarter": quarter, "period_start": row["period_start"], "period_end": row["period_end"], "asset_class": indicator, "bcpi_index": f"{values[index]:.3f}", "bcpi_yoy_percent": "" if yoy is None else f"{yoy:.6f}", "data_centre_permit_count": str(cell["count"]), "reported_permit_value_cad": f"{cell['value']:.2f}" if cell["value_n"] else "", "reported_permit_value_status": "partially_observed_permit_estimates" if cell["value_n"] else "not_available", "median_issue_to_completion_days": f"{statistics.median(durations):.1f}" if durations else "", "completion_duration_count": str(len(durations)), "permit_source_scope": "cleared_permits_only_right_censored" if city == "toronto" else "issued_permits_initial_issuance", "evidence_status": "observed_and_inferred_proxy", "quality_flags": "not_realized_spend_or_labour_hours|permit_records_not_linked_to_underlying_projects|not_ai_specific"})
    if not output_rows: raise ValidationError("comparison market panel is empty")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle: writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(output_rows)
    report = {"schema_version": "1.0.0", "model_id": MODEL_ID, "status": "comparison_market_proxy_panel", "row_count": len(output_rows), "market_count": 3, "asset_class_count": len({row["asset_class"] for row in output_rows}), "quarter_count": len({row["quarter"] for row in output_rows}), "permit_candidate_counts": {city: sum(cell["count"] for (name, _), cell in permit_cells.items() if name == city) for city in MARKETS}, "input_manifest": {str(path.relative_to(root)): _sha(path) for path in [bcpi_path, *permit_paths.values(), *permit_report_paths.values()]}, "output_sha256": _sha(output_csv), "limitations": ["Toronto contains cleared permits only, creating completion-lag right censoring relative to issued-permit feeds.", "Permit counts can contain multiple trades or revisions for one underlying project.", "Reported permit values are incomplete and are not comparable as realized expenditure.", "BCPI is a market bid-price index, not project cost or schedule outturn."], "publication_boundary": {"descriptive_comparison_authorized": True, "causal_interpretation_authorized": False, "executive_calibration_authorized": False, "ai_attributable_effect": None}}
    output_json.parent.mkdir(parents=True, exist_ok=True); output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"); return report


def _quarter(value: str) -> str: return f"{value[:4]}-Q{(int(value[5:7])-1)//3+1}"
def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle: rows = list(csv.DictReader(handle))
    if not rows: raise ValidationError(f"empty input: {path}")
    return rows
def _obj(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"));
    if not isinstance(value, dict): raise ValidationError(f"expected object: {path}")
    return value
def _sha(path: Path) -> str: return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
