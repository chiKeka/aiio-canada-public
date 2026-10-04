from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .paths import repository_path
from xml.etree import ElementTree

from .adapters.provincial_projects import classify_asset_class
from .quebec_revisions import _parse_money_millions, _parse_month_year
from .quebec_vintages import (
    REQUIRED_DASHBOARD_FIELDS,
    canonical_field_name,
    sha256_file,
)
from .schemas import ValidationError


MODEL_ID = "AIIO_QUEBEC_PQI_FULL_ARCHIVE_LONGITUDINAL_0_1"
SOURCE_ID = "QUEBEC_PQI_PROJECT_DASHBOARD"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
CELL_REFERENCE_RE = re.compile(r"([A-Z]+)(\d+)")
RETIREMENT_MARKERS = (
    "sera retire du tableau de bord",
    "sera retiree du tableau de bord",
    "sera retire lors de la prochaine mise a jour",
    "sera retiree lors de la prochaine mise a jour",
)
COMPLETE_SERVICE_MARKER = "mise en service complete"


def run_quebec_full_archive_longitudinal(
    contract_path: Path,
    repository_root: Path,
    milestone_report_path: Path,
    report_path: Path,
    snapshot_output_path: Path,
    lifecycle_output_path: Path,
    transition_output_path: Path,
) -> dict[str, Any]:
    contract = _read_json(contract_path, "Quebec full-archive contract")
    milestone_report = _read_json(
        milestone_report_path, "Quebec milestone longitudinal report"
    )
    if contract.get("contract_id") != "AIIO_QUEBEC_PQI_FULL_ARCHIVE_0_1":
        raise ValidationError("unexpected Quebec full-archive contract ID")
    resources = contract.get("resources", [])
    if (
        len(resources) != 69
        or len({item.get("snapshot_date") for item in resources}) != 69
        or contract.get("publication_boundary", {}).get(
            "catalog_snapshot_coverage_contract_complete"
        )
        is not True
    ):
        raise ValidationError("Quebec full-archive contract must cover 69 unique dates")
    if contract.get("publication_boundary", {}).get(
        "project_exit_outcome_authorized"
    ) is not False:
        raise ValidationError("Quebec full-archive contract must fail closed")

    resources = sorted(resources, key=lambda item: item["snapshot_date"])
    snapshot_dates = [item["snapshot_date"] for item in resources]
    snapshot_rows: list[dict[str, Any]] = []
    snapshot_summaries: list[dict[str, Any]] = []
    ids_by_date: dict[str, set[str]] = {}
    observations_by_project: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for vintage_index, resource in enumerate(resources):
        csv_path = _resolve_repository_path(repository_root, resource["archive_path"])
        csv_manifest_path = _resolve_repository_path(
            repository_root, resource["manifest_path"]
        )
        _verify_archive(
            csv_path,
            csv_manifest_path,
            resource["content_hash"],
            resource["resource_id"],
            resource["snapshot_date"],
        )
        fallback = resource.get("fallback_xlsx")
        if fallback:
            xlsx_path = _resolve_repository_path(
                repository_root, fallback["archive_path"]
            )
            xlsx_manifest_path = _resolve_repository_path(
                repository_root, fallback["manifest_path"]
            )
            _verify_archive(
                xlsx_path,
                xlsx_manifest_path,
                fallback["content_hash"],
                fallback["resource_id"],
                resource["snapshot_date"],
            )
            raw_rows = _read_xlsx_snapshot(xlsx_path)
            representation_type = "official_paired_xlsx_fallback"
            representation_hash = fallback["content_hash"]
        else:
            raw_rows = _read_csv_snapshot(csv_path)
            representation_type = resource["schema_profile"]
            representation_hash = resource["content_hash"]
        rows, duplicate_rows_collapsed = _deduplicate_rows(raw_rows, resource)
        date_ids: set[str] = set()
        for raw in rows:
            source_record_id = _normalize_project_id(raw["no_projet"])
            project_id = f"QCPQI_{source_record_id}"
            if project_id in date_ids:
                raise ValidationError(
                    f"duplicate Quebec project ID after normalization: {project_id}"
                )
            date_ids.add(project_id)
            history_text = raw.get("suivi_modifications", "")
            normalized_history = _normalized_text(history_text)
            asset_class = classify_asset_class(
                SOURCE_ID,
                raw.get("secteur_activite", ""),
                raw.get("nature_travaux", ""),
                "",
                raw.get("nom_projet", ""),
                raw.get("description", ""),
            )
            observation = {
                "snapshot_date": resource["snapshot_date"],
                "vintage_index": vintage_index,
                "threshold_regime": resource["threshold_regime"],
                "project_id": project_id,
                "source_record_id": source_record_id,
                "project_name": raw.get("nom_projet", "").strip(),
                "asset_class": asset_class,
                "source_category": raw.get("secteur_activite", "").strip(),
                "stage_source_text": raw.get("etat_avancement", "").strip(),
                "region": raw.get("region", "").strip(),
                "municipality": raw.get("localisation", "").strip(),
                "current_authorized_cost_cad": _parse_money_millions(
                    raw.get("cout_total")
                ),
                "current_completion_month": _parse_month_year(
                    raw.get("date_fin_mise_en_service")
                ),
                "publisher_retirement_marker": any(
                    marker in normalized_history for marker in RETIREMENT_MARKERS
                ),
                "publisher_complete_service_marker": (
                    COMPLETE_SERVICE_MARKER in normalized_history
                ),
                "history_text_sha256": _sha256_text(history_text),
                "representation_type": representation_type,
                "representation_hash": representation_hash,
                "source_id": SOURCE_ID,
                "evidence_status": "observed_snapshot_fields_with_inferred_asset_class",
            }
            snapshot_rows.append(observation)
            observations_by_project[project_id].append(observation)
        ids_by_date[resource["snapshot_date"]] = date_ids
        snapshot_summaries.append(
            {
                "snapshot_date": resource["snapshot_date"],
                "threshold_regime": resource["threshold_regime"],
                "project_count": len(rows),
                "publisher_duplicate_rows_collapsed": duplicate_rows_collapsed,
                "schema_profile": resource["schema_profile"],
                "representation_type": representation_type,
                "csv_content_hash": resource["content_hash"],
                "representation_hash": representation_hash,
                "resource_id": resource["resource_id"],
            }
        )

    transition_rows: list[dict[str, Any]] = []
    seen_before: set[str] = set()
    for index in range(1, len(snapshot_dates)):
        previous_date = snapshot_dates[index - 1]
        current_date = snapshot_dates[index]
        previous_ids = ids_by_date[previous_date]
        current_ids = ids_by_date[current_date]
        disappeared = previous_ids - current_ids
        newly_observed = current_ids - previous_ids
        prior_to_previous = seen_before | previous_ids
        reentered = newly_observed & seen_before
        previous_observations = {
            row["project_id"]: row
            for row in snapshot_rows
            if row["snapshot_date"] == previous_date
        }
        retirement_backed = {
            project_id
            for project_id in disappeared
            if previous_observations[project_id]["publisher_retirement_marker"]
            and previous_observations[project_id]["publisher_complete_service_marker"]
        }
        transition_rows.append(
            {
                "previous_snapshot_date": previous_date,
                "current_snapshot_date": current_date,
                "previous_project_count": len(previous_ids),
                "current_project_count": len(current_ids),
                "continuing_project_count": len(previous_ids & current_ids),
                "newly_observed_project_count": len(newly_observed),
                "disappeared_project_count": len(disappeared),
                "reentered_project_count": len(reentered),
                "publisher_declared_retirement_disappearance_count": len(
                    retirement_backed
                ),
                "unclassified_disappearance_count": len(
                    disappeared - retirement_backed
                ),
                "threshold_transition": (
                    previous_date < "2020-11-01" <= current_date
                ),
                "source_id": SOURCE_ID,
                "evidence_status": "observed_stable_id_transition",
            }
        )
        seen_before = prior_to_previous

    lifecycle_rows: list[dict[str, Any]] = []
    for project_id, observations in sorted(observations_by_project.items()):
        observations.sort(key=lambda item: item["vintage_index"])
        present_indices = {int(item["vintage_index"]) for item in observations}
        presence = [index in present_indices for index in range(len(snapshot_dates))]
        observation_by_index = {
            int(item["vintage_index"]): item for item in observations
        }
        disappearance_indices = [
            index
            for index in range(len(presence) - 1)
            if presence[index] and not presence[index + 1]
        ]
        reentry_indices = [
            index
            for index in range(1, len(presence))
            if presence[index]
            and not presence[index - 1]
            and any(presence[: index - 1])
        ]
        retirement_backed_disappearances = sum(
            1
            for index in disappearance_indices
            if observation_by_index[index]["publisher_retirement_marker"]
            and observation_by_index[index]["publisher_complete_service_marker"]
        )
        consecutive_pairs = [
            (previous, current)
            for previous, current in zip(observations, observations[1:])
            if int(current["vintage_index"]) == int(previous["vintage_index"]) + 1
        ]
        cost_pairs = [
            pair
            for pair in consecutive_pairs
            if pair[0]["current_authorized_cost_cad"] is not None
            and pair[1]["current_authorized_cost_cad"] is not None
        ]
        completion_pairs = [
            pair
            for pair in consecutive_pairs
            if pair[0]["current_completion_month"] is not None
            and pair[1]["current_completion_month"] is not None
        ]
        latest = observations[-1]
        quality_flags = ["complete_catalog_snapshot_coverage"]
        if disappearance_indices:
            quality_flags.append("interval_disappearance_observed")
        if retirement_backed_disappearances:
            quality_flags.append(
                "publisher_declared_complete_service_precedes_disappearance"
            )
        if len(disappearance_indices) > retirement_backed_disappearances:
            quality_flags.append("some_disappearance_causes_unknown")
        if reentry_indices:
            quality_flags.append("catalog_reentry_observed")
        if observations[0]["threshold_regime"] == "cad_20m_and_over":
            quality_flags.append("first_observed_after_threshold_change")
        lifecycle_rows.append(
            {
                "project_id": project_id,
                "source_record_id": latest["source_record_id"],
                "latest_project_name": latest["project_name"],
                "latest_asset_class": latest["asset_class"],
                "first_observed_snapshot": observations[0]["snapshot_date"],
                "last_observed_snapshot": latest["snapshot_date"],
                "observed_snapshot_count": len(observations),
                "present_in_latest_snapshot": presence[-1],
                "observed_pre_threshold": any(
                    item["threshold_regime"] == "cad_50m_and_over"
                    for item in observations
                ),
                "observed_post_threshold": any(
                    item["threshold_regime"] == "cad_20m_and_over"
                    for item in observations
                ),
                "interval_disappearance_count": len(disappearance_indices),
                "catalog_reentry_count": len(reentry_indices),
                "publisher_declared_retirement_disappearance_count": retirement_backed_disappearances,
                "unclassified_disappearance_count": len(disappearance_indices)
                - retirement_backed_disappearances,
                "consecutive_observation_pair_count": len(consecutive_pairs),
                "comparable_cost_pair_count": len(cost_pairs),
                "authorized_cost_change_pair_count": sum(
                    1
                    for previous, current in cost_pairs
                    if abs(
                        float(current["current_authorized_cost_cad"])
                        - float(previous["current_authorized_cost_cad"])
                    )
                    > 1
                ),
                "comparable_completion_pair_count": len(completion_pairs),
                "completion_month_change_pair_count": sum(
                    1
                    for previous, current in completion_pairs
                    if current["current_completion_month"]
                    != previous["current_completion_month"]
                ),
                "presence_pattern": "".join(
                    "1" if item else "0" for item in presence
                ),
                "source_id": SOURCE_ID,
                "quality_flags": "|".join(quality_flags),
            }
        )

    snapshot_output_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_output_path.parent.mkdir(parents=True, exist_ok=True)
    transition_output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(snapshot_output_path, snapshot_rows)
    _write_csv(lifecycle_output_path, lifecycle_rows)
    _write_csv(transition_output_path, transition_rows)

    latest_ids = ids_by_date[snapshot_dates[-1]]
    lifecycle_by_id = {row["project_id"]: row for row in lifecycle_rows}
    result = {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "contract_id": contract["contract_id"],
        "contract_sha256": sha256_file(contract_path),
        "milestone_report_sha256": sha256_file(milestone_report_path),
        "snapshot_date_count": len(snapshot_dates),
        "snapshot_start_date": snapshot_dates[0],
        "snapshot_end_date": snapshot_dates[-1],
        "snapshot_observation_count": len(snapshot_rows),
        "unique_project_count": len(lifecycle_rows),
        "latest_snapshot_project_count": len(latest_ids),
        "present_in_latest_project_count": sum(
            1 for row in lifecycle_rows if row["present_in_latest_snapshot"]
        ),
        "absent_from_latest_project_count": sum(
            1 for row in lifecycle_rows if not row["present_in_latest_snapshot"]
        ),
        "project_with_interval_disappearance_count": sum(
            1 for row in lifecycle_rows if row["interval_disappearance_count"] > 0
        ),
        "project_with_catalog_reentry_count": sum(
            1 for row in lifecycle_rows if row["catalog_reentry_count"] > 0
        ),
        "project_with_publisher_declared_retirement_disappearance_count": sum(
            1
            for row in lifecycle_rows
            if row["publisher_declared_retirement_disappearance_count"] > 0
        ),
        "disappearance_event_count": sum(
            int(row["interval_disappearance_count"]) for row in lifecycle_rows
        ),
        "publisher_declared_retirement_disappearance_event_count": sum(
            int(row["publisher_declared_retirement_disappearance_count"])
            for row in lifecycle_rows
        ),
        "unclassified_disappearance_event_count": sum(
            int(row["unclassified_disappearance_count"]) for row in lifecycle_rows
        ),
        "linked_change_diagnostics": {
            "consecutive_observation_pair_count": sum(
                int(row["consecutive_observation_pair_count"])
                for row in lifecycle_rows
            ),
            "comparable_cost_pair_count": sum(
                int(row["comparable_cost_pair_count"]) for row in lifecycle_rows
            ),
            "authorized_cost_change_pair_count": sum(
                int(row["authorized_cost_change_pair_count"])
                for row in lifecycle_rows
            ),
            "comparable_completion_pair_count": sum(
                int(row["comparable_completion_pair_count"])
                for row in lifecycle_rows
            ),
            "completion_month_change_pair_count": sum(
                int(row["completion_month_change_pair_count"])
                for row in lifecycle_rows
            ),
        },
        "milestone_comparison": {
            "milestone_snapshot_count": milestone_report["vintage_count"],
            "milestone_unique_project_count": milestone_report["unique_project_count"],
            "full_archive_unique_project_count": len(lifecycle_rows),
            "additional_unique_projects_observed": len(lifecycle_rows)
            - int(milestone_report["unique_project_count"]),
            "milestone_absent_from_latest_project_count": milestone_report[
                "absent_from_latest_project_count"
            ],
            "full_archive_absent_from_latest_project_count": sum(
                1 for row in lifecycle_rows if not row["present_in_latest_snapshot"]
            ),
            "milestone_reentry_project_count": milestone_report[
                "project_with_milestone_reentry_count"
            ],
            "full_archive_reentry_project_count": sum(
                1 for row in lifecycle_rows if row["catalog_reentry_count"] > 0
            ),
            "interpretation": "The full archive is the authoritative selection diagnostic; milestone differences quantify information lost by annual sampling.",
        },
        "snapshot_summaries": snapshot_summaries,
        "outputs": {
            "snapshot_csv": repository_path(snapshot_output_path),
            "snapshot_csv_sha256": sha256_file(snapshot_output_path),
            "lifecycle_csv": repository_path(lifecycle_output_path),
            "lifecycle_csv_sha256": sha256_file(lifecycle_output_path),
            "transition_csv": repository_path(transition_output_path),
            "transition_csv_sha256": sha256_file(transition_output_path),
        },
        "limitations": [
            "One publisher CSV is structurally unusable and is represented by the official paired XLSX for the same snapshot date.",
            "A stable ID disappearance without an explicit prior complete-service and retirement statement has an unknown cause.",
            "Publisher-declared complete service and planned dashboard retirement are not independently audited final completion outcomes.",
            "The November 2020 publication-threshold change confounds threshold entry with ordinary project entry.",
            "Authorized cost and completion fields are plans, not final audited outturns, and no common estimate price-basis date is available.",
            "No AI treatment is present, so no AI-attributable effect is estimated.",
        ],
        "publication_boundary": {
            "catalog_snapshot_coverage_complete": True,
            "all_snapshots_parsed_directly_from_csv": False,
            "publisher_declared_retirement_is_final_outcome": False,
            "project_exit_outcome_authorized": False,
            "public_project_cost_outcome_authorized": False,
            "public_project_schedule_outcome_authorized": False,
            "ai_attributable_effect_authorized": False,
            "status": "complete_catalog_selection_diagnostic_research_only",
            "reason": "All 69 official snapshot dates are represented and stable-ID transitions are reproducible, but one official XLSX substitution is required, most disappearance causes remain unclassified, authorized parameters are not final outturns and no AI treatment is observed.",
        },
    }
    if result["present_in_latest_project_count"] != len(latest_ids):
        raise ValidationError("Quebec full-archive latest-presence count mismatch")
    if result["unique_project_count"] < milestone_report["unique_project_count"]:
        raise ValidationError("Quebec full archive cannot contain fewer IDs than milestones")
    if any(project_id not in lifecycle_by_id for project_id in latest_ids):
        raise ValidationError("Quebec full archive lost a latest-snapshot project")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _resolve_repository_path(repository_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repository_root / path


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be an object")
    return value


def _verify_archive(
    archive_path: Path,
    manifest_path: Path,
    expected_hash: str,
    resource_id: str,
    snapshot_date: str,
) -> None:
    manifest = _read_json(manifest_path, "Quebec full-archive manifest")
    actual_hash = sha256_file(archive_path)
    if actual_hash != expected_hash or manifest.get("content_hash") != actual_hash:
        raise ValidationError(f"Quebec full-archive hash mismatch: {snapshot_date}")
    if manifest.get("resource_id") != resource_id:
        raise ValidationError(f"Quebec full-archive resource mismatch: {snapshot_date}")
    if manifest.get("snapshot_date") != snapshot_date:
        raise ValidationError(f"Quebec full-archive date mismatch: {snapshot_date}")


def _read_csv_snapshot(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            original_fields = [field.strip() for field in (reader.fieldnames or [])]
            canonical_fields = [canonical_field_name(field) for field in original_fields]
            missing = REQUIRED_DASHBOARD_FIELDS - set(canonical_fields)
            if missing:
                raise ValidationError(
                    f"Quebec full-archive CSV is missing {sorted(missing)}: {path.name}"
                )
            if len(canonical_fields) != len(set(canonical_fields)):
                raise ValidationError(
                    f"Quebec full-archive CSV has duplicate canonical fields: {path.name}"
                )
            mapping = dict(zip(original_fields, canonical_fields))
            rows: list[dict[str, str]] = []
            for raw in reader:
                if None in raw:
                    raise ValidationError(
                        f"Quebec full-archive CSV has an over-wide row: {path.name}"
                    )
                rows.append(
                    {
                        mapping[str(key).strip()]: (value or "").strip()
                        for key, value in raw.items()
                        if key is not None
                    }
                )
            return rows
    except UnicodeDecodeError as exc:
        raise ValidationError(f"unable to decode Quebec CSV {path.name}: {exc}") from exc


def _read_xlsx_snapshot(path: Path) -> list[dict[str, str]]:
    try:
        with zipfile.ZipFile(path) as archive:
            shared_strings = _read_shared_strings(archive)
            sheet_xml = archive.read("xl/worksheets/sheet1.xml")
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        raise ValidationError(f"unable to read Quebec fallback XLSX: {exc}") from exc
    root = ElementTree.fromstring(sheet_xml)
    matrix: list[list[str]] = []
    for row_element in root.findall(f".//{{{MAIN_NS}}}row"):
        values: list[str] = []
        for cell in row_element.findall(f"{{{MAIN_NS}}}c"):
            reference = cell.attrib.get("r", "")
            match = CELL_REFERENCE_RE.fullmatch(reference)
            if match is None:
                raise ValidationError(f"invalid XLSX cell reference: {reference!r}")
            column_index = _column_number(match.group(1))
            while len(values) <= column_index:
                values.append("")
            cell_type = cell.attrib.get("t")
            value_element = cell.find(f"{{{MAIN_NS}}}v")
            if cell_type == "inlineStr":
                text = "".join(
                    element.text or ""
                    for element in cell.findall(f".//{{{MAIN_NS}}}t")
                )
            elif value_element is None:
                text = ""
            elif cell_type == "s":
                text = shared_strings[int(value_element.text or "0")]
            else:
                text = value_element.text or ""
            values[column_index] = _decode_excel_text(text)
        matrix.append(values)
    if len(matrix) < 2:
        raise ValidationError("Quebec fallback XLSX contains no project rows")
    canonical_fields = [canonical_field_name(value) for value in matrix[0]]
    missing = REQUIRED_DASHBOARD_FIELDS - set(canonical_fields)
    if missing:
        raise ValidationError(
            f"Quebec fallback XLSX is missing fields: {sorted(missing)}"
        )
    rows: list[dict[str, str]] = []
    for raw_values in matrix[1:]:
        padded = raw_values + [""] * (len(canonical_fields) - len(raw_values))
        row = {
            field: str(padded[index]).strip()
            for index, field in enumerate(canonical_fields)
        }
        if not any(row.values()):
            continue
        if row.get("date_fin_mise_en_service"):
            row["date_fin_mise_en_service"] = _excel_serial_to_date(
                row["date_fin_mise_en_service"]
            )
        rows.append(row)
    return rows


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [
        _decode_excel_text(
            "".join(
                element.text or "" for element in item.findall(f".//{{{MAIN_NS}}}t")
            )
        )
        for item in root.findall(f"{{{MAIN_NS}}}si")
    ]


def _column_number(letters: str) -> int:
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter) - ord("A") + 1
    return value - 1


def _decode_excel_text(value: str) -> str:
    return value.replace("_x000D_\n", "\n").replace("_x000D_", "\n")


def _excel_serial_to_date(value: str) -> str:
    try:
        serial = float(value)
    except ValueError:
        return value
    return (datetime(1899, 12, 30) + timedelta(days=serial)).date().isoformat()


def _deduplicate_rows(
    rows: list[dict[str, str]], resource: dict[str, Any]
) -> tuple[list[dict[str, str]], int]:
    output: dict[str, dict[str, str]] = {}
    collapsed = 0
    for row in rows:
        project_id = _normalize_project_id(row.get("no_projet", ""))
        if not project_id:
            raise ValidationError(
                f"blank Quebec project ID in {resource['snapshot_date']}"
            )
        if project_id not in output:
            output[project_id] = row
            continue
        previous = output[project_id]
        comparison_keys = (set(previous) | set(row)) - {"latitude", "longitude"}
        if any(previous.get(key, "") != row.get(key, "") for key in comparison_keys):
            raise ValidationError(
                "conflicting Quebec duplicate project ID "
                f"{project_id!r} in {resource['snapshot_date']}"
            )
        collapsed += 1
    return list(output.values()), collapsed


def _normalize_project_id(value: str) -> str:
    stripped = str(value).strip()
    if re.fullmatch(r"\d+\.0", stripped):
        return stripped[:-2]
    return stripped


def _normalized_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(without_accents.casefold().replace("’", "'").split())


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValidationError(f"cannot write empty Quebec full-archive output: {path.name}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
