import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from aiio.schemas import ValidationError
from aiio.vintage_linkage import CONTRACT, OUTPUT, PERMITS, inventory, review_permits, run_vintage_linkage, verify_local_archives

ROOT = Path(__file__).resolve().parents[2]


class VintageLinkageTests(unittest.TestCase):
    def test_report_reproduces_without_promoting_models(self):
        report, verification = run_vintage_linkage(ROOT)
        self.assertEqual(report, json.loads((ROOT / OUTPUT).read_text()))
        self.assertIsNone(verification)
        self.assertFalse(any(report["publication_boundary"].values()))
        self.assertEqual(len(report["forecast_origin_audit"]), 8)
        self.assertTrue(all(not r["sources_with_archived_snapshot_by_origin"] for r in report["forecast_origin_audit"]))
        self.assertEqual(len(report["included_permit_review"]), 6)
        self.assertEqual(len(report["facility_candidate_groups"]), 5)
        self.assertTrue(all(not r["confirmed_link"] for r in report["facility_candidate_groups"]))
        self.assertEqual(report["component_overlap"]["simultaneously_positive_market_quarter_cells"], 0)
        self.assertFalse(report["component_overlap"]["permits_deduplicated"])
        horizon = report["schedule_horizon_audit"][0]
        self.assertEqual(horizon["full_schedule_quarters"], 12)
        self.assertEqual(horizon["archived_proxy_window_quarters"], 10)
        self.assertLess(horizon["full_schedule_denominator_allocation_cad"], horizon["v0_1_clipped_schedule_allocation_cad"])
        self.assertFalse(horizon["model_modified"])

    def test_identical_downloads_do_not_become_distinct_vintages(self):
        report, _ = run_vintage_linkage(ROOT)
        edmonton = next(r for r in report["archive_inventory"] if r["source_id"] == "EDMONTON_GENERAL_BUILDING_PERMITS")
        self.assertEqual(edmonton["retrieval_count"], 3)
        self.assertEqual(edmonton["distinct_content_count"], 1)

    def test_review_requires_full_coverage_and_matching_description_hash(self):
        contract = json.loads((ROOT / CONTRACT).read_text())
        draft = json.loads((ROOT / contract["review_path"]).read_text())
        with (ROOT / PERMITS).open(newline="") as handle:
            permits = list(csv.DictReader(handle))
        for mutation, message in [("missing", "every included permit"), ("duplicate", "every included permit"), ("hash", "description"), ("confirmed", "unconfirmed")]:
            modified = copy.deepcopy(draft)
            if mutation == "missing":
                modified["records"].pop()
            elif mutation == "duplicate":
                modified["records"].append(modified["records"][0])
            elif mutation == "hash":
                modified["records"][0]["description_sha256"] = "sha256:bad"
            else:
                modified["records"][0]["facility_match_status"] = "confirmed"
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValidationError, message):
                review_permits(permits, modified, "2017-01-01", "2026-06-30")

    def test_missing_raw_bytes_do_not_count_as_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            records = [{"source_id": "EDMONTON_GENERAL_BUILDING_PERMITS", "retrievals": [{"content_hash": "sha256:missing", "archive_path": "missing.json"}]}]
            with self.assertRaisesRegex(ValidationError, "unavailable"):
                verify_local_archives(Path(folder), records, [])

    def test_manifest_paths_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValidationError, "escapes"):
                inventory(Path(folder), ["../outside.json"], "TEST")

    def test_contract_rejects_input_drift_and_authorization(self):
        contract = json.loads((ROOT / CONTRACT).read_text())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / CONTRACT
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValidationError, "input drift"):
                run_vintage_linkage(root)
            contract["publication_boundary"]["validated_proxy_estimate_allowed"] = True
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValidationError, "authorizing"):
                run_vintage_linkage(root)
