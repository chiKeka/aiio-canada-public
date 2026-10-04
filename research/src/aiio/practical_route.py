from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .schemas import ValidationError
from .planning_validation import assess_proxy_planning
from .project_longitudinal import retain_snapshot, build_history


RUN_ID = "AIIO_PRACTICAL_EVIDENCE_ROUTE_0_1"
TARGET_ASSETS = {"health_facilities", "schools_and_postsecondary", "government_and_civic_facilities"}
SNAPSHOT_FIELDS = [
    "snapshot_date", "project_id", "source_record_id", "name", "geography_id", "province",
    "municipality", "asset_class", "stage", "estimated_cost_cad", "start_period",
    "completion_period", "source_id", "source_as_of_date", "source_evidence_status",
]


def build_practical_evidence_route(
    root: Path,
    as_of: str,
    treatment_proxy_path: Path,
    public_projects_path: Path,
    revision_events_path: Path,
    snapshot_output_path: Path,
    report_output_path: Path,
) -> dict[str, Any]:
    try:
        date.fromisoformat(as_of)
    except ValueError as exc:
        raise ValidationError(f"as_of must be an ISO date: {as_of!r}") from exc

    treatment = _rows(treatment_proxy_path)
    projects = _rows(public_projects_path)
    events = _rows(revision_events_path)

    treatment_geographies: dict[str, set[str]] = defaultdict(set)
    positive_cells = 0
    for row in treatment:
        positive = float(row["reconstructed_proxy_central_cad"]) > 0
        if positive:
            positive_cells += 1
            treatment_geographies[row["geography_id"]].add(row["quarter"])

    # Alberta's stable official project IDs join the prospective comparator inventory.
    # Preserve the publisher vintage; the weekly build date is not an observation.
    alberta_path = root / "data/processed/public_project_exposure_alberta.csv"
    if alberta_path.exists():
        for row in _rows(alberta_path):
            projects.append({**row, "source_record_id": row["project_id"].removeprefix("ABMP_"),
                             "geography_id": "PR_48", "province": "Alberta",
                             "start_period": row.get("start_year", ""),
                             "completion_period": row.get("end_year", "")})
    target_projects = [row for row in projects if row["asset_class"] in TARGET_ASSETS]
    snapshot_rows = [
        {
            "snapshot_date": row["as_of_date"],
            "project_id": row["project_id"],
            "source_record_id": row["source_record_id"],
            "name": row["name"],
            "geography_id": row["geography_id"],
            "province": row["province"],
            "municipality": row["municipality"],
            "asset_class": row["asset_class"],
            "stage": row["stage"],
            "estimated_cost_cad": row["estimated_cost_cad"],
            "start_period": row["start_period"],
            "completion_period": row["completion_period"],
            "source_id": row["source_id"],
            "source_as_of_date": row["as_of_date"],
            "source_evidence_status": row["source_evidence_status"],
        }
        for row in sorted(target_projects, key=lambda item: (item["province"], item["project_id"]))
    ]
    snapshot_output_path.parent.mkdir(parents=True, exist_ok=True)
    with snapshot_output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SNAPSHOT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(snapshot_rows)

    archive = root / "data/processed/public_project_snapshots"
    snapshot_receipt = retain_snapshot(snapshot_rows, archive)
    longitudinal_report = build_history(archive)
    comparator_path = root / "data/model-runs/quebec_pqi_full_archive_longitudinal_v0.1.json"
    if comparator_path.exists():
        comparator = json.loads(comparator_path.read_text())
        longitudinal_report["existing_comparator_archive"] = {
            "province": "Quebec", "report_path": str(comparator_path.relative_to(root)),
            "report_hash": "sha256:" + hashlib.sha256(comparator_path.read_bytes()).hexdigest(),
            "limitations": comparator["limitations"],
            "publication_boundary": comparator["publication_boundary"],
            "linked_change_diagnostics": comparator["linked_change_diagnostics"],
        }
    longitudinal_report["alberta_outcome_gap"] = "Released Alberta evidence has one capture. Review candidate observations are not released outcomes; inventory capture dates are not revision effective dates."
    longitudinal_path = root / "data/model-runs/public_project_longitudinal_current.json"
    longitudinal_path.write_text(json.dumps(longitudinal_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    quarterly_revisions: dict[tuple[str, str, str, str, str], list[float]] = defaultdict(list)
    for row in events:
        if row["asset_class"] not in TARGET_ASSETS or row["arithmetic_reconciles"] != "True":
            continue
        quarter = _month_quarter(row["effective_month"])
        quarterly_revisions[(
            row["geography_id"], row["asset_class"], quarter, row["event_type"], row["unit"]
        )].append(float(row["change_value"]))
    revision_cells = []
    for (geography, asset, quarter, event_type, unit), values in sorted(quarterly_revisions.items()):
        revision_cells.append({
            "geography_id": geography,
            "asset_class": asset,
            "quarter": quarter,
            "event_type": event_type,
            "unit": unit,
            "revision_event_count": len(values),
            "net_authorized_change": round(sum(values), 2),
            "median_authorized_change": round(statistics.median(values), 2),
        })

    project_provinces = sorted({row["province"] for row in snapshot_rows})
    project_assets = sorted({row["asset_class"] for row in snapshot_rows})
    event_geographies = sorted({row["geography_id"] for row in revision_cells})
    treatment_ready_as_proxy = len(treatment_geographies) >= 2 and positive_cells > 0
    prospective_baseline_ready = len(project_provinces) >= 3 and len(project_assets) >= 2
    revision_estimand_ready = len(event_geographies) >= 2 and len({row["asset_class"] for row in revision_cells}) >= 2

    report = {
        "proxy_planning_validation": assess_proxy_planning(root),
        "schema_version": "1.0.0",
        "run_id": RUN_ID,
        "as_of_date": as_of,
        "status": "pipeline_operational_evidence_accumulating",
        "tracks": {
            "reconstructed_quarterly_treatment": {
                "status": "implemented_non_authorizing_proxy" if treatment_ready_as_proxy else "insufficient_proxy_coverage",
                "geography_count": len(treatment_geographies),
                "positive_geography_quarter_count": positive_cells,
                "geography_quarter_coverage": {key: len(value) for key, value in sorted(treatment_geographies.items())},
                "authorizing_treatment": False,
            },
            "prospective_public_project_tracking": {
                "status": "baseline_snapshot_ready" if prospective_baseline_ready else "insufficient_baseline_coverage",
                "project_count": len(snapshot_rows),
                "province_count": len(project_provinces),
                "provinces": project_provinces,
                "asset_classes": project_assets,
                "snapshot_path": str(snapshot_output_path.relative_to(root)),
                "immutable_observation": snapshot_receipt,
                "longitudinal_report_path": str(longitudinal_path.relative_to(root)),
                "next_observation_required": "A later official snapshot with the same stable project IDs, followed by reconciled estimate, stage and schedule changes.",
            },
            "authorized_revision_estimand": {
                "estimand": "quarterly change in publisher-authorized project cost or completion plan",
                "status": "eligible_for_preregistered_multi_region_analysis" if revision_estimand_ready else "single_region_descriptive_reference",
                "quarter_asset_cell_count": len(revision_cells),
                "geography_count": len(event_geographies),
                "geographies": event_geographies,
                "cells": revision_cells,
                "final_cost_outturn": False,
                "ai_attributable_effect_authorized": False,
            },
        },
        "gate_evaluation": {
            "proxy_route_implemented": treatment_ready_as_proxy,
            "prospective_baseline_implemented": prospective_baseline_ready,
            "multi_region_revision_outcome_available": revision_estimand_ready,
            "original_authorizing_evidence_gate_satisfied": False,
            "narrow_revision_estimand_authorized": False,
            "remaining_p0": [
                "Acquire a second region with stable-ID authorized cost or completion revisions.",
                "Accumulate at least eight pre-event and four post-event quarters in treated and control regions.",
                "Reconcile price basis and approved changes where the outcome is expressed in CAD.",
                "Complete independent parser and modelling review before publishing an attributable result.",
            ],
        },
        "input_manifest": {
            str(path.relative_to(root)): "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (treatment_proxy_path, public_projects_path, revision_events_path, *([alberta_path] if alberta_path.exists() else []))
        },
        "output_manifest": {
            str(snapshot_output_path.relative_to(root)): "sha256:" + hashlib.sha256(snapshot_output_path.read_bytes()).hexdigest()
        },
        "publication_boundary": {
            "decision_grade_ready": False,
            "proxy_results_may_be_displayed": True,
            "authorized_revisions_may_be_described": True,
            "authorized_revisions_must_not_be_labelled_final_outturn": True,
            "causal_or_ai_attributable_claim": False,
        },
    }
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValidationError(f"practical-route input is empty: {path}")
    return rows


def _month_quarter(value: str) -> str:
    if len(value) != 7:
        raise ValidationError(f"revision effective_month is invalid: {value!r}")
    return f"{value[:4]}-Q{(int(value[5:7]) - 1) // 3 + 1}"
