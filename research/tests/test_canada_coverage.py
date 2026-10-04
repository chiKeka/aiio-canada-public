import json
import tempfile
import unittest
from pathlib import Path

from aiio.canada_coverage import (
    build_canada_cross_domain_coverage,
    validate_canada_cross_domain_coverage,
)
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "data/model-runs/canada_cross_domain_coverage_v0.1.json"


class CanadaCoverageTests(unittest.TestCase):
    def test_committed_report_reproduces(self):
        self.assertEqual(validate_canada_cross_domain_coverage(ROOT, REPORT)["matrix_cell_count"], 91)

    def test_scope_and_fail_closed_boundary(self):
        report = build_canada_cross_domain_coverage(ROOT)
        self.assertEqual((report["geography_count"], report["domain_count"]), (13, 7))
        boundary = report["publication_boundary"]
        self.assertFalse(boundary["cross_province_comparison_authorized"])
        self.assertFalse(boundary["province_model_calibration_authorized"])
        self.assertFalse(boundary["missingness_imputed"])
        self.assertFalse(boundary["ai_attributable_effect_authorized"])

    def test_known_coverage_and_gaps_are_explicit(self):
        report = build_canada_cross_domain_coverage(ROOT)
        rows = {row["geography_id"]: row["domains"] for row in report["geographies"]}
        self.assertEqual(rows["PR_11"]["materials"]["status"], "not_available")
        for geography_id in ("PR_60", "PR_61", "PR_62"):
            self.assertEqual(rows[geography_id]["materials"]["status"], "not_available")
        for geography_id in ("PR_24", "PR_35", "PR_48", "PR_59"):
            self.assertEqual(rows[geography_id]["public_projects"]["status"], "available")
            self.assertEqual(rows[geography_id]["power_planning"]["status"], "available")
        self.assertEqual(rows["PR_10"]["public_projects"]["status"], "not_available")

    def test_tampered_report_is_rejected(self):
        payload = json.loads(REPORT.read_text())
        payload["publication_boundary"]["cross_province_comparison_authorized"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.json"
            path.write_text(json.dumps(payload))
            with self.assertRaises(ValidationError):
                validate_canada_cross_domain_coverage(ROOT, path)


if __name__ == "__main__":
    unittest.main()
