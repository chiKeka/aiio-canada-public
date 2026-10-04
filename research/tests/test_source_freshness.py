import json
import tempfile
import unittest
from pathlib import Path

from aiio.schemas import ValidationError
from aiio.source_freshness import build_source_freshness_report


ROOT = Path(__file__).resolve().parents[2]


class SourceFreshnessTests(unittest.TestCase):
    def test_committed_report_is_reproducible_and_current(self):
        committed = json.loads((ROOT / "public/data/source-freshness.json").read_text())
        rebuilt = build_source_freshness_report(
            ROOT / "data/registry/sources.json", committed["as_of_date"]
        )
        self.assertEqual(rebuilt, committed)
        self.assertEqual(rebuilt["status"], "operational")
        self.assertEqual(rebuilt["stale_count"], 0)

    def test_operational_receipts_reproduce_without_advancing_frozen_release(self):
        committed = json.loads((ROOT / "public/data/source-receipts.json").read_text())
        self.assertEqual(build_source_freshness_report(ROOT / "data/registry/sources.json", committed["as_of_date"]), committed)
        frozen = json.loads((ROOT / "public/data/source-freshness.json").read_text())
        self.assertLessEqual(frozen["as_of_date"], committed["as_of_date"])
        self.assertEqual(build_source_freshness_report(ROOT / "data/registry/sources.json", frozen["as_of_date"]), frozen)
        self.assertEqual(committed["source_count"], len(committed["sources"]))
        for item in committed["sources"]:
            if item["last_success"]:
                self.assertEqual(item["verification_basis"], "successful_retrieval_receipt")
                self.assertLessEqual(item["last_success"], committed["as_of_date"])

    def test_stale_daily_source_degrades_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            registry = json.loads((ROOT / "data/registry/sources.json").read_text())
            registry["sources"] = [registry["sources"][1]]
            registry["sources"][0]["last_verified"] = "2026-01-01"
            path.write_text(json.dumps(registry))
            report = build_source_freshness_report(path, "2026-09-03")
            self.assertEqual(report["status"], "degraded")
            self.assertEqual(report["stale_source_ids"], ["TORONTO_CLEARED_BUILDING_PERMITS"])

    def test_receipt_success_and_failure_are_separate_from_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry_path = root / "data/registry/sources.json"
            registry_path.parent.mkdir(parents=True)
            registry = json.loads((ROOT / "data/registry/sources.json").read_text())
            registry["sources"] = [registry["sources"][1]]
            registry["sources"][0]["last_verified"] = "2026-01-01"
            registry_path.write_text(json.dumps(registry))
            receipts = root / "data/model-runs/construction-source-refresh.json"
            receipts.parent.mkdir(parents=True)
            receipts.write_text(json.dumps({"sources": {"TORONTO_CLEARED_BUILDING_PERMITS": {
                "last_success": "2026-09-01", "last_attempt": "2026-09-20", "status": "error",
                "observation_date": "2026-08-01"}}}))
            report = build_source_freshness_report(registry_path, "2026-09-20")
            item = report["sources"][0]
            self.assertEqual(item["age_days"], 19)
            self.assertEqual(item["last_success"], "2026-09-01")
            self.assertEqual(item["last_attempt"], "2026-09-20")
            self.assertEqual(item["observation_date"], "2026-08-01")
            self.assertEqual(item["freshness_state"], "stale")

    def test_unknown_frequency_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            registry = json.loads((ROOT / "data/registry/sources.json").read_text())
            registry["sources"] = [registry["sources"][1]]
            registry["sources"][0]["update_frequency"] = "whenever convenient"
            path.write_text(json.dumps(registry))
            with self.assertRaises(ValidationError):
                build_source_freshness_report(path, "2026-09-03")


if __name__ == "__main__":
    unittest.main()
