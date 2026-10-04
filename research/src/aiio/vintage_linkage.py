"""Audit archive availability and draft linkage without changing frozen models."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .planning_benchmark import CONTRACT as BENCHMARK_CONTRACT, quarter, quarter_label
from .proxy_treatment import _boundaries, _project_geography, _schedule_weights
from .schemas import ValidationError

CONTRACT = "data/model/vintage_linkage_audit_contract_v0.1.json"
OUTPUT = "data/model-runs/vintage_linkage_audit_v0.1.json"
PERMITS = "data/processed/edmonton_data_centre_permit_proxy.csv"
PROJECTS = "data/processed/alberta_ai_projects.csv"
PROXY = "data/processed/ai_construction_proxy_alberta_v0.1.csv"


def _digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _path(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValidationError("vintage audit path escapes repository")
    return path


def _csv(path, key):
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or len({r[key] for r in rows}) != len(rows):
        raise ValidationError("empty or duplicate source records")
    return rows


def _stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValidationError("archive retrieval timestamp requires timezone")
    return result


def inventory(root, manifest_paths, source):
    rows = []
    for name in manifest_paths:
        manifest = json.loads(_path(root, name).read_text())
        if manifest["source_id"] != source or manifest.get("result") != "success":
            raise ValidationError("archive source or retrieval status mismatch")
        _stamp(manifest["retrieved_at"])
        _path(root, manifest["archive_path"])
        rows.append({"manifest_path": name, "retrieved_at": manifest["retrieved_at"],
                     "content_hash": manifest["content_hash"], "archive_path": manifest["archive_path"]})
    if not rows:
        raise ValidationError("empty archive inventory")
    rows.sort(key=lambda row: _stamp(row["retrieved_at"]))
    return {"source_id": source, "retrieval_count": len(rows),
            "distinct_content_count": len({r["content_hash"] for r in rows}),
            "earliest_archived_retrieval": rows[0]["retrieved_at"], "retrievals": rows,
            "evidence_basis": "committed retrieval manifests; retrieval time is not publication time"}


def review_permits(permits, draft, start, end):
    included = {r["permit_proxy_id"]: r for r in permits
                if r["classification"] == "explicit_data_centre_reference"
                and "DEMOLITION" not in r["work_type"].upper()
                and r["reported_estimated_construction_value_cad"]
                and start <= r["issue_date"] <= end}
    if draft["status"] != "analyst_draft_independent_review_pending":
        raise ValidationError("audit cannot accept an authorizing review verdict")
    reviewed = draft["records"]
    if len(reviewed) != len(included) or {r["permit_proxy_id"] for r in reviewed} != set(included):
        raise ValidationError("draft review must cover every included permit exactly once")
    result = []
    for record in reviewed:
        source = included[record["permit_proxy_id"]]
        if any(record[key] != source[key] for key in ("source_row_id", "description_sha256")):
            raise ValidationError("review description or source ID drift")
        if record["facility_match_status"] != "candidate_unconfirmed" or record["independent_review_status"] != "pending":
            raise ValidationError("facility linkage must remain unconfirmed")
        if record["work_class"] not in {"maintenance", "fitout", "expansion"}:
            raise ValidationError("unsupported work classification")
        result.append({**record, "issue_date": source["issue_date"], "geography_id": "CMA_835",
                       "reported_value_cad": source["reported_estimated_construction_value_cad"],
                       "ai_specificity_status": source["ai_specificity_status"]})
    return sorted(result, key=lambda r: r["permit_proxy_id"])


def verify_local_archives(root, inventories, permit_review):
    """Verify local bytes, allowing identical-content archives to share a copy.

    Missing raw caches on a clean clone are never interpreted as verification.
    This optional check does not change the portable report's manifest-based facts.
    """
    raw_permits = None
    verified = 0
    for item in inventories:
        groups = defaultdict(list)
        for row in item["retrievals"]:
            groups[row["content_hash"]].append(_path(root, row["archive_path"]))
        for expected, paths in groups.items():
            available = [p for p in paths if p.is_file()]
            if not available:
                raise ValidationError("raw archive bytes unavailable for local verification")
            if any(_digest(p) != expected for p in available):
                raise ValidationError("raw archive hash drift")
            verified += 1
            if item["source_id"] == "EDMONTON_GENERAL_BUILDING_PERMITS":
                rows = json.loads(available[0].read_text())
                if len({r["row_id"] for r in rows}) != len(rows):
                    raise ValidationError("duplicate raw permit identifiers")
                raw_permits = {r["row_id"]: r for r in rows}
    if raw_permits is None:
        raise ValidationError("permit archive missing")
    from .adapters.edmonton_permits import clean_text
    for record in permit_review:
        raw = raw_permits.get(record["source_row_id"])
        if raw is None:
            raise ValidationError("review record not found in archive")
        description_hash = "sha256:" + hashlib.sha256(clean_text(raw.get("job_description")).encode()).hexdigest()
        if description_hash != record["description_sha256"]:
            raise ValidationError("raw description hash mismatch")
    return {"status": "verified", "unique_content_blobs": verified,
            "description_hashes_verified": len(permit_review), "classification_verdict": "independent_review_pending"}


def run_vintage_linkage(root: Path, output: Path | None = None, verify_raw: bool = False):
    contract = json.loads((root / CONTRACT).read_text())
    if contract["contract_id"] != "AIIO_VINTAGE_LINKAGE_AUDIT_0_1" or any(contract["publication_boundary"].values()):
        raise ValidationError("unsupported or authorizing vintage/linkage contract")
    for name, expected in contract["input_manifest"].items():
        path = _path(root, name)
        if not path.is_file() or _digest(path) != expected:
            raise ValidationError(f"vintage/linkage input drift: {name}")
    inventories = [inventory(root, paths, source) for source, paths in sorted(contract["snapshot_manifests"].items())]
    benchmark = json.loads((root / BENCHMARK_CONTRACT).read_text())
    first = quarter(benchmark["design"]["first_test_quarter"])
    last = quarter(benchmark["design"]["last_test_quarter"])
    origins = []
    for target in range(first, last + 1):
        origin_end = _boundaries(quarter_label(target - 1))[1]
        available = [item["source_id"] for item in inventories if item["earliest_archived_retrieval"][:10] <= origin_end]
        origins.append({"target_quarter": quarter_label(target), "forecast_origin_end": origin_end,
                        "sources_with_archived_snapshot_by_origin": available,
                        "status": "no_complete_point_in_time_evidence" if len(available) != len(inventories) else "archive_present_release_vintage_review_required"})
    with (root / PROXY).open(newline="") as handle:
        cells = list(csv.DictReader(handle))
    periods = sorted({r["quarter"] for r in cells})
    start, end = _boundaries(periods[0])[0], _boundaries(periods[-1])[1]
    permits = review_permits(_csv(root / PERMITS, "permit_proxy_id"), json.loads(_path(root, contract["review_path"]).read_text()), start, end)
    totals = defaultdict(Decimal)
    clusters = defaultdict(list)
    for record in permits:
        totals[record["work_class"]] += Decimal(record["reported_value_cad"])
        clusters[record["facility_candidate_id"]].append(record["permit_proxy_id"])
    projects, horizon_checks = [], []
    for row in _csv(root / PROJECTS, "project_id"):
        geography = _project_geography(row["municipality"])
        if row["ai_relevance"] != "core_data_centre" or row["stage"] != "Under Construction" or geography is None:
            continue
        complete = all(row[k] for k in ("start_year", "end_year", "estimated_cost_cad"))
        projects.append({"project_id": row["project_id"], "geography_id": geography,
                         "enters_dollar_proxy": complete, "permit_match": "no_confirmed_link"})
        if not complete:
            continue
        full = [quarter_label(q) for q in range(quarter(row["start_year"] + "-Q1"), quarter(row["end_year"] + "-Q4") + 1)]
        overlap = [q for q in full if q in periods]
        full_weights = _schedule_weights(len(full))
        full_sum = float(row["estimated_cost_cad"]) * sum(w for q, w in zip(full, full_weights) if q in periods)
        clipped_sum = float(row["estimated_cost_cad"]) if overlap else 0
        horizon_checks.append({"project_id": row["project_id"], "full_schedule_quarters": len(full),
                               "archived_proxy_window_quarters": len(overlap),
                               "v0_1_clipped_schedule_allocation_cad": round(clipped_sum, 2),
                               "full_schedule_denominator_allocation_cad": round(full_sum, 2),
                               "status": "truncated_schedule_denominator_requires_versioned_fix" if len(overlap) != len(full) else "full_schedule_within_window",
                               "model_modified": False})
    simultaneous = [r for r in cells if Decimal(r["project_schedule_proxy_cad"]) > 0 and Decimal(r["permit_activity_proxy_cad"]) > 0]
    report = {
        "audit_id": contract["contract_id"], "status": "audit_complete_evidence_and_review_pending",
        "archive_inventory": inventories, "forecast_origin_audit": origins,
        "historical_publication_vintages_verified": False,
        "included_permit_review": permits,
        "work_scope_summary": [{"work_class": kind, "record_count": sum(r["work_class"] == kind for r in permits), "reported_value_cad": str(value)} for kind, value in sorted(totals.items())],
        "facility_candidate_groups": [{"candidate_id": key, "permit_ids": ids, "confirmed_link": False} for key, ids in sorted(clusters.items())],
        "project_inventory": projects,
        "component_overlap": {"simultaneously_positive_market_quarter_cells": len(simultaneous),
                              "finding": "No same-cell project/permit dollar overlap in the frozen proxy." if not simultaneous else "Potential same-cell overlap requires record linkage.",
                              "scope": "current included dollar components and declared CMA mapping only; not proof of distinct facilities or permit work packages",
                              "permits_deduplicated": False},
        "schedule_horizon_audit": horizon_checks,
        "next_evidence_required": [
            "Archived project cost, schedule and stage records with publication dates before each forecast origin.",
            "Historical BCPI release vintages; an old reference quarter in a current extract is insufficient.",
            "Permit publication/update history; issue dates alone cannot establish historical availability.",
            "Independently reviewed facility and work-package linkage for the two Rogers candidates; do not collapse separate maintenance and expansion permits.",
            "A separately versioned full-schedule denominator and source-ablation protocol before any refit.",
        ],
        "limitations": ["Inventory covers the pinned local archive only; it does not establish whether external historical archives exist.",
                        "Proposed work classes and facility candidates are analyst interpretations awaiting independent review.",
                        "Neither permits, reported project costs, nor timing profiles establish realized AI expenditure."],
        "publication_boundary": contract["publication_boundary"],
        "contract_sha256": _digest(root / CONTRACT), "input_manifest": contract["input_manifest"],
        "implementation_manifest": {name: _digest(root / name) for name in ("research/src/aiio/vintage_linkage.py", "research/src/aiio/proxy_treatment.py", "research/src/aiio/planning_benchmark.py")},
    }
    verification = verify_local_archives(root, inventories, permits) if verify_raw else None
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report, verification
