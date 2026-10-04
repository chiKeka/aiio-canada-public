from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from .schemas import ValidationError


SOURCE_ID = "OAGO_SELECTED_INFRASTRUCTURE_PROJECTS_2024"
MODEL_ID = "AIIO_OAGO_AUDITED_PROJECT_OUTCOME_REFERENCES_0_1"
ALLOWED_REVIEW_STATUSES = {
    "primary_visual_review_complete_pending_independent_review",
    "independently_reviewed",
}
ALLOWED_PRECISIONS = {"day", "month", "year", "missing"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _extract_pdf_text(path: Path) -> str:
    executable = shutil.which("pdftotext")
    if executable is None:
        raise ValidationError(
            "pdftotext is required to verify the audited-outcome source anchors"
        )
    result = subprocess.run(
        [executable, "-layout", str(path), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValidationError(
            "audited-outcome source PDF text extraction failed: "
            + result.stderr.strip()
        )
    return result.stdout


def _validate_date(value: str | None, precision: str, field_name: str) -> None:
    if precision not in ALLOWED_PRECISIONS:
        raise ValidationError(f"{field_name} uses unsupported precision {precision!r}")
    if precision == "missing":
        if value is not None:
            raise ValidationError(f"{field_name} must be null when precision is missing")
        return
    if value is None:
        raise ValidationError(f"{field_name} cannot be null at {precision} precision")
    patterns = {
        "day": r"\d{4}-\d{2}-\d{2}",
        "month": r"\d{4}-\d{2}",
        "year": r"\d{4}",
    }
    if not re.fullmatch(patterns[precision], value):
        raise ValidationError(
            f"{field_name} does not match its declared {precision} precision"
        )
    if precision == "day":
        date.fromisoformat(value)
    elif precision == "month":
        date.fromisoformat(value + "-01")
    else:
        date.fromisoformat(value + "-01-01")


def _normalized_case(case: dict[str, Any], review_status: str) -> dict[str, Any]:
    for field in (
        "outcome_case_id",
        "project_reference_id",
        "project_reference_id_status",
        "project_name",
        "geography_id",
        "province",
        "municipality",
        "asset_class",
        "delivery_model",
        "baseline_cost",
        "latest_or_final_cost",
        "cost_variance",
        "approved_change_history",
        "cost_components",
        "schedule",
        "authorizing_field_status",
        "quality_flags",
    ):
        if case.get(field) in (None, "", [], {}):
            raise ValidationError(
                f"audited outcome {case.get('outcome_case_id', '<unknown>')} is missing {field}"
            )

    baseline = case["baseline_cost"]
    latest = case["latest_or_final_cost"]
    variance = case["cost_variance"]
    if baseline.get("scope_id") != latest.get("scope_id"):
        raise ValidationError(
            f"{case['outcome_case_id']} cannot compare cost values with different scopes"
        )
    baseline_value = float(baseline["value_cad"])
    latest_value = float(latest["value_cad"])
    if baseline_value <= 0 or latest_value <= 0:
        raise ValidationError("audited project costs must be positive")
    computed_value = latest_value - baseline_value
    computed_percent = computed_value / baseline_value * 100
    if not math.isclose(
        float(variance["computed_value_cad"]), computed_value, abs_tol=1.0
    ):
        raise ValidationError(
            f"{case['outcome_case_id']} cost variance CAD does not reconcile"
        )
    if not math.isclose(
        float(variance["computed_percent"]), computed_percent, abs_tol=0.00001
    ):
        raise ValidationError(
            f"{case['outcome_case_id']} cost variance percent does not reconcile"
        )
    if abs(float(variance["source_reported_percent"]) - computed_percent) > 0.75:
        raise ValidationError(
            f"{case['outcome_case_id']} source-reported cost variance is outside rounding tolerance"
        )

    components = case["cost_components"]
    component_items = components.get("items", [])
    if not component_items:
        raise ValidationError(f"{case['outcome_case_id']} requires cost components")
    for item in component_items:
        if not item.get("source_category") or not item.get("graph_channel"):
            raise ValidationError("cost components require source category and graph channel")
        if float(item.get("value_cad", -1)) < 0:
            raise ValidationError("cost component values cannot be negative")
    component_sum = sum(float(item["value_cad"]) for item in component_items)
    if not math.isclose(component_sum, float(components["total_cad"]), abs_tol=1.0):
        raise ValidationError(
            f"{case['outcome_case_id']} cost components do not reconcile to their source total"
        )

    _validate_date(
        baseline["approval_date"],
        baseline["date_precision"],
        "baseline_cost.approval_date",
    )
    _validate_date(
        latest["as_of_date"],
        latest["date_precision"],
        "latest_or_final_cost.as_of_date",
    )

    schedule = case["schedule"]
    schedule_dates = (
        ("baseline_start_date", "baseline_start_precision"),
        ("actual_start_date", "actual_start_precision"),
        ("baseline_substantial_completion_date", "baseline_completion_precision"),
        ("actual_substantial_completion_date", "actual_completion_precision"),
        ("final_completion_date", "final_completion_precision"),
    )
    for value_field, precision_field in schedule_dates:
        _validate_date(
            schedule[value_field],
            schedule[precision_field],
            f"schedule.{value_field}",
        )

    both_day_precision = (
        schedule["baseline_completion_precision"] == "day"
        and schedule["actual_completion_precision"] == "day"
    )
    if both_day_precision:
        delay_days = (
            date.fromisoformat(schedule["actual_substantial_completion_date"])
            - date.fromisoformat(schedule["baseline_substantial_completion_date"])
        ).days
        if schedule["computed_delay_days"] != delay_days:
            raise ValidationError(
                f"{case['outcome_case_id']} schedule delay days do not reconcile"
            )
    else:
        delay_days = None
        if schedule["computed_delay_days"] is not None:
            raise ValidationError(
                f"{case['outcome_case_id']} cannot compute delay days from mixed-precision dates"
            )

    field_status = case["authorizing_field_status"]
    required_flags = {
        "independent_estimate_with_price_basis",
        "complete_approved_change_history",
        "consistent_asset_reference_class",
        "stable_publisher_project_id",
        "complete_baseline_and_actual_schedule_dates",
    }
    if set(field_status) != required_flags:
        raise ValidationError(
            f"{case['outcome_case_id']} authorizing field status is incomplete"
        )
    if case.get("reference_case_publication_authorized") is not False:
        raise ValidationError(
            "audited reference cases must remain unpublished until independent review"
        )
    if review_status != "independently_reviewed" and any(field_status.values()):
        raise ValidationError(
            "pending-review reference cases cannot mark authorizing fields complete"
        )

    return {
        "outcome_case_id": case["outcome_case_id"],
        "project_reference_id": case["project_reference_id"],
        "project_reference_id_status": case["project_reference_id_status"],
        "project_name": case["project_name"],
        "geography_id": case["geography_id"],
        "province": case["province"],
        "municipality": case["municipality"],
        "asset_class": case["asset_class"],
        "delivery_model": case["delivery_model"],
        "baseline_cost_cad": baseline_value,
        "baseline_cost_approval_date": baseline["approval_date"],
        "baseline_cost_scope_id": baseline["scope_id"],
        "baseline_price_basis_date": baseline["price_basis_date"],
        "latest_or_final_cost_cad": latest_value,
        "latest_or_final_cost_as_of_date": latest["as_of_date"],
        "latest_or_final_cost_status": latest["status"],
        "cost_variance_cad": computed_value,
        "cost_variance_percent": computed_percent,
        "source_reported_cost_variance_percent": float(
            variance["source_reported_percent"]
        ),
        "baseline_start_date": schedule["baseline_start_date"],
        "actual_start_date": schedule["actual_start_date"],
        "baseline_substantial_completion_date": schedule[
            "baseline_substantial_completion_date"
        ],
        "baseline_completion_precision": schedule[
            "baseline_completion_precision"
        ],
        "actual_substantial_completion_date": schedule[
            "actual_substantial_completion_date"
        ],
        "actual_completion_precision": schedule["actual_completion_precision"],
        "schedule_delay_days": delay_days,
        "source_reported_schedule_delay": schedule["source_reported_delay"],
        "final_completion_date": schedule["final_completion_date"],
        "approved_change_history_complete": bool(
            case["approved_change_history"]["complete"]
        ),
        "known_change_count": len(case["approved_change_history"]["known_changes"]),
        "cost_component_total_cad": component_sum,
        "cost_component_scope_id": components["total_scope_id"],
        "cost_component_count": len(component_items),
        "cost_components": [
            {
                "source_category": item["source_category"],
                "value_cad": float(item["value_cad"]),
                "graph_channel": item["graph_channel"],
                "source_evidence_status": "observed",
                "graph_channel_evidence_status": "inferred",
            }
            for item in component_items
        ],
        "authorizing_field_status": field_status,
        "cost_outcome_panel_authorized": False,
        "schedule_outcome_panel_authorized": False,
        "reference_case_publication_authorized": False,
        "quality_flags": list(case["quality_flags"]),
        "source_id": SOURCE_ID,
        "source_locators": {
            "baseline_cost": baseline["source_locator"],
            "latest_or_final_cost": latest["source_locator"],
        },
    }


def run_audited_project_outcomes(
    manual_extract_path: Path,
    source_pdf_path: Path,
    output_json_path: Path,
    output_csv_path: Path,
    *,
    source_text_override: str | None = None,
) -> dict[str, Any]:
    manual = json.loads(manual_extract_path.read_text(encoding="utf-8"))
    if manual.get("schema_version") != "1.0.0":
        raise ValidationError("audited outcome extract must use schema_version 1.0.0")
    if manual.get("source_id") != SOURCE_ID:
        raise ValidationError("audited outcome extract uses an unexpected source_id")
    actual_hash = sha256_file(source_pdf_path)
    if manual.get("source_content_hash") != actual_hash:
        raise ValidationError(
            "audited outcome extraction does not match the supplied source PDF hash"
        )
    review_status = manual.get("review_status")
    if review_status not in ALLOWED_REVIEW_STATUSES:
        raise ValidationError("audited outcome extract has an unsupported review status")

    source_text = (
        source_text_override
        if source_text_override is not None
        else _extract_pdf_text(source_pdf_path)
    )
    normalized_source_text = _normalized_text(source_text)
    anchors = manual.get("source_anchors", [])
    if not anchors:
        raise ValidationError("audited outcome extract requires source anchors")
    for anchor in anchors:
        if _normalized_text(str(anchor.get("anchor_text", ""))) not in normalized_source_text:
            raise ValidationError(
                "audited outcome source anchor not found: "
                + str(anchor.get("field_group", "unknown"))
            )

    cases = [_normalized_case(case, review_status) for case in manual.get("cases", [])]
    if len(cases) != 2:
        raise ValidationError("the audited outcome intake must contain exactly two completed cases")
    case_ids = [case["outcome_case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValidationError("audited outcome case IDs must be unique")
    boundary = manual.get("publication_boundary", {})
    if any(
        boundary.get(field) is not False
        for field in (
            "public_project_cost_outcome_authorized",
            "public_project_schedule_outcome_authorized",
            "ai_attributable_effect_authorized",
        )
    ):
        raise ValidationError("audited outcome publication boundary must fail closed")

    completed_cost_cases = sum(
        case["latest_or_final_cost_status"] == "completed_total_project_cost"
        for case in cases
    )
    exact_schedule_pairs = sum(
        case["baseline_completion_precision"] == "day"
        and case["actual_completion_precision"] == "day"
        for case in cases
    )
    result = {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "extract_id": manual["extract_id"],
        "source_id": SOURCE_ID,
        "source_as_of_date": manual["source_as_of_date"],
        "evidence_status": "observed_named_cases_with_inferred_reconciliations",
        "review": {
            "status": review_status,
            "reviewed_by": manual["reviewed_by"],
            "reviewer_type": manual["reviewer_type"],
            "reviewed_at": manual["reviewed_at"],
            "review_record": manual["review_record"],
        },
        "source_file": {
            "content_hash": actual_hash,
            "archive_file": source_pdf_path.name,
            "verified_anchor_count": len(anchors),
        },
        "coverage_summary": {
            "named_completed_project_count": len(cases),
            "completed_total_cost_case_count": completed_cost_cases,
            "exact_day_substantial_completion_pair_count": exact_schedule_pairs,
            "price_basis_date_case_count": sum(
                case["baseline_price_basis_date"] is not None for case in cases
            ),
            "complete_change_history_case_count": sum(
                case["approved_change_history_complete"] for case in cases
            ),
            "publisher_stable_project_id_case_count": sum(
                case["authorizing_field_status"]["stable_publisher_project_id"]
                for case in cases
            ),
        },
        "cases": cases,
        "publication_boundary": {
            **boundary,
            "reference_case_publication_authorized": False,
        },
        "limitations": [
            "The two cases are named audited references, not a reusable multi-region or quarterly outcome panel.",
            "Neither case publishes an estimate price-basis date or complete approved-change history.",
            "Lakeridge Gardens has mixed month/day completion precision, so no calendar-day delay is calculated.",
            "Highway 427 cost was estimated, disputed and not finalized at the audit date.",
            "No AI-attributable effect can be inferred from these project histories.",
        ],
    }

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "outcome_case_id",
        "project_reference_id",
        "project_name",
        "geography_id",
        "province",
        "municipality",
        "asset_class",
        "delivery_model",
        "baseline_cost_cad",
        "baseline_cost_approval_date",
        "baseline_price_basis_date",
        "latest_or_final_cost_cad",
        "latest_or_final_cost_as_of_date",
        "latest_or_final_cost_status",
        "cost_variance_cad",
        "cost_variance_percent",
        "baseline_substantial_completion_date",
        "baseline_completion_precision",
        "actual_substantial_completion_date",
        "actual_completion_precision",
        "schedule_delay_days",
        "source_reported_schedule_delay",
        "approved_change_history_complete",
        "cost_component_total_cad",
        "cost_component_count",
        "cost_outcome_panel_authorized",
        "schedule_outcome_panel_authorized",
        "source_id",
        "quality_flags",
    ]
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for case in cases:
            row = {field: case.get(field) for field in fieldnames}
            row["quality_flags"] = "|".join(case["quality_flags"])
            writer.writerow(row)
    return result
