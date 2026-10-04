from __future__ import annotations

import csv
import hashlib
import io
import re
from contextlib import closing
from io import TextIOWrapper
import zipfile
from pathlib import Path

from ..constants import EvidenceStatus
from ..material_taxonomy import material_indicator_targets
from ..schemas import ObservationRecord, ValidationError


TRADE_NOC_TO_NODE = {
    "72200": "trade_electricians",
    "72201": "trade_electricians",
    "72202": "trade_power_line",
    "72203": "trade_power_line",
    "72402": "trade_hvac",
    "73100": "trade_concrete",
}

PROVINCE_DGUID_TO_GEOGRAPHY_ID = {
    "2021A000210": "PR_10",
    "2021A000211": "PR_11",
    "2021A000212": "PR_12",
    "2021A000213": "PR_13",
    "2021A000224": "PR_24",
    "2021A000235": "PR_35",
    "2021A000246": "PR_46",
    "2021A000247": "PR_47",
    "2021A000248": "PR_48",
    "2021A000259": "PR_59",
    "2021A000260": "PR_60",
    "2021A000261": "PR_61",
    "2021A000262": "PR_62",
}

JVWS_STATISTICS = {"Job vacancies", "Average offered hourly wage"}
JVWS_ALBERTA_TRANSFORMATION_ID = "TR_STATCAN_JVWS_AB_NOC_1_0_0"
JVWS_CANADA_TRANSFORMATION_ID = "TR_STATCAN_JVWS_CA_PROVINCES_NOC_1_0_0"
BCPI_PROVINCIAL_TRANSFORMATION_ID = "TR_STATCAN_BCPI_CA_PROVINCES_MATERIALS_1_0_0"
BCPI_REFERENCE_PROVINCIAL_TRANSFORMATION_ID = (
    "TR_STATCAN_BCPI_BC_ON_QC_REFERENCE_CLASSES_1_0_0"
)
BCPI_REFERENCE_CMA_TRANSFORMATION_ID = (
    "TR_STATCAN_BCPI_VAN_TOR_MTL_REFERENCE_CLASSES_1_0_0"
)
BCPI_PROVINCE_DGUID_TO_GEOGRAPHY_ID = {
    key: PROVINCE_DGUID_TO_GEOGRAPHY_ID[key]
    for key in (
        "2021A000210",
        "2021A000212",
        "2021A000213",
        "2021A000224",
        "2021A000235",
        "2021A000246",
        "2021A000247",
        "2021A000248",
        "2021A000259",
    )
}
BCPI_REFERENCE_PROVINCE_DGUID_TO_GEOGRAPHY_ID = {
    "2021A000224": "PR_24",
    "2021A000235": "PR_35",
    "2021A000259": "PR_59",
}
BCPI_REFERENCE_CMA_DGUID_TO_GEOGRAPHY_ID = {
    "2021S0503462": "CMA_462",
    "2021S0503535": "CMA_535",
    "2021S0503933": "CMA_933",
}
BCPI_REFERENCE_INDICATOR_IDS = {
    "BCPI_INSTITUTIONAL_BUILDINGS_62213_DIVISION_COMPOSITE",
    "BCPI_SCHOOL_DIVISION_COMPOSITE",
    "BCPI_OFFICE_BUILDING_62212_DIVISION_COMPOSITE",
    (
        "BCPI_BUS_DEPOT_WITH_MAINTENANCE_AND_REPAIR_FACILITIES_"
        "DIVISION_COMPOSITE"
    ),
}


def normalize_bcpi_alberta(zip_path: Path, output_path: Path) -> list[ObservationRecord]:
    """Normalize Alberta BCPI rows without erasing building/division detail."""
    with zipfile.ZipFile(zip_path) as archive:
        csv_names = [name for name in archive.namelist() if name.endswith(".csv") and "MetaData" not in name]
        if len(csv_names) != 1:
            raise ValidationError(f"expected one BCPI data CSV, found {csv_names}")
        csv_bytes = archive.read(csv_names[0])

    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")))
    rows = list(reader)
    required = {
        "REF_DATE",
        "GEO",
        "Type of building",
        "Division",
        "UOM",
        "VALUE",
    }
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValidationError(f"BCPI schema changed; missing {sorted(required - set(reader.fieldnames or []))}")

    observations: list[ObservationRecord] = []
    for raw in rows:
        geography = raw["GEO"].strip()
        if geography not in {"Calgary, Alberta", "Edmonton, Alberta"}:
            continue
        if not raw["VALUE"].strip():
            continue
        period_start, period_end = quarter_bounds(raw["REF_DATE"])
        building = raw["Type of building"].strip()
        division = raw["Division"].strip()
        identity = "|".join((raw["REF_DATE"], geography, building, division, raw["UOM"]))
        observation = ObservationRecord(
            observation_id=f"OBS_BCPI_{hashlib.sha256(identity.encode()).hexdigest()[:20].upper()}",
            indicator_id=f"BCPI_{slug(building)}_{slug(division)}",
            value=float(raw["VALUE"]),
            unit=raw["UOM"].strip(),
            geography_id="CMA_825" if geography.startswith("Calgary") else "CMA_835",
            period_start=period_start,
            period_end=period_end,
            source_id="STATCAN_BCPI_18100289",
            evidence_status=EvidenceStatus.OBSERVED,
            as_of_date=period_end,
            quality_flags=tuple(filter(None, (raw.get("STATUS", "").strip(), raw.get("SYMBOL", "").strip()))),
        )
        observation.validate()
        observations.append(observation)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "observation_id",
                "indicator_id",
                "value",
                "unit",
                "geography_id",
                "period_start",
                "period_end",
                "source_id",
                "evidence_status",
                "as_of_date",
                "transformation_id",
                "quality_flags",
            ),
        )
        writer.writeheader()
        for item in observations:
            writer.writerow(
                {
                    **item.__dict__,
                    "evidence_status": item.evidence_status.value,
                    "quality_flags": "|".join(item.quality_flags),
                }
            )
    return observations


def normalize_bcpi_provinces(
    zip_path: Path, output_path: Path
) -> list[ObservationRecord]:
    """Normalize selected BCPI material rows for published provinces.

    The Statistics Canada table currently includes province-level rows for nine
    provinces. Prince Edward Island and the territories are absent from this
    product and remain explicit coverage gaps rather than being imputed.
    """
    with zipfile.ZipFile(zip_path) as archive:
        csv_names = [
            name
            for name in archive.namelist()
            if name.endswith(".csv") and "MetaData" not in name
        ]
        if len(csv_names) != 1:
            raise ValidationError(f"expected one BCPI data CSV, found {csv_names}")
        with closing(archive.open(csv_names[0])) as binary_handle:
            with TextIOWrapper(
                binary_handle, encoding="utf-8-sig", newline=""
            ) as text_handle:
                reader = csv.DictReader(text_handle)
                required = {
                    "REF_DATE",
                    "GEO",
                    "DGUID",
                    "Type of building",
                    "Division",
                    "UOM",
                    "VALUE",
                    "STATUS",
                    "SYMBOL",
                }
                if not reader.fieldnames or not required.issubset(reader.fieldnames):
                    raise ValidationError(
                        f"BCPI schema changed; missing "
                        f"{sorted(required - set(reader.fieldnames or []))}"
                    )
                targets = material_indicator_targets()
                observations: list[tuple[ObservationRecord, dict[str, str]]] = []
                published_province_dguids: set[str] = set()
                for raw in reader:
                    statcan_dguid = raw["DGUID"].strip()
                    if statcan_dguid in PROVINCE_DGUID_TO_GEOGRAPHY_ID:
                        published_province_dguids.add(statcan_dguid)
                    if statcan_dguid not in BCPI_PROVINCE_DGUID_TO_GEOGRAPHY_ID:
                        continue
                    building = raw["Type of building"].strip()
                    division = raw["Division"].strip()
                    indicator_id = f"BCPI_{slug(building)}_{slug(division)}"
                    if indicator_id not in targets:
                        continue
                    period_start, period_end = quarter_bounds(raw["REF_DATE"].strip())
                    value_text = raw["VALUE"].strip()
                    quality_flags = tuple(
                        flag
                        for flag in (
                            f"status:{raw['STATUS'].strip()}"
                            if raw["STATUS"].strip()
                            else "",
                            f"symbol:{raw['SYMBOL'].strip()}"
                            if raw["SYMBOL"].strip()
                            else "",
                            "value_missing_or_suppressed" if not value_text else "",
                        )
                        if flag
                    )
                    identity = "|".join(
                        (
                            raw["REF_DATE"].strip(),
                            statcan_dguid,
                            building,
                            division,
                            raw["UOM"].strip(),
                        )
                    )
                    observation = ObservationRecord(
                        observation_id=(
                            f"OBS_BCPI_{hashlib.sha256(identity.encode()).hexdigest()[:20].upper()}"
                        ),
                        indicator_id=indicator_id,
                        value=float(value_text) if value_text else None,
                        unit=raw["UOM"].strip(),
                        geography_id=BCPI_PROVINCE_DGUID_TO_GEOGRAPHY_ID[
                            statcan_dguid
                        ],
                        period_start=period_start,
                        period_end=period_end,
                        source_id="STATCAN_BCPI_18100289",
                        evidence_status=EvidenceStatus.OBSERVED,
                        as_of_date=period_end,
                        transformation_id=BCPI_PROVINCIAL_TRANSFORMATION_ID,
                        quality_flags=quality_flags,
                    )
                    observation.validate()
                    observations.append(
                        (
                            observation,
                            {
                                "geography_label": raw["GEO"].replace("\xa0", " ").strip(),
                                "statcan_dguid": statcan_dguid,
                            },
                        )
                    )

    expected_published_dguids = set(BCPI_PROVINCE_DGUID_TO_GEOGRAPHY_ID)
    if published_province_dguids != expected_published_dguids:
        raise ValidationError(
            "BCPI source province coverage changed; expected DGUIDs "
            f"{sorted(expected_published_dguids)}, found "
            f"{sorted(published_province_dguids)}. Review coverage before publication."
        )
    actual_geographies = {item.geography_id for item, _ in observations}
    expected_geographies = set(BCPI_PROVINCE_DGUID_TO_GEOGRAPHY_ID.values())
    if actual_geographies != expected_geographies:
        raise ValidationError(
            "BCPI provincial material scope changed; expected "
            f"{sorted(expected_geographies)}, found {sorted(actual_geographies)}"
        )
    observations.sort(
        key=lambda item: (
            item[0].geography_id,
            item[0].indicator_id,
            item[0].period_end,
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "observation_id",
        "indicator_id",
        "geography_id",
        "geography_label",
        "statcan_dguid",
        "value",
        "unit",
        "period_start",
        "period_end",
        "source_id",
        "evidence_status",
        "as_of_date",
        "transformation_id",
        "quality_flags",
    )
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item, dimensions in observations:
            writer.writerow(
                {
                    **item.__dict__,
                    **dimensions,
                    "evidence_status": item.evidence_status.value,
                    "quality_flags": "|".join(item.quality_flags),
                }
            )
    return [item for item, _ in observations]


def normalize_bcpi_reference_provinces(
    zip_path: Path, output_path: Path
) -> list[ObservationRecord]:
    """Normalize public-building reference classes for BC, Ontario and Quebec.

    This is a province-preserving expansion input. It never substitutes an
    Alberta CMA series or a Canada aggregate for a provincial observation.
    """
    with zipfile.ZipFile(zip_path) as archive:
        csv_names = [
            name
            for name in archive.namelist()
            if name.endswith(".csv") and "MetaData" not in name
        ]
        if len(csv_names) != 1:
            raise ValidationError(f"expected one BCPI data CSV, found {csv_names}")
        with closing(archive.open(csv_names[0])) as binary_handle:
            with TextIOWrapper(
                binary_handle, encoding="utf-8-sig", newline=""
            ) as text_handle:
                reader = csv.DictReader(text_handle)
                required = {
                    "REF_DATE",
                    "GEO",
                    "DGUID",
                    "Type of building",
                    "Division",
                    "UOM",
                    "VALUE",
                    "STATUS",
                    "SYMBOL",
                }
                if not reader.fieldnames or not required.issubset(reader.fieldnames):
                    raise ValidationError(
                        "BCPI schema changed; missing "
                        f"{sorted(required - set(reader.fieldnames or []))}"
                    )
                observations: list[tuple[ObservationRecord, dict[str, str]]] = []
                series_keys: set[tuple[str, str]] = set()
                for raw in reader:
                    statcan_dguid = raw["DGUID"].strip()
                    if (
                        statcan_dguid
                        not in BCPI_REFERENCE_PROVINCE_DGUID_TO_GEOGRAPHY_ID
                    ):
                        continue
                    building = raw["Type of building"].strip()
                    division = raw["Division"].strip()
                    indicator_id = f"BCPI_{slug(building)}_{slug(division)}"
                    if indicator_id not in BCPI_REFERENCE_INDICATOR_IDS:
                        continue
                    period_start, period_end = quarter_bounds(raw["REF_DATE"].strip())
                    value_text = raw["VALUE"].strip()
                    quality_flags = tuple(
                        flag
                        for flag in (
                            f"status:{raw['STATUS'].strip()}"
                            if raw["STATUS"].strip()
                            else "",
                            f"symbol:{raw['SYMBOL'].strip()}"
                            if raw["SYMBOL"].strip()
                            else "",
                            "value_missing_or_suppressed" if not value_text else "",
                        )
                        if flag
                    )
                    geography_id = (
                        BCPI_REFERENCE_PROVINCE_DGUID_TO_GEOGRAPHY_ID[
                            statcan_dguid
                        ]
                    )
                    identity = "|".join(
                        (
                            raw["REF_DATE"].strip(),
                            statcan_dguid,
                            building,
                            division,
                            raw["UOM"].strip(),
                        )
                    )
                    observation = ObservationRecord(
                        observation_id=(
                            "OBS_BCPI_"
                            f"{hashlib.sha256(identity.encode()).hexdigest()[:20].upper()}"
                        ),
                        indicator_id=indicator_id,
                        value=float(value_text) if value_text else None,
                        unit=raw["UOM"].strip(),
                        geography_id=geography_id,
                        period_start=period_start,
                        period_end=period_end,
                        source_id="STATCAN_BCPI_18100289",
                        evidence_status=EvidenceStatus.OBSERVED,
                        as_of_date=period_end,
                        transformation_id=(
                            BCPI_REFERENCE_PROVINCIAL_TRANSFORMATION_ID
                        ),
                        quality_flags=quality_flags,
                    )
                    observation.validate()
                    observations.append(
                        (
                            observation,
                            {
                                "geography_label": raw["GEO"]
                                .replace("\xa0", " ")
                                .strip(),
                                "statcan_dguid": statcan_dguid,
                            },
                        )
                    )
                    series_keys.add((indicator_id, geography_id))

    expected_series_keys = {
        (indicator_id, geography_id)
        for indicator_id in BCPI_REFERENCE_INDICATOR_IDS
        for geography_id in (
            BCPI_REFERENCE_PROVINCE_DGUID_TO_GEOGRAPHY_ID.values()
        )
    }
    if series_keys != expected_series_keys:
        raise ValidationError(
            "BCPI provincial reference-class coverage changed; missing="
            f"{sorted(expected_series_keys - series_keys)}, unexpected="
            f"{sorted(series_keys - expected_series_keys)}"
        )
    observations.sort(
        key=lambda item: (
            item[0].geography_id,
            item[0].indicator_id,
            item[0].period_end,
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "observation_id",
        "indicator_id",
        "geography_id",
        "geography_label",
        "statcan_dguid",
        "value",
        "unit",
        "period_start",
        "period_end",
        "source_id",
        "evidence_status",
        "as_of_date",
        "transformation_id",
        "quality_flags",
    )
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item, dimensions in observations:
            writer.writerow(
                {
                    **item.__dict__,
                    **dimensions,
                    "evidence_status": item.evidence_status.value,
                    "quality_flags": "|".join(item.quality_flags),
                }
            )
    return [item for item, _ in observations]


def normalize_bcpi_reference_cmas(
    zip_path: Path, output_path: Path
) -> list[ObservationRecord]:
    """Normalize public-building reference classes for three long-history CMAs.

    Vancouver, Toronto and Montréal are selected because the current official
    table publishes the same building reference classes used by the Alberta
    pilot, with 1981-onward histories for health, school and office proxies.
    The output remains city-market evidence and never substitutes for a
    province-wide index.
    """
    with zipfile.ZipFile(zip_path) as archive:
        csv_names = [
            name
            for name in archive.namelist()
            if name.endswith(".csv") and "MetaData" not in name
        ]
        if len(csv_names) != 1:
            raise ValidationError(f"expected one BCPI data CSV, found {csv_names}")
        with closing(archive.open(csv_names[0])) as binary_handle:
            with TextIOWrapper(
                binary_handle, encoding="utf-8-sig", newline=""
            ) as text_handle:
                reader = csv.DictReader(text_handle)
                required = {
                    "REF_DATE",
                    "GEO",
                    "DGUID",
                    "Type of building",
                    "Division",
                    "UOM",
                    "VALUE",
                    "STATUS",
                    "SYMBOL",
                }
                if not reader.fieldnames or not required.issubset(reader.fieldnames):
                    raise ValidationError(
                        "BCPI schema changed; missing "
                        f"{sorted(required - set(reader.fieldnames or []))}"
                    )
                observations: list[tuple[ObservationRecord, dict[str, str]]] = []
                series_keys: set[tuple[str, str]] = set()
                for raw in reader:
                    statcan_dguid = raw["DGUID"].strip()
                    if statcan_dguid not in BCPI_REFERENCE_CMA_DGUID_TO_GEOGRAPHY_ID:
                        continue
                    building = raw["Type of building"].strip()
                    division = raw["Division"].strip()
                    indicator_id = f"BCPI_{slug(building)}_{slug(division)}"
                    if indicator_id not in BCPI_REFERENCE_INDICATOR_IDS:
                        continue
                    value_text = raw["VALUE"].strip()
                    if not value_text:
                        raise ValidationError(
                            "BCPI CMA reference series contains a missing or suppressed value"
                        )
                    period_start, period_end = quarter_bounds(raw["REF_DATE"].strip())
                    geography_id = BCPI_REFERENCE_CMA_DGUID_TO_GEOGRAPHY_ID[
                        statcan_dguid
                    ]
                    quality_flags = tuple(
                        flag
                        for flag in (
                            f"status:{raw['STATUS'].strip()}"
                            if raw["STATUS"].strip()
                            else "",
                            f"symbol:{raw['SYMBOL'].strip()}"
                            if raw["SYMBOL"].strip()
                            else "",
                        )
                        if flag
                    )
                    identity = "|".join(
                        (
                            raw["REF_DATE"].strip(),
                            statcan_dguid,
                            building,
                            division,
                            raw["UOM"].strip(),
                        )
                    )
                    observation = ObservationRecord(
                        observation_id=(
                            "OBS_BCPI_"
                            f"{hashlib.sha256(identity.encode()).hexdigest()[:20].upper()}"
                        ),
                        indicator_id=indicator_id,
                        value=float(value_text),
                        unit=raw["UOM"].strip(),
                        geography_id=geography_id,
                        period_start=period_start,
                        period_end=period_end,
                        source_id="STATCAN_BCPI_18100289",
                        evidence_status=EvidenceStatus.OBSERVED,
                        as_of_date=period_end,
                        transformation_id=BCPI_REFERENCE_CMA_TRANSFORMATION_ID,
                        quality_flags=quality_flags,
                    )
                    observation.validate()
                    observations.append(
                        (
                            observation,
                            {
                                "geography_label": raw["GEO"]
                                .replace("\xa0", " ")
                                .strip(),
                                "statcan_dguid": statcan_dguid,
                            },
                        )
                    )
                    series_keys.add((indicator_id, geography_id))

    expected_series_keys = {
        (indicator_id, geography_id)
        for indicator_id in BCPI_REFERENCE_INDICATOR_IDS
        for geography_id in BCPI_REFERENCE_CMA_DGUID_TO_GEOGRAPHY_ID.values()
    }
    if series_keys != expected_series_keys:
        raise ValidationError(
            "BCPI CMA reference-class coverage changed; missing="
            f"{sorted(expected_series_keys - series_keys)}, unexpected="
            f"{sorted(series_keys - expected_series_keys)}"
        )
    observations.sort(
        key=lambda item: (
            item[0].geography_id,
            item[0].indicator_id,
            item[0].period_end,
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "observation_id",
        "indicator_id",
        "geography_id",
        "geography_label",
        "statcan_dguid",
        "value",
        "unit",
        "period_start",
        "period_end",
        "source_id",
        "evidence_status",
        "as_of_date",
        "transformation_id",
        "quality_flags",
    )
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item, dimensions in observations:
            writer.writerow(
                {
                    **item.__dict__,
                    **dimensions,
                    "evidence_status": item.evidence_status.value,
                    "quality_flags": "|".join(item.quality_flags),
                }
            )
    return [item for item, _ in observations]


def normalize_jvws_alberta(zip_path: Path, output_path: Path) -> list[ObservationRecord]:
    """Normalize Alberta vacancy and offered-wage rows for graph-relevant trades.

    Statistics Canada suppression and quality codes are retained. A suppressed
    value is published as missing with flags and is never converted to zero.
    """
    return _normalize_jvws_trade_scope(
        zip_path,
        output_path,
        {"2021A000248": "PR_48"},
        transformation_id=JVWS_ALBERTA_TRANSFORMATION_ID,
        include_geography_dimensions=False,
    )


def normalize_jvws_canada(zip_path: Path, output_path: Path) -> list[ObservationRecord]:
    """Normalize the same trade indicators for all provinces and territories.

    Province and territory estimates remain separate. Canada totals and economic
    regions are deliberately excluded so a national value cannot silently stand
    in for local labour-market conditions.
    """
    return _normalize_jvws_trade_scope(
        zip_path,
        output_path,
        PROVINCE_DGUID_TO_GEOGRAPHY_ID,
        transformation_id=JVWS_CANADA_TRANSFORMATION_ID,
        include_geography_dimensions=True,
    )


def _normalize_jvws_trade_scope(
    zip_path: Path,
    output_path: Path,
    geography_dguid_to_id: dict[str, str],
    *,
    transformation_id: str,
    include_geography_dimensions: bool,
) -> list[ObservationRecord]:
    observations: list[tuple[ObservationRecord, dict[str, str]]] = []
    with zipfile.ZipFile(zip_path) as archive:
        csv_names = [
            name for name in archive.namelist() if name.endswith(".csv") and "MetaData" not in name
        ]
        if len(csv_names) != 1:
            raise ValidationError(f"expected one JVWS data CSV, found {csv_names}")
        with closing(archive.open(csv_names[0])) as binary_handle:
            with TextIOWrapper(binary_handle, encoding="utf-8-sig", newline="") as text_handle:
                reader = csv.DictReader(text_handle)
                required = {
                    "REF_DATE",
                    "GEO",
                    "DGUID",
                    "National Occupational Classification",
                    "Statistics",
                    "UOM",
                    "VALUE",
                    "STATUS",
                    "SYMBOL",
                    "TERMINATED",
                }
                if not reader.fieldnames or not required.issubset(reader.fieldnames):
                    raise ValidationError(
                        f"JVWS schema changed; missing {sorted(required - set(reader.fieldnames or []))}"
                    )

                for raw in reader:
                    statcan_dguid = raw["DGUID"].strip()
                    if statcan_dguid not in geography_dguid_to_id:
                        continue
                    occupation = raw["National Occupational Classification"].strip()
                    match = re.search(r"\[(\d{5})\]\s*$", occupation)
                    if not match:
                        continue
                    noc_code = match.group(1)
                    if noc_code not in TRADE_NOC_TO_NODE:
                        continue
                    statistic = raw["Statistics"].strip()
                    if statistic not in JVWS_STATISTICS:
                        continue

                    period_start, period_end = quarter_bounds(raw["REF_DATE"].strip())
                    value_text = raw["VALUE"].strip()
                    quality_flags = tuple(
                        flag
                        for flag in (
                            f"status:{raw['STATUS'].strip()}" if raw["STATUS"].strip() else "",
                            f"symbol:{raw['SYMBOL'].strip()}" if raw["SYMBOL"].strip() else "",
                            f"terminated:{raw['TERMINATED'].strip()}"
                            if raw["TERMINATED"].strip()
                            else "",
                            "value_missing_or_suppressed" if not value_text else "",
                        )
                        if flag
                    )
                    identity = "|".join(
                        (
                            raw["REF_DATE"].strip(),
                            raw["DGUID"].strip(),
                            noc_code,
                            statistic,
                            raw["UOM"].strip(),
                        )
                    )
                    observation = ObservationRecord(
                        observation_id=(
                            f"OBS_JVWS_{hashlib.sha256(identity.encode()).hexdigest()[:20].upper()}"
                        ),
                        indicator_id=f"JVWS_{slug(statistic)}_NOC_{noc_code}",
                        value=float(value_text) if value_text else None,
                        unit=raw["UOM"].strip(),
                        geography_id=geography_dguid_to_id[statcan_dguid],
                        period_start=period_start,
                        period_end=period_end,
                        source_id="STATCAN_JVWS_14100444",
                        evidence_status=EvidenceStatus.OBSERVED,
                        as_of_date=period_end,
                        transformation_id=transformation_id,
                        quality_flags=quality_flags,
                    )
                    observation.validate()
                    observations.append(
                        (
                            observation,
                            {
                                "noc_code": noc_code,
                                "occupation_label": occupation.rsplit(" [", 1)[0],
                                "trade_node_id": TRADE_NOC_TO_NODE[noc_code],
                                "statistic": statistic,
                                "geography_label": raw["GEO"].strip(),
                                "statcan_dguid": statcan_dguid,
                            },
                        )
                    )

    observations.sort(
        key=lambda item: (
            item[0].period_start,
            item[0].geography_id,
            item[1]["trade_node_id"],
            item[1]["noc_code"],
            item[1]["statistic"],
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "observation_id",
        "indicator_id",
    ]
    if include_geography_dimensions:
        fieldnames.extend(("geography_label", "statcan_dguid"))
    fieldnames.extend(
        (
            "noc_code",
            "occupation_label",
            "trade_node_id",
            "statistic",
            "value",
            "unit",
            "geography_id",
            "period_start",
            "period_end",
            "source_id",
            "evidence_status",
            "as_of_date",
            "transformation_id",
            "quality_flags",
        )
    )
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for observation, dimensions in observations:
            if not include_geography_dimensions:
                dimensions = {
                    key: value
                    for key, value in dimensions.items()
                    if key not in {"geography_label", "statcan_dguid"}
                }
            writer.writerow(
                {
                    **dimensions,
                    **observation.__dict__,
                    "value": "" if observation.value is None else observation.value,
                    "evidence_status": observation.evidence_status.value,
                    "quality_flags": "|".join(observation.quality_flags),
                }
            )
    return [observation for observation, _ in observations]


def quarter_bounds(reference_period: str) -> tuple[str, str]:
    quarter_match = re.fullmatch(r"(\d{4})-Q([1-4])", reference_period)
    month_match = re.fullmatch(r"(\d{4})-(01|04|07|10)", reference_period)
    if quarter_match:
        year, quarter = int(quarter_match.group(1)), int(quarter_match.group(2))
    elif month_match:
        year = int(month_match.group(1))
        quarter = {"01": 1, "04": 2, "07": 3, "10": 4}[month_match.group(2)]
    else:
        raise ValidationError(f"unsupported quarterly period: {reference_period!r}")
    starts = {1: "01-01", 2: "04-01", 3: "07-01", 4: "10-01"}
    ends = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
    return f"{year}-{starts[quarter]}", f"{year}-{ends[quarter]}"


def slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")
