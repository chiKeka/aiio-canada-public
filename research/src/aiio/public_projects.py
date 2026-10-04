from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .schemas import ValidationError


ASSET_CLASS_TYPES: dict[str, set[str]] = {
    "health_facilities": {"Health Care", "Continuing Care"},
    "schools_and_postsecondary": {"School", "Post-Secondary"},
    "government_and_civic_facilities": {
        "Administration",
        "Arts and Culture",
        "Community Centre",
        "Court/Justice",
        "Emergency Services",
        "Library",
        "Military",
        "Research Centre",
    },
    "roads_transit_and_airports": {
        "Airport",
        "Pedestrian Bridge",
        "Roadwork",
        "Transit",
    },
    "municipal_water_and_resilience": {
        "Flood Mitigation/Reservoir",
        "Other Infrastructure",
        "Water/Wastewater",
    },
}

PUBLIC_SPONSOR_PREFIXES = (
    "alberta infrastructure",
    "alberta transportation and economic corridors",
    "city of ",
    "town of ",
    "village of ",
    "county of ",
    "municipal district",
    "regional municipality",
    "improvement district",
    "government of canada",
    "defence construction canada",
    "parks canada",
)
PUBLIC_INSTITUTION_TOKENS = (
    "university",
    "college",
    "institute of technology",
    "school board",
    "school division",
)
PUBLIC_UTILITY_PREFIXES = ("epcor", "enmax")


def classify_asset_class(project_type: str, sector: str) -> str | None:
    for asset_class, project_types in ASSET_CLASS_TYPES.items():
        if project_type in project_types:
            return asset_class
    if sector == "Power":
        return "power_sector_infrastructure"
    return None


def classify_sponsor_signal(developer: str) -> str:
    value = " ".join(developer.lower().split())
    if value.startswith(PUBLIC_SPONSOR_PREFIXES) or any(
        token in value for token in PUBLIC_INSTITUTION_TOKENS
    ):
        return "government_or_public_institution_signal"
    if value.startswith(PUBLIC_UTILITY_PREFIXES):
        return "municipal_or_public_utility_signal"
    return "unresolved"


def schedule_overlap(
    start_year: int | None,
    end_year: int | None,
    window_start: int,
    window_end: int,
) -> tuple[str, list[int]]:
    if start_year is not None and end_year is not None:
        years = list(range(max(start_year, window_start), min(end_year, window_end) + 1))
        return ("overlaps" if years else "outside_window"), years
    if end_year is not None and end_year < window_start:
        return "outside_window", []
    if start_year is not None and start_year > window_end:
        return "outside_window", []
    return "indeterminate_incomplete_schedule", []


def run_public_project_exposure(
    projects_path: Path,
    output_json_path: Path,
    output_csv_path: Path,
    *,
    window_start: int = 2027,
    window_end: int = 2036,
) -> dict[str, Any]:
    if window_start > window_end:
        raise ValidationError("public-project exposure window start cannot exceed end")
    with projects_path.open(encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    if not source_rows:
        raise ValidationError("Alberta project inventory cannot be empty")

    records: list[dict[str, Any]] = []
    for raw in source_rows:
        asset_class = classify_asset_class(raw["project_type"], raw["sector"])
        if asset_class is None or raw["ai_relevance"] != "none":
            continue
        start_year = int(raw["start_year"]) if raw["start_year"] else None
        end_year = int(raw["end_year"]) if raw["end_year"] else None
        cost = float(raw["estimated_cost_cad"]) if raw["estimated_cost_cad"] else None
        overlap_status, overlap_years = schedule_overlap(
            start_year, end_year, window_start, window_end
        )
        annualized_cost = None
        if cost is not None and start_year is not None and end_year is not None:
            if end_year < start_year:
                raise ValidationError(f"project {raw['project_id']} has an inverted schedule")
            annualized_cost = cost / (end_year - start_year + 1)
        records.append(
            {
                "project_id": raw["project_id"],
                "name": raw["name"],
                "asset_class": asset_class,
                "asset_class_evidence_status": "inferred",
                "project_type": raw["project_type"],
                "sector": raw["sector"],
                "developer": raw["developer"],
                "sponsor_signal": classify_sponsor_signal(raw["developer"]),
                "sponsor_signal_evidence_status": "inferred",
                "municipality": raw["municipality"],
                "stage": raw["stage"],
                "estimated_cost_cad": cost,
                "start_year": start_year,
                "end_year": end_year,
                "schedule_overlap_status": overlap_status,
                "overlap_years": overlap_years,
                "annualized_cost_cad_if_complete": annualized_cost,
                "indicative_cost_allocated_to_window_cad": (
                    annualized_cost * len(overlap_years)
                    if annualized_cost is not None
                    else None
                ),
                "longitude": float(raw["longitude"]) if raw["longitude"] else None,
                "latitude": float(raw["latitude"]) if raw["latitude"] else None,
                "location_precision": raw["location_precision"],
                "source_id": raw["source_id"],
                "source_evidence_status": raw["source_evidence_status"],
                "as_of_date": raw["as_of_date"],
            }
        )

    if not records:
        raise ValidationError("public-delivery asset screen produced no records")

    asset_classes = sorted({item["asset_class"] for item in records})
    summaries = []
    for asset_class in asset_classes:
        items = [item for item in records if item["asset_class"] == asset_class]
        known_cost = [item for item in items if item["estimated_cost_cad"] is not None]
        overlap = [item for item in items if item["schedule_overlap_status"] == "overlaps"]
        annualized = [
            item for item in overlap if item["annualized_cost_cad_if_complete"] is not None
        ]
        summaries.append(
            {
                "asset_class": asset_class,
                "project_count": len(items),
                "stage_counts": dict(sorted(Counter(item["stage"] for item in items).items())),
                "government_or_public_institution_signal_count": sum(
                    item["sponsor_signal"]
                    == "government_or_public_institution_signal"
                    for item in items
                ),
                "municipal_or_public_utility_signal_count": sum(
                    item["sponsor_signal"] == "municipal_or_public_utility_signal"
                    for item in items
                ),
                "unresolved_sponsor_signal_count": sum(
                    item["sponsor_signal"] == "unresolved" for item in items
                ),
                "reported_cost_project_count": len(known_cost),
                "reported_cost_cad": sum(item["estimated_cost_cad"] for item in known_cost),
                "complete_schedule_project_count": sum(
                    item["start_year"] is not None and item["end_year"] is not None
                    for item in items
                ),
                "overlap_project_count": len(overlap),
                "overlap_with_cost_and_complete_schedule_count": len(annualized),
                "indicative_cost_allocated_to_window_cad": sum(
                    item["indicative_cost_allocated_to_window_cad"]
                    for item in annualized
                ),
            }
        )

    annual = []
    for year in range(window_start, window_end + 1):
        for asset_class in asset_classes:
            items = [
                item
                for item in records
                if item["asset_class"] == asset_class and year in item["overlap_years"]
            ]
            cost_items = [
                item for item in items if item["annualized_cost_cad_if_complete"] is not None
            ]
            annual.append(
                {
                    "year": year,
                    "asset_class": asset_class,
                    "active_project_count_with_complete_schedule": len(items),
                    "annualized_cost_project_count": len(cost_items),
                    "indicative_annualized_cost_cad": sum(
                        item["annualized_cost_cad_if_complete"] for item in cost_items
                    ),
                }
            )

    result = {
        "model_id": "AIIO_AB_PUBLIC_PROJECT_EXPOSURE_0_1",
        "geography_id": "PR_48",
        "window": {"start_year": window_start, "end_year": window_end},
        "source_id": "ALBERTA_MAJOR_PROJECTS",
        "as_of_date": max(item["as_of_date"] for item in records),
        "evidence_status": "observed_with_inferred_classification_and_annualization",
        "source_inventory_project_count": len(source_rows),
        "excluded_ai_relevant_project_count": sum(
            raw["ai_relevance"] != "none" for raw in source_rows
        ),
        "exclusion_rule": "Exclude records classified by the upstream controlled AI-relevance taxonomy as core_data_centre or enabling_power so the scenario shock is not counted as an exposed public-delivery asset.",
        "screened_project_count": len(records),
        "asset_class_summaries": summaries,
        "annual_screen": annual,
        "projects": sorted(records, key=lambda item: (item["asset_class"], item["name"])),
        "limitations": [
            "Asset class and sponsor signals are controlled-vocabulary inferences; they are not legal ownership determinations.",
            "The Alberta Major Projects inventory has a publication threshold and is not a complete capital plan or procurement register.",
            "Reported costs are estimates, are not probability-weighted and may be missing. Missing costs remain null.",
            "Uniform annualization is a scheduling screen, not an expenditure forecast or a claim about construction curves.",
            "Overlap identifies simultaneous delivery windows; it does not prove competition, delay or cost causation.",
            "Core data-centre and classified enabling-power records are excluded by the declared AI-relevance rule; this screen is not an AI-project census.",
        ],
    }

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_fields = [
        "project_id",
        "name",
        "asset_class",
        "asset_class_evidence_status",
        "project_type",
        "sector",
        "developer",
        "sponsor_signal",
        "sponsor_signal_evidence_status",
        "municipality",
        "stage",
        "estimated_cost_cad",
        "start_year",
        "end_year",
        "schedule_overlap_status",
        "overlap_years",
        "annualized_cost_cad_if_complete",
        "indicative_cost_allocated_to_window_cad",
        "longitude",
        "latitude",
        "location_precision",
        "source_id",
        "source_evidence_status",
        "as_of_date",
    ]
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        for item in result["projects"]:
            writer.writerow(
                {
                    **item,
                    "overlap_years": "|".join(str(year) for year in item["overlap_years"]),
                }
            )
    return result
