from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from aiio.adapters.statcan import (
    BCPI_REFERENCE_CMA_DGUID_TO_GEOGRAPHY_ID,
    normalize_bcpi_reference_cmas,
)
from aiio.cma_calibration import run_cma_reference_class_baseline
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
BUILDING_CLASSES = (
    ("Institutional buildings [62213]", "Division composite"),
    ("School", "Division composite"),
    ("Office building [62212]", "Division composite"),
    (
        "Bus depot with maintenance and repair facilities",
        "Division composite",
    ),
)
GEOGRAPHY_LABELS = {
    "2021S0503462": "Montréal, Quebec",
    "2021S0503535": "Toronto, Ontario",
    "2021S0503933": "Vancouver, British Columbia",
}


class CmaReferenceCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.zip_path = self.root / "source.zip"
        self.output_csv_path = self.root / "output.csv"

    def build_zip(
        self,
        *,
        missing_value: bool = False,
        omit_symbol_column: bool = False,
    ) -> None:
        fieldnames = [
            "REF_DATE",
            "GEO",
            "DGUID",
            "Type of building",
            "Division",
            "UOM",
            "VALUE",
            "STATUS",
        ]
        if not omit_symbol_column:
            fieldnames.append("SYMBOL")
        text = io.StringIO()
        writer = csv.DictWriter(text, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for dguid in BCPI_REFERENCE_CMA_DGUID_TO_GEOGRAPHY_ID:
            for building, division in BUILDING_CLASSES:
                row = {
                    "REF_DATE": "2026-04",
                    "GEO": GEOGRAPHY_LABELS[dguid],
                    "DGUID": dguid,
                    "Type of building": building,
                    "Division": division,
                    "UOM": "Index, 2023=100",
                    "VALUE": (
                        ""
                        if missing_value
                        and dguid == "2021S0503933"
                        and building == "School"
                        else "105.0"
                    ),
                    "STATUS": "",
                }
                if not omit_symbol_column:
                    row["SYMBOL"] = ""
                writer.writerow(row)
        with zipfile.ZipFile(self.zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("18100289.csv", text.getvalue())

    def test_normalizes_three_cmas_and_all_reference_classes(self) -> None:
        self.build_zip()
        observations = normalize_bcpi_reference_cmas(
            self.zip_path, self.output_csv_path
        )
        self.assertEqual(len(observations), 12)
        self.assertEqual(
            {item.geography_id for item in observations},
            {"CMA_462", "CMA_535", "CMA_933"},
        )
        self.assertTrue(
            all(
                item.transformation_id
                == "TR_STATCAN_BCPI_VAN_TOR_MTL_REFERENCE_CLASSES_1_0_0"
                for item in observations
            )
        )

    def test_fails_closed_on_missing_value_or_schema_drift(self) -> None:
        self.build_zip(missing_value=True)
        with self.assertRaisesRegex(ValidationError, "missing or suppressed"):
            normalize_bcpi_reference_cmas(self.zip_path, self.output_csv_path)
        self.build_zip(omit_symbol_column=True)
        with self.assertRaisesRegex(ValidationError, "schema changed"):
            normalize_bcpi_reference_cmas(self.zip_path, self.output_csv_path)

    def test_committed_artifacts_reproduce_and_remain_withheld(self) -> None:
        source = (
            ROOT
            / "data/raw/statcan_bcpi_18100289/2026-08-31_d0d11fda82bf.zip"
        )
        committed_csv = ROOT / "data/processed/bcpi_reference_van_tor_mtl.csv"
        committed_json = (
            ROOT
            / "data/model-runs/vancouver_toronto_montreal_bcpi_reference_baseline_v0.1.json"
        )
        report = json.loads(committed_json.read_text(encoding="utf-8"))
        self.assertEqual(report["publication_summary"]["reference_series_count"], 12)
        self.assertEqual(
            report["publication_summary"]["horizon_status_counts"],
            {"gate_failed": 36, "gate_passed": 9, "not_assessed": 15},
        )
        self.assertFalse(
            report["publication_authorization"]["public_projection_authorized"]
        )
        passing_geographies = {
            result["geography_id"]
            for result in report["reference_class_results"]
            if any(horizon["status"] == "gate_passed" for horizon in result["horizons"])
        }
        self.assertEqual(passing_geographies, {"CMA_933"})
        self.assertEqual(
            report["input_sha256"],
            hashlib.sha256(committed_csv.read_bytes()).hexdigest(),
        )
        with tempfile.TemporaryDirectory() as directory:
            regenerated_csv = Path(directory) / "cma.csv"
            regenerated_json = Path(directory) / "cma.json"
            normalize_bcpi_reference_cmas(source, regenerated_csv)
            self.assertEqual(regenerated_csv.read_bytes(), committed_csv.read_bytes())
            regenerated_report = run_cma_reference_class_baseline(
                regenerated_csv, regenerated_json
            )
            self.assertEqual(regenerated_report, report)
            self.assertEqual(
                json.loads(regenerated_json.read_text(encoding="utf-8")), report
            )


if __name__ == "__main__":
    unittest.main()
