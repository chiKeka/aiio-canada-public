from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from .paths import repository_path
from .schemas import SourceRecord, ValidationError


@dataclass(frozen=True)
class RetrievalRecord:
    retrieval_id: str
    source_id: str
    retrieved_at: str
    effective_url: str
    content_hash: str
    content_type: str
    byte_length: int
    archive_path: str
    result: str


def retrieve(source: SourceRecord, raw_root: Path, *, validate_content: Callable[[bytes], None] | None = None) -> RetrievalRecord:
    if source.access_method not in {
        "api_json",
        "bulk_zip",
        "csv",
        "geojson",
        "html",
        "pdf",
        "xlsx",
    }:
        raise ValidationError(
            f"{source.source_id} uses {source.access_method}; a source-specific adapter is required"
        )

    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    request = urllib.request.Request(
        source.retrieval_url,
        headers={"User-Agent": "AIIO-Canada-Research/0.1 (+public research retrieval)"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        content = response.read()
        effective_url = response.geturl()
        content_type = response.headers.get_content_type()

    # Validate candidate payloads before recording a successful verification.
    if validate_content is not None:
        validate_content(content)

    digest = hashlib.sha256(content).hexdigest()
    suffix = _suffix_for(source.access_method, content_type)
    destination_dir = raw_root / source.source_id.lower()
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{retrieved_at[:10]}_{digest[:12]}{suffix}"
    if not destination.exists():
        destination.write_bytes(content)

    record = RetrievalRecord(
        retrieval_id=f"RET_{source.source_id}_{digest[:16]}",
        source_id=source.source_id,
        retrieved_at=retrieved_at,
        effective_url=effective_url,
        content_hash=f"sha256:{digest}",
        content_type=content_type,
        byte_length=len(content),
        archive_path=repository_path(destination),
        result="success",
    )
    manifest_path = destination.with_suffix(destination.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(asdict(record), indent=2) + "\n", encoding="utf-8")
    return record


def _suffix_for(access_method: str, content_type: str) -> str:
    if access_method == "bulk_zip" or content_type == "application/zip":
        return ".zip"
    if access_method == "pdf" or content_type == "application/pdf":
        return ".pdf"
    if access_method == "xlsx":
        return ".xlsx"
    if access_method == "api_json":
        return ".json"
    if access_method == "csv" or content_type == "text/csv":
        return ".csv"
    if access_method == "geojson" or content_type in {
        "application/geo+json",
    }:
        return ".geojson"
    return ".html"
