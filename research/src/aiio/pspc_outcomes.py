from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .schemas import ValidationError


MODEL_ID = "AIIO_PSPC_REAL_PROPERTY_OUTCOME_FEASIBILITY_0_1"
SOURCE_ID = "PSPC_REAL_PROPERTY_PROJECT_PERFORMANCE_2024_2025"
SOURCE_FIELDS = {
    "Fscl-yr_Ex-fin", "Project-nbr_No-de-projet", "On-time_Respect-des-delais",
    "On-budget_Respect-du-budget", "On-scope_Respect-de-la-portee",
    "Overall-project-health_Sante-globale-du-projet",
}
OUTPUT_FIELDS = ["record_id", "fiscal_year", "on_time_status", "on_budget_status", "on_scope_status", "overall_health_status", "source_id", "evidence_status", "quality_flags"]


def normalize_pspc_outcomes(input_path: Path, output_csv_path: Path, output_json_path: Path) -> dict[str, Any]:
    manifest_path = input_path.with_suffix(input_path.suffix + ".manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_id") != SOURCE_ID or manifest.get("content_hash") != "sha256:" + _sha(input_path):
        raise ValidationError("PSPC outcome retrieval manifest mismatch")
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or []) != SOURCE_FIELDS: raise ValidationError("PSPC outcome schema drift")
        source_rows = list(reader)
    if not source_rows: raise ValidationError("PSPC outcome file is empty")
    rows = []
    for row in source_rows:
        values = [row[field] for field in SOURCE_FIELDS if field not in {"Fscl-yr_Ex-fin", "Project-nbr_No-de-projet"}]
        if any(value not in {"1", "2", "3"} for value in values): raise ValidationError("PSPC outcome status code drift")
        rows.append({
            "record_id": row["Project-nbr_No-de-projet"], "fiscal_year": row["Fscl-yr_Ex-fin"],
            "on_time_status": row["On-time_Respect-des-delais"], "on_budget_status": row["On-budget_Respect-du-budget"],
            "on_scope_status": row["On-scope_Respect-de-la-portee"], "overall_health_status": row["Overall-project-health_Sante-globale-du-projet"],
            "source_id": SOURCE_ID, "evidence_status": "observed_ordinal_project_status",
            "quality_flags": "publisher_project_identity_anonymized|geography_missing|asset_class_missing|cost_and_date_values_missing",
        })
    if len({row["record_id"] for row in rows}) != len(rows): raise ValidationError("PSPC outcome record IDs are duplicated")
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    report = {
        "schema_version": "1.0.0", "model_id": MODEL_ID, "status": "aggregate_outcome_context_only",
        "record_count": len(rows), "fiscal_years": sorted({row["fiscal_year"] for row in rows}),
        "status_counts": {field: dict(sorted(Counter(row[field] for row in rows).items())) for field in ["on_time_status", "on_budget_status", "on_scope_status", "overall_health_status"]},
        "field_availability": {"ordinal_time_budget_scope_health": True, "stable_cross_year_project_id": False, "geography_id": False, "asset_class": False, "baseline_and_actual_dates": False, "estimate_and_outturn_cost": False},
        "input_sha256": "sha256:" + _sha(input_path), "retrieval_manifest_sha256": "sha256:" + _sha(manifest_path),
        "output_path": "data/processed/pspc_real_property_outcome_context_2024_2025.csv", "output_sha256": "sha256:" + _sha(output_csv_path),
        "publication_boundary": {"aggregate_delivery_risk_context_authorized": True, "project_outcome_authorized": False, "panel_linkage_authorized": False, "causal_effect_authorized": False, "reason": "The public file provides anonymous ordinal statuses without geography, asset class, cost values, schedule dates or stable longitudinal project identity."},
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
