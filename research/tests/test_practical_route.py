import json
import tempfile
import unittest
from pathlib import Path

from aiio.practical_route import build_practical_evidence_route


ROOT = Path(__file__).resolve().parents[2]


class PracticalEvidenceRouteTests(unittest.TestCase):
    def test_committed_route_reproduces_and_preserves_boundary(self):
        committed = json.loads((ROOT / "data/model-runs/practical_evidence_route_current.json").read_text())
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            snapshot = Path(directory) / "snapshot.csv"
            report_path = Path(directory) / "report.json"
            rebuilt = build_practical_evidence_route(
                ROOT,
                committed["as_of_date"],
                ROOT / "data/processed/ai_construction_proxy_alberta_v0.1.csv",
                ROOT / "data/processed/public_projects_bc_on_qc.csv",
                ROOT / "data/processed/quebec_pqi_authorized_revision_events.csv",
                snapshot,
                report_path,
            )
            rebuilt["tracks"]["prospective_public_project_tracking"]["snapshot_path"] = "data/processed/public_project_prospective_snapshot_current.csv"
            rebuilt["output_manifest"] = committed["output_manifest"]
            self.assertEqual(rebuilt, committed)
            self.assertFalse(rebuilt["gate_evaluation"]["original_authorizing_evidence_gate_satisfied"])
            self.assertFalse(rebuilt["publication_boundary"]["causal_or_ai_attributable_claim"])

    def test_current_pipeline_has_two_region_proxy_and_three_province_baseline(self):
        report = json.loads((ROOT / "data/model-runs/practical_evidence_route_current.json").read_text())
        self.assertTrue(report["gate_evaluation"]["proxy_route_implemented"])
        self.assertTrue(report["gate_evaluation"]["prospective_baseline_implemented"])
        self.assertFalse(report["gate_evaluation"]["multi_region_revision_outcome_available"])
        self.assertTrue(all(cell["unit"] in {"CAD", "calendar_months"} for cell in report["tracks"]["authorized_revision_estimand"]["cells"]))


if __name__ == "__main__":
    unittest.main()
