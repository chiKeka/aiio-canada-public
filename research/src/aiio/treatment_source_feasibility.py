from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .schemas import ValidationError


FEASIBILITY_ID = "AIIO_E2_TREATMENT_SOURCE_FEASIBILITY_0_1"
REQUIRED_GATES = (
    "ai_or_data_centre_specific",
    "construction_activity_specific",
    "realized_not_intended",
    "region_or_project_linkable",
    "quarterly_or_finer",
    "publicly_retrievable",
    "revision_provenance_available",
)
ALLOWED_ROLES = {
    "candidate_treatment",
    "activity_proxy",
    "operating_stock_context",
    "labour_context",
}


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repository_relative_path(path: Path) -> str:
    resolved = path.resolve()
    for parent in resolved.parents:
        if (parent / "data").is_dir() and (parent / "research").is_dir():
            return resolved.relative_to(parent).as_posix()
    return path.as_posix()


def validate_treatment_source_contract(
    contract: dict[str, Any], *, registry_ids: set[str]
) -> None:
    if contract.get("schema_version") != "1.0.0":
        raise ValidationError("treatment-source contract must use schema_version 1.0.0")
    if tuple(contract.get("required_authorizing_gates", [])) != REQUIRED_GATES:
        raise ValidationError("treatment-source contract changed the locked authorizing gates")

    candidates = contract.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValidationError("treatment-source contract needs candidates")
    candidate_ids = [item.get("candidate_id") for item in candidates]
    if any(not item for item in candidate_ids) or len(candidate_ids) != len(
        set(candidate_ids)
    ):
        raise ValidationError("treatment-source candidate IDs must be unique and non-blank")

    for candidate in candidates:
        if candidate.get("source_id") not in registry_ids:
            raise ValidationError(
                f"treatment-source candidate references unknown source: {candidate.get('source_id')}"
            )
        if candidate.get("analytical_role") not in ALLOWED_ROLES:
            raise ValidationError("treatment-source candidate has an invalid analytical role")
        gates = candidate.get("gate_assessment")
        if not isinstance(gates, dict) or tuple(gates) != REQUIRED_GATES:
            raise ValidationError("treatment-source candidate gate coverage is incomplete")
        if any(type(value) is not bool for value in gates.values()):
            raise ValidationError("treatment-source gate assessments must be boolean")
        eligible = all(gates.values())
        expected_status = "authorizing_candidate" if eligible else "excluded_non_authorizing"
        if candidate.get("authorizing_status") != expected_status:
            raise ValidationError("treatment-source authorizing status contradicts its gates")
        if not eligible and not candidate.get("exclusion_reason"):
            raise ValidationError("excluded treatment-source candidate needs a reason")
        if eligible and candidate.get("exclusion_reason") is not None:
            raise ValidationError("eligible treatment-source candidate cannot have an exclusion reason")

    boundary = contract.get("publication_boundary", {})
    eligible_count = sum(
        1
        for candidate in candidates
        if candidate["authorizing_status"] == "authorizing_candidate"
    )
    if boundary.get("current_authorizing_source_count") != eligible_count:
        raise ValidationError("publication boundary source count contradicts candidates")
    if boundary.get("treatment_authorized") is not (eligible_count > 0):
        raise ValidationError("publication boundary treatment authorization contradicts candidates")
    if eligible_count == 0 and boundary.get("authorizing_treatment_measure") is not None:
        raise ValidationError("a treatment measure cannot be published without an authorizing source")
    if eligible_count == 0 and any(
        boundary.get(field) is not None
        for field in ("ai_attributable_cost_effect", "ai_attributable_schedule_effect")
    ):
        raise ValidationError("an AI-attributable effect cannot be published without an authorizing source")


def build_treatment_source_feasibility(
    contract_path: Path, registry_path: Path
) -> dict[str, Any]:
    contract = _load_object(contract_path)
    registry = _load_object(registry_path)
    registry_by_id = {item["source_id"]: item for item in registry["sources"]}
    validate_treatment_source_contract(contract, registry_ids=set(registry_by_id))

    candidates = []
    for item in contract["candidates"]:
        failed_gates = [
            gate for gate in REQUIRED_GATES if not item["gate_assessment"][gate]
        ]
        candidates.append(
            {
                **item,
                "source_title": registry_by_id[item["source_id"]]["title"],
                "failed_gates": failed_gates,
                "passed_gate_count": len(REQUIRED_GATES) - len(failed_gates),
                "required_gate_count": len(REQUIRED_GATES),
            }
        )

    role_counts = Counter(item["analytical_role"] for item in candidates)
    authorizing = [
        item for item in candidates if item["authorizing_status"] == "authorizing_candidate"
    ]
    return {
        "feasibility_id": FEASIBILITY_ID,
        "schema_version": "1.0.0",
        "evidence_status": "observed_source_capability_with_inferred_eligibility",
        "input_manifest": {
            "contract_path": _repository_relative_path(contract_path),
            "contract_sha256": _sha256(contract_path),
            "registry_path": _repository_relative_path(registry_path),
            "registry_sha256": _sha256(registry_path),
        },
        "required_authorizing_gates": list(REQUIRED_GATES),
        "candidate_count": len(candidates),
        "analytical_role_counts": dict(sorted(role_counts.items())),
        "authorizing_candidate_count": len(authorizing),
        "candidates": candidates,
        "acquisition_decision": {
            "status": "ready_for_panel_intake" if authorizing else "no_authorizing_public_source_identified",
            "next_evidence_needed": contract["next_evidence_needed"],
            "search_boundary": contract["search_boundary"],
        },
        "publication_boundary": contract["publication_boundary"],
    }


def run_treatment_source_feasibility(
    contract_path: Path, registry_path: Path, output_path: Path
) -> dict[str, Any]:
    report = build_treatment_source_feasibility(contract_path, registry_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
