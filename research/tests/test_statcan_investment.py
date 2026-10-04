from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from aiio.adapters.statcan import PROVINCE_DGUID_TO_GEOGRAPHY_ID
from aiio.adapters.statcan_investment import (
    SELECTED_INVESTMENT_VALUES,
    SELECTED_STRUCTURES,
    normalize_investment_controls,
)
from aiio.schemas import ValidationError


class InvestmentControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.zip_path = self.root / "input.zip"
        self.output_path = self.root / "output.csv"
        self.report_path = self.root / "report.json"

    def build_zip(self, *, omit_one_month: bool = False) -> None:
        fieldnames = [
            "REF_DATE",
            "GEO",
            "DGUID",
            "Type of structure",
            "Type of work",
            "Investment Value",
            "UOM",
            "VALUE",
            "STATUS",
        ]
        geographies = [
            (geography_id, dguid, geography_id)
            for dguid, geography_id in PROVINCE_DGUID_TO_GEOGRAPHY_ID.items()
        ]
        geographies.extend(
            (f"CMA_{index:03d}", f"2021S0503{index}", f"CMA {index}")
            for index in range(1, 31)
        )
        text = io.StringIO()
        writer = csv.DictWriter(text, fieldnames=fieldnames)
        writer.writeheader()
        for geography_id, dguid, label in geographies:
            for month in ("2026-01", "2026-02", "2026-03"):
                for structure in sorted(SELECTED_STRUCTURES):
                    for investment_value in sorted(SELECTED_INVESTMENT_VALUES):
                        if (
                            omit_one_month
                            and geography_id == "PR_48"
                            and month == "2026-03"
                            and structure == "Total commercial"
                            and investment_value == "Seasonally adjusted - current"
                        ):
                            continue
                        writer.writerow(
                            {
                                "REF_DATE": month,
                                "GEO": label,
                                "DGUID": dguid,
                                "Type of structure": structure,
                                "Type of work": "Types of work, total",
                                "Investment Value": investment_value,
                                "UOM": "Dollars",
                                "VALUE": "10",
                                "STATUS": "",
                            }
                        )
        with zipfile.ZipFile(self.zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("34100293.csv", text.getvalue())

    def test_normalizes_monthly_values_to_quarterly_controls(self) -> None:
        self.build_zip()
        rows = normalize_investment_controls(
            self.zip_path, self.output_path, self.report_path
        )
        self.assertEqual(len(rows), 43 * 4 * 2)
        alberta = next(
            row
            for row in rows
            if row["geography_id"] == "PR_48"
            and row["type_of_structure"] == "Total commercial"
            and row["investment_basis"] == "Seasonally adjusted - current"
        )
        self.assertEqual(alberta["value"], "30.00")
        self.assertEqual(alberta["source_evidence_status"], "observed")
        self.assertEqual(alberta["evidence_status"], "inferred")
        self.assertEqual(alberta["source_month_count"], "3")
        self.assertTrue(self.report_path.exists())

    def test_rejects_incomplete_quarter(self) -> None:
        self.build_zip(omit_one_month=True)
        with self.assertRaisesRegex(ValidationError, "incomplete investment quarter"):
            normalize_investment_controls(self.zip_path, self.output_path)

    def test_committed_control_artifact_is_hash_locked_and_fail_closed(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        output_path = project_root / "data/processed/building_investment_controls_canada.csv"
        report = json.loads(
            (
                project_root
                / "data/model-runs/building_investment_controls_canada_v0.1.json"
            ).read_text(encoding="utf-8")
        )
        output_hash = "sha256:" + hashlib.sha256(output_path.read_bytes()).hexdigest()
        self.assertEqual(output_hash, report["output_sha256"])
        self.assertEqual(report["observation_count"], 14896)
        self.assertEqual(report["province_and_territory_count"], 13)
        self.assertEqual(report["cma_or_cma_part_count"], 36)
        self.assertEqual(report["quarter_count"], 38)
        self.assertEqual(report["missing_quarterly_value_count"], 0)
        boundary = report["publication_boundary"]
        self.assertFalse(boundary["ai_treatment_authorized"])
        self.assertFalse(boundary["public_project_outcome_authorized"])
        self.assertFalse(boundary["ai_attributable_effect_authorized"])


if __name__ == "__main__":
    unittest.main()
