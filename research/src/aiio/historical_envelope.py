from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .calibration import GEOGRAPHY_LABELS, REFERENCE_CLASSES, SOURCE_ID
from .schemas import ValidationError


MODEL_ID = "AIIO_AB_BCPI_HISTORICAL_ENVELOPE_0_1"
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)


def _quarter_ordinal(period_end: str) -> int:
    year, month, day = (int(value) for value in period_end.split("-"))
    expected_days = {3: 31, 6: 30, 9: 30, 12: 31}
    if expected_days.get(month) != day:
        raise ValidationError(f"BCPI period is not a calendar quarter-end: {period_end}")
    return year * 4 + (month // 3 - 1)


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValidationError("historical envelope requires at least one window")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _validate_series(rows: list[dict[str, str]]) -> tuple[list[str], list[float]]:
    if not rows:
        raise ValidationError("historical envelope series cannot be empty")
    ordered = sorted(rows, key=lambda row: row["period_end"])
    periods = [row["period_end"] for row in ordered]
    if len(periods) != len(set(periods)):
        raise ValidationError("historical envelope series contains duplicate periods")
    ordinals = [_quarter_ordinal(period) for period in periods]
    if any(current != previous + 1 for previous, current in zip(ordinals, ordinals[1:])):
        raise ValidationError("historical envelope series contains a missing calendar quarter")
    if any(not row["value"] for row in ordered):
        raise ValidationError("historical envelope series contains a missing index value")
    values = [float(row["value"]) for row in ordered]
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValidationError("historical envelope values must be finite and positive")
    if {row["source_id"] for row in ordered} != {SOURCE_ID}:
        raise ValidationError("historical envelope source changed within a series")
    if len({row["unit"] for row in ordered}) != 1:
        raise ValidationError("historical envelope unit changed within a series")
    return periods, values


def _horizon_summary(
    periods: list[str], values: list[float], horizon_years: int
) -> dict[str, Any]:
    horizon_quarters = horizon_years * 4
    if len(values) <= horizon_quarters:
        raise ValidationError("historical envelope has insufficient horizon history")
    changes = [
        (values[index] / values[index - horizon_quarters] - 1) * 100
        for index in range(horizon_quarters, len(values))
    ]
    latest = changes[-1]
    previous = changes[:-1]
    rank_sample = previous or changes
    percentile_rank = (
        sum(value <= latest for value in rank_sample) / len(rank_sample) * 100
    )
    non_overlapping_window_count = (len(values) - 1) // horizon_quarters
    quantiles = {
        f"p{int(probability * 100):02d}": round(
            _percentile(changes, probability), 3
        )
        for probability in QUANTILES
    }
    median_change = quantiles["p50"]
    median_annualized = (
        (1 + median_change / 100) ** (1 / horizon_years) - 1
    ) * 100
    return {
        "horizon_years": horizon_years,
        "horizon_quarters": horizon_quarters,
        "overlapping_window_count": len(changes),
        "non_overlapping_window_count": non_overlapping_window_count,
        "interpretation_status": (
            "historical_context_available"
            if non_overlapping_window_count >= 8
            else "limited_history_only"
        ),
        "first_window_origin_period_end": periods[0],
        "first_window_target_period_end": periods[horizon_quarters],
        "latest_window_origin_period_end": periods[-horizon_quarters - 1],
        "latest_window_target_period_end": periods[-1],
        "historical_cumulative_change_percent": {
            **quantiles,
            "minimum": round(min(changes), 3),
            "maximum": round(max(changes), 3),
        },
        "historical_median_annualized_change_percent": round(
            median_annualized, 3
        ),
        "latest_realized_cumulative_change_percent": round(latest, 3),
        "latest_realized_percentile_rank": round(percentile_rank, 1),
    }


def build_historical_reference_envelope(
    bcpi_path: Path,
    *,
    horizons_years: Iterable[int] = range(1, 6),
) -> dict[str, Any]:
    horizon_list = sorted(set(horizons_years))
    if not horizon_list or any(year < 1 or year > 10 for year in horizon_list):
        raise ValidationError("historical envelope horizons must be unique years from 1 through 10")
    with bcpi_path.open(encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    if not source_rows:
        raise ValidationError("historical envelope cannot use an empty input")

    eligible_indicators = {
        definition["indicator_id"] for definition in REFERENCE_CLASSES.values()
    }
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        if (
            row["indicator_id"] in eligible_indicators
            and row["geography_id"] in GEOGRAPHY_LABELS
        ):
            grouped[(row["indicator_id"], row["geography_id"])].append(row)
    expected_keys = {
        (definition["indicator_id"], geography_id)
        for definition in REFERENCE_CLASSES.values()
        for geography_id in GEOGRAPHY_LABELS
    }
    if set(grouped) != expected_keys:
        raise ValidationError(
            "historical envelope reference-class coverage changed; "
            f"missing={sorted(expected_keys - set(grouped))}, "
            f"unexpected={sorted(set(grouped) - expected_keys)}"
        )

    results = []
    for asset_class, definition in REFERENCE_CLASSES.items():
        for geography_id, geography_label in GEOGRAPHY_LABELS.items():
            rows = grouped[(definition["indicator_id"], geography_id)]
            periods, values = _validate_series(rows)
            results.append(
                {
                    "asset_class": asset_class,
                    "asset_class_label": definition["label"],
                    "reference_indicator_id": definition["indicator_id"],
                    "reference_class_label": definition["reference_label"],
                    "mapping_status": definition["mapping_status"],
                    "mapping_note": definition["mapping_note"],
                    "geography_id": geography_id,
                    "geography_label": geography_label,
                    "unit": rows[0]["unit"],
                    "observation_count": len(values),
                    "first_period_end": periods[0],
                    "latest_period_end": periods[-1],
                    "latest_index": round(values[-1], 3),
                    "horizons": [
                        _horizon_summary(periods, values, horizon_year)
                        for horizon_year in horizon_list
                    ],
                }
            )

    return {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "source_id": SOURCE_ID,
        "input_sha256": hashlib.sha256(bcpi_path.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "as_of_date": max(item["latest_period_end"] for item in results),
        "evidence_status": "observed_series_with_inferred_historical_summary",
        "estimand": (
            "The empirical distribution of realized cumulative percentage changes "
            "in each BCPI model-building reference index across all overlapping "
            "historical windows of the stated length."
        ),
        "configuration": {
            "horizons_years": horizon_list,
            "quantiles": [int(value * 100) for value in QUANTILES],
            "window_method": "all overlapping quarterly-origin windows",
            "annualization_method": "compound annual rate implied by the historical median cumulative change",
        },
        "publication_authorization": {
            "historical_summary_authorized": True,
            "future_projection_authorized": False,
            "ai_attributable_effect_authorized": False,
            "project_cost_translation_authorized": False,
            "reason": (
                "The artifact publishes deterministic descriptive statistics from "
                "observed public index history. It does not project a future index, "
                "select a probability distribution or translate an AI effect into cost."
            ),
        },
        "reference_class_results": results,
        "unsupported_asset_classes": [
            "roads_transit_and_airports",
            "municipal_water_and_resilience",
            "power_sector_infrastructure",
        ],
        "limitations": [
            "BCPI measures contractor bid-price change for model buildings, not the realized cost of a particular project.",
            "Overlapping historical windows are serially dependent; their quantiles are descriptive and are not confidence or probability intervals.",
            "A horizon is labelled historical_context_available only when the series spans at least eight non-overlapping windows; shorter histories remain limited-history summaries.",
            "Historical ranges do not incorporate a current macroeconomic forecast or condition on the Alberta AI-infrastructure scenario.",
            "Calgary and Edmonton CMA reference indexes are not province-wide substitutes.",
            "A future planning range, project-cost translation or AI increment requires a separately validated and authorized method.",
        ],
    }


def run_historical_reference_envelope(
    bcpi_path: Path, output_path: Path
) -> dict[str, Any]:
    result = build_historical_reference_envelope(bcpi_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
