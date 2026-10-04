from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .schemas import ValidationError


PANEL_ID = "AIIO_E2_EMPIRICAL_COVARIATE_PANEL_0_1"
REGIONS = {
    "CMA_825": ("Calgary CMA", "PR_48"),
    "CMA_835": ("Edmonton CMA", "PR_48"),
    "CMA_933": ("Vancouver CMA", "PR_59"),
    "CMA_535": ("Toronto CMA", "PR_35"),
    "CMA_462": ("Montréal CMA", "PR_24"),
}
ASSETS = {
    "health_facilities": "BCPI_INSTITUTIONAL_BUILDINGS_62213_DIVISION_COMPOSITE",
    "schools_and_postsecondary": "BCPI_SCHOOL_DIVISION_COMPOSITE",
    "government_and_civic_facilities": "BCPI_OFFICE_BUILDING_62212_DIVISION_COMPOSITE",
}
INVESTMENT_ID = "IBC_TOTAL_NON_RESIDENTIAL_SEASONALLY_ADJUSTED_CONSTANT"
MACRO_IDS = {
    "MACRO_CPI_ALL_ITEMS_QAVG": "cpi_all_items_index",
    "MACRO_CPI_SHELTER_QAVG": "cpi_shelter_index",
    "MACRO_POPULATION_QUARTERLY": "population",
    "MACRO_WEEKLY_EARNINGS_CONSTRUCTION_QAVG": "construction_weekly_earnings_cad",
    "MACRO_HOUSING_STARTS_SAAR_QAVG": "housing_starts_saar",
}
FIELDS = [
    "panel_row_id", "geography_id", "geography_label", "province_id", "quarter",
    "period_start", "period_end", "asset_class", "market_price_index",
    "market_price_qoq_percent", "market_price_yoy_percent",
    "non_residential_building_investment_constant_cad", "cpi_all_items_index",
    "cpi_shelter_index", "population", "construction_weekly_earnings_cad",
    "housing_starts_saar", "trade_job_vacancies", "trade_average_offered_wage_cad",
    "reconstructed_ai_construction_proxy_low_cad", "reconstructed_ai_construction_proxy_central_cad",
    "reconstructed_ai_construction_proxy_high_cad", "proxy_treatment_coverage_status",
    "realized_ai_construction_spend_cad", "data_centre_construction_labour_hours",
    "public_project_cost_change", "public_project_schedule_change_days",
    "authorizing_treatment_present", "authorizing_outcome_present", "estimation_eligible",
    "evidence_status", "quality_flags",
]


def build_empirical_covariate_panel(
    root: Path,
    attribution_contract_path: Path,
    acquisition_contract_path: Path,
    alberta_bcpi_path: Path,
    comparison_bcpi_path: Path,
    investment_path: Path,
    macro_path: Path,
    labour_path: Path,
    proxy_treatment_path: Path,
    output_csv_path: Path,
    output_json_path: Path,
) -> dict[str, Any]:
    attribution = _object(attribution_contract_path)
    acquisition = _object(acquisition_contract_path)
    _validate_contracts(attribution, acquisition)

    bcpi_rows = _csv(alberta_bcpi_path) + _csv(comparison_bcpi_path)
    bcpi = {
        (row["geography_id"], row["indicator_id"], row["period_end"]): _number(row["value"])
        for row in bcpi_rows
        if row["geography_id"] in REGIONS and row["indicator_id"] in set(ASSETS.values())
    }
    investment = {
        (row["geography_id"], row["period_end"]): _number(row["value"])
        for row in _csv(investment_path)
        if row["geography_id"] in REGIONS and row["indicator_id"] == INVESTMENT_ID
    }
    macro = {
        (row["geography_id"], row["indicator_id"], row["period_end"]): _number(row["value"])
        for row in _csv(macro_path)
        if row["geography_id"] in {province for _, province in REGIONS.values()}
        and row["indicator_id"] in MACRO_IDS
    }
    labour_groups: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in _csv(labour_path):
        if row["geography_id"] not in {province for _, province in REGIONS.values()} or not row["value"]:
            continue
        statistic = row["statistic"]
        if statistic in {"Job vacancies", "Average offered hourly wage"}:
            labour_groups[(row["geography_id"], row["period_end"])][statistic].append(float(row["value"]))
    proxy = {(row["geography_id"], row["period_end"]): row for row in _csv(proxy_treatment_path)}

    periods = sorted(
        set(period for geography, _, period in bcpi if geography in REGIONS)
        & set(period for geography, period in investment if geography in REGIONS)
    )
    labour_latest = max(period for _, period in labour_groups)
    macro_latest = min(max(period for province, indicator, period in macro if indicator == metric) for metric in MACRO_IDS for province in {p for _, p in REGIONS.values()})
    common_latest = min(max(periods), labour_latest, macro_latest)
    periods = [period for period in periods if "2017-" <= period <= common_latest]
    if len(periods) < attribution["design"]["minimum_pre_treatment_quarters"] + attribution["design"]["minimum_post_treatment_quarters"]:
        raise ValidationError("empirical covariate panel has insufficient quarterly history")

    rows: list[dict[str, str]] = []
    for geography_id, (geography_label, province_id) in REGIONS.items():
        for asset_class, indicator_id in ASSETS.items():
            history: list[float] = []
            for period_end in periods:
                key = (geography_id, indicator_id, period_end)
                if key not in bcpi or (geography_id, period_end) not in investment:
                    raise ValidationError(f"required panel cell is missing: {geography_id}/{asset_class}/{period_end}")
                value = bcpi[key]
                history.append(value)
                period_start = _quarter_start(period_end)
                labour = labour_groups.get((province_id, period_end), {})
                macro_values = {column: macro.get((province_id, metric, period_end)) for metric, column in MACRO_IDS.items()}
                missing = sorted(name for name, item in macro_values.items() if item is None)
                vacancies = labour.get("Job vacancies", [])
                wages = labour.get("Average offered hourly wage", [])
                proxy_row = proxy.get((geography_id, period_end))
                row = {
                    "panel_row_id": _row_id(geography_id, asset_class, period_end),
                    "geography_id": geography_id, "geography_label": geography_label, "province_id": province_id,
                    "quarter": _quarter(period_end), "period_start": period_start, "period_end": period_end, "asset_class": asset_class,
                    "market_price_index": _format(value),
                    "market_price_qoq_percent": _change(value, history[-2]) if len(history) >= 2 else "",
                    "market_price_yoy_percent": _change(value, history[-5]) if len(history) >= 5 else "",
                    "non_residential_building_investment_constant_cad": _format(investment[(geography_id, period_end)]),
                    **{name: _format(item) for name, item in macro_values.items()},
                    "trade_job_vacancies": _format(sum(vacancies)) if vacancies else "",
                    "trade_average_offered_wage_cad": _format(sum(wages) / len(wages)) if wages else "",
                    "reconstructed_ai_construction_proxy_low_cad": proxy_row["reconstructed_proxy_low_cad"] if proxy_row else "",
                    "reconstructed_ai_construction_proxy_central_cad": proxy_row["reconstructed_proxy_central_cad"] if proxy_row else "",
                    "reconstructed_ai_construction_proxy_high_cad": proxy_row["reconstructed_proxy_high_cad"] if proxy_row else "",
                    "proxy_treatment_coverage_status": "alberta_reconstruction_available" if proxy_row else "not_observed_outside_alberta",
                    "realized_ai_construction_spend_cad": "", "data_centre_construction_labour_hours": "",
                    "public_project_cost_change": "", "public_project_schedule_change_days": "",
                    "authorizing_treatment_present": "false", "authorizing_outcome_present": "false", "estimation_eligible": "false",
                    "evidence_status": "observed_covariates_with_non_authorizing_market_price_proxy",
                    "quality_flags": "|".join([*(f"missing:{name}" for name in missing), *( ["missing:trade_job_vacancies"] if not vacancies else []), *( ["missing:trade_average_offered_wage_cad"] if not wages else [])]),
                }
                rows.append(row)

    _validate_rows(rows, periods)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)

    inputs = [attribution_contract_path, acquisition_contract_path, alberta_bcpi_path, comparison_bcpi_path, investment_path, macro_path, labour_path, proxy_treatment_path]
    report = {
        "schema_version": "1.0.0", "panel_id": PANEL_ID,
        "unit_of_analysis": attribution["unit_of_analysis"], "frequency": "quarterly",
        "status": "covariate_panel_assembled_estimation_withheld",
        "row_count": len(rows), "region_count": len(REGIONS), "asset_class_count": len(ASSETS), "quarter_count": len(periods),
        "first_period_end": periods[0], "latest_period_end": periods[-1],
        "complete_market_price_cell_count": sum(bool(row["market_price_index"]) for row in rows),
        "complete_investment_control_cell_count": sum(bool(row["non_residential_building_investment_constant_cad"]) for row in rows),
        "field_completeness": {
            field: {"non_missing_count": sum(bool(row[field]) for row in rows), "row_count": len(rows)}
            for field in [*MACRO_IDS.values(), "trade_job_vacancies", "trade_average_offered_wage_cad"]
        },
        "authorizing_treatment_cell_count": 0, "authorizing_outcome_cell_count": 0, "estimation_eligible_row_count": 0,
        "proxy_treatment_cell_count": sum(bool(row["reconstructed_ai_construction_proxy_central_cad"]) for row in rows),
        "proxy_treatment_geography_count": len({row["geography_id"] for row in rows if row["reconstructed_ai_construction_proxy_central_cad"]}),
        "input_manifest": {str(path.relative_to(root)): "sha256:" + _sha(path) for path in inputs},
        "output_path": "data/processed/ai_attribution_empirical_covariate_panel_v0.1.csv", "output_sha256": "sha256:" + _sha(output_csv_path),
        "publication_boundary": {
            "descriptive_covariate_panel_authorized": True, "market_price_proxy_authorized": True,
            "treatment_authorized": False, "public_project_outcome_authorized": False,
            "effect_estimation_authorized": False, "ai_attributable_increment": None,
            "reason": "The panel assembles observed comparison-market covariates and price-index proxies, but contains no authorizing realized AI-construction dose or public-project outcome.",
        },
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _validate_contracts(attribution: dict[str, Any], acquisition: dict[str, Any]) -> None:
    if attribution.get("contract_id") != acquisition.get("attribution_contract_id"):
        raise ValidationError("empirical panel contracts do not reconcile")
    if set(REGIONS) != {row["geography_id"] for row in acquisition["candidate_regions"]}:
        raise ValidationError("empirical panel region scope drifted from acquisition contract")
    if set(ASSETS) != set(acquisition["target_asset_classes"]):
        raise ValidationError("empirical panel asset scope drifted from acquisition contract")


def _validate_rows(rows: list[dict[str, str]], periods: list[str]) -> None:
    expected = len(REGIONS) * len(ASSETS) * len(periods)
    if len(rows) != expected or len({row["panel_row_id"] for row in rows}) != expected:
        raise ValidationError("empirical panel row scope is incomplete or duplicated")
    prohibited = ("realized_ai_construction_spend_cad", "data_centre_construction_labour_hours", "public_project_cost_change", "public_project_schedule_change_days")
    if any(row[field] for row in rows for field in prohibited):
        raise ValidationError("non-authorizing panel populated a prohibited treatment or outcome field")
    if any(row["estimation_eligible"] != "false" for row in rows):
        raise ValidationError("non-authorizing panel cannot contain estimation-eligible rows")


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValidationError(f"empirical panel input is empty: {path}")
    return rows


def _object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict): raise ValidationError(f"expected JSON object: {path}")
    return payload


def _number(value: str) -> float:
    if value == "": raise ValidationError("required numeric panel input is missing")
    return float(value)


def _quarter_start(period_end: str) -> str:
    year, month, _ = period_end.split("-")
    return f"{year}-{int(month)-2:02d}-01"


def _quarter(period_end: str) -> str:
    year, month, _ = period_end.split("-")
    return f"{year}-Q{int(month)//3}"


def _change(current: float, previous: float) -> str:
    return _format((current / previous - 1) * 100) if previous else ""


def _format(value: float | None) -> str:
    if value is None: return ""
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _row_id(geography_id: str, asset_class: str, period_end: str) -> str:
    token = f"{geography_id}|{asset_class}|{period_end}".encode()
    return "E2P_" + hashlib.sha256(token).hexdigest()[:20].upper()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
