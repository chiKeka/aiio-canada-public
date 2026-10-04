from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.adapters.vancouver_permits import OUTPUT_FIELDS, normalize_vancouver_permit_proxy
from aiio.schemas import ValidationError


class VancouverPermitProxyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.raw = self.root / "raw.json"
        self.output = self.root / "output.csv"; self.report = self.root / "report.json"

    def test_normalizes_explicit_facility_and_withholds_causal_status(self) -> None:
        self.raw.write_text(json.dumps({"results": [{
            "permitnumber": "BP-1", "permitnumbercreateddate": "2025-01-01",
            "issuedate": "2025-04-01", "permitelapseddays": 90, "projectvalue": 75000000,
            "typeofwork": "New Building", "projectdescription": "Construct a three-storey Data Center",
            "specificusecategory": ["Bulk Data Storage"], "issueyear": "2025", "yearmonth": "2025-04",
        }]}), encoding="utf-8")
        report = normalize_vancouver_permit_proxy(self.raw, self.output, self.report, source_as_of_date="2026-09-02")
        with self.output.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle); rows = list(reader)
        self.assertEqual(set(reader.fieldnames or ()), set(OUTPUT_FIELDS))
        self.assertEqual(rows[0]["candidate_status"], "data_centre_candidate")
        self.assertEqual(rows[0]["reported_estimated_construction_value_cad"], "75000000.00")
        self.assertFalse(report["publication_boundary"]["realized_ai_construction_treatment_authorized"])
        self.assertNotIn("projectdescription", rows[0])

    def test_rejects_schema_drift_and_manifest_tampering(self) -> None:
        self.raw.write_text(json.dumps({"results": [{"permitnumber": "BP-1"}]}), encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "schema changed"):
            normalize_vancouver_permit_proxy(self.raw, self.output, self.report, source_as_of_date="2026-09-02")
        self.raw.write_text(json.dumps({"results": [{"permitnumber": "BP-1", "issuedate": "2025-01-01", "projectdescription": "data centre", "typeofwork": "New"}]}), encoding="utf-8")
        manifest = self.root / "raw.json.manifest.json"; manifest.write_text(json.dumps({"content_hash": "sha256:bad"}), encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "hash mismatch"):
            normalize_vancouver_permit_proxy(self.raw, self.output, self.report, source_as_of_date="2026-09-02", retrieval_manifest_path=manifest)

    def test_committed_artifact_is_hash_locked(self) -> None:
        root = Path(__file__).resolve().parents[2]
        output = root / "data/processed/vancouver_data_centre_permit_proxy.csv"
        report = root / "data/model-runs/vancouver_data_centre_permit_proxy_v0.1.json"
        if not output.exists() or not report.exists(): self.skipTest("artifact not built")
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["output_sha256"], "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest())
        self.assertGreater(payload["data_centre_candidate_count"], 0)
        self.assertFalse(payload["publication_boundary"]["causal_effect_authorized"])


if __name__ == "__main__": unittest.main()
