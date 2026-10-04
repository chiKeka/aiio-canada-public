from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .schemas import ValidationError


PACKAGE_ID = "AIIO_AB_REFERENCE_COST_REVIEW_PACKAGE_0_1"
ALLOWED_REVIEWER_TYPES = {
    "human_subject_matter_expert",
    "claude_cli",
    "grok_cli",
}
ALLOWED_CRITERION_STATUSES = {"pass", "conditional", "fail"}
ALLOWED_FINDING_SEVERITIES = {"critical", "high", "medium", "low", "observation"}
ALLOWED_FINDING_STATUSES = {"open", "resolved", "accepted_limitation"}

REVIEW_CRITERIA = [
    {
        "criterion_id": "estimand_boundary",
        "question": "Does the artifact consistently describe a BCPI model-building reference-index path rather than a project-cost or AI-effect forecast?",
        "required": True,
    },
    {
        "criterion_id": "temporal_integrity",
        "question": "Are every candidate selection, error-band estimate and validation decision based only on information available at each rolling origin?",
        "required": True,
    },
    {
        "criterion_id": "predeclared_model_selection",
        "question": "Are candidates, lookback, tie rule, horizons, partitioning and gates fixed in code without post-outcome tuning?",
        "required": True,
    },
    {
        "criterion_id": "validation_adequacy",
        "question": "Are the locked origin counts, error gates and flat-benchmark comparison appropriate for the narrow baseline-only claim?",
        "required": True,
    },
    {
        "criterion_id": "interval_semantics",
        "question": "Are the p10/p90 bands correctly constructed and described as empirical historical error ranges, not confidence or probability intervals?",
        "required": True,
    },
    {
        "criterion_id": "fail_closed_outputs",
        "question": "Do failed or unassessed horizons remain null everywhere downstream, including project-cost translation and the public surface?",
        "required": True,
    },
    {
        "criterion_id": "reference_class_mapping",
        "question": "Are the four building reference mappings and Calgary/Edmonton geographic limits defensible and sufficiently disclosed?",
        "required": True,
    },
    {
        "criterion_id": "graph_unit_separation",
        "question": "Is the dimensionless PSPE-informed graph kept separate from BCPI percentages and project dollars?",
        "required": True,
    },
    {
        "criterion_id": "reproducibility",
        "question": "Do locked inputs, implementation hash, deterministic artifact and tests provide enough evidence to reproduce the exact run?",
        "required": True,
    },
    {
        "criterion_id": "public_claim_boundary",
        "question": "Would authorization remain limited to individual gate-passing E1 horizons, with no E2, province-wide, long-horizon health/school or project-budget claim?",
        "required": True,
    },
]

REVIEW_FILES = [
    ("normalized_input", "data/processed/bcpi_alberta.csv"),
    ("model_artifact", "data/model-runs/alberta_bcpi_reference_baseline_v0.1.json"),
    ("implementation", "research/src/aiio/calibration.py"),
    ("review_packager", "research/src/aiio/model_review.py"),
    ("unit_tests", "research/tests/test_calibration.py"),
    ("artifact_tests", "research/tests/test_calibration_artifact.py"),
    ("method_protocol", "docs/methodology/calibration-protocol.md"),
    ("review_protocol", "docs/methodology/reference-cost-independent-review.md"),
    ("pspe_boundary_audit", "docs/methodology/pspe-integration-audit.md"),
    ("product_contract", "docs/product/decision-mode.md"),
]


def sha256_file(path: Path, *, prefixed: bool = True) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}" if prefixed else digest


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a JSON object")
    return value


def _relative_file_manifest(root: Path) -> list[dict[str, str]]:
    manifest: list[dict[str, str]] = []
    for role, relative_path in REVIEW_FILES:
        path = root / relative_path
        if not path.is_file():
            raise ValidationError(f"review input is missing: {relative_path}")
        manifest.append(
            {
                "role": role,
                "path": relative_path,
                "sha256": sha256_file(path),
            }
        )
    return manifest


def _validate_baseline_lock(root: Path, baseline: dict[str, Any]) -> None:
    if baseline.get("model_id") != "AIIO_AB_BCPI_REFERENCE_BASELINE_0_1":
        raise ValidationError("review package received an unexpected model artifact")
    if baseline.get("input_sha256") != sha256_file(
        root / "data/processed/bcpi_alberta.csv", prefixed=False
    ):
        raise ValidationError("baseline input hash does not match normalized BCPI")
    if baseline.get("code_sha256") != sha256_file(
        root / "research/src/aiio/calibration.py", prefixed=False
    ):
        raise ValidationError("baseline implementation hash is missing or stale")
    authorization = baseline.get("publication_authorization", {})
    if authorization.get("public_projection_authorized") is not False:
        raise ValidationError("review package must be built from an unauthorized baseline")
    statuses = baseline.get("publication_summary", {}).get(
        "horizon_status_counts", {}
    )
    if sum(statuses.values()) != 40 or statuses.get("gate_passed") != 1:
        raise ValidationError("baseline horizon status inventory changed")


def build_reference_cost_review_package(
    root: Path, output_json_path: Path, output_prompt_path: Path
) -> dict[str, Any]:
    root = root.resolve()
    baseline_path = root / "data/model-runs/alberta_bcpi_reference_baseline_v0.1.json"
    baseline = _read_object(baseline_path, "Alberta reference-cost baseline")
    _validate_baseline_lock(root, baseline)
    manifest = _relative_file_manifest(root)
    passed_horizons = [
        {
            "asset_class": result["asset_class"],
            "geography_id": result["geography_id"],
            "horizon_years": horizon["horizon_years"],
            "selected_method": horizon["selected_method"],
            "projected_cumulative_change_percent": horizon[
                "projected_cumulative_change_percent"
            ],
        }
        for result in baseline["reference_class_results"]
        for horizon in result["horizons"]
        if horizon["status"] == "gate_passed"
    ]
    package = {
        "schema_version": "1.0.0",
        "package_id": PACKAGE_ID,
        "review_status": "pending_independent_review",
        "review_scope": "Alberta BCPI reference-class baseline E1 only",
        "artifact_as_of_date": baseline["as_of_date"],
        "model_id": baseline["model_id"],
        "model_artifact_sha256": sha256_file(baseline_path),
        "input_manifest": manifest,
        "facts_to_reconcile": {
            "reference_series_count": 8,
            "horizon_result_count": 40,
            "horizon_status_counts": baseline["publication_summary"][
                "horizon_status_counts"
            ],
            "gate_passing_horizons": passed_horizons,
        },
        "required_criteria": REVIEW_CRITERIA,
        "reviewer_instructions": [
            "Perform a read-only review of every input-manifest file and verify each hash before forming a verdict.",
            "Run the declared research tests or explain why they could not be run; green tests do not substitute for methodological judgment.",
            "Record a criterion-level status and evidence-backed note for every required criterion.",
            "Use findings for defects or limitations; unresolved critical or high findings prohibit a pass verdict.",
            "A pass can recommend authorization only for the individually gate-passing E1 horizon listed in facts_to_reconcile.",
            "Do not authorize E2, long-horizon health or school projections, project-budget translation, province-wide claims or graph-score monetization.",
            "Return a separate JSON verdict conforming to verdict_contract; do not edit the model artifact or package.",
        ],
        "test_commands": [
            "PYTHONPATH=research/src python3 -m unittest research/tests/test_calibration.py research/tests/test_calibration_artifact.py -v",
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
            "tests_run": [{"command": "<command>", "status": "pass|fail|not_run", "notes": "<nonblank>"}],
            "criteria": [
                {
                    "criterion_id": item["criterion_id"],
                    "status": "pass|conditional|fail",
                    "notes": "<evidence-backed notes>",
                }
                for item in REVIEW_CRITERIA
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
            "publication_recommendation": "authorize_baseline_only|withhold",
            "claim_boundary_acknowledged": True,
            "summary": "<nonblank>",
        },
        "publication_boundary": {
            "independent_review_complete": False,
            "public_projection_authorized": False,
            "ai_attributable_effect_authorized": False,
            "project_cost_translation_authorized": False,
            "reason": "This deterministic packet is a review instrument, not a completed independent verdict.",
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


def _render_prompt(
    package: dict[str, Any], package_path: Path, root: Path
) -> str:
    try:
        display_path = package_path.resolve().relative_to(root).as_posix()
    except ValueError:
        display_path = package_path.name
    criteria = "\n".join(
        f"{index}. `{item['criterion_id']}` — {item['question']}"
        for index, item in enumerate(package["required_criteria"], start=1)
    )
    manifest = "\n".join(
        f"- `{item['path']}` — `{item['sha256']}`"
        for item in package["input_manifest"]
    )
    return (
        "# Independent review prompt — Alberta reference-cost baseline\n\n"
        "Act as an independent modelling reviewer. Perform a read-only review; do not edit files, alter gates, authorize publication directly or supply replacement parameters. Verify the exact packet and input hashes before reviewing.\n\n"
        f"Packet: `{display_path}`\n"
        f"Packet SHA-256: `{sha256_file(package_path)}`\n\n"
        "## Locked inputs\n\n"
        f"{manifest}\n\n"
        "## Required criteria\n\n"
        f"{criteria}\n\n"
        "Run the packet's declared tests where possible. Return only one JSON object matching `verdict_contract`. A pass is prohibited if any required criterion is conditional or failed, or if any critical/high finding remains open. Even a pass may recommend only the single listed gate-passing E1 horizon; every E2, project-budget, graph monetization, long-horizon health/school and province-wide claim remains withheld.\n"
    )


def validate_reference_cost_review_verdict(
    package_path: Path, verdict_path: Path
) -> dict[str, Any]:
    package = _read_object(package_path, "reference-cost review package")
    verdict = _read_object(verdict_path, "reference-cost review verdict")
    if package.get("package_id") != PACKAGE_ID:
        raise ValidationError("unexpected reference-cost review package ID")
    if verdict.get("schema_version") != "1.0.0":
        raise ValidationError("review verdict schema version mismatch")
    if verdict.get("package_id") != PACKAGE_ID:
        raise ValidationError("review verdict package ID mismatch")
    if verdict.get("package_sha256") != sha256_file(package_path):
        raise ValidationError("review verdict does not lock the exact package")

    reviewer = verdict.get("reviewer")
    if not isinstance(reviewer, dict):
        raise ValidationError("review verdict requires a reviewer object")
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
        raise ValidationError("reviewer type is not allowed")
    if reviewer.get("reviewer_is_not_model_author") is not True:
        raise ValidationError("reviewer must affirm separation from model authorship")
    try:
        date.fromisoformat(verdict["reviewed_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError("reviewed_at must be an ISO date") from exc

    expected_ids = {item["criterion_id"] for item in REVIEW_CRITERIA}
    criteria = verdict.get("criteria")
    if not isinstance(criteria, list) or len(criteria) != len(expected_ids):
        raise ValidationError("review verdict must contain every criterion exactly once")
    by_id: dict[str, dict[str, Any]] = {}
    for item in criteria:
        if not isinstance(item, dict) or item.get("criterion_id") in by_id:
            raise ValidationError("review criterion is malformed or duplicated")
        criterion_id = item.get("criterion_id")
        if criterion_id not in expected_ids:
            raise ValidationError("review verdict contains an unknown criterion")
        if item.get("status") not in ALLOWED_CRITERION_STATUSES:
            raise ValidationError("review criterion status is invalid")
        if not isinstance(item.get("notes"), str) or not item["notes"].strip():
            raise ValidationError("review criterion notes must be nonblank")
        by_id[criterion_id] = item
    if set(by_id) != expected_ids:
        raise ValidationError("review verdict criterion coverage changed")

    tests_run = verdict.get("tests_run")
    if not isinstance(tests_run, list) or not tests_run:
        raise ValidationError("review verdict must record at least one test disposition")
    for test in tests_run:
        if (
            not isinstance(test, dict)
            or not isinstance(test.get("command"), str)
            or not test["command"].strip()
            or test.get("status") not in {"pass", "fail", "not_run"}
            or not isinstance(test.get("notes"), str)
            or not test["notes"].strip()
        ):
            raise ValidationError("review test disposition is malformed")

    findings = verdict.get("findings")
    if not isinstance(findings, list):
        raise ValidationError("review findings must be a list")
    finding_ids: set[str] = set()
    unresolved_high = False
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValidationError("review finding must be an object")
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id.strip() or finding_id in finding_ids:
            raise ValidationError("review finding IDs must be unique and nonblank")
        finding_ids.add(finding_id)
        if finding.get("criterion_id") not in expected_ids:
            raise ValidationError("review finding references an unknown criterion")
        if finding.get("severity") not in ALLOWED_FINDING_SEVERITIES:
            raise ValidationError("review finding severity is invalid")
        if finding.get("status") not in ALLOWED_FINDING_STATUSES:
            raise ValidationError("review finding status is invalid")
        for field in ("summary", "evidence"):
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                raise ValidationError(f"review finding {field} must be nonblank")
        if finding["severity"] in {"critical", "high"} and finding["status"] == "open":
            unresolved_high = True

    overall = verdict.get("overall_verdict")
    recommendation = verdict.get("publication_recommendation")
    if overall not in {"pass", "hold"}:
        raise ValidationError("overall review verdict must be pass or hold")
    if recommendation not in {"authorize_baseline_only", "withhold"}:
        raise ValidationError("publication recommendation is invalid")
    if verdict.get("claim_boundary_acknowledged") is not True:
        raise ValidationError("reviewer must acknowledge the claim boundary")
    if not isinstance(verdict.get("summary"), str) or not verdict["summary"].strip():
        raise ValidationError("review summary must be nonblank")
    pass_eligible = (
        all(item["status"] == "pass" for item in criteria)
        and not unresolved_high
        and all(test["status"] == "pass" for test in tests_run)
    )
    if overall == "pass" and not pass_eligible:
        raise ValidationError("pass verdict conflicts with criteria, findings or tests")
    if (overall == "pass") != (recommendation == "authorize_baseline_only"):
        raise ValidationError("review verdict and publication recommendation conflict")
    return {
        "status": "validated",
        "package_id": PACKAGE_ID,
        "package_sha256": sha256_file(package_path),
        "reviewer_type": reviewer["reviewer_type"],
        "overall_verdict": overall,
        "publication_recommendation": recommendation,
        "gate_status": "passed" if overall == "pass" else "held",
        "finding_count": len(findings),
        "unresolved_high_or_critical_finding": unresolved_high,
    }
