from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from .adapters.statcan import (
    PROVINCE_DGUID_TO_GEOGRAPHY_ID,
    TRADE_NOC_TO_NODE,
)
from .schemas import ValidationError


LABOUR_PRESSURE_MODEL_ID = "AIIO_LABOUR_RECRUITMENT_PRESSURE_0_1"


def run_labour_recruitment_pressure(
    vacancy_path: Path,
    workforce_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Build a cross-vintage recruitment-pressure diagnostic with explicit limits."""
    vacancy_rows = _latest_vacancy_rows(vacancy_path)
    workforce_rows = _workforce_rows(workforce_path)
    expected_keys = {
        (geography_id, noc_code)
        for geography_id in PROVINCE_DGUID_TO_GEOGRAPHY_ID.values()
        for noc_code in TRADE_NOC_TO_NODE
    }
    if set(vacancy_rows) != expected_keys:
        raise ValidationError("labour pressure vacancy input must contain exactly 78 cells")
    if set(workforce_rows) != expected_keys:
        raise ValidationError("labour pressure workforce input must contain exactly 78 cells")

    vacancy_period_end = max(item["period_end"] for item in vacancy_rows.values())
    workforce_period_end = max(item["period_end"] for item in workforce_rows.values())
    period_gap_days = (
        date.fromisoformat(vacancy_period_end) - date.fromisoformat(workforce_period_end)
    ).days
    if period_gap_days <= 0:
        raise ValidationError("workforce stock must predate the current vacancy observation")

    occupation_rows = []
    for geography_id, noc_code in sorted(expected_keys):
        vacancy = vacancy_rows[(geography_id, noc_code)]
        workforce = workforce_rows[(geography_id, noc_code)]
        vacancy_value = float(vacancy["value"]) if vacancy["value"] else None
        workforce_value = float(workforce["value"])
        ratio = None
        availability = "available"
        if vacancy_value is None and workforce_value <= 0:
            availability = "vacancy_not_published_and_workforce_denominator_zero"
        elif vacancy_value is None:
            availability = "vacancy_not_published"
        elif workforce_value <= 0:
            availability = "workforce_denominator_zero"
        else:
            ratio = round(vacancy_value / workforce_value * 1_000, 2)
        occupation_rows.append(
            {
                "geography_id": geography_id,
                "geography_label": vacancy["geography_label"],
                "noc_code": noc_code,
                "occupation_label": vacancy["occupation_label"],
                "trade_node_id": TRADE_NOC_TO_NODE[noc_code],
                "vacancies": vacancy_value,
                "vacancy_unit": vacancy["unit"],
                "vacancy_period_end": vacancy["period_end"],
                "workforce_stock": workforce_value,
                "workforce_unit": workforce["unit"],
                "workforce_period_start": workforce["period_start"],
                "workforce_period_end": workforce["period_end"],
                "vacancies_per_1_000_2021_employed": ratio,
                "availability": availability,
                "evidence_status": "inferred" if ratio is not None else "observed",
                "vacancy_quality_flags": _flags(vacancy["quality_flags"]),
                "workforce_quality_flags": _flags(workforce["quality_flags"]),
            }
        )

    trade_rows = []
    for geography_id in sorted(PROVINCE_DGUID_TO_GEOGRAPHY_ID.values()):
        geography_items = [
            item for item in occupation_rows if item["geography_id"] == geography_id
        ]
        for trade_node_id in sorted(set(TRADE_NOC_TO_NODE.values())):
            items = [
                item for item in geography_items if item["trade_node_id"] == trade_node_id
            ]
            complete = all(
                item["vacancies"] is not None and item["workforce_stock"] > 0
                for item in items
            )
            vacancies = sum(item["vacancies"] for item in items) if complete else None
            workforce = sum(item["workforce_stock"] for item in items) if complete else None
            ratio = (
                round(vacancies / workforce * 1_000, 2)
                if complete and workforce and vacancies is not None
                else None
            )
            trade_rows.append(
                {
                    "geography_id": geography_id,
                    "geography_label": items[0]["geography_label"],
                    "trade_node_id": trade_node_id,
                    "noc_codes": [item["noc_code"] for item in items],
                    "component_cells": len(items),
                    "complete_cells": sum(
                        item["vacancies"] is not None and item["workforce_stock"] > 0
                        for item in items
                    ),
                    "vacancies": vacancies,
                    "workforce_stock": workforce,
                    "vacancies_per_1_000_2021_employed": ratio,
                    "availability": "available" if complete else "incomplete_components",
                    "evidence_status": "inferred",
                }
            )

    rankings = []
    for geography_id in sorted(PROVINCE_DGUID_TO_GEOGRAPHY_ID.values()):
        rows = [item for item in trade_rows if item["geography_id"] == geography_id]
        ranked = sorted(
            (item for item in rows if item["vacancies_per_1_000_2021_employed"] is not None),
            key=lambda item: -item["vacancies_per_1_000_2021_employed"],
        )
        rankings.append(
            {
                "geography_id": geography_id,
                "geography_label": rows[0]["geography_label"],
                "ranked_trade_node_ids": [item["trade_node_id"] for item in ranked],
                "excluded_trade_node_ids": [
                    item["trade_node_id"]
                    for item in rows
                    if item["vacancies_per_1_000_2021_employed"] is None
                ],
            }
        )

    output = {
        "schema_version": "1.0.0",
        "model_id": LABOUR_PRESSURE_MODEL_ID,
        "metric_id": "JVWS_VACANCIES_PER_1000_CENSUS_2021_EMPLOYED",
        "metric_label": "Cross-vintage vacancies per 1,000 employed persons in the 2021 Census",
        "evidence_status": "inferred",
        "vacancy_source_id": "STATCAN_JVWS_14100444",
        "workforce_source_id": "STATCAN_CENSUS_OCCUPATION_98100449",
        "vacancy_period_end": vacancy_period_end,
        "workforce_period_start": "2021-05-02",
        "workforce_period_end": workforce_period_end,
        "period_gap_days": period_gap_days,
        "geography_scope": "13 provinces and territories; Canada totals excluded",
        "occupation_diagnostics": occupation_rows,
        "trade_diagnostics": trade_rows,
        "rankings": rankings,
        "interpretation": (
            "A screening diagnostic for recruitment pressure. It is not the Statistics Canada "
            "job vacancy rate, not a current workforce denominator and not a measure of spare capacity."
        ),
        "limitations": [
            "The numerator and denominator come from different surveys and reference periods.",
            "The 2021 Census reference week occurred during the COVID-19 pandemic's third wave.",
            "Census counts use the 25% long-form sample and random rounding.",
            "A trade-node ranking is published only when every component NOC has a published vacancy and a positive workforce denominator.",
            "The diagnostic does not calibrate graph-edge effect sizes or estimate project delay.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def _latest_vacancy_rows(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        all_rows = list(csv.DictReader(handle))
    period_end = max(item["period_end"] for item in all_rows)
    rows = [
        item
        for item in all_rows
        if item["period_end"] == period_end and item["statistic"] == "Job vacancies"
    ]
    result = {(item["geography_id"], item["noc_code"]): item for item in rows}
    if len(result) != len(rows):
        raise ValidationError("latest vacancy input contains duplicate geography/NOC cells")
    return result


def _workforce_rows(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = {(item["geography_id"], item["noc_code"]): item for item in rows}
    if len(result) != len(rows):
        raise ValidationError("workforce input contains duplicate geography/NOC cells")
    return result


def _flags(value: str) -> list[str]:
    return [flag for flag in value.split("|") if flag]
