from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from aiio.quebec_review import build_quebec_parser_review_package, sha256_file
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = (
    ROOT
    / "data"
    / "raw"
    / "quebec_pqi_project_dashboard"
    / "2026-09-01_a437f7ba9a74.csv"
)
REVISION_REPORT = (
    ROOT / "data" / "model-runs" / "quebec_pqi_authorized_project_revisions_v0.1.json"
)
SUMMARY = ROOT / "data" / "processed" / "quebec_pqi_authorized_project_revisions.csv"
EVENTS = ROOT / "data" / "processed" / "quebec_pqi_authorized_revision_events.csv"
LONGITUDINAL_REPORT = (
    ROOT / "data" / "model-runs" / "quebec_pqi_milestone_longitudinal_v0.1.json"
)
LIFECYCLE = ROOT / "data" / "processed" / "quebec_pqi_milestone_project_lifecycles.csv"


class QuebecReviewTests(unittest.TestCase):
    def test_review_package_reproduces_and_remains_unauthorized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            review_csv = temporary / "review.csv"
            package_json = temporary / "package.json"
            result = build_quebec_parser_review_package(
                DASHBOARD,
                REVISION_REPORT,
                SUMMARY,
                EVENTS,
                LONGITUDINAL_REPORT,
                LIFECYCLE,
                review_csv,
                package_json,
            )
            committed = json.loads(
                (
                    ROOT
                    / "data"
                    / "model-runs"
                    / "quebec_pqi_parser_review_package_v0.1.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(result["sample_project_count"], committed["sample_project_count"])
            self.assertEqual(
                result["selection_reason_counts"], committed["selection_reason_counts"]
            )
            self.assertEqual(
                sha256_file(review_csv), committed["review_output"]["content_hash"]
            )
            self.assertEqual(result["review_status"], "pending_independent_review")
            self.assertFalse(
                result["publication_boundary"]["independent_parser_review_complete"]
            )
            with review_csv.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            self.assertTrue(all(row["reviewer_name"] == "" for row in rows))
            self.assertTrue(all(row["review_status"] == "" for row in rows))
            self.assertTrue(
                any("all_unreconciled_cost_chains" in row["selection_reasons"] for row in rows)
            )
            self.assertTrue(
                any("all_milestone_reentries" in row["selection_reasons"] for row in rows)
            )

    def test_review_package_fails_on_tampered_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            tampered = temporary / "summary.csv"
            tampered.write_bytes(SUMMARY.read_bytes() + b"\n")
            with self.assertRaises(ValidationError):
                build_quebec_parser_review_package(
                    DASHBOARD,
                    REVISION_REPORT,
                    tampered,
                    EVENTS,
                    LONGITUDINAL_REPORT,
                    LIFECYCLE,
                    temporary / "review.csv",
                    temporary / "package.json",
                )


if __name__ == "__main__":
    unittest.main()
