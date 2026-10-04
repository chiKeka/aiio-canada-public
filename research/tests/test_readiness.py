from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from aiio.readiness import (
    BLOCKED,
    FAIL,
    PASS,
    PENDING,
    audit_digest_artifacts,
    audit_frozen_release,
    require_release_ready,
    select_latest_workbook,
    sha256_file,
    summarize_readiness,
    validate_workbook_receipt,
)
from aiio.schemas import ValidationError


class ReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def test_summary_separates_integrity_from_release_readiness(self) -> None:
        report = summarize_readiness(
            [
                {
                    "check_id": "built",
                    "category": "research_design",
                    "status": PASS,
                    "release_gate": True,
                },
                {
                    "check_id": "review",
                    "category": "governance",
                    "status": BLOCKED,
                    "release_gate": True,
                },
                {
                    "check_id": "calibration",
                    "category": "decision_grade_outputs",
                    "status": PENDING,
                    "release_gate": True,
                },
            ],
            as_of_date=date(2026, 9, 1),
        )
        self.assertTrue(report["structural_integrity"])
        self.assertFalse(report["decision_grade_ready"])
        self.assertFalse(report["release_ready"])
        with self.assertRaisesRegex(ValidationError, "review, calibration"):
            require_release_ready(report)

    def test_latest_workbook_uses_semantic_version_order(self) -> None:
        candidates = [
            self.root / "AIIO_Canada_Research_0.9.0-dev.xlsx",
            self.root / "AIIO_Canada_Research_0.11.0-dev.xlsx",
            self.root / "AIIO_Canada_Research_0.12.0-dev.xlsx",
        ]
        self.assertEqual(select_latest_workbook(candidates), candidates[2])

    def test_workbook_receipt_hash_locks_builder_inspection_and_coverage(self) -> None:
        workbook = self.root / "outputs/run/AIIO_Canada_Research_0.27.0-dev.xlsx"
        inspection = workbook.with_suffix(".xlsx.inspect.ndjson")
        receipt_path = workbook.with_suffix(".xlsx.receipt.json")
        builder = self.root / "workbook-work/build_aiio_workbook.mjs"
        coverage = self.root / "data/model-runs/canada_cross_domain_coverage_v0.1.json"
        for path, content in (
            (workbook, b"workbook"),
            (inspection, b"inspection"),
            (builder, b"builder"),
            (coverage, b"coverage"),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        receipt = {
            "receipt_id": "AIIO_CANADA_WORKBOOK_BUILD_RECEIPT_0_1",
            "workbook_path": str(workbook.relative_to(self.root)),
            "workbook_sha256": sha256_file(workbook),
            "inspection_path": str(inspection.relative_to(self.root)),
            "inspection_sha256": sha256_file(inspection),
            "builder_path": "workbook-work/build_aiio_workbook.mjs",
            "builder_sha256": sha256_file(builder),
            "canada_coverage_path": "data/model-runs/canada_cross_domain_coverage_v0.1.json",
            "canada_coverage_sha256": sha256_file(coverage),
            "worksheet_count": 39,
            "required_worksheet": "Canada Coverage",
            "coverage_reconciliation_check_cell": "Release Checks!B55",
            "coverage_reconciliation_status": "PASS",
            "formula_error_match_count": 0,
            "publication_boundary": {
                "is_frozen_public_release": False,
                "research_workbook_only": True,
                "cross_province_comparison_authorized": False,
                "ai_attributable_effect_authorized": False,
            },
        }
        receipt_path.write_text(json.dumps(receipt))
        self.assertEqual(validate_workbook_receipt(self.root, workbook), receipt)
        coverage.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValidationError, "canada_coverage_sha256"):
            validate_workbook_receipt(self.root, workbook)

    def write_digest_fixture(self) -> None:
        items_dir = self.root / "data/digests/items"
        items_dir.mkdir(parents=True)
        registry_path = self.root / "data/registry/sources.json"
        registry_path.parent.mkdir(parents=True)
        items_path = items_dir / "2026-09-01.json"
        markdown_path = self.root / "data/digests/2026-09-01.md"
        items_path.write_text(
            json.dumps({"edition_date": "2026-09-01"}) + "\n", encoding="utf-8"
        )
        markdown_path.write_text("# Digest\n", encoding="utf-8")
        registry_path.write_text("{}\n", encoding="utf-8")
        manifest = {
            "items_sha256": sha256_file(items_path),
            "markdown_sha256": sha256_file(markdown_path),
            "source_registry_sha256": sha256_file(registry_path),
            "automatic_model_change": False,
            "publication_boundary": {
                "model_parameters_changed": False,
                "baseline_changed": False,
            },
        }
        (self.root / "data/digests/2026-09-01.manifest.json").write_text(
            json.dumps(manifest) + "\n", encoding="utf-8"
        )

    def test_digest_audit_detects_tampering(self) -> None:
        self.write_digest_fixture()
        status, _, _ = audit_digest_artifacts(
            self.root, as_of_date=date(2026, 9, 2)
        )
        self.assertEqual(status, PASS)
        (self.root / "data/digests/2026-09-01.md").write_text(
            "# Tampered\n", encoding="utf-8"
        )
        status, _, _ = audit_digest_artifacts(
            self.root, as_of_date=date(2026, 9, 2)
        )
        self.assertEqual(status, FAIL)

    def test_frozen_release_audit_detects_output_tampering(self) -> None:
        release_dir = self.root / "data/releases/0.6.0-dev"
        public_dir = self.root / "public/data"
        release_dir.mkdir(parents=True)
        public_dir.mkdir(parents=True)
        output_path = release_dir / "result.json"
        output_path.write_text('{"value": 1}\n', encoding="utf-8")
        manifest = {
            "version": "0.6.0-dev",
            "outputs": {"result.json": sha256_file(output_path)},
        }
        for path, payload in (
            (release_dir / "manifest.json", manifest),
            (public_dir / "manifest.json", manifest),
            (public_dir / "latest.json", {"manifest": manifest}),
        ):
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        status, _, _ = audit_frozen_release(self.root)
        self.assertEqual(status, PASS)
        output_path.write_text('{"value": 2}\n', encoding="utf-8")
        status, _, _ = audit_frozen_release(self.root)
        self.assertEqual(status, FAIL)


if __name__ == "__main__":
    unittest.main()
