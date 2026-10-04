from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from .statcan import PROVINCE_DGUID_TO_GEOGRAPHY_ID
from ..schemas import ValidationError


SOURCE_ID = "STATCAN_CAPEX_INDUSTRY_GEOGRAPHY_34100035"
MODEL_ID = "AIIO_INFORMATION_SECTOR_CONSTRUCTION_CAPEX_SCREEN_0_1"
TRANSFORMATION_ID = "TR_STATCAN_INFORMATION_SECTOR_CONSTRUCTION_CAPEX_0_1"
SOURCE_MEMBER = "34100035.csv"
SELECTED_EXPENDITURE = "Capital, construction"
SELECTED_NAICS_CODE = "51"
SELECTED_NAICS_LABEL = "Information and cultural industries [51]"
CANADA_DGUID = "2021A000011124"
EXPECTED_FIRST_YEAR = 2006
EXPECTED_LATEST_YEAR = 2026
EXPECTED_GEOGRAPHY_COUNT = 14
SOURCE_RELEASE_DATE = "2026-02-25"

QUALITY_LABELS = {
    "": "not_flagged",
    "A": "excellent",
    "B": "very_good",
    "C": "good",
    "D": "acceptable",
    "E": "use_with_caution",
    "F": "too_unreliable_to_publish",
    "x": "suppressed_confidentiality",
    "..": "not_available",
}


def sha256_path(path: Path, *, prefixed: bool = True) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}" if prefixed else digest


def geography_id_from_dguid(dguid: str) -> str | None:
    if dguid == CANADA_DGUID:
        return "CA"
    return PROVINCE_DGUID_TO_GEOGRAPHY_ID.get(dguid)


def release_measure_status(year: int) -> str:
    if year == EXPECTED_LATEST_YEAR:
        return "intentions"
    if year == EXPECTED_LATEST_YEAR - 1:
        return "preliminary_actual"
    return "actual_or_revised"


def _naics_code(label: str) -> str | None:
    match = re.search(r"\[([^\]]+)\]$", label)
    return match.group(1) if match else None


def _verify_manifest(zip_path: Path, manifest_path: Path | None) -> str | None:
    if manifest_path is None:
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read capex retrieval manifest: {exc}") from exc
    if manifest.get("source_id") != SOURCE_ID:
        raise ValidationError("capex retrieval manifest source ID mismatch")
    if manifest.get("content_hash") != sha256_path(zip_path):
        raise ValidationError("capex retrieval manifest hash mismatch")
    return sha256_path(manifest_path)


def normalize_information_sector_construction_capex(
    zip_path: Path,
    output_csv_path: Path,
    output_json_path: Path,
    *,
    retrieval_manifest_path: Path | None = None,
) -> dict[str, Any]:
    manifest_sha256 = _verify_manifest(zip_path, retrieval_manifest_path)
    with zipfile.ZipFile(zip_path) as archive:
        data_members = [
            name
            for name in archive.namelist()
            if name.endswith(".csv") and "MetaData" not in name
        ]
        if data_members != [SOURCE_MEMBER]:
            raise ValidationError(
                f"unexpected Statistics Canada capex archive members: {data_members}"
            )
        with archive.open(SOURCE_MEMBER) as raw_handle:
            text_handle = io.TextIOWrapper(
                raw_handle, encoding="utf-8-sig", newline=""
            )
            reader = csv.DictReader(text_handle)
            required = {
                "REF_DATE",
                "GEO",
                "DGUID",
                "Capital and repair expenditures",
                "North American Industry Classification System (NAICS)",
                "UOM",
                "SCALAR_FACTOR",
                "VALUE",
                "STATUS",
            }
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValidationError("Statistics Canada capex schema changed")
            source_rows = list(reader)

    naics_labels = {
        row["North American Industry Classification System (NAICS)"]
        for row in source_rows
    }
    if any(_naics_code(label) == "518210" for label in naics_labels):
        raise ValidationError(
            "source now contains NAICS 518210; review the preregistered broad-sector selection before normalization"
        )
    if SELECTED_NAICS_LABEL not in naics_labels:
        raise ValidationError("information and cultural industries NAICS 51 is missing")

    selected = [
        row
        for row in source_rows
        if row["Capital and repair expenditures"] == SELECTED_EXPENDITURE
        and row["North American Industry Classification System (NAICS)"]
        == SELECTED_NAICS_LABEL
        and geography_id_from_dguid(row["DGUID"]) is not None
    ]
    if not selected:
        raise ValidationError("information-sector construction capex selection is empty")
    keys = {(row["DGUID"], row["REF_DATE"]) for row in selected}
    if len(keys) != len(selected):
        raise ValidationError("information-sector construction capex has duplicate cells")
    years = sorted({int(row["REF_DATE"]) for row in selected})
    expected_years = list(range(EXPECTED_FIRST_YEAR, EXPECTED_LATEST_YEAR + 1))
    if years != expected_years:
        raise ValidationError(
            f"information-sector construction capex year coverage changed: {years}"
        )
    geography_ids = {
        geography_id_from_dguid(row["DGUID"]) for row in selected
    }
    expected_geographies = {"CA", *PROVINCE_DGUID_TO_GEOGRAPHY_ID.values()}
    if geography_ids != expected_geographies or len(geography_ids) != EXPECTED_GEOGRAPHY_COUNT:
        raise ValidationError("information-sector capex geography coverage changed")
    if len(selected) != len(expected_years) * EXPECTED_GEOGRAPHY_COUNT:
        raise ValidationError("information-sector capex cell coverage is incomplete")

    output_rows: list[dict[str, str]] = []
    for row in sorted(selected, key=lambda item: (item["DGUID"], item["REF_DATE"])):
        if row["UOM"] != "Dollars" or row["SCALAR_FACTOR"] != "millions":
            raise ValidationError("information-sector capex source unit changed")
        status = row["STATUS"].strip()
        if status not in QUALITY_LABELS:
            raise ValidationError(f"unknown capex quality symbol: {status!r}")
        value_text = row["VALUE"].strip()
        if value_text:
            value_millions = float(value_text)
            value_cad = value_millions * 1_000_000
        else:
            value_millions = None
            value_cad = None
        if value_text == "" and status not in {"x", "F", ".."}:
            raise ValidationError(
                "missing capex value does not carry a publisher missingness symbol"
            )
        geography_id = geography_id_from_dguid(row["DGUID"])
        assert geography_id is not None
        year = int(row["REF_DATE"])
        output_rows.append(
            {
                "observation_id": (
                    f"CAPEX51_{geography_id}_{year}_CAPITAL_CONSTRUCTION"
                ),
                "geography_id": geography_id,
                "geography_label": row["GEO"],
                "statcan_dguid": row["DGUID"],
                "reference_year": str(year),
                "release_measure_status": release_measure_status(year),
                "value_millions_cad": (
                    "" if value_millions is None else format(value_millions, ".1f")
                ),
                "value_cad": "" if value_cad is None else format(value_cad, ".0f"),
                "unit": "current Canadian dollars",
                "naics_code": SELECTED_NAICS_CODE,
                "naics_label": SELECTED_NAICS_LABEL,
                "expenditure_category": SELECTED_EXPENDITURE,
                "statcan_quality_symbol": status,
                "quality_flag": QUALITY_LABELS[status],
                "source_id": SOURCE_ID,
                "source_evidence_status": (
                    "observed" if value_text else "publisher_withheld_or_unavailable"
                ),
                "classification_evidence_status": "inferred",
                "treatment_role": "research_only_broad_sector_capex_proxy",
                "ai_construction_treatment_authorized": "false",
            }
        )

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(output_rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(output_rows)

    status_counts = Counter(row["release_measure_status"] for row in output_rows)
    quality_counts = Counter(row["quality_flag"] for row in output_rows)
    geography_summaries = []
    for geography_id in sorted(expected_geographies):
        rows = [row for row in output_rows if row["geography_id"] == geography_id]
        latest_actual = next(
            (
                row
                for row in reversed(rows)
                if row["release_measure_status"] == "actual_or_revised"
                and row["value_cad"]
            ),
            None,
        )
        geography_summaries.append(
            {
                "geography_id": geography_id,
                "geography_label": rows[0]["geography_label"],
                "published_value_count": sum(bool(row["value_cad"]) for row in rows),
                "withheld_or_unavailable_count": sum(
                    not row["value_cad"] for row in rows
                ),
                "latest_actual_or_revised_year": (
                    int(latest_actual["reference_year"]) if latest_actual else None
                ),
                "latest_actual_or_revised_value_cad": (
                    int(latest_actual["value_cad"]) if latest_actual else None
                ),
            }
        )

    report = {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "source_id": SOURCE_ID,
        "transformation_id": TRANSFORMATION_ID,
        "as_of_date": SOURCE_RELEASE_DATE,
        "source_release_date": SOURCE_RELEASE_DATE,
        "input_sha256": sha256_path(zip_path),
        "retrieval_manifest_sha256": manifest_sha256,
        "code_sha256": sha256_path(Path(__file__)),
        "output_sha256": sha256_path(output_csv_path),
        "observation_count": len(output_rows),
        "geography_count": len(expected_geographies),
        "reference_year_count": len(expected_years),
        "first_reference_year": min(expected_years),
        "latest_reference_year": max(expected_years),
        "release_measure_status_counts": dict(sorted(status_counts.items())),
        "quality_flag_counts": dict(sorted(quality_counts.items())),
        "geography_summaries": geography_summaries,
        "treatment_requirement_assessment": {
            "status": "proxy_only_not_authorizing",
            "construction_capital_separable": True,
            "actual_or_revised_data_available_through": 2024,
            "exact_naics_518210_present": False,
            "finest_available_relevant_naics_code": SELECTED_NAICS_CODE,
            "required_industry_specificity": "NAICS 518210 or project-level data-centre construction",
            "published_frequency": "annual",
            "required_frequency": "quarterly",
            "published_geography": "province_or_territory",
            "required_geography": "CMA_or_reconciled_electricity_planning_region",
            "realized_ai_construction_spend_cad_present": False,
            "data_centre_construction_labour_hours_present": False,
            "authorizing_treatment_present": False,
            "reason": (
                "The table separates construction capital and includes historical actual/revised values, but its finest relevant provincial industry is NAICS 51. That sector includes telecommunications, publishing, broadcasting and other information activities and cannot identify AI or data-centre construction. Annual province cells also do not satisfy the locked quarterly regional treatment contract."
            ),
        },
        "publication_boundary": {
            "descriptive_broad_sector_capex_authorized": True,
            "ai_construction_treatment_authorized": False,
            "ai_attributable_effect_authorized": False,
            "cost_escalation_percent": None,
            "schedule_delay_days": None,
            "permitted_use": "regional information-sector construction activity context or sensitivity control",
            "prohibited_use": "AI treatment onset, AI treatment dose, project-cost escalation or schedule-delay attribution",
        },
        "limitations": [
            "NAICS 51 is substantially broader than computing infrastructure providers and cannot isolate data-centre construction.",
            "The source is annual and provincial/territorial, not quarterly at CMA or electricity-planning-region resolution.",
            "2025 is preliminary actual and 2026 is intentions; only years through 2024 are actual or revised in this vintage.",
            "Suppressed cells remain missing and are never converted to zero.",
            "Capital construction expenditure is not construction labour hours and does not identify public-project outcomes.",
        ],
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
