from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..paths import repository_path
from ..schemas import ValidationError


SOURCE_ID = "VANCOUVER_ISSUED_BUILDING_PERMITS"
DATASET_ID = "issued-building-permits"
API_ROOT = f"https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/{DATASET_ID}"
RECORDS_URL = f"{API_ROOT}/records"
TRANSFORMATION_ID = "TR_VANCOUVER_DATA_CENTRE_PERMIT_PROXY_0_1"
SELECT_FIELDS = (
    "permitnumber", "permitnumbercreateddate", "issuedate", "permitelapseddays",
    "projectvalue", "typeofwork", "projectdescription", "propertyuse",
    "specificusecategory", "issueyear", "yearmonth",
)
WHERE = (
    'search(projectdescription, "data centre") OR '
    'search(projectdescription, "data center") OR '
    'specificusecategory = "Bulk Data Storage"'
)
DATA_CENTRE_PATTERN = re.compile(r"\bdata[\s-]*cent(?:er|re)s?\b|\bbulk data storage\b", re.I)
AI_PATTERN = re.compile(r"\bartificial intelligence\b|\bmachine learning\b|\bGPU(?:s)?\b|\bAI\b", re.I)
OUTPUT_FIELDS = (
    "permit_proxy_id", "source_permit_number", "permit_created_date", "issue_date",
    "issue_year", "year_month", "permit_elapsed_days", "work_type", "classification",
    "candidate_status", "reported_estimated_construction_value_cad",
    "construction_value_status", "ai_specificity_status", "description_sha256",
    "source_id", "source_evidence_status", "classification_evidence_status",
    "transformation_id", "quality_flags",
)


def fetch_vancouver_permit_candidates(raw_root: Path) -> dict[str, Any]:
    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    params = {"select": ",".join(SELECT_FIELDS), "where": WHERE, "order_by": "issuedate,permitnumber", "limit": "100"}
    url = RECORDS_URL + "?" + urllib.parse.urlencode(params)
    content, effective_url, content_type = _request(url)
    payload = json.loads(content)
    rows = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValidationError("Vancouver permit query returned no candidate rows")
    if payload.get("total_count", 0) > len(rows):
        raise ValidationError("Vancouver permit candidate query exceeded its row limit")
    digest = hashlib.sha256(content).hexdigest()
    destination_dir = raw_root / SOURCE_ID.lower(); destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{retrieved_at[:10]}_{digest[:12]}.json"
    destination.write_bytes(content)
    record = {
        "retrieval_id": f"RET_{SOURCE_ID}_{digest[:16]}", "source_id": SOURCE_ID,
        "dataset_id": DATASET_ID, "retrieved_at": retrieved_at, "effective_url": effective_url,
        "query_parameters": params, "content_hash": f"sha256:{digest}",
        "content_type": content_type, "byte_length": len(content), "row_count": len(rows),
        "archive_path": repository_path(destination), "excluded_fields": ["address", "applicant", "applicantaddress", "buildingcontractor", "buildingcontractoraddress", "geom", "geo_point_2d"],
        "result": "success",
    }
    destination.with_suffix(".json.manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def normalize_vancouver_permit_proxy(raw_path: Path, output_path: Path, report_path: Path, *, source_as_of_date: str, retrieval_manifest_path: Path | None = None) -> dict[str, Any]:
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    rows = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValidationError("Vancouver permit input must contain non-empty results")
    if retrieval_manifest_path is not None:
        manifest = json.loads(retrieval_manifest_path.read_text(encoding="utf-8"))
        if manifest.get("content_hash") != "sha256:" + hashlib.sha256(raw_path.read_bytes()).hexdigest():
            raise ValidationError("Vancouver permit retrieval hash mismatch")
    normalized = [_normalize(row) for row in rows]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(normalized)
    candidates = [row for row in normalized if row["candidate_status"] == "data_centre_candidate"]
    values = [Decimal(row["reported_estimated_construction_value_cad"]) for row in candidates if row["reported_estimated_construction_value_cad"]]
    report = {
        "schema_version": "0.1.0", "model_id": "AIIO_VANCOUVER_DATA_CENTRE_PERMIT_PROXY_0_1",
        "transformation_id": TRANSFORMATION_ID, "as_of_date": source_as_of_date,
        "evidence_status": "observed_permit_fields_with_inferred_keyword_classification",
        "source_ids": [SOURCE_ID], "input_sha256": _sha(raw_path),
        "retrieval_manifest_sha256": _sha(retrieval_manifest_path) if retrieval_manifest_path else None,
        "output_sha256": _sha(output_path), "broad_screen_row_count": len(normalized),
        "classification_counts": dict(sorted(Counter(row["classification"] for row in normalized).items())),
        "data_centre_candidate_count": len(candidates),
        "explicit_ai_reference_count": sum(row["ai_specificity_status"] == "explicit_ai_reference_observed" for row in candidates),
        "data_centre_candidate_reported_value_total_cad_proxy": float(sum(values, Decimal("0"))),
        "publication_boundary": {"status": "municipal_permit_activity_proxy_only", "proxy_exposure_authorized": True, "realized_ai_construction_treatment_authorized": False, "realized_construction_spend_authorized": False, "causal_effect_authorized": False, "reason": "Issued permits and declared project values indicate authorized activity, not realized quarterly expenditure or labour hours; text does not establish AI use."},
        "limitations": ["The dataset starts in 2017 and records initial issuance rather than construction progress.", "Project value is an applicant estimate and may be zero, incomplete, revised or overlap related permits.", "Classification is a disclosed text/category rule; AI specificity is not imputed.", "Personal and precise location fields are excluded from the processed artifact."],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True); report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _normalize(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict): raise ValidationError("Vancouver permit rows must be objects")
    missing = {"permitnumber", "issuedate", "projectdescription", "typeofwork"} - set(raw)
    if missing: raise ValidationError(f"Vancouver permit schema changed; missing fields: {sorted(missing)}")
    description = str(raw.get("projectdescription") or ""); categories = "|".join(raw.get("specificusecategory") or [])
    matches = DATA_CENTRE_PATTERN.findall(description + " " + categories)
    candidate = bool(matches)
    raw_value = raw.get("projectvalue"); value = ""
    if raw_value not in (None, ""):
        try:
            parsed = Decimal(str(raw_value)); value = f"{parsed:.2f}" if parsed > 0 else ""
        except InvalidOperation as exc: raise ValidationError("invalid Vancouver project value") from exc
    flags = ["not_realized_spend_or_labour_hours", "permit_project_linkage_not_observed"]
    if not value: flags.append("project_value_missing_or_nonpositive")
    return {
        "permit_proxy_id": f"VAN-{hashlib.sha256(str(raw['permitnumber']).encode()).hexdigest()[:16]}",
        "source_permit_number": str(raw["permitnumber"]), "permit_created_date": str(raw.get("permitnumbercreateddate") or ""),
        "issue_date": str(raw["issuedate"]), "issue_year": str(raw.get("issueyear") or str(raw["issuedate"])[:4]),
        "year_month": str(raw.get("yearmonth") or str(raw["issuedate"])[:7]), "permit_elapsed_days": str(raw.get("permitelapseddays") or ""),
        "work_type": str(raw["typeofwork"]), "classification": "explicit_data_centre_reference" if candidate else "excluded_false_positive",
        "candidate_status": "data_centre_candidate" if candidate else "not_candidate",
        "reported_estimated_construction_value_cad": value, "construction_value_status": "reported_permit_estimate_proxy" if value else "not_available",
        "ai_specificity_status": "explicit_ai_reference_observed" if AI_PATTERN.search(description) else "not_ai_specific",
        "description_sha256": "sha256:" + hashlib.sha256(description.encode()).hexdigest(), "source_id": SOURCE_ID,
        "source_evidence_status": "observed", "classification_evidence_status": "inferred_rule_based",
        "transformation_id": TRANSFORMATION_ID, "quality_flags": "|".join(flags),
    }


def _request(url: str) -> tuple[bytes, str, str]:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "AIIO-Canada/0.1"}), timeout=120) as response:
        return response.read(), response.geturl(), response.headers.get_content_type()


def _sha(path: Path | None) -> str | None:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() if path else None
