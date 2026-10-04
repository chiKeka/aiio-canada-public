from __future__ import annotations

import hashlib
import http.cookiejar
import csv
import io
import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from ..paths import repository_path
from ..retrieval import RetrievalRecord
from ..schemas import ValidationError


LANDING_URL = "https://www.majorprojects.alberta.ca/"
EXPORT_URL = "https://www.majorprojects.alberta.ca/BulkAction"
TOKEN_PATTERN = re.compile(
    r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', re.IGNORECASE
)
CORE_NAME_PATTERN = re.compile(
    r"\b(data[ -]?cent(?:re|er)s?|compute (?:facility|park)|high density compute)\b",
    re.IGNORECASE,
)
DETAIL_DATA_PATTERN = re.compile(r"\bdata[ -]?cent(?:re|er)s?\b", re.IGNORECASE)


def fetch_major_projects(raw_root: Path) -> RetrievalRecord:
    """Use the site's public full-dataset export while retaining retrieval provenance."""
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    landing_request = urllib.request.Request(
        LANDING_URL,
        headers={"User-Agent": "AIIO-Canada-Research/0.1 (+public research retrieval)"},
    )
    with opener.open(landing_request, timeout=90) as response:
        landing_html = response.read().decode("utf-8-sig")
    token = extract_verification_token(landing_html)

    form_data = urllib.parse.urlencode(
        {
            "__RequestVerificationToken": token,
            "action": "ExportAllPublicCsv",
            "selecteddate": "1999-01-01",
        }
    ).encode()
    export_request = urllib.request.Request(
        EXPORT_URL,
        data=form_data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LANDING_URL,
            "User-Agent": "AIIO-Canada-Research/0.1 (+public research retrieval)",
        },
    )
    with opener.open(export_request, timeout=180) as response:
        content = response.read()
        effective_url = response.geturl()
        content_type = response.headers.get_content_type()

    if b"," not in content[:1000] or b"<html" in content[:1000].lower():
        raise ValidationError("Alberta Major Projects export did not return a CSV payload")

    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    digest = hashlib.sha256(content).hexdigest()
    destination_dir = raw_root / "alberta_major_projects"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{retrieved_at[:10]}_{digest[:12]}.csv"
    if not destination.exists():
        destination.write_bytes(content)

    record = RetrievalRecord(
        retrieval_id=f"RET_ALBERTA_MAJOR_PROJECTS_{digest[:16]}",
        source_id="ALBERTA_MAJOR_PROJECTS",
        retrieved_at=retrieved_at,
        effective_url=effective_url,
        content_hash=f"sha256:{digest}",
        content_type=content_type,
        byte_length=len(content),
        archive_path=repository_path(destination),
        result="success",
    )
    destination.with_suffix(".csv.manifest.json").write_text(
        json.dumps(asdict(record), indent=2) + "\n", encoding="utf-8"
    )
    return record


def extract_verification_token(html: str) -> str:
    match = TOKEN_PATTERN.search(html)
    if not match:
        raise ValidationError("public export form verification token was not found")
    return match.group(1)


def normalize_major_projects(
    csv_path: Path, all_output_path: Path, ai_output_path: Path, as_of_date: str
) -> tuple[int, int]:
    content = csv_path.read_text(encoding="utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    required = {
        "Id",
        "Name",
        "Estimated Cost",
        "Municipality",
        "Schedule",
        "Sector",
        "Type",
        "Power Generation Capacity (MW)",
        "Stage",
        "Developer",
        "Project Website",
        "Location",
        "Detail",
    }
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValidationError(
            f"Alberta Major Projects schema changed; missing {sorted(required - set(reader.fieldnames or []))}"
        )

    normalized = [normalize_project_row(row, as_of_date) for row in reader]
    ai_projects = [row for row in normalized if row["ai_relevance"] != "none"]
    fields = tuple(normalized[0].keys()) if normalized else ()
    if not fields:
        raise ValidationError("Alberta Major Projects export contained no records")
    for path, rows in ((all_output_path, normalized), (ai_output_path, ai_projects)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return len(normalized), len(ai_projects)


def normalize_project_row(raw: dict[str, str], as_of_date: str) -> dict[str, object]:
    name = raw["Name"].strip()
    detail = raw["Detail"].strip()
    relevance, basis = classify_ai_relevance(name, raw["Sector"], detail)
    longitude, latitude, location_count = extract_coordinates(raw["Location"])
    start_year, end_year = schedule_years(raw["Schedule"])
    cost = raw["Estimated Cost"].strip()
    power = raw["Power Generation Capacity (MW)"].strip()
    detail_lower = detail.lower()
    location_precision = (
        "approximate"
        if any(phrase in detail_lower for phrase in ("not exact", "not precise", "placeholder", "unknown"))
        else "reported"
    )
    return {
        "project_id": f"ABMP_{raw['Id'].strip()}",
        "name": name,
        "estimated_cost_cad": float(cost) if cost else "",
        "municipality": raw["Municipality"].strip(),
        "schedule_text": raw["Schedule"].strip(),
        "start_year": start_year or "",
        "end_year": end_year or "",
        "sector": raw["Sector"].strip(),
        "project_type": raw["Type"].strip(),
        "power_generation_capacity_mw": float(power) if power else "",
        "stage": raw["Stage"].strip(),
        "substage": raw.get("SubStage", "").strip(),
        "developer": raw["Developer"].strip(),
        "project_website": raw["Project Website"].strip(),
        "longitude": longitude if longitude is not None else "",
        "latitude": latitude if latitude is not None else "",
        "location_count": location_count,
        "location_precision": location_precision,
        "ai_relevance": relevance,
        "ai_classification_basis": basis,
        "source_id": "ALBERTA_MAJOR_PROJECTS",
        "source_evidence_status": "observed",
        "classification_evidence_status": "inferred" if relevance != "none" else "not_applicable",
        "as_of_date": as_of_date,
    }


def classify_ai_relevance(name: str, sector: str, detail: str) -> tuple[str, str]:
    if CORE_NAME_PATTERN.search(name):
        return "core_data_centre", "project name matches controlled data-centre/compute vocabulary"
    if sector.strip().lower() == "power" and DETAIL_DATA_PATTERN.search(detail):
        return "enabling_power", "power-sector project description explicitly references data-centre demand or use"
    return "none", "no controlled-vocabulary match"


def schedule_years(schedule: str) -> tuple[int | None, int | None]:
    years = [int(value) for value in re.findall(r"\b(?:19|20)\d{2}\b", schedule)]
    if not years:
        return None, None
    lower = schedule.lower()
    if len(years) >= 2:
        return years[0], years[-1]
    if "completion" in lower:
        return None, years[0]
    if "commencing" in lower or "starting" in lower:
        return years[0], None
    return years[0], years[0]


def extract_coordinates(location_json: str) -> tuple[float | None, float | None, int]:
    if not location_json.strip():
        return None, None, 0
    try:
        location = json.loads(location_json)
    except json.JSONDecodeError as exc:
        raise ValidationError("invalid project Location GeoJSON") from exc
    geometry = location.get("geometry", {})
    coordinates: list[list[float]] = []
    if geometry.get("type") == "Point":
        coordinates = [geometry.get("coordinates", [])]
    elif geometry.get("type") == "GeometryCollection":
        coordinates = [
            item.get("coordinates", [])
            for item in geometry.get("geometries", [])
            if item.get("type") == "Point"
        ]
    valid = [item for item in coordinates if len(item) >= 2]
    if not valid:
        return None, None, 0
    return float(valid[0][0]), float(valid[0][1]), len(valid)
