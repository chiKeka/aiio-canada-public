from __future__ import annotations

import unittest
from pathlib import Path

from aiio.registry import load_registry


class RegistryTests(unittest.TestCase):
    def test_project_registry_is_valid_and_unique(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        sources = load_registry(project_root / "data" / "registry" / "sources.json")
        self.assertGreaterEqual(len(sources), 8)
        self.assertEqual(len(sources), len({source.source_id for source in sources}))
        self.assertTrue(any(source.domain == "power" for source in sources))
        self.assertTrue(any(source.domain == "labour" for source in sources))


if __name__ == "__main__":
    unittest.main()
