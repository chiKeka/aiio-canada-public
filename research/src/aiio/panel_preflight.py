from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .schemas import ValidationError


PREFLIGHT_ID = "AIIO_E2_PANEL_ACQUISITION_PREFLIGHT_0_1"
ALLOWED_REGION_ROLES = {"potential_treated", "potential_control"}
ALLOWED_RECEIPT_STATUSES = {
    "candidate_proxy",
    "candidate_outcome",
    "available_control",
}
ALLOWED_AUTHORIZING_STATUSES = {"non_authorizing", "control_only"}
REQUIRED_SCOPE_IDS = {
    "REALIZED_AI_CONSTRUCTION_TREATMENT",
    "PUBLIC_PROJECT_COST_OUTCOMES",
    "PUBLIC_PROJECT_SCHEDULE_OUTCOMES",
    "PROCUREMENT_COMPETITION",
}


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_project_path(root: Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValidationError("panel preflight artifact paths must stay inside the project")
    resolved = (root / candidate).resolve()
    if root.resolve() not in resolved.parents:
        raise ValidationError("panel preflight artifact path escaped the project")
    if not resolved.is_file():
        raise ValidationError(f"panel preflight evidence artifact is missing: {relative_path}")
    return resolved


def _json_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for token in path.split("."):
        if not isinstance(current, dict) or token not in current:
            raise ValidationError(f"panel preflight assertion path is missing: {path}")
        current = current[token]
    return current


def _scope_requirements(attribution: dict[str, Any]) -> dict[str, list[str]]:
    outcomes = {item["outcome_id"]: item for item in attribution["outcomes"]}
    return {
        "REALIZED_AI_CONSTRUCTION_TREATMENT": list(
            attribution["treatment"]["authorizing_measures"]
        ),
        "PUBLIC_PROJECT_COST_OUTCOMES": list(
            outcomes["PUBLIC_PROJECT_COST_CHANGE"]["required_fields"]
        ),
        "PUBLIC_PROJECT_SCHEDULE_OUTCOMES": list(
            outcomes["PUBLIC_PROJECT_SCHEDULE_CHANGE"]["required_fields"]
        ),
        "PROCUREMENT_COMPETITION": list(
            outcomes["PROCUREMENT_COMPETITION"]["required_fields"]
        ),
    }


def validate_panel_acquisition_contract(
    acquisition: dict[str, Any],
    attribution: dict[str, Any],
    *,
    registry_ids: set[str],
    root: Path,
) -> None:
    if acquisition.get("schema_version") != "1.0.0":
        raise ValidationError("panel acquisition contract must use schema_version 1.0.0")
    if acquisition.get("attribution_contract_id") != attribution.get("contract_id"):
        raise ValidationError("panel acquisition contract references the wrong attribution contract")

    design = attribution["design"]
    regions = acquisition.get("candidate_regions")
    if not isinstance(regions, list) or not regions:
        raise ValidationError("panel acquisition contract needs candidate regions")
    region_ids = [item.get("geography_id") for item in regions]
    if any(not value for value in region_ids) or len(region_ids) != len(set(region_ids)):
        raise ValidationError("panel acquisition candidate geography IDs must be unique and non-blank")
    if any(item.get("cohort_role") not in ALLOWED_REGION_ROLES for item in regions):
        raise ValidationError("panel acquisition candidate region has an invalid cohort role")
    role_counts = Counter(item["cohort_role"] for item in regions)
    if role_counts["potential_treated"] < design["minimum_treated_regions"]:
        raise ValidationError("panel acquisition scope has too few potential treated regions")
    if role_counts["potential_control"] < design["minimum_control_regions_per_cohort"]:
        raise ValidationError("panel acquisition scope has too few potential control regions")

    asset_classes = acquisition.get("target_asset_classes")
    if (
        not isinstance(asset_classes, list)
        or len(asset_classes) < design["minimum_asset_classes"]
        or len(asset_classes) != len(set(asset_classes))
        or any(not item for item in asset_classes)
    ):
        raise ValidationError("panel acquisition asset-class scope is incomplete")

    data_domains = {item["domain_id"]: item for item in attribution["data_domains"]}
    outcome_ids = {item["outcome_id"] for item in attribution["outcomes"]}
    allowed_scope_ids = set(data_domains) | outcome_ids
    receipts = acquisition.get("evidence_receipts")
    if not isinstance(receipts, list) or not receipts:
        raise ValidationError("panel acquisition contract needs evidence receipts")
    receipt_ids = [item.get("receipt_id") for item in receipts]
    if any(not value for value in receipt_ids) or len(receipt_ids) != len(set(receipt_ids)):
        raise ValidationError("panel acquisition receipt IDs must be unique and non-blank")

    for receipt in receipts:
        scope_id = receipt.get("domain_id")
        if scope_id not in allowed_scope_ids:
            raise ValidationError(f"panel acquisition receipt has unknown domain: {scope_id}")
        if receipt.get("evidence_status") not in ALLOWED_RECEIPT_STATUSES:
            raise ValidationError(f"panel acquisition receipt has invalid evidence status: {receipt_ids}")
        if receipt.get("authorizing_status") not in ALLOWED_AUTHORIZING_STATUSES:
            raise ValidationError("panel acquisition preflight cannot authorize treatment or outcomes")
        source_ids = receipt.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            raise ValidationError("panel acquisition receipt needs source IDs")
        unknown_sources = set(source_ids) - registry_ids
        if unknown_sources:
            raise ValidationError(
                f"panel acquisition receipt references unknown sources: {sorted(unknown_sources)}"
            )
        if scope_id in data_domains:
            unexpected = set(source_ids) - set(data_domains[scope_id]["source_ids"])
            if unexpected:
                raise ValidationError(
                    f"panel acquisition receipt source is outside its locked domain: {sorted(unexpected)}"
                )
        if not receipt.get("geography_ids") or not receipt.get("available_variables"):
            raise ValidationError("panel acquisition receipt needs geography and variable coverage")
        artifact_path = _safe_project_path(root, receipt.get("artifact_path", ""))
        artifact = _load_object(artifact_path)
        assertions = receipt.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            raise ValidationError("panel acquisition receipt needs artifact assertions")
        for assertion in assertions:
            json_path = assertion.get("json_path")
            if not json_path or "equals" not in assertion:
                raise ValidationError("panel acquisition assertion is incomplete")
            if _json_path(artifact, json_path) != assertion["equals"]:
                raise ValidationError(
                    f"panel acquisition evidence assertion failed: {receipt['receipt_id']}::{json_path}"
                )

    requirements = _scope_requirements(attribution)
    tasks = acquisition.get("acquisition_tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValidationError("panel acquisition contract needs acquisition tasks")
    task_ids = [item.get("task_id") for item in tasks]
    if any(not value for value in task_ids) or len(task_ids) != len(set(task_ids)):
        raise ValidationError("panel acquisition task IDs must be unique and non-blank")
    tasks_by_scope = {item.get("domain_id"): item for item in tasks}
    if set(tasks_by_scope) != REQUIRED_SCOPE_IDS:
        raise ValidationError("panel acquisition tasks must cover every authorizing scope")
    for scope_id, required_fields in requirements.items():
        task = tasks_by_scope[scope_id]
        if set(task.get("required_fields", [])) != set(required_fields):
            raise ValidationError(
                f"panel acquisition task does not cover the locked fields for {scope_id}"
            )
        if task.get("priority") not in {"P0", "P1", "P2"}:
            raise ValidationError("panel acquisition task priority is invalid")
        if not task.get("current_status") or not task.get("completion_rule"):
            raise ValidationError("panel acquisition task needs status and completion rule")
        if not isinstance(task.get("minimum_geography_count"), int) or task[
            "minimum_geography_count"
        ] < 1:
            raise ValidationError("panel acquisition task geography minimum is invalid")
        unknown_sources = set(task.get("candidate_source_ids", [])) - registry_ids
        if unknown_sources:
            raise ValidationError(
                f"panel acquisition task references unknown sources: {sorted(unknown_sources)}"
            )

    shortcuts = acquisition.get("prohibited_shortcuts")
    if not isinstance(shortcuts, list) or len(shortcuts) < 7:
        raise ValidationError("panel acquisition contract must preserve the prohibited shortcuts")
    shortcut_text = " ".join(shortcuts).lower()
    for token in ("announced capex", "requested or contracted mw", "permit value", "pspe graph"):
        if token not in shortcut_text:
            raise ValidationError(f"panel acquisition contract is missing prohibited shortcut: {token}")


def build_panel_acquisition_preflight(
    root: Path,
    attribution_contract_path: Path,
    acquisition_contract_path: Path,
    registry_path: Path,
) -> dict[str, Any]:
    attribution = _load_object(attribution_contract_path)
    acquisition = _load_object(acquisition_contract_path)
    registry = _load_object(registry_path)
    registry_ids = {item["source_id"] for item in registry["sources"]}
    validate_panel_acquisition_contract(
        acquisition,
        attribution,
        registry_ids=registry_ids,
        root=root,
    )

    requirements = _scope_requirements(attribution)
    receipts: list[dict[str, Any]] = []
    for receipt in acquisition["evidence_receipts"]:
        artifact_path = _safe_project_path(root, receipt["artifact_path"])
        receipts.append(
            {
                "receipt_id": receipt["receipt_id"],
                "domain_id": receipt["domain_id"],
                "geography_ids": receipt["geography_ids"],
                "source_ids": receipt["source_ids"],
                "artifact_path": receipt["artifact_path"],
                "artifact_sha256": _sha256(artifact_path),
                "evidence_status": receipt["evidence_status"],
                "authorizing_status": receipt["authorizing_status"],
                "available_variables": receipt["available_variables"],
                "assertion_count": len(receipt["assertions"]),
                "assertions_passed": True,
            }
        )

    receipt_counts = Counter(item["domain_id"] for item in receipts)
    authorizing_counts = Counter(
        item["domain_id"]
        for item in receipts
        if item["authorizing_status"] not in {"non_authorizing", "control_only"}
    )
    scope_coverage = []
    for scope_id in sorted(REQUIRED_SCOPE_IDS):
        scope_receipts = [item for item in receipts if item["domain_id"] == scope_id]
        scope_coverage.append(
            {
                "domain_id": scope_id,
                "required_field_count": len(requirements[scope_id]),
                "candidate_receipt_count": receipt_counts[scope_id],
                "candidate_variable_count": len(
                    {
                        variable
                        for item in scope_receipts
                        for variable in item["available_variables"]
                    }
                ),
                "authorizing_receipt_count": authorizing_counts[scope_id],
                "eligibility_status": "pending_authorizing_evidence",
            }
        )

    design = attribution["design"]
    role_counts = Counter(
        item["cohort_role"] for item in acquisition["candidate_regions"]
    )
    required_field_instance_count = sum(len(fields) for fields in requirements.values())
    covered_task_field_instance_count = sum(
        len(item["required_fields"]) for item in acquisition["acquisition_tasks"]
    )
    evidence_manifest = {
        item["artifact_path"]: item["artifact_sha256"] for item in receipts
    }

    return {
        "schema_version": "1.0.0",
        "preflight_id": PREFLIGHT_ID,
        "contract_id": acquisition["contract_id"],
        "attribution_contract_id": attribution["contract_id"],
        "analysis_status": "not_assessed",
        "evidence_status": "inferred_preflight_from_hash_locked_receipts",
        "input_manifest": {
            "attribution_contract_path": str(attribution_contract_path.relative_to(root)),
            "attribution_contract_sha256": _sha256(attribution_contract_path),
            "acquisition_contract_path": str(acquisition_contract_path.relative_to(root)),
            "acquisition_contract_sha256": _sha256(acquisition_contract_path),
            "source_registry_path": str(registry_path.relative_to(root)),
            "source_registry_sha256": _sha256(registry_path),
            "code_sha256": _sha256(Path(__file__)),
            "evidence_artifact_sha256": evidence_manifest,
        },
        "design_thresholds": {
            "minimum_pre_treatment_quarters": design["minimum_pre_treatment_quarters"],
            "minimum_post_treatment_quarters": design["minimum_post_treatment_quarters"],
            "anticipation_periods": design["anticipation_periods"],
            "minimum_treated_regions": design["minimum_treated_regions"],
            "minimum_control_regions_per_cohort": design[
                "minimum_control_regions_per_cohort"
            ],
            "minimum_asset_classes": design["minimum_asset_classes"],
        },
        "candidate_scope": {
            "region_count": len(acquisition["candidate_regions"]),
            "potential_treated_region_count": role_counts["potential_treated"],
            "potential_control_region_count": role_counts["potential_control"],
            "asset_class_count": len(acquisition["target_asset_classes"]),
            "regions": acquisition["candidate_regions"],
            "asset_classes": acquisition["target_asset_classes"],
            "candidate_does_not_mean_eligible": True,
        },
        "current_eligibility": {
            "authorizing_treated_region_count": 0,
            "eligible_control_region_count": 0,
            "eligible_asset_class_count": 0,
            "assembled_panel_row_count": 0,
            "cohort_overlap_assessed": False,
            "pretrend_equivalence_assessed": False,
            "estimator_run_authorized": False,
        },
        "field_gap_summary": {
            "authorizing_scope_count": len(REQUIRED_SCOPE_IDS),
            "required_field_instance_count": required_field_instance_count,
            "acquisition_task_field_instance_count": covered_task_field_instance_count,
            "uncovered_required_field_instance_count": 0,
            "complete_authorizing_scope_count": 0,
        },
        "scope_coverage": scope_coverage,
        "evidence_receipts": receipts,
        "acquisition_queue": acquisition["acquisition_tasks"],
        "prohibited_shortcuts": acquisition["prohibited_shortcuts"],
        "panel_assembly": {
            "status": "not_assessed_missing_authorizing_treatment_and_outcomes",
            "reason": (
                "The preflight inventories candidate evidence and covers every locked field with an acquisition task, "
                "but zero regions, asset classes or panel rows are eligible for estimation."
            ),
        },
        "publication_boundary": {
            "candidate_scope_publication_authorized": True,
            "evidence_gap_publication_authorized": True,
            "effect_estimation_authorized": False,
            "ai_attributable_cost_escalation_percent": None,
            "ai_attributable_cost_escalation_cad": None,
            "ai_attributable_schedule_delay_days": None,
        },
        "pspe_role": (
            "S3/PSPE is used to prioritize missing treatment and outcome nodes and the ties needed for a testable panel. "
            "It does not fill missing fields, define treatment dose or authorize an effect."
        ),
    }


def run_panel_acquisition_preflight(
    root: Path,
    attribution_contract_path: Path,
    acquisition_contract_path: Path,
    registry_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    report = build_panel_acquisition_preflight(
        root,
        attribution_contract_path,
        acquisition_contract_path,
        registry_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
