from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from .calibration import GEOGRAPHY_LABELS, REFERENCE_CLASSES, SOURCE_ID
from .schemas import ValidationError


MODEL_ID = "AIIO_AB_PROJECT_HISTORICAL_ANALOG_MATRIX_0_1"
PROFILE_IDS = ("even", "front_loaded", "back_loaded")
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
MAX_HORIZON_YEARS = 10


def _quarter_ordinal(period_end: str) -> int:
    year, month, day = (int(value) for value in period_end.split("-"))
    expected_days = {3: 31, 6: 30, 9: 30, 12: 31}
    if expected_days.get(month) != day:
        raise ValidationError(f"BCPI period is not a calendar quarter-end: {period_end}")
    return year * 4 + (month // 3 - 1)


def _percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValidationError("historical analog percentile requires observations")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _profile(duration_years: int, profile_id: str) -> list[float]:
    if not 1 <= duration_years <= MAX_HORIZON_YEARS:
        raise ValidationError("duration_years is outside the historical analog grid")
    if profile_id == "even":
        weights = [1.0] * duration_years
    elif profile_id == "front_loaded":
        weights = [float(value) for value in range(duration_years, 0, -1)]
    elif profile_id == "back_loaded":
        weights = [float(value) for value in range(1, duration_years + 1)]
    else:
        raise ValidationError(f"unsupported historical analog profile: {profile_id}")
    total = sum(weights)
    return [value / total for value in weights]


def _validate_series(rows: list[dict[str, str]]) -> tuple[list[str], list[float]]:
    ordered = sorted(rows, key=lambda row: row["period_end"])
    if not ordered:
        raise ValidationError("historical analog reference series cannot be empty")
    periods = [row["period_end"] for row in ordered]
    if len(periods) != len(set(periods)):
        raise ValidationError("historical analog reference series has duplicate periods")
    ordinals = [_quarter_ordinal(period) for period in periods]
    if any(current != previous + 1 for previous, current in zip(ordinals, ordinals[1:])):
        raise ValidationError("historical analog reference series has a missing calendar quarter")
    if {row["source_id"] for row in ordered} != {SOURCE_ID}:
        raise ValidationError("historical analog source changed within a series")
    if len({row["unit"] for row in ordered}) != 1:
        raise ValidationError("historical analog unit changed within a series")
    values = [float(row["value"]) for row in ordered]
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValidationError("historical analog values must be finite and positive")
    return periods, values


def _grid_result(
    periods: list[str],
    values: list[float],
    *,
    start_lag_years: int,
    duration_years: int,
    profile_id: str,
) -> dict[str, Any]:
    shares = _profile(duration_years, profile_id)
    expenditure_horizons = [start_lag_years + offset for offset in range(duration_years)]
    maximum_horizon = max(expenditure_horizons)
    maximum_horizon_quarters = maximum_horizon * 4
    origin_count = len(values) - maximum_horizon_quarters
    schedule = [
        {
            "horizon_years": horizon,
            "share": round(share, 9),
        }
        for horizon, share in zip(expenditure_horizons, shares)
    ]
    base = {
        "start_lag_years": start_lag_years,
        "duration_years": duration_years,
        "profile_id": profile_id,
        "expenditure_schedule": schedule,
        "maximum_horizon_years": maximum_horizon,
    }
    if origin_count <= 0:
        return {
            **base,
            "status": "not_assessed",
            "reason": "the reference series has no complete historical trajectory for this schedule",
            "overlapping_trajectory_count": 0,
            "non_overlapping_trajectory_count": 0,
            "first_origin_period_end": None,
            "latest_origin_period_end": None,
            "schedule_weighted_factor": None,
            "schedule_weighted_change_percent": None,
        }

    factors = []
    for origin_index in range(origin_count):
        origin = values[origin_index]
        factor = sum(
            share * (values[origin_index + horizon * 4] / origin)
            for horizon, share in zip(expenditure_horizons, shares)
        )
        factors.append(factor)
    non_overlapping = (
        (len(values) - 1) // maximum_horizon_quarters
        if maximum_horizon_quarters > 0
        else len(values)
    )
    factor_quantiles = {
        f"p{int(probability * 100):02d}": round(_percentile(factors, probability), 6)
        for probability in QUANTILES
    }
    factor_summary = {
        **factor_quantiles,
        "minimum": round(min(factors), 6),
        "maximum": round(max(factors), 6),
    }
    change_summary = {
        key: round((value - 1) * 100, 3)
        for key, value in factor_summary.items()
    }
    return {
        **base,
        "status": (
            "historical_context_available"
            if non_overlapping >= 8
            else "limited_history_only"
        ),
        "reason": None,
        "overlapping_trajectory_count": len(factors),
        "non_overlapping_trajectory_count": non_overlapping,
        "first_origin_period_end": periods[0],
        "latest_origin_period_end": periods[origin_count - 1],
        "schedule_weighted_factor": factor_summary,
        "schedule_weighted_change_percent": change_summary,
    }


def build_historical_analog_matrix(bcpi_path: Path) -> dict[str, Any]:
    with bcpi_path.open(encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
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
            "historical analog reference-class coverage changed; "
            f"missing={sorted(expected_keys - set(grouped))}, "
            f"unexpected={sorted(set(grouped) - expected_keys)}"
        )

    series_results = []
    for asset_class, definition in REFERENCE_CLASSES.items():
        for geography_id, geography_label in GEOGRAPHY_LABELS.items():
            rows = grouped[(definition["indicator_id"], geography_id)]
            periods, values = _validate_series(rows)
            grid = []
            for duration_years in range(1, MAX_HORIZON_YEARS + 1):
                for start_lag_years in range(
                    0, MAX_HORIZON_YEARS - duration_years + 2
                ):
                    for profile_id in PROFILE_IDS:
                        grid.append(
                            _grid_result(
                                periods,
                                values,
                                start_lag_years=start_lag_years,
                                duration_years=duration_years,
                                profile_id=profile_id,
                            )
                        )
            series_results.append(
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
                    "grid": grid,
                }
            )

    return {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "source_id": SOURCE_ID,
        "input_sha256": hashlib.sha256(bcpi_path.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "as_of_date": max(item["latest_period_end"] for item in series_results),
        "evidence_status": "observed_series_with_inferred_historical_analog_stress_test",
        "estimand": (
            "The empirical distribution of a project's schedule-weighted BCPI factor "
            "across coherent historical trajectories matching its declared start lag, "
            "duration and expenditure-profile shape."
        ),
        "configuration": {
            "maximum_horizon_years": MAX_HORIZON_YEARS,
            "profile_ids": list(PROFILE_IDS),
            "profile_rules": {
                "even": "equal annual shares",
                "front_loaded": "linearly declining annual shares",
                "back_loaded": "linearly increasing annual shares",
            },
            "quantiles": [int(value * 100) for value in QUANTILES],
            "trajectory_method": "same-quarter annual index factors from each eligible historical quarterly origin",
            "schedule_weighting_method": "sum(expenditure_share × historical_index_at_horizon / index_at_origin)",
        },
        "publication_authorization": {
            "historical_analog_stress_test_authorized": True,
            "historical_analog_budget_translation_authorized": True,
            "future_projection_authorized": False,
            "probability_interval_authorized": False,
            "recommended_escalation_allowance_authorized": False,
            "ai_attributable_effect_authorized": False,
            "forecast_project_cost_translation_authorized": False,
            "reason": (
                "The artifact authorizes transparent what-if translation of a user-entered "
                "price-basis estimate under coherent observed historical index paths. It does "
                "not select a future path, attach probabilities, recommend an allowance or "
                "estimate an AI increment."
            ),
        },
        "reference_class_results": series_results,
        "unsupported_asset_classes": [
            "roads_transit_and_airports",
            "municipal_water_and_resilience",
            "power_sector_infrastructure",
        ],
        "limitations": [
            "BCPI measures contractor bid-price change for model buildings, not realized total project cost.",
            "Historical trajectory origins overlap and are serially dependent; quantiles are descriptive markers, not probabilities or confidence intervals.",
            "The entered estimate must be stated in the artifact's latest price basis and must exclude any escalation already embedded in the estimate.",
            "Annual expenditure profiles are declared stress-test shapes, not inferred project cash flows.",
            "Calgary and Edmonton CMA references are local building-market proxies, not province-wide or civil-infrastructure indexes.",
            "The matrix contains no AI-attributable increment and does not use graph pressure scores.",
        ],
    }


def run_historical_analog_matrix(bcpi_path: Path, output_path: Path) -> dict[str, Any]:
    result = build_historical_analog_matrix(bcpi_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
