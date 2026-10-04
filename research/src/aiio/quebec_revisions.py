from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import statistics
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from .paths import repository_path
from .adapters.provincial_projects import QUEBEC_SOURCE_ID, classify_asset_class
from .schemas import ValidationError


DICTIONARY_SOURCE_ID = "QUEBEC_PQI_DATA_DICTIONARY"
MODEL_ID = "AIIO_QUEBEC_AUTHORIZED_PROJECT_REVISIONS_0_1"
GEOGRAPHY_ID = "PR_24"
REQUIRED_FIELDS = {
    "no_projet",
    "nom_projet",
    "description",
    "cout_total",
    "date_fin_mise_en_service",
    "etat_avancement",
    "suivi_modifications",
    "secteur_activite",
    "region",
    "localisation",
    "nature_travaux",
}
FRENCH_MONTHS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}
MONTH_PATTERN = "|".join(FRENCH_MONTHS)
EVENT_HEADING_RE = re.compile(
    rf"(?im)^\s*({MONTH_PATTERN})\s+(\d{{4}})\s*$"
)
MONEY_TOKEN = r"[0-9][0-9 \u00a0\u202f]*(?:,[0-9]+)?"
COST_PAIR_RE = re.compile(
    rf"(?:initialement\s+)?prévu(?:e)?\s+à\s+({MONEY_TOKEN})\s*m\s*\$\s*,?\s*"
    rf"le\s+coût\s+est\s+maintenant\s+de\s+({MONEY_TOKEN})\s*m\s*\$",
    re.IGNORECASE,
)
COST_CHANGE_RE = re.compile(
    rf"une\s+(hausse|baisse)\s+de\s+({MONEY_TOKEN})\s*m\s*\$\s+au\s+coût",
    re.IGNORECASE,
)
MONTH_YEAR_TOKEN = rf"(?:{MONTH_PATTERN})\s+\d{{4}}"
SCHEDULE_PAIR_RESCHEDULED_RE = re.compile(
    rf"(?:initialement\s+)?prévue?\s+en\s+({MONTH_YEAR_TOKEN})\s*,?\s*"
    rf"elle\s+est\s+(reportée|devancée)\s+(?:en|à)\s+({MONTH_YEAR_TOKEN})",
    re.IGNORECASE,
)
SCHEDULE_PAIR_PASSING_RE = re.compile(
    rf"passant\s+d(?:e|u|\s)\s*({MONTH_YEAR_TOKEN})\s+à\s+({MONTH_YEAR_TOKEN})",
    re.IGNORECASE,
)
SCHEDULE_PAIR_COMPLETE_SERVICE_RE = re.compile(
    rf"mise\s+en\s+service\s+complète\s+(?:a\s+été\s+)?"
    rf"(reportée|devancée)\s+de\s+({MONTH_YEAR_TOKEN})\s+à\s+({MONTH_YEAR_TOKEN})",
    re.IGNORECASE,
)
COMPLETION_FISCAL_YEAR_RE = re.compile(
    r"mise\s+en\s+service\s+complète\s+de\s+l\s+infrastructure\s+a\s+été\s+"
    r"réalisée\s+au\s+cours\s+de\s+l\s+année\s+financière\s+(\d{4})-(\d{4})",
    re.IGNORECASE,
)
AMBIGUOUS_SCHEDULE_MARKERS = (
    "dates de la mise en service partielle et complète",
    "dates de mise en service partielle et complète",
    "dates de début et de fin de la mise en service",
)
DICTIONARY_ANCHORS = (
    "Numéro unique conservé durant l’ensemble du cycle de vie du projet.",
    "Coût total autorisé.",
    "Présentation des modifications autorisées au projet durant son cycle de vie et leur date d’entrée en vigueur.",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalized_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("’", " ").replace("'", " ")
    return " ".join(normalized.casefold().split())


def _extract_pdf_text(path: Path) -> str:
    executable = shutil.which("pdftotext")
    if executable is None:
        raise ValidationError(
            "pdftotext is required to verify the Quebec field-dictionary anchors"
        )
    result = subprocess.run(
        [executable, "-layout", str(path), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValidationError(
            "Quebec field-dictionary text extraction failed: "
            + result.stderr.strip()
        )
    return result.stdout


def _validate_retrieval_manifest(path: Path, source_id: str) -> dict[str, Any]:
    manifest_path = path.with_suffix(path.suffix + ".manifest.json")
    if not manifest_path.exists():
        raise ValidationError(f"retrieval manifest is missing for {path.name}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_id") != source_id:
        raise ValidationError(f"retrieval manifest source_id mismatch for {path.name}")
    actual_hash = sha256_file(path)
    if manifest.get("content_hash") != actual_hash:
        raise ValidationError(f"retrieval manifest hash mismatch for {path.name}")
    return manifest


def _parse_money_millions(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    normalized = (
        unicodedata.normalize("NFKC", value)
        .replace("\u00a0", "")
        .replace("\u202f", "")
        .replace(" ", "")
        .replace(",", ".")
    )
    try:
        return float(normalized) * 1_000_000
    except ValueError as exc:
        raise ValidationError(f"invalid Quebec project cost value: {value!r}") from exc


def _parse_month_year(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = _normalized_text(value)
    iso_match = re.fullmatch(r"(\d{4})-(\d{2})(?:-\d{2})?", normalized)
    if iso_match:
        month = int(iso_match.group(2))
        if not 1 <= month <= 12:
            raise ValidationError(f"invalid month in date value: {value!r}")
        return f"{iso_match.group(1)}-{month:02d}"
    match = re.fullmatch(rf"({MONTH_PATTERN})\s+(\d{{4}})", normalized)
    if match is None:
        return None
    return f"{match.group(2)}-{FRENCH_MONTHS[match.group(1)]:02d}"


def _month_difference(start: str, end: str) -> int:
    start_year, start_month = (int(part) for part in start.split("-"))
    end_year, end_month = (int(part) for part in end.split("-"))
    return (end_year - start_year) * 12 + end_month - start_month


def _split_history(value: str) -> list[dict[str, Any]]:
    normalized = unicodedata.normalize("NFKC", value).replace("\r\n", "\n")
    matches = list(EVENT_HEADING_RE.finditer(normalized))
    events: list[dict[str, Any]] = []
    for source_order, match in enumerate(matches):
        month_name = match.group(1).casefold()
        effective_month = f"{match.group(2)}-{FRENCH_MONTHS[month_name]:02d}"
        text_start = match.end()
        text_end = matches[source_order + 1].start() if source_order + 1 < len(matches) else len(normalized)
        event_text = normalized[text_start:text_end].strip()
        events.append(
            {
                "effective_month": effective_month,
                "source_order": source_order,
                "source_text_sha256": _sha256_text(event_text),
                "text": event_text,
            }
        )
    return events


def _extract_cost_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for event in events:
        normalized = _normalized_text(event["text"])
        change_match = COST_CHANGE_RE.search(normalized)
        for pair_index, match in enumerate(COST_PAIR_RE.finditer(normalized)):
            from_cost = _parse_money_millions(match.group(1))
            to_cost = _parse_money_millions(match.group(2))
            if from_cost is None or to_cost is None:
                raise ValidationError("parsed Quebec cost revision unexpectedly became null")
            direction = change_match.group(1).casefold() if change_match else "not_stated"
            stated_change = (
                _parse_money_millions(change_match.group(2)) if change_match else None
            )
            signed_stated_change = (
                stated_change
                if direction == "hausse"
                else -stated_change
                if direction == "baisse" and stated_change is not None
                else None
            )
            arithmetic_reconciles = signed_stated_change is None or math.isclose(
                to_cost - from_cost,
                signed_stated_change,
                abs_tol=110_000,
            )
            output.append(
                {
                    "effective_month": event["effective_month"],
                    "source_order": event["source_order"],
                    "pair_index": pair_index,
                    "from_value_cad": from_cost,
                    "to_value_cad": to_cost,
                    "stated_change_cad": signed_stated_change,
                    "direction_source_text": direction,
                    "arithmetic_reconciles": arithmetic_reconciles,
                    "source_text_sha256": event["source_text_sha256"],
                }
            )
    return sorted(
        output,
        key=lambda item: (
            item["effective_month"],
            -item["source_order"],
            item["pair_index"],
        ),
    )


def _extract_schedule_events(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    output: list[dict[str, Any]] = []
    ambiguous_count = 0
    for event in events:
        normalized = _normalized_text(event["text"])
        if any(marker in normalized for marker in AMBIGUOUS_SCHEDULE_MARKERS):
            ambiguous_count += 1
            continue
        pairs: list[tuple[str, str, str]] = []
        for match in SCHEDULE_PAIR_RESCHEDULED_RE.finditer(normalized):
            pairs.append((match.group(1), match.group(3), match.group(2).casefold()))
        for match in SCHEDULE_PAIR_PASSING_RE.finditer(normalized):
            pairs.append((match.group(1), match.group(2), "passant_de_a"))
        for match in SCHEDULE_PAIR_COMPLETE_SERVICE_RE.finditer(normalized):
            pairs.append((match.group(2), match.group(3), match.group(1).casefold()))
        for pair_index, (from_text, to_text, direction) in enumerate(pairs):
            from_month = _parse_month_year(from_text)
            to_month = _parse_month_year(to_text)
            if from_month is None or to_month is None:
                continue
            output.append(
                {
                    "effective_month": event["effective_month"],
                    "source_order": event["source_order"],
                    "pair_index": pair_index,
                    "from_completion_month": from_month,
                    "to_completion_month": to_month,
                    "change_months": _month_difference(from_month, to_month),
                    "direction_source_text": direction,
                    "source_text_sha256": event["source_text_sha256"],
                }
            )
    return (
        sorted(
            output,
            key=lambda item: (
                item["effective_month"],
                -item["source_order"],
                item["pair_index"],
            ),
        ),
        ambiguous_count,
    )


def _chain_reconciles(
    events: list[dict[str, Any]],
    current_value: float | str | None,
    from_key: str,
    to_key: str,
    *,
    numeric_tolerance: float | None = None,
) -> bool:
    if not events or current_value is None:
        return False
    for earlier, later in zip(events, events[1:]):
        earlier_to = earlier[to_key]
        later_from = later[from_key]
        if numeric_tolerance is None:
            if earlier_to != later_from:
                return False
        elif not math.isclose(
            float(earlier_to), float(later_from), abs_tol=numeric_tolerance
        ):
            return False
    last_value = events[-1][to_key]
    if numeric_tolerance is None:
        return last_value == current_value
    return math.isclose(float(last_value), float(current_value), abs_tol=numeric_tolerance)


def _stage_authorization_month(
    events: list[dict[str, Any]], stage: str
) -> str | None:
    needle = f"autorisé à l étape « {stage.casefold()} »"
    months = [
        event["effective_month"]
        for event in events
        if needle in _normalized_text(event["text"])
    ]
    return min(months) if months else None


def _completion_fiscal_year(events: list[dict[str, Any]]) -> str | None:
    periods: list[str] = []
    for event in events:
        match = COMPLETION_FISCAL_YEAR_RE.search(_normalized_text(event["text"]))
        if match:
            periods.append(f"FY{match.group(1)}-{match.group(2)}")
    return max(periods) if periods else None


def _event_id(
    project_id: str,
    event_type: str,
    effective_month: str,
    pair_index: int,
) -> str:
    payload = f"{project_id}|{event_type}|{effective_month}|{pair_index}"
    return "QCPQIREV_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20].upper()


def _percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = position - lower_index
    return ordered[lower_index] * (1 - weight) + ordered[upper_index] * weight


def _summary_stats(values: list[float]) -> dict[str, float | int | None]:
    clean_values = [float(value) for value in values if math.isfinite(float(value))]
    return {
        "count": len(clean_values),
        "minimum": min(clean_values) if clean_values else None,
        "p25": _percentile(clean_values, 0.25),
        "median": statistics.median(clean_values) if clean_values else None,
        "p75": _percentile(clean_values, 0.75),
        "p90": _percentile(clean_values, 0.90),
        "maximum": max(clean_values) if clean_values else None,
        "mean": statistics.fmean(clean_values) if clean_values else None,
    }


def run_quebec_authorized_revisions(
    dashboard_csv_path: Path,
    dictionary_pdf_path: Path,
    output_json_path: Path,
    summary_csv_path: Path,
    event_csv_path: Path,
    *,
    dictionary_text_override: str | None = None,
) -> dict[str, Any]:
    dashboard_manifest = _validate_retrieval_manifest(
        dashboard_csv_path, QUEBEC_SOURCE_ID
    )
    dictionary_manifest = _validate_retrieval_manifest(
        dictionary_pdf_path, DICTIONARY_SOURCE_ID
    )
    dictionary_text = (
        dictionary_text_override
        if dictionary_text_override is not None
        else _extract_pdf_text(dictionary_pdf_path)
    )
    normalized_dictionary = _normalized_text(dictionary_text)
    for anchor in DICTIONARY_ANCHORS:
        if _normalized_text(anchor) not in normalized_dictionary:
            raise ValidationError(
                "Quebec field-dictionary anchor is missing: " + anchor
            )

    with dashboard_csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual_fields = set(reader.fieldnames or [])
        missing_fields = REQUIRED_FIELDS - actual_fields
        if missing_fields:
            raise ValidationError(
                "Quebec revision source schema changed; missing "
                + str(sorted(missing_fields))
            )
        raw_rows = list(reader)
    if not raw_rows:
        raise ValidationError("Quebec revision source cannot be empty")
    source_record_ids = [row["no_projet"].strip() for row in raw_rows]
    if any(not value for value in source_record_ids):
        raise ValidationError("Quebec revision source contains a blank no_projet")
    if len(source_record_ids) != len(set(source_record_ids)):
        raise ValidationError("Quebec revision source contains duplicate no_projet values")

    summaries: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        project_id = f"QCPQI_{raw['no_projet'].strip()}"
        history = raw["suivi_modifications"] or ""
        events = _split_history(history)
        current_cost = _parse_money_millions(raw["cout_total"])
        current_completion = _parse_month_year(raw["date_fin_mise_en_service"])
        cost_events = _extract_cost_events(events)
        schedule_events, ambiguous_schedule_count = _extract_schedule_events(events)
        cost_chain = _chain_reconciles(
            cost_events,
            current_cost,
            "from_value_cad",
            "to_value_cad",
            numeric_tolerance=110_000,
        ) and all(item["arithmetic_reconciles"] for item in cost_events)
        schedule_chain = _chain_reconciles(
            schedule_events,
            current_completion,
            "from_completion_month",
            "to_completion_month",
        )
        category = raw["secteur_activite"].strip()
        source_type = raw["nature_travaux"].strip()
        project_name = raw["nom_projet"].strip()
        asset_class = classify_asset_class(
            QUEBEC_SOURCE_ID,
            category,
            source_type,
            "",
            project_name,
            raw["description"].strip(),
        )
        baseline_cost = cost_events[0]["from_value_cad"] if cost_chain else None
        latest_cost = current_cost if cost_chain else None
        cost_variance = (
            latest_cost - baseline_cost
            if baseline_cost is not None and latest_cost is not None
            else None
        )
        cost_variance_percent = (
            cost_variance / baseline_cost
            if cost_variance is not None and baseline_cost
            else None
        )
        baseline_completion = (
            schedule_events[0]["from_completion_month"] if schedule_chain else None
        )
        latest_completion = current_completion if schedule_chain else None
        schedule_change_months = (
            _month_difference(baseline_completion, latest_completion)
            if baseline_completion and latest_completion
            else None
        )
        quality_flags = [
            "authorized_revision_not_final_outturn",
            "price_basis_date_missing",
            "single_province_current_dashboard_survivor_snapshot",
        ]
        if current_cost is None:
            quality_flags.append("current_authorized_cost_missing")
        if cost_events and not cost_chain:
            quality_flags.append("cost_revision_chain_unreconciled")
        if current_completion is None:
            quality_flags.append("current_completion_month_missing")
        if schedule_events and not schedule_chain:
            quality_flags.append("schedule_revision_chain_unreconciled")
        if ambiguous_schedule_count:
            quality_flags.append("ambiguous_multi_date_revision_excluded")
        completion_fiscal_year = _completion_fiscal_year(events)
        if completion_fiscal_year:
            quality_flags.append("actual_completion_exact_date_missing")

        summary = {
            "project_id": project_id,
            "source_record_id": raw["no_projet"].strip(),
            "project_name": project_name,
            "geography_id": GEOGRAPHY_ID,
            "province": "Quebec",
            "region": raw["region"].strip(),
            "municipality": raw["localisation"].strip(),
            "asset_class": asset_class,
            "source_category": category,
            "source_type": source_type,
            "stage_source_text": raw["etat_avancement"].strip(),
            "planning_authorization_month": _stage_authorization_month(
                events, "en planification"
            ),
            "realization_authorization_month": _stage_authorization_month(
                events, "en réalisation"
            ),
            "actual_completion_fiscal_year": completion_fiscal_year,
            "cost_revision_event_count": len(cost_events),
            "cost_revision_chain_reconciles": cost_chain,
            "reported_current_authorized_cost_cad": current_cost,
            "baseline_authorized_cost_cad": baseline_cost,
            "current_authorized_cost_cad": latest_cost,
            "authorized_cost_variance_cad": cost_variance,
            "authorized_cost_variance_percent": cost_variance_percent,
            "schedule_revision_event_count": len(schedule_events),
            "schedule_revision_chain_reconciles": schedule_chain,
            "reported_current_completion_month": current_completion,
            "baseline_completion_month": baseline_completion,
            "current_completion_month": latest_completion,
            "authorized_schedule_change_months": schedule_change_months,
            "ambiguous_schedule_event_count": ambiguous_schedule_count,
            "stable_lifecycle_project_id": True,
            "dashboard_lifecycle_history_published": bool(history.strip()),
            "cost_outcome_panel_authorized": False,
            "schedule_outcome_panel_authorized": False,
            "source_id": QUEBEC_SOURCE_ID,
            "quality_flags": sorted(set(quality_flags)),
        }
        summaries.append(summary)

        for event in cost_events:
            event_rows.append(
                {
                    "revision_event_id": _event_id(
                        project_id,
                        "authorized_cost_revision",
                        event["effective_month"],
                        event["pair_index"],
                    ),
                    "project_id": project_id,
                    "project_name": project_name,
                    "geography_id": GEOGRAPHY_ID,
                    "asset_class": asset_class,
                    "event_type": "authorized_cost_revision",
                    "effective_month": event["effective_month"],
                    "from_value": event["from_value_cad"],
                    "to_value": event["to_value_cad"],
                    "change_value": event["to_value_cad"]
                    - event["from_value_cad"],
                    "unit": "CAD",
                    "direction_source_text": event["direction_source_text"],
                    "arithmetic_reconciles": event["arithmetic_reconciles"],
                    "source_text_sha256": event["source_text_sha256"],
                    "source_id": QUEBEC_SOURCE_ID,
                    "evidence_status": "observed_text_with_inferred_parse",
                }
            )
        for event in schedule_events:
            event_rows.append(
                {
                    "revision_event_id": _event_id(
                        project_id,
                        "authorized_completion_revision",
                        event["effective_month"],
                        event["pair_index"],
                    ),
                    "project_id": project_id,
                    "project_name": project_name,
                    "geography_id": GEOGRAPHY_ID,
                    "asset_class": asset_class,
                    "event_type": "authorized_completion_revision",
                    "effective_month": event["effective_month"],
                    "from_value": event["from_completion_month"],
                    "to_value": event["to_completion_month"],
                    "change_value": event["change_months"],
                    "unit": "calendar_months",
                    "direction_source_text": event["direction_source_text"],
                    "arithmetic_reconciles": True,
                    "source_text_sha256": event["source_text_sha256"],
                    "source_id": QUEBEC_SOURCE_ID,
                    "evidence_status": "observed_text_with_inferred_parse",
                }
            )

    summary_fields = list(summaries[0])
    event_fields = list(event_rows[0]) if event_rows else []
    summary_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary_fields)
        writer.writeheader()
        for row in summaries:
            writer.writerow(
                {
                    **row,
                    "quality_flags": "|".join(row["quality_flags"]),
                }
            )
    event_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with event_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=event_fields)
        writer.writeheader()
        writer.writerows(event_rows)

    eligible_cost = [row for row in summaries if row["cost_revision_chain_reconciles"]]
    eligible_schedule = [
        row for row in summaries if row["schedule_revision_chain_reconciles"]
    ]
    cost_variance_values = [
        row["authorized_cost_variance_percent"]
        for row in eligible_cost
        if row["authorized_cost_variance_percent"] is not None
    ]
    schedule_change_values = [
        row["authorized_schedule_change_months"]
        for row in eligible_schedule
        if row["authorized_schedule_change_months"] is not None
    ]
    report = {
        "schema_version": "1.0.0",
        "model_id": MODEL_ID,
        "source_as_of_date": "2026-08-20",
        "geography_scope": [GEOGRAPHY_ID],
        "evidence_status": "observed_authorized_change_text_with_inferred_parser",
        "source_contract": {
            "stable_project_id": "no_projet is publisher-defined as unique across the project lifecycle",
            "current_cost": "cout_total is publisher-defined as total authorized cost",
            "history": "suivi_modifications is publisher-defined as authorized changes during the project lifecycle and their effective dates",
            "dictionary_anchor_count": len(DICTIONARY_ANCHORS),
        },
        "coverage_summary": {
            "source_project_count": len(summaries),
            "stable_lifecycle_project_id_count": sum(
                row["stable_lifecycle_project_id"] for row in summaries
            ),
            "history_published_count": sum(
                row["dashboard_lifecycle_history_published"] for row in summaries
            ),
            "cost_revision_project_count": sum(
                row["cost_revision_event_count"] > 0 for row in summaries
            ),
            "cost_revision_chain_reconciled_project_count": len(eligible_cost),
            "schedule_revision_project_count": sum(
                row["schedule_revision_event_count"] > 0 for row in summaries
            ),
            "schedule_revision_chain_reconciled_project_count": len(
                eligible_schedule
            ),
            "joint_reconciled_revision_project_count": sum(
                row["cost_revision_chain_reconciles"]
                and row["schedule_revision_chain_reconciles"]
                for row in summaries
            ),
            "actual_completion_fiscal_year_count": sum(
                row["actual_completion_fiscal_year"] is not None for row in summaries
            ),
            "authorized_cost_revision_event_count": sum(
                row["event_type"] == "authorized_cost_revision"
                for row in event_rows
            ),
            "authorized_schedule_revision_event_count": sum(
                row["event_type"] == "authorized_completion_revision"
                for row in event_rows
            ),
        },
        "asset_class_coverage": [
            {
                "asset_class": asset_class,
                "project_count": count,
                "cost_reconciled_count": sum(
                    row["asset_class"] == asset_class
                    and row["cost_revision_chain_reconciles"]
                    for row in summaries
                ),
                "schedule_reconciled_count": sum(
                    row["asset_class"] == asset_class
                    and row["schedule_revision_chain_reconciles"]
                    for row in summaries
                ),
            }
            for asset_class, count in sorted(
                Counter(row["asset_class"] for row in summaries).items()
            )
        ],
        "descriptive_statistics": {
            "authorized_cost_variance_fraction": _summary_stats(
                cost_variance_values
            ),
            "authorized_schedule_change_months": _summary_stats(
                schedule_change_values
            ),
            "by_asset_class": [
                {
                    "asset_class": asset_class,
                    "authorized_cost_variance_fraction": _summary_stats(
                        [
                            row["authorized_cost_variance_percent"]
                            for row in eligible_cost
                            if row["asset_class"] == asset_class
                            and row["authorized_cost_variance_percent"] is not None
                        ]
                    ),
                    "authorized_schedule_change_months": _summary_stats(
                        [
                            row["authorized_schedule_change_months"]
                            for row in eligible_schedule
                            if row["asset_class"] == asset_class
                            and row["authorized_schedule_change_months"] is not None
                        ]
                    ),
                }
                for asset_class in sorted(
                    {row["asset_class"] for row in summaries}
                )
            ],
        },
        "publication_boundary": {
            "authorized_revision_reference_panel_authorized": False,
            "public_project_cost_outcome_authorized": False,
            "public_project_schedule_outcome_authorized": False,
            "ai_attributable_effect_authorized": False,
            "status": "research_candidate_pending_independent_parser_review",
            "reason": "The source supplies stable lifecycle IDs and authorized revision histories, but the current dashboard is a single-province survivor snapshot; costs are authorized parameters rather than final outturns, completion is usually planned or fiscal-year precision, estimate price-basis dates are absent, and independent parser review is pending.",
        },
        "limitations": [
            "The current dashboard omits projects already retired from prior vintages, so survivor and threshold selection remain unresolved.",
            "Authorized cost revisions are not final audited outturns and do not include estimate price-basis dates.",
            "Authorized completion revisions are month-precision plans; fiscal-year completion statements do not supply exact actual dates.",
            "Ambiguous events containing both partial and complete service dates are excluded from schedule-pair parsing.",
            "No AI treatment is present, so no AI-attributable effect is estimated.",
        ],
        "source_files": {
            QUEBEC_SOURCE_ID: {
                "path": dashboard_csv_path.name,
                "content_hash": dashboard_manifest["content_hash"],
                "retrieved_at": dashboard_manifest["retrieved_at"],
            },
            DICTIONARY_SOURCE_ID: {
                "path": dictionary_pdf_path.name,
                "content_hash": dictionary_manifest["content_hash"],
                "retrieved_at": dictionary_manifest["retrieved_at"],
            },
        },
        "outputs": {
            "summary_csv": repository_path(summary_csv_path),
            "summary_csv_sha256": sha256_file(summary_csv_path),
            "event_csv": repository_path(event_csv_path),
            "event_csv_sha256": sha256_file(event_csv_path),
        },
    }
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report
