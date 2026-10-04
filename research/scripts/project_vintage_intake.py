#!/usr/bin/env python3
"""Prepare Alberta inventory changes for review without replacing released inputs."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from aiio.adapters.alberta_projects import normalize_major_projects
from aiio.project_longitudinal import reconcile_snapshots, retain_snapshot
from aiio.public_projects import run_public_project_exposure
from aiio.practical_route import TARGET_ASSETS
from aiio.schemas import ValidationError


def intake(root: Path, raw: Path, manifest: Path, output: Path):
    receipt = json.loads(manifest.read_text())
    digest = "sha256:" + hashlib.sha256(raw.read_bytes()).hexdigest()
    if receipt.get("source_id") != "ALBERTA_MAJOR_PROJECTS" or receipt.get("content_hash") != digest or receipt.get("result") != "success":
        raise ValidationError("Alberta capture receipt does not bind successful raw content")
    capture_date = receipt["retrieved_at"][:10]
    output.mkdir(parents=True, exist_ok=True)
    all_path, ai_path = output / "alberta_major_projects.csv", output / "alberta_ai_projects.csv"
    total, ai_total = normalize_major_projects(raw, all_path, ai_path, capture_date)
    exposure = output / "public_project_exposure_alberta.csv"
    run_public_project_exposure(all_path, output / "public_project_exposure_alberta.json", exposure)
    def rows(path):
        with path.open(newline="", encoding="utf-8") as handle:
            return [{**row, "source_record_id": row["project_id"].removeprefix("ABMP_"),
                     "source_as_of_date": row["as_of_date"], "start_period": row["start_year"],
                     "completion_period": row["end_year"]}
                    for row in csv.DictReader(handle) if row["asset_class"] in TARGET_ASSETS]
    baseline_path = root / "data/processed/public_project_exposure_alberta.csv"
    before, after = rows(baseline_path), rows(exposure)
    # Hash only the fields in the observational contract, avoiding derived annualization.
    fields = ("project_id", "source_record_id", "source_id", "source_as_of_date", "name", "asset_class", "stage", "estimated_cost_cad", "start_period", "completion_period")
    before = [{key: row[key] for key in fields} for row in before]
    after = [{key: row[key] for key in fields} for row in after]
    archive = output / "snapshots"
    first, latest = retain_snapshot(before, archive), retain_snapshot(after, archive)
    events = reconcile_snapshots(before, after)
    report = {"schema_version": "1.0.0", "status": "review_pending",
              "source_id": "ALBERTA_MAJOR_PROJECTS", "retrieved_at": receipt["retrieved_at"],
              "observation_date_basis": "inventory_observed_at_capture_not_publisher_revision_effective_date",
              "publisher_revision_effective_dates_available": False,
              "raw_content_hash": digest, "baseline_content_hash": "sha256:" + hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
              "normalized_project_count": total, "ai_screen_project_count": ai_total,
              "target_projects_before": len(before), "target_projects_after": len(after),
              "baseline_observation": first, "candidate_observation": latest,
              "events": events, "review_requirements": ["Review parser and source-scope continuity", "Reconcile cost price basis and scope", "Confirm milestone dates from project-specific evidence"],
              "publication_boundary": {"published_inputs_replaced": False, "observed_field_changes_are_final_outcomes": False, "causal_claim_authorized": False}}
    (output / "intake.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = intake(Path(__file__).resolve().parents[2], args.raw, args.manifest, args.output)
    print(json.dumps({"status": report["status"], "event_count": len(report["events"]), "project_count": report["normalized_project_count"]}))
