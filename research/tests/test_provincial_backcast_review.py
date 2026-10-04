from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from aiio.provincial_backcast_review import (
    CRITERIA,
    PACKAGE_ID,
    build_province_linked_review_package,
    validate_province_linked_review_verdict,
)
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = (
    ROOT / "data/model-runs/bc_on_qc_province_linked_review_package_v0.1.json"
)


def passing_verdict() -> dict[str, object]:
    import hashlib

    package_hash = "sha256:" + hashlib.sha256(PACKAGE_PATH.read_bytes()).hexdigest()
    return {
        "schema_version": "1.0.0",
        "package_id": PACKAGE_ID,
        "package_sha256": package_hash,
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
                "command": "fixture province-linked tests",
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
            for item in CRITERIA
        ],
        "findings": [],
        "overall_verdict": "pass",
        "publication_recommendation": "authorize_research_display_only",
        "claim_boundary_acknowledged": True,
        "summary": "Fixture pass is limited to labelled research display.",
    }


class ProvinceLinkedReviewTests(unittest.TestCase):
    def test_committed_package_is_reproducible_and_non_authorizing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            generated_package = temporary_root / "package.json"
            generated_prompt = temporary_root / "prompt.md"
            build_province_linked_review_package(
                ROOT, generated_package, generated_prompt
            )
            self.assertEqual(
                json.loads(generated_package.read_text(encoding="utf-8")),
                json.loads(PACKAGE_PATH.read_text(encoding="utf-8")),
            )
        package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(package["review_status"], "pending_independent_review")
        self.assertEqual(len(package["input_manifest"]), 10)
        self.assertEqual(len(package["required_criteria"]), 10)
        self.assertFalse(package["publication_boundary"]["independent_review_complete"])
        self.assertFalse(package["publication_boundary"]["public_projection_authorized"])
        self.assertEqual(
            package["facts_to_reconcile"]["horizon_status_counts"],
            {"gate_failed": 36, "gate_passed": 9, "not_assessed": 15},
        )

    def test_validates_consistent_research_display_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            verdict_path = Path(temporary_directory) / "verdict.json"
            verdict_path.write_text(json.dumps(passing_verdict()), encoding="utf-8")
            result = validate_province_linked_review_verdict(
                PACKAGE_PATH, verdict_path
            )
        self.assertEqual(result["gate_status"], "passed")
        self.assertEqual(
            result["publication_recommendation"],
            "authorize_research_display_only",
        )

    def test_rejects_incomplete_or_internally_inconsistent_pass(self) -> None:
        incomplete = passing_verdict()
        incomplete["criteria"] = incomplete["criteria"][:-1]
        with tempfile.TemporaryDirectory() as temporary_directory:
            verdict_path = Path(temporary_directory) / "incomplete.json"
            verdict_path.write_text(json.dumps(incomplete), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_province_linked_review_verdict(PACKAGE_PATH, verdict_path)

        inconsistent = copy.deepcopy(passing_verdict())
        inconsistent["findings"] = [
            {
                "finding_id": "F-001",
                "criterion_id": "reference_market_choice",
                "severity": "high",
                "status": "open",
                "summary": "Fixture representativeness risk.",
                "evidence": "docs/methodology/province-linked-bcpi-backcast.md",
            }
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            verdict_path = Path(temporary_directory) / "inconsistent.json"
            verdict_path.write_text(json.dumps(inconsistent), encoding="utf-8")
            with self.assertRaises(ValidationError):
                validate_province_linked_review_verdict(PACKAGE_PATH, verdict_path)


if __name__ == "__main__":
    unittest.main()
