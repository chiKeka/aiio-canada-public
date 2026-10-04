from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.empirical_panel import build_empirical_covariate_panel
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
ATTRIBUTION = ROOT / "data/model/ai_attribution_panel_contract_v0.1.json"
ACQUISITION = ROOT / "data/model/ai_attribution_panel_acquisition_contract_v0.1.json"
AB_BCPI = ROOT / "data/processed/bcpi_alberta.csv"
COMPARISON_BCPI = ROOT / "data/processed/bcpi_reference_van_tor_mtl.csv"
INVESTMENT = ROOT / "data/processed/building_investment_controls_canada.csv"
MACRO = ROOT / "data/processed/regional_macro_controls_canada.csv"
LABOUR = ROOT / "data/processed/labour_availability_canada.csv"
PROXY = ROOT / "data/processed/ai_construction_proxy_alberta_v0.1.csv"
COMMITTED_CSV = ROOT / "data/processed/ai_attribution_empirical_covariate_panel_v0.1.csv"
COMMITTED_REPORT = ROOT / "data/model-runs/ai_attribution_empirical_covariate_panel_v0.1.json"


class EmpiricalCovariatePanelTests(unittest.TestCase):
    def _build(self, output_csv: Path, output_json: Path, *, alberta_bcpi: Path = AB_BCPI):
        return build_empirical_covariate_panel(
            ROOT, ATTRIBUTION, ACQUISITION, alberta_bcpi, COMPARISON_BCPI,
            INVESTMENT, MACRO, LABOUR, PROXY, output_csv, output_json,
        )

    def test_committed_panel_reproduces_and_remains_non_authorizing(self) -> None:
        report = json.loads(COMMITTED_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(report["row_count"], 555)
        self.assertEqual(report["region_count"], 5)
        self.assertEqual(report["asset_class_count"], 3)
        self.assertEqual(report["quarter_count"], 37)
        self.assertEqual(report["first_period_end"], "2017-03-31")
        self.assertEqual(report["latest_period_end"], "2026-03-31")
        self.assertEqual(report["authorizing_treatment_cell_count"], 0)
        self.assertEqual(report["authorizing_outcome_cell_count"], 0)
        self.assertEqual(report["estimation_eligible_row_count"], 0)
        self.assertFalse(report["publication_boundary"]["effect_estimation_authorized"])
        self.assertIsNone(report["publication_boundary"]["ai_attributable_increment"])
        self.assertEqual(report["output_sha256"], "sha256:" + hashlib.sha256(COMMITTED_CSV.read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "panel.csv"
            json_path = Path(directory) / "report.json"
            rebuilt = self._build(csv_path, json_path)
            self.assertEqual(csv_path.read_bytes(), COMMITTED_CSV.read_bytes())
            self.assertEqual(rebuilt, report)

    def test_rows_have_unique_balanced_keys_and_null_authorizing_fields(self) -> None:
        with COMMITTED_CSV.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len({row["panel_row_id"] for row in rows}), 555)
        self.assertEqual(len({(row["geography_id"], row["asset_class"], row["quarter"]) for row in rows}), 555)
        for row in rows:
            self.assertEqual(row["realized_ai_construction_spend_cad"], "")
            self.assertEqual(row["data_centre_construction_labour_hours"], "")
            self.assertEqual(row["public_project_cost_change"], "")
            self.assertEqual(row["public_project_schedule_change_days"], "")
            self.assertEqual(row["estimation_eligible"], "false")

    def test_missing_required_market_cell_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tampered = Path(directory) / "bcpi.csv"
            with AB_BCPI.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            fields = list(rows[0])
            removed = False
            with tampered.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                for row in rows:
                    if not removed and row["geography_id"] == "CMA_825" and row["indicator_id"] == "BCPI_SCHOOL_DIVISION_COMPOSITE" and row["period_end"] == "2026-03-31":
                        removed = True
                        continue
                    writer.writerow(row)
            with self.assertRaisesRegex(ValidationError, "required panel cell is missing"):
                self._build(Path(directory) / "out.csv", Path(directory) / "out.json", alberta_bcpi=tampered)


if __name__ == "__main__":
    unittest.main()
