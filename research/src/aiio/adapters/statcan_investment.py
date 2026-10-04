from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..adapters.statcan import PROVINCE_DGUID_TO_GEOGRAPHY_ID
from ..schemas import ValidationError


SOURCE_ID = "STATCAN_IBC_34100293"
TRANSFORMATION_ID = "TR_STATCAN_IBC_QUARTERLY_CONTROLS_0_1"
SELECTED_STRUCTURES = {
    "Total non-residential",
    "Total industrial",
    "Total commercial",
    "Total institutional and governmental",
}
SELECTED_INVESTMENT_VALUES = {
    "Seasonally adjusted - current",
    "Seasonally adjusted - constant",
}
EXPECTED_MONTHS_PER_QUARTER = 3
MINIMUM_CMA_COUNT = 30


@dataclass(frozen=True)
class MonthlyInvestment:
    geography_id: str
    geography_label: str
    statcan_dguid: str
    period: str
    structure: str
    investment_value: str
    value: float | None
    status: str


def normalize_investment_controls(
    zip_path: Path,
    output_path: Path,
    report_path: Path | None = None,
    retrieval_manifest_path: Path | None = None,
) -> list[dict[str, str]]:
    monthly = read_selected_monthly_rows(zip_path)
    validate_monthly_scope(monthly)
    grouped: dict[
        tuple[str, str, str, str, str, str], list[MonthlyInvestment]
    ] = defaultdict(list)
    for item in monthly:
        quarter = month_to_quarter(item.period)
        grouped[
            (
                item.geography_id,
                item.geography_label,
                item.statcan_dguid,
                quarter,
                item.structure,
                item.investment_value,
            )
        ].append(item)

    output: list[dict[str, str]] = []
    for key, observations in sorted(grouped.items()):
        geography_id, geography_label, dguid, quarter, structure, investment_value = key
        months = sorted(item.period for item in observations)
        if len(observations) != EXPECTED_MONTHS_PER_QUARTER:
            raise ValidationError(
                f"incomplete investment quarter for {geography_id} {quarter} "
                f"{structure} {investment_value}: {months}"
            )
        expected_months = quarter_months(quarter)
        if months != expected_months:
            raise ValidationError(
                f"non-contiguous investment quarter for {geography_id} {quarter}: {months}"
            )
        statuses = sorted({item.status or "blank" for item in observations})
        missing = [item for item in observations if item.value is None]
        value = None if missing else sum(item.value or 0.0 for item in observations)
        quality_flags = [f"monthly_status:{status}" for status in statuses]
        if missing:
            quality_flags.append("quarterly_value_missing_due_to_monthly_missingness")
        period_start, period_end = quarter_boundaries(quarter)
        structure_slug = slug(structure)
        basis_slug = slug(investment_value)
        output.append(
            {
                "observation_id": stable_id(
                    geography_id, quarter, structure_slug, basis_slug
                ),
                "indicator_id": f"IBC_{structure_slug}_{basis_slug}",
                "geography_label": geography_label,
                "statcan_dguid": dguid,
                "type_of_structure": structure,
                "investment_basis": investment_value,
                "value": "" if value is None else format(value, ".2f"),
                "unit": "Dollars per quarter",
                "geography_id": geography_id,
                "period_start": period_start,
                "period_end": period_end,
                "source_id": SOURCE_ID,
                "source_evidence_status": "observed",
                "evidence_status": "inferred",
                "transformation_id": TRANSFORMATION_ID,
                "source_month_count": str(len(observations)),
                "quality_flags": "|".join(quality_flags),
            }
        )

    write_rows(output_path, output)
    if report_path is not None:
        report = build_report(
            zip_path,
            output_path,
            output,
            retrieval_manifest_path=retrieval_manifest_path,
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return output


def read_selected_monthly_rows(zip_path: Path) -> list[MonthlyInvestment]:
    with zipfile.ZipFile(zip_path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv") and "MetaData" not in name]
        if csv_names != ["34100293.csv"]:
            raise ValidationError(
                f"unexpected Statistics Canada investment archive members: {csv_names}"
            )
        with archive.open(csv_names[0]) as raw_handle:
            text_handle = io.TextIOWrapper(raw_handle, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text_handle)
            required = {
                "REF_DATE",
                "GEO",
                "DGUID",
                "Type of structure",
                "Type of work",
                "Investment Value",
                "UOM",
                "VALUE",
                "STATUS",
            }
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValidationError("Statistics Canada investment schema changed")
            rows: list[MonthlyInvestment] = []
            for row in reader:
                if row["Type of structure"] not in SELECTED_STRUCTURES:
                    continue
                if row["Type of work"] != "Types of work, total":
                    continue
                if row["Investment Value"] not in SELECTED_INVESTMENT_VALUES:
                    continue
                geography_id = geography_id_from_dguid(row["DGUID"])
                if geography_id is None:
                    continue
                if row["UOM"] != "Dollars":
                    raise ValidationError("investment control source unit changed")
                value_text = row["VALUE"].strip()
                rows.append(
                    MonthlyInvestment(
                        geography_id=geography_id,
                        geography_label=row["GEO"],
                        statcan_dguid=row["DGUID"],
                        period=row["REF_DATE"],
                        structure=row["Type of structure"],
                        investment_value=row["Investment Value"],
                        value=float(value_text) if value_text else None,
                        status=row["STATUS"].strip(),
                    )
                )
    if not rows:
        raise ValidationError("investment control selection is empty")
    return rows


def validate_monthly_scope(rows: list[MonthlyInvestment]) -> None:
    province_ids = set(PROVINCE_DGUID_TO_GEOGRAPHY_ID.values())
    observed_provinces = {
        item.geography_id for item in rows if item.geography_id.startswith("PR_")
    }
    if observed_provinces != province_ids:
        raise ValidationError(
            "investment control extract must include all 13 provinces and territories"
        )
    cma_ids = {
        item.geography_id
        for item in rows
        if item.geography_id.startswith("CMA_")
    }
    if len(cma_ids) < MINIMUM_CMA_COUNT:
        raise ValidationError(
            f"investment control extract has too few CMA geographies: {len(cma_ids)}"
        )
    combinations = {
        (item.geography_id, item.period, item.structure, item.investment_value)
        for item in rows
    }
    if len(combinations) != len(rows):
        raise ValidationError("investment control extract has duplicate monthly cells")


def geography_id_from_dguid(dguid: str) -> str | None:
    if dguid in PROVINCE_DGUID_TO_GEOGRAPHY_ID:
        return PROVINCE_DGUID_TO_GEOGRAPHY_ID[dguid]
    if "S0503" in dguid:
        return f"CMA_{dguid.rsplit('S0503', 1)[1].zfill(3)}"
    if "S0505" in dguid:
        return f"CMA_PART_{dguid.rsplit('S0505', 1)[1]}"
    return None


def month_to_quarter(period: str) -> str:
    try:
        year_text, month_text = period.split("-")
        month = int(month_text)
        year = int(year_text)
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"invalid monthly investment period: {period}") from exc
    if month not in range(1, 13):
        raise ValidationError(f"invalid monthly investment period: {period}")
    quarter = (month - 1) // 3 + 1
    return f"{year}-Q{quarter}"


def quarter_months(quarter: str) -> list[str]:
    year_text, quarter_text = quarter.split("-Q")
    start_month = (int(quarter_text) - 1) * 3 + 1
    return [f"{year_text}-{month:02d}" for month in range(start_month, start_month + 3)]


def quarter_boundaries(quarter: str) -> tuple[str, str]:
    year_text, quarter_text = quarter.split("-Q")
    year = int(year_text)
    quarter_number = int(quarter_text)
    start_month = (quarter_number - 1) * 3 + 1
    end_month = start_month + 2
    end_day = 31 if end_month in {3, 12} else 30
    return (
        date(year, start_month, 1).isoformat(),
        date(year, end_month, end_day).isoformat(),
    )


def slug(value: str) -> str:
    return "_".join(
        part for part in value.upper().replace("-", " ").split() if part
    )


def stable_id(*parts: str) -> str:
    token = "|".join(parts)
    return "IBC_" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:20].upper()


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_report(
    zip_path: Path,
    output_path: Path,
    rows: list[dict[str, str]],
    *,
    retrieval_manifest_path: Path | None,
) -> dict[str, object]:
    geographies = {row["geography_id"] for row in rows}
    quarters = {row["period_end"] for row in rows}
    structures = {row["type_of_structure"] for row in rows}
    bases = {row["investment_basis"] for row in rows}
    province_count = sum(item.startswith("PR_") for item in geographies)
    return {
        "schema_version": "0.1.0",
        "model_id": "AIIO_BUILDING_INVESTMENT_CONTROLS_CANADA_0_1",
        "source_id": SOURCE_ID,
        "transformation_id": TRANSFORMATION_ID,
        "as_of_date": max(row["period_end"] for row in rows),
        "evidence_status": "inferred_quarterly_aggregation_of_observed_monthly_values",
        "input_sha256": sha256_path(zip_path),
        "retrieval_manifest_sha256": sha256_path(retrieval_manifest_path)
        if retrieval_manifest_path and retrieval_manifest_path.exists()
        else None,
        "output_sha256": sha256_path(output_path),
        "observation_count": len(rows),
        "geography_count": len(geographies),
        "province_and_territory_count": province_count,
        "cma_or_cma_part_count": len(geographies) - province_count,
        "quarter_count": len(quarters),
        "structure_count": len(structures),
        "investment_basis_count": len(bases),
        "missing_quarterly_value_count": sum(not row["value"] for row in rows),
        "geography_ids": sorted(geographies),
        "structures": sorted(structures),
        "investment_bases": sorted(bases),
        "publication_boundary": {
            "status": "regional_control_only",
            "ai_treatment_authorized": False,
            "public_project_outcome_authorized": False,
            "ai_attributable_effect_authorized": False,
            "reason": (
                "Regional building investment is a construction-activity control. It is not "
                "AI-specific, excludes engineering construction, and does not report "
                "estimate-to-outturn public-project performance."
            ),
        },
    }


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"
