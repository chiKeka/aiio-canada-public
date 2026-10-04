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
from aiio.adapters.statcan_capex import (
    CANADA_DGUID,
    EXPECTED_FIRST_YEAR,
    EXPECTED_LATEST_YEAR,
    SELECTED_EXPENDITURE,
    SELECTED_NAICS_LABEL,
    normalize_information_sector_construction_capex,
)
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]


class InformationSectorConstructionCapexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.zip_path = self.root / "source.zip"
        self.output_csv_path = self.root / "output.csv"
        self.output_json_path = self.root / "report.json"

    def build_zip(
        self,
        *,
        omit_cell: bool = False,
        include_exact_naics: bool = False,
        omit_status_column: bool = False,
    ) -> None:
        fieldnames = [
            "REF_DATE",
            "GEO",
            "DGUID",
            "Capital and repair expenditures",
            "North American Industry Classification System (NAICS)",
            "UOM",
            "SCALAR_FACTOR",
            "VALUE",
        ]
        if not omit_status_column:
            fieldnames.append("STATUS")
        geographies = [("Canada", CANADA_DGUID)] + [
            (geography_id, dguid)
            for dguid, geography_id in PROVINCE_DGUID_TO_GEOGRAPHY_ID.items()
        ]
        text = io.StringIO()
        writer = csv.DictWriter(text, fieldnames=fieldnames)
        writer.writeheader()
        for label, dguid in geographies:
            for year in range(EXPECTED_FIRST_YEAR, EXPECTED_LATEST_YEAR + 1):
                if omit_cell and dguid == "2021A000248" and year == 2024:
                    continue
                suppressed = dguid == "2021A000248" and year == 2023
                row = {
                    "REF_DATE": str(year),
                    "GEO": label,
                    "DGUID": dguid,
                    "Capital and repair expenditures": SELECTED_EXPENDITURE,
                    "North American Industry Classification System (NAICS)": SELECTED_NAICS_LABEL,
                    "UOM": "Dollars",
                    "SCALAR_FACTOR": "millions",
                    "VALUE": "" if suppressed else "1.5",
                }
                if not omit_status_column:
                    row["STATUS"] = "x" if suppressed else "A"
                writer.writerow(row)
        if include_exact_naics:
            row = {
                "REF_DATE": "2024",
                "GEO": "Alberta",
                "DGUID": "2021A000248",
                "Capital and repair expenditures": SELECTED_EXPENDITURE,
                "North American Industry Classification System (NAICS)": "Computing infrastructure providers, data processing, web hosting, and related services [518210]",
                "UOM": "Dollars",
                "SCALAR_FACTOR": "millions",
                "VALUE": "1.0",
            }
            if not omit_status_column:
                row["STATUS"] = "A"
            writer.writerow(row)
        with zipfile.ZipFile(self.zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("34100035.csv", text.getvalue())

    def test_normalizes_broad_sector_capex_and_preserves_suppression(self) -> None:
        self.build_zip()
        report = normalize_information_sector_construction_capex(
            self.zip_path, self.output_csv_path, self.output_json_path
        )
        self.assertEqual(report["observation_count"], 294)
        self.assertEqual(report["geography_count"], 14)
        self.assertEqual(report["reference_year_count"], 21)
        self.assertFalse(
            report["treatment_requirement_assessment"][
                "authorizing_treatment_present"
            ]
        )
        with self.output_csv_path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        alberta_2024 = next(
            row
            for row in rows
            if row["geography_id"] == "PR_48"
            and row["reference_year"] == "2024"
        )
        self.assertEqual(alberta_2024["value_cad"], "1500000")
        self.assertEqual(alberta_2024["release_measure_status"], "actual_or_revised")
        alberta_2023 = next(
            row
            for row in rows
            if row["geography_id"] == "PR_48"
            and row["reference_year"] == "2023"
        )
        self.assertEqual(alberta_2023["value_cad"], "")
        self.assertEqual(alberta_2023["quality_flag"], "suppressed_confidentiality")

    def test_rejects_missing_cell_schema_drift_and_new_exact_industry(self) -> None:
        self.build_zip(omit_cell=True)
        with self.assertRaisesRegex(ValidationError, "cell coverage is incomplete"):
            normalize_information_sector_construction_capex(
                self.zip_path, self.output_csv_path, self.output_json_path
            )
        self.build_zip(omit_status_column=True)
        with self.assertRaisesRegex(ValidationError, "schema changed"):
            normalize_information_sector_construction_capex(
                self.zip_path, self.output_csv_path, self.output_json_path
            )
        self.build_zip(include_exact_naics=True)
        with self.assertRaisesRegex(ValidationError, "now contains NAICS 518210"):
            normalize_information_sector_construction_capex(
                self.zip_path, self.output_csv_path, self.output_json_path
            )

    def test_committed_artifact_is_reproducible_and_fail_closed(self) -> None:
        source = (
            ROOT
            / "data/raw/statcan_capex_industry_geography_34100035/2026-09-01_a65541e3a9ad.zip"
        )
        manifest = source.with_suffix(source.suffix + ".manifest.json")
        committed_csv = (
            ROOT / "data/processed/information_sector_construction_capex_canada.csv"
        )
        committed_json = (
            ROOT
            / "data/model-runs/information_sector_construction_capex_screen_v0.1.json"
        )
        report = json.loads(committed_json.read_text(encoding="utf-8"))
        self.assertEqual(
            report["input_sha256"],
            "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            report["output_sha256"],
            "sha256:" + hashlib.sha256(committed_csv.read_bytes()).hexdigest(),
        )
        self.assertEqual(report["observation_count"], 294)
        self.assertEqual(report["quality_flag_counts"]["suppressed_confidentiality"], 99)
        self.assertTrue(
            report["publication_boundary"][
                "descriptive_broad_sector_capex_authorized"
            ]
        )
        self.assertFalse(
            report["publication_boundary"]["ai_construction_treatment_authorized"]
        )
        with tempfile.TemporaryDirectory() as directory:
            regenerated_csv = Path(directory) / "screen.csv"
            regenerated_json = Path(directory) / "screen.json"
            normalize_information_sector_construction_capex(
                source,
                regenerated_csv,
                regenerated_json,
                retrieval_manifest_path=manifest,
            )
            self.assertEqual(regenerated_csv.read_bytes(), committed_csv.read_bytes())
            self.assertEqual(
                json.loads(regenerated_json.read_text(encoding="utf-8")), report
            )


if __name__ == "__main__":
    unittest.main()
