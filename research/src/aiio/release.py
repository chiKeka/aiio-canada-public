from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .adapters.statcan import (
    JVWS_STATISTICS,
    PROVINCE_DGUID_TO_GEOGRAPHY_ID,
    TRADE_NOC_TO_NODE,
)
from .schemas import ValidationError


def build_release(root: Path, version: str, created_at: str) -> dict[str, Any]:
    code_commit, dirty = git_state(root)
    if code_commit == "uncommitted" or dirty:
        raise ValidationError(
            "release builds require a clean committed source tree so the code revision is reproducible"
        )
    release_dir = root / "data" / "releases" / version
    public_dir = root / "public" / "data"
    release_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    inputs = release_input_paths(root)
    missing = [name for name, path in inputs.items() if not path.exists()]
    if missing:
        raise ValidationError(f"release inputs are missing: {', '.join(missing)}")

    baseline = build_baseline(
        inputs["alberta_ai_projects"],
        inputs["bcpi_alberta"],
        inputs["labour_availability_alberta"],
        inputs["labour_availability_canada"],
        inputs["labour_workforce_stock_canada"],
    )
    model_run = json.loads(inputs["model_run"].read_text(encoding="utf-8"))
    power_run = json.loads(inputs["power_run"].read_text(encoding="utf-8"))
    labour_pressure = json.loads(inputs["labour_pressure_run"].read_text(encoding="utf-8"))
    material_cost_screen = json.loads(
        inputs["material_cost_screen_run"].read_text(encoding="utf-8")
    )
    public_project_exposure = json.loads(
        inputs["public_project_exposure_run"].read_text(encoding="utf-8")
    )
    cost_baseline = json.loads(
        inputs["cost_baseline_run"].read_text(encoding="utf-8")
    )
    validate_cost_baseline_publication(cost_baseline)
    power_evidence = json.loads(
        inputs["power_evidence_run"].read_text(encoding="utf-8")
    )
    scenario = build_public_scenario(model_run)
    power_overlay = build_public_power_overlay(power_run)
    sources = build_public_sources(inputs["source_registry"])
    digest = build_public_digest(inputs["digest_items"])

    baseline_path = release_dir / "baseline.json"
    scenario_path = release_dir / "scenario.json"
    power_path = release_dir / "power_overlay.json"
    sources_path = release_dir / "sources.json"
    digest_path = release_dir / "digest.json"
    labour_pressure_path = release_dir / "labour_pressure.json"
    material_cost_screen_path = release_dir / "material_cost_screen.json"
    public_project_exposure_path = release_dir / "public_project_exposure.json"
    cost_baseline_path = release_dir / "cost_baseline.json"
    power_evidence_path = release_dir / "power_evidence.json"
    write_json(baseline_path, baseline)
    write_json(scenario_path, scenario)
    write_json(power_path, power_overlay)
    write_json(sources_path, sources)
    write_json(digest_path, digest)
    write_json(labour_pressure_path, labour_pressure)
    write_json(material_cost_screen_path, material_cost_screen)
    write_json(public_project_exposure_path, public_project_exposure)
    write_json(cost_baseline_path, cost_baseline)
    write_json(power_evidence_path, power_evidence)
    shutil.copyfile(inputs["alberta_ai_projects"], release_dir / "alberta_ai_projects.csv")
    shutil.copyfile(inputs["bcpi_alberta"], release_dir / "bcpi_alberta.csv")
    shutil.copyfile(
        inputs["labour_availability_alberta"],
        release_dir / "labour_availability_alberta.csv",
    )
    shutil.copyfile(
        inputs["labour_availability_canada"],
        release_dir / "labour_availability_canada.csv",
    )
    shutil.copyfile(
        inputs["labour_workforce_stock_canada"],
        release_dir / "labour_workforce_stock_canada.csv",
    )
    shutil.copyfile(
        inputs["material_cost_screen_csv"],
        release_dir / "bcpi_material_cost_screen_alberta.csv",
    )
    shutil.copyfile(
        inputs["public_project_exposure_csv"],
        release_dir / "public_project_exposure_alberta.csv",
    )
    shutil.copyfile(
        inputs["power_evidence_csv"],
        release_dir / "power_evidence_alberta.csv",
    )

    input_hashes = {name: sha256_file(path) for name, path in sorted(inputs.items())}
    input_manifest_hash = sha256_json(input_hashes)
    output_hashes = {
        "baseline.json": sha256_file(baseline_path),
        "scenario.json": sha256_file(scenario_path),
        "power_overlay.json": sha256_file(power_path),
        "sources.json": sha256_file(sources_path),
        "digest.json": sha256_file(digest_path),
        "labour_pressure.json": sha256_file(labour_pressure_path),
        "material_cost_screen.json": sha256_file(material_cost_screen_path),
        "public_project_exposure.json": sha256_file(public_project_exposure_path),
        "cost_baseline.json": sha256_file(cost_baseline_path),
        "power_evidence.json": sha256_file(power_evidence_path),
        "alberta_ai_projects.csv": sha256_file(release_dir / "alberta_ai_projects.csv"),
        "bcpi_alberta.csv": sha256_file(release_dir / "bcpi_alberta.csv"),
        "labour_availability_alberta.csv": sha256_file(
            release_dir / "labour_availability_alberta.csv"
        ),
        "labour_availability_canada.csv": sha256_file(
            release_dir / "labour_availability_canada.csv"
        ),
        "labour_workforce_stock_canada.csv": sha256_file(
            release_dir / "labour_workforce_stock_canada.csv"
        ),
        "bcpi_material_cost_screen_alberta.csv": sha256_file(
            release_dir / "bcpi_material_cost_screen_alberta.csv"
        ),
        "public_project_exposure_alberta.csv": sha256_file(
            release_dir / "public_project_exposure_alberta.csv"
        ),
        "power_evidence_alberta.csv": sha256_file(
            release_dir / "power_evidence_alberta.csv"
        ),
    }
    manifest = {
        "schema_version": "1.4.0",
        "release_id": f"AIIO_RELEASE_{version.upper().replace('.', '_').replace('-', '_')}",
        "version": version,
        "status": "research-prototype",
        "created_at": created_at,
        "code_commit": code_commit,
        "dirty_worktree": dirty,
        "model_version": model_run["model_id"],
        "engine_version": model_run["engine_version"],
        "parameter_set_id": model_run["parameter_set_id"],
        "power_overlay_version": power_run["overlay_id"],
        "cost_baseline_version": cost_baseline["model_id"],
        "input_manifest_hash": input_manifest_hash,
        "configuration_hash": sha256_json(
            {
                "graph": input_hashes["graph"],
                "scenario": input_hashes["scenario"],
                "power_definition": input_hashes["power_definition"],
            }
        ),
        "inputs": input_hashes,
        "outputs": output_hashes,
        "publication_note": "Research prototype. Reference-index projections publish only where held-out gates pass; the AI-attributable increment remains null and graph diagnostics are not findings or forecasts.",
    }
    manifest_path = release_dir / "manifest.json"
    write_json(manifest_path, manifest)

    latest = {
        "manifest": manifest,
        "baseline": baseline,
        "scenario": scenario,
        "power_overlay": power_overlay,
        "sources": sources,
        "digest": digest,
        "labour_pressure": labour_pressure,
        "material_cost_screen": material_cost_screen,
        "public_project_exposure": public_project_exposure,
        "cost_baseline": cost_baseline,
        "power_evidence": power_evidence,
    }
    latest_path = public_dir / "latest.json"
    write_json(latest_path, latest)
    shutil.copyfile(manifest_path, public_dir / "manifest.json")
    downloads_dir = root / "public" / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(release_dir / "alberta_ai_projects.csv", downloads_dir / "alberta_ai_projects.csv")
    shutil.copyfile(release_dir / "bcpi_alberta.csv", downloads_dir / "bcpi_alberta.csv")
    shutil.copyfile(
        release_dir / "labour_availability_alberta.csv",
        downloads_dir / "labour_availability_alberta.csv",
    )
    shutil.copyfile(
        release_dir / "labour_availability_canada.csv",
        downloads_dir / "labour_availability_canada.csv",
    )
    shutil.copyfile(
        release_dir / "labour_workforce_stock_canada.csv",
        downloads_dir / "labour_workforce_stock_canada.csv",
    )
    shutil.copyfile(
        release_dir / "bcpi_material_cost_screen_alberta.csv",
        downloads_dir / "bcpi_material_cost_screen_alberta.csv",
    )
    shutil.copyfile(
        release_dir / "public_project_exposure_alberta.csv",
        downloads_dir / "public_project_exposure_alberta.csv",
    )
    shutil.copyfile(
        release_dir / "power_evidence_alberta.csv",
        downloads_dir / "power_evidence_alberta.csv",
    )
    shutil.copyfile(
        cost_baseline_path,
        downloads_dir / "alberta_bcpi_reference_baseline.json",
    )
    return manifest


def build_baseline(
    projects_path: Path,
    bcpi_path: Path,
    labour_path: Path,
    labour_canada_path: Path,
    workforce_canada_path: Path,
) -> dict[str, Any]:
    with projects_path.open(encoding="utf-8") as handle:
        projects = list(csv.DictReader(handle))
    if not projects:
        raise ValidationError("AI project baseline cannot be empty")
    core = [item for item in projects if item["ai_relevance"] == "core_data_centre"]
    enabling = [item for item in projects if item["ai_relevance"] == "enabling_power"]
    known_core = [item for item in core if item["estimated_cost_cad"]]
    known_enabling = [item for item in enabling if item["estimated_cost_cad"]]
    stages = Counter(item["stage"] for item in projects)

    bcpi_latest = latest_bcpi(bcpi_path)
    labour_latest = latest_labour_availability(labour_path)
    labour_canada_latest = latest_labour_availability_canada(labour_canada_path)
    workforce_canada = labour_workforce_stock_canada(workforce_canada_path)
    return {
        "schema_version": "1.3.0",
        "geography_id": "PR_48",
        "as_of_date": max(item["as_of_date"] for item in projects),
        "evidence_status": "observed_with_inferred_classification",
        "ai_project_pipeline": {
            "core_project_count": len(core),
            "enabling_power_project_count": len(enabling),
            "stage_counts": dict(sorted(stages.items())),
            "known_core_capex_cad": sum(float(item["estimated_cost_cad"]) for item in known_core),
            "known_core_capex_coverage": {"projects_with_value": len(known_core), "core_projects": len(core)},
            "known_enabling_capex_cad": sum(
                float(item["estimated_cost_cad"]) for item in known_enabling
            ),
            "known_enabling_capex_coverage": {
                "projects_with_value": len(known_enabling),
                "enabling_projects": len(enabling),
            },
            "source_id": "ALBERTA_MAJOR_PROJECTS",
            "warning": "Reported project values are announcements, not commitments or realized spend. Totals are not probability-weighted and may contain portfolio or phase overlap.",
        },
        "construction_prices": bcpi_latest,
        "labour_availability": labour_latest,
        "labour_availability_canada": labour_canada_latest,
        "labour_workforce_stock_canada": workforce_canada,
        "projects": [
            {
                "project_id": item["project_id"],
                "name": item["name"],
                "estimated_cost_cad": float(item["estimated_cost_cad"])
                if item["estimated_cost_cad"]
                else None,
                "municipality": item["municipality"],
                "start_year": int(item["start_year"]) if item["start_year"] else None,
                "end_year": int(item["end_year"]) if item["end_year"] else None,
                "stage": item["stage"],
                "developer": item["developer"],
                "project_website": item["project_website"] or None,
                "longitude": float(item["longitude"]) if item["longitude"] else None,
                "latitude": float(item["latitude"]) if item["latitude"] else None,
                "location_precision": item["location_precision"],
                "ai_relevance": item["ai_relevance"],
                "source_evidence_status": item["source_evidence_status"],
                "classification_evidence_status": item["classification_evidence_status"],
                "as_of_date": item["as_of_date"],
            }
            for item in sorted(projects, key=lambda row: row["name"])
        ],
    }


def validate_cost_baseline_publication(cost_baseline: dict[str, Any]) -> None:
    authorization = cost_baseline.get("publication_authorization", {})
    if authorization.get("public_projection_authorized") is not True:
        raise ValidationError(
            "cost baseline cannot enter a public release until the independent "
            "modelling gate authorizes its projections"
        )


def latest_labour_availability(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValidationError("labour availability baseline cannot be empty")
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for item in rows:
        groups.setdefault((item["noc_code"], item["statistic"]), []).append(item)

    latest_rows = [
        sorted(items, key=lambda item: item["period_end"])[-1]
        for _, items in sorted(groups.items())
    ]
    period_end = max(item["period_end"] for item in latest_rows)
    observations = []
    for item in sorted(latest_rows, key=lambda row: (row["trade_node_id"], row["noc_code"], row["statistic"])):
        value = float(item["value"]) if item["value"] else None
        observations.append(
            {
                "observation_id": item["observation_id"],
                "indicator_id": item["indicator_id"],
                "noc_code": item["noc_code"],
                "occupation_label": item["occupation_label"],
                "trade_node_id": item["trade_node_id"],
                "statistic": item["statistic"],
                "value": value,
                "unit": item["unit"],
                "period_end": item["period_end"],
                "source_id": item["source_id"],
                "evidence_status": item["evidence_status"],
                "transformation_id": item["transformation_id"],
                "quality_flags": [flag for flag in item["quality_flags"].split("|") if flag],
            }
        )
    return {
        "period_end": period_end,
        "source_id": "STATCAN_JVWS_14100444",
        "evidence_status": "observed",
        "observations": observations,
        "warning": (
            "Job vacancies measure unmet labour demand, not total labour supply. Offered wages are "
            "posted offers, not realized earnings. Suppressed Statistics Canada values remain missing "
            "and are never interpreted as zero."
        ),
    }


def latest_labour_availability_canada(path: Path) -> dict[str, Any]:
    """Build a province-preserving latest-quarter labour evidence snapshot."""
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValidationError("Canada labour availability baseline cannot be empty")

    period_end = max(item["period_end"] for item in rows)
    latest_rows = [item for item in rows if item["period_end"] == period_end]
    expected_geographies = set(PROVINCE_DGUID_TO_GEOGRAPHY_ID.values())
    expected_pairs = {
        (noc_code, statistic)
        for noc_code in TRADE_NOC_TO_NODE
        for statistic in JVWS_STATISTICS
    }
    geography_groups: dict[str, list[dict[str, str]]] = {}
    for item in latest_rows:
        expected_geography_id = PROVINCE_DGUID_TO_GEOGRAPHY_ID.get(
            item["statcan_dguid"]
        )
        if expected_geography_id != item["geography_id"]:
            raise ValidationError(
                "latest Canada labour snapshot contains a non-provincial or "
                f"mismatched geography: {item['geography_id']} / {item['statcan_dguid']}"
            )
        geography_groups.setdefault(item["geography_id"], []).append(item)

    actual_geographies = set(geography_groups)
    if actual_geographies != expected_geographies:
        missing = sorted(expected_geographies - actual_geographies)
        unexpected = sorted(actual_geographies - expected_geographies)
        raise ValidationError(
            "latest Canada labour snapshot must contain exactly 13 provinces and "
            f"territories; missing={missing}, unexpected={unexpected}"
        )

    coverage = []
    for geography_id, items in sorted(geography_groups.items()):
        actual_pairs = {(item["noc_code"], item["statistic"]) for item in items}
        if actual_pairs != expected_pairs or len(items) != len(expected_pairs):
            missing_pairs = sorted(expected_pairs - actual_pairs)
            unexpected_pairs = sorted(actual_pairs - expected_pairs)
            raise ValidationError(
                f"latest Canada labour snapshot is incomplete for {geography_id}: "
                f"{len(items)} of {len(expected_pairs)} cells; "
                f"missing={missing_pairs}, unexpected={unexpected_pairs}"
            )
        observed_cells = sum(item["value"] != "" for item in items)
        total_cells = len(items)
        coverage.append(
            {
                "geography_id": geography_id,
                "geography_label": items[0]["geography_label"],
                "observed_cells": observed_cells,
                "not_published_cells": total_cells - observed_cells,
                "total_cells": total_cells,
                "coverage_percent": round(observed_cells / total_cells * 100, 1),
            }
        )

    observations = []
    for item in sorted(
        latest_rows,
        key=lambda row: (
            row["geography_id"],
            row["trade_node_id"],
            row["noc_code"],
            row["statistic"],
        ),
    ):
        observations.append(
            {
                "observation_id": item["observation_id"],
                "indicator_id": item["indicator_id"],
                "geography_id": item["geography_id"],
                "geography_label": item["geography_label"],
                "statcan_dguid": item["statcan_dguid"],
                "noc_code": item["noc_code"],
                "occupation_label": item["occupation_label"],
                "trade_node_id": item["trade_node_id"],
                "statistic": item["statistic"],
                "value": float(item["value"]) if item["value"] else None,
                "unit": item["unit"],
                "period_end": item["period_end"],
                "source_id": item["source_id"],
                "evidence_status": item["evidence_status"],
                "transformation_id": item["transformation_id"],
                "quality_flags": [
                    flag for flag in item["quality_flags"].split("|") if flag
                ],
            }
        )

    return {
        "period_end": period_end,
        "source_id": "STATCAN_JVWS_14100444",
        "evidence_status": "observed",
        "geography_scope": "13 provinces and territories; Canada totals excluded",
        "coverage": coverage,
        "observations": observations,
        "warning": (
            "Cross-province comparisons must account for survey quality, confidentiality, "
            "suppression and unavailable cells. "
            "Vacancies measure unmet demand rather than workforce stock; offered wages are posted "
            "offers rather than realized earnings. Missing cells are not zero and are not imputed."
        ),
    }


def labour_workforce_stock_canada(path: Path) -> dict[str, Any]:
    """Build the 2021 detailed-trade workforce stock with strict coverage checks."""
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValidationError("Canada labour workforce stock cannot be empty")

    expected_geographies = set(PROVINCE_DGUID_TO_GEOGRAPHY_ID.values())
    expected_nocs = set(TRADE_NOC_TO_NODE)
    geography_groups: dict[str, list[dict[str, str]]] = {}
    for item in rows:
        expected_geography_id = PROVINCE_DGUID_TO_GEOGRAPHY_ID.get(
            item["statcan_dguid"]
        )
        if expected_geography_id != item["geography_id"]:
            raise ValidationError(
                "Canada workforce stock contains a non-provincial or mismatched "
                f"geography: {item['geography_id']} / {item['statcan_dguid']}"
            )
        if item["source_id"] != "STATCAN_CENSUS_OCCUPATION_98100449":
            raise ValidationError("Canada workforce stock contains an unexpected source")
        if item["statistic"] != "Employed" or item["unit"] != "Persons":
            raise ValidationError("Canada workforce stock must contain employed-person counts")
        geography_groups.setdefault(item["geography_id"], []).append(item)

    if set(geography_groups) != expected_geographies:
        raise ValidationError(
            "Canada workforce stock must contain exactly 13 provinces and territories"
        )

    coverage = []
    for geography_id, items in sorted(geography_groups.items()):
        actual_nocs = {item["noc_code"] for item in items}
        if actual_nocs != expected_nocs or len(items) != len(expected_nocs):
            raise ValidationError(
                f"Canada workforce stock is incomplete for {geography_id}: "
                f"{len(items)} of {len(expected_nocs)} cells"
            )
        if any(item["value"] == "" for item in items):
            raise ValidationError(
                f"Canada workforce stock contains an unpublished value for {geography_id}"
            )
        coverage.append(
            {
                "geography_id": geography_id,
                "geography_label": items[0]["geography_label"],
                "published_cells": len(items),
                "zero_filler_cells": sum(
                    "census_zero_filler" in item["quality_flags"] for item in items
                ),
                "total_cells": len(items),
                "coverage_percent": 100.0,
            }
        )

    observations = []
    for item in sorted(
        rows,
        key=lambda row: (
            row["geography_id"],
            row["trade_node_id"],
            row["noc_code"],
        ),
    ):
        observations.append(
            {
                "observation_id": item["observation_id"],
                "indicator_id": item["indicator_id"],
                "geography_id": item["geography_id"],
                "geography_label": item["geography_label"],
                "statcan_dguid": item["statcan_dguid"],
                "noc_code": item["noc_code"],
                "occupation_label": item["occupation_label"],
                "trade_node_id": item["trade_node_id"],
                "statistic": item["statistic"],
                "value": float(item["value"]),
                "unit": item["unit"],
                "period_start": item["period_start"],
                "period_end": item["period_end"],
                "release_date": item["release_date"],
                "source_id": item["source_id"],
                "evidence_status": item["evidence_status"],
                "transformation_id": item["transformation_id"],
                "quality_flags": [
                    flag for flag in item["quality_flags"].split("|") if flag
                ],
            }
        )

    return {
        "period_start": "2021-05-02",
        "period_end": "2021-05-08",
        "release_date": "2022-11-30",
        "source_id": "STATCAN_CENSUS_OCCUPATION_98100449",
        "evidence_status": "observed",
        "geography_scope": "13 provinces and territories; Canada totals excluded",
        "coverage": coverage,
        "observations": observations,
        "warning": (
            "This is a structural workforce stock from the 2021 Census reference week, not a "
            "current estimate of available workers. Counts use the 25% long-form sample and "
            "random rounding. They must not be combined with current vacancies and labelled a "
            "current vacancy rate without a disclosed temporal adjustment and survey bridge."
        ),
    }


def latest_bcpi(path: Path) -> list[dict[str, Any]]:
    indicators = {
        "BCPI_NON_RESIDENTIAL_BUILDINGS_622_DIVISION_COMPOSITE",
        "BCPI_SCHOOL_DIVISION_COMPOSITE",
    }
    with path.open(encoding="utf-8") as handle:
        rows = [item for item in csv.DictReader(handle) if item["indicator_id"] in indicators]
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for item in rows:
        groups.setdefault((item["indicator_id"], item["geography_id"]), []).append(item)
    output: list[dict[str, Any]] = []
    for (indicator, geography), items in sorted(groups.items()):
        ordered = sorted(items, key=lambda item: item["period_end"])
        latest = ordered[-1]
        previous = ordered[-2] if len(ordered) > 1 else None
        change = None
        if previous and float(previous["value"]) != 0:
            change = (float(latest["value"]) / float(previous["value"]) - 1) * 100
        output.append(
            {
                "indicator_id": indicator,
                "geography_id": geography,
                "period_end": latest["period_end"],
                "value": float(latest["value"]),
                "unit": latest["unit"],
                "quarter_over_quarter_percent": round(change, 2) if change is not None else None,
                "evidence_status": "observed",
                "source_id": "STATCAN_BCPI_18100289",
            }
        )
    return output


def build_public_scenario(model_run: dict[str, Any]) -> dict[str, Any]:
    public_peaks = [public_pressure_row(item) for item in model_run["pressure_peaks"]]
    resources = [item for item in public_peaks if item["node_type"] == "resource"]
    outcomes = [item for item in public_peaks if item["node_type"] == "outcome"]
    return {
        "schema_version": "1.1.0",
        "scenario_id": model_run["scenario_id"],
        "parameter_set_id": model_run["parameter_set_id"],
        "name": model_run["scenario_name"],
        "description": model_run["scenario_description"],
        "evidence_status": "scenario",
        "structural_test_banner": model_run["structural_test_banner"],
        "investment_total_cad": model_run["investment_total_cad"],
        "modelled_component_share": model_run["modelled_component_share"],
        "excluded_component_share": model_run["excluded_component_share"],
        "local_capture_share": model_run["local_capture_share"],
        "annual_flows": model_run["annual_flows"],
        "trade_pressure_order": sorted(resources, key=lambda item: -item["central"]),
        "public_delivery_pressure_order": sorted(outcomes, key=lambda item: -item["central"]),
        "dominant_outcome_paths": model_run["dominant_outcome_paths"],
        "sensitivity": [public_sensitivity_row(item) for item in model_run["sensitivity"]],
        "diagnostic_scale": {
            "display_score_range": "[0, 1)",
            "display_transform": "raw_pressure / (1 + raw_pressure)",
            "interpretation": "Monotone bounded display score only; not a probability, percentage, effect size or delay estimate.",
        },
        "case_note": model_run["case_note"],
        "limitations": model_run["limitations"],
    }


def bounded_display_score(raw_pressure: float) -> float:
    if raw_pressure < 0:
        raise ValidationError("absolute pressure scores cannot be negative")
    return min(0.9999, round(raw_pressure / (1 + raw_pressure), 4))


def public_pressure_row(item: dict[str, Any]) -> dict[str, Any]:
    output = dict(item)
    for case in ("low", "central", "high"):
        output[f"raw_{case}"] = item[case]
        output[case] = bounded_display_score(item[case])
    return output


def public_sensitivity_row(item: dict[str, Any]) -> dict[str, Any]:
    output = dict(item)
    for key in ("top_resource", "top_public_delivery_outcome"):
        peak = dict(item[key])
        peak["raw_pressure_score"] = peak["pressure_score"]
        peak["pressure_score"] = bounded_display_score(peak["pressure_score"])
        output[key] = peak
    return output


def build_public_power_overlay(power_run: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": power_run["schema_version"],
        "overlay_id": power_run["overlay_id"],
        "parameter_set_id": power_run["parameter_set_id"],
        "name": power_run["name"],
        "description": power_run["description"],
        "evidence_status": power_run["evidence_status"],
        "structural_test_banner": power_run["structural_test_banner"],
        "start_year": power_run["start_year"],
        "end_year": power_run["end_year"],
        "cases": power_run["cases"],
        "limitations": power_run["limitations"],
    }


def build_public_sources(path: Path) -> list[dict[str, Any]]:
    sources = json.loads(path.read_text(encoding="utf-8"))["sources"]
    return [
        {
            "source_id": item["source_id"],
            "title": item["title"],
            "publisher": item["publisher"],
            "canonical_url": item["canonical_url"],
            "domain": item["domain"],
            "geography": item["geography"],
            "as_of_date": item["as_of_date"],
            "evidence_status": item["evidence_status"],
            "status": item["status"],
        }
        for item in sources
    ]


def build_public_digest(path: Path) -> dict[str, Any]:
    digest = json.loads(path.read_text(encoding="utf-8"))
    return {
        "edition_date": digest["edition_date"],
        "status": digest["status"],
        "items": digest["items"],
        "promotion_rule": "Digest evidence does not change model values until reviewed and included in a versioned release.",
    }


def verify_manifest(root: Path, version: str) -> None:
    release_dir = root / "data" / "releases" / version
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["outputs"].items():
        actual = sha256_file(release_dir / name)
        if actual != expected:
            raise ValidationError(f"release output hash mismatch: {name}")
    available_inputs = release_input_paths(root)
    unknown_inputs = set(manifest["inputs"]) - set(available_inputs)
    if unknown_inputs:
        raise ValidationError(
            "release input key set contains names unknown to this verifier: "
            + ", ".join(sorted(unknown_inputs))
        )
    current_inputs = {
        name: available_inputs[name] for name in manifest["inputs"]
    }
    for name, path in current_inputs.items():
        actual = sha256_file(path)
        expected = manifest["inputs"].get(name)
        if actual != expected:
            raise ValidationError(f"release input hash mismatch: {name}")
    current_commit, _ = git_state(root)
    if current_commit != manifest["code_commit"]:
        raise ValidationError("current HEAD does not match the release code_commit")
    latest = json.loads((root / "public" / "data" / "latest.json").read_text(encoding="utf-8"))
    if latest["manifest"] != manifest:
        raise ValidationError("public latest manifest does not match the immutable release")


def release_input_paths(root: Path) -> dict[str, Path]:
    return {
        "source_registry": root / "data" / "registry" / "sources.json",
        "bcpi_alberta": root / "data" / "processed" / "bcpi_alberta.csv",
        "labour_availability_alberta": (
            root / "data" / "processed" / "labour_availability_alberta.csv"
        ),
        "labour_availability_canada": (
            root / "data" / "processed" / "labour_availability_canada.csv"
        ),
        "labour_workforce_stock_canada": (
            root / "data" / "processed" / "labour_workforce_stock_canada.csv"
        ),
        "census_workforce_retrieval_manifest": (
            root
            / "data"
            / "raw"
            / "statcan_census_occupation_98100449"
            / "2026-08-31_47d7833ff136.json.manifest.json"
        ),
        "alberta_ai_projects": root / "data" / "processed" / "alberta_ai_projects.csv",
        "graph": root / "data" / "model" / "alberta_graph_v0.2.json",
        "scenario": root / "data" / "scenarios" / "alberta_50b_counterfactual_v0.2.json",
        "model_run": root / "data" / "model-runs" / "alberta_50b_counterfactual_v0.2.json",
        "power_definition": root / "data" / "scenarios" / "alberta_power_overlay_v0.1.json",
        "power_run": root / "data" / "model-runs" / "alberta_power_overlay_v0.1.json",
        "labour_pressure_run": (
            root
            / "data"
            / "model-runs"
            / "labour_recruitment_pressure_canada_v0.1.json"
        ),
        "material_cost_screen_run": (
            root
            / "data"
            / "model-runs"
            / "bcpi_material_cost_screen_alberta_v0.1.json"
        ),
        "material_cost_screen_csv": (
            root / "data" / "processed" / "bcpi_material_cost_screen_alberta.csv"
        ),
        "public_project_exposure_run": (
            root
            / "data"
            / "model-runs"
            / "public_project_exposure_alberta_v0.1.json"
        ),
        "cost_baseline_run": (
            root
            / "data"
            / "model-runs"
            / "alberta_bcpi_reference_baseline_v0.1.json"
        ),
        "public_project_exposure_csv": (
            root / "data" / "processed" / "public_project_exposure_alberta.csv"
        ),
        "power_evidence_run": (
            root / "data" / "model-runs" / "power_evidence_alberta_v0.1.json"
        ),
        "power_evidence_csv": (
            root / "data" / "processed" / "power_evidence_alberta.csv"
        ),
        "alberta_major_projects": (
            root / "data" / "processed" / "alberta_major_projects.csv"
        ),
        "aeso_data_centre_update_manual_extract": (
            root / "data" / "manual" / "aeso_data_centre_update_2025_09_page1.json"
        ),
        "aeso_data_centre_update_retrieval_manifest": (
            root
            / "data"
            / "raw"
            / "aeso_data_centre_update_2025_09"
            / "2026-08-31_d997820b3ed2.pdf.manifest.json"
        ),
        "aeso_large_load_projects_retrieval_manifest": (
            root
            / "data"
            / "raw"
            / "aeso_large_load_projects"
            / "2026-08-31_43d55ccde558.html.manifest.json"
        ),
        "aeso_interim_large_load_retrieval_manifest": (
            root
            / "data"
            / "raw"
            / "aeso_interim_large_load_2025_06"
            / "2026-08-31_86ea3ce051e0.html.manifest.json"
        ),
        "digest_items": root / "data" / "digests" / "items" / "2026-08-31.json",
    }


def build_publication_artifacts(
    root: Path,
    version: str,
    workbook_path: Path,
) -> dict[str, Any]:
    """Publish and hash all user-facing artifacts after the workbook is generated."""

    verify_manifest(root, version)
    if not workbook_path.exists():
        raise ValidationError(f"workbook does not exist: {workbook_path}")
    manifest = json.loads(
        (root / "data" / "releases" / version / "manifest.json").read_text(encoding="utf-8")
    )
    downloads_dir = root / "public" / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    workbook_name = f"AIIO_Alberta_Pilot_{version}.xlsx"
    public_workbook = downloads_dir / workbook_name
    shutil.copyfile(workbook_path, public_workbook)

    relative_paths = [
        Path("public/data/latest.json"),
        Path("public/data/manifest.json"),
        Path(f"public/downloads/{workbook_name}"),
        Path("public/downloads/alberta_ai_projects.csv"),
        Path("public/downloads/bcpi_alberta.csv"),
        Path("public/downloads/labour_availability_alberta.csv"),
        Path("public/downloads/labour_availability_canada.csv"),
        Path("public/downloads/labour_workforce_stock_canada.csv"),
        Path("public/downloads/bcpi_material_cost_screen_alberta.csv"),
        Path("public/downloads/public_project_exposure_alberta.csv"),
        Path("public/downloads/power_evidence_alberta.csv"),
    ]
    artifacts = {
        "schema_version": "1.2.0",
        "release_version": version,
        "release_id": manifest["release_id"],
        "code_commit": manifest["code_commit"],
        "input_manifest_hash": manifest["input_manifest_hash"],
        "artifacts": [
            {
                "path": str(relative_path),
                "sha256": hashlib.sha256((root / relative_path).read_bytes()).hexdigest(),
            }
            for relative_path in relative_paths
        ],
    }
    release_path = root / "data" / "releases" / version / "publication-artifacts.json"
    public_path = root / "public" / "data" / "publication-artifacts.json"
    write_json(release_path, artifacts)
    write_json(public_path, artifacts)
    return artifacts


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def git_state(root: Path) -> tuple[str, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False
    )
    return (commit.stdout.strip() or "uncommitted", bool(status.stdout.strip()))
