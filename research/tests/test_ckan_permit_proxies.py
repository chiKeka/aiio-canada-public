from __future__ import annotations

import csv, hashlib, json, tempfile, unittest
from pathlib import Path

from aiio.adapters.ckan_permit_proxies import FIELDS, normalize_ckan_permit_proxy
from aiio.schemas import ValidationError


class CkanPermitProxyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root = Path(self.temp.name)

    def run_case(self, city: str, source_id: str, record: dict[str, object]) -> tuple[list[dict[str, str]], dict[str, object]]:
        raw = self.root / f"{city}.json"; raw.write_text(json.dumps({"source_id": source_id, "records": [record]}), encoding="utf-8")
        manifest = raw.with_suffix(".json.manifest.json"); manifest.write_text(json.dumps({"content_hash": "sha256:" + hashlib.sha256(raw.read_bytes()).hexdigest()}), encoding="utf-8")
        output = self.root / f"{city}.csv"; report = self.root / f"{city}-report.json"
        result = normalize_ckan_permit_proxy(city, raw, output, report, source_as_of_date="2026-09-02", retrieval_manifest_path=manifest)
        with output.open(encoding="utf-8", newline="") as handle: reader = csv.DictReader(handle); rows = list(reader); self.assertEqual(set(reader.fieldnames or ()), set(FIELDS))
        return rows, result

    def test_toronto_preserves_completion_duration_and_cost_proxy(self) -> None:
        rows, report = self.run_case("toronto", "TORONTO_CLEARED_BUILDING_PERMITS", {"PERMIT_NUM": "22-1", "REVISION_NUM": "00", "APPLICATION_DATE": "2022-01-01", "ISSUED_DATE": "2022-02-01", "COMPLETED_DATE": "2023-02-01", "DESCRIPTION": "Construct a data center", "PERMIT_TYPE": "Building", "WORK": "New", "EST_CONST_COST": "$1,250,000"})
        self.assertEqual(rows[0]["issue_to_completion_days"], "365"); self.assertEqual(rows[0]["reported_estimated_construction_value_cad"], "1250000.00")
        self.assertTrue(report["publication_boundary"]["permit_completion_duration_authorized"]); self.assertFalse(report["publication_boundary"]["causal_effect_authorized"])

    def test_montreal_preserves_bilingual_facility_match_without_cost(self) -> None:
        rows, report = self.run_case("montreal", "MONTREAL_CONSTRUCTION_PERMITS", {"id_permis": "1", "date_debut": "2022-01-01", "date_emission": "2022-03-01", "nature_travaux": "Aménagement d'un centre de données", "description_type_demande": "Transformation", "description_type_batiment": "Commercial"})
        self.assertEqual(rows[0]["candidate_status"], "data_centre_candidate"); self.assertEqual(rows[0]["construction_value_status"], "not_available")
        self.assertFalse(report["publication_boundary"]["permit_completion_duration_authorized"])

    def test_hash_drift_fails_closed(self) -> None:
        raw = self.root / "bad.json"; raw.write_text(json.dumps({"source_id": "TORONTO_CLEARED_BUILDING_PERMITS", "records": [{}]}), encoding="utf-8")
        manifest = raw.with_suffix(".json.manifest.json"); manifest.write_text(json.dumps({"content_hash": "sha256:bad"}), encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "hash mismatch"):
            normalize_ckan_permit_proxy("toronto", raw, self.root / "x.csv", self.root / "x.json", source_as_of_date="2026-09-02", retrieval_manifest_path=manifest)

    def test_committed_artifacts_are_hash_locked(self) -> None:
        root = Path(__file__).resolve().parents[2]
        for city in ("toronto", "montreal"):
            output = root / f"data/processed/{city}_data_centre_permit_proxy.csv"; report = root / f"data/model-runs/{city}_data_centre_permit_proxy_v0.1.json"
            if not output.exists() or not report.exists(): self.skipTest("artifacts not built")
            payload = json.loads(report.read_text(encoding="utf-8")); self.assertEqual(payload["output_sha256"], "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest()); self.assertGreater(payload["data_centre_candidate_count"], 0)


if __name__ == "__main__": unittest.main()
