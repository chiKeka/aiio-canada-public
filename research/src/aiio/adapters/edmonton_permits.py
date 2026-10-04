from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..paths import repository_path
from ..schemas import ValidationError


SOURCE_ID = "EDMONTON_GENERAL_BUILDING_PERMITS"
DATASET_ID = "24uj-dj8v"
METADATA_URL = f"https://data.edmonton.ca/api/views/{DATASET_ID}"
RESOURCE_URL = f"https://data.edmonton.ca/resource/{DATASET_ID}.json"
TRANSFORMATION_ID = "TR_EDMONTON_DATA_CENTRE_PERMIT_PROXY_0_1"

SELECT_FIELDS = (
    "row_id",
    "issue_date",
    "year",
    "month_number",
    "job_category",
    "job_description",
    "building_type",
    "work_type",
    "construction_value",
    "floor_area",
    "neighbourhood",
    "occupancy_granted_date",
)
REQUIRED_ROW_FIELDS = {
    "row_id",
    "issue_date",
    "year",
    "job_category",
    "job_description",
    "building_type",
}
BROAD_SCREEN_WHERE = (
    "upper(job_description) like '%DATA CENT%' "
    "OR upper(building_type) like '%DATA CENT%' "
    "OR upper(job_category) like '%DATA CENT%' "
    "OR upper(work_type) like '%DATA CENT%' "
    "OR upper(job_description) like '%SERVER%' "
    "OR upper(building_type) like '%SERVER%' "
    "OR upper(job_description) like '%COLOCATION%' "
    "OR upper(job_description) like '%CO-LOCATION%' "
    "OR upper(job_description) like '%HYPERSCALE%'"
)
QUERY_PARAMETERS = (
    ("$select", ",".join(SELECT_FIELDS)),
    ("$where", BROAD_SCREEN_WHERE),
    ("$order", "issue_date,row_id"),
    ("$limit", "50000"),
)

DATA_CENTRE_PATTERN = re.compile(
    r"\bdata[\s-]*cent(?:er|re)s?\b|\bserver[\s-]+farms?\b|"
    r"\bco[\s-]?locations?\b|\bhyperscale\b",
    re.IGNORECASE,
)
SERVER_PATTERN = re.compile(r"\bservers?\b", re.IGNORECASE)
AI_PATTERN = re.compile(
    r"\bartificial intelligence\b|\bmachine learning\b|\bGPU(?:s)?\b|\bAI\b",
    re.IGNORECASE,
)

OUTPUT_FIELDS = (
    "permit_proxy_id",
    "source_row_id",
    "issue_date",
    "issue_year",
    "job_category",
    "building_type",
    "work_type",
    "classification",
    "candidate_status",
    "matched_terms",
    "reported_estimated_construction_value_cad",
    "construction_value_status",
    "floor_area_sq_ft",
    "occupancy_granted_date",
    "occupancy_date_status",
    "description_sha256",
    "ai_specificity_status",
    "realized_construction_status",
    "source_id",
    "source_evidence_status",
    "classification_evidence_status",
    "transformation_id",
    "quality_flags",
)


def fetch_edmonton_permit_candidates(raw_root: Path) -> dict[str, Any]:
    """Retrieve a field-minimized broad keyword screen plus dataset metadata."""
    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    metadata_bytes, metadata_effective_url, metadata_content_type = _request(METADATA_URL)
    try:
        metadata = json.loads(metadata_bytes)
    except json.JSONDecodeError as exc:
        raise ValidationError("Edmonton permit metadata was not valid JSON") from exc
    validate_metadata(metadata)

    query_url = RESOURCE_URL + "?" + urllib.parse.urlencode(QUERY_PARAMETERS)
    content, effective_url, content_type = _request(query_url)
    try:
        rows = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValidationError("Edmonton permit query did not return valid JSON") from exc
    if not isinstance(rows, list) or not rows:
        raise ValidationError("Edmonton permit query returned no candidate rows")
    if len(rows) >= int(dict(QUERY_PARAMETERS)["$limit"]):
        raise ValidationError("Edmonton permit candidate query reached its row limit")

    digest = hashlib.sha256(content).hexdigest()
    metadata_digest = hashlib.sha256(metadata_bytes).hexdigest()
    destination_dir = raw_root / SOURCE_ID.lower()
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{retrieved_at[:10]}_{digest[:12]}.json"
    metadata_destination = destination_dir / f"{retrieved_at[:10]}_{digest[:12]}.metadata.json"
    if not destination.exists():
        destination.write_bytes(content)
    if not metadata_destination.exists():
        metadata_destination.write_bytes(metadata_bytes)

    record = {
        "retrieval_id": f"RET_{SOURCE_ID}_{digest[:16]}",
        "source_id": SOURCE_ID,
        "dataset_id": DATASET_ID,
        "retrieved_at": retrieved_at,
        "effective_url": effective_url,
        "metadata_effective_url": metadata_effective_url,
        "query_parameters": dict(QUERY_PARAMETERS),
        "content_hash": f"sha256:{digest}",
        "metadata_content_hash": f"sha256:{metadata_digest}",
        "content_type": content_type,
        "metadata_content_type": metadata_content_type,
        "byte_length": len(content),
        "metadata_byte_length": len(metadata_bytes),
        "row_count": len(rows),
        "archive_path": repository_path(destination),
        "metadata_archive_path": repository_path(metadata_destination),
        "excluded_fields": [
            "address",
            "legal_description",
            "latitude",
            "longitude",
            "location",
            "geometry_point",
        ],
        "result": "success",
    }
    manifest_path = destination.with_suffix(".json.manifest.json")
    manifest_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def normalize_edmonton_permit_proxy(
    raw_path: Path,
    output_path: Path,
    report_path: Path,
    *,
    source_as_of_date: str,
    retrieval_manifest_path: Path | None = None,
) -> dict[str, Any]:
    try:
        raw_rows = json.loads(raw_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError("Edmonton permit candidate input is not valid JSON") from exc
    if not isinstance(raw_rows, list) or not raw_rows:
        raise ValidationError("Edmonton permit candidate input must be a non-empty list")

    if retrieval_manifest_path is not None:
        verify_manifest(raw_path, retrieval_manifest_path)

    rows = [normalize_row(raw, source_as_of_date) for raw in raw_rows]
    write_rows(output_path, rows)

    classification_counts = Counter(row["classification"] for row in rows)
    candidates = [row for row in rows if row["candidate_status"] == "data_centre_candidate"]
    candidate_values = [
        Decimal(str(row["reported_estimated_construction_value_cad"]))
        for row in candidates
        if row["reported_estimated_construction_value_cad"] != ""
    ]
    non_demolition_candidate_values = [
        Decimal(str(row["reported_estimated_construction_value_cad"]))
        for row in candidates
        if row["reported_estimated_construction_value_cad"] != ""
        and "demolition_scope" not in str(row["quality_flags"]).split("|")
    ]
    issue_dates = [row["issue_date"] for row in rows]
    report = {
        "schema_version": "0.1.0",
        "model_id": "AIIO_EDMONTON_DATA_CENTRE_PERMIT_PROXY_0_1",
        "transformation_id": TRANSFORMATION_ID,
        "as_of_date": source_as_of_date,
        "evidence_status": "observed_permit_fields_with_inferred_keyword_classification",
        "source_ids": [SOURCE_ID],
        "input_sha256": sha256_path(raw_path),
        "retrieval_manifest_sha256": (
            sha256_path(retrieval_manifest_path)
            if retrieval_manifest_path is not None and retrieval_manifest_path.exists()
            else None
        ),
        "output_sha256": sha256_path(output_path),
        "broad_screen_row_count": len(rows),
        "period_start": min(issue_dates),
        "period_end": max(issue_dates),
        "classification_counts": dict(sorted(classification_counts.items())),
        "data_centre_candidate_count": len(candidates),
        "data_centre_candidate_count_since_2018": sum(
            int(row["issue_year"]) >= 2018 for row in candidates
        ),
        "explicit_ai_reference_count": sum(
            row["ai_specificity_status"] == "explicit_ai_reference_observed"
            for row in candidates
        ),
        "reported_estimated_value_available_count": sum(
            row["reported_estimated_construction_value_cad"] != "" for row in rows
        ),
        "data_centre_candidate_reported_value_available_count": len(candidate_values),
        "data_centre_candidate_reported_value_total_cad_proxy": float(
            sum(candidate_values, Decimal("0"))
        ),
        "data_centre_candidate_demolition_count": sum(
            "demolition_scope" in str(row["quality_flags"]).split("|")
            for row in candidates
        ),
        "data_centre_candidate_non_demolition_reported_value_total_cad_proxy": float(
            sum(non_demolition_candidate_values, Decimal("0"))
        ),
        "occupancy_date_available_count": sum(
            row["occupancy_granted_date"] != "" for row in rows
        ),
        "data_centre_candidate_occupancy_date_available_count": sum(
            row["occupancy_granted_date"] != "" for row in candidates
        ),
        "field_minimization": {
            "processed_output_excludes": [
                "address",
                "legal_description",
                "latitude",
                "longitude",
                "location",
                "geometry_point",
                "neighbourhood",
                "job_description",
            ],
            "description_trace": "sha256 hash plus controlled matched-term labels",
        },
        "publication_boundary": {
            "status": "municipal_permit_activity_proxy_only",
            "realized_ai_construction_treatment_authorized": False,
            "realized_construction_spend_authorized": False,
            "construction_completion_outcome_authorized": False,
            "ai_attributable_effect_authorized": False,
            "reason": (
                "Issued permits and publisher-estimated construction values are activity "
                "proxies. Text matches do not identify AI use, and occupancy-granted dates "
                "are incomplete trend fields rather than realized spend, labour hours, legal "
                "occupancy confirmation or a causal treatment measure."
            ),
        },
        "limitations": [
            "The API is a current City of Edmonton snapshot covering issued permits from 2009 onward; it is not a versioned census of Alberta construction.",
            "The server-side query is a broad keyword screen. Controlled word-boundary classification is inferred and requires human review before model use.",
            "A data-centre phrase does not establish that a permit is AI-related; explicit AI specificity is reported separately and is not imputed.",
            "Construction value is the publisher's estimated value of permitted work. Aggregates can include fit-outs, maintenance, expansions and demolition and are not realized capital expenditure.",
            "The City describes occupancy-granted dates as trend fields with limited historical coverage and not legal confirmation of occupancy.",
            "Exact addresses, legal descriptions, coordinates, neighbourhoods and free-text descriptions are excluded from the processed artifact.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def normalize_row(raw: Any, source_as_of_date: str) -> dict[str, str | int]:
    if not isinstance(raw, dict):
        raise ValidationError("Edmonton permit rows must be JSON objects")
    missing = REQUIRED_ROW_FIELDS - set(raw)
    if missing:
        raise ValidationError(f"Edmonton permit schema changed; missing fields: {sorted(missing)}")

    row_id = clean_text(raw.get("row_id"))
    if not row_id:
        raise ValidationError("Edmonton permit row_id cannot be blank")
    issue_date = parse_date(raw.get("issue_date"), "issue_date")
    issue_year = parse_year(raw.get("year"), issue_date)
    description = clean_text(raw.get("job_description"))
    classification, status, matched_terms = classify_description(description)
    ai_specificity = (
        "explicit_ai_reference_observed"
        if AI_PATTERN.search(description)
        else "not_observed"
    )
    value = parse_nonnegative_decimal(raw.get("construction_value"), "construction_value")
    floor_area = parse_nonnegative_decimal(raw.get("floor_area"), "floor_area")
    occupancy_date = parse_optional_date(
        raw.get("occupancy_granted_date"), "occupancy_granted_date"
    )
    quality_flags = ["permit_activity_proxy", "not_realized_construction"]
    if status == "data_centre_candidate":
        quality_flags.append("manual_review_required")
        if ai_specificity != "explicit_ai_reference_observed":
            quality_flags.append("not_ai_specific")
    elif status == "server_reference_context":
        quality_flags.append("not_data_centre_facility_reference")
    else:
        quality_flags.append("excluded_substring_false_positive")
    if value is None:
        quality_flags.append("estimated_value_missing")
    if occupancy_date is None:
        quality_flags.append("occupancy_date_missing")
    if "demolition" in clean_text(raw.get("work_type")).lower():
        quality_flags.append("demolition_scope")

    return {
        "permit_proxy_id": f"EDMBP_{row_id.replace('-', '_')}",
        "source_row_id": row_id,
        "issue_date": issue_date,
        "issue_year": issue_year,
        "job_category": clean_text(raw.get("job_category")),
        "building_type": clean_text(raw.get("building_type")),
        "work_type": clean_text(raw.get("work_type")),
        "classification": classification,
        "candidate_status": status,
        "matched_terms": "|".join(matched_terms),
        "reported_estimated_construction_value_cad": format_decimal(value, 2),
        "construction_value_status": (
            "reported_permit_estimate_proxy" if value is not None else "missing"
        ),
        "floor_area_sq_ft": format_decimal(floor_area, 2),
        "occupancy_granted_date": occupancy_date or "",
        "occupancy_date_status": (
            "observed_trend_proxy" if occupancy_date else "missing"
        ),
        "description_sha256": "sha256:"
        + hashlib.sha256(description.encode("utf-8")).hexdigest(),
        "ai_specificity_status": ai_specificity,
        "realized_construction_status": "not_observed",
        "source_id": SOURCE_ID,
        "source_evidence_status": "observed",
        "classification_evidence_status": "inferred",
        "transformation_id": TRANSFORMATION_ID,
        "quality_flags": "|".join(sorted(set(quality_flags))),
    }


def classify_description(description: str) -> tuple[str, str, list[str]]:
    explicit_matches = [match.group(0).lower() for match in DATA_CENTRE_PATTERN.finditer(description)]
    if explicit_matches:
        return (
            "explicit_data_centre_reference",
            "data_centre_candidate",
            sorted(set(explicit_matches)),
        )
    server_matches = [match.group(0).lower() for match in SERVER_PATTERN.finditer(description)]
    if server_matches:
        return (
            "server_reference_only",
            "server_reference_context",
            sorted(set(server_matches)),
        )
    return "broad_query_substring_false_positive", "excluded_false_positive", []


def validate_metadata(metadata: Any) -> None:
    if not isinstance(metadata, dict) or metadata.get("id") != DATASET_ID:
        raise ValidationError("Edmonton permit metadata dataset ID changed")
    columns = metadata.get("columns")
    if not isinstance(columns, list):
        raise ValidationError("Edmonton permit metadata has no column contract")
    fields = {column.get("fieldName") for column in columns if isinstance(column, dict)}
    missing = set(SELECT_FIELDS) - fields
    if missing:
        raise ValidationError(
            f"Edmonton permit metadata schema changed; missing fields: {sorted(missing)}"
        )


def verify_manifest(raw_path: Path, manifest_path: Path) -> None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError("Edmonton permit retrieval manifest is invalid JSON") from exc
    if manifest.get("source_id") != SOURCE_ID:
        raise ValidationError("Edmonton permit retrieval manifest source_id changed")
    if manifest.get("content_hash") != sha256_path(raw_path):
        raise ValidationError("Edmonton permit raw payload hash does not match its manifest")
    if manifest.get("query_parameters") != dict(QUERY_PARAMETERS):
        raise ValidationError("Edmonton permit retrieval query does not match the registered adapter")


def _request(url: str) -> tuple[bytes, str, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AIIO-Canada-Research/0.1 (+public research retrieval)"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read(), response.geturl(), response.headers.get_content_type()


def write_rows(path: Path, rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def parse_date(value: Any, field_name: str) -> str:
    text = clean_text(value)[:10]
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValidationError(f"Edmonton permit {field_name} is not an ISO date") from exc


def parse_optional_date(value: Any, field_name: str) -> str | None:
    return parse_date(value, field_name) if clean_text(value) else None


def parse_year(value: Any, issue_date: str) -> int:
    try:
        year = int(clean_text(value))
    except ValueError as exc:
        raise ValidationError("Edmonton permit year is not an integer") from exc
    if year != int(issue_date[:4]):
        raise ValidationError("Edmonton permit year does not match issue_date")
    return year


def parse_nonnegative_decimal(value: Any, field_name: str) -> Decimal | None:
    text = clean_text(value).replace(",", "")
    if not text:
        return None
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValidationError(f"Edmonton permit {field_name} is not numeric") from exc
    if parsed < 0:
        raise ValidationError(f"Edmonton permit {field_name} cannot be negative")
    return parsed


def format_decimal(value: Decimal | None, places: int) -> str:
    if value is None:
        return ""
    return f"{value:.{places}f}"


def sha256_path(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
