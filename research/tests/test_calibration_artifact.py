from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.calibration import (
    PROVINCIAL_REFERENCE_GEOGRAPHY_LABELS,
    PROVINCIAL_REFERENCE_LIMITATIONS,
    PROVINCIAL_REFERENCE_MODEL_ID,
    run_reference_class_baseline,
)
from aiio.project_cost import build_project_reference_cost


ROOT = Path(__file__).resolve().parents[2]


class CalibrationArtifactTests(unittest.TestCase):
    def test_committed_v01_artifact_is_locked_and_reproducible(self) -> None:
        source = ROOT / "data/processed/bcpi_alberta.csv"
        committed = (
            ROOT
            / "data/model-runs/alberta_bcpi_reference_baseline_v0.1.json"
        )
        self.assertEqual(
            hashlib.sha256(committed.read_bytes()).hexdigest(),
            "9909c2d10a6c67f9699d98cd16dead6e619635b3a16b535c389ae9efa518bd40",
        )
        with tempfile.TemporaryDirectory() as directory:
            regenerated_path = Path(directory) / "baseline.json"
            run_reference_class_baseline(source, regenerated_path)
            regenerated = json.loads(regenerated_path.read_text(encoding="utf-8"))
        expected = json.loads(committed.read_text(encoding="utf-8"))
        self.assertEqual(regenerated, expected)

    def test_v01_withholds_long_horizon_health_and_school_results(self) -> None:
        artifact = json.loads(
            (
                ROOT
                / "data/model-runs/alberta_bcpi_reference_baseline_v0.1.json"
            ).read_text(encoding="utf-8")
        )
        relevant = [
            result
            for result in artifact["reference_class_results"]
            if result["asset_class"]
            in {"health_facilities", "schools_and_postsecondary"}
        ]
        self.assertEqual(len(relevant), 4)
        for result in relevant:
            for horizon in result["horizons"]:
                if horizon["horizon_years"] in {4, 5}:
                    self.assertEqual(horizon["status"], "gate_failed")
                    self.assertIsNone(
                        horizon["projected_cumulative_change_percent"]
                    )
        self.assertEqual(
            artifact["ai_attributable_increment"]["status"], "not_calibrated"
        )
        self.assertIsNone(
            artifact["ai_attributable_increment"]["cost_escalation_percent"]
        )
        self.assertFalse(
            artifact["publication_authorization"][
                "public_projection_authorized"
            ]
        )

    def test_real_five_year_health_project_fails_closed(self) -> None:
        artifact = json.loads(
            (
                ROOT
                / "data/model-runs/alberta_bcpi_reference_baseline_v0.1.json"
            ).read_text(encoding="utf-8")
        )
        result = build_project_reference_cost(
            {
                "project_id": "INTEGRATION_TEST",
                "project_name": "Five-year health integration test",
                "asset_class": "health_facilities",
                "geography_id": "CMA_825",
                "current_estimate_cad": 1.0,
                "estimate_price_basis_period_end": "2026-06-30",
                "expenditure_profile": [
                    {"horizon_years": year, "share": 0.2}
                    for year in range(1, 6)
                ],
            },
            artifact,
        )
        self.assertEqual(result["status"], "not_assessed")
        self.assertEqual(
            [item["horizon_years"] for item in result["failed_horizons"]],
            [1, 2, 3, 4, 5],
        )
        self.assertIsNone(
            result["market_reference_baseline"][
                "schedule_weighted_estimate_cad"
            ]
        )

    def test_provincial_reference_expansion_is_locked_and_not_assessed(self) -> None:
        source = ROOT / "data/processed/bcpi_reference_bc_on_qc.csv"
        committed = (
            ROOT
            / "data/model-runs/bc_on_qc_bcpi_reference_baseline_v0.1.json"
        )
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            "8d6f2bce624176f736d68ac40f87fc5a3e78aec68d7ad0493ee26b3cfba60a5e",
        )
        self.assertEqual(
            hashlib.sha256(committed.read_bytes()).hexdigest(),
            "b79e81862d8e70865a21ff72781d5d45589948de347abf191b81b78d91ca3969",
        )
        with tempfile.TemporaryDirectory() as directory:
            regenerated_path = Path(directory) / "provincial-baseline.json"
            run_reference_class_baseline(
                source,
                regenerated_path,
                geography_labels=PROVINCIAL_REFERENCE_GEOGRAPHY_LABELS,
                model_id=PROVINCIAL_REFERENCE_MODEL_ID,
                limitations=PROVINCIAL_REFERENCE_LIMITATIONS,
            )
            regenerated = json.loads(
                regenerated_path.read_text(encoding="utf-8")
            )
        expected = json.loads(committed.read_text(encoding="utf-8"))
        self.assertEqual(regenerated, expected)
        self.assertEqual(expected["release_state"], "not_assessed")
        self.assertEqual(
            expected["publication_summary"]["horizon_status_counts"],
            {"not_assessed": 60},
        )
        self.assertEqual(
            {
                item["geography_id"]
                for item in expected["reference_class_results"]
            },
            set(PROVINCIAL_REFERENCE_GEOGRAPHY_LABELS),
        )
        self.assertTrue(
            all(
                horizon["projected_index"] is None
                for item in expected["reference_class_results"]
                for horizon in item["horizons"]
            )
        )


if __name__ == "__main__":
    unittest.main()
