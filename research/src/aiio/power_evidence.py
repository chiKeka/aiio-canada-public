from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .schemas import ValidationError


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _number(pattern: str, text: str, label: str) -> float:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValidationError(f"AESO evidence parser could not locate {label}")
    return float(match.group(1).replace(",", ""))


def run_power_evidence_screen(
    manual_extract_path: Path,
    source_pdf_path: Path,
    large_load_html_path: Path,
    interim_html_path: Path,
    output_json_path: Path,
    output_csv_path: Path,
) -> dict[str, Any]:
    manual = json.loads(manual_extract_path.read_text(encoding="utf-8"))
    actual_hash = sha256_file(source_pdf_path)
    if manual.get("source_content_hash") != actual_hash:
        raise ValidationError(
            "manual AESO chart extraction does not match the supplied source PDF hash"
        )
    if manual.get("review_status") != "independently_reviewed":
        raise ValidationError(
            "manual AESO chart extraction must pass independent source review before publication"
        )
    requested_series = manual.get("requested_load_series", [])
    if len(requested_series) != 6:
        raise ValidationError("AESO requested-load extraction must contain six chart bars")
    values = [float(item["requested_load_mw"]) for item in requested_series]
    if values != sorted(values):
        raise ValidationError("AESO cumulative requested-load series must be non-decreasing")

    large_load_html = large_load_html_path.read_text(
        encoding="utf-8", errors="replace"
    )
    interim_html = interim_html_path.read_text(encoding="utf-8", errors="replace")
    allocated_mw = _number(
        r"All\s+([0-9,]+)\s+MW\s+of the interim connection limit was successfully allocated",
        large_load_html,
        "allocated Phase 1 MW",
    )
    gldc_mw = _number(
        r"P2936\s+GLDC Load\s*-\s*<strong>([0-9,]+)\s+MW",
        large_load_html,
        "P2936 contracted MW",
    )
    keephills_mw = _number(
        r"P3083\s+Keephills Data Centre Phase I\s*-\s*<strong>([0-9,]+)\s+MW",
        large_load_html,
        "P3083 contracted MW",
    )
    interim_limit_mw = _number(
        r"interim limit of\s+([0-9,]+)\s+MW",
        interim_html,
        "interim limit MW",
    )
    no_reinforcement = bool(
        re.search(
            r"No new transmission system reinforcements or upgrades are required",
            interim_html,
            re.IGNORECASE,
        )
    )
    if not no_reinforcement:
        raise ValidationError("AESO Phase 1 transmission-scope statement was not found")
    if allocated_mw != interim_limit_mw or gldc_mw + keephills_mw != allocated_mw:
        raise ValidationError("AESO Phase 1 limit, allocation and contract MW do not reconcile")

    latest_requested = requested_series[-1]
    requested_load_mw = float(latest_requested["requested_load_mw"])
    metrics = [
        {
            "metric_id": "AESO_DC_REQUESTED_LOAD",
            "period": item["application_period"],
            "value": float(item["requested_load_mw"]),
            "unit": "MW",
            "evidence_status": "observed",
            "source_id": manual["source_id"],
            "source_locator": manual["source_locator"],
        }
        for item in requested_series
    ]
    metrics.extend(
        [
            {
                "metric_id": "AESO_PHASE1_INTERIM_LIMIT",
                "period": "2025-06-04",
                "value": interim_limit_mw,
                "unit": "MW",
                "evidence_status": "observed",
                "source_id": "AESO_INTERIM_LARGE_LOAD_2025_06",
                "source_locator": "Managing Demand Responsibly, interim limit",
            },
            {
                "metric_id": "AESO_PHASE1_ALLOCATED_LOAD_CONTRACTS",
                "period": "2026-08-31",
                "value": allocated_mw,
                "unit": "MW",
                "evidence_status": "observed",
                "source_id": "AESO_LARGE_LOAD_PROJECTS",
                "source_locator": "Phase 1: Large Load Integration | Complete",
            },
            {
                "metric_id": "AESO_P2936_EXECUTED_LOAD_CONTRACT",
                "period": "2026-08-31",
                "value": gldc_mw,
                "unit": "MW",
                "evidence_status": "observed",
                "source_id": "AESO_LARGE_LOAD_PROJECTS",
                "source_locator": "Phase 1 project list, P2936",
            },
            {
                "metric_id": "AESO_P3083_EXECUTED_LOAD_CONTRACT",
                "period": "2026-08-31",
                "value": keephills_mw,
                "unit": "MW",
                "evidence_status": "observed",
                "source_id": "AESO_LARGE_LOAD_PROJECTS",
                "source_locator": "Phase 1 project list, P3083",
            },
        ]
    )

    result = {
        "model_id": "AIIO_AB_POWER_EVIDENCE_SCREEN_0_1",
        "geography_id": "PR_48",
        "as_of_date": "2026-08-31",
        "evidence_status": "observed_with_scoped_interpretation",
        "manual_extraction_review": {
            "status": manual["review_status"],
            "reviewed_by": manual["reviewed_by"],
            "reviewer_type": manual["reviewer_type"],
            "reviewed_at": manual["reviewed_at"],
            "review_record": manual["review_record"],
        },
        "requested_load": {
            "latest_application_period": latest_requested["application_period"],
            "latest_requested_load_mw": requested_load_mw,
            "series": requested_series,
            "warning": "Connection requests are not contracts, forecasts or realized load and may include projects that do not proceed.",
        },
        "phase1": {
            "interim_limit_mw": interim_limit_mw,
            "allocated_mw": allocated_mw,
            "executed_load_contracts": [
                {"project_id": "P2936", "project_name": "GLDC Load", "mw": gldc_mw},
                {
                    "project_id": "P3083",
                    "project_name": "Keephills Data Centre Phase I",
                    "mw": keephills_mw,
                },
            ],
        },
        "transmission_boundary": {
            "phase1_new_transmission_reinforcement_required": False,
            "scope": "AESO 1,200 MW interim approach through 2028",
            "additional_transmission_required_for_50b_counterfactual_mw": None,
            "interpretation": "AESO stated that no new transmission reinforcements or upgrades were required for the scoped Phase 1 approach. This does not establish the need for larger, later or differently located loads. The $50B counterfactual requires project locations, connection studies and a system needs assessment before physical transmission additions can be stated.",
        },
        "metrics": metrics,
        "source_files": {
            "data_centre_update_pdf": actual_hash,
            "large_load_projects_html": sha256_file(large_load_html_path),
            "interim_approach_html": sha256_file(interim_html_path),
        },
        "limitations": [
            "Requested MW, executed load-contract MW, connected MW, coincident peak and transmission capacity are distinct quantities.",
            "The Q3 2025 request quantity and the later executed-contract record have different publication vintages and must not be treated as one queue-conversion snapshot.",
            "No province-wide scalar can convert the $50B CAD scenario into a transmission build requirement.",
            "The independent scenario power overlay remains separate and is not calibrated by this evidence screen.",
        ],
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metrics[0].keys()))
        writer.writeheader()
        writer.writerows(metrics)
    return result
