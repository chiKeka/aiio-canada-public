from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .paths import repository_path
from .quebec_revisions import REQUIRED_FIELDS, _sha256_text
from .schemas import ValidationError


PACKAGE_ID = "AIIO_QUEBEC_PQI_PARSER_REVIEW_PACKAGE_0_1"
SOURCE_ID = "QUEBEC_PQI_PROJECT_DASHBOARD"
REVIEW_STATUS = "pending_independent_review"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def build_quebec_parser_review_package(
    dashboard_csv_path: Path,
    revision_report_path: Path,
    summary_csv_path: Path,
    event_csv_path: Path,
    longitudinal_report_path: Path,
    lifecycle_csv_path: Path,
    review_csv_path: Path,
    package_json_path: Path,
) -> dict[str, Any]:
    revision_report = _read_json(revision_report_path, "Quebec revision report")
    longitudinal_report = _read_json(
        longitudinal_report_path, "Quebec longitudinal report"
    )
    _verify_report_output(
        revision_report,
        "summary_csv_sha256",
        summary_csv_path,
        "revision summary",
    )
    _verify_report_output(
        revision_report,
        "event_csv_sha256",
        event_csv_path,
        "revision events",
    )
    _verify_report_output(
        longitudinal_report,
        "lifecycle_csv_sha256",
        lifecycle_csv_path,
        "longitudinal lifecycle",
    )
    if revision_report.get("publication_boundary", {}).get(
        "authorized_revision_reference_panel_authorized"
    ) is not False:
        raise ValidationError("Quebec revision report must remain unauthorized")
    if longitudinal_report.get("publication_boundary", {}).get(
        "complete_longitudinal_panel_authorized"
    ) is not False:
        raise ValidationError("Quebec longitudinal report must remain unauthorized")

    source_manifest_path = dashboard_csv_path.with_suffix(
        dashboard_csv_path.suffix + ".manifest.json"
    )
    source_manifest = _read_json(source_manifest_path, "Quebec dashboard manifest")
    source_hash = sha256_file(dashboard_csv_path)
    if source_manifest.get("source_id") != SOURCE_ID:
        raise ValidationError("Quebec dashboard manifest source ID mismatch")
    if source_manifest.get("content_hash") != source_hash:
        raise ValidationError("Quebec dashboard manifest hash mismatch")

    raw_rows = _read_csv(dashboard_csv_path)
    if not raw_rows or not REQUIRED_FIELDS.issubset(raw_rows[0]):
        raise ValidationError("Quebec dashboard review source schema mismatch")
    raw_by_id = _unique_by(raw_rows, "no_projet", "Quebec dashboard source")
    summary_by_id = _unique_by(
        _read_csv(summary_csv_path), "source_record_id", "Quebec revision summary"
    )
    lifecycle_by_id = _unique_by(
        _read_csv(lifecycle_csv_path), "source_record_id", "Quebec lifecycle"
    )
    event_rows = _read_csv(event_csv_path)
    events_by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    for event in event_rows:
        events_by_project[event["project_id"]].append(event)

    if set(summary_by_id) != set(raw_by_id):
        raise ValidationError("Quebec revision summary does not cover the source rows")

    selected_reasons: dict[str, set[str]] = defaultdict(set)

    def select(source_record_id: str, reason: str) -> None:
        if source_record_id not in summary_by_id:
            raise ValidationError(
                f"review selection references unknown source record {source_record_id}"
            )
        selected_reasons[source_record_id].add(reason)

    summaries = list(summary_by_id.values())
    for row in summaries:
        if _as_int(row["cost_revision_event_count"]) and not _as_bool(
            row["cost_revision_chain_reconciles"]
        ):
            select(row["source_record_id"], "all_unreconciled_cost_chains")
        if _as_int(row["schedule_revision_event_count"]) and not _as_bool(
            row["schedule_revision_chain_reconciles"]
        ):
            select(row["source_record_id"], "all_unreconciled_schedule_chains")

    asset_classes = sorted({row["asset_class"] for row in summaries})
    for asset_class in asset_classes:
        members = [row for row in summaries if row["asset_class"] == asset_class]
        for row in _stable_take(
            [item for item in members if _as_bool(item["cost_revision_chain_reconciles"])],
            2,
        ):
            select(row["source_record_id"], f"reconciled_cost_asset_class:{asset_class}")
        for row in _stable_take(
            [
                item
                for item in members
                if _as_bool(item["schedule_revision_chain_reconciles"])
            ],
            2,
        ):
            select(
                row["source_record_id"],
                f"reconciled_schedule_asset_class:{asset_class}",
            )
        for row in _stable_take(
            [
                item
                for item in members
                if _as_int(item["cost_revision_event_count"]) == 0
                and _as_int(item["schedule_revision_event_count"]) == 0
            ],
            1,
        ):
            select(row["source_record_id"], f"no_parsed_revision_control:{asset_class}")

    cost_rows = [
        row
        for row in summaries
        if _as_bool(row["cost_revision_chain_reconciles"])
        and row["authorized_cost_variance_percent"]
    ]
    for row in sorted(
        (item for item in cost_rows if float(item["authorized_cost_variance_percent"]) < 0),
        key=lambda item: (float(item["authorized_cost_variance_percent"]), item["project_id"]),
    )[:5]:
        select(row["source_record_id"], "largest_authorized_cost_decreases")
    for row in sorted(
        cost_rows,
        key=lambda item: (-float(item["authorized_cost_variance_percent"]), item["project_id"]),
    )[:5]:
        select(row["source_record_id"], "largest_authorized_cost_increases")

    schedule_rows = [
        row
        for row in summaries
        if _as_bool(row["schedule_revision_chain_reconciles"])
        and row["authorized_schedule_change_months"]
    ]
    for row in sorted(
        schedule_rows,
        key=lambda item: (float(item["authorized_schedule_change_months"]), item["project_id"]),
    )[:5]:
        select(row["source_record_id"], "largest_authorized_schedule_advances")
    for row in sorted(
        schedule_rows,
        key=lambda item: (-float(item["authorized_schedule_change_months"]), item["project_id"]),
    )[:5]:
        select(row["source_record_id"], "largest_authorized_schedule_delays")

    for row in _stable_take(
        [item for item in summaries if _as_int(item["ambiguous_schedule_event_count"])],
        5,
    ):
        select(row["source_record_id"], "ambiguous_multi_date_schedule_text")
    for row in _stable_take(
        [item for item in summaries if item["actual_completion_fiscal_year"]], 5
    ):
        select(row["source_record_id"], "actual_completion_fiscal_year_marker")

    for row in lifecycle_by_id.values():
        if (
            _as_int(row["milestone_reentry_count"])
            and row["source_record_id"] in summary_by_id
        ):
            select(row["source_record_id"], "all_milestone_reentries")

    review_rows: list[dict[str, Any]] = []
    for sample_index, source_record_id in enumerate(sorted(selected_reasons), start=1):
        raw = raw_by_id[source_record_id]
        summary = summary_by_id[source_record_id]
        lifecycle = lifecycle_by_id.get(source_record_id, {})
        project_events = sorted(
            events_by_project.get(summary["project_id"], []),
            key=lambda item: (
                item["effective_month"], item["event_type"], item["revision_event_id"]
            ),
        )
        history_text = raw.get("suivi_modifications", "")
        review_rows.append(
            {
                "sample_id": f"QCPQIREVIEW_{sample_index:03d}",
                "selection_reasons": "|".join(sorted(selected_reasons[source_record_id])),
                "source_record_id": source_record_id,
                "project_id": summary["project_id"],
                "project_name": summary["project_name"],
                "asset_class": summary["asset_class"],
                "source_category": summary["source_category"],
                "source_row_locator": f"no_projet={source_record_id}",
                "source_snapshot_date": revision_report["source_as_of_date"],
                "source_file_sha256": source_hash,
                "history_text_sha256": _sha256_text(history_text),
                "source_history_text": history_text,
                "parsed_cost_revision_event_count": summary["cost_revision_event_count"],
                "parsed_cost_chain_reconciles": summary[
                    "cost_revision_chain_reconciles"
                ],
                "parsed_baseline_authorized_cost_cad": summary[
                    "baseline_authorized_cost_cad"
                ],
                "parsed_current_authorized_cost_cad": summary[
                    "current_authorized_cost_cad"
                ],
                "parsed_authorized_cost_variance_percent": summary[
                    "authorized_cost_variance_percent"
                ],
                "parsed_schedule_revision_event_count": summary[
                    "schedule_revision_event_count"
                ],
                "parsed_schedule_chain_reconciles": summary[
                    "schedule_revision_chain_reconciles"
                ],
                "parsed_baseline_completion_month": summary[
                    "baseline_completion_month"
                ],
                "parsed_current_completion_month": summary[
                    "current_completion_month"
                ],
                "parsed_authorized_schedule_change_months": summary[
                    "authorized_schedule_change_months"
                ],
                "parsed_ambiguous_schedule_event_count": summary[
                    "ambiguous_schedule_event_count"
                ],
                "parsed_actual_completion_fiscal_year": summary[
                    "actual_completion_fiscal_year"
                ],
                "parsed_events_json": json.dumps(
                    project_events, ensure_ascii=False, sort_keys=True
                ),
                "milestone_presence_pattern": lifecycle.get("presence_pattern", ""),
                "milestone_reentry_count": lifecycle.get("milestone_reentry_count", ""),
                "reviewer_name": "",
                "review_date": "",
                "review_status": "",
                "review_notes": "",
                "reviewed_cost_event_count": "",
                "reviewed_cost_chain_reconciles": "",
                "reviewed_schedule_event_count": "",
                "reviewed_schedule_chain_reconciles": "",
                "reviewed_completion_marker": "",
            }
        )

    if not review_rows:
        raise ValidationError("Quebec parser review sample cannot be empty")
    review_csv_path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(review_csv_path, review_rows)
    reason_counts: dict[str, int] = defaultdict(int)
    for reasons in selected_reasons.values():
        for reason in reasons:
            reason_counts[reason] += 1

    package = {
        "schema_version": "1.0.0",
        "package_id": PACKAGE_ID,
        "review_status": REVIEW_STATUS,
        "source_id": SOURCE_ID,
        "source_snapshot_date": revision_report["source_as_of_date"],
        "source_file_sha256": source_hash,
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "revision_report_sha256": sha256_file(revision_report_path),
        "longitudinal_report_sha256": sha256_file(longitudinal_report_path),
        "sample_project_count": len(review_rows),
        "source_project_count": len(summary_by_id),
        "sampling_fraction": len(review_rows) / len(summary_by_id),
        "selection_reason_counts": dict(sorted(reason_counts.items())),
        "review_output": {
            "path": repository_path(review_csv_path),
            "content_hash": sha256_file(review_csv_path),
        },
        "review_protocol": [
            "Compare source_history_text against the parsed event JSON and summary fields.",
            "Record a reviewer identity, review date, status, reviewed counts and notes in the blank review columns.",
            "Treat disagreements as parser defects or documented exclusions; do not silently overwrite source text.",
            "Re-run this deterministic package after parser or source-vintage changes.",
        ],
        "limitations": [
            "The package is a deterministic stratified review sample, not a completed independent review.",
            "Sampling emphasizes parser edge cases and is not an estimator of population error without design weights.",
            "The current dashboard remains a survivor snapshot; milestone reentries are included only where the source ID is present in the current snapshot.",
        ],
        "publication_boundary": {
            "independent_parser_review_complete": False,
            "parser_authorized_for_decision_use": False,
            "authorized_revision_reference_panel_authorized": False,
            "public_project_cost_outcome_authorized": False,
            "public_project_schedule_outcome_authorized": False,
            "ai_attributable_effect_authorized": False,
            "status": REVIEW_STATUS,
            "reason": "The review workbook is populated with source evidence and deterministic selections, but all reviewer fields are blank and no independent review has been completed.",
        },
    }
    package_json_path.parent.mkdir(parents=True, exist_ok=True)
    package_json_path.write_text(
        json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return package


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be an object")
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValidationError(f"CSV has no header: {path.name}")
            return [
                {str(key).strip(): (value or "").strip() for key, value in row.items()}
                for row in reader
            ]
    except OSError as exc:
        raise ValidationError(f"unable to read CSV {path.name}: {exc}") from exc


def _unique_by(
    rows: list[dict[str, str]], key: str, label: str
) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "").strip()
        if not value:
            raise ValidationError(f"{label} contains a blank {key}")
        if value in output:
            raise ValidationError(f"{label} contains duplicate {key}={value}")
        output[value] = row
    return output


def _verify_report_output(
    report: dict[str, Any], hash_key: str, path: Path, label: str
) -> None:
    expected = report.get("outputs", {}).get(hash_key)
    if expected != sha256_file(path):
        raise ValidationError(f"{label} hash does not match its report")


def _as_bool(value: str) -> bool:
    if value not in {"True", "False"}:
        raise ValidationError(f"expected serialized boolean, got {value!r}")
    return value == "True"


def _as_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValidationError(f"expected integer, got {value!r}") from exc


def _stable_take(rows: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    return sorted(
        rows,
        key=lambda row: hashlib.sha256(row["project_id"].encode("utf-8")).hexdigest(),
    )[:count]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
