import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from aiio.schemas import ValidationError

SPEC = importlib.util.spec_from_file_location("project_vintage_intake", Path(__file__).resolve().parents[1] / "scripts/project_vintage_intake.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProjectVintageIntakeTests(unittest.TestCase):
    def test_candidate_binds_capture_and_preserves_released_input(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            baseline = root / "data/processed/public_project_exposure_alberta.csv"
            baseline.parent.mkdir(parents=True)
            fields = ["project_id", "source_id", "as_of_date", "name", "asset_class", "stage", "estimated_cost_cad", "start_year", "end_year"]
            baseline.write_text(",".join(fields) + "\nABMP_1,ALBERTA_MAJOR_PROJECTS,2026-08-31,Hospital,health_facilities,Proposed,100.0,2026,2027\n")
            original = baseline.read_bytes()
            raw = root / "capture.csv"
            raw_fields = ["Id", "Name", "Estimated Cost", "Municipality", "Schedule", "Sector", "Type", "Power Generation Capacity (MW)", "Stage", "Developer", "Project Website", "Location", "Detail"]
            values = ["1", "Hospital", "200", "Edmonton", "2026-2027", "Institutional", "Health Care", "", "Under Construction", "Alberta Infrastructure", "", "", ""]
            with raw.open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(raw_fields)
                writer.writerow(values)
            receipt = root / "manifest.json"
            receipt.write_text(json.dumps({"source_id": "ALBERTA_MAJOR_PROJECTS", "content_hash": "sha256:" + hashlib.sha256(raw.read_bytes()).hexdigest(), "result": "success", "retrieved_at": "2026-10-03T20:18:09+00:00"}))
            report = MODULE.intake(root, raw, receipt, root / "candidate")
            self.assertEqual(baseline.read_bytes(), original)
            self.assertEqual(report["status"], "review_pending")
            self.assertEqual(len(report["events"]), 1)
            self.assertFalse(report["publisher_revision_effective_dates_available"])
            self.assertFalse(report["publication_boundary"]["published_inputs_replaced"])
            receipt.write_text(json.dumps({"source_id": "ALBERTA_MAJOR_PROJECTS", "content_hash": "wrong", "result": "success"}))
            with self.assertRaises(ValidationError):
                MODULE.intake(root, raw, receipt, root / "rejected")


if __name__ == "__main__":
    unittest.main()
