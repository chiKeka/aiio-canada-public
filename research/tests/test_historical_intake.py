import json
import tempfile
import unittest
from pathlib import Path

from aiio.historical_intake import CATALOG, OUTPUT, blob_hash, build_snapshot_readiness, encoded, inspect_csv, load_snapshots, register_snapshot, select_snapshot
from aiio.schemas import ValidationError

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "STATCAN_BCPI_18100289"


def fixture(root, identifier="TEST_RELEASE_ONE", captured="2026-08-31T12:00:00+00:00", value="100"):
    folder = root / identifier
    folder.mkdir(parents=True)
    raw = folder / "raw.txt"
    raw.write_text("Synthetic raw test data " + value)
    normalized = folder / "normalized.csv"
    normalized.write_text(f"observation_id,source_id,value,period_start\nOBS_1,{SOURCE},{value},2010-01-01\n")
    reference = lambda p: {"path": p.relative_to(root).as_posix(), "sha256": blob_hash(p.read_bytes())}
    capture = folder / "capture.json"
    capture.write_bytes(encoded({"source_id": SOURCE, "result": "success", "retrieved_at": captured,
                                "archive_path": raw.relative_to(root).as_posix(), "content_hash": blob_hash(raw.read_bytes())}))
    descriptor = {"schema_version": "AIIO_SNAPSHOT_INTAKE_1.0", "snapshot_id": identifier, "source_id": SOURCE,
                  "capture_manifest": reference(capture), "normalized_artifact": reference(normalized), "publication": None}
    path = folder / "intake.json"
    path.write_bytes(encoded(descriptor))
    return path, descriptor


class HistoricalIntakeTests(unittest.TestCase):
    def test_live_report_reproduces_without_inventing_historical_coverage(self):
        report = build_snapshot_readiness(ROOT)
        self.assertEqual(report, json.loads((ROOT / OUTPUT).read_text()))
        self.assertEqual(report["snapshot_count"], 3)
        self.assertEqual(report["complete_source_snapshot_origins"], 0)
        self.assertEqual(report["missing_source_origin_pairs"], 24)
        self.assertFalse(any(report["publication_boundary"].values()))
        for origin in report["origins"]:
            for selected in origin["source_selections"].values():
                self.assertIsNone(selected["snapshot_id"])
                self.assertIsNone(selected["record_count"])

    def test_old_observation_date_never_backdates_capture_and_future_revision_is_excluded(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            intake, _ = fixture(root, captured="2024-04-01T00:00:00+00:00")
            register_snapshot(root, intake)
            before = select_snapshot(load_snapshots(root), SOURCE, "2024-03-31T23:59:59Z")
            self.assertEqual(before["status"], "missing")
            selected = select_snapshot(load_snapshots(root), SOURCE, "2024-04-01T00:00:00Z")
            self.assertEqual(selected["snapshot_id"], "TEST_RELEASE_ONE")
            later, _ = fixture(root, "TEST_RELEASE_TWO", "2025-04-01T00:00:00Z", "999")
            register_snapshot(root, later)
            self.assertEqual(select_snapshot(load_snapshots(root), SOURCE, "2024-04-01T00:00:00Z"), selected)

    def test_registration_is_idempotent_and_original_csv_changes_do_not_rewrite_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, descriptor = fixture(root)
            register_snapshot(root, path)
            self.assertEqual(register_snapshot(root, path)["status"], "already_registered")
            original = root / descriptor["normalized_artifact"]["path"]
            original.write_text(original.read_text().replace(",100,", ",999,"))
            snapshots = load_snapshots(root)
            self.assertIn(",100,", (root / snapshots[0]["normalized_artifact"]["path"]).read_text())
            descriptor["normalized_artifact"]["sha256"] = blob_hash(original.read_bytes())
            path.write_bytes(encoded(descriptor))
            with self.assertRaisesRegex(ValidationError, "immutable"):
                register_snapshot(root, path)
            self.assertEqual(len(load_snapshots(root)), 1)

    def test_reviewed_historical_publication_requires_content_date_and_evidence_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, descriptor = fixture(root)
            evidence = root / "publication.txt"
            evidence.write_text("Synthetic test evidence only")
            proof = {"path": "publication.txt", "sha256": blob_hash(evidence.read_bytes())}
            capture = json.loads((root / descriptor["capture_manifest"]["path"]).read_text())
            receipt = {"schema_version": "AIIO_PUBLICATION_DATE_REVIEW_1.0", "decision": "accept_snapshot_publication_date",
                       "source_id": SOURCE, "raw_content_sha256": capture["content_hash"], "published_at": "2024-01-15T12:00:00Z",
                       "evidence_sha256": proof["sha256"], "scope": "source_publication_date_only",
                       "reviewer": "synthetic-test-reviewer", "reviewed_at": "2026-09-05T12:00:00Z"}
            review_path = root / "review.json"
            review_path.write_bytes(encoded({**receipt, "raw_content_sha256": "sha256:wrong"}))
            descriptor["publication"] = {"published_at": receipt["published_at"], "evidence": proof,
                                         "review_receipt": {"path": "review.json", "sha256": blob_hash(review_path.read_bytes())}}
            path.write_bytes(encoded(descriptor))
            with self.assertRaisesRegex(ValidationError, "does not match"):
                register_snapshot(root, path)
            self.assertFalse((root / CATALOG).exists())
            review_path.write_bytes(encoded(receipt))
            descriptor["publication"]["review_receipt"]["sha256"] = blob_hash(review_path.read_bytes())
            path.write_bytes(encoded(descriptor))
            register_snapshot(root, path)
            selection = select_snapshot(load_snapshots(root), SOURCE, "2024-03-31T23:59:59Z")
            self.assertEqual(selection["availability_basis"], "reviewed_publication_date")

    def test_hash_drift_missing_raw_and_path_escape_are_rejected_before_registration(self):
        for mutation in ("raw", "normalized", "escape"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                path, descriptor = fixture(root)
                if mutation == "raw":
                    (path.parent / "raw.txt").unlink()
                elif mutation == "normalized":
                    (path.parent / "normalized.csv").write_text("changed")
                else:
                    descriptor["raw_copy_path"] = "../outside.txt"
                    path.write_bytes(encoded(descriptor))
                with self.assertRaises(ValidationError):
                    register_snapshot(root, path)
                self.assertFalse((root / CATALOG).exists())

    def test_conflicting_same_time_versions_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for identifier, value in (("TEST_RELEASE_ONE", "100"), ("TEST_RELEASE_TWO", "101")):
                path, _ = fixture(root, identifier, "2024-01-01T00:00:00Z", value)
                register_snapshot(root, path)
            with self.assertRaisesRegex(ValidationError, "ambiguous"):
                select_snapshot(load_snapshots(root), SOURCE, "2025-01-01T00:00:00Z")

    def test_source_ids_duplicates_and_malformed_csv_rejected(self):
        for content in (b"", b"observation_id,source_id\nOBS_1,WRONG\n",
                        f"observation_id,source_id\nOBS_1,{SOURCE}\nOBS_1,{SOURCE}\n".encode(),
                        f"observation_id,source_id,value\nOBS_1,{SOURCE}\n".encode()):
            with self.assertRaises(ValidationError):
                inspect_csv(content, SOURCE)

    def test_selected_snapshot_is_whole_and_never_merges_removed_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, descriptor = fixture(root, "TEST_RELEASE_ONE", "2024-01-01T00:00:00Z")
            normalized = root / descriptor["normalized_artifact"]["path"]
            normalized.write_text(normalized.read_text() + f"OBS_2,{SOURCE},200,2010-01-01\n")
            descriptor["normalized_artifact"]["sha256"] = blob_hash(normalized.read_bytes())
            path.write_bytes(encoded(descriptor))
            register_snapshot(root, path)
            path, _ = fixture(root, "TEST_RELEASE_TWO", "2025-01-01T00:00:00Z")
            register_snapshot(root, path)
            selected = select_snapshot(load_snapshots(root), SOURCE, "2025-02-01T00:00:00Z")
            self.assertEqual(selected["record_count"], 1)
            self.assertNotIn("OBS_2", (root / selected["normalized_artifact"]["path"]).read_text())

    def test_preserved_snapshot_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path, _ = fixture(root)
            register_snapshot(root, path)
            selected = load_snapshots(root)[0]
            (root / selected["normalized_artifact"]["path"]).write_text("tampered")
            with self.assertRaisesRegex(ValidationError, "hash drift"):
                load_snapshots(root)
