from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from .schemas import ValidationError


MODEL_ID = "AIIO_AB_BCPI_REFERENCE_BASELINE_0_1"
SOURCE_ID = "STATCAN_BCPI_18100289"
LOOKBACK_QUARTERS = 20
MAX_BACKTEST_ORIGINS = 40
MIN_CALIBRATION_ORIGINS = 15
MIN_VALIDATION_ORIGINS = 10
DRIFT_SELECTION_MARGIN_PERCENTAGE_POINTS = 0.10
MAX_VALIDATION_MAPE_PERCENT = 15.0
MAX_ABSOLUTE_VALIDATION_BIAS_PERCENT = 10.0
MAX_DEGRADATION_FROM_FLAT_PERCENTAGE_POINTS = 2.0
MIN_VALIDATION_INTERVAL_COVERAGE_PERCENT = 60.0


def _implementation_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

GEOGRAPHY_LABELS = {
    "CMA_825": "Calgary CMA",
    "CMA_835": "Edmonton CMA",
}
PROVINCIAL_REFERENCE_MODEL_ID = "AIIO_CA_BC_ON_QC_BCPI_REFERENCE_BASELINE_0_1"
PROVINCIAL_REFERENCE_GEOGRAPHY_LABELS = {
    "PR_24": "Quebec",
    "PR_35": "Ontario",
    "PR_59": "British Columbia",
}
PROVINCIAL_REFERENCE_LIMITATIONS = [
    "BCPI measures contractor bid-price change for model buildings, not the realized cost of a particular project.",
    "Province-level model-building indexes do not substitute for local project-market conditions.",
    "The published provincial history begins in 2017 and may be too short for the locked rolling-origin validation partitions.",
    "Empirical error bands are historical forecast-error ranges, not confidence intervals or probability guarantees.",
    "The baseline contains no AI-attributable effect and no Alberta coefficient is transferred across provinces.",
]

REFERENCE_CLASSES = {
    "health_facilities": {
        "label": "Health facility",
        "indicator_id": "BCPI_INSTITUTIONAL_BUILDINGS_62213_DIVISION_COMPOSITE",
        "reference_label": "Institutional buildings division composite",
        "mapping_status": "proxy",
        "mapping_note": (
            "The source is an institutional-building aggregate, not a hospital-specific index."
        ),
    },
    "schools_and_postsecondary": {
        "label": "School or post-secondary facility",
        "indicator_id": "BCPI_SCHOOL_DIVISION_COMPOSITE",
        "reference_label": "School division composite",
        "mapping_status": "direct_for_school_proxy_for_postsecondary",
        "mapping_note": (
            "The source represents schools directly and is only a proxy for post-secondary facilities."
        ),
    },
    "government_and_civic_facilities": {
        "label": "Government administrative facility",
        "indicator_id": "BCPI_OFFICE_BUILDING_62212_DIVISION_COMPOSITE",
        "reference_label": "Office building division composite",
        "mapping_status": "proxy_for_administrative_facilities_only",
        "mapping_note": (
            "The source may inform administrative offices but not every civic facility subtype."
        ),
    },
    "municipal_operations_facilities": {
        "label": "Municipal operations facility",
        "indicator_id": (
            "BCPI_BUS_DEPOT_WITH_MAINTENANCE_AND_REPAIR_FACILITIES_"
            "DIVISION_COMPOSITE"
        ),
        "reference_label": (
            "Bus depot with maintenance and repair facilities division composite"
        ),
        "mapping_status": "proxy",
        "mapping_note": (
            "The source is a municipal-operations building proxy and does not represent water or resilience works."
        ),
    },
}

UNSUPPORTED_ASSET_CLASSES = {
    "roads_transit_and_airports": (
        "The BCPI building reference classes do not represent horizontal civil or "
        "transportation construction."
    ),
    "municipal_water_and_resilience": (
        "The BCPI building reference classes do not represent water, wastewater or "
        "resilience infrastructure."
    ),
    "power_sector_infrastructure": (
        "The BCPI building reference classes do not represent generation, transmission "
        "or distribution construction."
    ),
}


def _quarter_ordinal(period_end: str) -> int:
    parsed = date.fromisoformat(period_end)
    if parsed.month not in {3, 6, 9, 12}:
        raise ValidationError(f"BCPI period is not a calendar quarter-end: {period_end}")
    return parsed.year * 4 + (parsed.month // 3 - 1)


def _percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValidationError("cannot calculate a percentile from an empty sample")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _round(value: float | None, digits: int = 3) -> float | None:
    return None if value is None else round(value, digits)


def _metrics(errors_percent: list[float]) -> dict[str, float | int]:
    if not errors_percent:
        raise ValidationError("cannot calculate validation metrics without errors")
    return {
        "origin_count": len(errors_percent),
        "mean_absolute_percentage_error": round(
            sum(abs(value) for value in errors_percent) / len(errors_percent), 3
        ),
        "mean_percentage_error": round(
            sum(errors_percent) / len(errors_percent), 3
        ),
        "root_mean_squared_percentage_error": round(
            math.sqrt(
                sum(value * value for value in errors_percent) / len(errors_percent)
            ),
            3,
        ),
    }


def _median_recent_yoy_log_rate(values: list[float]) -> float:
    if len(values) < LOOKBACK_QUARTERS:
        raise ValidationError(
            f"drift candidate requires at least {LOOKBACK_QUARTERS} quarterly observations"
        )
    start = max(4, len(values) - LOOKBACK_QUARTERS)
    annual_log_changes = [
        math.log(values[index] / values[index - 4])
        for index in range(start, len(values))
    ]
    if not annual_log_changes:
        raise ValidationError("drift candidate has no year-over-year changes")
    return median(annual_log_changes)


def _predict(values: list[float], horizon_quarters: int, method: str) -> float:
    if method == "flat_index":
        return values[-1]
    if method == "median_recent_yoy_drift":
        annual_log_rate = _median_recent_yoy_log_rate(values)
        return values[-1] * math.exp(annual_log_rate * horizon_quarters / 4)
    raise ValidationError(f"unknown baseline method: {method}")


def _backtest_rows(
    values: list[float], periods: list[str], horizon_quarters: int
) -> list[dict[str, Any]]:
    rows = []
    first_origin = LOOKBACK_QUARTERS - 1
    last_origin = len(values) - horizon_quarters - 1
    for origin in range(first_origin, last_origin + 1):
        training = values[: origin + 1]
        actual = values[origin + horizon_quarters]
        predictions = {
            method: _predict(training, horizon_quarters, method)
            for method in ("flat_index", "median_recent_yoy_drift")
        }
        rows.append(
            {
                "origin_period_end": periods[origin],
                "target_period_end": periods[origin + horizon_quarters],
                "actual_index": actual,
                "predictions": predictions,
                "errors_percent": {
                    method: (actual / prediction - 1) * 100
                    for method, prediction in predictions.items()
                },
            }
        )
    return rows[-MAX_BACKTEST_ORIGINS:]


def _forecast_horizon(
    values: list[float], periods: list[str], horizon_years: int
) -> dict[str, Any]:
    horizon_quarters = horizon_years * 4
    rows = _backtest_rows(values, periods, horizon_quarters)
    split = len(rows) // 2
    calibration_rows = rows[:split]
    validation_rows = rows[split:]
    if (
        len(calibration_rows) < MIN_CALIBRATION_ORIGINS
        or len(validation_rows) < MIN_VALIDATION_ORIGINS
    ):
        return {
            "horizon_years": horizon_years,
            "horizon_quarters": horizon_quarters,
            "status": "not_assessed",
            "reason": "insufficient rolling-origin history for locked partitions",
            "available_origin_count": len(rows),
            "required_calibration_origin_count": MIN_CALIBRATION_ORIGINS,
            "required_validation_origin_count": MIN_VALIDATION_ORIGINS,
            "selected_method": None,
            "projected_index": None,
            "projected_cumulative_change_percent": None,
            "empirical_error_band_low_index": None,
            "empirical_error_band_high_index": None,
            "empirical_error_band_low_change_percent": None,
            "empirical_error_band_high_change_percent": None,
        }

    calibration_metrics = {
        method: _metrics([row["errors_percent"][method] for row in calibration_rows])
        for method in ("flat_index", "median_recent_yoy_drift")
    }
    flat_calibration_mape = calibration_metrics["flat_index"][
        "mean_absolute_percentage_error"
    ]
    drift_calibration_mape = calibration_metrics["median_recent_yoy_drift"][
        "mean_absolute_percentage_error"
    ]
    selected_method = (
        "median_recent_yoy_drift"
        if drift_calibration_mape
        < flat_calibration_mape - DRIFT_SELECTION_MARGIN_PERCENTAGE_POINTS
        else "flat_index"
    )

    calibration_errors = [
        row["errors_percent"][selected_method] for row in calibration_rows
    ]
    validation_errors = [
        row["errors_percent"][selected_method] for row in validation_rows
    ]
    lower_error_percent = _percentile(calibration_errors, 0.10)
    upper_error_percent = _percentile(calibration_errors, 0.90)
    validation_metrics = _metrics(validation_errors)
    flat_validation_metrics = _metrics(
        [row["errors_percent"]["flat_index"] for row in validation_rows]
    )
    covered = 0
    for row in validation_rows:
        prediction = row["predictions"][selected_method]
        lower = prediction * (1 + lower_error_percent / 100)
        upper = prediction * (1 + upper_error_percent / 100)
        if min(lower, upper) <= row["actual_index"] <= max(lower, upper):
            covered += 1
    coverage_percent = covered / len(validation_rows) * 100

    gates = {
        "minimum_partition_sizes": True,
        "validation_mape_at_most_15_percent": (
            validation_metrics["mean_absolute_percentage_error"]
            <= MAX_VALIDATION_MAPE_PERCENT
        ),
        "absolute_validation_bias_at_most_10_percent": (
            abs(validation_metrics["mean_percentage_error"])
            <= MAX_ABSOLUTE_VALIDATION_BIAS_PERCENT
        ),
        "not_materially_worse_than_flat_benchmark": (
            validation_metrics["mean_absolute_percentage_error"]
            <= flat_validation_metrics["mean_absolute_percentage_error"]
            + MAX_DEGRADATION_FROM_FLAT_PERCENTAGE_POINTS
        ),
        "validation_interval_coverage_at_least_60_percent": (
            coverage_percent >= MIN_VALIDATION_INTERVAL_COVERAGE_PERCENT
        ),
    }
    passed = all(gates.values())
    current_index = values[-1]
    point = _predict(values, horizon_quarters, selected_method)
    low = point * (1 + lower_error_percent / 100)
    high = point * (1 + upper_error_percent / 100)
    low, high = min(low, high), max(low, high)

    return {
        "horizon_years": horizon_years,
        "horizon_quarters": horizon_quarters,
        "status": "gate_passed" if passed else "gate_failed",
        "reason": None if passed else "one or more predeclared validation gates failed",
        "selected_method": selected_method,
        "selection_rule": (
            "drift must improve calibration MAPE by more than 0.10 percentage points; "
            "otherwise select flat"
        ),
        "calibration_period": {
            "origin_count": len(calibration_rows),
            "first_origin_period_end": calibration_rows[0]["origin_period_end"],
            "last_target_period_end": calibration_rows[-1]["target_period_end"],
            "candidate_metrics": calibration_metrics,
            "selected_error_percentiles": {
                "p10": _round(lower_error_percent),
                "p90": _round(upper_error_percent),
            },
        },
        "validation_period": {
            "origin_count": len(validation_rows),
            "first_origin_period_end": validation_rows[0]["origin_period_end"],
            "last_target_period_end": validation_rows[-1]["target_period_end"],
            "selected_method_metrics": validation_metrics,
            "flat_benchmark_metrics": flat_validation_metrics,
            "empirical_interval_coverage_percent": _round(coverage_percent, 1),
        },
        "gates": gates,
        "projected_index": _round(point) if passed else None,
        "projected_cumulative_change_percent": (
            _round((point / current_index - 1) * 100) if passed else None
        ),
        "empirical_error_band_low_index": _round(low) if passed else None,
        "empirical_error_band_high_index": _round(high) if passed else None,
        "empirical_error_band_low_change_percent": (
            _round((low / current_index - 1) * 100) if passed else None
        ),
        "empirical_error_band_high_change_percent": (
            _round((high / current_index - 1) * 100) if passed else None
        ),
    }


def _validate_series(rows: list[dict[str, str]]) -> tuple[list[str], list[float]]:
    if not rows:
        raise ValidationError("BCPI reference series cannot be empty")
    ordered = sorted(rows, key=lambda row: row["period_end"])
    periods = [row["period_end"] for row in ordered]
    if len(periods) != len(set(periods)):
        raise ValidationError("BCPI reference series contains duplicate periods")
    ordinals = [_quarter_ordinal(period) for period in periods]
    if any(current != previous + 1 for previous, current in zip(ordinals, ordinals[1:])):
        raise ValidationError("BCPI reference series contains a missing calendar quarter")
    if any(not row["value"] for row in ordered):
        raise ValidationError("BCPI reference series contains a missing index value")
    values = [float(row["value"]) for row in ordered]
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValidationError("BCPI reference series values must be finite and positive")
    units = {row["unit"] for row in ordered}
    sources = {row["source_id"] for row in ordered}
    if len(units) != 1 or sources != {SOURCE_ID}:
        raise ValidationError("BCPI reference series unit or source changed within history")
    return periods, values


def build_reference_class_baseline(
    bcpi_path: Path,
    *,
    horizons_years: Iterable[int] = range(1, 6),
    geography_labels: dict[str, str] | None = None,
    model_id: str = MODEL_ID,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    horizon_list = sorted(set(horizons_years))
    if not horizon_list or any(year < 1 or year > 10 for year in horizon_list):
        raise ValidationError("baseline horizons must be unique years from 1 through 10")
    with bcpi_path.open(encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    if not source_rows:
        raise ValidationError("BCPI baseline cannot use an empty input")
    active_geography_labels = (
        GEOGRAPHY_LABELS if geography_labels is None else geography_labels
    )
    if not active_geography_labels:
        raise ValidationError("baseline requires at least one geography")

    eligible_indicators = {
        definition["indicator_id"] for definition in REFERENCE_CLASSES.values()
    }
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        if (
            row["indicator_id"] in eligible_indicators
            and row["geography_id"] in active_geography_labels
        ):
            grouped[(row["indicator_id"], row["geography_id"])].append(row)

    expected_keys = {
        (definition["indicator_id"], geography_id)
        for definition in REFERENCE_CLASSES.values()
        for geography_id in active_geography_labels
    }
    if set(grouped) != expected_keys:
        missing = sorted(expected_keys - set(grouped))
        unexpected = sorted(set(grouped) - expected_keys)
        raise ValidationError(
            f"BCPI reference-class coverage changed; missing={missing}, unexpected={unexpected}"
        )

    outputs = []
    for asset_class, definition in REFERENCE_CLASSES.items():
        for geography_id, geography_label in active_geography_labels.items():
            rows = grouped[(definition["indicator_id"], geography_id)]
            periods, values = _validate_series(rows)
            horizons = [
                _forecast_horizon(values, periods, horizon_year)
                for horizon_year in horizon_list
            ]
            outputs.append(
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
                    "latest_index": _round(values[-1]),
                    "release_state": (
                        "baseline_only"
                        if any(item["status"] == "gate_passed" for item in horizons)
                        else "not_assessed"
                    ),
                    "horizons": horizons,
                }
            )

    input_hash = hashlib.sha256(bcpi_path.read_bytes()).hexdigest()
    as_of_date = max(item["latest_period_end"] for item in outputs)
    horizon_status_counts: dict[str, int] = defaultdict(int)
    for output in outputs:
        for horizon in output["horizons"]:
            horizon_status_counts[horizon["status"]] += 1
    any_horizon_passed = any(
        item["release_state"] == "baseline_only" for item in outputs
    )
    return {
        "schema_version": "1.0.0",
        "model_id": model_id,
        "source_id": SOURCE_ID,
        "input_sha256": input_hash,
        "code_sha256": _implementation_sha256(),
        "as_of_date": as_of_date,
        "evidence_status": "observed_series_with_held_out_model_validation",
        "release_state": (
            "baseline_only" if any_horizon_passed else "not_assessed"
        ),
        "publication_authorization": {
            "status": "withheld_pending_independent_modelling_review",
            "public_projection_authorized": False,
            "reason": (
                "The reproducible internal run is complete, but the required independent "
                "modelling gate has not returned a verdict."
            ),
        },
        "estimand": (
            "Cumulative percentage change in a BCPI model-building reference index "
            "from the latest observed quarter to the stated horizon."
        ),
        "publication_summary": {
            "reference_series_count": len(outputs),
            "horizon_result_count": sum(horizon_status_counts.values()),
            "horizon_status_counts": dict(sorted(horizon_status_counts.items())),
            "warning": (
                (
                    "A baseline_only release state means at least one reference-series "
                    "horizon passed. Each requested asset, geography and horizon must be "
                    "checked individually; failed values remain null."
                )
                if any_horizon_passed
                else (
                    "No reference-series horizon has enough validated evidence for a "
                    "projection. Every project-cost output remains null."
                )
            ),
        },
        "configuration": {
            "horizons_years": horizon_list,
            "lookback_quarters": LOOKBACK_QUARTERS,
            "max_backtest_origins": MAX_BACKTEST_ORIGINS,
            "calibration_partition": "earlier half of retained rolling origins",
            "validation_partition": "later half of retained rolling origins",
            "candidate_methods": ["flat_index", "median_recent_yoy_drift"],
            "empirical_error_band_percentiles": [10, 90],
            "gates": {
                "minimum_calibration_origins": MIN_CALIBRATION_ORIGINS,
                "minimum_validation_origins": MIN_VALIDATION_ORIGINS,
                "maximum_validation_mape_percent": MAX_VALIDATION_MAPE_PERCENT,
                "maximum_absolute_validation_bias_percent": (
                    MAX_ABSOLUTE_VALIDATION_BIAS_PERCENT
                ),
                "maximum_degradation_from_flat_percentage_points": (
                    MAX_DEGRADATION_FROM_FLAT_PERCENTAGE_POINTS
                ),
                "minimum_validation_interval_coverage_percent": (
                    MIN_VALIDATION_INTERVAL_COVERAGE_PERCENT
                ),
            },
        },
        "reference_class_results": outputs,
        "unsupported_asset_classes": [
            {
                "asset_class": asset_class,
                "status": "not_assessed",
                "reason": reason,
            }
            for asset_class, reason in UNSUPPORTED_ASSET_CLASSES.items()
        ],
        "ai_attributable_increment": {
            "status": "not_calibrated",
            "cost_escalation_percent": None,
            "cost_escalation_cad": None,
            "schedule_delay_days": None,
            "reason": (
                "No reviewed historical treatment, counterfactual and project-outcome "
                "panel currently identifies an AI-infrastructure effect."
            ),
        },
        "graph_role": (
            "Mechanism and exposure ranking only; graph pressure scores are not inputs "
            "to the reference-index projection."
        ),
        "limitations": (
            limitations
            if limitations is not None
            else [
                "BCPI measures contractor bid-price change for model buildings, not the realized cost of a particular project.",
                "Calgary and Edmonton CMA results are not province-wide substitutes.",
                "Empirical error bands are historical forecast-error ranges, not confidence intervals or probability guarantees.",
                "A project-cost translation requires a known estimate price basis and a declared expenditure profile.",
                "The baseline contains no AI-attributable effect and must not be added to a graph pressure score.",
            ]
        ),
    }


def run_reference_class_baseline(
    bcpi_path: Path,
    output_path: Path,
    *,
    horizons_years: Iterable[int] = range(1, 6),
    geography_labels: dict[str, str] | None = None,
    model_id: str = MODEL_ID,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    result = build_reference_class_baseline(
        bcpi_path,
        horizons_years=horizons_years,
        geography_labels=geography_labels,
        model_id=model_id,
        limitations=limitations,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
