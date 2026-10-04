from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .schemas import ValidationError


RUN_ID = "AIIO_E2_EMPIRICAL_ESTIMATION_GATE_0_1"
REQUIRED_DIAGNOSTICS = [
    "cohort_common_support", "pretrend_equivalence", "placebo_event_dates",
    "negative_control_outcome", "leave_one_region_out", "leave_one_event_out",
    "independent_modelling_review",
]


def run_empirical_estimation_gate(
    root: Path,
    contract_path: Path,
    panel_path: Path,
    panel_report_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    contract = _object(contract_path)
    panel_report = _object(panel_report_path)
    rows = _csv(panel_path)
    if panel_report.get("output_sha256") != "sha256:" + _sha(panel_path):
        raise ValidationError("empirical estimation panel hash mismatch")
    if panel_report.get("panel_id") != "AIIO_E2_EMPIRICAL_COVARIATE_PANEL_0_1":
        raise ValidationError("empirical estimation received an unknown panel")
    if len(rows) != panel_report.get("row_count"):
        raise ValidationError("empirical estimation panel row count drifted")

    treated_regions = {row["geography_id"] for row in rows if row["authorizing_treatment_present"] == "true"}
    outcome_assets = {row["asset_class"] for row in rows if row["authorizing_outcome_present"] == "true"}
    eligible_rows = [row for row in rows if row["estimation_eligible"] == "true"]
    if eligible_rows and (not treated_regions or not outcome_assets):
        raise ValidationError("estimation-eligible rows lack authorizing treatment or outcomes")

    design = contract["design"]
    gate_checks = [
        _gate("authorizing_treatment", len(treated_regions) >= design["minimum_treated_regions"], len(treated_regions), design["minimum_treated_regions"]),
        _gate("authorizing_outcomes", len(outcome_assets) >= design["minimum_asset_classes"], len(outcome_assets), design["minimum_asset_classes"]),
        _gate("eligible_panel_rows", bool(eligible_rows), len(eligible_rows), 1),
    ]
    estimator_authorized = all(item["passed"] for item in gate_checks)
    if estimator_authorized:
        raise ValidationError("eligible treatment/outcome data require the diagnostic implementation before estimation can run")

    result = {
        "schema_version": "1.0.0", "run_id": RUN_ID, "estimand_id": contract["estimand_id"],
        "estimator": design["primary_estimator"], "status": "withheld_ineligible_panel",
        "panel_summary": {
            "row_count": len(rows), "authorizing_treated_region_count": len(treated_regions),
            "authorizing_outcome_asset_class_count": len(outcome_assets), "estimation_eligible_row_count": len(eligible_rows),
        },
        "gate_checks": gate_checks,
        "diagnostic_plan": [{"diagnostic_id": diagnostic, "status": "not_run_estimator_withheld"} for diagnostic in REQUIRED_DIAGNOSTICS],
        "input_manifest": {
            str(contract_path.relative_to(root)): "sha256:" + _sha(contract_path),
            str(panel_path.relative_to(root)): "sha256:" + _sha(panel_path),
            str(panel_report_path.relative_to(root)): "sha256:" + _sha(panel_report_path),
        },
        "estimates": {"cost_escalation_percent": None, "cost_escalation_cad": None, "schedule_delay_days": None},
        "publication_boundary": {
            "estimator_run_authorized": False, "effect_publication_authorized": False,
            "reason": "No row contains both an authorizing realized AI-construction treatment and an authorizing public-project outcome.",
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _gate(gate_id: str, passed: bool, observed: int, required: int) -> dict[str, Any]:
    return {"gate_id": gate_id, "passed": passed, "observed": observed, "required": required}


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValidationError(f"expected JSON object: {path}")
    return value


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle: rows = list(csv.DictReader(handle))
    if not rows: raise ValidationError("empirical estimation panel is empty")
    return rows


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
