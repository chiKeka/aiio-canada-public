from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from aiio.proxy_treatment import build_reconstructed_treatment_proxy
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
PROJECTS = ROOT / "data/processed/alberta_ai_projects.csv"
PERMITS = ROOT / "data/processed/edmonton_data_centre_permit_proxy.csv"
PROJECT_REPORT = ROOT / "data/model-runs/alberta_ai_capex_announcement_ledger_v0.1.json"
PERMIT_REPORT = ROOT / "data/model-runs/edmonton_data_centre_permit_proxy_v0.1.json"
COMMITTED_CSV = ROOT / "data/processed/ai_construction_proxy_alberta_v0.1.csv"
COMMITTED_REPORT = ROOT / "data/model-runs/ai_construction_proxy_alberta_v0.1.json"


class ProxyTreatmentTests(unittest.TestCase):
    def test_committed_proxy_reproduces_and_is_bounded(self) -> None:
        committed = json.loads(COMMITTED_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(committed["row_count"], 76)
        self.assertEqual(committed["costed_project_count"], 1)
        self.assertEqual(committed["permit_candidate_count"], 6)
        self.assertFalse(committed["publication_boundary"]["realized_treatment_authorized"])
        with COMMITTED_CSV.open(encoding="utf-8", newline="") as handle: rows = list(csv.DictReader(handle))
        for row in rows:
            low, central, high = (float(row[f"reconstructed_proxy_{case}_cad"]) for case in ("low", "central", "high"))
            self.assertLessEqual(low, central); self.assertLessEqual(central, high)
        with tempfile.TemporaryDirectory() as directory:
            csv_path, json_path = Path(directory) / "proxy.csv", Path(directory) / "proxy.json"
            rebuilt = build_reconstructed_treatment_proxy(ROOT, PROJECTS, PERMITS, PROJECT_REPORT, PERMIT_REPORT, csv_path, json_path)
            self.assertEqual(csv_path.read_bytes(), COMMITTED_CSV.read_bytes()); self.assertEqual(rebuilt, committed)

    def test_authorizing_input_boundary_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = json.loads(PROJECT_REPORT.read_text(encoding="utf-8")); report["publication_boundary"]["realized_construction_treatment_authorized"] = True
            path = Path(directory) / "report.json"; path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "must remain non-authorizing"):
                build_reconstructed_treatment_proxy(ROOT, PROJECTS, PERMITS, path, PERMIT_REPORT, Path(directory) / "out.csv", Path(directory) / "out.json")


if __name__ == "__main__": unittest.main()
