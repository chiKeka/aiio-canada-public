from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.adapters.edmonton_permits import (
    DATASET_ID,
    OUTPUT_FIELDS,
    SELECT_FIELDS,
    classify_description,
    normalize_edmonton_permit_proxy,
    validate_metadata,
)
from aiio.schemas import ValidationError


class EdmontonPermitProxyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.raw_path = self.root / "permits.json"
        self.output_path = self.root / "permits.csv"
        self.report_path = self.root / "report.json"

    def test_classifier_separates_facility_server_and_substring_matches(self) -> None:
        self.assertEqual(
            classify_description("Expansion of a Rogers data center"),
            (
                "explicit_data_centre_reference",
                "data_centre_candidate",
                ["data center"],
            ),
        )
        self.assertEqual(
            classify_description("New server room in an elementary school")[1],
            "server_reference_context",
        )
        self.assertEqual(
            classify_description("Upgrade the restaurant servery counter")[1],
            "excluded_false_positive",
        )
        self.assertEqual(
            classify_description("Basement development on Observer Lane")[1],
            "excluded_false_positive",
        )

    def test_normalization_is_field_minimized_and_fail_closed(self) -> None:
        self.write_rows(
            [
                self.row(
                    row_id="1-1",
                    issue_date="2025-01-10T00:00:00.000",
                    year="2025",
                    job_description="Interior expansion of a data centre for AI compute",
                    construction_value="1200000",
                    occupancy_granted_date="2025-10-01",
                ),
                self.row(
                    row_id="1-2",
                    issue_date="2025-02-10T00:00:00.000",
                    year="2025",
                    job_description="New server room in an office",
                    construction_value="50000",
                ),
                self.row(
                    row_id="1-3",
                    issue_date="2025-03-10T00:00:00.000",
                    year="2025",
                    job_description="Restaurant servery alteration",
                    construction_value="10000",
                ),
            ]
        )
        report = normalize_edmonton_permit_proxy(
            self.raw_path,
            self.output_path,
            self.report_path,
            source_as_of_date="2026-08-31",
        )
        with self.output_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fields = set(reader.fieldnames or ())
        self.assertEqual(len(rows), 3)
        self.assertEqual(report["data_centre_candidate_count"], 1)
        self.assertEqual(report["explicit_ai_reference_count"], 1)
        self.assertEqual(rows[0]["construction_value_status"], "reported_permit_estimate_proxy")
        self.assertEqual(rows[0]["realized_construction_status"], "not_observed")
        self.assertEqual(rows[0]["ai_specificity_status"], "explicit_ai_reference_observed")
        self.assertNotIn("not_ai_specific", rows[0]["quality_flags"].split("|"))
        self.assertFalse(
            report["publication_boundary"]["realized_ai_construction_treatment_authorized"]
        )
        self.assertFalse(report["publication_boundary"]["ai_attributable_effect_authorized"])
        self.assertEqual(fields, set(OUTPUT_FIELDS))
        self.assertFalse(
            fields
            & {
                "address",
                "legal_description",
                "latitude",
                "longitude",
                "neighbourhood",
                "job_description",
            }
        )

    def test_rejects_row_schema_drift(self) -> None:
        row = self.row(
            row_id="1-1",
            issue_date="2025-01-10T00:00:00.000",
            year="2025",
            job_description="Data centre expansion",
        )
        del row["building_type"]
        self.write_rows([row])
        with self.assertRaisesRegex(ValidationError, "schema changed"):
            normalize_edmonton_permit_proxy(
                self.raw_path,
                self.output_path,
                self.report_path,
                source_as_of_date="2026-08-31",
            )

    def test_metadata_contract_rejects_missing_selected_field(self) -> None:
        validate_metadata(
            {
                "id": DATASET_ID,
                "columns": [{"fieldName": field} for field in SELECT_FIELDS],
            }
        )
        with self.assertRaisesRegex(ValidationError, "metadata schema changed"):
            validate_metadata(
                {
                    "id": DATASET_ID,
                    "columns": [
                        {"fieldName": field}
                        for field in SELECT_FIELDS
                        if field != "occupancy_granted_date"
                    ],
                }
            )

    def test_committed_artifact_is_hash_locked_and_non_authorizing(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        output_path = project_root / "data/processed/edmonton_data_centre_permit_proxy.csv"
        report_path = (
            project_root
            / "data/model-runs/edmonton_data_centre_permit_proxy_v0.1.json"
        )
        if not output_path.exists() or not report_path.exists():
            self.skipTest("committed permit proxy artifact has not been built yet")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        output_hash = "sha256:" + hashlib.sha256(output_path.read_bytes()).hexdigest()
        self.assertEqual(output_hash, report["output_sha256"])
        self.assertGreater(report["broad_screen_row_count"], 0)
        self.assertGreater(report["data_centre_candidate_count"], 0)
        self.assertEqual(report["explicit_ai_reference_count"], 0)
        self.assertFalse(
            report["publication_boundary"]["realized_ai_construction_treatment_authorized"]
        )
        self.assertFalse(report["publication_boundary"]["ai_attributable_effect_authorized"])

    def write_rows(self, rows: list[dict[str, str]]) -> None:
        self.raw_path.write_text(json.dumps(rows), encoding="utf-8")

    @staticmethod
    def row(**overrides: str) -> dict[str, str]:
        row = {
            "row_id": "1-0",
            "issue_date": "2025-01-01T00:00:00.000",
            "year": "2025",
            "month_number": "1",
            "job_category": "Commercial Final",
            "job_description": "Data centre alteration",
            "building_type": "Office Buildings (520)",
            "work_type": "(03) Interior Alterations",
            "construction_value": "100000",
            "floor_area": "1000",
            "occupancy_granted_date": "",
        }
        row.update(overrides)
        return row


if __name__ == "__main__":
    unittest.main()
