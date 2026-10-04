"""Immutable project observations, with conservative stable-ID reconciliation.

Capture/verification time is not observation time. Repeated normalized content is
one observation even when fetched again. Absence only records a coverage change.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

from .schemas import ValidationError

CHANGE_FIELDS = ("estimated_cost_cad", "stage", "start_period", "completion_period", "name", "asset_class")


def reconcile_snapshots(before: list[dict[str, str]], after: list[dict[str, str]]) -> list[dict[str, Any]]:
    def indexed(rows):
        result = {}
        for row in rows:
            key = (row["source_id"], row["source_record_id"])
            if not all(key) or key in result:
                raise ValidationError(f"missing or duplicate stable source project ID: {key}")
            date.fromisoformat(row["source_as_of_date"])
            result[key] = row
        return result
    previous, current = indexed(before), indexed(after)
    events = []
    for key in sorted(previous.keys() | current.keys()):
        old, new = previous.get(key), current.get(key)
        if old is None or new is None:
            events.append({"source_id": key[0], "source_record_id": key[1],
                           "event_type": "first_observed" if old is None else "not_in_later_inventory",
                           "completion_inferred": False, "causal_claim": False})
            continue
        changes = {field: {"before": old.get(field, ""), "after": new.get(field, "")}
                   for field in CHANGE_FIELDS if old.get(field, "") != new.get(field, "")}
        if changes:
            later = new["source_as_of_date"] > old["source_as_of_date"]
            events.append({"source_id": key[0], "source_record_id": key[1],
                           "event_type": "inventory_field_revision" if later else "undated_or_same_vintage_conflict",
                           "before_observation_date": old["source_as_of_date"],
                           "after_observation_date": new["source_as_of_date"], "changes": changes,
                           "eligible_dated_revision": later,
                           "scope_price_basis_reconciliation": "pending" if "estimated_cost_cad" in changes else "not_applicable",
                           "final_cost_outturn": False, "completion_inferred": False, "causal_claim": False})
    return events


def retain_snapshot(rows: list[dict[str, str]], archive: Path) -> dict[str, Any]:
    # snapshot_date in old callers meant build time; it must never create history.
    observations = [{key: value for key, value in row.items() if key != "snapshot_date"} for row in rows]
    observations.sort(key=lambda row: (row["source_id"], row["source_record_id"]))
    reconcile_snapshots([], observations)  # validate stable IDs and source observation dates
    payload = json.dumps(observations, sort_keys=True, separators=(",", ":")) + "\n"
    semantic = [{key: value for key, value in row.items() if key != "source_as_of_date"}
                for row in observations]
    digest = hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    archive.mkdir(parents=True, exist_ok=True)
    path = archive / f"{digest}.json"
    if path.exists():
        retained = json.loads(path.read_text())
        retained_semantic = [{key: value for key, value in row.items() if key != "source_as_of_date"}
                             for row in retained]
        if retained_semantic != semantic:
            raise ValidationError("immutable snapshot hash/content mismatch")
        observations = retained
    else:
        path.write_text(payload, encoding="utf-8")
    return {"observation_hash": "sha256:" + digest,
            "observation_dates": sorted({row["source_as_of_date"] for row in observations}),
            "archive_file": path.name,
            "archive_content_hash": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            "repeated_fetch_is_new_observation": False,
            "disappearance_implies_completion": False}


def build_history(archive: Path) -> dict[str, Any]:
    """Summarize per-source histories; mixed province dates cannot order a panel."""
    sources: dict[str, dict[str, list[dict[str, str]]]] = {}
    for path in sorted(archive.glob("*.json")):
        rows = json.loads(path.read_text())
        groups: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            groups.setdefault(row["source_id"], []).append(row)
        for source, observations in groups.items():
            content = json.dumps([{key: value for key, value in row.items() if key != "source_as_of_date"}
                                  for row in observations], sort_keys=True)
            digest = hashlib.sha256(content.encode()).hexdigest()
            existing = sources.setdefault(source, {}).get(digest)
            if existing is None or max(row["source_as_of_date"] for row in observations) < max(row["source_as_of_date"] for row in existing):
                sources[source][digest] = observations
    results = {}
    for source, vintages in sorted(sources.items()):
        ordered = sorted(vintages.values(), key=lambda rows: max(row["source_as_of_date"] for row in rows))
        events = []
        for before, after in zip(ordered, ordered[1:]):
            events.extend(reconcile_snapshots(before, after))
        dates = sorted({row["source_as_of_date"] for rows in ordered for row in rows})
        results[source] = {"distinct_content_count": len(ordered), "source_observation_dates": dates,
                           "dated_vintage_count": len(dates), "reconciled_events": events,
                           "outcome_status": "revisions_require_scope_review" if len(dates) > 1 else "baseline_only_no_longitudinal_outcome"}
    return {"schema_version": "1.0.0", "sources": results, "ai_attributable_effect_authorized": False}
