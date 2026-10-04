from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from aiio.digest import (
    build_digest,
    find_latest_digest_items,
    sha256_file,
    validate_digest_cadence,
    publish_reviewed_digest,
)
from aiio.schemas import ValidationError


class DigestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.items_dir = self.root / "items"
        self.items_dir.mkdir()
        self.items_path = self.items_dir / "2026-09-01.json"
        self.output_path = self.root / "2026-09-01.md"
        self.registry_path = self.root / "sources.json"
        self.registry_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "source_id": "SOURCE_A",
                            "canonical_url": "https://example.test/a",
                        },
                        {
                            "source_id": "SOURCE_B",
                            "canonical_url": "https://example.test/b",
                        },
                    ]
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.payload = {
            "schema_version": "1.1.0",
            "digest_id": "AIIO_DIGEST_2026_09_01",
            "edition_date": "2026-09-01",
            "status": "review",
            "items": [
                {
                    "item_id": "ITEM_01",
                    "headline": "Two public sources were reconciled",
                    "sources": [
                        {
                            "source_id": "SOURCE_A",
                            "source_url": "https://example.test/a",
                        },
                        {
                            "source_id": "SOURCE_B",
                            "source_url": "https://example.test/b",
                        },
                    ],
                    "observed_change": "The public sources report distinct quantities.",
                    "model_implication": "Keep their units separate.",
                    "evidence_status": "inferred",
                    "geography_ids": ["PR_35", "PR_59"],
                    "model_action": "no_change",
                    "automatic_model_change": False,
                }
            ],
        }
        self.write_payload()

    def write_payload(self) -> None:
        self.items_path.write_text(
            json.dumps(self.payload, indent=2) + "\n", encoding="utf-8"
        )

    def build(self) -> dict:
        return build_digest(
            self.items_path,
            self.output_path,
            date(2026, 9, 1),
            source_registry_path=self.registry_path,
        )

    def test_builds_registry_bound_digest_and_manifest(self) -> None:
        manifest = self.build()
        self.assertEqual(manifest["item_count"], 1)
        self.assertEqual(manifest["source_ids"], ["SOURCE_A", "SOURCE_B"])
        self.assertFalse(manifest["automatic_model_change"])
        self.assertEqual(manifest["items_sha256"], sha256_file(self.items_path))
        self.assertEqual(manifest["markdown_sha256"], sha256_file(self.output_path))
        self.assertTrue(self.output_path.with_suffix(".manifest.json").exists())
        markdown = self.output_path.read_text(encoding="utf-8")
        self.assertIn("no automatic parameter or baseline change", markdown)
        self.assertIn("[SOURCE_B](https://example.test/b)", markdown)

    def test_approved_digest_requires_pinned_internal_editorial_receipt(self):
        registry = self.root / 'data/registry/sources.json'
        registry.parent.mkdir(parents=True)
        registry.write_bytes(self.registry_path.read_bytes())
        candidate = self.root / 'candidate.json'
        candidate.write_bytes(self.items_path.read_bytes())
        self.payload['status'] = 'approved'
        self.write_payload()
        with self.assertRaisesRegex(ValidationError, 'approval receipt'):
            build_digest(self.items_path, self.output_path, date(2026,9,1), source_registry_path=registry)
        artifact = self.root / 'source.json'
        artifact.write_text('{"verified": true}')
        receipt = {'scope': 'evidence_digest_only', 'decision': 'approved', 'reviewer_role': 'internal_editorial', 'reviewer': 'Internal editorial agent', 'reviewed_at': '2026-09-01T12:00:00Z', 'automatic_model_change': False, 'independent_model_review_waived': False, 'items_sha256': sha256_file(self.items_path), 'source_registry_sha256': sha256_file(registry), 'candidate_items_path': 'candidate.json', 'candidate_items_sha256': sha256_file(candidate), 'source_artifacts': [{'source_id': source_id, 'path': 'source.json', 'sha256': sha256_file(artifact)} for source_id in ('SOURCE_A','SOURCE_B')]}
        receipt_path = self.root / 'approval.json'
        def approve():
            receipt_path.write_text(json.dumps(receipt))
            return build_digest(self.items_path, self.output_path, date(2026,9,1), source_registry_path=registry, approval_receipt_path=receipt_path)
        approved = approve()
        publish_reviewed_digest(self.root, self.items_path, approved, receipt_path)
        pointer_path = self.root / 'public/data/latest-digest.json'
        self.assertEqual(json.loads(pointer_path.read_text())['status'], 'approved')
        self.assertEqual(json.loads((self.root / 'public/data/reviewed-digest.json').read_text()), self.payload)
        pointer_before = pointer_path.read_bytes()
        publish_reviewed_digest(self.root, candidate, {'status': 'review'}, receipt_path)
        self.assertEqual(pointer_path.read_bytes(), pointer_before)
        self.assertFalse(approved['editorial_approval']['independent_model_review_waived'])
        self.assertEqual(json.loads(candidate.read_text())['status'], 'review')
        before = self.output_path.read_bytes()
        artifact.write_text('{"verified": false}')
        with self.assertRaisesRegex(ValidationError, 'hash mismatch'):
            approve()
        with self.assertRaisesRegex(ValidationError, 'hash mismatch'):
            publish_reviewed_digest(self.root, self.items_path, approved, receipt_path)
        self.assertEqual(pointer_path.read_bytes(), pointer_before)
        self.assertEqual(self.output_path.read_bytes(), before)
        artifact.write_text('{"verified": true}')
        receipt['independent_model_review_waived'] = True
        with self.assertRaisesRegex(ValidationError, 'without waiving'):
            approve()

    def test_legacy_single_source_shape_remains_valid(self) -> None:
        item = self.payload["items"][0]
        item.pop("sources")
        item["source_id"] = "SOURCE_A"
        item["source_url"] = "https://example.test/a"
        self.write_payload()
        manifest = self.build()
        self.assertEqual(manifest["source_ids"], ["SOURCE_A"])

    def test_rejects_edition_date_mismatch(self) -> None:
        self.payload["edition_date"] = "2026-08-31"
        self.write_payload()
        with self.assertRaisesRegex(ValidationError, "must match"):
            self.build()

    def test_rejects_unregistered_or_mismatched_source_url(self) -> None:
        self.payload["items"][0]["sources"][0]["source_url"] = (
            "https://example.test/not-canonical"
        )
        self.write_payload()
        with self.assertRaisesRegex(ValidationError, "does not match registry"):
            self.build()

    def test_rejects_automatic_model_change(self) -> None:
        self.payload["items"][0]["automatic_model_change"] = True
        self.write_payload()
        with self.assertRaisesRegex(ValidationError, "cannot authorize"):
            self.build()

    def test_rejects_scenario_as_new_evidence(self) -> None:
        self.payload["items"][0]["evidence_status"] = "scenario"
        self.write_payload()
        with self.assertRaisesRegex(ValidationError, "assumptions or scenarios"):
            self.build()

    def test_cadence_accepts_current_edition_and_rejects_stale_one(self) -> None:
        current = validate_digest_cadence(
            self.items_dir, as_of_date=date(2026, 9, 8), max_age_days=8
        )
        self.assertEqual(current["age_days"], 7)
        with self.assertRaisesRegex(ValidationError, "stale"):
            validate_digest_cadence(
                self.items_dir, as_of_date=date(2026, 9, 10), max_age_days=8
            )

    def test_cadence_rejects_filename_payload_date_mismatch(self) -> None:
        self.payload["edition_date"] = "2026-08-31"
        self.write_payload()
        with self.assertRaisesRegex(ValidationError, "disagree"):
            validate_digest_cadence(
                self.items_dir, as_of_date=date(2026, 9, 1), max_age_days=8
            )

    def test_latest_selector_uses_newest_valid_dated_intake(self) -> None:
        older_path = self.items_dir / "2026-08-25.json"
        older_path.write_text(
            json.dumps({"edition_date": "2026-08-25", "items": []}) + "\n",
            encoding="utf-8",
        )
        (self.items_dir / "README.json").write_text("{}\n", encoding="utf-8")
        edition_date, path = find_latest_digest_items(self.items_dir)
        self.assertEqual(edition_date, date(2026, 9, 1))
        self.assertEqual(path, self.items_path)

    def test_latest_selector_rejects_date_drift_and_empty_directory(self) -> None:
        self.payload["edition_date"] = "2026-08-31"
        self.write_payload()
        with self.assertRaisesRegex(ValidationError, "disagree"):
            find_latest_digest_items(self.items_dir)
        self.items_path.unlink()
        with self.assertRaisesRegex(ValidationError, "no dated digest"):
            find_latest_digest_items(self.items_dir)


if __name__ == "__main__":
    unittest.main()
