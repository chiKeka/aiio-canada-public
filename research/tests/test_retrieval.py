from __future__ import annotations

import unittest

from aiio.retrieval import _suffix_for


class RetrievalTests(unittest.TestCase):
    def test_geojson_access_preserves_geographic_json_suffix(self) -> None:
        self.assertEqual(_suffix_for("geojson", "application/geo+json"), ".geojson")
        self.assertEqual(_suffix_for("geojson", "application/json"), ".geojson")

    def test_api_json_access_uses_plain_json_suffix(self) -> None:
        self.assertEqual(_suffix_for("api_json", "application/json"), ".json")


if __name__ == "__main__":
    unittest.main()
