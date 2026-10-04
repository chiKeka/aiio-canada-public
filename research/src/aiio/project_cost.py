from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .schemas import ValidationError


MODEL_ID = "AIIO_PROJECT_REFERENCE_COST_0_1"


def _require_text(project: dict[str, Any], field: str) -> str:
    value = project.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"project definition requires non-empty {field}")
    return value.strip()


def _validate_project(project: dict[str, Any]) -> list[dict[str, float | int]]:
    for field in (
        "project_id",
        "project_name",
        "asset_class",
        "geography_id",
        "estimate_price_basis_period_end",
    ):
        _require_text(project, field)

    estimate = project.get("current_estimate_cad")
    if (
        isinstance(estimate, bool)
        or not isinstance(estimate, (int, float))
        or not math.isfinite(float(estimate))
        or float(estimate) <= 0
    ):
        raise ValidationError("current_estimate_cad must be finite and positive")

    raw_profile = project.get("expenditure_profile")
    if not isinstance(raw_profile, list) or not raw_profile:
        raise ValidationError("project definition requires an expenditure_profile")
    profile: list[dict[str, float | int]] = []
    seen_horizons = set()
    for item in raw_profile:
        if not isinstance(item, dict):
            raise ValidationError("each expenditure profile row must be an object")
        horizon = item.get("horizon_years")
        share = item.get("share")
        if isinstance(horizon, bool) or not isinstance(horizon, int) or not 0 <= horizon <= 10:
            raise ValidationError("expenditure horizon_years must be an integer from 0 through 10")
        if horizon in seen_horizons:
            raise ValidationError("expenditure profile horizons must be unique")
        if (
            isinstance(share, bool)
            or not isinstance(share, (int, float))
            or not math.isfinite(float(share))
            or not 0 < float(share) <= 1
        ):
            raise ValidationError("each expenditure share must be finite and in (0, 1]")
        seen_horizons.add(horizon)
        profile.append({"horizon_years": horizon, "share": float(share)})
    share_total = sum(float(item["share"]) for item in profile)
    if not math.isclose(share_total, 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValidationError("expenditure profile shares must sum to exactly 1")
    return sorted(profile, key=lambda item: int(item["horizon_years"]))


def _find_reference_result(
    baseline: dict[str, Any], asset_class: str, geography_id: str
) -> dict[str, Any] | None:
    matches = [
        item
        for item in baseline.get("reference_class_results", [])
        if item.get("asset_class") == asset_class
        and item.get("geography_id") == geography_id
    ]
    if len(matches) > 1:
        raise ValidationError("cost baseline contains duplicate project reference classes")
    return matches[0] if matches else None


def _null_result(
    project: dict[str, Any],
    baseline: dict[str, Any],
    profile: list[dict[str, float | int]],
    *,
    status: str,
    reason: str,
    reference: dict[str, Any] | None = None,
    failed_horizons: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "project_id": project["project_id"],
        "project_name": project["project_name"],
        "asset_class": project["asset_class"],
        "geography_id": project["geography_id"],
        "current_estimate_cad": float(project["current_estimate_cad"]),
        "estimate_price_basis_period_end": project[
            "estimate_price_basis_period_end"
        ],
        "expenditure_profile": profile,
        "source_baseline_model_id": baseline.get("model_id"),
        "source_baseline_as_of_date": baseline.get("as_of_date"),
        "reference_indicator_id": (
            reference.get("reference_indicator_id") if reference else None
        ),
        "reference_mapping_status": (
            reference.get("mapping_status") if reference else None
        ),
        "reference_mapping_note": (
            reference.get("mapping_note") if reference else None
        ),
        "status": status,
        "reason": reason,
        "failed_horizons": failed_horizons or [],
        "market_reference_baseline": {
            "schedule_weighted_factor": None,
            "schedule_weighted_change_percent": None,
            "schedule_weighted_estimate_cad": None,
            "schedule_weighted_escalation_cad": None,
        },
        "ai_attributable_increment": {
            "status": "not_calibrated",
            "cost_escalation_percent": None,
            "cost_escalation_cad": None,
            "schedule_delay_days": None,
        },
        "graph_role": (
            "The graph may explain relevant mechanisms but is not used in the "
            "schedule-weighted reference calculation."
        ),
    }


def build_project_reference_cost(
    project: dict[str, Any], baseline: dict[str, Any]
) -> dict[str, Any]:
    profile = _validate_project(project)
    asset_class = project["asset_class"]
    geography_id = project["geography_id"]
    reference = _find_reference_result(baseline, asset_class, geography_id)
    if reference is None:
        return _null_result(
            project,
            baseline,
            profile,
            status="not_assessed",
            reason="no eligible asset-class and geography reference series",
        )

    latest_period_end = reference.get("latest_period_end")
    if project["estimate_price_basis_period_end"] != latest_period_end:
        return _null_result(
            project,
            baseline,
            profile,
            status="not_assessed",
            reason=(
                "estimate price basis does not match the baseline origin; rebasing is "
                "not implemented in v0.1"
            ),
            reference=reference,
        )

    current_index = reference.get("latest_index")
    if not isinstance(current_index, (int, float)) or current_index <= 0:
        raise ValidationError("project reference series requires a positive latest index")
    horizons_by_year = {
        item["horizon_years"]: item for item in reference.get("horizons", [])
    }
    failed_horizons = []
    weighted_rows = []
    for item in profile:
        horizon = int(item["horizon_years"])
        share = float(item["share"])
        if horizon == 0:
            projected_index = float(current_index)
            horizon_status = "observed_origin"
        else:
            forecast = horizons_by_year.get(horizon)
            if (
                forecast is None
                or forecast.get("status") != "gate_passed"
                or not isinstance(forecast.get("projected_index"), (int, float))
            ):
                failed_horizons.append(
                    {
                        "horizon_years": horizon,
                        "share": share,
                        "status": forecast.get("status") if forecast else "not_available",
                        "reason": forecast.get("reason") if forecast else "horizon absent",
                    }
                )
                continue
            projected_index = float(forecast["projected_index"])
            horizon_status = "gate_passed"
        weighted_rows.append(
            {
                "horizon_years": horizon,
                "share": share,
                "status": horizon_status,
                "reference_index": projected_index,
                "index_factor": projected_index / float(current_index),
            }
        )

    if failed_horizons:
        return _null_result(
            project,
            baseline,
            profile,
            status="not_assessed",
            reason=(
                "one or more expenditure horizons failed or lacked the reference "
                "baseline gate"
            ),
            reference=reference,
            failed_horizons=failed_horizons,
        )

    authorization = baseline.get("publication_authorization", {})
    if authorization.get("public_projection_authorized") is not True:
        return _null_result(
            project,
            baseline,
            profile,
            status="withheld",
            reason="independent modelling review has not authorized public projection",
            reference=reference,
        )

    factor = sum(row["share"] * row["index_factor"] for row in weighted_rows)
    estimate = float(project["current_estimate_cad"])
    projected_estimate = estimate * factor
    return {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "project_id": project["project_id"],
        "project_name": project["project_name"],
        "asset_class": asset_class,
        "geography_id": geography_id,
        "current_estimate_cad": estimate,
        "estimate_price_basis_period_end": project[
            "estimate_price_basis_period_end"
        ],
        "expenditure_profile": profile,
        "source_baseline_model_id": baseline.get("model_id"),
        "source_baseline_as_of_date": baseline.get("as_of_date"),
        "reference_indicator_id": reference["reference_indicator_id"],
        "reference_mapping_status": reference.get("mapping_status"),
        "reference_mapping_note": reference.get("mapping_note"),
        "status": "baseline_only",
        "reason": None,
        "failed_horizons": [],
        "reference_schedule": weighted_rows,
        "market_reference_baseline": {
            "schedule_weighted_factor": round(factor, 6),
            "schedule_weighted_change_percent": round((factor - 1) * 100, 3),
            "schedule_weighted_estimate_cad": round(projected_estimate, 2),
            "schedule_weighted_escalation_cad": round(
                projected_estimate - estimate, 2
            ),
        },
        "ai_attributable_increment": {
            "status": "not_calibrated",
            "cost_escalation_percent": None,
            "cost_escalation_cad": None,
            "schedule_delay_days": None,
        },
        "graph_role": (
            "The graph may explain relevant mechanisms but is not used in the "
            "schedule-weighted reference calculation."
        ),
        "limitations": [
            "The result is a schedule-weighted BCPI reference equivalent, not a forecast of realized project cost.",
            "Expenditure shares are user inputs and are not inferred from project duration.",
            "Each positive horizon uses a point-in-time annual horizon from the baseline, not a within-year cash-flow curve.",
            "The result contains no AI-attributable increment and does not use graph pressure scores.",
        ],
    }


def run_project_reference_cost(
    project_path: Path, baseline_path: Path, output_path: Path
) -> dict[str, Any]:
    project = json.loads(project_path.read_text(encoding="utf-8"))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    result = build_project_reference_cost(project, baseline)
    result["inputs"] = {
        "project_definition_sha256": hashlib.sha256(
            project_path.read_bytes()
        ).hexdigest(),
        "cost_baseline_sha256": hashlib.sha256(
            baseline_path.read_bytes()
        ).hexdigest(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
