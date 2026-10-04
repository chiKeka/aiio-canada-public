from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.model_review import (
    PACKAGE_ID,
    REVIEW_CRITERIA,
    build_reference_cost_review_package,
    sha256_file,
    validate_reference_cost_review_verdict,
)
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = (
    ROOT / "data/model-runs/alberta_reference_cost_review_package_v0.1.json"
)


def passing_verdict(package_path: Path) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "package_id": PACKAGE_ID,
        "package_sha256": sha256_file(package_path),
        "reviewer": {
            "name": "Independent fixture reviewer",
            "organization": "Test fixture",
            "reviewer_type": "human_subject_matter_expert",
            "reviewer_is_not_model_author": True,
            "independence_declaration": "Fixture reviewer is independent of model authorship.",
            "conflicts_of_interest": "none",
            "tool_version": "not_applicable",
        },
        "reviewed_at": "2026-09-01",
        "tests_run": [
            {
                "command": "fixture calibration tests",
                "status": "pass",
                "notes": "Fixture test disposition passed.",
            }
        ],
        "criteria": [
            {
                "criterion_id": item["criterion_id"],
                "status": "pass",
                "notes": f"Fixture evidence for {item['criterion_id']}.",
            }
            for item in REVIEW_CRITERIA
        ],
        "findings": [],
        "overall_verdict": "pass",
        "publication_recommendation": "authorize_baseline_only",
        "claim_boundary_acknowledged": True,
        "summary": "Fixture pass limited to the gate-passing E1 horizon.",
    }


class ReferenceCostModelReviewTests(unittest.TestCase):
    def test_committed_package_is_deterministic_and_fail_closed(self) -> None:
        self.assertEqual(
            hashlib.sha256(PACKAGE_PATH.read_bytes()).hexdigest(),
            "24df8d2263f0c6875a981eeed1dda2bf5576b0870531a2e88cf11572e25b5935",
        )
        with tempfile.TemporaryDirectory() as directory:
            generated_package = Path(directory) / "package.json"
            generated_prompt = Path(directory) / "prompt.md"
            build_reference_cost_review_package(
                ROOT, generated_package, generated_prompt
            )
            self.assertEqual(
                json.loads(generated_package.read_text(encoding="utf-8")),
                json.loads(PACKAGE_PATH.read_text(encoding="utf-8")),
            )
        package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(package["review_status"], "pending_independent_review")
        self.assertFalse(
            package["publication_boundary"]["independent_review_complete"]
        )
        self.assertFalse(
            package["publication_boundary"]["public_projection_authorized"]
        )
        self.assertEqual(
            package["facts_to_reconcile"]["horizon_status_counts"],
            {"gate_failed": 29, "gate_passed": 1, "not_assessed": 10},
        )

    def test_validates_consistent_pass_verdict_without_mutating_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            verdict_path = Path(directory) / "verdict.json"
            verdict_path.write_text(
                json.dumps(passing_verdict(PACKAGE_PATH)), encoding="utf-8"
            )
            result = validate_reference_cost_review_verdict(
                PACKAGE_PATH, verdict_path
            )
        self.assertEqual(result["gate_status"], "passed")
        self.assertEqual(result["publication_recommendation"], "authorize_baseline_only")
        package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
        self.assertFalse(
            package["publication_boundary"]["public_projection_authorized"]
        )

    def test_rejects_pass_with_open_high_finding(self) -> None:
        verdict = passing_verdict(PACKAGE_PATH)
        verdict["findings"] = [
            {
                "finding_id": "F-001",
                "criterion_id": "temporal_integrity",
                "severity": "high",
                "status": "open",
                "summary": "Fixture leakage risk.",
                "evidence": "research/src/aiio/calibration.py",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            verdict_path = Path(directory) / "verdict.json"
            verdict_path.write_text(json.dumps(verdict), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_reference_cost_review_verdict(PACKAGE_PATH, verdict_path)

    def test_rejects_missing_criterion_and_stale_package_hash(self) -> None:
        verdict = passing_verdict(PACKAGE_PATH)
        verdict["criteria"] = verdict["criteria"][:-1]
        with tempfile.TemporaryDirectory() as directory:
            verdict_path = Path(directory) / "verdict.json"
            verdict_path.write_text(json.dumps(verdict), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_reference_cost_review_verdict(PACKAGE_PATH, verdict_path)
        stale = copy.deepcopy(passing_verdict(PACKAGE_PATH))
        stale["package_sha256"] = "sha256:" + "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            verdict_path = Path(directory) / "verdict.json"
            verdict_path.write_text(json.dumps(stale), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_reference_cost_review_verdict(PACKAGE_PATH, verdict_path)


if __name__ == "__main__":
    unittest.main()
