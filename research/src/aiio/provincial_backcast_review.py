from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .schemas import ValidationError


PACKAGE_ID = "AIIO_CA_PROVINCE_LINKED_BCPI_REVIEW_PACKAGE_0_1"
ALLOWED_REVIEWER_TYPES = {
    "human_subject_matter_expert",
    "claude_cli",
    "grok_cli",
}
CRITERIA = [
    {
        "criterion_id": "source_lineage",
        "question": "Do both normalized inputs reconcile to the locked Statistics Canada BCPI source and retain their distinct province/CMA geographies?",
    },
    {
        "criterion_id": "evidence_status_boundary",
        "question": "Are official provincial observations preserved and every pre-2017 bridge value unambiguously labelled inferred and not official?",
    },
    {
        "criterion_id": "anchor_formula",
        "question": "Is the single-anchor scaling formula implemented deterministically without using future provincial values to alter pre-anchor growth?",
    },
    {
        "criterion_id": "reference_market_choice",
        "question": "Are Montréal, Toronto and Vancouver defensible, sufficiently disclosed historical reference markets for the narrow research-validation use?",
    },
    {
        "criterion_id": "overlap_diagnostic",
        "question": "Is the predeclared 3% overlap MAPE screen correctly calculated, interpreted and insufficient on its own to establish historical representativeness?",
    },
    {
        "criterion_id": "splice_integrity",
        "question": "Are quarter continuity, anchor continuity, units, index base, source IDs and DGUID lineage preserved across the inferred/observed splice?",
    },
    {
        "criterion_id": "forecast_validation",
        "question": "Does the unchanged rolling-origin protocol remain temporally valid when applied to the mixed inferred/observed history?",
    },
    {
        "criterion_id": "fail_closed_outputs",
        "question": "Do failed and unassessed horizons remain null and do all internal passes remain withheld from project-cost translation?",
    },
    {
        "criterion_id": "reproducibility",
        "question": "Do the hashes, deterministic artifacts and tests reproduce all 1,752 observations, 12 diagnostics and 60 horizon dispositions?",
    },
    {
        "criterion_id": "public_claim_boundary",
        "question": "Would any authorization remain limited to research display of the bridge, with no official-history, project-cost, AI-effect or province-wide representativeness claim?",
    },
]
REVIEW_FILES = [
    ("official_province_input", "data/processed/bcpi_reference_bc_on_qc.csv"),
    ("cma_reference_input", "data/processed/bcpi_reference_van_tor_mtl.csv"),
    ("linked_history", "data/processed/bcpi_province_linked_history_bc_on_qc.csv"),
    (
        "model_artifact",
        "data/model-runs/bc_on_qc_province_linked_reference_baseline_v0.1.json",
    ),
    ("backcast_implementation", "research/src/aiio/provincial_backcast.py"),
    ("forecast_implementation", "research/src/aiio/calibration.py"),
    ("review_packager", "research/src/aiio/provincial_backcast_review.py"),
    ("artifact_tests", "research/tests/test_provincial_backcast.py"),
    ("method_protocol", "docs/methodology/province-linked-bcpi-backcast.md"),
    ("product_contract", "docs/product/decision-mode.md"),
]


def build_province_linked_review_package(
    root: Path, output_json_path: Path, output_prompt_path: Path
) -> dict[str, Any]:
    root = root.resolve()
    artifact_path = (
        root
        / "data/model-runs/bc_on_qc_province_linked_reference_baseline_v0.1.json"
    )
    artifact = _read_object(artifact_path, "province-linked model artifact")
    _validate_artifact(root, artifact)
    manifest = []
    for role, relative_path in REVIEW_FILES:
        path = root / relative_path
        if not path.is_file():
            raise ValidationError(f"province-linked review input is missing: {relative_path}")
        manifest.append(
            {"role": role, "path": relative_path, "sha256": _sha256(path)}
        )

    package = {
        "schema_version": "1.0.0",
        "package_id": PACKAGE_ID,
        "review_status": "pending_independent_review",
        "review_scope": "BC, Ontario and Quebec province-linked BCPI historical bridge and held-out reference validation",
        "artifact_as_of_date": artifact["as_of_date"],
        "model_id": artifact["model_id"],
        "model_artifact_sha256": _sha256(artifact_path),
        "input_manifest": manifest,
        "facts_to_reconcile": {
            "total_observation_count": 1752,
            "inferred_observation_count": 1296,
            "official_observation_count": 456,
            "diagnostic_count": 12,
            "maximum_overlap_mape_percent": max(
                item["overlap_mape_percent"]
                for item in artifact["backcast_method"]["diagnostics"]
            ),
            "horizon_status_counts": artifact["publication_summary"][
                "horizon_status_counts"
            ],
            "gate_passing_geographies": ["PR_59"],
        },
        "required_criteria": [
            {**criterion, "required": True} for criterion in CRITERIA
        ],
        "reviewer_instructions": [
            "Perform a read-only review and verify every manifest hash before forming a verdict.",
            "Run the declared tests or record why they were not run; passing tests do not substitute for methodological judgment.",
            "Disposition every criterion with file-, row-, formula- or test-backed notes.",
            "Any conditional/failed criterion or unresolved critical/high finding requires a hold verdict.",
            "A pass may recommend research display of the labelled bridge only; it cannot authorize a public projection, project-cost translation, AI effect or official pre-2017 provincial history.",
            "Return a separate JSON verdict and do not edit the package, artifact or governance gate.",
        ],
        "test_commands": [
            "PYTHONPATH=research/src python3 -m unittest research.tests.test_provincial_backcast -v",
            "PYTHONPATH=research/src python3 -m aiio.cli --root . audit-program-readiness",
        ],
        "verdict_contract": {
            "schema_version": "1.0.0",
            "package_id": PACKAGE_ID,
            "package_sha256": "sha256:<hash of this package file>",
            "reviewer": {
                "name": "<nonblank>",
                "organization": "<nonblank or independent>",
                "reviewer_type": sorted(ALLOWED_REVIEWER_TYPES),
                "reviewer_is_not_model_author": True,
                "independence_declaration": "<nonblank>",
                "conflicts_of_interest": "<none or disclosure>",
                "tool_version": "<version or not_applicable>",
            },
            "reviewed_at": "YYYY-MM-DD",
            "tests_run": [
                {
                    "command": "<command>",
                    "status": "pass|fail|not_run",
                    "notes": "<nonblank>",
                }
            ],
            "criteria": [
                {
                    "criterion_id": item["criterion_id"],
                    "status": "pass|conditional|fail",
                    "notes": "<evidence-backed notes>",
                }
                for item in CRITERIA
            ],
            "findings": [
                {
                    "finding_id": "<unique>",
                    "criterion_id": "<required criterion ID>",
                    "severity": "critical|high|medium|low|observation",
                    "status": "open|resolved|accepted_limitation",
                    "summary": "<nonblank>",
                    "evidence": "<file/line or test evidence>",
                }
            ],
            "overall_verdict": "pass|hold",
            "publication_recommendation": "authorize_research_display_only|withhold",
            "claim_boundary_acknowledged": True,
            "summary": "<nonblank>",
        },
        "publication_boundary": {
            "independent_review_complete": False,
            "province_linked_backcast_authorized_for_research_display": True,
            "public_projection_authorized": False,
            "project_cost_translation_authorized": False,
            "ai_attributable_effect_authorized": False,
            "reason": "This deterministic packet is a review instrument, not an independent verdict.",
        },
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    output_prompt_path.parent.mkdir(parents=True, exist_ok=True)
    output_prompt_path.write_text(
        _render_prompt(package, output_json_path, root), encoding="utf-8"
    )
    return package


def validate_province_linked_review_verdict(
    package_path: Path, verdict_path: Path
) -> dict[str, Any]:
    package = _read_object(package_path, "province-linked review package")
    verdict = _read_object(verdict_path, "province-linked review verdict")
    if package.get("package_id") != PACKAGE_ID:
        raise ValidationError("unexpected province-linked review package ID")
    if verdict.get("schema_version") != "1.0.0":
        raise ValidationError("province-linked verdict schema version mismatch")
    if verdict.get("package_id") != PACKAGE_ID:
        raise ValidationError("province-linked verdict package ID mismatch")
    if verdict.get("package_sha256") != _sha256(package_path):
        raise ValidationError("province-linked verdict does not lock the exact package")

    reviewer = verdict.get("reviewer")
    if not isinstance(reviewer, dict):
        raise ValidationError("province-linked verdict requires a reviewer object")
    for field in (
        "name",
        "organization",
        "independence_declaration",
        "conflicts_of_interest",
        "tool_version",
    ):
        if not isinstance(reviewer.get(field), str) or not reviewer[field].strip():
            raise ValidationError(f"reviewer {field} must be nonblank")
    if reviewer.get("reviewer_type") not in ALLOWED_REVIEWER_TYPES:
        raise ValidationError("province-linked reviewer type is not allowed")
    if reviewer.get("reviewer_is_not_model_author") is not True:
        raise ValidationError("reviewer must affirm separation from model authorship")
    try:
        date.fromisoformat(verdict["reviewed_at"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValidationError("reviewed_at must be an ISO date") from error

    expected_ids = {item["criterion_id"] for item in CRITERIA}
    criteria = verdict.get("criteria")
    if not isinstance(criteria, list) or len(criteria) != len(expected_ids):
        raise ValidationError("province-linked verdict must contain every criterion")
    statuses = {}
    for item in criteria:
        if not isinstance(item, dict):
            raise ValidationError("province-linked criterion is malformed")
        criterion_id = item.get("criterion_id")
        if criterion_id not in expected_ids or criterion_id in statuses:
            raise ValidationError("province-linked criterion is unknown or duplicated")
        if item.get("status") not in {"pass", "conditional", "fail"}:
            raise ValidationError("province-linked criterion status is invalid")
        if not isinstance(item.get("notes"), str) or not item["notes"].strip():
            raise ValidationError("province-linked criterion notes must be nonblank")
        statuses[criterion_id] = item["status"]

    tests_run = verdict.get("tests_run")
    if not isinstance(tests_run, list) or not tests_run:
        raise ValidationError("province-linked verdict must record test dispositions")
    for test in tests_run:
        if (
            not isinstance(test, dict)
            or not isinstance(test.get("command"), str)
            or not test["command"].strip()
            or test.get("status") not in {"pass", "fail", "not_run"}
            or not isinstance(test.get("notes"), str)
            or not test["notes"].strip()
        ):
            raise ValidationError("province-linked test disposition is malformed")

    unresolved_high = False
    finding_ids: set[str] = set()
    findings = verdict.get("findings")
    if not isinstance(findings, list):
        raise ValidationError("province-linked findings must be a list")
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValidationError("province-linked finding is malformed")
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id.strip() or finding_id in finding_ids:
            raise ValidationError("province-linked finding IDs must be unique")
        finding_ids.add(finding_id)
        if finding.get("criterion_id") not in expected_ids:
            raise ValidationError("province-linked finding criterion is unknown")
        if finding.get("severity") not in {
            "critical",
            "high",
            "medium",
            "low",
            "observation",
        } or finding.get("status") not in {"open", "resolved", "accepted_limitation"}:
            raise ValidationError("province-linked finding disposition is invalid")
        for field in ("summary", "evidence"):
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                raise ValidationError("province-linked finding text must be nonblank")
        if finding["severity"] in {"critical", "high"} and finding["status"] == "open":
            unresolved_high = True

    overall = verdict.get("overall_verdict")
    recommendation = verdict.get("publication_recommendation")
    if overall not in {"pass", "hold"}:
        raise ValidationError("province-linked overall verdict is invalid")
    if recommendation not in {"authorize_research_display_only", "withhold"}:
        raise ValidationError("province-linked recommendation is invalid")
    if verdict.get("claim_boundary_acknowledged") is not True:
        raise ValidationError("province-linked claim boundary must be acknowledged")
    if not isinstance(verdict.get("summary"), str) or not verdict["summary"].strip():
        raise ValidationError("province-linked verdict summary must be nonblank")
    if overall == "pass" and (
        any(status != "pass" for status in statuses.values())
        or unresolved_high
        or recommendation != "authorize_research_display_only"
    ):
        raise ValidationError("province-linked pass verdict is internally inconsistent")
    if overall == "hold" and recommendation != "withhold":
        raise ValidationError("province-linked hold verdict must withhold")
    return {
        "status": "passed",
        "gate_status": "passed" if overall == "pass" else "held",
        "publication_recommendation": recommendation,
        "package_sha256": _sha256(package_path),
    }


def _validate_artifact(root: Path, artifact: dict[str, Any]) -> None:
    if artifact.get("model_id") != "AIIO_CA_BC_ON_QC_PROVINCE_LINKED_REFERENCE_BASELINE_0_1":
        raise ValidationError("province-linked review received an unexpected artifact")
    if artifact.get("backcast_output_sha256") != _sha256(
        root / "data/processed/bcpi_province_linked_history_bc_on_qc.csv",
        prefixed=False,
    ):
        raise ValidationError("province-linked history hash is stale")
    diagnostics = artifact.get("backcast_method", {}).get("diagnostics", [])
    if len(diagnostics) != 12 or any(item.get("status") != "pass" for item in diagnostics):
        raise ValidationError("province-linked diagnostic inventory changed")
    if artifact.get("publication_summary", {}).get("horizon_status_counts") != {
        "gate_failed": 36,
        "gate_passed": 9,
        "not_assessed": 15,
    }:
        raise ValidationError("province-linked horizon inventory changed")
    boundary = artifact.get("publication_authorization", {})
    if (
        boundary.get("public_projection_authorized") is not False
        or boundary.get("project_cost_translation_authorized") is not False
        or boundary.get("ai_attributable_effect_authorized") is not False
    ):
        raise ValidationError("province-linked review requires a withheld artifact")


def _render_prompt(package: dict[str, Any], package_path: Path, root: Path) -> str:
    try:
        display_path = package_path.resolve().relative_to(root).as_posix()
    except ValueError:
        display_path = package_path.name
    manifest = "\n".join(
        f"- `{item['path']}` — `{item['sha256']}`"
        for item in package["input_manifest"]
    )
    criteria = "\n".join(
        f"{index}. `{item['criterion_id']}` — {item['question']}"
        for index, item in enumerate(package["required_criteria"], start=1)
    )
    return (
        "# Independent review prompt — province-linked BCPI bridge\n\n"
        "Act as an independent modelling reviewer. Work read-only: do not edit artifacts, alter governance gates or authorize publication directly. Verify the exact packet and every manifest hash before reviewing.\n\n"
        f"Packet: `{display_path}`\n"
        f"Packet SHA-256: `{_sha256(package_path)}`\n\n"
        "## Locked inputs\n\n"
        f"{manifest}\n\n"
        "## Required criteria\n\n"
        f"{criteria}\n\n"
        "Run the declared tests where possible and return only one JSON object matching `verdict_contract`. A pass is prohibited when any criterion is conditional or failed or an unresolved critical/high finding exists. Even a pass may recommend research display only; official pre-2017 province history, public projections, project-cost translation and AI attribution remain prohibited.\n"
    )


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"unable to read {label}: {error}") from error
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object")
    return value


def _sha256(path: Path, *, prefixed: bool = True) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}" if prefixed else digest
