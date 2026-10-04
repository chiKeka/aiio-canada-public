from __future__ import annotations

from enum import StrEnum


class EvidenceStatus(StrEnum):
    OBSERVED = "observed"
    CORROBORATED = "corroborated"
    INFERRED = "inferred"
    ASSUMED = "assumed"
    SCENARIO = "scenario"


class SourceStatus(StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    PAUSED = "paused"
    RETIRED = "retired"


ALLOWED_ACCESS_METHODS = {
    "api_json",
    "bulk_zip",
    "csv",
    "geojson",
    "html",
    "html_form_export",
    "pdf",
    "xlsx",
}

SCHEMA_VERSION = "1.0.0"
