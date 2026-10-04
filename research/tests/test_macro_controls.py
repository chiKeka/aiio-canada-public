from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from aiio.macro_controls import build_regional_macro_controls
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw"
CPI = RAW / "statcan_cpi_18100004/2026-09-01_19f2712264fc.zip"
POPULATION = (
    RAW / "statcan_population_17100009/2026-09-01_4c99d5f13722.zip"
)
EARNINGS = (
    RAW / "statcan_seph_earnings_14100223/2026-09-01_06c7a79f80a0.zip"
)
HOUSING = (
    RAW / "statcan_cmhc_housing_starts_34100156/2026-09-01_b022bf41c44d.zip"
)
INVESTMENT_CSV = ROOT / "data/processed/building_investment_controls_canada.csv"
INVESTMENT_REPORT = (
    ROOT / "data/model-runs/building_investment_controls_canada_v0.1.json"
)
COMMITTED_CSV = ROOT / "data/processed/regional_macro_controls_canada.csv"
COMMITTED_REPORT = (
    ROOT / "data/model-runs/regional_macro_controls_canada_v0.1.json"
)


class RegionalMacroControlTests(unittest.TestCase):
    def test_committed_panel_is_reproducible_and_fail_closed(self) -> None:
        report = json.loads(COMMITTED_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["observation_count"], 3116)
        self.assertEqual(report["series_count"], 82)
        self.assertEqual(report["metric_count"], 7)
        self.assertEqual(report["province_and_territory_count"], 13)
        self.assertEqual(report["quarter_count"], 38)
        self.assertEqual(report["missing_value_count"], 1)
        self.assertEqual(report["common_latest_period_end"], "2026-06-30")
        self.assertEqual(
            report["output_sha256"],
            "sha256:" + hashlib.sha256(COMMITTED_CSV.read_bytes()).hexdigest(),
        )
        boundary = report["publication_boundary"]
        self.assertTrue(boundary["regional_macro_context_authorized"])
        self.assertFalse(boundary["composite_macro_pressure_score_authorized"])
        self.assertFalse(boundary["scenario_calibration_authorized"])
        self.assertFalse(boundary["public_project_cost_translation_authorized"])
        self.assertFalse(boundary["ai_attributable_effect_authorized"])

        with tempfile.TemporaryDirectory() as directory:
            output_csv = Path(directory) / "panel.csv"
            output_json = Path(directory) / "report.json"
            regenerated = build_regional_macro_controls(
                CPI,
                POPULATION,
                EARNINGS,
                HOUSING,
                INVESTMENT_CSV,
                INVESTMENT_REPORT,
                output_csv,
                output_json,
            )
            self.assertEqual(output_csv.read_bytes(), COMMITTED_CSV.read_bytes())
            self.assertEqual(regenerated, report)

    def test_rejects_stale_retrieval_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied_cpi = Path(directory) / CPI.name
            copied_manifest = copied_cpi.with_suffix(
                copied_cpi.suffix + ".manifest.json"
            )
            shutil.copy2(CPI, copied_cpi)
            shutil.copy2(
                CPI.with_suffix(CPI.suffix + ".manifest.json"), copied_manifest
            )
            with copied_cpi.open("ab") as handle:
                handle.write(b"stale")
            with self.assertRaisesRegex(ValidationError, "hash mismatch"):
                build_regional_macro_controls(
                    copied_cpi,
                    POPULATION,
                    EARNINGS,
                    HOUSING,
                    INVESTMENT_CSV,
                    INVESTMENT_REPORT,
                    Path(directory) / "panel.csv",
                    Path(directory) / "report.json",
                )


if __name__ == "__main__":
    unittest.main()
