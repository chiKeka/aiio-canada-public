from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree

from .schemas import ValidationError


MODEL_ID = "AIIO_PROVINCIAL_POWER_PLANNING_CONTRACT_0_1"
EXPECTED_SOURCE_IDS = {
    "IESO_APO_2026_DATA_TABLES",
    "IESO_APO_2026_DEMAND_MODULE",
    "BC_HYDRO_IRP_2025_SUMMARY",
    "QUEBEC_SUPPLY_PLAN_PROGRESS_2025",
    "HYDRO_QUEBEC_DATA_CENTRE_RATE_2026",
}
EXPECTED_GEOGRAPHIES = {"PR_24", "PR_35", "PR_59"}
SOURCE_GEOGRAPHY = {
    "IESO_APO_2026_DATA_TABLES": "PR_35",
    "IESO_APO_2026_DEMAND_MODULE": "PR_35",
    "BC_HYDRO_IRP_2025_SUMMARY": "PR_59",
    "QUEBEC_SUPPLY_PLAN_PROGRESS_2025": "PR_24",
    "HYDRO_QUEBEC_DATA_CENTRE_RATE_2026": "PR_24",
}
UNIT_CONTRACTS = {
    "system_net_annual_energy": {"TWh"},
    "system_regular_electricity_sales": {"TWh"},
    "seasonal_peak_demand": {"GW", "MW"},
    "remaining_capacity_need_after_in_flight": {"MW"},
    "remaining_energy_need_after_in_flight": {"TWh"},
    "data_centre_net_annual_energy": {"TWh"},
    "data_centre_winter_peak": {"MW"},
    "data_centre_peak_announcement": {"MW"},
    "planned_energy_acquisition": {"GWh_per_year"},
    "planned_generation_capacity_addition": {"MW"},
}
COMPARABILITY_GROUPS = {
    "system_net_annual_energy": "system_energy_forecast",
    "system_regular_electricity_sales": "system_energy_forecast_source_specific",
    "seasonal_peak_demand": "system_peak_forecast",
    "remaining_capacity_need_after_in_flight": "operator_remaining_capacity_need",
    "remaining_energy_need_after_in_flight": "operator_remaining_energy_need",
    "data_centre_net_annual_energy": "data_centre_energy_forecast",
    "data_centre_winter_peak": "data_centre_peak_forecast",
    "data_centre_peak_announcement": "data_centre_peak_announcement",
    "planned_energy_acquisition": "planned_supply_action_energy",
    "planned_generation_capacity_addition": "planned_supply_action_capacity",
}
CSV_FIELDS = [
    "metric_id",
    "geography_id",
    "quantity_type",
    "quantity_status",
    "scenario",
    "period",
    "value",
    "unit",
    "is_approximate",
    "source_id",
    "source_locator",
    "comparability_group",
    "evidence_status",
    "publication_authorized",
]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _xlsx_sheet_paths(archive: zipfile.ZipFile) -> dict[str, str]:
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    package_rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    relationships = ElementTree.fromstring(
        archive.read("xl/_rels/workbook.xml.rels")
    )
    targets = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in relationships.findall(f"{{{package_rel_ns}}}Relationship")
    }
    paths: dict[str, str] = {}
    for sheet in workbook.findall(f".//{{{main_ns}}}sheet"):
        relationship_id = sheet.attrib[f"{{{rel_ns}}}id"]
        target = PurePosixPath(targets[relationship_id])
        if target.is_absolute():
            target = PurePosixPath(str(target).lstrip("/"))
        elif not str(target).startswith("xl/"):
            target = PurePosixPath("xl") / target
        paths[sheet.attrib["name"]] = str(target)
    return paths


def _xlsx_cell_value(path: Path, sheet_name: str, cell_ref: str) -> float:
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    with zipfile.ZipFile(path) as archive:
        sheet_paths = _xlsx_sheet_paths(archive)
        if sheet_name not in sheet_paths:
            raise ValidationError(f"XLSX source is missing worksheet {sheet_name}")
        sheet = ElementTree.fromstring(archive.read(sheet_paths[sheet_name]))
        for cell in sheet.findall(f".//{{{main_ns}}}c"):
            if cell.attrib.get("r") != cell_ref:
                continue
            value = cell.find(f"{{{main_ns}}}v")
            if value is None or value.text is None:
                raise ValidationError(f"XLSX cell {sheet_name}!{cell_ref} has no value")
            try:
                return float(value.text)
            except ValueError as exc:
                raise ValidationError(
                    f"XLSX cell {sheet_name}!{cell_ref} is not numeric"
                ) from exc
    raise ValidationError(f"XLSX source is missing cell {sheet_name}!{cell_ref}")


def _validate_source_files(raw: dict[str, Any], root: Path) -> dict[str, Path]:
    source_files = raw.get("source_files", [])
    if {item.get("source_id") for item in source_files} != EXPECTED_SOURCE_IDS:
        raise ValidationError("provincial power extract must bind the exact source set")
    resolved: dict[str, Path] = {}
    for item in source_files:
        source_id = str(item["source_id"])
        path = (root / str(item["archive_path"])).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValidationError(f"{source_id} archive path must remain inside the repository")
        if not path.is_file():
            raise ValidationError(f"{source_id} archive file is missing")
        if _sha256_file(path) != item.get("content_hash"):
            raise ValidationError(f"{source_id} archive hash does not match the extract")
        resolved[source_id] = path
    return resolved


def _validate_metrics(
    metrics: list[dict[str, Any]], source_paths: dict[str, Path]
) -> list[dict[str, Any]]:
    if not metrics:
        raise ValidationError("provincial power extract requires metrics")
    metric_ids = [str(item.get("metric_id", "")) for item in metrics]
    if "" in metric_ids or len(metric_ids) != len(set(metric_ids)):
        raise ValidationError("provincial power metric_id values must be non-empty and unique")
    if {str(item.get("geography_id")) for item in metrics} != EXPECTED_GEOGRAPHIES:
        raise ValidationError("provincial power metrics must cover Ontario, Quebec and B.C.")

    validated: list[dict[str, Any]] = []
    for item in metrics:
        source_id = str(item.get("source_id", ""))
        geography_id = str(item.get("geography_id", ""))
        quantity_type = str(item.get("quantity_type", ""))
        unit = str(item.get("unit", ""))
        if source_id not in EXPECTED_SOURCE_IDS:
            raise ValidationError(f"unknown power source_id {source_id}")
        if SOURCE_GEOGRAPHY[source_id] != geography_id:
            raise ValidationError(f"{item['metric_id']} source/geography mismatch")
        if quantity_type not in UNIT_CONTRACTS or unit not in UNIT_CONTRACTS[quantity_type]:
            raise ValidationError(f"{item['metric_id']} violates its quantity/unit contract")
        if not str(item.get("quantity_status", "")).strip():
            raise ValidationError(f"{item['metric_id']} requires quantity_status")
        if not str(item.get("scenario", "")).strip() or not str(item.get("period", "")).strip():
            raise ValidationError(f"{item['metric_id']} requires scenario and period")
        if not isinstance(item.get("is_approximate"), bool):
            raise ValidationError(f"{item['metric_id']} requires a boolean approximation flag")
        try:
            value = float(item["value"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError(f"{item['metric_id']} requires a numeric value") from exc
        if value < 0:
            raise ValidationError(f"{item['metric_id']} cannot be negative")

        if source_id == "IESO_APO_2026_DATA_TABLES":
            locator = str(item.get("source_locator", ""))
            match = re.fullmatch(r"(Figure \d+)!([A-Z]+\d+)", locator)
            if not match:
                raise ValidationError(f"{item['metric_id']} requires an exact XLSX locator")
            workbook_value = _xlsx_cell_value(
                source_paths[source_id], match.group(1), match.group(2)
            )
            if abs(workbook_value - value) > 1e-9:
                raise ValidationError(
                    f"{item['metric_id']} does not match {locator}: {workbook_value}"
                )

        output = dict(item)
        output["value"] = value
        output["comparability_group"] = COMPARABILITY_GROUPS[quantity_type]
        output["evidence_status"] = "observed_source_publication"
        validated.append(output)
    return sorted(validated, key=lambda item: (item["geography_id"], item["metric_id"]))


def _validate_transmission_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    action_ids = [str(item.get("action_id", "")) for item in actions]
    if not actions or "" in action_ids or len(action_ids) != len(set(action_ids)):
        raise ValidationError("transmission actions must be non-empty with unique identifiers")
    for item in actions:
        if item.get("geography_id") != "PR_59" or item.get("source_id") != "BC_HYDRO_IRP_2025_SUMMARY":
            raise ValidationError("current transmission actions must remain scoped to B.C.")
        if not all(str(item.get(key, "")).strip() for key in ("status", "action", "source_locator")):
            raise ValidationError(f"{item['action_id']} has an incomplete action contract")
    return sorted(actions, key=lambda item: item["action_id"])


def run_provincial_power_planning_contract(
    extract_path: Path,
    root: Path,
    output_json_path: Path,
    output_csv_path: Path,
) -> dict[str, Any]:
    raw = json.loads(extract_path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "0.1.0":
        raise ValidationError("provincial power extract must use schema_version 0.1.0")
    source_paths = _validate_source_files(raw, root)
    metrics = _validate_metrics(raw.get("metrics", []), source_paths)
    actions = _validate_transmission_actions(raw.get("transmission_actions", []))
    reviewed = raw.get("review_status") == "independently_reviewed"

    for metric in metrics:
        metric["publication_authorized"] = reviewed

    coverage = {
        geography: {
            "metric_count": sum(item["geography_id"] == geography for item in metrics),
            "quantity_types": sorted(
                {item["quantity_type"] for item in metrics if item["geography_id"] == geography}
            ),
        }
        for geography in sorted(EXPECTED_GEOGRAPHIES)
    }
    result = {
        "schema_version": "0.1.0",
        "model_id": MODEL_ID,
        "extract_id": raw["extract_id"],
        "as_of_date": raw["as_of_date"],
        "evidence_status": "observed_publications_with_published_forecasts_and_plan_actions",
        "review_status": raw["review_status"],
        "review_note": raw.get("review_note", ""),
        "source_count": len(source_paths),
        "metric_count": len(metrics),
        "transmission_action_count": len(actions),
        "coverage": coverage,
        "quantity_status_counts": dict(sorted(Counter(item["quantity_status"] for item in metrics).items())),
        "metrics": metrics,
        "transmission_actions": actions,
        "comparability_contract": {
            "allowed": [
                "Compare values only when quantity type, unit, scenario meaning, period basis and system boundary align.",
                "Convert GW to MW only for like-for-like system peak comparisons while retaining the publisher's original unit.",
                "Compare scenarios within one publisher's forecast before considering cross-province contrasts.",
            ],
            "prohibited": [
                "Do not pool Ontario data-centre annual energy with Quebec data-centre winter peak.",
                "Do not treat planned generation, energy acquisitions or named transmission actions as demand or spare capacity.",
                "Do not infer a transmission build requirement from province-wide load or capex values without location-specific connection and system studies.",
                "Do not treat a published forecast as realized demand, a connection request, an executed contract or an approval.",
            ],
        },
        "publication_boundary": {
            "status": "research_evidence_only" if not reviewed else "reviewed_source_profile",
            "provincial_power_profile_authorized": reviewed,
            "scenario_calibration_authorized": False,
            "transmission_requirement_authorized": False,
            "reason": "Independent source extraction review is pending; even after review, calibration and location-specific transmission studies remain separate gates.",
        },
        "limitations": [
            "The selected metrics are a decision-oriented source profile, not a complete extraction of every published series.",
            "Ontario publishes data-centre annual energy scenarios; Quebec publishes winter peak by use; the B.C. public summary does not publish a comparable data-centre path.",
            "Quebec regular electricity sales and Ontario net annual energy use different publisher definitions and should not be treated as one national total without a reconciliation study.",
            "B.C. numeric actions are supply-plan measures, not a quantified data-centre demand forecast or a reserve margin.",
        ],
    }

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: item[field] for field in CSV_FIELDS} for item in metrics)
    return result
