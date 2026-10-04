from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aiio.quebec_full_archive import (
    _read_xlsx_snapshot,
    run_quebec_full_archive_longitudinal,
)
from aiio.quebec_vintages import sha256_file
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data" / "model" / "quebec_pqi_full_archive_contract_v0.1.json"
MILESTONE_REPORT = (
    ROOT / "data" / "model-runs" / "quebec_pqi_milestone_longitudinal_v0.1.json"
)
REPORT = (
    ROOT / "data" / "model-runs" / "quebec_pqi_full_archive_longitudinal_v0.1.json"
)


class QuebecFullArchiveTests(unittest.TestCase):
    def test_official_xlsx_fallback_has_expected_schema_and_rows(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        december = next(
            item for item in contract["resources"] if item["snapshot_date"] == "2024-12-04"
        )
        self.assertEqual(december["schema_profile"], "publisher_wrapped_csv_unusable")
        self.assertIsNotNone(december["fallback_xlsx"])
        rows = _read_xlsx_snapshot(ROOT / december["fallback_xlsx"]["archive_path"])
        self.assertEqual(len(rows), 700)
        project = next(row for row in rows if row["no_projet"] == "10")
        self.assertEqual(project["nom_projet"], "Échangeur Dorval – Montréal – Réaménagement")
        self.assertEqual(project["cout_total"], "334.2")
        self.assertEqual(project["date_fin_mise_en_service"], "2021-09-21")

    def test_committed_full_archive_reproduces_and_fails_closed(self) -> None:
        expected = json.loads(REPORT.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            actual = run_quebec_full_archive_longitudinal(
                CONTRACT,
                ROOT,
                MILESTONE_REPORT,
                output_root / "report.json",
                output_root / "snapshots.csv",
                output_root / "lifecycles.csv",
                output_root / "transitions.csv",
            )
            for key in (
                "snapshot_date_count",
                "snapshot_observation_count",
                "unique_project_count",
                "latest_snapshot_project_count",
                "absent_from_latest_project_count",
                "project_with_interval_disappearance_count",
                "project_with_catalog_reentry_count",
                "project_with_publisher_declared_retirement_disappearance_count",
                "disappearance_event_count",
                "publisher_declared_retirement_disappearance_event_count",
                "unclassified_disappearance_event_count",
                "linked_change_diagnostics",
                "milestone_comparison",
                "snapshot_summaries",
            ):
                self.assertEqual(actual[key], expected[key])
            self.assertEqual(
                actual["outputs"]["snapshot_csv_sha256"],
                sha256_file(output_root / "snapshots.csv"),
            )
            self.assertEqual(
                actual["outputs"]["lifecycle_csv_sha256"],
                sha256_file(output_root / "lifecycles.csv"),
            )
            self.assertEqual(
                actual["outputs"]["transition_csv_sha256"],
                sha256_file(output_root / "transitions.csv"),
            )
            self.assertTrue(
                actual["publication_boundary"]["catalog_snapshot_coverage_complete"]
            )
            self.assertFalse(
                actual["publication_boundary"]["project_exit_outcome_authorized"]
            )
            self.assertFalse(
                actual["publication_boundary"]["ai_attributable_effect_authorized"]
            )

    def test_rejects_incomplete_archive_contract(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        contract["resources"] = contract["resources"][:-1]
        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            bad_contract = output_root / "contract.json"
            bad_contract.write_text(json.dumps(contract), encoding="utf-8")
            with self.assertRaises(ValidationError):
                run_quebec_full_archive_longitudinal(
                    bad_contract,
                    ROOT,
                    MILESTONE_REPORT,
                    output_root / "report.json",
                    output_root / "snapshots.csv",
                    output_root / "lifecycles.csv",
                    output_root / "transitions.csv",
                )


if __name__ == "__main__":
    unittest.main()
