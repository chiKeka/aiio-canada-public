from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from aiio.provincial_backcast import (
    BACKCASTABLE_INDICATORS,
    MAX_OVERLAP_MAPE_PERCENT,
    run_province_linked_reference_backcast,
)
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
PROVINCE_PATH = ROOT / "data/processed/bcpi_reference_bc_on_qc.csv"
CMA_PATH = ROOT / "data/processed/bcpi_reference_van_tor_mtl.csv"
OUTPUT_PATH = ROOT / "data/processed/bcpi_province_linked_history_bc_on_qc.csv"
REPORT_PATH = (
    ROOT
    / "data/model-runs/bc_on_qc_province_linked_reference_baseline_v0.1.json"
)


class ProvinceLinkedReferenceBackcastTests(unittest.TestCase):
    def test_committed_artifacts_are_reproducible_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            generated_csv = temporary_root / "backcast.csv"
            generated_json = temporary_root / "backcast.json"
            run_province_linked_reference_backcast(
                PROVINCE_PATH,
                CMA_PATH,
                generated_csv,
                generated_json,
            )
            self.assertEqual(generated_csv.read_bytes(), OUTPUT_PATH.read_bytes())
            self.assertEqual(
                json.loads(generated_json.read_text(encoding="utf-8")),
                json.loads(REPORT_PATH.read_text(encoding="utf-8")),
            )

        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            report["publication_summary"]["horizon_status_counts"],
            {"gate_failed": 36, "gate_passed": 9, "not_assessed": 15},
        )
        self.assertFalse(
            report["publication_authorization"]["public_projection_authorized"]
        )
        self.assertFalse(
            report["publication_authorization"]["project_cost_translation_authorized"]
        )
        self.assertFalse(
            report["publication_authorization"]["ai_attributable_effect_authorized"]
        )

    def test_preserves_observed_history_and_labels_inference(self) -> None:
        with OUTPUT_PATH.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1752)
        inferred = [row for row in rows if row["evidence_status"] == "inferred"]
        observed = [row for row in rows if row["evidence_status"] == "observed"]
        self.assertEqual(len(inferred), 1296)
        self.assertEqual(len(observed), 456)
        self.assertTrue(all(row["period_end"] < "2017-03-31" for row in inferred))
        self.assertTrue(
            all(row["indicator_id"] in BACKCASTABLE_INDICATORS for row in inferred)
        )
        self.assertTrue(
            all(
                "not_official_provincial_observation" in row["quality_flags"]
                for row in inferred
            )
        )

        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        diagnostics = report["backcast_method"]["diagnostics"]
        self.assertEqual(len(diagnostics), 12)
        self.assertTrue(all(item["status"] == "pass" for item in diagnostics))
        self.assertTrue(
            all(
                item["overlap_mape_percent"] <= MAX_OVERLAP_MAPE_PERCENT
                for item in diagnostics
            )
        )

    def test_rejects_source_lineage_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            tampered = temporary_root / "province.csv"
            text = PROVINCE_PATH.read_text(encoding="utf-8")
            tampered.write_text(
                text.replace("STATCAN_BCPI_18100289", "UNREGISTERED", 1),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValidationError, "source lineage changed"):
                run_province_linked_reference_backcast(
                    tampered,
                    CMA_PATH,
                    temporary_root / "output.csv",
                    temporary_root / "output.json",
                )


if __name__ == "__main__":
    unittest.main()
