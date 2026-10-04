import json
import tempfile
import unittest
from pathlib import Path

from aiio.planning_validation import assess_proxy_planning, PROXY_REPORT, PROXY_ROWS
from aiio.schemas import ValidationError

ROOT = Path(__file__).resolve().parents[2]


class ProxyPlanningValidationTests(unittest.TestCase):
    def test_current_assessment_reproduces_and_separates_claims(self):
        report = assess_proxy_planning(ROOT)
        committed = json.loads((ROOT / "data/model-runs/practical_evidence_route_current.json").read_text())
        self.assertEqual(report, committed["proxy_planning_validation"])
        self.assertEqual(report["passed_check_count"], 2)
        self.assertEqual(report["check_count"], 7)
        boundary = report["publication_boundary"]
        self.assertTrue(boundary["scenario_sensitivity_allowed"])
        self.assertFalse(boundary["validated_proxy_estimate_allowed"])
        self.assertFalse(boundary["causal_attribution_allowed"])
        self.assertFalse(boundary["requires_private_realized_spending_or_labour_hours"])
        self.assertIsNone(boundary["ai_attributable_effect"])

    def test_missing_validation_is_not_a_pass(self):
        checks = {c["id"]: c["status"] for c in assess_proxy_planning(ROOT)["checks"]}
        for key in ("scope_coverage", "timing_validation", "out_of_sample_performance", "overlap_and_double_counting", "independent_planning_review"):
            self.assertEqual(checks[key], "not_assessed")

    def test_source_drift_is_rejected(self):
        from aiio.planning_validation import ASSOCIATION_REPORT
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in (PROXY_REPORT, ASSOCIATION_REPORT):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / name).read_bytes())
            proxy = json.loads((root / PROXY_REPORT).read_text())
            for name in (*proxy["input_manifest"], PROXY_ROWS):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / name).read_bytes())
            self.assertEqual(assess_proxy_planning(root)["passed_check_count"], 2)
            with (root / PROXY_ROWS).open("a") as handle:
                handle.write("tampered\n")
            with self.assertRaises(ValidationError):
                assess_proxy_planning(root)
