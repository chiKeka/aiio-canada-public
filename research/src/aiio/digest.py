from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .constants import EvidenceStatus
from .schemas import ValidationError


ALLOWED_DIGEST_STATUSES = {"draft", "review", "approved"}
ALLOWED_MODEL_ACTIONS = {"no_change", "review_candidate", "promote_after_release"}
EVIDENCE_ONLY_STATUSES = {
    EvidenceStatus.OBSERVED,
    EvidenceStatus.CORROBORATED,
    EvidenceStatus.INFERRED,
}


def build_digest(
    items_path: Path,
    output_path: Path,
    edition_date: date,
    *,
    source_registry_path: Path | None = None,
    manifest_path: Path | None = None,
    approval_receipt_path: Path | None = None,
) -> dict[str, Any]:
    payload = json.loads(items_path.read_text(encoding="utf-8"))
    registry = load_registry(source_registry_path) if source_registry_path else None
    items: list[dict[str, Any]] = payload.get("items", [])
    if not items:
        raise ValidationError("digest requires at least one evidence item")

    item_ids: set[str] = set()
    normalized_items = []
    for index, item in enumerate(items, start=1):
        normalized = validate_item(item, index=index, registry=registry)
        if normalized["item_id"] in item_ids:
            raise ValidationError(
                f"digest item_id must be unique: {normalized['item_id']}"
            )
        item_ids.add(normalized["item_id"])
        normalized_items.append(normalized)

    payload_date = payload.get("edition_date")
    if payload_date != edition_date.isoformat():
        raise ValidationError(
            "digest edition_date must match the requested output date: "
            f"{payload_date!r} != {edition_date.isoformat()!r}"
        )
    status = payload.get("status")
    if status not in ALLOWED_DIGEST_STATUSES:
        raise ValidationError(
            "digest status must be one of: " + ", ".join(sorted(ALLOWED_DIGEST_STATUSES))
        )

    approval = None
    if status == "approved":
        if approval_receipt_path is None or source_registry_path is None:
            raise ValidationError("approved digest requires an internal editorial approval receipt and source registry")
        approval = validate_editorial_approval(approval_receipt_path, items_path, source_registry_path, payload, normalized_items)

    lines = [
        f"# AIIO Canada weekly evidence digest — {edition_date.isoformat()}",
        "",
        f"> Edition status: `{status}`. New public evidence and its possible model implications. Implications are research notes, not findings, until incorporated into a reviewed release.",
        "",
    ]
    for item in normalized_items:
        source_links = ", ".join(
            f"[{source['source_id']}]({source['source_url']})"
            for source in item["sources"]
        )
        geography = ", ".join(item["geography_ids"]) or "not specified"
        lines.extend(
            [
                f"## {item['headline']}",
                "",
                f"- **Item ID:** `{item['item_id']}`",
                f"- **Evidence status:** `{item['evidence_status']}`",
                f"- **Geography:** `{geography}`",
                f"- **Sources:** {source_links}",
                "",
                f"**Observed or inferred change:** {item['observed_change']}",
                "",
                f"**Potential model implication:** {item['model_implication']}",
                "",
                f"**Model action:** `{item['model_action']}` — no automatic parameter or baseline change.",
                "",
            ]
        )
    lines.extend(
        [
            "## Release note",
            "",
            "No model value changes automatically from a digest item. Promotion into the baseline requires schema validation, evidence review and a versioned release.",
            "",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    registry_hash = sha256_file(source_registry_path) if source_registry_path else None
    manifest = {
        "schema_version": "1.0.0",
        "digest_id": payload.get(
            "digest_id", f"AIIO_DIGEST_{edition_date.isoformat().replace('-', '_')}"
        ),
        "edition_date": edition_date.isoformat(),
        "status": status,
        "automatic_model_change": False,
        "item_count": len(normalized_items),
        "item_ids": [item["item_id"] for item in normalized_items],
        "source_ids": sorted(
            {
                source["source_id"]
                for item in normalized_items
                for source in item["sources"]
            }
        ),
        "items_sha256": sha256_file(items_path),
        "markdown_sha256": sha256_file(output_path),
        "source_registry_sha256": registry_hash,
        "publication_boundary": {
            "model_parameters_changed": False,
            "baseline_changed": False,
            "release_required_for_promotion": True,
        },
    }
    if approval is not None:
        manifest["editorial_approval"] = approval
    resolved_manifest_path = manifest_path or output_path.with_suffix(".manifest.json")
    resolved_manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def validate_editorial_approval(receipt_path: Path, items_path: Path, registry_path: Path, payload: dict, items: list[dict]) -> dict:
    """Approve evidence publication only; retain the immutable reviewed candidate."""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    required = {"scope": "evidence_digest_only", "decision": "approved", "reviewer_role": "internal_editorial", "automatic_model_change": False, "independent_model_review_waived": False}
    if any(receipt.get(key) != value for key, value in required.items()):
        raise ValidationError("editorial receipt must approve evidence only without waiving independent model review")
    if not isinstance(receipt.get("reviewer"), str) or not receipt["reviewer"].strip():
        raise ValidationError("editorial receipt requires an identified internal reviewer")
    try:
        reviewed_at = datetime.fromisoformat(receipt["reviewed_at"].replace("Z", "+00:00"))
        if reviewed_at.tzinfo is None:
            raise ValueError("timezone required")
    except (KeyError, ValueError, AttributeError) as exc:
        raise ValidationError("editorial receipt requires a timezone-qualified reviewed_at") from exc
    if receipt.get("items_sha256") != sha256_file(items_path) or receipt.get("source_registry_sha256") != sha256_file(registry_path):
        raise ValidationError("editorial approval intake or registry hash mismatch")
    root = registry_path.resolve().parents[2]
    def pinned_file(relative, expected_hash):
        if not isinstance(relative, str):
            raise ValidationError("editorial receipt requires repository-relative artifact paths")
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256_file(path) != expected_hash:
            raise ValidationError("editorial receipt artifact missing, outside repository or hash mismatch")
        return path
    candidate = pinned_file(receipt.get("candidate_items_path"), receipt.get("candidate_items_sha256"))
    candidate_payload = json.loads(candidate.read_text(encoding="utf-8"))
    if candidate_payload.get("status") != "review" or {key: value for key, value in candidate_payload.items() if key != "status"} != {key: value for key, value in payload.items() if key != "status"}:
        raise ValidationError("approved intake must match an immutable review candidate except status")
    artifacts = receipt.get("source_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValidationError("editorial receipt requires pinned source artifacts")
    expected_sources = {source["source_id"] for item in items for source in item["sources"]}
    covered = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or artifact.get("source_id") not in expected_sources:
            raise ValidationError("editorial receipt artifact source does not match digest")
        pinned_file(artifact.get("path"), artifact.get("sha256"))
        covered.add(artifact["source_id"])
    if covered != expected_sources:
        raise ValidationError("editorial receipt must cover every digest source")
    for artifact in receipt.get("context_artifacts", []):
        if not isinstance(artifact, dict):
            raise ValidationError("editorial receipt context artifacts must be pinned files")
        pinned_file(artifact.get("path"), artifact.get("sha256"))
    return {"receipt_sha256": sha256_file(receipt_path), "scope": "evidence_digest_only", "reviewer": receipt["reviewer"], "reviewer_role": "internal_editorial", "reviewed_at": receipt["reviewed_at"], "candidate_items_sha256": receipt["candidate_items_sha256"], "independent_model_review_waived": False}


def publish_reviewed_digest(root: Path, items_path: Path, manifest: dict, receipt_path: Path) -> None:
    """Update evidence pointers only after rechecking approved content and its receipt."""
    if manifest.get("status") != "approved":
        return
    payload = json.loads(items_path.read_text())
    registry_path = root / 'data/registry/sources.json'
    registry = load_registry(registry_path)
    items = [validate_item(item, index=index, registry=registry) for index, item in enumerate(payload['items'], 1)]
    approval = validate_editorial_approval(receipt_path, items_path, registry_path, payload, items)
    if payload.get('status') != 'approved' or manifest.get('items_sha256') != sha256_file(items_path) or manifest.get('editorial_approval') != approval:
        raise ValidationError('reviewed digest pointer requires matching approved manifest')
    pointer = {key: manifest[key] for key in ('schema_version', 'digest_id', 'edition_date', 'status', 'item_count', 'source_ids', 'automatic_model_change')}
    outputs = {root / 'public/data/reviewed-digest.json': payload, root / 'public/data/latest-digest.json': pointer}
    backups = {path: path.read_bytes() if path.exists() else None for path in outputs}
    try:
        for path, value in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.with_suffix('.tmp').write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
        for path in outputs:
            path.with_suffix('.tmp').replace(path)
    except Exception:
        for path, old in backups.items():
            if old is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(old)
        raise
    finally:
        for path in outputs:
            path.with_suffix('.tmp').unlink(missing_ok=True)


def validate_item(
    item: dict[str, Any],
    *,
    index: int,
    registry: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    missing = [
        key
        for key in (
            "headline",
            "observed_change",
            "model_implication",
            "evidence_status",
        )
        if not item.get(key)
    ]
    if missing:
        raise ValidationError(f"digest item {index} is missing: {', '.join(missing)}")

    try:
        evidence_status = EvidenceStatus(item["evidence_status"])
    except ValueError as exc:
        raise ValidationError(
            f"digest item {index} has an invalid evidence_status"
        ) from exc
    if evidence_status not in EVIDENCE_ONLY_STATUSES:
        raise ValidationError(
            "weekly evidence items cannot present assumptions or scenarios as new evidence"
        )

    sources = item.get("sources")
    if sources is None and item.get("source_id") and item.get("source_url"):
        sources = [
            {"source_id": item["source_id"], "source_url": item["source_url"]}
        ]
    if not isinstance(sources, list) or not sources:
        raise ValidationError(f"digest item {index} requires at least one source")
    normalized_sources = []
    seen_sources: set[str] = set()
    for source in sources:
        if not isinstance(source, dict) or not source.get("source_id") or not source.get(
            "source_url"
        ):
            raise ValidationError(
                f"digest item {index} has an incomplete source reference"
            )
        source_id = source["source_id"]
        if source_id in seen_sources:
            raise ValidationError(
                f"digest item {index} repeats source_id {source_id}"
            )
        seen_sources.add(source_id)
        if registry is not None:
            registered = registry.get(source_id)
            if registered is None:
                raise ValidationError(
                    f"digest item {index} references unknown source_id {source_id}"
                )
            if source["source_url"] != registered["canonical_url"]:
                raise ValidationError(
                    f"digest item {index} source URL does not match registry for {source_id}"
                )
        normalized_sources.append(
            {"source_id": source_id, "source_url": source["source_url"]}
        )

    item_id = item.get("item_id") or f"DIGEST_ITEM_{index:02d}"
    model_action = item.get("model_action", "no_change")
    if model_action not in ALLOWED_MODEL_ACTIONS:
        raise ValidationError(
            f"digest item {index} has an invalid model_action: {model_action}"
        )
    if item.get("automatic_model_change") not in (None, False):
        raise ValidationError(
            f"digest item {index} cannot authorize an automatic model change"
        )
    geography_ids = item.get("geography_ids", [])
    if not isinstance(geography_ids, list) or any(
        not isinstance(value, str) or not value for value in geography_ids
    ):
        raise ValidationError(
            f"digest item {index} geography_ids must be a list of identifiers"
        )

    return {
        "item_id": item_id,
        "headline": item["headline"],
        "sources": normalized_sources,
        "observed_change": item["observed_change"],
        "model_implication": item["model_implication"],
        "evidence_status": evidence_status.value,
        "geography_ids": geography_ids,
        "model_action": model_action,
    }


def validate_digest_cadence(
    items_dir: Path,
    *,
    as_of_date: date,
    max_age_days: int = 8,
) -> dict[str, Any]:
    if max_age_days < 1:
        raise ValidationError("digest cadence max_age_days must be positive")
    editions = []
    for path in sorted(items_dir.glob("*.json")):
        try:
            filename_date = date.fromisoformat(path.stem)
        except ValueError:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("edition_date") != filename_date.isoformat():
            raise ValidationError(
                f"digest filename and edition_date disagree: {path.name}"
            )
        editions.append((filename_date, path))
    if not editions:
        raise ValidationError("no dated digest item files found")
    latest_date, latest_path = max(editions)
    age_days = (as_of_date - latest_date).days
    if age_days < 0:
        raise ValidationError("latest digest edition is dated after the audit date")
    if age_days > max_age_days:
        raise ValidationError(
            f"weekly digest is stale: latest edition is {age_days} days old"
        )
    return {
        "status": "current",
        "as_of_date": as_of_date.isoformat(),
        "latest_edition": latest_date.isoformat(),
        "latest_items_path": str(latest_path),
        "age_days": age_days,
        "max_age_days": max_age_days,
    }


def find_latest_digest_items(items_dir: Path) -> tuple[date, Path]:
    """Return the newest valid dated intake without silently accepting date drift."""
    editions: list[tuple[date, Path]] = []
    for path in sorted(items_dir.glob("*.json")):
        try:
            filename_date = date.fromisoformat(path.stem)
        except ValueError:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(f"unable to read digest intake {path.name}: {exc}") from exc
        if payload.get("edition_date") != filename_date.isoformat():
            raise ValidationError(
                f"digest filename and edition_date disagree: {path.name}"
            )
        editions.append((filename_date, path))
    if not editions:
        raise ValidationError("no dated digest item files found")
    return max(editions)


def load_registry(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources", [])
    return {source["source_id"]: source for source in sources}


def sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
