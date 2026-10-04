from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .adapters.statcan import PROVINCE_DGUID_TO_GEOGRAPHY_ID
from .adapters.statcan_investment import quarter_boundaries
from .schemas import ValidationError


MODEL_ID = "AIIO_REGIONAL_MACRO_CONTROLS_CANADA_0_1"
TRANSFORMATION_ID = "TR_AIIO_REGIONAL_MACRO_QUARTERLY_CONTROLS_0_1"
PANEL_START_QUARTER = "2017-Q1"

CPI_SOURCE_ID = "STATCAN_CPI_18100004"
POPULATION_SOURCE_ID = "STATCAN_POPULATION_17100009"
EARNINGS_SOURCE_ID = "STATCAN_SEPH_EARNINGS_14100223"
HOUSING_SOURCE_ID = "STATCAN_CMHC_HOUSING_STARTS_34100156"
INVESTMENT_SOURCE_ID = "STATCAN_IBC_34100293"

PROVINCE_LABELS = {
    "PR_10": "Newfoundland and Labrador",
    "PR_11": "Prince Edward Island",
    "PR_12": "Nova Scotia",
    "PR_13": "New Brunswick",
    "PR_24": "Quebec",
    "PR_35": "Ontario",
    "PR_46": "Manitoba",
    "PR_47": "Saskatchewan",
    "PR_48": "Alberta",
    "PR_59": "British Columbia",
    "PR_60": "Yukon",
    "PR_61": "Northwest Territories",
    "PR_62": "Nunavut",
}
PROVINCE_IDS = set(PROVINCE_LABELS)
TEN_PROVINCE_IDS = PROVINCE_IDS - {"PR_60", "PR_61", "PR_62"}
LEGACY_PROVINCE_DGUID_TO_GEOGRAPHY_ID = {
    dguid.replace("2021A", "2016A"): geography_id
    for dguid, geography_id in PROVINCE_DGUID_TO_GEOGRAPHY_ID.items()
}

SOURCE_URLS = {
    CPI_SOURCE_ID: "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810000401",
    POPULATION_SOURCE_ID: "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000901",
    EARNINGS_SOURCE_ID: "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410022301",
    HOUSING_SOURCE_ID: "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410015601",
    INVESTMENT_SOURCE_ID: "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410029301",
}

METRIC_LABELS = {
    "MACRO_CPI_ALL_ITEMS_QAVG": "All-items CPI quarterly average",
    "MACRO_CPI_SHELTER_QAVG": "Shelter CPI quarterly average",
    "MACRO_POPULATION_QUARTERLY": "Quarterly population estimate",
    "MACRO_WEEKLY_EARNINGS_ALL_INDUSTRIES_QAVG": (
        "Average weekly earnings, all industries, quarterly average"
    ),
    "MACRO_WEEKLY_EARNINGS_CONSTRUCTION_QAVG": (
        "Average weekly earnings, construction, quarterly average"
    ),
    "MACRO_HOUSING_STARTS_SAAR_QAVG": (
        "Housing starts, seasonally adjusted annual rate, quarterly average"
    ),
    "MACRO_NON_RESIDENTIAL_BUILDING_INVESTMENT_QSUM": (
        "Non-residential building investment, current dollars, quarterly sum"
    ),
}

EXPECTED_GEOGRAPHIES = {
    "MACRO_CPI_ALL_ITEMS_QAVG": TEN_PROVINCE_IDS,
    "MACRO_CPI_SHELTER_QAVG": TEN_PROVINCE_IDS,
    "MACRO_POPULATION_QUARTERLY": PROVINCE_IDS,
    "MACRO_WEEKLY_EARNINGS_ALL_INDUSTRIES_QAVG": PROVINCE_IDS,
    "MACRO_WEEKLY_EARNINGS_CONSTRUCTION_QAVG": PROVINCE_IDS,
    "MACRO_HOUSING_STARTS_SAAR_QAVG": TEN_PROVINCE_IDS,
    "MACRO_NON_RESIDENTIAL_BUILDING_INVESTMENT_QSUM": PROVINCE_IDS,
}


@dataclass(frozen=True)
class MonthlyValue:
    metric_id: str
    geography_id: str
    geography_label: str
    statcan_dguid: str
    period: str
    value: float | None
    source_id: str
    source_status: str
    unit: str


def build_regional_macro_controls(
    cpi_zip_path: Path,
    population_zip_path: Path,
    earnings_zip_path: Path,
    housing_zip_path: Path,
    investment_csv_path: Path,
    investment_report_path: Path,
    output_csv_path: Path,
    output_json_path: Path,
) -> dict[str, object]:
    input_paths = {
        CPI_SOURCE_ID: cpi_zip_path,
        POPULATION_SOURCE_ID: population_zip_path,
        EARNINGS_SOURCE_ID: earnings_zip_path,
        HOUSING_SOURCE_ID: housing_zip_path,
        INVESTMENT_SOURCE_ID: investment_csv_path,
    }
    _validate_retrieval_manifests(input_paths)
    _validate_investment_report(investment_csv_path, investment_report_path)

    rows: list[dict[str, str]] = []
    rows.extend(_aggregate_monthly(_read_cpi(cpi_zip_path)))
    rows.extend(_read_population(population_zip_path))
    rows.extend(_aggregate_monthly(_read_earnings(earnings_zip_path)))
    rows.extend(_aggregate_monthly(_read_housing(housing_zip_path)))
    rows.extend(_read_investment(investment_csv_path))

    common_latest_period_end = _common_latest_period_end(rows)
    rows = [
        row
        for row in rows
        if row["period_end"] <= common_latest_period_end
        and _quarter_key(row["period_end"]) >= PANEL_START_QUARTER
    ]
    _validate_panel_scope(rows, common_latest_period_end)
    _attach_year_over_year_changes(rows)
    rows.sort(
        key=lambda row: (
            row["geography_id"], row["indicator_id"], row["period_end"]
        )
    )
    _write_rows(output_csv_path, rows)

    report = _build_report(
        input_paths,
        investment_report_path,
        output_csv_path,
        rows,
        common_latest_period_end,
    )
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def _read_cpi(zip_path: Path) -> list[MonthlyValue]:
    selected_products = {
        "All-items": "MACRO_CPI_ALL_ITEMS_QAVG",
        "Shelter": "MACRO_CPI_SHELTER_QAVG",
    }
    rows: list[MonthlyValue] = []
    for raw in _read_zip_csv(
        zip_path,
        "18100004.csv",
        {
            "REF_DATE",
            "GEO",
            "DGUID",
            "Products and product groups",
            "UOM",
            "VALUE",
            "STATUS",
            "SYMBOL",
        },
    ):
        metric_id = selected_products.get(raw["Products and product groups"])
        geography_id = LEGACY_PROVINCE_DGUID_TO_GEOGRAPHY_ID.get(raw["DGUID"])
        if metric_id is None or geography_id not in TEN_PROVINCE_IDS:
            continue
        if raw["UOM"] != "2002=100":
            raise ValidationError("selected CPI source unit changed")
        rows.append(
            _monthly_value(
                raw,
                metric_id=metric_id,
                geography_id=geography_id,
                source_id=CPI_SOURCE_ID,
                unit="Index, 2002=100",
            )
        )
    _validate_monthly_selection(rows, selected_products.values(), TEN_PROVINCE_IDS)
    return rows


def _read_earnings(zip_path: Path) -> list[MonthlyValue]:
    selected_industries = {
        "Industrial aggregate excluding unclassified businesses [11-91N]": (
            "MACRO_WEEKLY_EARNINGS_ALL_INDUSTRIES_QAVG"
        ),
        "Construction [23]": "MACRO_WEEKLY_EARNINGS_CONSTRUCTION_QAVG",
    }
    selected_estimate = "Average weekly earnings including overtime for all employees"
    rows: list[MonthlyValue] = []
    for raw in _read_zip_csv(
        zip_path,
        "14100223.csv",
        {
            "REF_DATE",
            "GEO",
            "DGUID",
            "Estimate",
            "North American Industry Classification System (NAICS)",
            "UOM",
            "VALUE",
            "STATUS",
            "SYMBOL",
        },
    ):
        if raw["Estimate"] != selected_estimate:
            continue
        metric_id = selected_industries.get(
            raw["North American Industry Classification System (NAICS)"]
        )
        geography_id = PROVINCE_DGUID_TO_GEOGRAPHY_ID.get(raw["DGUID"])
        if metric_id is None or geography_id not in PROVINCE_IDS:
            continue
        if raw["UOM"] != "Dollars":
            raise ValidationError("selected SEPH weekly-earnings unit changed")
        rows.append(
            _monthly_value(
                raw,
                metric_id=metric_id,
                geography_id=geography_id,
                source_id=EARNINGS_SOURCE_ID,
                unit="Dollars per week",
            )
        )
    _validate_monthly_selection(rows, selected_industries.values(), PROVINCE_IDS)
    return rows


def _read_housing(zip_path: Path) -> list[MonthlyValue]:
    metric_id = "MACRO_HOUSING_STARTS_SAAR_QAVG"
    rows: list[MonthlyValue] = []
    for raw in _read_zip_csv(
        zip_path,
        "34100156.csv",
        {
            "REF_DATE",
            "GEO",
            "DGUID",
            "Type of unit",
            "UOM",
            "SCALAR_FACTOR",
            "VALUE",
            "STATUS",
            "SYMBOL",
        },
    ):
        geography_id = LEGACY_PROVINCE_DGUID_TO_GEOGRAPHY_ID.get(raw["DGUID"])
        if raw["Type of unit"] != "Total units" or geography_id not in TEN_PROVINCE_IDS:
            continue
        if raw["UOM"] != "Units" or raw["SCALAR_FACTOR"] != "thousands":
            raise ValidationError("selected CMHC housing-starts unit changed")
        item = _monthly_value(
            raw,
            metric_id=metric_id,
            geography_id=geography_id,
            source_id=HOUSING_SOURCE_ID,
            unit="Units, seasonally adjusted annual rate",
        )
        rows.append(
            MonthlyValue(
                **{
                    **item.__dict__,
                    "value": None if item.value is None else item.value * 1000.0,
                }
            )
        )
    _validate_monthly_selection(rows, {metric_id}, TEN_PROVINCE_IDS)
    return rows


def _read_population(zip_path: Path) -> list[dict[str, str]]:
    metric_id = "MACRO_POPULATION_QUARTERLY"
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw in _read_zip_csv(
        zip_path,
        "17100009.csv",
        {"REF_DATE", "GEO", "DGUID", "UOM", "VALUE", "STATUS", "SYMBOL"},
    ):
        geography_id = PROVINCE_DGUID_TO_GEOGRAPHY_ID.get(raw["DGUID"])
        if geography_id not in PROVINCE_IDS:
            continue
        if raw["UOM"] != "Persons":
            raise ValidationError("selected population-estimate unit changed")
        quarter = _month_to_quarter(raw["REF_DATE"])
        if quarter < PANEL_START_QUARTER:
            continue
        key = (geography_id, quarter)
        if key in seen:
            raise ValidationError(f"duplicate population control cell: {key}")
        seen.add(key)
        value_text = raw["VALUE"].strip()
        value = None if not value_text else float(value_text)
        period_start, period_end = quarter_boundaries(quarter)
        rows.append(
            _output_row(
                metric_id=metric_id,
                geography_id=geography_id,
                geography_label=raw["GEO"],
                statcan_dguid=raw["DGUID"],
                period_start=period_start,
                period_end=period_end,
                value=value,
                unit="Persons",
                source_id=POPULATION_SOURCE_ID,
                evidence_status="observed",
                aggregation_method="published_quarterly_point_estimate",
                source_observation_count=1,
                source_statuses=_statuses(raw),
            )
        )
    _validate_quarterly_geographies(rows, metric_id, PROVINCE_IDS)
    return rows


def _read_investment(csv_path: Path) -> list[dict[str, str]]:
    selected_indicator = "IBC_TOTAL_NON_RESIDENTIAL_SEASONALLY_ADJUSTED_CURRENT"
    metric_id = "MACRO_NON_RESIDENTIAL_BUILDING_INVESTMENT_QSUM"
    rows: list[dict[str, str]] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "indicator_id",
            "geography_label",
            "statcan_dguid",
            "value",
            "unit",
            "geography_id",
            "period_start",
            "period_end",
            "source_id",
            "source_month_count",
            "quality_flags",
        }
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValidationError("building-investment control schema changed")
        for raw in reader:
            if (
                raw["indicator_id"] != selected_indicator
                or raw["geography_id"] not in PROVINCE_IDS
            ):
                continue
            if raw["source_id"] != INVESTMENT_SOURCE_ID:
                raise ValidationError("building-investment source ID changed")
            rows.append(
                _output_row(
                    metric_id=metric_id,
                    geography_id=raw["geography_id"],
                    geography_label=raw["geography_label"],
                    statcan_dguid=raw["statcan_dguid"],
                    period_start=raw["period_start"],
                    period_end=raw["period_end"],
                    value=None if not raw["value"] else float(raw["value"]),
                    unit="Dollars per quarter",
                    source_id=INVESTMENT_SOURCE_ID,
                    evidence_status="inferred",
                    aggregation_method="sum_of_three_monthly_current_dollar_values",
                    source_observation_count=int(raw["source_month_count"]),
                    source_statuses=raw["quality_flags"].split("|")
                    if raw["quality_flags"]
                    else [],
                )
            )
    _validate_quarterly_geographies(rows, metric_id, PROVINCE_IDS)
    return rows


def _aggregate_monthly(values: list[MonthlyValue]) -> list[dict[str, str]]:
    latest_complete_quarter = _latest_complete_quarter(item.period for item in values)
    grouped: dict[tuple[str, str, str], list[MonthlyValue]] = defaultdict(list)
    for item in values:
        quarter = _month_to_quarter(item.period)
        if quarter < PANEL_START_QUARTER or quarter > latest_complete_quarter:
            continue
        grouped[(item.metric_id, item.geography_id, quarter)].append(item)

    rows: list[dict[str, str]] = []
    for (metric_id, geography_id, quarter), observations in sorted(grouped.items()):
        periods = sorted(item.period for item in observations)
        if len(observations) != 3 or periods != _quarter_months(quarter):
            raise ValidationError(
                f"incomplete regional macro quarter for {metric_id} "
                f"{geography_id} {quarter}: {periods}"
            )
        missing = [item for item in observations if item.value is None]
        value = (
            None
            if missing
            else sum(item.value or 0.0 for item in observations) / len(observations)
        )
        first = observations[0]
        period_start, period_end = quarter_boundaries(quarter)
        statuses = sorted(
            {status for item in observations for status in [item.source_status] if status}
        )
        if missing:
            statuses.append("quarterly_value_missing_due_to_monthly_missingness")
        rows.append(
            _output_row(
                metric_id=metric_id,
                geography_id=geography_id,
                geography_label=first.geography_label,
                statcan_dguid=first.statcan_dguid,
                period_start=period_start,
                period_end=period_end,
                value=value,
                unit=first.unit,
                source_id=first.source_id,
                evidence_status="inferred",
                aggregation_method="arithmetic_mean_of_three_monthly_values",
                source_observation_count=3,
                source_statuses=statuses,
            )
        )
    return rows


def _monthly_value(
    raw: dict[str, str],
    *,
    metric_id: str,
    geography_id: str,
    source_id: str,
    unit: str,
) -> MonthlyValue:
    value_text = raw["VALUE"].strip()
    return MonthlyValue(
        metric_id=metric_id,
        geography_id=geography_id,
        geography_label=raw["GEO"].replace("\xa0", " ").strip(),
        statcan_dguid=raw["DGUID"].strip(),
        period=raw["REF_DATE"].strip(),
        value=None if not value_text else float(value_text),
        source_id=source_id,
        source_status="|".join(_statuses(raw)),
        unit=unit,
    )


def _output_row(
    *,
    metric_id: str,
    geography_id: str,
    geography_label: str,
    statcan_dguid: str,
    period_start: str,
    period_end: str,
    value: float | None,
    unit: str,
    source_id: str,
    evidence_status: str,
    aggregation_method: str,
    source_observation_count: int,
    source_statuses: Iterable[str],
) -> dict[str, str]:
    token = "|".join((metric_id, geography_id, period_end))
    return {
        "observation_id": "MACRO_"
        + hashlib.sha256(token.encode("utf-8")).hexdigest()[:20].upper(),
        "indicator_id": metric_id,
        "indicator_label": METRIC_LABELS[metric_id],
        "geography_id": geography_id,
        "geography_label": geography_label,
        "statcan_dguid": statcan_dguid,
        "period_start": period_start,
        "period_end": period_end,
        "value": "" if value is None else _format_value(metric_id, value),
        "unit": unit,
        "year_over_year_change_percent": "",
        "source_id": source_id,
        "source_url": SOURCE_URLS[source_id],
        "source_evidence_status": "observed",
        "evidence_status": evidence_status,
        "transformation_id": TRANSFORMATION_ID,
        "aggregation_method": aggregation_method,
        "source_observation_count": str(source_observation_count),
        "quality_flags": "|".join(
            sorted({item for item in source_statuses if item})
        ),
    }


def _attach_year_over_year_changes(rows: list[dict[str, str]]) -> None:
    by_series: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        by_series[(row["indicator_id"], row["geography_id"])][
            row["period_end"]
        ] = row
    for series in by_series.values():
        for period_end, row in series.items():
            prior_period_end = _shift_year(period_end, -1)
            prior = series.get(prior_period_end)
            if not row["value"] or prior is None or not prior["value"]:
                continue
            current_value = float(row["value"])
            prior_value = float(prior["value"])
            if prior_value == 0:
                row["quality_flags"] = _append_flag(
                    row["quality_flags"], "year_over_year_denominator_zero"
                )
                continue
            row["year_over_year_change_percent"] = format(
                (current_value / prior_value - 1.0) * 100.0, ".6f"
            )


def _build_report(
    input_paths: dict[str, Path],
    investment_report_path: Path,
    output_csv_path: Path,
    rows: list[dict[str, str]],
    common_latest_period_end: str,
) -> dict[str, object]:
    metric_coverage: dict[str, object] = {}
    for metric_id, expected_geographies in sorted(EXPECTED_GEOGRAPHIES.items()):
        selected = [row for row in rows if row["indicator_id"] == metric_id]
        actual_geographies = {row["geography_id"] for row in selected}
        metric_coverage[metric_id] = {
            "label": METRIC_LABELS[metric_id],
            "series_count": len(actual_geographies),
            "expected_series_count": len(expected_geographies),
            "available_geography_ids": sorted(actual_geographies),
            "unavailable_geography_ids": sorted(PROVINCE_IDS - actual_geographies),
            "observation_count": len(selected),
            "missing_value_count": sum(not row["value"] for row in selected),
            "first_period_end": min(row["period_end"] for row in selected),
            "latest_period_end": max(row["period_end"] for row in selected),
            "source_id": selected[0]["source_id"],
            "source_url": selected[0]["source_url"],
        }

    latest_controls = [
        {
            "geography_id": row["geography_id"],
            "geography_label": row["geography_label"],
            "indicator_id": row["indicator_id"],
            "indicator_label": row["indicator_label"],
            "value": None if not row["value"] else float(row["value"]),
            "unit": row["unit"],
            "year_over_year_change_percent": (
                None
                if not row["year_over_year_change_percent"]
                else float(row["year_over_year_change_percent"])
            ),
            "period_end": row["period_end"],
            "source_id": row["source_id"],
            "source_url": row["source_url"],
            "evidence_status": row["evidence_status"],
        }
        for row in rows
        if row["period_end"] == common_latest_period_end
    ]
    latest_controls.sort(
        key=lambda item: (item["geography_id"], item["indicator_id"])
    )
    latest_alberta = [
        item for item in latest_controls if item["geography_id"] == "PR_48"
    ]
    latest_alberta.sort(key=lambda item: item["indicator_id"])

    input_manifest = []
    for source_id, path in sorted(input_paths.items()):
        item = {
            "source_id": source_id,
            "sha256": _sha256_path(path),
        }
        retrieval_manifest = path.with_suffix(path.suffix + ".manifest.json")
        if retrieval_manifest.exists():
            item["retrieval_manifest_sha256"] = _sha256_path(retrieval_manifest)
        if source_id == INVESTMENT_SOURCE_ID:
            item["control_report_sha256"] = _sha256_path(investment_report_path)
        input_manifest.append(item)

    return {
        "schema_version": "0.1.0",
        "model_id": MODEL_ID,
        "transformation_id": TRANSFORMATION_ID,
        "as_of_date": common_latest_period_end,
        "panel_start_quarter": PANEL_START_QUARTER,
        "panel_start_period_end": min(row["period_end"] for row in rows),
        "common_latest_period_end": common_latest_period_end,
        "input_manifest": input_manifest,
        "code_sha256": _sha256_path(Path(__file__)),
        "output_sha256": _sha256_path(output_csv_path),
        "source_ids": sorted(input_paths),
        "observation_count": len(rows),
        "series_count": len(
            {(row["indicator_id"], row["geography_id"]) for row in rows}
        ),
        "metric_count": len(METRIC_LABELS),
        "province_and_territory_count": len(
            {row["geography_id"] for row in rows}
        ),
        "quarter_count": len({row["period_end"] for row in rows}),
        "missing_value_count": sum(not row["value"] for row in rows),
        "year_over_year_change_count": sum(
            bool(row["year_over_year_change_percent"]) for row in rows
        ),
        "metric_coverage": metric_coverage,
        "latest_controls": latest_controls,
        "latest_alberta_controls": latest_alberta,
        "limitations": [
            "The panel contains regional controls and descriptive context; it does not identify an AI-attributable macroeconomic effect.",
            "CPI measures household consumption prices and is separate from BCPI construction bid prices.",
            "Average weekly earnings are payroll earnings, not occupation-specific offered wages, labour availability or wage causation.",
            "Housing starts are seasonally adjusted annual-rate activity and do not measure housing affordability or worker accommodation capacity.",
            "Population is a demand and denominator control; it does not measure construction capacity.",
            "Non-residential building investment excludes engineering construction and is not a public-project outcome.",
            "CPI and housing-start series cover the ten provinces; territorial values are not filled from capital-city or national proxies.",
            "Quarterly averages and year-over-year changes are deterministic transformations of observed source values, not forecasts.",
        ],
        "publication_boundary": {
            "status": "descriptive_control_panel_only",
            "regional_macro_context_authorized": True,
            "composite_macro_pressure_score_authorized": False,
            "scenario_calibration_authorized": False,
            "public_project_cost_translation_authorized": False,
            "ai_attributable_effect_authorized": False,
            "reason": (
                "The sources can describe dated regional macro conditions and support future "
                "control design. They do not isolate AI infrastructure demand, authorize a "
                "composite score or translate macro movement into project cost or delay."
            ),
        },
    }


def _validate_panel_scope(rows: list[dict[str, str]], common_latest: str) -> None:
    if not rows:
        raise ValidationError("regional macro panel is empty")
    if {row["indicator_id"] for row in rows} != set(METRIC_LABELS):
        raise ValidationError("regional macro metric coverage changed")
    if {row["geography_id"] for row in rows} != PROVINCE_IDS:
        raise ValidationError("regional macro panel must retain all 13 jurisdictions")
    keys = {
        (row["indicator_id"], row["geography_id"], row["period_end"])
        for row in rows
    }
    if len(keys) != len(rows):
        raise ValidationError("regional macro panel contains duplicate cells")
    for metric_id, expected_geographies in EXPECTED_GEOGRAPHIES.items():
        latest = {
            row["geography_id"]
            for row in rows
            if row["indicator_id"] == metric_id
            and row["period_end"] == common_latest
        }
        if latest != expected_geographies:
            raise ValidationError(
                f"regional macro latest-quarter coverage changed for {metric_id}: "
                f"missing={sorted(expected_geographies - latest)}, "
                f"unexpected={sorted(latest - expected_geographies)}"
            )


def _common_latest_period_end(rows: list[dict[str, str]]) -> str:
    latest_by_metric = {
        metric_id: max(
            row["period_end"] for row in rows if row["indicator_id"] == metric_id
        )
        for metric_id in METRIC_LABELS
    }
    return min(latest_by_metric.values())


def _validate_monthly_selection(
    rows: list[MonthlyValue], metric_ids: Iterable[str], geography_ids: set[str]
) -> None:
    if not rows:
        raise ValidationError("regional macro monthly selection is empty")
    latest_period = max(item.period for item in rows)
    for metric_id in metric_ids:
        actual = {
            item.geography_id
            for item in rows
            if item.metric_id == metric_id and item.period == latest_period
        }
        if actual != geography_ids:
            raise ValidationError(
                f"regional macro monthly geography coverage changed for {metric_id}: "
                f"missing={sorted(geography_ids - actual)}, "
                f"unexpected={sorted(actual - geography_ids)}"
            )
    keys = {(item.metric_id, item.geography_id, item.period) for item in rows}
    if len(keys) != len(rows):
        raise ValidationError("regional macro monthly selection contains duplicate cells")


def _validate_quarterly_geographies(
    rows: list[dict[str, str]], metric_id: str, expected: set[str]
) -> None:
    if not rows:
        raise ValidationError(f"regional macro quarterly selection is empty: {metric_id}")
    latest = max(row["period_end"] for row in rows)
    actual = {
        row["geography_id"] for row in rows if row["period_end"] == latest
    }
    if actual != expected:
        raise ValidationError(
            f"regional macro quarterly geography coverage changed for {metric_id}: "
            f"missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}"
        )


def _validate_retrieval_manifests(input_paths: dict[str, Path]) -> None:
    for source_id, path in input_paths.items():
        if source_id == INVESTMENT_SOURCE_ID:
            continue
        manifest_path = path.with_suffix(path.suffix + ".manifest.json")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(
                f"regional macro retrieval manifest is unavailable for {source_id}"
            ) from exc
        if manifest.get("source_id") != source_id:
            raise ValidationError(f"regional macro retrieval source mismatch: {source_id}")
        if manifest.get("content_hash") != _sha256_path(path):
            raise ValidationError(f"regional macro retrieval hash mismatch: {source_id}")


def _validate_investment_report(csv_path: Path, report_path: Path) -> None:
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError("building-investment control report is unavailable") from exc
    if report.get("output_sha256") != _sha256_path(csv_path):
        raise ValidationError("building-investment control report hash is stale")
    boundary = report.get("publication_boundary", {})
    if boundary.get("ai_attributable_effect_authorized") is not False:
        raise ValidationError("building-investment control boundary is unsafe")


def _read_zip_csv(
    zip_path: Path, expected_member: str, required_fields: set[str]
) -> Iterable[dict[str, str]]:
    with zipfile.ZipFile(zip_path) as archive:
        csv_names = [
            name
            for name in archive.namelist()
            if name.endswith(".csv") and "MetaData" not in name
        ]
        if csv_names != [expected_member]:
            raise ValidationError(
                f"unexpected Statistics Canada archive members: {csv_names}"
            )
        with archive.open(expected_member) as raw_handle:
            text_handle = io.TextIOWrapper(
                raw_handle, encoding="utf-8-sig", newline=""
            )
            reader = csv.DictReader(text_handle)
            if not reader.fieldnames or not required_fields.issubset(
                reader.fieldnames
            ):
                raise ValidationError(
                    f"Statistics Canada macro source schema changed: {expected_member}"
                )
            yield from reader


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def _latest_complete_quarter(periods: Iterable[str]) -> str:
    latest_period = max(periods)
    year_text, month_text = latest_period.split("-")
    month = int(month_text)
    quarter = (month - 1) // 3 + 1
    if month not in {3, 6, 9, 12}:
        quarter -= 1
        if quarter == 0:
            quarter = 4
            year_text = str(int(year_text) - 1)
    return f"{year_text}-Q{quarter}"


def _month_to_quarter(period: str) -> str:
    try:
        year_text, month_text = period.split("-")
        month = int(month_text)
        year = int(year_text)
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"invalid regional macro period: {period}") from exc
    if month not in range(1, 13):
        raise ValidationError(f"invalid regional macro period: {period}")
    return f"{year}-Q{(month - 1) // 3 + 1}"


def _quarter_months(quarter: str) -> list[str]:
    year_text, quarter_text = quarter.split("-Q")
    start_month = (int(quarter_text) - 1) * 3 + 1
    return [f"{year_text}-{month:02d}" for month in range(start_month, start_month + 3)]


def _quarter_key(period_end: str) -> str:
    value = date.fromisoformat(period_end)
    return f"{value.year}-Q{(value.month - 1) // 3 + 1}"


def _shift_year(period_end: str, years: int) -> str:
    value = date.fromisoformat(period_end)
    return value.replace(year=value.year + years).isoformat()


def _statuses(raw: dict[str, str]) -> list[str]:
    return [
        item
        for item in (
            f"source_status:{raw.get('STATUS', '').strip()}"
            if raw.get("STATUS", "").strip()
            else "source_status:blank",
            f"source_symbol:{raw.get('SYMBOL', '').strip()}"
            if raw.get("SYMBOL", "").strip()
            else "",
        )
        if item
    ]


def _append_flag(flags: str, value: str) -> str:
    return "|".join(sorted({item for item in (*flags.split("|"), value) if item}))


def _format_value(metric_id: str, value: float) -> str:
    if metric_id == "MACRO_POPULATION_QUARTERLY":
        return format(value, ".0f")
    if metric_id == "MACRO_NON_RESIDENTIAL_BUILDING_INVESTMENT_QSUM":
        return format(value, ".2f")
    return format(value, ".6f")


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"
