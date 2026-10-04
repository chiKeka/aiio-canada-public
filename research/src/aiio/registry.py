from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .schemas import SourceRecord, ValidationError


def load_registry(path: Path) -> list[SourceRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "1.0.0":
        raise ValidationError("source registry must use schema_version 1.0.0")
    sources = [SourceRecord.from_dict(item) for item in raw.get("sources", [])]
    if not sources:
        raise ValidationError("source registry cannot be empty")
    source_ids = [source.source_id for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValidationError("source_id values must be unique")
    urls = [source.canonical_url for source in sources]
    if len(urls) != len(set(urls)):
        raise ValidationError("canonical_url values must be unique")
    return sources


def registry_as_json(path: Path) -> str:
    return json.dumps([asdict(item) for item in load_registry(path)], default=str, indent=2)
