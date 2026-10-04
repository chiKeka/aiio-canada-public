from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.request
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..constants import EvidenceStatus
from ..paths import repository_path
from ..retrieval import RetrievalRecord
from ..schemas import ObservationRecord, ValidationError
from .statcan import PROVINCE_DGUID_TO_GEOGRAPHY_ID, TRADE_NOC_TO_NODE


CENSUS_WORKFORCE_SOURCE_ID = "STATCAN_CENSUS_OCCUPATION_98100449"
CENSUS_WORKFORCE_PRODUCT_ID = 98100449
CENSUS_WORKFORCE_CANONICAL_URL = (
    "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810044901"
)
CENSUS_WORKFORCE_METADATA_URL = (
    "https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
)
CENSUS_WORKFORCE_DATA_URL = (
    "https://www150.statcan.gc.ca/t1/wds/rest/"
    "getDataFromCubePidCoordAndLatestNPeriods"
)
CENSUS_WORKFORCE_TRANSFORMATION_ID = "TR_STATCAN_CENSUS_WORKFORCE_CA_NOC_1_0_0"
CENSUS_REFERENCE_START = "2021-05-02"
CENSUS_REFERENCE_END = "2021-05-08"

EXPECTED_DIMENSIONS = {
    1: "Geography",
    2: "Highest certificate, diploma or degree (16)",
    3: "Age (15A)",
    4: "Gender (3)",
    5: "Occupation - Unit group - National Occupational Classification (NOC) 2021 (821A)",
    6: "Labour force status (3)",
}


def fetch_census_trade_employment(raw_root: Path) -> RetrievalRecord:
    """Retrieve the 78 selected Census cells and their complete cube metadata."""
    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    metadata_bytes, metadata_effective_url, metadata_content_type = _post_json(
        CENSUS_WORKFORCE_METADATA_URL,
        [{"productId": CENSUS_WORKFORCE_PRODUCT_ID}],
    )
    metadata_response = _json_payload(metadata_bytes, "Census cube metadata")
    metadata = _successful_object(metadata_response, "Census cube metadata")
    requests, cells = census_workforce_requests(metadata)

    data_bytes, data_effective_url, data_content_type = _post_json(
        CENSUS_WORKFORCE_DATA_URL,
        requests,
    )
    responses = _json_payload(data_bytes, "Census selected data")
    if not isinstance(responses, list):
        raise ValidationError("Census selected-data response must be a list")
    if len(responses) != len(cells):
        raise ValidationError(
            f"expected {len(cells)} Census selected-data responses, found {len(responses)}"
        )
    _validated_census_responses(responses, {item["coordinate"] for item in cells})

    payload = {
        "schema_version": "1.0.0",
        "source_id": CENSUS_WORKFORCE_SOURCE_ID,
        "product_id": CENSUS_WORKFORCE_PRODUCT_ID,
        "canonical_url": CENSUS_WORKFORCE_CANONICAL_URL,
        "retrieved_at": retrieved_at,
        "metadata_endpoint": metadata_effective_url,
        "data_endpoint": data_effective_url,
        "metadata_content_type": metadata_content_type,
        "data_content_type": data_content_type,
        "metadata_response_hash": _sha256_bytes(metadata_bytes),
        "data_response_hash": _sha256_bytes(data_bytes),
        "selection": {
            "education": "Total - Highest certificate, diploma or degree",
            "age": "Total - Age",
            "gender": "Total - Gender",
            "labour_force_status": "Employed",
            "reference_period_start": CENSUS_REFERENCE_START,
            "reference_period_end": CENSUS_REFERENCE_END,
            "geography_count": 13,
            "occupation_count": len(TRADE_NOC_TO_NODE),
        },
        "requests": cells,
        "metadata": metadata_response,
        "responses": responses,
    }
    content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    destination_dir = raw_root / "statcan_census_occupation_98100449"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{retrieved_at[:10]}_{digest[:12]}.json"
    if not destination.exists():
        destination.write_bytes(content)

    record = RetrievalRecord(
        retrieval_id=f"RET_{CENSUS_WORKFORCE_SOURCE_ID}_{digest[:16]}",
        source_id=CENSUS_WORKFORCE_SOURCE_ID,
        retrieved_at=retrieved_at,
        effective_url=data_effective_url,
        content_hash=f"sha256:{digest}",
        content_type="application/json",
        byte_length=len(content),
        archive_path=repository_path(destination),
        result="success",
    )
    destination.with_suffix(".json.manifest.json").write_text(
        json.dumps(asdict(record), indent=2) + "\n",
        encoding="utf-8",
    )
    return record


def census_workforce_requests(
    metadata: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve stable public member labels into WDS coordinates."""
    if int(metadata.get("productId", 0)) != CENSUS_WORKFORCE_PRODUCT_ID:
        raise ValidationError("unexpected Census product metadata")
    dimensions = {
        int(item["dimensionPositionId"]): item for item in metadata.get("dimension", [])
    }
    for position, name in EXPECTED_DIMENSIONS.items():
        if position not in dimensions:
            raise ValidationError(f"Census metadata is missing dimension {position}: {name}")
        if dimensions[position].get("dimensionNameEn") != name:
            raise ValidationError(
                f"Census dimension {position} changed: "
                f"{dimensions[position].get('dimensionNameEn')!r}"
            )

    geography_members = {
        str(item.get("classificationCode")): item
        for item in dimensions[1].get("member", [])
        if item.get("geoLevel") == 2
    }
    province_code_to_dguid = {
        geography_id.removeprefix("PR_"): dguid
        for dguid, geography_id in PROVINCE_DGUID_TO_GEOGRAPHY_ID.items()
    }
    if set(geography_members) != set(province_code_to_dguid):
        raise ValidationError(
            "Census province/territory membership changed; expected exactly 13 geographies"
        )

    occupation_members: dict[str, dict[str, Any]] = {}
    for item in dimensions[5].get("member", []):
        match = re.match(r"^(\d{5})\s", str(item.get("memberNameEn", "")))
        if match and match.group(1) in TRADE_NOC_TO_NODE:
            occupation_members[match.group(1)] = item
    if set(occupation_members) != set(TRADE_NOC_TO_NODE):
        raise ValidationError("Census metadata is missing one or more required NOC unit groups")

    _require_member(dimensions[2], 1, "Total - Highest certificate, diploma or degree")
    _require_member(dimensions[3], 1, "Total - Age")
    _require_member(dimensions[4], 1, "Total - Gender")
    _require_member(dimensions[6], 2, "Employed")

    requests: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    for province_code in sorted(province_code_to_dguid, key=int):
        geography = geography_members[province_code]
        dguid = province_code_to_dguid[province_code]
        geography_id = PROVINCE_DGUID_TO_GEOGRAPHY_ID[dguid]
        for noc_code in sorted(TRADE_NOC_TO_NODE):
            occupation = occupation_members[noc_code]
            coordinate = (
                f"{geography['memberId']}.1.1.1.{occupation['memberId']}.2.0.0.0.0"
            )
            requests.append(
                {
                    "productId": CENSUS_WORKFORCE_PRODUCT_ID,
                    "coordinate": coordinate,
                    "latestN": 1,
                }
            )
            cells.append(
                {
                    "coordinate": coordinate,
                    "geography_id": geography_id,
                    "geography_label": geography["memberNameEn"],
                    "statcan_dguid": dguid,
                    "province_code": province_code,
                    "noc_code": noc_code,
                    "occupation_label": re.sub(
                        r"^\d{5}\s+", "", occupation["memberNameEn"]
                    ),
                    "trade_node_id": TRADE_NOC_TO_NODE[noc_code],
                }
            )
    if len(cells) != 13 * len(TRADE_NOC_TO_NODE):
        raise ValidationError("Census workforce selection must contain exactly 78 cells")
    return requests, cells


def normalize_census_trade_employment(
    raw_path: Path, output_path: Path
) -> list[ObservationRecord]:
    """Normalize detailed Census employment counts without implying current capacity."""
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    if payload.get("source_id") != CENSUS_WORKFORCE_SOURCE_ID:
        raise ValidationError("unexpected Census workforce raw source_id")
    if int(payload.get("product_id", 0)) != CENSUS_WORKFORCE_PRODUCT_ID:
        raise ValidationError("unexpected Census workforce raw product_id")

    metadata = _successful_object(payload.get("metadata"), "archived Census metadata")
    _, expected_cells = census_workforce_requests(metadata)
    archived_cells = payload.get("requests")
    if archived_cells != expected_cells:
        raise ValidationError("archived Census request coordinates do not match metadata")

    responses = payload.get("responses")
    if not isinstance(responses, list):
        raise ValidationError("archived Census responses must be a list")
    by_coordinate: dict[str, dict[str, Any]] = {}
    for wrapped in responses:
        response = _census_data_response(wrapped)
        coordinate = str(response.get("coordinate", ""))
        if not coordinate or coordinate in by_coordinate:
            raise ValidationError("Census responses require unique coordinates")
        by_coordinate[coordinate] = response
    expected_coordinates = {item["coordinate"] for item in expected_cells}
    if set(by_coordinate) != expected_coordinates:
        raise ValidationError("Census response coordinates do not match the 78-cell request")

    observations: list[tuple[ObservationRecord, dict[str, str]]] = []
    for cell in expected_cells:
        response = by_coordinate[cell["coordinate"]]
        flags = ["census_long_form_25pct_sample", "random_rounding"]
        if int(response["responseStatusCode"]) == 2:
            # StatCan documents code 2 on 9810* Census tables as a true zero
            # filler for some otherwise valid cube coordinates.
            value = 0.0
            release_date = str(metadata.get("issueDate", ""))[:10]
            flags.extend(("wds_response_status_code:2", "census_zero_filler"))
        else:
            points = response.get("vectorDataPoint")
            if not isinstance(points, list) or len(points) != 1:
                raise ValidationError(
                    "each successful Census coordinate must return one reference-period value"
                )
            point = points[0]
            if point.get("refPerRaw") != "2021-01-01":
                raise ValidationError("unexpected Census reference period")
            raw_value = point.get("value")
            value = None if raw_value is None else float(raw_value)
            release_date = str(point.get("releaseTime", ""))[:10]
            for name in ("statusCode", "symbolCode", "securityLevelCode"):
                code = point.get(name)
                if code not in (None, 0, "0"):
                    flags.append(f"{_snake(name)}:{code}")
            if value is None:
                flags.append("value_missing_or_suppressed")

        identity = f"{CENSUS_WORKFORCE_PRODUCT_ID}|{cell['coordinate']}|Employed"
        observation = ObservationRecord(
            observation_id=(
                "OBS_CENSUS_WORKFORCE_"
                f"{hashlib.sha256(identity.encode()).hexdigest()[:20].upper()}"
            ),
            indicator_id=f"CENSUS_EMPLOYED_PERSONS_NOC_{cell['noc_code']}",
            value=value,
            unit="Persons",
            geography_id=cell["geography_id"],
            period_start=CENSUS_REFERENCE_START,
            period_end=CENSUS_REFERENCE_END,
            source_id=CENSUS_WORKFORCE_SOURCE_ID,
            evidence_status=EvidenceStatus.OBSERVED,
            as_of_date=CENSUS_REFERENCE_END,
            transformation_id=CENSUS_WORKFORCE_TRANSFORMATION_ID,
            quality_flags=tuple(flags),
        )
        observation.validate()
        observations.append(
            (
                observation,
                {
                    **cell,
                    "statistic": "Employed",
                    "release_date": release_date,
                },
            )
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "observation_id",
        "indicator_id",
        "geography_label",
        "statcan_dguid",
        "province_code",
        "noc_code",
        "occupation_label",
        "trade_node_id",
        "statistic",
        "value",
        "unit",
        "geography_id",
        "period_start",
        "period_end",
        "release_date",
        "source_id",
        "evidence_status",
        "as_of_date",
        "transformation_id",
        "quality_flags",
        "coordinate",
    )
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for observation, dimensions in observations:
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


def _post_json(url: str, payload: Any) -> tuple[bytes, str, str]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AIIO-Canada-Research/0.5 (+public research retrieval)",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return (
            response.read(),
            response.geturl(),
            response.headers.get_content_type(),
        )


def _json_payload(content: bytes, label: str) -> Any:
    try:
        return json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{label} was not valid UTF-8 JSON") from exc


def _successful_object(payload: Any, label: str) -> dict[str, Any]:
    if not isinstance(payload, list) or len(payload) != 1:
        raise ValidationError(f"{label} must contain one wrapped response")
    wrapped = payload[0]
    if not isinstance(wrapped, dict) or wrapped.get("status") != "SUCCESS":
        raise ValidationError(f"{label} did not return SUCCESS")
    result = wrapped.get("object")
    if not isinstance(result, dict) or int(result.get("responseStatusCode", -1)) != 0:
        raise ValidationError(f"{label} returned an invalid response object")
    return result


def _census_data_response(wrapped: Any) -> dict[str, Any]:
    if not isinstance(wrapped, dict) or not isinstance(wrapped.get("object"), dict):
        raise ValidationError("Census selected-data response is malformed")
    result = wrapped["object"]
    code = int(result.get("responseStatusCode", -1))
    if wrapped.get("status") == "SUCCESS" and code == 0:
        return result
    if (
        wrapped.get("status") == "FAILED"
        and code == 2
        and result.get("vectorDataPoint") == []
        and int(result.get("productId", 0)) == CENSUS_WORKFORCE_PRODUCT_ID
    ):
        return result
    raise ValidationError(
        f"Census selected-data response returned unsupported status/code "
        f"{wrapped.get('status')}/{code}"
    )


def _validated_census_responses(
    responses: list[Any], expected_coordinates: set[str]
) -> dict[str, dict[str, Any]]:
    by_coordinate: dict[str, dict[str, Any]] = {}
    for wrapped in responses:
        response = _census_data_response(wrapped)
        coordinate = str(response.get("coordinate", ""))
        if not coordinate or coordinate in by_coordinate:
            raise ValidationError("Census responses require unique coordinates")
        by_coordinate[coordinate] = response
    if set(by_coordinate) != expected_coordinates:
        raise ValidationError("Census response coordinates do not match the requested cells")
    return by_coordinate


def _require_member(dimension: dict[str, Any], member_id: int, label: str) -> None:
    member = next(
        (item for item in dimension.get("member", []) if int(item.get("memberId", 0)) == member_id),
        None,
    )
    if member is None or member.get("memberNameEn") != label:
        raise ValidationError(
            f"Census dimension {dimension.get('dimensionNameEn')} changed at member {member_id}"
        )


def _sha256_bytes(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _snake(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
