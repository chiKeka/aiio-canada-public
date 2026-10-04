import importlib.util
import json
import shutil
import tempfile
import unittest
from datetime import UTC, datetime, date
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch
from aiio.digest import build_digest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('review_refresh', ROOT / 'research/scripts/review_evidence_refresh.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ReviewRefreshTests(unittest.TestCase):
    def fixture(self, root):
        for name, content in [('data/processed/frozen.csv', 'last-good\n'), ('public/data/latest-digest.json', '{"edition_date":"2026-09-03"}'), ('data/pilots/frozen.json', '{"cost":null}')]:
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
        for name in ['vendor/compatible/dist/index.js', 'dist/build.js']:
            path = root / name; path.parent.mkdir(parents=True); path.write_text('fixture')
        registry = root / 'data/registry/sources.json'; registry.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'data/registry/sources.json', registry)
        script = root / 'research/scripts/weekly_evidence_refresh.py'; script.parent.mkdir(parents=True)
        script.write_text('# placeholder; mocked runner does not fetch\n')

    @staticmethod
    def surface(root, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text('{"operational_receipts_reconciled":true}\n')

    def runner(self, success):
        def run(command, cwd, **kwargs):
            stage = Path(cwd)
            self.assertTrue((stage / 'vendor/compatible/dist/index.js').is_file())
            self.assertFalse((stage / 'dist').exists())
            (stage / 'data/processed/frozen.csv').write_text('new-candidate\n')
            (stage / 'public/data/latest-digest.json').write_text('{"edition_date":"NEW"}')
            raw = stage / 'data/raw/feed/new.json'; raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text('{"value":1}')
            manifest = raw.with_suffix('.json.manifest.json')
            manifest.write_text(json.dumps({'archive_path': 'data/raw/feed/new.json', 'source_id': 'TEST', 'result': 'success', 'retrieved_at': datetime.now(UTC).isoformat(), 'content_hash': module.digest(raw)}))
            attempts = stage / 'data/model-runs/weekly-source-refresh.json'; attempts.parent.mkdir(parents=True, exist_ok=True)
            attempts.write_text('{"sources":{"TEST":{"status":"error","last_attempt":"2026-10-03","last_success":"2026-09-03"}}}')
            if success:
                edition = command[-1]
                payload = json.loads((ROOT / 'data/digests/items/2026-09-03.json').read_text())
                payload['edition_date'] = edition; payload['status'] = 'review'
                items = stage / 'data/digests/items' / f'{edition}.json'; items.parent.mkdir(parents=True)
                items.write_text(json.dumps(payload))
                build_digest(items, stage / 'data/digests' / f'{edition}.md', date.fromisoformat(edition), source_registry_path=stage / 'data/registry/sources.json')
            return CompletedProcess(command, 0 if success else 1, 'real candidate diagnostic', 'failure detail' if not success else '')
        return run

    def test_failed_staging_preserves_last_good_frozen_and_digest_with_attempt_diagnostics(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); self.fixture(root)
            with patch('aiio.research_surface.build_research_surface_manifest', self.surface), patch.object(module, 'build_operational_inputs'):
                report = module.refresh_for_review(root, datetime.now(UTC).date().isoformat(), self.runner(False))
            self.assertEqual(report['status'], 'partial_candidate_refresh_failed')
            self.assertEqual((root / 'data/processed/frozen.csv').read_text(), 'last-good\n')
            self.assertIn('2026-09-03', (root / 'public/data/latest-digest.json').read_text())
            self.assertEqual((root / 'data/pilots/frozen.json').read_text(), '{"cost":null}')
            raw_receipt = json.loads((root / 'data/raw/feed/new.json.manifest.json').read_text())
            self.assertTrue((root / raw_receipt['archive_path']).is_file())
            self.assertFalse((root / 'data/raw/feed/new.json').exists())
            self.assertEqual(json.loads((root / 'data/model-runs/weekly-source-refresh.json').read_text())['sources']['TEST']['last_success'], '2026-09-03')
            with self.assertRaisesRegex(ValueError, 'No complete'): module.check_candidates(root)

    def test_review_candidate_hashes_registry_cadence_and_missing_raw_limits(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); self.fixture(root)
            with patch('aiio.research_surface.build_research_surface_manifest', self.surface), patch.object(module, 'build_operational_inputs'):
                report = module.refresh_for_review(root, datetime.now(UTC).date().isoformat(), self.runner(True))
            candidate = root / report['candidate_directory']
            with patch('aiio.research_surface.build_research_surface_manifest', self.surface), patch.object(module, 'build_operational_inputs'):
                module.refresh_for_review(root, '2026-09-01', self.runner(True))
            checked = module.check_candidates(root)
            self.assertEqual(len(checked['candidates']), 2)
            self.assertEqual(sum('cadence' in item for item in checked['candidates']), 1)
            self.assertFalse(checked['publication_authorized'])
            self.assertFalse(checked['digest_promoted'])
            (candidate / 'data/raw/feed/new.json').unlink()
            checked = module.check_candidates(root)
            self.assertEqual(next(item for item in checked['candidates'] if item['directory'] == report['candidate_directory'])['raw_archives_not_available_for_byte_verification'], ['data/raw/feed/new.json'])
            manifest_path = candidate / 'manifest.json'
            original = manifest_path.read_text()
            payload = json.loads(original); payload['digest_promoted'] = True
            manifest_path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, 'cannot authorize'): module.check_candidates(root)
            payload = json.loads(original); payload['candidate_manifest']['../../escape'] = 'sha256:wrong'
            manifest_path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, 'escaping'): module.check_candidates(root)
            payload = json.loads(original); payload['candidate_directory'] = 'other-directory'
            manifest_path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, 'identity mismatch'): module.check_candidates(root)
            manifest_path.write_text(original)
            (candidate / 'data/processed/frozen.csv').write_text('drift')
            with self.assertRaisesRegex(ValueError, 'hash drift'): module.check_candidates(root)
