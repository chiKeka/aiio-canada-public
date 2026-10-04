from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from .schemas import ValidationError


LEDGER_ID = "AIIO_AB_AI_CAPEX_ANNOUNCEMENT_LEDGER_0_1"
SOURCE_ID = "ALBERTA_MAJOR_PROJECTS"
GEOGRAPHY_ID = "PR_48"
ALLOWED_RELEVANCE = {"core_data_centre", "enabling_power"}
REQUIRED_FIELDS = {
    "project_id",
    "name",
    "estimated_cost_cad",
    "municipality",
    "schedule_text",
    "start_year",
    "end_year",
    "sector",
    "project_type",
    "power_generation_capacity_mw",
    "stage",
    "substage",
    "developer",
    "project_website",
    "longitude",
    "latitude",
    "location_count",
    "location_precision",
    "ai_relevance",
    "ai_classification_basis",
    "source_id",
    "source_evidence_status",
    "classification_evidence_status",
    "as_of_date",
}


def _optional_number(value: str, *, field: str) -> float | None:
    if not value.strip():
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise ValidationError(f"AI capex ledger {field} is not numeric") from exc
    if not math.isfinite(number) or number < 0:
        raise ValidationError(f"AI capex ledger {field} must be finite and non-negative")
    return number


def _optional_year(value: str, *, field: str) -> int | None:
    if not value.strip():
        return None
    try:
        year = int(value)
    except ValueError as exc:
        raise ValidationError(f"AI capex ledger {field} is not an integer year") from exc
    if not 1990 <= year <= 2100:
        raise ValidationError(f"AI capex ledger {field} is outside the accepted range")
    return year


def _schedule_status(start_year: int | None, end_year: int | None) -> str:
    if start_year is not None and end_year is not None:
        if end_year < start_year:
            raise ValidationError("AI capex ledger schedule ends before it starts")
        return "start_and_end_year_available"
    if start_year is not None:
        return "start_year_only"
    if end_year is not None:
        return "end_year_only"
    return "schedule_years_unavailable"


def build_ai_capex_announcement_ledger(input_path: Path) -> dict[str, Any]:
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED_FIELDS.issubset(reader.fieldnames):
            missing = sorted(REQUIRED_FIELDS - set(reader.fieldnames or []))
            raise ValidationError(f"AI capex ledger input schema changed; missing {missing}")
        rows = list(reader)

    if not rows:
        raise ValidationError("AI capex ledger input cannot be empty")
    project_ids = [row["project_id"].strip() for row in rows]
    if any(not project_id for project_id in project_ids):
        raise ValidationError("AI capex ledger project ID cannot be blank")
    if len(project_ids) != len(set(project_ids)):
        raise ValidationError("AI capex ledger contains duplicate project IDs")
    if {row["source_id"].strip() for row in rows} != {SOURCE_ID}:
        raise ValidationError("AI capex ledger source lineage changed")
    if {row["source_evidence_status"].strip() for row in rows} != {"observed"}:
        raise ValidationError("AI capex ledger source fields must remain observed")
    if {row["classification_evidence_status"].strip() for row in rows} != {"inferred"}:
        raise ValidationError("AI capex ledger relevance classifications must remain inferred")
    if not {row["ai_relevance"].strip() for row in rows}.issubset(ALLOWED_RELEVANCE):
        raise ValidationError("AI capex ledger contains an unsupported relevance class")
    as_of_dates = {row["as_of_date"].strip() for row in rows}
    if len(as_of_dates) != 1 or not next(iter(as_of_dates)):
        raise ValidationError("AI capex ledger requires one non-blank as-of date")

    records: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: item["project_id"]):
        reported_cost = _optional_number(
            row["estimated_cost_cad"], field="estimated_cost_cad"
        )
        power_capacity = _optional_number(
            row["power_generation_capacity_mw"],
            field="power_generation_capacity_mw",
        )
        start_year = _optional_year(row["start_year"], field="start_year")
        end_year = _optional_year(row["end_year"], field="end_year")
        schedule_status = _schedule_status(start_year, end_year)
        stage = row["stage"].strip()
        treatment_screen_status = (
            "publisher_stage_indicates_construction_activity_candidate"
            if "construction" in stage.lower()
            else "announcement_or_planning_record_only"
        )
        records.append(
            {
                "project_id": row["project_id"].strip(),
                "name": row["name"].strip(),
                "geography_id": GEOGRAPHY_ID,
                "municipality": row["municipality"].strip(),
                "developer": row["developer"].strip() or None,
                "ai_relevance": row["ai_relevance"].strip(),
                "ai_relevance_evidence_status": "inferred",
                "ai_classification_basis": row["ai_classification_basis"].strip(),
                "publisher_stage": stage or None,
                "publisher_substage": row["substage"].strip() or None,
                "reported_estimated_cost_cad": reported_cost,
                "reported_cost_status": (
                    "reported_estimate_available"
                    if reported_cost is not None
                    else "reported_estimate_unavailable"
                ),
                "schedule_text": row["schedule_text"].strip() or None,
                "start_year": start_year,
                "end_year": end_year,
                "schedule_status": schedule_status,
                "project_website": row["project_website"].strip() or None,
                "location_count": int(row["location_count"] or 0),
                "location_precision": row["location_precision"].strip(),
                "power_generation_capacity_mw": power_capacity,
                "treatment_screen_status": treatment_screen_status,
                "realized_construction_start_date": None,
                "realized_construction_spend_cad": None,
                "operational_date": None,
                "authorizing_treatment_onset_available": False,
                "authorizing_treatment_dose_available": False,
                "source_id": SOURCE_ID,
                "source_evidence_status": "observed",
                "as_of_date": row["as_of_date"].strip(),
                "quality_flags": [
                    "announcement_inventory_not_commitment",
                    "reported_cost_not_realized_spend",
                    "publisher_stage_not_verified_construction_onset",
                    "ai_relevance_inferred",
                ],
            }
        )

    relevance_counts = Counter(item["ai_relevance"] for item in records)
    stage_counts = Counter(item["publisher_stage"] or "not_reported" for item in records)
    schedule_counts = Counter(item["schedule_status"] for item in records)
    known_cost_records = [
        item for item in records if item["reported_estimated_cost_cad"] is not None
    ]
    known_core_cost_records = [
        item
        for item in known_cost_records
        if item["ai_relevance"] == "core_data_centre"
    ]
    known_enabling_cost_records = [
        item for item in known_cost_records if item["ai_relevance"] == "enabling_power"
    ]
    construction_candidates = [
        item
        for item in records
        if item["treatment_screen_status"]
        == "publisher_stage_indicates_construction_activity_candidate"
    ]

    return {
        "schema_version": "1.0.0",
        "ledger_id": LEDGER_ID,
        "source_id": SOURCE_ID,
        "geography_id": GEOGRAPHY_ID,
        "as_of_date": next(iter(as_of_dates)),
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "evidence_status": "observed_project_fields_with_inferred_ai_relevance_and_treatment_screen",
        "record_count": len(records),
        "coverage_summary": {
            "core_data_centre_record_count": relevance_counts["core_data_centre"],
            "enabling_power_record_count": relevance_counts["enabling_power"],
            "reported_estimated_cost_record_count": len(known_cost_records),
            "reported_estimated_cost_coverage_share": round(
                len(known_cost_records) / len(records), 6
            ),
            "known_reported_estimated_cost_cad": round(
                sum(item["reported_estimated_cost_cad"] for item in known_cost_records)
            ),
            "known_core_reported_estimated_cost_record_count": len(
                known_core_cost_records
            ),
            "known_core_reported_estimated_cost_cad": round(
                sum(
                    item["reported_estimated_cost_cad"]
                    for item in known_core_cost_records
                )
            ),
            "known_enabling_reported_estimated_cost_record_count": len(
                known_enabling_cost_records
            ),
            "known_enabling_reported_estimated_cost_cad": round(
                sum(
                    item["reported_estimated_cost_cad"]
                    for item in known_enabling_cost_records
                )
            ),
            "complete_schedule_year_record_count": schedule_counts[
                "start_and_end_year_available"
            ],
            "any_schedule_year_record_count": sum(
                count
                for status, count in schedule_counts.items()
                if status != "schedule_years_unavailable"
            ),
            "project_website_record_count": sum(
                item["project_website"] is not None for item in records
            ),
            "publisher_construction_stage_candidate_count": len(construction_candidates),
            "authorizing_treatment_onset_count": 0,
            "authorizing_treatment_dose_count": 0,
        },
        "stage_counts": dict(sorted(stage_counts.items())),
        "schedule_status_counts": dict(sorted(schedule_counts.items())),
        "treatment_requirement_assessment": {
            "status": "candidate_announcement_ledger_not_authorizing",
            "required_authorizing_fields": [
                "verified_realized_construction_start_date",
                "realized_construction_spend_by_region_and_period_cad",
                "stable_project_and_geography_identifier",
                "operational_or_completion_date_where_applicable",
            ],
            "authorizing_treatment_present": False,
            "reason": (
                "The source reports a current project inventory, estimated cost, publisher "
                "stage and partial schedules. It does not provide verified realized "
                "construction onset or realized AI-construction spending by region and period."
            ),
        },
        "aggregation_controls": {
            "known_cost_sum_is_partial": True,
            "missing_costs_are_not_zero": True,
            "enabling_power_kept_separate": True,
            "multi_location_projects_count_once": True,
            "probability_or_stage_weighting_applied": False,
            "scenario_capex_included": False,
        },
        "publication_boundary": {
            "descriptive_announcement_ledger_authorized": True,
            "partial_known_reported_cost_aggregate_authorized": True,
            "committed_investment_claim_authorized": False,
            "realized_construction_treatment_authorized": False,
            "probability_weighted_pipeline_authorized": False,
            "future_spend_forecast_authorized": False,
            "ai_attributable_effect_authorized": False,
        },
        "records": records,
        "limitations": [
            "The Alberta Major Projects inventory is a public project register, not an audited commitments or realized-spending dataset.",
            "Reported estimated costs are incomplete and cannot be summed as a complete portfolio total.",
            "Project stage is publisher-reported and does not establish a treatment-onset date.",
            "Schedule strings often provide only a start year, an end year or neither; no missing field is imputed.",
            "AI relevance is inferred from controlled project-name or description vocabulary.",
            "The ledger contains no probability weighting, no scenario values and no AI-attributable cost or schedule effect.",
        ],
    }


def run_ai_capex_announcement_ledger(
    input_path: Path, output_path: Path
) -> dict[str, Any]:
    result = build_ai_capex_announcement_ledger(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
