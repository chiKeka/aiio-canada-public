"""Immutable source snapshots and conservative as-of selection for research."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from .planning_benchmark import CONTRACT as BENCHMARK_CONTRACT, digest, quarter, quarter_label
from .proxy_treatment import _boundaries
from .schemas import ValidationError

CATALOG = "data/vintages/catalog.json"
OUTPUT = "data/model-runs/historical_snapshot_readiness_current.json"
KEYS = {"ALBERTA_MAJOR_PROJECTS": "project_id", "EDMONTON_GENERAL_BUILDING_PERMITS": "permit_proxy_id", "STATCAN_BCPI_18100289": "observation_id"}
BOUNDARY = {"validated_estimate_authorized": False, "causal_attribution_authorized": False, "model_replay_authorized": False}


def path_in(root, name):
    if not isinstance(name, str) or Path(name).is_absolute():
        raise ValidationError("snapshot paths must be repository-relative")
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValidationError("snapshot path escapes repository")
    return path


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValidationError("snapshot date must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValidationError("snapshot timestamp requires a timezone")
    return parsed.astimezone(UTC)


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def blob_hash(content):
    return "sha256:" + hashlib.sha256(content).hexdigest()


def checked_file(root, reference):
    path = path_in(root, reference["path"])
    if not path.is_file() or digest(path) != reference["sha256"]:
        raise ValidationError(f"snapshot file missing or hash drift: {reference['path']}")
    return path


def inspect_csv(content, source):
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
        rows = list(reader)
    except (UnicodeError, csv.Error) as exc:
        raise ValidationError("snapshot must be a UTF-8 normalized CSV") from exc
    key = KEYS[source]
    if not rows or not {key, "source_id"}.issubset(reader.fieldnames or []):
        raise ValidationError("snapshot is empty or lacks source and record identifiers")
    if any(not row.get(key) or row.get("source_id") != source or None in row or any(v is None for v in row.values()) for row in rows):
        raise ValidationError("snapshot has malformed rows or mismatched source IDs")
    if len({row[key] for row in rows}) != len(rows):
        raise ValidationError("snapshot has duplicate record identifiers")
    return len(rows)


def availability(root, source, capture, publication):
    captured = timestamp(capture["retrieved_at"])
    if publication is None:
        return captured.isoformat(), "capture_time_only"
    published = timestamp(publication["published_at"])
    if published > captured:
        raise ValidationError("publication cannot follow the captured historical snapshot")
    checked_file(root, publication["evidence"])
    receipt = json.loads(checked_file(root, publication["review_receipt"]).read_text())
    expected = {
        "schema_version": "AIIO_PUBLICATION_DATE_REVIEW_1.0",
        "decision": "accept_snapshot_publication_date", "source_id": source,
        "raw_content_sha256": capture["content_hash"],
        "published_at": publication["published_at"],
        "evidence_sha256": publication["evidence"]["sha256"],
        "scope": "source_publication_date_only",
    }
    if any(receipt.get(k) != v for k, v in expected.items()) or not str(receipt.get("reviewer", "")).strip():
        raise ValidationError("publication-date review does not match source, content, date and evidence")
    reviewed = timestamp(receipt.get("reviewed_at"))
    if reviewed < captured:
        raise ValidationError("review must follow acquisition of the captured evidence")
    return published.isoformat(), "reviewed_publication_date"


def _catalog(root):
    path = root / CATALOG
    if not path.exists():
        return {"schema_version": "AIIO_SNAPSHOT_CATALOG_1.0", "snapshots": []}
    data = json.loads(path.read_text())
    if data.get("schema_version") != "AIIO_SNAPSHOT_CATALOG_1.0" or not isinstance(data.get("snapshots"), list):
        raise ValidationError("invalid snapshot catalog")
    ids = [r["snapshot_id"] for r in data["snapshots"]]
    if len(ids) != len(set(ids)):
        raise ValidationError("duplicate snapshot IDs in catalog")
    return data


def load_snapshots(root):
    entries = []
    for ref in _catalog(root)["snapshots"]:
        entry = json.loads(checked_file(root, ref).read_text())
        if entry.get("schema_version") != "AIIO_SOURCE_SNAPSHOT_1.0" or entry["snapshot_id"] != ref["snapshot_id"] or entry["source_id"] not in KEYS or entry["publication_boundary"] != BOUNDARY:
            raise ValidationError("unsupported or authorizing snapshot")
        manifest_path = checked_file(root, entry["capture_manifest"])
        capture = json.loads(manifest_path.read_text())
        if capture != entry["capture"] or capture["source_id"] != entry["source_id"] or capture.get("result") != "success":
            raise ValidationError("capture manifest does not match snapshot")
        available, basis = availability(root, entry["source_id"], capture, entry["publication"])
        if (available, basis) != (entry["available_at"], entry["availability_basis"]):
            raise ValidationError("snapshot availability was altered")
        data = checked_file(root, entry["normalized_artifact"]).read_bytes()
        if inspect_csv(data, entry["source_id"]) != entry["record_count"]:
            raise ValidationError("snapshot record count mismatch")
        entries.append(entry)
    return entries


def register_snapshot(root: Path, descriptor_path: Path):
    descriptor = json.loads(descriptor_path.read_text())
    if descriptor.get("schema_version") != "AIIO_SNAPSHOT_INTAKE_1.0":
        raise ValidationError("unsupported snapshot intake descriptor")
    source, identifier = descriptor["source_id"], descriptor["snapshot_id"]
    if source not in KEYS or not re.fullmatch(r"[A-Z][A-Z0-9_]{5,95}", identifier):
        raise ValidationError("unsupported source or invalid snapshot ID")
    capture_path = checked_file(root, descriptor["capture_manifest"])
    capture = json.loads(capture_path.read_text())
    if capture["source_id"] != source or capture.get("result") != "success":
        raise ValidationError("intake capture source or retrieval result mismatch")
    # A supplied identical-content copy may replace a missing named cache file.
    raw_path = path_in(root, descriptor.get("raw_copy_path", capture["archive_path"]))
    if not raw_path.is_file() or digest(raw_path) != capture["content_hash"]:
        raise ValidationError("intake requires raw bytes matching the capture hash")
    content = checked_file(root, descriptor["normalized_artifact"]).read_bytes()
    count = inspect_csv(content, source)
    publication = descriptor.get("publication")
    available, basis = availability(root, source, capture, publication)
    artifact_name = f"data/vintages/artifacts/{identifier}.csv"
    entry_name = f"data/vintages/snapshots/{identifier}.json"
    entry = {
        "schema_version": "AIIO_SOURCE_SNAPSHOT_1.0", "snapshot_id": identifier, "source_id": source,
        "capture": capture, "capture_manifest": descriptor["capture_manifest"],
        "normalized_artifact": {"path": artifact_name, "sha256": blob_hash(content)},
        "normalized_from": descriptor["normalized_artifact"], "record_count": count,
        "available_at": available, "availability_basis": basis, "publication": publication,
        "intake_validation": "raw and normalized bytes hashed; source IDs, uniqueness and CSV shape checked",
        "limitation": "Hashes verify file identity, not normalization correctness or independent reviewer identity. Dataset availability is not model-ready coverage.",
        "publication_boundary": BOUNDARY,
    }
    # Validate current contents before mutating an existing catalog.
    existing = load_snapshots(root)
    match = next((e for e in existing if e["snapshot_id"] == identifier), None)
    if match is not None:
        if match != entry:
            raise ValidationError("snapshot IDs are immutable; use a new ID for revised content or evidence")
        return {"status": "already_registered", "snapshot_id": identifier}
    artifact_path, entry_path = path_in(root, artifact_name), path_in(root, entry_name)
    if artifact_path.exists() or entry_path.exists():
        raise ValidationError("snapshot output path already exists outside the catalog")
    data = _catalog(root)
    data["snapshots"].append({"snapshot_id": identifier, "path": entry_name, "sha256": blob_hash(encoded(entry))})
    data["snapshots"].sort(key=lambda r: r["snapshot_id"])
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    with artifact_path.open("xb") as handle:
        handle.write(content)
    with entry_path.open("xb") as handle:
        handle.write(encoded(entry))
    catalog_path = path_in(root, CATALOG)
    pending = catalog_path.with_suffix(".pending")
    pending.write_bytes(encoded(data))
    pending.replace(catalog_path)
    return {"status": "registered", "snapshot_id": identifier, "available_at": available, "record_count": count}


def select_snapshot(entries, source, as_of):
    if source not in KEYS:
        raise ValidationError("unsupported snapshot source")
    cutoff = timestamp(as_of)
    eligible = [e for e in entries if e["source_id"] == source and timestamp(e["available_at"]) <= cutoff]
    if not eligible:
        return {"status": "missing", "snapshot_id": None, "normalized_artifact": None, "record_count": None}
    latest = max(timestamp(e["available_at"]) for e in eligible)
    candidates = [e for e in eligible if timestamp(e["available_at"]) == latest]
    signatures = {(e["capture"]["content_hash"], e["normalized_artifact"]["sha256"]) for e in candidates}
    if len(signatures) != 1:
        raise ValidationError("ambiguous different snapshot contents at the same availability time")
    # Identical captures may have multiple IDs; deterministically retain one.
    chosen = sorted(candidates, key=lambda e: e["snapshot_id"])[0]
    return {"status": "selected", **{key: chosen[key] for key in ("snapshot_id", "available_at", "availability_basis", "normalized_artifact", "record_count")}}


def build_snapshot_readiness(root: Path, output: Path | None = None):
    entries = load_snapshots(root)
    contract = json.loads((root / BENCHMARK_CONTRACT).read_text())
    design = contract["design"]
    origins = []
    for target in range(quarter(design["first_test_quarter"]), quarter(design["last_test_quarter"]) + 1):
        end = _boundaries(quarter_label(target - 1))[1] + "T23:59:59+00:00"
        selections = {source: select_snapshot(entries, source, end) for source in sorted(KEYS)}
        origins.append({"target_quarter": quarter_label(target), "forecast_origin_end_utc": end,
                        "source_selections": selections,
                        "all_source_snapshots_available": all(s["status"] == "selected" for s in selections.values()),
                        "row_level_coverage_verified": False})
    manifest = {BENCHMARK_CONTRACT: digest(root / BENCHMARK_CONTRACT)}
    if (root / CATALOG).exists():
        manifest[CATALOG] = digest(root / CATALOG)
    for ref in _catalog(root)["snapshots"]:
        manifest[ref["path"]] = ref["sha256"]
    for entry in entries:
        for reference in (entry["capture_manifest"], entry["normalized_artifact"]):
            manifest[reference["path"]] = reference["sha256"]
        if entry["publication"]:
            for key in ("evidence", "review_receipt"):
                ref = entry["publication"][key]
                manifest[ref["path"]] = ref["sha256"]
    report = {
        "report_id": "AIIO_HISTORICAL_SNAPSHOT_READINESS_1_0", "status": "source_selection_complete_model_replay_withheld",
        "snapshot_count": len(entries), "origins": origins,
        "complete_source_snapshot_origins": sum(r["all_source_snapshots_available"] for r in origins),
        "required_source_origin_pairs": len(origins) * len(KEYS),
        "missing_source_origin_pairs": sum(s["status"] == "missing" for r in origins for s in r["source_selections"].values()),
        "acquisition_queue": [{"source_id": source, "needed_by": r["forecast_origin_end_utc"], "target_quarter": r["target_quarter"],
                               "requirement": "Acquire a dated full source snapshot; hash raw and normalized files. An earlier publication date requires evidence bound to these raw bytes and a matching review receipt."}
                              for r in origins for source, selection in r["source_selections"].items() if selection["status"] == "missing"],
        "publication_boundary": BOUNDARY,
        "limitations": ["Whole snapshots are selected atomically; rows from later captures are never merged backward.",
                        "Missing source selections remain null, never zero-valued observations.",
                        "Snapshot existence does not establish the required markets, assets, fields, training coverage or predictive validity.",
                        "A publication-date receipt is a recorded reviewer assertion, not cryptographic authentication of the reviewer or source."],
        "input_manifest": manifest,
        "implementation_manifest": {"research/src/aiio/historical_intake.py": digest(root / "research/src/aiio/historical_intake.py")},
    }
    if output:
        if output.resolve() in {(root / p).resolve() for p in manifest}:
            raise ValidationError("readiness output cannot overwrite an input")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(encoded(report))
    return report
