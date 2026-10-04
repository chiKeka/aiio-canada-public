from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from ..schemas import ValidationError


TENDER_SOURCE_ID = "CANADABUYS_TENDER_NOTICES_FY2026_2027"
AWARD_SOURCE_ID = "CANADABUYS_AWARD_NOTICES_FY2026_2027"
CONTRACT_SOURCE_ID = "CANADABUYS_CONTRACT_HISTORY_FY2026_2027"
TRANSFORMATION_ID = "TR_CANADABUYS_PROCUREMENT_OUTCOME_FEASIBILITY_0_1"

TITLE = "title-titre-eng"
REFERENCE = "referenceNumber-numeroReference"
AMENDMENT = "amendmentNumber-numeroModification"
SOLICITATION = "solicitationNumber-numeroSollicitation"
CATEGORY = "procurementCategory-categorieApprovisionnement"
REGION = "regionsOfDelivery-regionsLivraison-eng"
PUBLICATION_DATE = "publicationDate-datePublication"
TENDER_CLOSE = "tenderClosingDate-appelOffresDateCloture"
TENDER_STATUS = "tenderStatus-appelOffresStatut-eng"
AWARD_DATE = "contractAwardDate-dateAttributionContrat"
CONTRACT_NUMBER = "contractNumber-numeroContrat"
CONTRACT_AMOUNT = "contractAmount-montantContrat"
TOTAL_CONTRACT_VALUE = "totalContractValue-valeurTotaleContrat"
CURRENCY = "contractCurrency-contratMonnaie"
CONTRACT_START = "contractStartDate-contratDateDebut"
CONTRACT_END = "contractEndDate-dateFinContrat"
AMENDMENT_TYPE = "amendmentType-typeModification-eng"

TENDER_REQUIRED_FIELDS = {
    TITLE,
    REFERENCE,
    AMENDMENT,
    SOLICITATION,
    PUBLICATION_DATE,
    TENDER_CLOSE,
    TENDER_STATUS,
    CATEGORY,
    REGION,
}
AWARD_REQUIRED_FIELDS = {
    TITLE,
    REFERENCE,
    AMENDMENT,
    SOLICITATION,
    CONTRACT_NUMBER,
    PUBLICATION_DATE,
    AWARD_DATE,
    CONTRACT_START,
    CONTRACT_END,
    CONTRACT_AMOUNT,
    TOTAL_CONTRACT_VALUE,
    CURRENCY,
    CATEGORY,
    REGION,
}
CONTRACT_REQUIRED_FIELDS = AWARD_REQUIRED_FIELDS | {AMENDMENT_TYPE}

OUTPUT_FIELDS = (
    "procurement_linkage_id",
    "physical_project_id",
    "solicitation_number",
    "title",
    "procurement_category",
    "geography_id",
    "geography_label",
    "geography_evidence_status",
    "tender_reference_number",
    "tender_publication_date",
    "tender_close_date",
    "tender_duration_days",
    "tender_status",
    "award_record_count",
    "award_date",
    "reported_award_value_cad",
    "contract_record_count",
    "contract_number_count",
    "contract_amendment_row_count",
    "reported_total_contract_value_cad",
    "reported_contract_start_date",
    "reported_contract_end_date",
    "independent_estimate_value_cad",
    "estimate_price_basis_date",
    "approved_change_value_cad",
    "actual_completion_date",
    "compliant_bidder_count",
    "cost_outcome_status",
    "schedule_outcome_status",
    "competition_outcome_status",
    "source_ids",
    "source_evidence_status",
    "evidence_status",
    "transformation_id",
    "quality_flags",
)

PROVINCE_TOKENS = {
    "Newfoundland and Labrador": ("PR_10", "Newfoundland and Labrador"),
    "Prince Edward Island": ("PR_11", "Prince Edward Island"),
    "Nova Scotia": ("PR_12", "Nova Scotia"),
    "New Brunswick": ("PR_13", "New Brunswick"),
    "Quebec": ("PR_24", "Quebec"),
    "Ontario": ("PR_35", "Ontario"),
    "Manitoba": ("PR_46", "Manitoba"),
    "Saskatchewan": ("PR_47", "Saskatchewan"),
    "Alberta": ("PR_48", "Alberta"),
    "British Columbia": ("PR_59", "British Columbia"),
    "Yukon": ("PR_60", "Yukon"),
    "Northwest Territories": ("PR_61", "Northwest Territories"),
    "Nunavut": ("PR_62", "Nunavut"),
}


def normalize_canadabuys_outcome_intake(
    tender_path: Path,
    award_path: Path,
    contract_path: Path,
    output_path: Path,
    report_path: Path,
    *,
    retrieval_manifest_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    tenders = read_rows(tender_path, TENDER_REQUIRED_FIELDS, TENDER_SOURCE_ID)
    awards = read_rows(award_path, AWARD_REQUIRED_FIELDS, AWARD_SOURCE_ID)
    contracts = read_rows(contract_path, CONTRACT_REQUIRED_FIELDS, CONTRACT_SOURCE_ID)

    by_source = {
        TENDER_SOURCE_ID: group_by_link_key(tenders, TENDER_SOURCE_ID),
        AWARD_SOURCE_ID: group_by_link_key(awards, AWARD_SOURCE_ID),
        CONTRACT_SOURCE_ID: group_by_link_key(contracts, CONTRACT_SOURCE_ID),
    }
    construction_keys = {
        key
        for source_groups in by_source.values()
        for key, rows in source_groups.items()
        if any(is_construction(row) for row in rows)
    }
    if not construction_keys:
        raise ValidationError("CanadaBuys intake contains no construction procurement rows")

    output_rows = []
    for key in sorted(construction_keys):
        tender_rows = by_source[TENDER_SOURCE_ID].get(key, [])
        award_rows = by_source[AWARD_SOURCE_ID].get(key, [])
        contract_rows = by_source[CONTRACT_SOURCE_ID].get(key, [])
        output_rows.append(build_linkage_row(key, tender_rows, award_rows, contract_rows))

    write_rows(output_path, output_rows)
    geography_counts = Counter(row["geography_evidence_status"] for row in output_rows)
    report = {
        "schema_version": "0.1.0",
        "model_id": "AIIO_CANADABUYS_PROCUREMENT_OUTCOME_FEASIBILITY_0_1",
        "transformation_id": TRANSFORMATION_ID,
        "as_of_date": "2026-08-31",
        "evidence_status": "observed_procurement_fields_with_inferred_linkage_and_geography",
        "source_ids": [TENDER_SOURCE_ID, AWARD_SOURCE_ID, CONTRACT_SOURCE_ID],
        "input_sha256": {
            TENDER_SOURCE_ID: sha256_path(tender_path),
            AWARD_SOURCE_ID: sha256_path(award_path),
            CONTRACT_SOURCE_ID: sha256_path(contract_path),
        },
        "retrieval_manifest_sha256": {
            source_id: sha256_path(path)
            for source_id, path in sorted((retrieval_manifest_paths or {}).items())
            if path.exists()
        },
        "output_sha256": sha256_path(output_path),
        "source_row_counts": {
            TENDER_SOURCE_ID: len(tenders),
            AWARD_SOURCE_ID: len(awards),
            CONTRACT_SOURCE_ID: len(contracts),
        },
        "construction_linkage_count": len(output_rows),
        "linked_tender_award_count": sum(
            bool(
                row["tender_reference_number"]
                and int(row["award_record_count"]) > 0
            )
            for row in output_rows
        ),
        "linked_tender_contract_count": sum(
            bool(
                row["tender_reference_number"]
                and int(row["contract_record_count"]) > 0
            )
            for row in output_rows
        ),
        "single_province_geography_count": geography_counts["inferred_single_province"],
        "cma_geography_count": 0,
        "field_availability": {
            "tender_open_date": availability_count(output_rows, "tender_publication_date"),
            "tender_close_date": availability_count(output_rows, "tender_close_date"),
            "award_date": availability_count(output_rows, "award_date"),
            "reported_award_value_cad": availability_count(
                output_rows, "reported_award_value_cad"
            ),
            "reported_contract_start_date": availability_count(
                output_rows, "reported_contract_start_date"
            ),
            "reported_contract_end_date": availability_count(
                output_rows, "reported_contract_end_date"
            ),
            "independent_estimate_with_price_basis": 0,
            "complete_approved_change_history": 0,
            "actual_physical_completion_date": 0,
            "compliant_bidder_count": 0,
            "physical_project_identifier": 0,
            "cma_geography": 0,
        },
        "publication_boundary": {
            "status": "procurement_feasibility_only",
            "public_project_cost_outcome_authorized": False,
            "public_project_schedule_outcome_authorized": False,
            "procurement_competition_outcome_authorized": False,
            "ai_attributable_effect_authorized": False,
            "reason": (
                "The current-fiscal-year CanadaBuys files expose useful tender, award and "
                "contract fields, but do not identify a stable physical project, independent "
                "estimate with price basis, complete approved-change history, actual physical "
                "completion, compliant bidder count or CMA geography."
            ),
        },
        "limitations": [
            "The intake covers federal CanadaBuys files for fiscal year 2026-2027, not a national census of provincial, municipal or broader-public-sector construction.",
            "Solicitation-number joins are inferred record linkages and are not stable physical-project identifiers.",
            "Reported contract start and end dates describe procurement instruments and cannot be interpreted as physical construction start or completion.",
            "Delivery regions are publisher labels; the source does not provide a consistent CMA project location.",
            "No contact names, emails, phone numbers, supplier addresses or free-text descriptions are carried into the processed output.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def read_rows(path: Path, required_fields: set[str], source_id: str) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        missing = required_fields - fields
        if missing:
            raise ValidationError(
                f"{source_id} schema changed; missing fields: {sorted(missing)}"
            )
        rows = [{key: clean_text(value) for key, value in row.items()} for row in reader]
    if not rows:
        raise ValidationError(f"{source_id} input is empty")
    return rows


def clean_text(value: str | None) -> str:
    return " ".join((value or "").split())


def group_by_link_key(
    rows: Iterable[dict[str, str]], source_id: str
) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        solicitation = row.get(SOLICITATION, "").strip()
        reference = row.get(REFERENCE, "").strip()
        key = solicitation or f"{source_id}:{reference}"
        groups[key].append(row)
    return groups


def build_linkage_row(
    key: str,
    tenders: list[dict[str, str]],
    awards: list[dict[str, str]],
    contracts: list[dict[str, str]],
) -> dict[str, str]:
    tender = latest_row(tenders, PUBLICATION_DATE)
    award = latest_row(awards, AWARD_DATE)
    contract = latest_row(contracts, PUBLICATION_DATE)
    title = first_value(tender, award, contract, field=TITLE)
    region = first_value(tender, award, contract, field=REGION)
    geography_id, geography_label, geography_status = map_region(region)
    open_date = iso_date(first_value(tender, field=PUBLICATION_DATE))
    close_date = iso_date(first_value(tender, field=TENDER_CLOSE))
    award_date = max_iso(row.get(AWARD_DATE, "") for row in awards)
    contract_start = min_iso(row.get(CONTRACT_START, "") for row in contracts or awards)
    contract_end = max_iso(row.get(CONTRACT_END, "") for row in contracts or awards)
    duration = date_difference(open_date, close_date)
    award_value = sum_cad_values(awards, CONTRACT_AMOUNT)
    latest_contract_values = latest_total_by_contract(contracts)
    total_contract_value = sum(latest_contract_values.values()) if latest_contract_values else None
    contract_numbers = {row.get(CONTRACT_NUMBER, "") for row in contracts if row.get(CONTRACT_NUMBER, "")}
    amendment_rows = sum(is_amendment(row) for row in contracts)
    source_ids = [
        source_id
        for source_id, rows in (
            (TENDER_SOURCE_ID, tenders),
            (AWARD_SOURCE_ID, awards),
            (CONTRACT_SOURCE_ID, contracts),
        )
        if rows
    ]
    flags = {
        "fiscal_year_2026_2027_snapshot_only",
        "federal_scope_only",
        "solicitation_linkage_not_physical_project_id",
        "region_not_cma",
        "independent_estimate_missing",
        "complete_approved_change_history_missing",
        "actual_physical_completion_missing",
        "compliant_bidder_count_missing",
    }
    if not tenders:
        flags.add("tender_link_missing")
    if not awards:
        flags.add("award_link_missing")
    elif award_value is None:
        flags.add("reported_award_value_missing_or_zero")
    if not contracts:
        flags.add("contract_history_link_missing")
    elif total_contract_value is None:
        flags.add("reported_total_contract_value_missing_or_zero")
    if geography_status != "inferred_single_province":
        flags.add("single_province_geography_unavailable")
    return {
        "procurement_linkage_id": stable_id(key),
        "physical_project_id": "",
        "solicitation_number": key if ":" not in key else "",
        "title": title,
        "procurement_category": "construction",
        "geography_id": geography_id,
        "geography_label": geography_label,
        "geography_evidence_status": geography_status,
        "tender_reference_number": first_value(tender, field=REFERENCE),
        "tender_publication_date": open_date,
        "tender_close_date": close_date,
        "tender_duration_days": "" if duration is None else str(duration),
        "tender_status": first_value(tender, field=TENDER_STATUS),
        "award_record_count": str(len(awards)),
        "award_date": award_date,
        "reported_award_value_cad": format_number(award_value),
        "contract_record_count": str(len(contracts)),
        "contract_number_count": str(len(contract_numbers)),
        "contract_amendment_row_count": str(amendment_rows),
        "reported_total_contract_value_cad": format_number(total_contract_value),
        "reported_contract_start_date": contract_start,
        "reported_contract_end_date": contract_end,
        "independent_estimate_value_cad": "",
        "estimate_price_basis_date": "",
        "approved_change_value_cad": "",
        "actual_completion_date": "",
        "compliant_bidder_count": "",
        "cost_outcome_status": "missing_required_fields",
        "schedule_outcome_status": "missing_required_fields",
        "competition_outcome_status": "missing_compliant_bidder_count",
        "source_ids": "|".join(source_ids),
        "source_evidence_status": "observed",
        "evidence_status": "inferred_linkage_screen",
        "transformation_id": TRANSFORMATION_ID,
        "quality_flags": "|".join(sorted(flags)),
    }


def is_construction(row: dict[str, str]) -> bool:
    tokens = row.get(CATEGORY, "").replace("*", " ").replace(";", " ").split()
    return "CNST" in tokens


def latest_row(rows: list[dict[str, str]], date_field: str) -> dict[str, str]:
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            iso_date(row.get(date_field, "")),
            amendment_rank(row.get(AMENDMENT, "")),
            row.get(REFERENCE, ""),
        ),
    )


def latest_total_by_contract(rows: list[dict[str, str]]) -> dict[str, float]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get(CURRENCY, "").upper() != "CAD":
            continue
        contract_number = row.get(CONTRACT_NUMBER, "") or row.get(REFERENCE, "")
        if contract_number:
            grouped[contract_number].append(row)
    totals = {}
    for contract_number, items in grouped.items():
        latest = latest_row(items, PUBLICATION_DATE)
        value = optional_number(latest.get(TOTAL_CONTRACT_VALUE, ""))
        if value is not None and value > 0:
            totals[contract_number] = value
    return totals


def map_region(value: str) -> tuple[str, str, str]:
    matches = [mapping for token, mapping in PROVINCE_TOKENS.items() if token in value]
    matches = list(dict.fromkeys(matches))
    if len(matches) == 1 and "National Capital Region" not in value and "Canada" not in value:
        return matches[0][0], matches[0][1], "inferred_single_province"
    if "National Capital Region" in value and not matches:
        return "REGION_NCR", "National Capital Region", "inferred_ambiguous_region"
    if len(matches) > 1:
        return "REGION_MULTI", "Multiple provinces or territories", "inferred_multi_region"
    if "Canada" in value:
        return "CAN", "Canada", "observed_national_region"
    return "", value, "missing_or_unmapped_region"


def first_value(*rows: dict[str, str], field: str) -> str:
    return next((row.get(field, "") for row in rows if row.get(field, "")), "")


def iso_date(value: str) -> str:
    token = value.strip()[:10]
    if not token:
        return ""
    try:
        return date.fromisoformat(token).isoformat()
    except ValueError:
        return ""


def min_iso(values: Iterable[str]) -> str:
    dates = [iso_date(value) for value in values]
    return min((value for value in dates if value), default="")


def max_iso(values: Iterable[str]) -> str:
    dates = [iso_date(value) for value in values]
    return max((value for value in dates if value), default="")


def date_difference(start: str, end: str) -> int | None:
    if not start or not end:
        return None
    return (date.fromisoformat(end) - date.fromisoformat(start)).days


def amendment_rank(value: str) -> tuple[int, str]:
    token = value.strip()
    try:
        return int(token), token
    except ValueError:
        return -1, token


def is_amendment(row: dict[str, str]) -> bool:
    kind = row.get(AMENDMENT_TYPE, "").strip().lower()
    return kind not in {"", "original"} or amendment_rank(row.get(AMENDMENT, ""))[0] > 0


def optional_number(value: str) -> float | None:
    token = value.replace(",", "").strip()
    if not token:
        return None
    try:
        return float(token)
    except ValueError:
        return None


def sum_cad_values(rows: list[dict[str, str]], field: str) -> float | None:
    values = [
        optional_number(row.get(field, ""))
        for row in rows
        if row.get(CURRENCY, "").upper() == "CAD"
    ]
    observed = [value for value in values if value is not None and value > 0]
    return sum(observed) if observed else None


def format_number(value: float | None) -> str:
    return "" if value is None else format(value, ".2f")


def availability_count(rows: list[dict[str, str]], field: str) -> int:
    return sum(row[field] not in {"", None} for row in rows)


def stable_id(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:20].upper()
    return f"CBUY_{digest}"


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_path(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
