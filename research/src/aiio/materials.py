from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .material_taxonomy import (
    ARCHETYPES,
    COMPONENT_SUFFIXES,
    material_indicator_targets,
)
from .schemas import ValidationError


def percent_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return round((current / previous - 1) * 100, 3)


def run_material_cost_screen(
    bcpi_path: Path,
    output_json_path: Path,
    output_csv_path: Path,
    *,
    model_id: str = "AIIO_AB_BCPI_MATERIAL_COST_SCREEN_0_1",
    include_geography_label: bool = False,
    expected_geography_ids: set[str] | None = None,
    additional_limitations: list[str] | None = None,
) -> dict[str, Any]:
    with bcpi_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValidationError("BCPI material-cost screen cannot use an empty input")

    targets = material_indicator_targets()
    geography_scope = sorted({item["geography_id"] for item in rows})
    if expected_geography_ids is not None and set(geography_scope) != expected_geography_ids:
        raise ValidationError(
            "BCPI material screen geography scope changed; expected "
            f"{sorted(expected_geography_ids)}, found {geography_scope}"
        )

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for item in rows:
        if item["indicator_id"] in targets:
            grouped[(item["geography_id"], item["indicator_id"])].append(item)

    expected = len(geography_scope) * len(targets)
    if len(grouped) != expected:
        raise ValidationError(
            f"BCPI material screen expected {expected} series across "
            f"{len(geography_scope)} geographies, found {len(grouped)}"
        )

    observations = []
    for (geography_id, indicator_id), items in sorted(grouped.items()):
        ordered = sorted(items, key=lambda item: item["period_end"])
        latest = ordered[-1]
        latest_date = date.fromisoformat(latest["period_end"])
        year_ago_date = latest_date.replace(year=latest_date.year - 1).isoformat()
        year_ago = next(
            (item for item in ordered if item["period_end"] == year_ago_date), None
        )
        previous_quarter_date = {
            3: date(latest_date.year - 1, 12, 31),
            6: date(latest_date.year, 3, 31),
            9: date(latest_date.year, 6, 30),
            12: date(latest_date.year, 9, 30),
        }.get(latest_date.month)
        if previous_quarter_date is None:
            raise ValidationError(
                f"BCPI period end is not a calendar quarter-end: {latest['period_end']}"
            )
        previous_quarter_period_end = previous_quarter_date.isoformat()
        prior_quarter = next(
            (
                item
                for item in ordered
                if item["period_end"] == previous_quarter_period_end
            ),
            None,
        )
        current_value = float(latest["value"]) if latest["value"] else None
        prior_value = (
            float(prior_quarter["value"])
            if prior_quarter and prior_quarter["value"]
            else None
        )
        year_ago_value = (
            float(year_ago["value"]) if year_ago and year_ago["value"] else None
        )
        archetype, component = targets[indicator_id]
        observation = {
            "geography_id": geography_id,
            "archetype": archetype,
            "component": component,
            "indicator_id": indicator_id,
            "period_end": latest["period_end"],
            "index_value": current_value,
            "unit": latest["unit"],
            "index_points_above_2023_annual_base": (
                round(current_value - 100, 3) if current_value is not None else None
            ),
            "previous_quarter_period_end": previous_quarter_period_end,
            "previous_quarter_index": prior_value,
            "quarter_over_quarter_percent_change": percent_change(
                current_value, prior_value
            ),
            "year_ago_period_end": year_ago_date,
            "year_ago_index": year_ago_value,
            "year_over_year_percent_change": percent_change(
                current_value, year_ago_value
            ),
            "source_id": latest["source_id"],
            "source_evidence_status": latest["evidence_status"],
            "change_evidence_status": "inferred",
            "quality_flags": [
                *[flag for flag in latest["quality_flags"].split("|") if flag],
                *([] if prior_quarter else ["previous_calendar_quarter_missing"]),
            ],
        }
        if include_geography_label:
            observation["geography_label"] = latest["geography_label"]
        observations.append(observation)

    period_end = max(item["period_end"] for item in observations)
    if {item["period_end"] for item in observations} != {period_end}:
        raise ValidationError("BCPI material screen latest periods do not align")

    result = {
        "model_id": model_id,
        "geography_scope": geography_scope,
        "period_end": period_end,
        "source_id": "STATCAN_BCPI_18100289",
        "evidence_status": "observed_with_inferred_changes",
        "observation_count": len(observations),
        "observations": observations,
        "limitations": [
            "The industrial factory series is a public BCPI archetype proxy, not a data-centre construction index.",
            "BCPI divisions measure contractor bid-price change for model buildings; they are not commodity spot prices, quantities, lead times or local production capacity.",
            "Index levels and changes do not identify AI-caused effects. They describe a shared construction-cost baseline only.",
            *(additional_limitations or [
                "Calgary and Edmonton are separate CMAs and are not substituted for all Alberta regions."
            ]),
        ],
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(observations[0].keys())
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in observations:
            writer.writerow({**item, "quality_flags": "|".join(item["quality_flags"])})
    return result


def run_provincial_material_cost_screen(
    bcpi_path: Path,
    output_json_path: Path,
    output_csv_path: Path,
) -> dict[str, Any]:
    return run_material_cost_screen(
        bcpi_path,
        output_json_path,
        output_csv_path,
        model_id="AIIO_CA_PROVINCIAL_BCPI_MATERIAL_COST_SCREEN_0_1",
        include_geography_label=True,
        additional_limitations=[
            "The source table currently publishes province-level BCPI rows for nine provinces; Prince Edward Island and the territories are absent and are not imputed.",
            "Province-level indexes and CMA-level indexes are distinct geography products and must not be substituted for one another.",
            "School is a child archetype within the broader Institutional buildings [62213] source category; those rows are related, not disjoint market totals.",
            "Index points above the 2023 annual base equal index minus 100; they are not a change from 2023-Q1.",
        ],
        expected_geography_ids={
            "PR_10", "PR_12", "PR_13", "PR_24", "PR_35",
            "PR_46", "PR_47", "PR_48", "PR_59",
        },
    )
