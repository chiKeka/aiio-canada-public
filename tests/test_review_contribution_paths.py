"""Offline tests for maintainer-owned filename triage."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('review_paths', Path(__file__).resolve().parents[1] / 'scripts/review_contribution_paths.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReviewPathsTests(unittest.TestCase):
    def test_sensitive_paths_need_review(self):
        for path in ['.github/workflows/check.yml', 'package-lock.json', 'docs/helper.py', 'app/page.tsx', '.env.local', 'vendor/example/LICENSE', 'publication/source-commands.json', 'next.config.ts', 'tests/fixture.json', '.GITHUB/CODEOWNERS']:
            with self.subTest(path=path):
                self.assertIsNotNone(MODULE.reason(path))

    def test_ordinary_docs_are_not_a_safety_verdict(self):
        self.assertIsNone(MODULE.reason('docs/project-assessment-walkthrough.md'))

    def test_ambiguous_paths_need_review(self):
        for path in ['', '.', './', '../outside.md', '/absolute.md', 'docs/../outside.md', 'docs\\file.md', 'bad\x01.md']:
            with self.subTest(path=repr(path)):
                self.assertIsNotNone(MODULE.reason(path))

    def test_exit_status_and_no_named_file_access(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = Path(directory) / 'paths.txt'
            for contents, expected in [('docs/nonexistent.md\n', 0), ('scripts/nonexistent.py\n', 2), ('', 2)]:
                paths.write_text(contents)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(MODULE.main(['--paths-file', str(paths)]), expected)
                self.assertIn('manually inspect the complete diff', output.getvalue())


if __name__ == '__main__':
    unittest.main()
