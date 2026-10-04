from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from aiio.calibration import GEOGRAPHY_LABELS, REFERENCE_CLASSES
from aiio.historical_envelope import (
    build_historical_reference_envelope,
    run_historical_reference_envelope,
)
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]


def quarter_end(start_year: int, offset: int) -> str:
    quarter_index = (start_year * 4) + offset
    year, quarter_zero = divmod(quarter_index, 4)
    month = (quarter_zero + 1) * 3
    day = {3: 31, 6: 30, 9: 30, 12: 31}[month]
    return date(year, month, day).isoformat()


class HistoricalEnvelopeTests(unittest.TestCase):
    fields = [
        "observation_id", "indicator_id", "value", "unit", "geography_id",
        "period_start", "period_end", "source_id", "evidence_status",
        "as_of_date", "transformation_id", "quality_flags",
    ]

    def write_history(
        self, path: Path, *, observation_count: int = 100,
        quarterly_growth: float = 1.005, omit_offset: int | None = None,
    ) -> None:
        rows = []
        for definition in REFERENCE_CLASSES.values():
            for geography_id in GEOGRAPHY_LABELS:
                for offset in range(observation_count):
                    if offset == omit_offset:
                        continue
                    period_end = quarter_end(2000, offset)
                    rows.append({
                        "observation_id": f"OBS_{definition['indicator_id']}_{geography_id}_{offset}",
                        "indicator_id": definition["indicator_id"],
                        "value": 50 * quarterly_growth**offset,
                        "unit": "Index, 2023=100",
                        "geography_id": geography_id,
                        "period_start": period_end,
                        "period_end": period_end,
                        "source_id": "STATCAN_BCPI_18100289",
                        "evidence_status": "observed",
                        "as_of_date": period_end,
                        "transformation_id": "TR_TEST",
                        "quality_flags": "",
                    })
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_constant_growth_has_exact_historical_quantiles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(source)
            result = build_historical_reference_envelope(source)
        self.assertEqual(len(result["reference_class_results"]), 8)
        sample = result["reference_class_results"][0]
        five_year = next(item for item in sample["horizons"] if item["horizon_years"] == 5)
        expected = (1.005**20 - 1) * 100
        for label in ("p10", "p25", "p50", "p75", "p90", "minimum", "maximum"):
            self.assertAlmostEqual(
                five_year["historical_cumulative_change_percent"][label], expected, places=3
            )
        self.assertEqual(five_year["overlapping_window_count"], 80)
        self.assertEqual(five_year["non_overlapping_window_count"], 4)
        self.assertEqual(five_year["interpretation_status"], "limited_history_only")

    def test_missing_quarter_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(source, omit_offset=25)
            with self.assertRaisesRegex(ValidationError, "missing calendar quarter"):
                build_historical_reference_envelope(source)

    def test_committed_artifact_is_reproducible_and_fail_closed(self) -> None:
        source = ROOT / "data/processed/bcpi_alberta.csv"
        committed = ROOT / "data/model-runs/alberta_bcpi_historical_envelope_v0.1.json"
        with tempfile.TemporaryDirectory() as directory:
            regenerated_path = Path(directory) / "envelope.json"
            run_historical_reference_envelope(source, regenerated_path)
            regenerated = json.loads(regenerated_path.read_text(encoding="utf-8"))
        expected = json.loads(committed.read_text(encoding="utf-8"))
        self.assertEqual(regenerated, expected)
        self.assertEqual(expected["input_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        boundary = expected["publication_authorization"]
        self.assertTrue(boundary["historical_summary_authorized"])
        self.assertFalse(boundary["future_projection_authorized"])
        self.assertFalse(boundary["ai_attributable_effect_authorized"])
        self.assertFalse(boundary["project_cost_translation_authorized"])
        self.assertEqual(len(expected["reference_class_results"]), 8)
        for item in expected["reference_class_results"]:
            self.assertEqual(len(item["horizons"]), 5)
            for horizon in item["horizons"]:
                values = horizon["historical_cumulative_change_percent"]
                self.assertLessEqual(values["minimum"], values["p10"])
                self.assertLessEqual(values["p10"], values["p25"])
                self.assertLessEqual(values["p25"], values["p50"])
                self.assertLessEqual(values["p50"], values["p75"])
                self.assertLessEqual(values["p75"], values["p90"])
                self.assertLessEqual(values["p90"], values["maximum"])
                if (
                    item["asset_class"] == "municipal_operations_facilities"
                    and horizon["horizon_years"] in {4, 5}
                ):
                    self.assertEqual(horizon["interpretation_status"], "limited_history_only")

    def test_rejects_unsupported_horizon(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(source)
            with self.assertRaisesRegex(ValidationError, "unique years"):
                build_historical_reference_envelope(source, horizons_years=[0, 5])


if __name__ == "__main__":
    unittest.main()
