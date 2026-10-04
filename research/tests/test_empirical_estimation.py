from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from aiio.empirical_estimation import run_empirical_estimation_gate
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/model/ai_attribution_panel_contract_v0.1.json"
PANEL = ROOT / "data/processed/ai_attribution_empirical_covariate_panel_v0.1.csv"
PANEL_REPORT = ROOT / "data/model-runs/ai_attribution_empirical_covariate_panel_v0.1.json"
COMMITTED = ROOT / "data/model-runs/ai_attribution_empirical_estimation_v0.1.json"


class EmpiricalEstimationGateTests(unittest.TestCase):
    def test_committed_gate_reproduces_and_withholds_effects(self) -> None:
        committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
        self.assertEqual(committed["status"], "withheld_ineligible_panel")
        self.assertEqual(committed["panel_summary"]["row_count"], 555)
        self.assertEqual(committed["panel_summary"]["authorizing_treated_region_count"], 0)
        self.assertEqual(committed["panel_summary"]["estimation_eligible_row_count"], 0)
        self.assertTrue(all(value is None for value in committed["estimates"].values()))
        self.assertEqual(len(committed["diagnostic_plan"]), 7)
        self.assertFalse(committed["publication_boundary"]["effect_publication_authorized"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run.json"
            rebuilt = run_empirical_estimation_gate(ROOT, CONTRACT, PANEL, PANEL_REPORT, output)
            self.assertEqual(rebuilt, committed)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), committed)

    def test_panel_hash_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            panel = Path(directory) / "panel.csv"
            shutil.copy2(PANEL, panel)
            with panel.open("a", encoding="utf-8") as handle: handle.write("tampered\n")
            with self.assertRaisesRegex(ValidationError, "hash mismatch"):
                run_empirical_estimation_gate(ROOT, CONTRACT, panel, PANEL_REPORT, Path(directory) / "run.json")

    def test_premature_eligible_row_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            panel = Path(directory) / "panel.csv"
            report = Path(directory) / "report.json"
            with PANEL.open(encoding="utf-8", newline="") as source:
                rows = list(csv.DictReader(source)); fields = list(rows[0])
            rows[0]["estimation_eligible"] = "true"
            with panel.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
            payload = json.loads(PANEL_REPORT.read_text(encoding="utf-8"))
            payload["output_sha256"] = "sha256:" + hashlib.sha256(panel.read_bytes()).hexdigest()
            report.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "lack authorizing treatment or outcomes"):
                run_empirical_estimation_gate(ROOT, CONTRACT, panel, report, Path(directory) / "run.json")


if __name__ == "__main__":
    unittest.main()
