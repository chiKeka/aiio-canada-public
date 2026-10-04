"""Offline refresh receipts, failure retention and read-only diagnostic entry point."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('weekly_refresh', ROOT / 'research/scripts/weekly_evidence_refresh.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WeeklyRefreshTests(unittest.TestCase):
    def test_partial_feed_groups_return_control_to_independent_pipeline(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []
            def procurement(*args):
                calls.append('procurement')
                raise ValueError('remote details must not enter summary')
            def construction(*args, **kwargs):
                self.assertFalse(kwargs['check'])
                calls.append('construction')
                return SimpleNamespace(returncode=1)
            failures = MODULE.independent_refresh_checks(root, '2026-10-03', procurement=procurement, construction=construction)
            calls.append('independent municipal stage')
            receipt = root / 'data/model-runs/construction-source-refresh.json'
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({'sources': {'JVWS': {'status': 'error'}, 'BCPI': {'status': 'checked'}}}))
            summary = MODULE.partial_refresh_summary(root, failures)
            self.assertEqual(calls, ['procurement', 'construction', 'independent municipal stage'])
            self.assertEqual(summary['status'], 'partial_refresh')
            self.assertEqual(summary['failed_source_ids'], ['JVWS'])
            self.assertNotIn('remote details', json.dumps(summary))

    def test_canadabuys_validates_each_candidate_and_continues_after_schema_failure(self):
        from aiio.adapters.canadabuys import TENDER_SOURCE_ID, AWARD_SOURCE_ID, CONTRACT_SOURCE_ID, TENDER_REQUIRED_FIELDS, AWARD_REQUIRED_FIELDS, CONTRACT_REQUIRED_FIELDS
        from aiio.schemas import ValidationError
        fields = {TENDER_SOURCE_ID: TENDER_REQUIRED_FIELDS, AWARD_SOURCE_ID: AWARD_REQUIRED_FIELDS, CONTRACT_SOURCE_ID: CONTRACT_REQUIRED_FIELDS}
        @dataclass
        class Result:
            source_id: str
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / 'data/registry/sources.json'
            registry.parent.mkdir(parents=True)
            registry.write_bytes((ROOT / 'data/registry/sources.json').read_bytes())
            calls = []
            def fetcher(source, raw_root, *, validate_content):
                calls.append(source.source_id)
                payload = b'<html>service unavailable</html>' if source.source_id == AWARD_SOURCE_ID else (','.join(sorted(fields[source.source_id])) + '\n' + ','.join('fixture' for _ in fields[source.source_id]) + '\n').encode()
                validate_content(payload)
                return Result(source.source_id)
            with self.assertRaisesRegex(ValidationError, AWARD_SOURCE_ID):
                MODULE.refresh_canadabuys(root, '2026-10-03', fetcher=fetcher)
            self.assertEqual(set(calls), set(fields))
            receipts = json.loads((root / 'data/model-runs/weekly-source-refresh.json').read_text())['sources']
            self.assertEqual(receipts[TENDER_SOURCE_ID]['last_success'], '2026-10-03')
            self.assertEqual(receipts[CONTRACT_SOURCE_ID]['last_success'], '2026-10-03')
            self.assertNotIn('last_success', receipts[AWARD_SOURCE_ID])
            self.assertFalse((root / 'data/processed').exists())

    def test_unchanged_fetch_advances_verification_and_failed_fetch_retains_success(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / 'receipt.json'
            receipt.write_text(json.dumps({'sources': {'A': {'last_success': '2026-09-01', 'observation_date': '2026-08-01', 'content_hash': 'sha256:last-good'}}}))
            value = MODULE.record_fetch(receipt, 'A', '2026-10-03', lambda: {'changed': False})
            self.assertFalse(value['changed'])
            success = json.loads(receipt.read_text())['sources']['A']
            self.assertEqual(success['last_success'], '2026-10-03')
            self.assertEqual(success['observation_date'], '2026-08-01')
            def fail():
                raise ValueError('Sensitive remote diagnostic must not enter receipts')
            with self.assertRaises(ValueError):
                MODULE.record_fetch(receipt, 'A', '2026-10-10', fail)
            failed = json.loads(receipt.read_text())['sources']['A']
            self.assertEqual(failed['last_success'], '2026-10-03')
            self.assertEqual(failed['last_attempt'], '2026-10-10')
            self.assertEqual(failed['content_hash'], 'sha256:last-good')
            self.assertNotIn('Sensitive', receipt.read_text())
            self.assertFalse(receipt.with_suffix('.tmp').exists())

    def test_offline_check_does_not_write_or_fetch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / 'data/registry/sources.json'
            registry.parent.mkdir(parents=True)
            registry.write_bytes((ROOT / 'data/registry/sources.json').read_bytes())
            (root / 'research').mkdir()
            (root / 'research/src').symlink_to(ROOT / 'research/src', target_is_directory=True)
            before = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            result = subprocess.run([sys.executable, str(ROOT / 'research/scripts/weekly_evidence_refresh.py'), '--root', str(root), '--check-receipts'], capture_output=True, text=True, check=True)
            diagnostic = json.loads(result.stdout)
            self.assertFalse(diagnostic['writes'])
            self.assertFalse(diagnostic['network'])
            after = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
