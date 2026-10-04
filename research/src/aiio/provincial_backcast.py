from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .calibration import build_reference_class_baseline
from .schemas import ValidationError


MODEL_ID = "AIIO_CA_BC_ON_QC_PROVINCE_LINKED_REFERENCE_BASELINE_0_1"
BACKCAST_ID = "AIIO_CA_BC_ON_QC_PROVINCE_LINKED_BACKCAST_0_1"
TRANSFORMATION_ID = "TR_AIIO_BCPI_PROVINCE_LINKED_CMA_BACKCAST_0_1"
SOURCE_ID = "STATCAN_BCPI_18100289"
MAX_OVERLAP_MAPE_PERCENT = 3.0

PROVINCE_TO_REFERENCE_CMA = {
    "PR_24": "CMA_462",
    "PR_35": "CMA_535",
    "PR_59": "CMA_933",
}
PROVINCE_LABELS = {
    "PR_24": "Quebec",
    "PR_35": "Ontario",
    "PR_59": "British Columbia",
}
BACKCASTABLE_INDICATORS = {
    "BCPI_INSTITUTIONAL_BUILDINGS_62213_DIVISION_COMPOSITE",
    "BCPI_OFFICE_BUILDING_62212_DIVISION_COMPOSITE",
    "BCPI_SCHOOL_DIVISION_COMPOSITE",
}
ALL_INDICATORS = BACKCASTABLE_INDICATORS | {
    "BCPI_BUS_DEPOT_WITH_MAINTENANCE_AND_REPAIR_FACILITIES_DIVISION_COMPOSITE"
}
OUTPUT_FIELDS = [
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
]

LIMITATIONS = [
    "BCPI measures contractor bid-price change for model buildings, not the realized cost of a particular project.",
    "Values before the first official provincial observation are inferred by scaling a named CMA index to the province's first official index level; they are not official provincial observations.",
    "Montréal, Toronto and Vancouver are transparent historical reference markets, not complete representations of Quebec, Ontario or British Columbia.",
    "The overlap diagnostic tests level tracking after a single anchor; it does not validate historical province-wide representativeness before 2017.",
    "Empirical error bands are historical forecast-error ranges, not confidence intervals or probability guarantees.",
    "The baseline contains no AI-attributable effect and remains withheld pending independent review of both the backcast and forecast method.",
]


def run_province_linked_reference_backcast(
    province_csv_path: Path,
    cma_csv_path: Path,
    output_csv_path: Path,
    output_json_path: Path,
    *,
    horizons_years: Iterable[int] = range(1, 6),
) -> dict[str, Any]:
    province_rows = _read_rows(province_csv_path)
    cma_rows = _read_rows(cma_csv_path)
    _validate_inputs(province_rows, cma_rows)

    output_rows, diagnostics = _build_rows(province_rows, cma_rows)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    result = build_reference_class_baseline(
        output_csv_path,
        horizons_years=horizons_years,
        geography_labels=PROVINCE_LABELS,
        model_id=MODEL_ID,
        limitations=LIMITATIONS,
    )
    code_manifest = _code_manifest()
    result.update(
        {
            "backcast_id": BACKCAST_ID,
            "evidence_status": (
                "mixed_observed_official_province_and_inferred_cma_linked_backcast"
            ),
            "code_manifest": code_manifest,
            "code_sha256": _combined_hash(code_manifest),
            "source_input_manifest": [
                {
                    "role": "official_provincial_bcpi_2017_onward",
                    "path": _portable_path(province_csv_path),
                    "sha256": _sha256(province_csv_path),
                },
                {
                    "role": "named_cma_historical_reference",
                    "path": _portable_path(cma_csv_path),
                    "sha256": _sha256(cma_csv_path),
                },
            ],
            "backcast_output_sha256": _sha256(output_csv_path),
            "backcast_method": {
                "method": "single_anchor_level_splice",
                "description": (
                    "For each province, reference class and pre-2017 quarter, the named "
                    "CMA index is multiplied by the ratio of the first official provincial "
                    "index to the CMA index in that same anchor quarter. Official provincial "
                    "observations are used without modification from the anchor onward."
                ),
                "province_to_reference_cma": PROVINCE_TO_REFERENCE_CMA,
                "maximum_overlap_mape_percent": MAX_OVERLAP_MAPE_PERCENT,
                "diagnostics": diagnostics,
            },
            "publication_authorization": {
                "status": "withheld_pending_independent_backcast_and_modelling_review",
                "public_projection_authorized": False,
                "province_linked_backcast_authorized_for_research_display": True,
                "project_cost_translation_authorized": False,
                "ai_attributable_effect_authorized": False,
                "reason": (
                    "The backcast is reproducible and passes its predeclared overlap screen, "
                    "but it is an inferred historical proxy and has not received the required "
                    "independent method verdict."
                ),
            },
        }
    )
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != OUTPUT_FIELDS:
            raise ValidationError(f"BCPI reference schema changed for {path}")
        rows = list(reader)
    if not rows:
        raise ValidationError(f"BCPI reference input is empty: {path}")
    return rows


def _validate_inputs(
    province_rows: list[dict[str, str]], cma_rows: list[dict[str, str]]
) -> None:
    for role, rows, expected_geographies in (
        ("province", province_rows, set(PROVINCE_TO_REFERENCE_CMA)),
        ("CMA", cma_rows, set(PROVINCE_TO_REFERENCE_CMA.values())),
    ):
        if {row["source_id"] for row in rows} != {SOURCE_ID}:
            raise ValidationError(f"{role} BCPI source lineage changed")
        if {row["geography_id"] for row in rows} != expected_geographies:
            raise ValidationError(f"{role} BCPI geography coverage changed")
        keys = {(row["geography_id"], row["indicator_id"]) for row in rows}
        expected_keys = {
            (geography_id, indicator_id)
            for geography_id in expected_geographies
            for indicator_id in ALL_INDICATORS
        }
        if keys != expected_keys:
            raise ValidationError(f"{role} BCPI reference-class coverage changed")
        for row in rows:
            try:
                value = float(row["value"])
            except (TypeError, ValueError) as error:
                raise ValidationError(f"{role} BCPI contains a non-numeric value") from error
            if not math.isfinite(value) or value <= 0:
                raise ValidationError(f"{role} BCPI contains a non-positive value")


def _build_rows(
    province_rows: list[dict[str, str]], cma_rows: list[dict[str, str]]
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    province_grouped = _group(province_rows)
    cma_grouped = _group(cma_rows)
    output_rows: list[dict[str, str]] = []
    diagnostics: list[dict[str, Any]] = []

    for province_id, cma_id in PROVINCE_TO_REFERENCE_CMA.items():
        for indicator_id in sorted(ALL_INDICATORS):
            official = province_grouped[(province_id, indicator_id)]
            cma = cma_grouped[(cma_id, indicator_id)]
            official_by_period = {row["period_end"]: row for row in official}
            cma_by_period = {row["period_end"]: row for row in cma}
            anchor_period = min(official_by_period)
            if anchor_period not in cma_by_period:
                raise ValidationError("CMA history is missing the official province anchor")
            anchor_official = float(official_by_period[anchor_period]["value"])
            anchor_cma = float(cma_by_period[anchor_period]["value"])
            scale_factor = anchor_official / anchor_cma

            overlap_errors = []
            for period, official_row in official_by_period.items():
                if period not in cma_by_period:
                    raise ValidationError("CMA history is incomplete across provincial overlap")
                linked_value = float(cma_by_period[period]["value"]) * scale_factor
                overlap_errors.append(
                    (linked_value / float(official_row["value"]) - 1) * 100
                )
            overlap_mape = sum(abs(value) for value in overlap_errors) / len(
                overlap_errors
            )
            diagnostic = {
                "province_id": province_id,
                "reference_cma_id": cma_id,
                "indicator_id": indicator_id,
                "anchor_period_end": anchor_period,
                "anchor_scale_factor": round(scale_factor, 9),
                "overlap_observation_count": len(overlap_errors),
                "overlap_mape_percent": round(overlap_mape, 6),
                "overlap_max_absolute_error_percent": round(
                    max(abs(value) for value in overlap_errors), 6
                ),
                "backcast_observation_count": 0,
                "status": (
                    "pass"
                    if overlap_mape <= MAX_OVERLAP_MAPE_PERCENT
                    else "fail"
                ),
            }
            if diagnostic["status"] != "pass":
                raise ValidationError(
                    f"province-linked overlap MAPE exceeds the locked threshold: {diagnostic}"
                )

            if indicator_id in BACKCASTABLE_INDICATORS:
                for period, cma_row in cma_by_period.items():
                    if period >= anchor_period:
                        continue
                    value = float(cma_row["value"]) * scale_factor
                    output_rows.append(
                        _backcast_row(
                            cma_row,
                            province_id=province_id,
                            value=value,
                            anchor_period=anchor_period,
                            cma_id=cma_id,
                        )
                    )
                    diagnostic["backcast_observation_count"] += 1

            output_rows.extend(dict(row) for row in official)
            diagnostics.append(diagnostic)

    output_rows.sort(
        key=lambda row: (row["geography_id"], row["indicator_id"], row["period_end"])
    )
    return output_rows, diagnostics


def _group(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["geography_id"], row["indicator_id"])].append(row)
    for values in grouped.values():
        values.sort(key=lambda row: row["period_end"])
    return grouped


def _backcast_row(
    cma_row: dict[str, str],
    *,
    province_id: str,
    value: float,
    anchor_period: str,
    cma_id: str,
) -> dict[str, str]:
    identity = "|".join(
        [province_id, cma_row["indicator_id"], cma_row["period_end"], BACKCAST_ID]
    )
    observation_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20].upper()
    return {
        "observation_id": f"OBS_BCPI_BACKCAST_{observation_hash}",
        "indicator_id": cma_row["indicator_id"],
        "geography_id": province_id,
        "geography_label": PROVINCE_LABELS[province_id],
        "statcan_dguid": cma_row["statcan_dguid"],
        "value": f"{value:.6f}".rstrip("0").rstrip("."),
        "unit": cma_row["unit"],
        "period_start": cma_row["period_start"],
        "period_end": cma_row["period_end"],
        "source_id": SOURCE_ID,
        "evidence_status": "inferred",
        "as_of_date": cma_row["as_of_date"],
        "transformation_id": TRANSFORMATION_ID,
        "quality_flags": (
            "province_linked_cma_backcast;not_official_provincial_observation;"
            f"reference_cma={cma_id};anchor_period={anchor_period}"
        ),
    }


def _code_manifest() -> dict[str, str]:
    calibration_path = Path(__file__).with_name("calibration.py")
    return {
        "calibration_sha256": _sha256(calibration_path),
        "province_backcast_sha256": _sha256(Path(__file__)),
    }


def _combined_hash(manifest: dict[str, str]) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _portable_path(path: Path) -> str:
    parts = path.parts
    if "data" in parts:
        return Path(*parts[parts.index("data") :]).as_posix()
    return path.name
