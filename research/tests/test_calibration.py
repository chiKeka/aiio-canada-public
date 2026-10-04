from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from aiio.calibration import (
    GEOGRAPHY_LABELS,
    REFERENCE_CLASSES,
    build_reference_class_baseline,
    run_reference_class_baseline,
)
from aiio.schemas import ValidationError


def quarter_end(start_year: int, offset: int) -> str:
    quarter_index = (start_year * 4) + offset
    year, quarter_zero = divmod(quarter_index, 4)
    month = (quarter_zero + 1) * 3
    day = {3: 31, 6: 30, 9: 30, 12: 31}[month]
    return date(year, month, day).isoformat()


class ReferenceBaselineTests(unittest.TestCase):
    fields = [
        "observation_id",
        "indicator_id",
        "value",
        "unit",
        "geography_id",
        "period_start",
        "period_end",
        "source_id",
        "evidence_status",
        "as_of_date",
        "transformation_id",
        "quality_flags",
    ]

    def write_history(
        self,
        path: Path,
        *,
        observation_count: int = 100,
        quarterly_growth: float = 1.005,
        omit_offset: int | None = None,
        geography_labels: dict[str, str] = GEOGRAPHY_LABELS,
    ) -> None:
        rows = []
        for definition in REFERENCE_CLASSES.values():
            for geography_id in geography_labels:
                for offset in range(observation_count):
                    if offset == omit_offset:
                        continue
                    period_end = quarter_end(2000, offset)
                    rows.append(
                        {
                            "observation_id": (
                                f"OBS_{definition['indicator_id']}_{geography_id}_{offset}"
                            ),
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
                        }
                    )
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_constant_growth_selects_drift_and_passes_locked_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(source)
            result = build_reference_class_baseline(source)

        self.assertEqual(result["release_state"], "baseline_only")
        self.assertEqual(len(result["reference_class_results"]), 8)
        self.assertEqual(
            result["publication_summary"]["horizon_status_counts"],
            {"gate_passed": 40},
        )
        sample = result["reference_class_results"][0]
        five_year = next(
            item for item in sample["horizons"] if item["horizon_years"] == 5
        )
        self.assertEqual(five_year["status"], "gate_passed")
        self.assertEqual(five_year["selected_method"], "median_recent_yoy_drift")
        self.assertAlmostEqual(
            five_year["projected_cumulative_change_percent"],
            (1.005**20 - 1) * 100,
            places=3,
        )
        self.assertIsNone(result["ai_attributable_increment"]["cost_escalation_percent"])

    def test_insufficient_history_fails_closed_with_null_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(source, observation_count=38)
            result = build_reference_class_baseline(source)

        sample = result["reference_class_results"][0]
        self.assertEqual(sample["release_state"], "not_assessed")
        for horizon in sample["horizons"]:
            self.assertEqual(horizon["status"], "not_assessed")
            self.assertIsNone(horizon["projected_index"])

    def test_missing_quarter_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(source, omit_offset=25)
            with self.assertRaisesRegex(ValidationError, "missing calendar quarter"):
                build_reference_class_baseline(source)

    def test_runner_writes_same_auditable_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "bcpi.csv"
            output = root / "baseline.json"
            self.write_history(source)
            result = run_reference_class_baseline(source, output)
            written = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(written, result)
        self.assertEqual(len(written["input_sha256"]), 64)

    def test_custom_provincial_scope_does_not_transfer_alberta_geographies(self) -> None:
        provincial_geographies = {
            "PR_24": "Quebec",
            "PR_35": "Ontario",
            "PR_59": "British Columbia",
        }
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bcpi.csv"
            self.write_history(
                source,
                observation_count=38,
                geography_labels=provincial_geographies,
            )
            result = build_reference_class_baseline(
                source,
                geography_labels=provincial_geographies,
                model_id="PROVINCIAL_TEST",
                limitations=["Province-specific test limitation."],
            )

        self.assertEqual(result["model_id"], "PROVINCIAL_TEST")
        self.assertEqual(len(result["reference_class_results"]), 12)
        self.assertEqual(
            {
                item["geography_id"]
                for item in result["reference_class_results"]
            },
            set(provincial_geographies),
        )
        self.assertEqual(result["release_state"], "not_assessed")
        self.assertEqual(result["limitations"], ["Province-specific test limitation."])


if __name__ == "__main__":
    unittest.main()
