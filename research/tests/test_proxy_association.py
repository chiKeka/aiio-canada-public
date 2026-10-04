from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aiio.proxy_association import run_proxy_association


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data/processed/ai_attribution_empirical_covariate_panel_v0.1.csv"
REPORT = ROOT / "data/model-runs/ai_attribution_empirical_covariate_panel_v0.1.json"
COMMITTED = ROOT / "data/model-runs/ai_attribution_proxy_association_v0.1.json"


class ProxyAssociationTests(unittest.TestCase):
    def test_committed_association_reproduces_and_stays_noncausal(self) -> None:
        committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
        self.assertEqual([row["proxy_case"] for row in committed["results"]], ["low", "central", "high"])
        self.assertTrue(all(row["observation_count"] == 99 for row in committed["results"]))
        self.assertTrue(all(row["confidence_interval_95"][0] <= 0 <= row["confidence_interval_95"][1] for row in committed["results"]))
        self.assertIsNone(committed["publication_boundary"]["ai_attributable_effect"])
        self.assertFalse(committed["publication_boundary"]["executive_calibration_authorized"])
        with tempfile.TemporaryDirectory() as directory:
            rebuilt = run_proxy_association(PANEL, REPORT, Path(directory) / "out.json")
            self.assertEqual(rebuilt, committed)


if __name__ == "__main__": unittest.main()
