from __future__ import annotations

import csv, json, tempfile, unittest
from pathlib import Path

from aiio.comparison_market_association import run_comparison_market_association
from aiio.comparison_market_panel import build_comparison_market_panel

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/processed/comparison_market_permit_bcpi_panel_v0.1.csv"
REPORT = ROOT / "data/model-runs/comparison_market_permit_bcpi_panel_v0.1.json"
ASSOCIATION = ROOT / "data/model-runs/comparison_market_proxy_association_v0.1.json"


class ComparisonMarketPanelTests(unittest.TestCase):
    def test_committed_panel_reproduces_on_common_support(self) -> None:
        committed = json.loads(REPORT.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            out_csv = Path(directory) / "panel.csv"; out_json = Path(directory) / "panel.json"
            rebuilt = build_comparison_market_panel(ROOT, ROOT / "data/processed/bcpi_reference_van_tor_mtl.csv", {city: ROOT / f"data/processed/{city}_data_centre_permit_proxy.csv" for city in ("vancouver", "toronto", "montreal")}, {city: ROOT / f"data/model-runs/{city}_data_centre_permit_proxy_v0.1.json" for city in ("vancouver", "toronto", "montreal")}, out_csv, out_json)
            self.assertEqual(rebuilt, committed)
        with PANEL.open(encoding="utf-8", newline="") as handle: rows = list(csv.DictReader(handle))
        self.assertEqual({row["market"] for row in rows}, {"vancouver", "toronto", "montreal"})
        self.assertTrue(all("2017-Q1" <= row["quarter"] <= "2026-Q2" for row in rows))
        self.assertEqual(committed["quarter_count"], 38)
        self.assertFalse(committed["publication_boundary"]["executive_calibration_authorized"])

    def test_committed_association_reproduces_and_stays_noncausal(self) -> None:
        committed = json.loads(ASSOCIATION.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            rebuilt = run_comparison_market_association(PANEL, REPORT, Path(directory) / "association.json")
            self.assertEqual(rebuilt, committed)
        self.assertIsNone(committed["publication_boundary"]["ai_attributable_effect"])
        self.assertFalse(committed["publication_boundary"]["causal_interpretation_authorized"])


if __name__ == "__main__": unittest.main()
