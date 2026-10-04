from __future__ import annotations

import glob
import json
import tempfile
import unittest
from pathlib import Path

from aiio.pspc_outcomes import normalize_pspc_outcomes


ROOT = Path(__file__).resolve().parents[2]
INPUT = Path(glob.glob(str(ROOT / "data/raw/pspc_real_property_project_performance_2024_2025/*.csv"))[0])
COMMITTED_CSV = ROOT / "data/processed/pspc_real_property_outcome_context_2024_2025.csv"
COMMITTED_REPORT = ROOT / "data/model-runs/pspc_real_property_outcome_feasibility_v0.1.json"


class PspcOutcomeTests(unittest.TestCase):
    def test_committed_context_reproduces_and_does_not_authorize_outcome(self) -> None:
        committed = json.loads(COMMITTED_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(committed["record_count"], 691)
        self.assertFalse(committed["field_availability"]["geography_id"])
        self.assertFalse(committed["field_availability"]["estimate_and_outturn_cost"])
        self.assertFalse(committed["publication_boundary"]["project_outcome_authorized"])
        with tempfile.TemporaryDirectory() as directory:
            csv_path, report_path = Path(directory) / "out.csv", Path(directory) / "out.json"
            rebuilt = normalize_pspc_outcomes(INPUT, csv_path, report_path)
            self.assertEqual(csv_path.read_bytes(), COMMITTED_CSV.read_bytes()); self.assertEqual(rebuilt, committed)


if __name__ == "__main__": unittest.main()
