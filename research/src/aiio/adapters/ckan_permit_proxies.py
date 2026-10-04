from __future__ import annotations

import csv, hashlib, json, re, urllib.parse, urllib.request
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..paths import repository_path
from ..schemas import ValidationError

TORONTO_SOURCE_ID = "TORONTO_CLEARED_BUILDING_PERMITS"
TORONTO_RESOURCE_ID = "a96c0ba4-3026-402b-b09d-5b1268b8f810"
TORONTO_API = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/datastore_search"
MONTREAL_SOURCE_ID = "MONTREAL_CONSTRUCTION_PERMITS"
MONTREAL_RESOURCE_ID = "5232a72d-235a-48eb-ae20-bb9d501300ad"
MONTREAL_API = "https://donnees.montreal.ca/api/3/action/datastore_search"
TERMS = {
    "toronto": ("data center",),
    "montreal": ("centre de données", "centre données", "data center"),
}
FACILITY = re.compile(r"\bdata[ -]*cent(?:er|re)s?\b|\bcentre(?: des?| de)? donn[ée]es\b", re.I)
AI = re.compile(r"\bartificial intelligence\b|\bintelligence artificielle\b|\bmachine learning\b|\bGPU(?:s)?\b|\bAI\b", re.I)
FIELDS = (
    "permit_proxy_id", "source_permit_id", "application_date", "issue_date", "completion_date",
    "issue_to_completion_days", "permit_type", "work_type", "classification", "candidate_status",
    "reported_estimated_construction_value_cad", "construction_value_status", "ai_specificity_status",
    "description_sha256", "source_id", "source_evidence_status", "classification_evidence_status",
    "quality_flags",
)


def fetch_ckan_permit_candidates(city: str, raw_root: Path) -> dict[str, Any]:
    source_id, resource_id, endpoint = _config(city)
    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat(); records: list[dict[str, Any]] = []
    query_receipts = []
    for term in TERMS[city]:
        params = {"resource_id": resource_id, "q": term, "limit": "100"}
        content, effective_url, content_type = _request(endpoint + "?" + urllib.parse.urlencode(params))
        payload = json.loads(content)
        if payload.get("success") is not True or not isinstance(payload.get("result", {}).get("records"), list):
            raise ValidationError(f"{city} CKAN query failed")
        result = payload["result"]
        if result.get("total", 0) > len(result["records"]): raise ValidationError(f"{city} query exceeded row limit")
        records.extend(result["records"])
        query_receipts.append({"term": term, "total": result.get("total"), "effective_url": effective_url, "content_type": content_type, "response_sha256": "sha256:" + hashlib.sha256(content).hexdigest()})
    id_fields = ("PERMIT_NUM", "REVISION_NUM") if city == "toronto" else ("id_permis",)
    deduped = {tuple(str(row.get(key) or "") for key in id_fields): row for row in records}
    envelope = {"source_id": source_id, "resource_id": resource_id, "retrieved_at": retrieved_at, "query_receipts": query_receipts, "records": [deduped[key] for key in sorted(deduped)]}
    content = (json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    digest = hashlib.sha256(content).hexdigest(); destination_dir = raw_root / source_id.lower(); destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{retrieved_at[:10]}_{digest[:12]}.json"; destination.write_bytes(content)
    manifest = {"retrieval_id": f"RET_{source_id}_{digest[:16]}", "source_id": source_id, "resource_id": resource_id, "retrieved_at": retrieved_at, "query_terms": list(TERMS[city]), "content_hash": f"sha256:{digest}", "byte_length": len(content), "row_count": len(deduped), "archive_path": repository_path(destination), "excluded_fields": _excluded(city), "result": "success"}
    destination.with_suffix(".json.manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def normalize_ckan_permit_proxy(city: str, raw_path: Path, output_path: Path, report_path: Path, *, source_as_of_date: str, retrieval_manifest_path: Path) -> dict[str, Any]:
    source_id, _, _ = _config(city); envelope = json.loads(raw_path.read_text(encoding="utf-8")); records = envelope.get("records")
    if envelope.get("source_id") != source_id or not isinstance(records, list) or not records: raise ValidationError(f"invalid {city} permit envelope")
    manifest = json.loads(retrieval_manifest_path.read_text(encoding="utf-8"))
    if manifest.get("content_hash") != _sha(raw_path): raise ValidationError(f"{city} retrieval hash mismatch")
    rows = [_toronto(row) if city == "toronto" else _montreal(row) for row in records]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    candidates = [row for row in rows if row["candidate_status"] == "data_centre_candidate"]
    values = [Decimal(row["reported_estimated_construction_value_cad"]) for row in candidates if row["reported_estimated_construction_value_cad"]]
    durations = [int(row["issue_to_completion_days"]) for row in candidates if row["issue_to_completion_days"]]
    report = {"schema_version": "0.1.0", "model_id": f"AIIO_{city.upper()}_DATA_CENTRE_PERMIT_PROXY_0_1", "as_of_date": source_as_of_date,
        "evidence_status": "observed_permit_fields_with_inferred_keyword_classification", "source_ids": [source_id], "input_sha256": _sha(raw_path), "retrieval_manifest_sha256": _sha(retrieval_manifest_path), "output_sha256": _sha(output_path),
        "broad_screen_row_count": len(rows), "data_centre_candidate_count": len(candidates), "explicit_ai_reference_count": sum(row["ai_specificity_status"] == "explicit_ai_reference_observed" for row in candidates),
        "reported_value_available_count": len(values), "candidate_reported_value_total_cad_proxy": float(sum(values, Decimal("0"))), "completion_duration_available_count": len(durations),
        "publication_boundary": {"status": "municipal_permit_activity_proxy_only", "proxy_exposure_authorized": True, "permit_completion_duration_authorized": city == "toronto", "realized_ai_construction_treatment_authorized": False, "realized_construction_spend_authorized": False, "causal_effect_authorized": False, "reason": "Permit milestones and declared cost are administrative proxies, not quarterly realized expenditure or labour hours; text does not establish AI use."},
        "limitations": ["Keyword classification requires review and does not establish AI use.", "Permit records may include multiple permit types or revisions for one underlying project.", "Declared construction cost, where present, is not realized expenditure.", "Precise location and named-party fields are excluded from the processed artifact."]}
    report_path.parent.mkdir(parents=True, exist_ok=True); report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"); return report


def _toronto(raw: dict[str, Any]) -> dict[str, str]:
    required = {"PERMIT_NUM", "ISSUED_DATE", "DESCRIPTION"}
    if required - set(raw): raise ValidationError("Toronto permit schema changed")
    description = str(raw.get("DESCRIPTION") or ""); issue = str(raw.get("ISSUED_DATE") or ""); completion = str(raw.get("COMPLETED_DATE") or "")
    candidate = bool(FACILITY.search(" ".join([description, str(raw.get("CURRENT_USE") or ""), str(raw.get("PROPOSED_USE") or "")]))); value = _money(raw.get("EST_CONST_COST"))
    duration = _days(issue, completion); source_key = f"{raw['PERMIT_NUM']}|{raw.get('REVISION_NUM','')}"
    return _row(TORONTO_SOURCE_ID, source_key, str(raw.get("APPLICATION_DATE") or ""), issue, completion, duration, str(raw.get("PERMIT_TYPE") or ""), str(raw.get("WORK") or ""), description, candidate, value)


def _montreal(raw: dict[str, Any]) -> dict[str, str]:
    required = {"id_permis", "date_emission", "nature_travaux"}
    if required - set(raw): raise ValidationError("Montréal permit schema changed")
    description = str(raw.get("nature_travaux") or ""); candidate = bool(FACILITY.search(description))
    return _row(MONTREAL_SOURCE_ID, str(raw["id_permis"]), str(raw.get("date_debut") or ""), str(raw.get("date_emission") or ""), "", "", str(raw.get("description_type_demande") or ""), str(raw.get("description_type_batiment") or ""), description, candidate, "")


def _row(source_id: str, key: str, application: str, issue: str, completion: str, duration: int | str, permit_type: str, work_type: str, description: str, candidate: bool, value: str) -> dict[str, str]:
    flags = ["not_realized_spend_or_labour_hours", "underlying_project_linkage_not_observed"]
    if not value: flags.append("reported_cost_not_available")
    return {"permit_proxy_id": source_id[:3] + "-" + hashlib.sha256(key.encode()).hexdigest()[:16], "source_permit_id": key, "application_date": application, "issue_date": issue, "completion_date": completion, "issue_to_completion_days": str(duration), "permit_type": permit_type, "work_type": work_type, "classification": "explicit_data_centre_reference" if candidate else "excluded_false_positive", "candidate_status": "data_centre_candidate" if candidate else "not_candidate", "reported_estimated_construction_value_cad": value, "construction_value_status": "reported_permit_estimate_proxy" if value else "not_available", "ai_specificity_status": "explicit_ai_reference_observed" if AI.search(description) else "not_ai_specific", "description_sha256": "sha256:" + hashlib.sha256(description.encode()).hexdigest(), "source_id": source_id, "source_evidence_status": "observed", "classification_evidence_status": "inferred_rule_based", "quality_flags": "|".join(flags)}


def _money(value: Any) -> str:
    if value in (None, ""): return ""
    cleaned = re.sub(r"[^0-9.()-]", "", str(value)).replace("(", "-").replace(")", "")
    try: parsed = Decimal(cleaned)
    except InvalidOperation: return ""
    return f"{parsed:.2f}" if parsed > 0 else ""


def _days(start: str, end: str) -> int | str:
    if not start or not end: return ""
    try: return (date.fromisoformat(end[:10]) - date.fromisoformat(start[:10])).days
    except ValueError: return ""


def _config(city: str) -> tuple[str, str, str]:
    if city == "toronto": return TORONTO_SOURCE_ID, TORONTO_RESOURCE_ID, TORONTO_API
    if city == "montreal": return MONTREAL_SOURCE_ID, MONTREAL_RESOURCE_ID, MONTREAL_API
    raise ValidationError(f"unsupported city: {city}")


def _excluded(city: str) -> list[str]:
    return ["STREET_NUM", "STREET_NAME", "POSTAL", "GEO_ID", "BUILDER_NAME"] if city == "toronto" else ["emplacement", "longitude", "latitude", "loc_x", "loc_y"]


def _request(url: str) -> tuple[bytes, str, str]:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "AIIO-Canada/0.1"}), timeout=120) as response: return response.read(), response.geturl(), response.headers.get_content_type()


def _sha(path: Path) -> str: return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
