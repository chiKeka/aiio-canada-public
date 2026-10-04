from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .adapters.provincial_projects import classify_asset_class
from .paths import repository_path
from .quebec_revisions import _parse_money_millions, _parse_month_year
from .schemas import ValidationError


MODEL_ID = "AIIO_QUEBEC_PQI_MILESTONE_LONGITUDINAL_0_1"
REQUIRED_FIELDS = {
    "no_projet",
    "nom_projet",
    "cout_total",
    "date_fin_mise_en_service",
    "etat_avancement",
    "suivi_modifications",
    "secteur_activite",
    "region",
    "localisation",
    "nature_travaux",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def run_quebec_milestone_longitudinal(
    contract_path: Path,
    raw_root: Path,
    report_path: Path,
    snapshot_output_path: Path,
    lifecycle_output_path: Path,
) -> dict[str, Any]:
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read Quebec milestone contract: {exc}") from exc
    if contract.get("contract_id") != "AIIO_QUEBEC_PQI_MILESTONE_VINTAGES_0_1":
        raise ValidationError("unexpected Quebec milestone contract ID")
    vintages = contract.get("selected_vintages", [])
    if len(vintages) < 2 or contract.get("selection_rule", {}).get("complete_monthly_panel") is not False:
        raise ValidationError("Quebec milestone contract must be multi-vintage and explicitly incomplete")
    if contract.get("publication_boundary", {}).get("longitudinal_outcome_panel_authorized") is not False:
        raise ValidationError("Quebec milestone contract must fail closed")

    snapshot_rows: list[dict[str, Any]] = []
    vintage_summaries: list[dict[str, Any]] = []
    for vintage_index, vintage in enumerate(vintages):
        archive_path = raw_root / Path(str(vintage["archive_path"])).name
        manifest_path = archive_path.with_suffix(".csv.manifest.json")
        _verify_vintage(archive_path, manifest_path, vintage)
        rows, publisher_duplicate_rows_collapsed = _read_snapshot(archive_path)
        seen_ids: set[str] = set()
        for row in rows:
            source_record_id = row["no_projet"].strip()
            if not source_record_id:
                raise ValidationError(f"blank Quebec project ID in {vintage['snapshot_date']}")
            seen_ids.add(source_record_id)
            asset_class = classify_asset_class(
                "QUEBEC_PQI_PROJECT_DASHBOARD",
                row.get("secteur_activite", ""),
                row.get("nature_travaux", ""),
                "",
                row.get("nom_projet", ""),
                row.get("description", ""),
            )
            snapshot_rows.append(
                {
                    "snapshot_date": vintage["snapshot_date"],
                    "vintage_index": vintage_index,
                    "threshold_regime": vintage["threshold_regime"],
                    "project_id": f"QCPQI_{source_record_id}",
                    "source_record_id": source_record_id,
                    "project_name": row.get("nom_projet", "").strip(),
                    "asset_class": asset_class,
                    "source_category": row.get("secteur_activite", "").strip(),
                    "stage_source_text": row.get("etat_avancement", "").strip(),
                    "region": row.get("region", "").strip(),
                    "municipality": row.get("localisation", "").strip(),
                    "current_authorized_cost_cad": _parse_money_millions(
                        row.get("cout_total")
                    ),
                    "current_completion_month": _parse_month_year(
                        row.get("date_fin_mise_en_service")
                    ),
                    "history_text_sha256": _sha256_text(
                        row.get("suivi_modifications", "")
                    ),
                    "source_id": "QUEBEC_PQI_PROJECT_DASHBOARD",
                    "evidence_status": "observed_snapshot_fields_with_inferred_asset_class",
                }
            )
        vintage_summaries.append(
            {
                "snapshot_date": vintage["snapshot_date"],
                "threshold_regime": vintage["threshold_regime"],
                "project_count": len(rows),
                "raw_row_count": vintage["row_count"],
                "publisher_duplicate_rows_collapsed": publisher_duplicate_rows_collapsed,
                "content_hash": vintage["content_hash"],
                "resource_id": vintage["resource_id"],
            }
        )

    snapshot_dates = [item["snapshot_date"] for item in vintage_summaries]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in snapshot_rows:
        grouped[row["project_id"]].append(row)
    lifecycle_rows: list[dict[str, Any]] = []
    for project_id, observations in sorted(grouped.items()):
        observations.sort(key=lambda item: item["vintage_index"])
        present_indices = {int(item["vintage_index"]) for item in observations}
        presence = [index in present_indices for index in range(len(snapshot_dates))]
        disappearances = sum(
            1 for index in range(len(presence) - 1) if presence[index] and not presence[index + 1]
        )
        reentries = sum(
            1
            for index in range(1, len(presence))
            if presence[index]
            and not presence[index - 1]
            and any(presence[: index - 1])
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
        schedule_pairs = [
            pair
            for pair in consecutive_pairs
            if pair[0]["current_completion_month"] is not None
            and pair[1]["current_completion_month"] is not None
        ]
        latest = observations[-1]
        flags = ["milestone_sample_not_complete_monthly_panel"]
        if disappearances:
            flags.append("interval_disappearance_exit_cause_unknown")
        if reentries:
            flags.append("milestone_reentry_observed")
        if observations[0]["threshold_regime"] == "cad_20m_and_over":
            flags.append("first_observed_after_threshold_change")
        lifecycle_rows.append(
            {
                "project_id": project_id,
                "source_record_id": latest["source_record_id"],
                "latest_project_name": latest["project_name"],
                "latest_asset_class": latest["asset_class"],
                "first_observed_snapshot": observations[0]["snapshot_date"],
                "last_observed_snapshot": latest["snapshot_date"],
                "observed_milestone_count": len(observations),
                "present_in_latest_snapshot": presence[-1],
                "observed_pre_threshold": any(
                    item["threshold_regime"] == "cad_50m_and_over" for item in observations
                ),
                "observed_post_threshold": any(
                    item["threshold_regime"] == "cad_20m_and_over" for item in observations
                ),
                "interval_disappearance_count": disappearances,
                "milestone_reentry_count": reentries,
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
                "comparable_completion_pair_count": len(schedule_pairs),
                "completion_month_change_pair_count": sum(
                    1
                    for previous, current in schedule_pairs
                    if current["current_completion_month"]
                    != previous["current_completion_month"]
                ),
                "presence_pattern": "".join("1" if item else "0" for item in presence),
                "source_id": "QUEBEC_PQI_PROJECT_DASHBOARD",
                "quality_flags": "|".join(flags),
            }
        )

    snapshot_output_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(snapshot_output_path, snapshot_rows)
    _write_csv(lifecycle_output_path, lifecycle_rows)

    last_pre = next(
        item for item in reversed(vintage_summaries) if item["threshold_regime"] == "cad_50m_and_over"
    )
    first_post = next(
        item for item in vintage_summaries if item["threshold_regime"] == "cad_20m_and_over"
    )
    ids_by_date = {
        snapshot_date: {
            row["project_id"] for row in snapshot_rows if row["snapshot_date"] == snapshot_date
        }
        for snapshot_date in snapshot_dates
    }
    last_pre_ids = ids_by_date[last_pre["snapshot_date"]]
    first_post_ids = ids_by_date[first_post["snapshot_date"]]
    result = {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "contract_id": contract["contract_id"],
        "contract_sha256": sha256_file(contract_path),
        "vintage_count": len(vintage_summaries),
        "snapshot_start_date": snapshot_dates[0],
        "snapshot_end_date": snapshot_dates[-1],
        "snapshot_observation_count": len(snapshot_rows),
        "unique_project_count": len(lifecycle_rows),
        "latest_snapshot_project_count": vintage_summaries[-1]["project_count"],
        "present_in_latest_project_count": sum(
            1 for row in lifecycle_rows if row["present_in_latest_snapshot"]
        ),
        "absent_from_latest_project_count": sum(
            1 for row in lifecycle_rows if not row["present_in_latest_snapshot"]
        ),
        "project_with_interval_disappearance_count": sum(
            1 for row in lifecycle_rows if row["interval_disappearance_count"] > 0
        ),
        "project_with_milestone_reentry_count": sum(
            1 for row in lifecycle_rows if row["milestone_reentry_count"] > 0
        ),
        "threshold_transition": {
            "last_pre_threshold_snapshot": last_pre["snapshot_date"],
            "last_pre_threshold_project_count": len(last_pre_ids),
            "first_post_threshold_snapshot": first_post["snapshot_date"],
            "first_post_threshold_project_count": len(first_post_ids),
            "continuing_project_count": len(last_pre_ids & first_post_ids),
            "newly_observed_project_count": len(first_post_ids - last_pre_ids),
            "no_longer_observed_project_count": len(last_pre_ids - first_post_ids),
            "interpretation": "The newly observed count combines threshold expansion and other entry; it is not a pure treatment cohort.",
        },
        "linked_change_diagnostics": {
            "consecutive_observation_pair_count": sum(
                int(row["consecutive_observation_pair_count"]) for row in lifecycle_rows
            ),
            "comparable_cost_pair_count": sum(
                int(row["comparable_cost_pair_count"]) for row in lifecycle_rows
            ),
            "authorized_cost_change_pair_count": sum(
                int(row["authorized_cost_change_pair_count"]) for row in lifecycle_rows
            ),
            "comparable_completion_pair_count": sum(
                int(row["comparable_completion_pair_count"]) for row in lifecycle_rows
            ),
            "completion_month_change_pair_count": sum(
                int(row["completion_month_change_pair_count"]) for row in lifecycle_rows
            ),
        },
        "vintages": vintage_summaries,
        "outputs": {
            "snapshot_csv": repository_path(snapshot_output_path),
            "snapshot_csv_sha256": sha256_file(snapshot_output_path),
            "lifecycle_csv": repository_path(lifecycle_output_path),
            "lifecycle_csv_sha256": sha256_file(lifecycle_output_path),
        },
        "limitations": [
            "Ten milestone snapshots do not reproduce every change observable in the complete 69-CSV catalog.",
            "A project disappearing between milestones may be completed, cancelled, renamed, merged, fall outside publication scope or otherwise leave the dashboard; exit cause is not inferred.",
            "The November 2020 change from a CAD 50 million to CAD 20 million threshold confounds threshold entry with other project entry.",
            "Current authorized cost is not final audited outturn and has no common estimate price-basis date.",
            "No AI treatment is present, so no AI-attributable effect is estimated.",
        ],
        "publication_boundary": {
            "complete_longitudinal_panel_authorized": False,
            "project_exit_outcome_authorized": False,
            "public_project_cost_outcome_authorized": False,
            "public_project_schedule_outcome_authorized": False,
            "ai_attributable_effect_authorized": False,
            "status": "milestone_longitudinal_research_candidate",
            "reason": "The milestone panel reveals stable-ID presence and authorized-field changes across ten official snapshots, but it is not the full monthly catalog, exit causes are unknown, the publication threshold changed, and authorized parameters are not final outturns.",
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _verify_vintage(
    archive_path: Path, manifest_path: Path, vintage: dict[str, Any]
) -> None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read Quebec vintage manifest: {exc}") from exc
    actual_hash = sha256_file(archive_path)
    if actual_hash != vintage.get("content_hash") or manifest.get("content_hash") != actual_hash:
        raise ValidationError(f"Quebec vintage hash mismatch: {vintage.get('snapshot_date')}")
    if manifest.get("resource_id") != vintage.get("resource_id"):
        raise ValidationError(f"Quebec vintage resource ID mismatch: {vintage.get('snapshot_date')}")
    if manifest.get("snapshot_date") != vintage.get("snapshot_date"):
        raise ValidationError(f"Quebec vintage snapshot date mismatch: {vintage.get('snapshot_date')}")
    if manifest.get("row_count") != vintage.get("row_count"):
        raise ValidationError(f"Quebec vintage row count mismatch: {vintage.get('snapshot_date')}")


def _read_snapshot(path: Path) -> tuple[list[dict[str, str]], int]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValidationError(f"Quebec vintage CSV has no header: {path.name}")
        normalized_fields = [field.strip() for field in reader.fieldnames]
        if len(normalized_fields) != len(set(normalized_fields)):
            raise ValidationError(f"Quebec vintage CSV has duplicate normalized fields: {path.name}")
        missing = REQUIRED_FIELDS - set(normalized_fields)
        if missing:
            raise ValidationError(
                f"Quebec vintage CSV is missing fields {sorted(missing)}: {path.name}"
            )
        rows = []
        for raw in reader:
            normalized = {
                str(key).strip(): (value or "").strip()
                for key, value in raw.items()
                if key is not None
            }
            rows.append(normalized)
    deduplicated: dict[str, dict[str, str]] = {}
    collapsed = 0
    for row in rows:
        project_id = row["no_projet"]
        if project_id not in deduplicated:
            deduplicated[project_id] = row
            continue
        previous = deduplicated[project_id]
        comparison_keys = (set(previous) | set(row)) - {"latitude", "longitude"}
        if any(previous.get(key, "") != row.get(key, "") for key in comparison_keys):
            raise ValidationError(
                f"Quebec vintage has conflicting duplicate project ID {project_id!r}: {path.name}"
            )
        collapsed += 1
    return list(deduplicated.values()), collapsed


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValidationError(f"cannot write empty Quebec longitudinal output: {path.name}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
