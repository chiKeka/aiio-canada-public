from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.adapters.statcan import normalize_bcpi_reference_provinces


ROOT = Path(__file__).resolve().parents[2]


class ProvincialBcpiArtifactTests(unittest.TestCase):
    def test_committed_provincial_bcpi_vintage_is_locked(self) -> None:
        paths_and_hashes = {
            "data/raw/statcan_bcpi_18100289/2026-08-31_d0d11fda82bf.zip": (
                "d0d11fda82bf37c3720d159c1d441bc1f15abd73ba9b7d9e750f4b1929b26612"
            ),
            "data/processed/bcpi_material_provinces.csv": (
                "9394f1d5cbd322b1f872ce1aee0cc2cac06865725e4b18fc98e12204fec0e74c"
            ),
            "data/processed/bcpi_material_cost_screen_provinces.csv": (
                "69d9ce2e2cb9c1df94a472cb3ab737d2c30712bd25a0954c701f11dbec881581"
            ),
            "data/model-runs/bcpi_material_cost_screen_provinces_v0.1.json": (
                "34574b7f4479a5fa9877c4f3e06d6dff1e98ad42feb4b40a9e72ab5ce32dfcfc"
            ),
        }
        for relative_path, expected_hash in paths_and_hashes.items():
            with self.subTest(path=relative_path):
                content = (ROOT / relative_path).read_bytes()
                self.assertEqual(hashlib.sha256(content).hexdigest(), expected_hash)

    def test_committed_screen_has_complete_declared_scope(self) -> None:
        normalized_path = ROOT / "data/processed/bcpi_material_provinces.csv"
        screen_path = ROOT / "data/model-runs/bcpi_material_cost_screen_provinces_v0.1.json"
        with normalized_path.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        screen = json.loads(screen_path.read_text(encoding="utf-8"))

        self.assertEqual(len(rows), 5472)
        self.assertEqual(len({row["indicator_id"] for row in rows}), 16)
        self.assertEqual(len({row["geography_id"] for row in rows}), 9)
        self.assertEqual(
            {row["period_end"] for row in rows},
            {
                f"{year}-{month_day}"
                for year in range(2017, 2027)
                for month_day in ("03-31", "06-30", "09-30", "12-31")
                if not (year == 2026 and month_day in {"09-30", "12-31"})
            },
        )
        self.assertEqual(screen["observation_count"], 144)
        self.assertEqual(screen["period_end"], "2026-06-30")
        self.assertNotIn("PR_11", screen["geography_scope"])
        self.assertTrue(
            all(not label.startswith("CMA_") for label in screen["geography_scope"])
        )

    def test_provincial_reference_extract_reproduces_from_locked_raw_vintage(self) -> None:
        raw_path = (
            ROOT
            / "data/raw/statcan_bcpi_18100289/2026-08-31_d0d11fda82bf.zip"
        )
        committed = ROOT / "data/processed/bcpi_reference_bc_on_qc.csv"
        with tempfile.TemporaryDirectory() as directory:
            regenerated = Path(directory) / "reference.csv"
            observations = normalize_bcpi_reference_provinces(raw_path, regenerated)
            regenerated_bytes = regenerated.read_bytes()
        self.assertEqual(len(observations), 456)
        self.assertEqual(regenerated_bytes, committed.read_bytes())


if __name__ == "__main__":
    unittest.main()
