from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..constants import EvidenceStatus
from ..schemas import PublicProjectRecord, ValidationError


TRANSFORMATION_ID = "AIIO_PROVINCIAL_PUBLIC_PROJECTS_0_1"
SCHEMA_VERSION = "1.0.0"

BC_SOURCE_ID = "BC_MAJOR_PROJECTS_INVENTORY"
ONTARIO_SOURCE_ID = "ONTARIO_BUILDS_PROJECTS"
QUEBEC_SOURCE_ID = "QUEBEC_PQI_PROJECT_DASHBOARD"

BC_GEOGRAPHY = ("PR_59", "British Columbia")
ONTARIO_GEOGRAPHY = ("PR_35", "Ontario")
QUEBEC_GEOGRAPHY = ("PR_24", "Quebec")

CSV_FIELDS = tuple(PublicProjectRecord.__dataclass_fields__.keys())

BC_REQUIRED_FIELDS = {
    "PROJECT_ID",
    "PROJECT_NAME",
    "PROJECT_DESCRIPTION",
    "ESTIMATED_COST",
    "PROJECT_CATEGORY_NAME",
    "PROJECT_TYPE",
    "CONSTRUCTION_SUBTYPE",
    "REGION",
    "MUNICIPALITY",
    "DEVELOPER",
    "PROJECT_STATUS",
    "PROJECT_STAGE",
    "PUBLIC_FUNDING_IND",
    "CLEAN_ENERGY_IND",
    "STANDARDIZED_START_DATE",
    "STANDARDIZED_COMPLETION_DATE",
    "LATITUDE",
    "LONGITUDE",
    "PROJECT_WEBSITE",
}

ONTARIO_REQUIRED_FIELDS = {
    "Category",
    "Supporting Ministry",
    "Community",
    "Project",
    "Status",
    "Target Completion Date",
    "Description",
    "Result",
    "Area",
    "Region",
    "Address",
    "Highway / Transit Line",
    "Estimated Total Budget ($)",
    "Municipal Funding",
    "Provincial Funding",
    "Federal Funding",
    "Other Funding",
    "Website",
    "Latitude",
    "Longitude",
}

QUEBEC_REQUIRED_FIELDS = {
    "no_projet",
    "nom_projet",
    "description",
    "cout_total",
    "contribution_quebec",
    "contribution_partenaires",
    "date_fin_mise_en_service",
    "etat_avancement",
    "ministre",
    "organisme",
    "gestionnaire",
    "secteur_activite",
    "region",
    "nom_infrastructure",
    "localisation",
    "nature_travaux",
}


def normalize_provincial_projects(
    bc_geojson_path: Path,
    ontario_csv_path: Path,
    quebec_csv_path: Path,
    output_csv_path: Path,
    output_report_path: Path,
    *,
    source_as_of_dates: dict[str, str],
) -> dict[str, Any]:
    required_dates = {BC_SOURCE_ID, ONTARIO_SOURCE_ID, QUEBEC_SOURCE_ID}
    if required_dates != set(source_as_of_dates):
        raise ValidationError(
            "provincial project normalization requires exact source as-of dates for "
            + ", ".join(sorted(required_dates))
        )

    bc_records, bc_diagnostic = normalize_bc_projects(
        bc_geojson_path, source_as_of_dates[BC_SOURCE_ID]
    )
    ontario_records, ontario_diagnostic = normalize_ontario_projects(
        ontario_csv_path, source_as_of_dates[ONTARIO_SOURCE_ID]
    )
    quebec_records, quebec_diagnostic = normalize_quebec_projects(
        quebec_csv_path, source_as_of_dates[QUEBEC_SOURCE_ID]
    )
    records = sorted(
        [*bc_records, *ontario_records, *quebec_records],
        key=lambda item: (item.geography_id, item.project_id),
    )
    if len({item.project_id for item in records}) != len(records):
        raise ValidationError("normalized provincial project_id values must be unique")

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["source_evidence_status"] = record.source_evidence_status.value
            row["quality_flags"] = "|".join(record.quality_flags)
            writer.writerow(row)

    report = {
        "schema_version": SCHEMA_VERSION,
        "transformation_id": TRANSFORMATION_ID,
        "as_of_date": max(source_as_of_dates.values()),
        "evidence_status": "observed_with_inferred_cross_source_classification",
        "record_count": len(records),
        "geography_count": len({item.geography_id for item in records}),
        "source_count": 3,
        "input_hashes": {
            BC_SOURCE_ID: _sha256(bc_geojson_path),
            ONTARIO_SOURCE_ID: _sha256(ontario_csv_path),
            QUEBEC_SOURCE_ID: _sha256(quebec_csv_path),
        },
        "output_schema": list(CSV_FIELDS),
        "source_diagnostics": [
            bc_diagnostic,
            ontario_diagnostic,
            quebec_diagnostic,
        ],
        "asset_class_counts": dict(
            sorted(Counter(item.asset_class for item in records).items())
        ),
        "quality_flag_counts": dict(
            sorted(Counter(flag for item in records for flag in item.quality_flags).items())
        ),
        "publication_boundary": {
            "status": "research_evidence_only",
            "public_project_exposure_authorized": False,
            "reason": "Source inventories have different scopes, thresholds, vintages and schedule completeness. Normalized records support comparison and source audit; they do not yet authorize pooled project counts, cost totals, causal exposure estimates or AI-attributable escalation claims.",
        },
        "limitations": [
            "The three sources are not a uniform national capital-project census and must not be pooled without source-scope controls.",
            "Asset classes are controlled-vocabulary inferences from publisher fields and project text; original categories are retained.",
            "Missing, suppressed and zero-placeholder costs remain null and are never treated as zero investment.",
            "Most Ontario and Quebec records do not publish a construction start period, so schedule overlap is not yet comparable with Alberta.",
            "British Columbia feature-layer records carry a 2024-12-01 feature vintage and the inventory was subsequently discontinued; the source is historical, not current market coverage.",
            "Ontario describes its dataset as a sample of key infrastructure projects, not a complete plan.",
            "Quebec coverage is limited to projects of at least $20 million in the Plan québécois des infrastructures.",
        ],
    }
    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    output_report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def normalize_bc_projects(
    geojson_path: Path, as_of_date: str
) -> tuple[list[PublicProjectRecord], dict[str, Any]]:
    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection" or not isinstance(
        payload.get("features"), list
    ):
        raise ValidationError("BC Major Projects payload must be a GeoJSON FeatureCollection")
    features = payload["features"]
    if not features:
        raise ValidationError("BC Major Projects feature collection cannot be empty")
    fields = set((features[0].get("properties") or {}).keys())
    _validate_fields(fields, BC_REQUIRED_FIELDS, BC_SOURCE_ID)

    records: list[PublicProjectRecord] = []
    for feature in features:
        raw = feature.get("properties") or {}
        _validate_fields(set(raw), BC_REQUIRED_FIELDS, BC_SOURCE_ID)
        flags = ["source_inventory_discontinued", "source_feature_vintage_2024_12_01"]
        cost = _million_cost(raw.get("ESTIMATED_COST"))
        if cost is None:
            flags.append("missing_estimated_cost")
        start_period = _text(raw.get("STANDARDIZED_START_DATE"))
        completion_period = _text(raw.get("STANDARDIZED_COMPLETION_DATE"))
        start_year = _first_four_digit_year(start_period)
        end_year = _first_four_digit_year(completion_period)
        _schedule_flags(flags, start_period, completion_period, start_year, end_year)
        latitude = _optional_float(raw.get("LATITUDE"))
        longitude = _optional_float(raw.get("LONGITUDE"))
        if latitude is None or longitude is None:
            flags.append("missing_coordinates")
        project_url = _https_url_or_blank(raw.get("PROJECT_WEBSITE"), flags)
        public_signal = (
            "reported_public_funding"
            if _text(raw.get("PUBLIC_FUNDING_IND")).upper() == "TRUE"
            else "public_funding_not_reported"
        )
        if public_signal == "public_funding_not_reported":
            flags.append("public_funding_not_reported")
        category = _text(raw.get("PROJECT_CATEGORY_NAME"))
        project_type = _text(raw.get("PROJECT_TYPE"))
        subtype = _text(raw.get("CONSTRUCTION_SUBTYPE"))
        name = _text(raw.get("PROJECT_NAME"))
        description = _text(raw.get("PROJECT_DESCRIPTION"))
        asset_class = classify_asset_class(
            BC_SOURCE_ID,
            category,
            project_type,
            subtype,
            name,
            description,
            clean_energy=_text(raw.get("CLEAN_ENERGY_IND")).upper() == "TRUE",
        )
        if asset_class == "unclassified":
            flags.append("asset_class_unclassified")
        record = PublicProjectRecord(
            project_id=f"BCMPI_{_text(raw.get('PROJECT_ID'))}",
            source_record_id=_text(raw.get("PROJECT_ID")),
            name=name,
            description=description,
            geography_id=BC_GEOGRAPHY[0],
            province=BC_GEOGRAPHY[1],
            municipality=_text(raw.get("MUNICIPALITY")),
            region=_text(raw.get("REGION")),
            asset_class=asset_class,
            asset_class_evidence_status="inferred",
            source_category=category,
            source_type=project_type,
            source_subtype=subtype,
            stage=_canonical_stage(_text(raw.get("PROJECT_STATUS"))),
            stage_source_text=" | ".join(
                value
                for value in (
                    _text(raw.get("PROJECT_STATUS")),
                    _text(raw.get("PROJECT_STAGE")),
                )
                if value
            ),
            start_period=start_period,
            completion_period=completion_period,
            start_year=start_year,
            end_year=end_year,
            estimated_cost_cad=cost,
            cost_status=(
                "reported_estimate_converted_from_millions_cad"
                if cost is not None
                else "not_reported"
            ),
            public_funding_signal=public_signal,
            public_funding_evidence_status="observed",
            lead_organization=_text(raw.get("DEVELOPER")),
            supporting_ministry="",
            latitude=latitude,
            longitude=longitude,
            project_url=project_url,
            source_id=BC_SOURCE_ID,
            source_scope="major_projects_feature_layer_historical_discontinued",
            source_evidence_status=EvidenceStatus.OBSERVED,
            as_of_date=as_of_date,
            quality_flags=tuple(sorted(set(flags))),
        )
        record.validate()
        records.append(record)
    return records, _source_diagnostic(
        BC_SOURCE_ID,
        BC_GEOGRAPHY[0],
        len(features),
        records,
        source_scope="Historical official major-project feature layer; current inventory discontinued after Q3 2025. Feature attributes report a common 2024-12-01 update date.",
    )


def normalize_ontario_projects(
    csv_path: Path, as_of_date: str
) -> tuple[list[PublicProjectRecord], dict[str, Any]]:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        _validate_fields(set(reader.fieldnames or []), ONTARIO_REQUIRED_FIELDS, ONTARIO_SOURCE_ID)
        source_rows = list(reader)
    if not source_rows:
        raise ValidationError("Ontario Builds dataset cannot be empty")

    records: list[PublicProjectRecord] = []
    seen_row_hashes: set[str] = set()
    collapsed_duplicates = 0
    for raw in source_rows:
        row_hash = _row_hash(raw)
        if row_hash in seen_row_hashes:
            collapsed_duplicates += 1
            continue
        seen_row_hashes.add(row_hash)
        flags = [
            "derived_record_id_no_publisher_identifier",
            "source_is_sample_not_complete_inventory",
        ]
        raw_cost = _optional_float(raw.get("Estimated Total Budget ($)"))
        if raw_cost is None:
            cost = None
            cost_status = "not_reported"
            flags.append("missing_estimated_cost")
        elif raw_cost == 0:
            cost = None
            cost_status = "zero_placeholder_treated_as_missing"
            flags.extend(("missing_estimated_cost", "zero_budget_treated_as_missing"))
        else:
            cost = raw_cost
            cost_status = "reported_total_budget"
        completion_period = _text(raw.get("Target Completion Date"))
        end_year = _ontario_completion_year(completion_period)
        _schedule_flags(flags, "", completion_period, None, end_year)
        latitude = _optional_float(raw.get("Latitude"))
        longitude = _optional_float(raw.get("Longitude"))
        if latitude is None or longitude is None:
            flags.append("missing_coordinates")
        project_url = _https_url_or_blank(raw.get("Website"), flags)
        reported_funding = any(
            _text(raw.get(field)).casefold() == "yes"
            for field in (
                "Municipal Funding",
                "Provincial Funding",
                "Federal Funding",
                "Other Funding",
            )
        )
        category = _text(raw.get("Category"))
        name = _text(raw.get("Project"))
        description = " ".join(
            value
            for value in (_text(raw.get("Description")), _text(raw.get("Result")))
            if value
        )
        source_type = _text(raw.get("Highway / Transit Line"))
        asset_class = classify_asset_class(
            ONTARIO_SOURCE_ID, category, source_type, "", name, description
        )
        if asset_class == "unclassified":
            flags.append("asset_class_unclassified")
        record = PublicProjectRecord(
            project_id=f"ONBUILD_{row_hash[:20].upper()}",
            source_record_id=f"DERIVED_ROW_{row_hash[:24].upper()}",
            name=name,
            description=description,
            geography_id=ONTARIO_GEOGRAPHY[0],
            province=ONTARIO_GEOGRAPHY[1],
            municipality=_text(raw.get("Community")),
            region=" | ".join(
                value
                for value in (_text(raw.get("Region")), _text(raw.get("Area")))
                if value
            ),
            asset_class=asset_class,
            asset_class_evidence_status="inferred",
            source_category=category,
            source_type=source_type,
            source_subtype="",
            stage=_canonical_stage(_text(raw.get("Status"))),
            stage_source_text=_text(raw.get("Status")),
            start_period="",
            completion_period=completion_period,
            start_year=None,
            end_year=end_year,
            estimated_cost_cad=cost,
            cost_status=cost_status,
            public_funding_signal=(
                "reported_public_funding"
                if reported_funding
                else "source_scope_public_project"
            ),
            public_funding_evidence_status="observed",
            lead_organization="",
            supporting_ministry=_text(raw.get("Supporting Ministry")),
            latitude=latitude,
            longitude=longitude,
            project_url=project_url,
            source_id=ONTARIO_SOURCE_ID,
            source_scope="sample_of_key_infrastructure_projects",
            source_evidence_status=EvidenceStatus.OBSERVED,
            as_of_date=as_of_date,
            quality_flags=tuple(sorted(set(flags))),
        )
        record.validate()
        records.append(record)
    diagnostic = _source_diagnostic(
        ONTARIO_SOURCE_ID,
        ONTARIO_GEOGRAPHY[0],
        len(source_rows),
        records,
        source_scope="Publisher-described sample of key infrastructure projects updated on an ongoing basis; not a complete Ontario capital plan.",
    )
    diagnostic["collapsed_exact_duplicate_row_count"] = collapsed_duplicates
    return records, diagnostic


def normalize_quebec_projects(
    csv_path: Path, as_of_date: str
) -> tuple[list[PublicProjectRecord], dict[str, Any]]:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        _validate_fields(set(reader.fieldnames or []), QUEBEC_REQUIRED_FIELDS, QUEBEC_SOURCE_ID)
        source_rows = list(reader)
    if not source_rows:
        raise ValidationError("Quebec infrastructure dashboard cannot be empty")

    records: list[PublicProjectRecord] = []
    for raw in source_rows:
        flags = ["source_threshold_20m"]
        cost = _million_cost(raw.get("cout_total"))
        if cost is None:
            flags.append("missing_estimated_cost")
        completion_period = _text(raw.get("date_fin_mise_en_service"))
        end_year = _first_four_digit_year(completion_period)
        _schedule_flags(flags, "", completion_period, None, end_year)
        category = _text(raw.get("secteur_activite"))
        source_type = _text(raw.get("nature_travaux"))
        name = _text(raw.get("nom_projet"))
        description = _text(raw.get("description"))
        asset_class = classify_asset_class(
            QUEBEC_SOURCE_ID, category, source_type, "", name, description
        )
        if asset_class == "unclassified":
            flags.append("asset_class_unclassified")
        record = PublicProjectRecord(
            project_id=f"QCPQI_{_text(raw.get('no_projet'))}",
            source_record_id=_text(raw.get("no_projet")),
            name=name,
            description=description,
            geography_id=QUEBEC_GEOGRAPHY[0],
            province=QUEBEC_GEOGRAPHY[1],
            municipality=_text(raw.get("localisation")),
            region=_text(raw.get("region")),
            asset_class=asset_class,
            asset_class_evidence_status="inferred",
            source_category=category,
            source_type=source_type,
            source_subtype=_text(raw.get("nom_infrastructure")),
            stage=_canonical_stage(_text(raw.get("etat_avancement"))),
            stage_source_text=_text(raw.get("etat_avancement")),
            start_period="",
            completion_period=completion_period,
            start_year=None,
            end_year=end_year,
            estimated_cost_cad=cost,
            cost_status=(
                "reported_total_cost_converted_from_millions_cad"
                if cost is not None
                else "not_reported"
            ),
            public_funding_signal="source_scope_public_project",
            public_funding_evidence_status="observed",
            lead_organization=" | ".join(
                value
                for value in (
                    _text(raw.get("organisme")),
                    _text(raw.get("gestionnaire")),
                )
                if value
            ),
            supporting_ministry=_text(raw.get("ministre")),
            latitude=None,
            longitude=None,
            project_url="",
            source_id=QUEBEC_SOURCE_ID,
            source_scope="pqi_projects_20m_and_over",
            source_evidence_status=EvidenceStatus.OBSERVED,
            as_of_date=as_of_date,
            quality_flags=tuple(sorted(set([*flags, "missing_coordinates"]))),
        )
        record.validate()
        records.append(record)
    return records, _source_diagnostic(
        QUEBEC_SOURCE_ID,
        QUEBEC_GEOGRAPHY[0],
        len(source_rows),
        records,
        source_scope="Plan québécois des infrastructures projects of at least $20 million; data before November 2020 used a $50 million threshold.",
    )


def classify_asset_class(
    source_id: str,
    category: str,
    source_type: str,
    subtype: str,
    name: str,
    description: str,
    *,
    clean_energy: bool = False,
) -> str:
    text = _fold(" ".join((category, source_type, subtype, name, description)))
    category_text = _fold(category)
    type_text = _fold(" ".join((source_type, subtype)))

    if any(token in text for token in ("social housing", "affordable housing", "logements sociaux", "logement communautaire")):
        return "social_and_affordable_housing"
    if any(token in category_text for token in ("health", "sante")) or "health care" in type_text:
        return "health_facilities"
    if any(token in category_text for token in ("education", "enseignement superieur")) or "educational services" in type_text:
        return "schools_and_postsecondary"
    if clean_energy:
        return "power_sector_infrastructure"
    if any(
        token in text
        for token in (
            "wastewater",
            "sewage",
            "watermain",
            "drinking water",
            "stormwater",
            "flood mitigation",
            "traitement des eaux",
            "eaux usees",
            "aqueduc",
        )
    ):
        return "municipal_water_and_resilience"
    if any(
        token in text
        for token in (
            "transmission line",
            "substation",
            "electric utility",
            "hydroelectric",
            "solar farm",
            "wind farm",
            "battery energy",
        )
    ):
        return "power_sector_infrastructure"
    if any(
        token in category_text
        for token in (
            "roads and bridges",
            "transit",
            "reseau routier",
            "transport collectif",
            "transports maritime",
        )
    ) or any(
        token in type_text
        for token in (
            "roads & highways",
            "airport operations",
            "port and harbour",
            "transportation",
        )
    ):
        return "roads_transit_and_airports"
    if source_id == ONTARIO_SOURCE_ID and category_text in {
        "communities",
        "child care",
        "recreation",
    }:
        return "government_and_civic_facilities"
    if any(
        token in category_text
        for token in (
            "administration gouvernementale",
            "developpement du sport",
            "tourisme et activites recreatives",
            "culture",
            "recherche",
        )
    ) or any(token in type_text for token in ("public administration", "recreation")):
        return "government_and_civic_facilities"
    if category_text in {
        "municipalites",
        "environnement",
        "developpement du territoire nordique et des communautes autochtones",
        "agriculture, forets et faune",
    }:
        return "other_public_infrastructure"
    if category_text == "utilities (incl sewage treatment)":
        return "other_public_infrastructure"
    return "unclassified"


def _source_diagnostic(
    source_id: str,
    geography_id: str,
    raw_count: int,
    records: list[PublicProjectRecord],
    *,
    source_scope: str,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "geography_id": geography_id,
        "source_scope": source_scope,
        "raw_record_count": raw_count,
        "normalized_record_count": len(records),
        "reported_cost_record_count": sum(
            item.estimated_cost_cad is not None for item in records
        ),
        "complete_schedule_record_count": sum(
            item.start_year is not None and item.end_year is not None for item in records
        ),
        "end_year_record_count": sum(item.end_year is not None for item in records),
        "coordinate_record_count": sum(
            item.latitude is not None and item.longitude is not None for item in records
        ),
        "asset_class_counts": dict(
            sorted(Counter(item.asset_class for item in records).items())
        ),
        "stage_counts": dict(sorted(Counter(item.stage for item in records).items())),
        "public_funding_signal_counts": dict(
            sorted(Counter(item.public_funding_signal for item in records).items())
        ),
    }


def _validate_fields(actual: set[str], required: set[str], source_id: str) -> None:
    missing = sorted(required - actual)
    if missing:
        raise ValidationError(f"{source_id} schema changed; missing {missing}")


def _canonical_stage(value: str) -> str:
    folded = _fold(value)
    if any(token in folded for token in ("complete", "completed", "en service")):
        return "complete_or_in_service"
    if any(token in folded for token in ("construction started", "under construction", "en realisation")):
        return "under_construction_or_delivery"
    if any(token in folded for token in ("planning", "proposed", "en planification", "a l'etude")):
        return "planning_or_proposed"
    if "on hold" in folded:
        return "on_hold"
    return "unclassified_stage"


def _schedule_flags(
    flags: list[str],
    start_period: str,
    completion_period: str,
    start_year: int | None,
    end_year: int | None,
) -> None:
    if not start_period:
        flags.append("missing_start_period")
    if not completion_period or _fold(completion_period) in {"to be determined", "tbd"}:
        flags.append("missing_completion_period")
    elif end_year is None:
        flags.append("completion_period_unparsed")
    if start_year is None or end_year is None:
        flags.append("incomplete_schedule")


def _ontario_completion_year(value: str) -> int | None:
    text = value.strip()
    if not text or _fold(text) in {"to be determined", "tbd"}:
        return None
    year = _first_four_digit_year(text)
    if year is not None:
        return year
    match = re.fullmatch(r"(?:(\d{2})-[A-Za-z]{3}|[A-Za-z]{3}-(\d{2}))", text)
    if not match:
        return None
    short_year = int(match.group(1) or match.group(2))
    return 2000 + short_year if short_year <= 69 else 1900 + short_year


def _first_four_digit_year(value: str) -> int | None:
    match = re.search(r"(?<!\d)((?:19|20|21)\d{2})(?!\d)", value)
    return int(match.group(1)) if match else None


def _million_cost(value: Any) -> float | None:
    number = _optional_float(value)
    if number is None or number <= 0:
        return None
    return round(number * 1_000_000, 2)


def _optional_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _https_url_or_blank(value: Any, flags: list[str]) -> str:
    text = _text(value)
    if not text:
        return ""
    if text.startswith("https://"):
        return text
    flags.append("non_https_project_url_omitted")
    return ""


def _row_hash(raw: dict[str, str]) -> str:
    normalized = [f"{key}={_fold(value)}" for key, value in sorted(raw.items())]
    return hashlib.sha256("\n".join(normalized).encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\ufeff", "").split())


def _fold(value: Any) -> str:
    text = _text(value).casefold()
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(character)
    )
