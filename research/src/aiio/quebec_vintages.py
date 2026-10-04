from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from .paths import repository_path
from .schemas import ValidationError


CATALOG_SOURCE_ID = "QUEBEC_PQI_ARCHIVE_CATALOG"
DASHBOARD_SOURCE_ID = "QUEBEC_PQI_PROJECT_DASHBOARD"
THRESHOLD_CHANGE_DATE = date(2020, 11, 1)
DATASET_ID = "67d85a7a-10af-4af0-b4da-abc64cfd735a"
MONTHS = {
    "janvier": 1,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
}
NAME_DATE_PATTERN = re.compile(
    r"tableau de bord en date du\s+(?P<day>\d{1,2}|1er)\s+"
    r"(?P<month>[a-z]+)(?:\s+(?P<year>\d{4}))?\s*$",
    re.IGNORECASE,
)
URL_YEAR_PATTERN = re.compile(r"(?P<year>20\d{2})[-_]?\d{2}[-_]?\d{2}")
REQUIRED_DASHBOARD_FIELDS = {
    "no_projet",
    "nom_projet",
    "cout_total",
    "date_fin_mise_en_service",
    "etat_avancement",
    "suivi_modifications",
    "secteur_activite",
    "region",
    "localisation",
    "nature_travaux",
}
CANONICAL_HEADER_ALIASES = {
    "de_projet": "no_projet",
    "nom_du_projet": "nom_projet",
    "date_de_mise_en_service": "date_fin_mise_en_service",
    "etat_d_avancement": "etat_avancement",
    "suivi_des_modifications": "suivi_modifications",
    "secteur_d_activite": "secteur_activite",
    "nom_de_l_infrastructure": "nom_infrastructure",
    "nature_des_travaux": "nature_travaux",
}


def sha256_bytes(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _normalize_french(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def parse_snapshot_date(resource: dict[str, Any]) -> date:
    normalized_name = _normalize_french(str(resource.get("name", "")).strip()).lower()
    match = NAME_DATE_PATTERN.fullmatch(normalized_name)
    if match is None:
        raise ValidationError(f"unparseable Quebec dashboard resource date: {resource.get('name')!r}")
    month_name = match.group("month")
    if month_name not in MONTHS:
        raise ValidationError(f"unknown French month in resource name: {month_name!r}")
    year_text = match.group("year")
    if year_text is None:
        url_match = URL_YEAR_PATTERN.search(str(resource.get("url", "")))
        if url_match is None:
            raise ValidationError("resource name omits year and URL does not supply one")
        year_text = url_match.group("year")
    day_text = match.group("day")
    return date(int(year_text), MONTHS[month_name], 1 if day_text == "1er" else int(day_text))


def verify_catalog_retrieval(catalog_path: Path) -> dict[str, Any]:
    manifest_path = catalog_path.with_suffix(catalog_path.suffix + ".manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read Quebec archive catalog retrieval: {exc}") from exc
    if manifest.get("source_id") != CATALOG_SOURCE_ID:
        raise ValidationError("Quebec archive catalog manifest source_id mismatch")
    if manifest.get("content_hash") != sha256_file(catalog_path):
        raise ValidationError("Quebec archive catalog hash mismatch")
    if payload.get("success") is not True or not isinstance(payload.get("result"), dict):
        raise ValidationError("Quebec archive catalog API response is unsuccessful")
    return payload


def inventory_csv_resources(catalog_payload: dict[str, Any]) -> list[dict[str, Any]]:
    resources = catalog_payload.get("result", {}).get("resources", [])
    if not isinstance(resources, list):
        raise ValidationError("Quebec archive catalog resources must be a list")
    inventory: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for resource in resources:
        if not isinstance(resource, dict) or str(resource.get("format", "")).upper() != "CSV":
            continue
        resource_id = str(resource.get("id", "")).strip()
        url = str(resource.get("url", "")).strip()
        if not resource_id or resource_id in seen_ids:
            raise ValidationError("Quebec archive catalog has a missing or duplicate CSV resource ID")
        if DATASET_ID not in url or not url.startswith("https://www.donneesquebec.ca/"):
            raise ValidationError(f"unexpected Quebec dashboard resource URL: {url!r}")
        seen_ids.add(resource_id)
        snapshot_date = parse_snapshot_date(resource)
        inventory.append(
            {
                "resource_id": resource_id,
                "resource_name": str(resource.get("name", "")).strip(),
                "snapshot_date": snapshot_date.isoformat(),
                "created": resource.get("created"),
                "last_modified": resource.get("last_modified"),
                "url": url,
                "threshold_regime": (
                    "cad_50m_and_over"
                    if snapshot_date < THRESHOLD_CHANGE_DATE
                    else "cad_20m_and_over"
                ),
            }
        )
    inventory.sort(key=lambda item: (item["snapshot_date"], item["resource_id"]))
    dates = [item["snapshot_date"] for item in inventory]
    if not inventory or len(dates) != len(set(dates)):
        raise ValidationError("Quebec CSV resource snapshot dates must be unique")
    return inventory


def inventory_tabular_resources(
    catalog_payload: dict[str, Any], formats: set[str]
) -> list[dict[str, Any]]:
    resources = catalog_payload.get("result", {}).get("resources", [])
    if not isinstance(resources, list):
        raise ValidationError("Quebec archive catalog resources must be a list")
    output: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        resource_format = str(resource.get("format", "")).upper()
        if resource_format not in formats:
            continue
        resource_id = str(resource.get("id", "")).strip()
        url = str(resource.get("url", "")).strip()
        if not resource_id or resource_id in seen_ids:
            raise ValidationError("Quebec archive catalog has a missing or duplicate resource ID")
        if DATASET_ID not in url or not url.startswith("https://www.donneesquebec.ca/"):
            raise ValidationError(f"unexpected Quebec dashboard resource URL: {url!r}")
        seen_ids.add(resource_id)
        snapshot_date = parse_snapshot_date(resource)
        output.append(
            {
                "resource_id": resource_id,
                "resource_name": str(resource.get("name", "")).strip(),
                "snapshot_date": snapshot_date.isoformat(),
                "created": resource.get("created"),
                "last_modified": resource.get("last_modified"),
                "url": url,
                "format": resource_format,
            }
        )
    return sorted(output, key=lambda item: (item["snapshot_date"], item["resource_id"]))


def canonical_field_name(value: str) -> str:
    normalized = _normalize_french(unicodedata.normalize("NFKC", value)).casefold()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return CANONICAL_HEADER_ALIASES.get(normalized, normalized)


def profile_csv_content(content: bytes) -> dict[str, Any]:
    text = _decode_csv(content)
    first_line = text.splitlines()[0] if text.splitlines() else ""
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    original_fields = [field.strip() for field in (reader.fieldnames or [])]
    canonical_fields = [canonical_field_name(field) for field in original_fields]
    missing_fields = REQUIRED_DASHBOARD_FIELDS - set(canonical_fields)
    if missing_fields:
        if (
            original_fields
            and "no_projet" in original_fields[0]
            and all(not field for field in original_fields[1:])
        ):
            profile = "publisher_wrapped_csv_unusable"
        else:
            profile = "unsupported_schema"
        return {
            "schema_profile": profile,
            "delimiter": delimiter,
            "original_fields": original_fields,
            "canonical_fields": canonical_fields,
            "missing_fields": sorted(missing_fields),
            "row_count": None,
        }
    rows = list(reader)
    if not rows:
        raise ValidationError("Quebec dashboard CSV contains no records")
    if any(None in row for row in rows):
        raise ValidationError("Quebec dashboard CSV contains over-wide records")
    return {
        "schema_profile": (
            "canonical_csv"
            if original_fields == canonical_fields
            else "legacy_header_aliases"
        ),
        "delimiter": delimiter,
        "original_fields": original_fields,
        "canonical_fields": canonical_fields,
        "missing_fields": [],
        "row_count": len(rows),
    }


def retrieve_full_archive_resources(
    catalog_path: Path,
    milestone_contract_path: Path,
    raw_root: Path,
    contract_path: Path,
) -> dict[str, Any]:
    payload = verify_catalog_retrieval(catalog_path)
    csv_inventory = inventory_csv_resources(payload)
    xlsx_inventory = inventory_tabular_resources(payload, {"XLSX"})
    xlsx_by_date = {item["snapshot_date"]: item for item in xlsx_inventory}
    try:
        milestone_contract = json.loads(milestone_contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read Quebec milestone contract: {exc}") from exc
    reused_by_id = {
        item["resource_id"]: item
        for item in milestone_contract.get("selected_vintages", [])
    }
    project_root = contract_path.resolve().parents[2]

    def contract_path_value(value: str) -> str:
        resolved = Path(value).resolve()
        try:
            return str(resolved.relative_to(project_root))
        except ValueError:
            return str(resolved)

    raw_root.mkdir(parents=True, exist_ok=True)
    resources: list[dict[str, Any]] = []
    for item in csv_inventory:
        reused = reused_by_id.get(item["resource_id"])
        if reused:
            archive_path = Path(str(reused["archive_path"]))
            manifest_path = archive_path.with_suffix(".csv.manifest.json")
            if sha256_file(archive_path) != reused.get("content_hash"):
                raise ValidationError(
                    f"reused Quebec archive hash mismatch: {item['snapshot_date']}"
                )
            content = archive_path.read_bytes()
            csv_record = {
                "archive_path": repository_path(archive_path),
                "manifest_path": repository_path(manifest_path),
                "content_hash": reused["content_hash"],
                "byte_length": reused["byte_length"],
                "retrieved_at": reused["retrieved_at"],
                "reused_milestone_archive": True,
            }
        else:
            downloaded = _download_catalog_resource(
                item,
                raw_root,
                suffix=".csv",
                source_id=DASHBOARD_SOURCE_ID,
            )
            archive_path = Path(downloaded["archive_path"])
            content = archive_path.read_bytes()
            csv_record = {**downloaded, "reused_milestone_archive": False}
        profile = profile_csv_content(content)
        fallback: dict[str, Any] | None = None
        if profile["schema_profile"] in {
            "publisher_wrapped_csv_unusable",
            "unsupported_schema",
        }:
            xlsx_item = xlsx_by_date.get(item["snapshot_date"])
            if xlsx_item is None:
                raise ValidationError(
                    "Quebec CSV requires a fallback but no paired XLSX exists: "
                    + item["snapshot_date"]
                )
            fallback = _download_catalog_resource(
                xlsx_item,
                raw_root,
                suffix=".xlsx",
                source_id=DASHBOARD_SOURCE_ID,
            )
            fallback = {
                **xlsx_item,
                **fallback,
                "substitution_reason": profile["schema_profile"],
            }
        resources.append(
            {
                **item,
                **{
                    **csv_record,
                    "archive_path": contract_path_value(csv_record["archive_path"]),
                    "manifest_path": contract_path_value(csv_record["manifest_path"]),
                },
                "schema_profile": profile["schema_profile"],
                "source_row_count": profile["row_count"],
                "original_fields": profile["original_fields"],
                "canonical_fields": profile["canonical_fields"],
                "missing_fields": profile["missing_fields"],
                "fallback_xlsx": (
                    {
                        **fallback,
                        "archive_path": contract_path_value(fallback["archive_path"]),
                        "manifest_path": contract_path_value(fallback["manifest_path"]),
                    }
                    if fallback
                    else None
                ),
            }
        )

    if len(resources) != 69 or len({item["snapshot_date"] for item in resources}) != 69:
        raise ValidationError("Quebec full archive contract must cover exactly 69 dates")
    fallback_count = sum(1 for item in resources if item["fallback_xlsx"])
    result = {
        "schema_version": "1.0.0",
        "contract_id": "AIIO_QUEBEC_PQI_FULL_ARCHIVE_0_1",
        "catalog_source_id": CATALOG_SOURCE_ID,
        "dashboard_source_id": DASHBOARD_SOURCE_ID,
        "catalog_content_hash": sha256_file(catalog_path),
        "catalog_csv_resource_count": len(csv_inventory),
        "snapshot_start_date": resources[0]["snapshot_date"],
        "snapshot_end_date": resources[-1]["snapshot_date"],
        "snapshot_date_count": len(resources),
        "direct_csv_snapshot_count": len(resources) - fallback_count,
        "paired_xlsx_fallback_count": fallback_count,
        "resources": resources,
        "publication_boundary": {
            "catalog_snapshot_coverage_contract_complete": True,
            "all_snapshots_parsed_directly_from_csv": fallback_count == 0,
            "project_exit_outcome_authorized": False,
            "public_project_cost_outcome_authorized": False,
            "public_project_schedule_outcome_authorized": False,
            "ai_attributable_effect_authorized": False,
            "status": "complete_catalog_intake_pending_normalization",
            "reason": "All 69 catalog dates are hash-locked. One malformed publisher CSV requires its official paired XLSX representation; normalization and outcome interpretation remain separate gates.",
        },
    }
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def select_milestone_resources(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not inventory:
        raise ValidationError("cannot select Quebec milestones from an empty inventory")
    dated = [(date.fromisoformat(item["snapshot_date"]), item) for item in inventory]
    pre_threshold = [pair for pair in dated if pair[0] < THRESHOLD_CHANGE_DATE]
    post_threshold = [pair for pair in dated if pair[0] >= THRESHOLD_CHANGE_DATE]
    if not pre_threshold or not post_threshold:
        raise ValidationError("Quebec archive must span both publication-threshold regimes")

    selected_by_id: dict[str, tuple[dict[str, Any], set[str]]] = {}

    def include(item: dict[str, Any], reason: str) -> None:
        existing = selected_by_id.setdefault(item["resource_id"], (item, set()))
        existing[1].add(reason)

    include(dated[0][1], "earliest_official_csv")
    include(pre_threshold[-1][1], "last_pre_threshold_snapshot")
    include(post_threshold[0][1], "first_post_threshold_snapshot")
    years = sorted({snapshot_date.year for snapshot_date, _ in dated})
    for year in years:
        year_items = [pair for pair in dated if pair[0].year == year]
        include(year_items[-1][1], "latest_snapshot_in_calendar_year")
    include(dated[-1][1], "latest_official_csv")

    output: list[dict[str, Any]] = []
    for item, reasons in sorted(
        selected_by_id.values(), key=lambda pair: pair[0]["snapshot_date"]
    ):
        output.append({**item, "selection_reasons": sorted(reasons)})
    return output


def milestone_candidate_slots(
    inventory: list[dict[str, Any]],
) -> list[tuple[str, list[dict[str, Any]]]]:
    if not inventory:
        raise ValidationError("cannot select Quebec milestones from an empty inventory")
    dated = [(date.fromisoformat(item["snapshot_date"]), item) for item in inventory]
    pre_threshold = [pair for pair in dated if pair[0] < THRESHOLD_CHANGE_DATE]
    post_threshold = [pair for pair in dated if pair[0] >= THRESHOLD_CHANGE_DATE]
    if not pre_threshold or not post_threshold:
        raise ValidationError("Quebec archive must span both publication-threshold regimes")
    slots: list[tuple[str, list[dict[str, Any]]]] = [
        ("earliest_official_csv", [item for _, item in dated]),
        (
            "last_pre_threshold_snapshot",
            [item for _, item in reversed(pre_threshold)],
        ),
        ("first_post_threshold_snapshot", [item for _, item in post_threshold]),
    ]
    for year in sorted({snapshot_date.year for snapshot_date, _ in dated}):
        year_items = [item for snapshot_date, item in dated if snapshot_date.year == year]
        slots.append(
            (f"latest_schema_valid_snapshot_in_{year}", list(reversed(year_items)))
        )
    slots.append(("latest_official_csv", [item for _, item in reversed(dated)]))
    return slots


def retrieve_milestone_resources(
    catalog_path: Path,
    raw_root: Path,
    contract_path: Path,
) -> dict[str, Any]:
    payload = verify_catalog_retrieval(catalog_path)
    inventory = inventory_csv_resources(payload)
    raw_root.mkdir(parents=True, exist_ok=True)
    retrieved_by_id: dict[str, tuple[dict[str, Any], dict[str, Any], set[str]]] = {}
    rejected_by_id: dict[str, dict[str, Any]] = {}
    for reason, candidates in milestone_candidate_slots(inventory):
        selected_for_slot = False
        for item in candidates:
            if item["resource_id"] in retrieved_by_id:
                retrieved_by_id[item["resource_id"]][2].add(reason)
                selected_for_slot = True
                break
            if item["resource_id"] in rejected_by_id:
                continue
            try:
                record = _retrieve_resource(item, raw_root)
            except ValidationError as exc:
                rejected_by_id[item["resource_id"]] = {
                    "resource_id": item["resource_id"],
                    "resource_name": item["resource_name"],
                    "snapshot_date": item["snapshot_date"],
                    "url": item["url"],
                    "reason": str(exc),
                }
                continue
            retrieved_by_id[item["resource_id"]] = (item, record, {reason})
            selected_for_slot = True
            break
        if not selected_for_slot:
            raise ValidationError(f"no schema-valid Quebec resource satisfies slot: {reason}")
    retrieved = [
        {**item, **record, "selection_reasons": sorted(reasons)}
        for item, record, reasons in sorted(
            retrieved_by_id.values(), key=lambda triple: triple[0]["snapshot_date"]
        )
    ]

    result = {
        "schema_version": "1.0.0",
        "contract_id": "AIIO_QUEBEC_PQI_MILESTONE_VINTAGES_0_1",
        "catalog_source_id": CATALOG_SOURCE_ID,
        "dashboard_source_id": DASHBOARD_SOURCE_ID,
        "catalog_content_hash": sha256_file(catalog_path),
        "catalog_csv_resource_count": len(inventory),
        "catalog_start_date": inventory[0]["snapshot_date"],
        "catalog_end_date": inventory[-1]["snapshot_date"],
        "threshold_change_date": THRESHOLD_CHANGE_DATE.isoformat(),
        "selection_rule": {
            "earliest_official_csv": True,
            "last_pre_threshold_snapshot": True,
            "first_post_threshold_snapshot": True,
            "latest_snapshot_in_each_calendar_year": True,
            "schema_invalid_candidates_fall_back_with_audit_record": True,
            "latest_official_csv": True,
            "complete_monthly_panel": False,
        },
        "selected_vintage_count": len(retrieved),
        "selected_vintages": retrieved,
        "rejected_candidate_count": len(rejected_by_id),
        "rejected_candidates": sorted(
            rejected_by_id.values(), key=lambda item: item["snapshot_date"]
        ),
        "publication_boundary": {
            "longitudinal_outcome_panel_authorized": False,
            "attrition_interpretation_authorized": False,
            "ai_attributable_effect_authorized": False,
            "status": "milestone_vintage_research_candidate",
            "reason": "The milestone design can reveal entry, persistence and interval disappearance across official snapshots, including the November 2020 threshold change, but it is not the complete 69-vintage panel and disappearance does not identify completion, cancellation or another exit cause.",
        },
    }
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _retrieve_resource(item: dict[str, Any], raw_root: Path) -> dict[str, Any]:
    request = urllib.request.Request(
        item["url"],
        headers={"User-Agent": "AIIO-Canada-Research/0.1 (+public research retrieval)"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        content = response.read()
        effective_url = response.geturl()
        content_type = response.headers.get_content_type()
    if effective_url != item["url"]:
        raise ValidationError("Quebec milestone resource redirected unexpectedly")
    text = _decode_csv(content)
    delimiter = ";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    normalized_fields = {field.strip() for field in (reader.fieldnames or [])}
    missing_fields = REQUIRED_DASHBOARD_FIELDS - normalized_fields
    if not rows or missing_fields:
        raise ValidationError(
            "Quebec milestone CSV schema is incomplete "
            f"for {item['snapshot_date']}: missing {sorted(missing_fields)}"
        )
    digest = sha256_bytes(content)
    destination = raw_root / f"{item['snapshot_date']}_{digest.split(':', 1)[1][:12]}.csv"
    manifest_path = destination.with_suffix(".csv.manifest.json")
    if destination.exists() and sha256_file(destination) != digest:
        raise ValidationError(f"existing Quebec milestone archive hash mismatch: {destination}")
    if not destination.exists():
        destination.write_bytes(content)
    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    if manifest_path.exists():
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing_manifest.get("content_hash") != digest:
            raise ValidationError(f"existing Quebec milestone manifest hash mismatch: {manifest_path}")
        retrieved_at = existing_manifest["retrieved_at"]
    manifest = {
        "retrieval_id": f"RET_{DASHBOARD_SOURCE_ID}_{item['resource_id'].replace('-', '')[:12]}",
        "source_id": DASHBOARD_SOURCE_ID,
        "archive_catalog_source_id": CATALOG_SOURCE_ID,
        "resource_id": item["resource_id"],
        "resource_name": item["resource_name"],
        "snapshot_date": item["snapshot_date"],
        "threshold_regime": item["threshold_regime"],
        "retrieved_at": retrieved_at,
        "effective_url": effective_url,
        "content_hash": digest,
        "content_type": content_type,
        "byte_length": len(content),
        "row_count": len(rows),
        "archive_path": repository_path(destination),
        "result": "success",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "archive_path": repository_path(destination),
        "manifest_path": repository_path(manifest_path),
        "content_hash": digest,
        "byte_length": len(content),
        "row_count": len(rows),
        "retrieved_at": retrieved_at,
    }


def _download_catalog_resource(
    item: dict[str, Any],
    raw_root: Path,
    *,
    suffix: str,
    source_id: str,
) -> dict[str, Any]:
    for manifest_path in sorted(raw_root.glob(f"*{suffix}.manifest.json")):
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if existing_manifest.get("resource_id") != item["resource_id"]:
            continue
        destination = Path(str(existing_manifest.get("archive_path", "")))
        if not destination.is_absolute():
            destination = raw_root / destination.name
        if not destination.exists():
            raise ValidationError(
                f"existing Quebec full-archive file is missing: {destination}"
            )
        digest = sha256_file(destination)
        if existing_manifest.get("content_hash") != digest:
            raise ValidationError(
                f"existing Quebec full-archive manifest hash mismatch: {manifest_path}"
            )
        if existing_manifest.get("effective_url") != item["url"]:
            raise ValidationError(
                f"existing Quebec full-archive URL mismatch: {manifest_path}"
            )
        return {
            "archive_path": repository_path(destination),
            "manifest_path": repository_path(manifest_path),
            "content_hash": digest,
            "byte_length": destination.stat().st_size,
            "retrieved_at": existing_manifest["retrieved_at"],
        }
    request = urllib.request.Request(
        item["url"],
        headers={"User-Agent": "AIIO-Canada-Research/0.1 (+public research retrieval)"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        content = response.read()
        effective_url = response.geturl()
        content_type = response.headers.get_content_type()
    if effective_url != item["url"]:
        raise ValidationError("Quebec full-archive resource redirected unexpectedly")
    digest = sha256_bytes(content)
    destination = raw_root / f"{item['snapshot_date']}_{digest.split(':', 1)[1][:12]}{suffix}"
    manifest_path = destination.with_suffix(destination.suffix + ".manifest.json")
    if destination.exists() and sha256_file(destination) != digest:
        raise ValidationError(f"existing Quebec full-archive hash mismatch: {destination}")
    if not destination.exists():
        destination.write_bytes(content)
    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    if manifest_path.exists():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValidationError(
                f"unable to read existing Quebec full-archive manifest: {exc}"
            ) from exc
        if existing_manifest.get("content_hash") != digest:
            raise ValidationError(
                f"existing Quebec full-archive manifest hash mismatch: {manifest_path}"
            )
        retrieved_at = existing_manifest["retrieved_at"]
    manifest = {
        "retrieval_id": f"RET_{source_id}_{item['resource_id'].replace('-', '')[:12]}",
        "source_id": source_id,
        "archive_catalog_source_id": CATALOG_SOURCE_ID,
        "resource_id": item["resource_id"],
        "resource_name": item["resource_name"],
        "snapshot_date": item["snapshot_date"],
        "format": str(item.get("format", suffix.lstrip("."))).upper(),
        "retrieved_at": retrieved_at,
        "effective_url": effective_url,
        "content_hash": digest,
        "content_type": content_type,
        "byte_length": len(content),
        "archive_path": repository_path(destination),
        "result": "success",
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "archive_path": repository_path(destination),
        "manifest_path": repository_path(manifest_path),
        "content_hash": digest,
        "byte_length": len(content),
        "retrieved_at": retrieved_at,
    }


def _decode_csv(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValidationError("Quebec milestone CSV is not valid UTF-8 or CP1252")
