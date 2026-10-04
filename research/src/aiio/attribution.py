from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .registry import load_registry
from .schemas import ValidationError


REQUIRED_DOMAIN_IDS = {
    "REALIZED_AI_CONSTRUCTION_TREATMENT",
    "PUBLIC_PROJECT_COST_OUTCOMES",
    "PUBLIC_PROJECT_SCHEDULE_OUTCOMES",
    "REGIONAL_CONSTRUCTION_ACTIVITY_CONTROLS",
    "LABOUR_AND_WAGE_CONTROLS",
    "GRID_AND_LARGE_LOAD_CONTROLS",
}
ALLOWED_DOMAIN_STATUSES = {"available", "candidate", "missing"}
ALLOWED_DOMAIN_ROLES = {
    "authorizing_treatment",
    "authorizing_outcome",
    "control",
    "mechanism_and_control",
}
REQUIRED_OUTCOME_FAMILIES = {"cost", "schedule", "procurement"}
REQUIRED_DESIGN_FIELDS = {
    "primary_estimator",
    "control_cohort",
    "aggregation",
    "two_way_fixed_effects_event_study_primary",
    "anticipation_periods",
    "minimum_pre_treatment_quarters",
    "minimum_post_treatment_quarters",
    "minimum_treated_regions",
    "minimum_control_regions_per_cohort",
    "minimum_asset_classes",
    "leave_one_region_out_required",
    "leave_one_event_out_required",
    "negative_control_outcome_required",
    "placebo_event_dates_required",
    "pretrend_equivalence_assessment_required",
    "covariates_locked_before_outcome_analysis",
}
PROHIBITED_TREATMENT_TOKENS = {
    "announced_capex_cad",
    "requested_connection_load_mw",
    "forecast_data_centre_demand_mw",
    "scenario_capex_cad",
    "graph_pressure_score",
}


def build_attribution_readiness(
    contract_path: Path,
    registry_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    contract = load_object(contract_path)
    registry = {source.source_id: source for source in load_registry(registry_path)}
    validate_contract(contract, registry_ids=set(registry))

    domains = {item["domain_id"]: item for item in contract["data_domains"]}
    treatment = domains["REALIZED_AI_CONSTRUCTION_TREATMENT"]
    cost = domains["PUBLIC_PROJECT_COST_OUTCOMES"]
    schedule = domains["PUBLIC_PROJECT_SCHEDULE_OUTCOMES"]
    control_domains = [
        item
        for item in contract["data_domains"]
        if item["role"] in {"control", "mechanism_and_control"}
    ]

    readiness_checks = [
        check(
            "contract_and_source_lineage",
            "pass",
            "The preregistered contract validates and every candidate source is registry-bound.",
        ),
        check(
            "realized_ai_construction_treatment",
            "pass" if treatment["status"] == "available" else "pending",
            domain_message(treatment, "realized AI-construction treatment"),
        ),
        check(
            "public_project_cost_outcome",
            "pass" if cost["status"] == "available" else "pending",
            domain_message(cost, "reconciled public-project cost outcome"),
        ),
        check(
            "public_project_schedule_outcome",
            "pass" if schedule["status"] == "available" else "pending",
            domain_message(schedule, "baseline-to-actual public-project schedule outcome"),
        ),
        check(
            "regional_controls",
            "pass" if all(item["status"] == "available" for item in control_domains) else "pending",
            "All declared labour, construction-activity and grid controls are available."
            if all(item["status"] == "available" for item in control_domains)
            else "At least one declared control remains a candidate or has an explicit coverage gap.",
        ),
        check(
            "panel_assembly",
            "not_assessed",
            "No unit-period panel is assembled until both the authorizing treatment and outcome domains pass.",
        ),
        check(
            "cohort_overlap",
            "not_assessed",
            "Treated/control common support cannot be tested before panel assembly.",
        ),
        check(
            "pretrend_and_equivalence",
            "not_assessed",
            "Pre-treatment dynamics and equivalence bounds cannot be assessed before panel assembly.",
        ),
        check(
            "placebo_and_negative_controls",
            "not_assessed",
            "Placebo dates and negative-control outcomes cannot be run before panel assembly.",
        ),
        check(
            "leave_one_out_sensitivity",
            "not_assessed",
            "Region/event influence cannot be tested before an eligible estimation cohort exists.",
        ),
        check(
            "independent_modelling_review",
            "blocked",
            "Review cannot authorize an effect until the evidence and identification gates produce an eligible model package.",
        ),
    ]
    effect_ready = all(
        item["status"] == "pass"
        for item in readiness_checks
        if item["check_id"]
        in {
            "contract_and_source_lineage",
            "realized_ai_construction_treatment",
            "public_project_cost_outcome",
            "public_project_schedule_outcome",
            "regional_controls",
            "panel_assembly",
            "cohort_overlap",
            "pretrend_and_equivalence",
            "placebo_and_negative_controls",
            "leave_one_out_sensitivity",
            "independent_modelling_review",
        }
    )
    if effect_ready:
        raise ValidationError(
            "the readiness contract cannot authorize an effect without a separate estimator artifact"
        )

    output = {
        "schema_version": "1.0.0",
        "run_id": "AIIO_E2_IDENTIFICATION_READINESS_0_1",
        "contract_id": contract["contract_id"],
        "estimand_id": contract["estimand_id"],
        "analysis_status": "not_assessed",
        "evidence_status": "inferred_contract_audit",
        "contract_sha256": sha256_file(contract_path),
        "source_registry_sha256": sha256_file(registry_path),
        "registered_source_count": len(registry),
        "candidate_source_ids": sorted(
            {
                source_id
                for item in contract["data_domains"]
                for source_id in item["source_ids"]
            }
        ),
        "design": contract["design"],
        "treatment_contract": contract["treatment"],
        "outcome_contracts": contract["outcomes"],
        "domain_status": [
            {
                "domain_id": item["domain_id"],
                "role": item["role"],
                "status": item["status"],
                "source_ids": item["source_ids"],
                "available_variables": item["available_variables"],
                "missing_variables": item["missing_variables"],
                "limitation": item["limitation"],
            }
            for item in contract["data_domains"]
        ],
        "readiness_checks": readiness_checks,
        "publication_authorization": {
            "status": "withheld_missing_identification_panel",
            "ai_attributable_increment_authorized": False,
            "cost_escalation_percent": None,
            "cost_escalation_cad": None,
            "schedule_delay_days": None,
            "reason": (
                "Public data currently provide regional controls and useful proxies, but not a "
                "common realized AI-construction treatment plus estimate-to-outturn and "
                "baseline-to-actual public-project outcomes."
            ),
        },
        "graph_role": (
            "S3/PSPE maps mechanisms, priorities, bottlenecks and missing links. It does not "
            "supply the counterfactual or identify the E2 treatment effect."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


def validate_contract(contract: dict[str, Any], *, registry_ids: set[str]) -> None:
    if contract.get("schema_version") != "1.0.0":
        raise ValidationError("attribution contract must use schema_version 1.0.0")
    for key in (
        "contract_id",
        "estimand_id",
        "estimand",
        "unit_of_analysis",
        "geography_level",
        "frequency",
        "design",
        "treatment",
        "outcomes",
        "data_domains",
        "publication_authorization",
    ):
        if contract.get(key) in (None, "", [], {}):
            raise ValidationError(f"attribution contract is missing {key}")

    design = contract["design"]
    missing_design = REQUIRED_DESIGN_FIELDS - set(design)
    if missing_design:
        raise ValidationError(
            "attribution design is missing fields: " + ", ".join(sorted(missing_design))
        )
    if design["two_way_fixed_effects_event_study_primary"] is not False:
        raise ValidationError(
            "a conventional two-way fixed-effects event study cannot be the primary staggered estimator"
        )
    for field in (
        "anticipation_periods",
        "minimum_pre_treatment_quarters",
        "minimum_post_treatment_quarters",
        "minimum_treated_regions",
        "minimum_control_regions_per_cohort",
        "minimum_asset_classes",
    ):
        value = design[field]
        if not isinstance(value, int) or value < (0 if field == "anticipation_periods" else 1):
            raise ValidationError(f"attribution design field {field} is invalid")
    for field in (
        "leave_one_region_out_required",
        "leave_one_event_out_required",
        "negative_control_outcome_required",
        "placebo_event_dates_required",
        "pretrend_equivalence_assessment_required",
        "covariates_locked_before_outcome_analysis",
    ):
        if design[field] is not True:
            raise ValidationError(f"attribution design safeguard {field} must be true")

    treatment = contract["treatment"]
    authorizing = set(treatment.get("authorizing_measures", []))
    prohibited = set(treatment.get("prohibited_as_treatment", []))
    if not authorizing:
        raise ValidationError("attribution treatment needs at least one authorizing measure")
    if authorizing & PROHIBITED_TREATMENT_TOKENS:
        raise ValidationError("announcements, requests, scenarios and graph scores cannot authorize treatment")
    if not PROHIBITED_TREATMENT_TOKENS.issubset(prohibited):
        raise ValidationError("attribution treatment must explicitly prohibit non-realized quantities")

    outcomes = contract["outcomes"]
    outcome_ids = [item.get("outcome_id") for item in outcomes]
    if len(outcome_ids) != len(set(outcome_ids)):
        raise ValidationError("attribution outcome_id values must be unique")
    families = {item.get("family") for item in outcomes}
    if families != REQUIRED_OUTCOME_FAMILIES:
        raise ValidationError("attribution outcomes must define cost, schedule and procurement families")
    for item in outcomes:
        if not item.get("required_fields") or not item.get("publication_unit"):
            raise ValidationError(f"attribution outcome {item.get('outcome_id')} is incomplete")

    domains = contract["data_domains"]
    domain_ids = [item.get("domain_id") for item in domains]
    if len(domain_ids) != len(set(domain_ids)):
        raise ValidationError("attribution domain_id values must be unique")
    if set(domain_ids) != REQUIRED_DOMAIN_IDS:
        raise ValidationError(
            "attribution data domains must match the locked required domain set"
        )
    for item in domains:
        if item.get("status") not in ALLOWED_DOMAIN_STATUSES:
            raise ValidationError(f"invalid data-domain status for {item.get('domain_id')}")
        if item.get("role") not in ALLOWED_DOMAIN_ROLES:
            raise ValidationError(f"invalid data-domain role for {item.get('domain_id')}")
        for key in ("source_ids", "available_variables", "missing_variables"):
            if not isinstance(item.get(key), list):
                raise ValidationError(f"data domain {item.get('domain_id')} requires list field {key}")
        unknown = set(item["source_ids"]) - registry_ids
        if unknown:
            raise ValidationError(
                f"data domain {item['domain_id']} references unknown sources: {sorted(unknown)}"
            )
        if not item.get("limitation"):
            raise ValidationError(f"data domain {item.get('domain_id')} requires a limitation")

    authorization = contract["publication_authorization"]
    if authorization.get("ai_attributable_increment_authorized") is not False:
        raise ValidationError("an identification-readiness contract cannot authorize an AI increment")
    for field in ("cost_escalation_percent", "cost_escalation_cad", "schedule_delay_days"):
        if authorization.get(field) is not None:
            raise ValidationError(f"unidentified effect field must remain null: {field}")


def check(check_id: str, status: str, summary: str) -> dict[str, str]:
    return {"check_id": check_id, "status": status, "summary": summary}


def domain_message(domain: dict[str, Any], label: str) -> str:
    if domain["status"] == "available":
        return f"The {label} domain is available under the locked field contract."
    missing = ", ".join(domain["missing_variables"])
    return f"The {label} domain is {domain['status']}; missing: {missing}."


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return payload


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
