from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from aiio.calibration import GEOGRAPHY_LABELS, REFERENCE_CLASSES
from aiio.historical_analog import (
    build_historical_analog_matrix,
    run_historical_analog_matrix,
)
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]


def quarter_end(start_year: int, offset: int) -> str:
    quarter_index = (start_year * 4) + offset
    year, quarter_zero = divmod(quarter_index, 4)
    month = (quarter_zero + 1) * 3
    day = {3: 31, 6: 30, 9: 30, 12: 31}[month]
    return date(year, month, day).isoformat()


class HistoricalAnalogTests(unittest.TestCase):
    fields = [
        "observation_id", "indicator_id", "value", "unit", "geography_id",
        "period_start", "period_end", "source_id", "evidence_status",
        "as_of_date", "transformation_id", "quality_flags",
    ]

    def write_history(
        self,
        path: Path,
        *,
        observation_count: int = 180,
        quarterly_growth: float = 1.005,
        omit_offset: int | None = None,
        source_override: str | None = None,
    ) -> None:
        rows = []
        for definition in REFERENCE_CLASSES.values():
            for geography_id in GEOGRAPHY_LABELS:
                for offset in range(observation_count):
                    if offset == omit_offset:
                        continue
                    period_end = quarter_end(1981, offset)
                    rows.append({
                        "observation_id": f"OBS_{definition['indicator_id']}_{geography_id}_{offset}",
                        "indicator_id": definition["indicator_id"],
                        "value": 50 * quarterly_growth**offset,
                        "unit": "Index, 2023=100",
                        "geography_id": geography_id,
                        "period_start": period_end,
                        "period_end": period_end,
                        "source_id": source_override or "STATCAN_BCPI_18100289",
                        "evidence_status": "observed",
                        "as_of_date": period_end,
                        "transformation_id": "TR_TEST",
                        "quality_flags": "",
                    })
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_constant_growth_preserves_coherent_schedule_weighting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(source)
            result = build_historical_analog_matrix(source)
        sample = result["reference_class_results"][0]
        row = next(
            item
            for item in sample["grid"]
            if item["start_lag_years"] == 3
            and item["duration_years"] == 5
            and item["profile_id"] == "back_loaded"
        )
        weights = [value / 15 for value in range(1, 6)]
        expected = sum(
            share * 1.005 ** (4 * horizon)
            for share, horizon in zip(weights, range(3, 8))
        )
        for key in ("p10", "p25", "p50", "p75", "p90", "minimum", "maximum"):
            self.assertAlmostEqual(row["schedule_weighted_factor"][key], expected, places=6)
        self.assertEqual(row["overlapping_trajectory_count"], 152)
        self.assertEqual(row["non_overlapping_trajectory_count"], 6)
        self.assertEqual(row["status"], "limited_history_only")

    def test_profile_shape_changes_exposure_under_positive_growth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(source)
            result = build_historical_analog_matrix(source)
        grid = result["reference_class_results"][0]["grid"]
        values = {}
        for profile_id in ("front_loaded", "even", "back_loaded"):
            row = next(
                item
                for item in grid
                if item["start_lag_years"] == 1
                and item["duration_years"] == 5
                and item["profile_id"] == profile_id
            )
            values[profile_id] = row["schedule_weighted_factor"]["p50"]
        self.assertLess(values["front_loaded"], values["even"])
        self.assertLess(values["even"], values["back_loaded"])

    def test_committed_matrix_is_reproducible_and_fail_closed(self) -> None:
        source = ROOT / "data/processed/bcpi_alberta.csv"
        committed = ROOT / "data/model-runs/alberta_project_historical_analog_matrix_v0.1.json"
        with tempfile.TemporaryDirectory() as directory:
            regenerated_path = Path(directory) / "matrix.json"
            run_historical_analog_matrix(source, regenerated_path)
            regenerated = json.loads(regenerated_path.read_text(encoding="utf-8"))
        expected = json.loads(committed.read_text(encoding="utf-8"))
        self.assertEqual(regenerated, expected)
        self.assertEqual(expected["input_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(len(expected["reference_class_results"]), 8)
        self.assertEqual(
            sum(len(item["grid"]) for item in expected["reference_class_results"]),
            1560,
        )
        boundary = expected["publication_authorization"]
        self.assertTrue(boundary["historical_analog_stress_test_authorized"])
        self.assertTrue(boundary["historical_analog_budget_translation_authorized"])
        self.assertFalse(boundary["future_projection_authorized"])
        self.assertFalse(boundary["probability_interval_authorized"])
        self.assertFalse(boundary["recommended_escalation_allowance_authorized"])
        self.assertFalse(boundary["ai_attributable_effect_authorized"])
        self.assertFalse(boundary["forecast_project_cost_translation_authorized"])

    def test_missing_quarter_and_source_drift_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(source, omit_offset=25)
            with self.assertRaisesRegex(ValidationError, "missing calendar quarter"):
                build_historical_analog_matrix(source)
            self.write_history(source, source_override="UNREGISTERED_SOURCE")
            with self.assertRaisesRegex(ValidationError, "source changed"):
                build_historical_analog_matrix(source)


if __name__ == "__main__":
    unittest.main()
