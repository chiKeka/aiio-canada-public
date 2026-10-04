from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from urllib.parse import urlparse

from .constants import ALLOWED_ACCESS_METHODS, EvidenceStatus, SourceStatus


ID_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_]{2,79}$")


class ValidationError(ValueError):
    """Raised when a research record fails the publication contract."""


def _iso_date(value: str, field_name: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be an ISO date: {value!r}") from exc
    return value


def _https_url(value: str, field_name: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValidationError(f"{field_name} must be an absolute HTTPS URL: {value!r}")
    return value


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    title: str
    publisher: str
    canonical_url: str
    retrieval_url: str
    source_type: str
    domain: str
    geography: str
    as_of_date: str
    last_verified: str
    licence_note: str
    access_method: str
    update_frequency: str
    evidence_status: EvidenceStatus
    status: SourceStatus
    notes: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SourceRecord":
        missing = [
            key
            for key in (
                "source_id",
                "title",
                "publisher",
                "canonical_url",
                "retrieval_url",
                "source_type",
                "domain",
                "geography",
                "as_of_date",
                "last_verified",
                "licence_note",
                "access_method",
                "update_frequency",
                "evidence_status",
                "status",
            )
            if raw.get(key) in (None, "")
        ]
        if missing:
            raise ValidationError(f"source is missing required fields: {', '.join(missing)}")
        if not ID_PATTERN.fullmatch(str(raw["source_id"])):
            raise ValidationError(f"invalid source_id: {raw['source_id']!r}")
        if raw["access_method"] not in ALLOWED_ACCESS_METHODS:
            raise ValidationError(f"unsupported access_method: {raw['access_method']!r}")

        return cls(
            source_id=str(raw["source_id"]),
            title=str(raw["title"]),
            publisher=str(raw["publisher"]),
            canonical_url=_https_url(str(raw["canonical_url"]), "canonical_url"),
            retrieval_url=_https_url(str(raw["retrieval_url"]), "retrieval_url"),
            source_type=str(raw["source_type"]),
            domain=str(raw["domain"]),
            geography=str(raw["geography"]),
            as_of_date=_iso_date(str(raw["as_of_date"]), "as_of_date"),
            last_verified=_iso_date(str(raw["last_verified"]), "last_verified"),
            licence_note=str(raw["licence_note"]),
            access_method=str(raw["access_method"]),
            update_frequency=str(raw["update_frequency"]),
            evidence_status=EvidenceStatus(str(raw["evidence_status"])),
            status=SourceStatus(str(raw["status"])),
            notes=str(raw.get("notes", "")),
        )


@dataclass(frozen=True)
class ObservationRecord:
    observation_id: str
    indicator_id: str
    value: float | None
    unit: str
    geography_id: str
    period_start: str
    period_end: str
    source_id: str
    evidence_status: EvidenceStatus
    as_of_date: str
    transformation_id: str | None = None
    quality_flags: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if not self.observation_id or not self.indicator_id:
            raise ValidationError("observations require stable observation and indicator IDs")
        if not self.unit or not self.geography_id or not self.source_id:
            raise ValidationError("observations require unit, geography_id and source_id")
        _iso_date(self.period_start, "period_start")
        _iso_date(self.period_end, "period_end")
        _iso_date(self.as_of_date, "as_of_date")
        if self.period_start > self.period_end:
            raise ValidationError("period_start cannot be after period_end")
        if self.value is None and not self.quality_flags:
            raise ValidationError("missing observation values require a quality flag")
        if self.evidence_status is EvidenceStatus.SCENARIO:
            raise ValidationError("scenario values cannot enter the observation layer")


@dataclass(frozen=True)
class PublicProjectRecord:
    project_id: str
    source_record_id: str
    name: str
    description: str
    geography_id: str
    province: str
    municipality: str
    region: str
    asset_class: str
    asset_class_evidence_status: str
    source_category: str
    source_type: str
    source_subtype: str
    stage: str
    stage_source_text: str
    start_period: str
    completion_period: str
    start_year: int | None
    end_year: int | None
    estimated_cost_cad: float | None
    cost_status: str
    public_funding_signal: str
    public_funding_evidence_status: str
    lead_organization: str
    supporting_ministry: str
    latitude: float | None
    longitude: float | None
    project_url: str
    source_id: str
    source_scope: str
    source_evidence_status: EvidenceStatus
    as_of_date: str
    quality_flags: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if not ID_PATTERN.fullmatch(self.project_id):
            raise ValidationError(f"invalid public project_id: {self.project_id!r}")
        if not self.source_record_id or not self.name.strip():
            raise ValidationError("public projects require source_record_id and name")
        if not self.geography_id.startswith("PR_") or not self.province:
            raise ValidationError("public projects require a provincial geography")
        if not self.asset_class or not self.asset_class_evidence_status:
            raise ValidationError("public projects require an explicit asset classification")
        if self.estimated_cost_cad is not None and self.estimated_cost_cad < 0:
            raise ValidationError("public project cost cannot be negative")
        if self.start_year is not None and not 1900 <= self.start_year <= 2200:
            raise ValidationError("public project start_year is outside the supported range")
        if self.end_year is not None and not 1900 <= self.end_year <= 2200:
            raise ValidationError("public project end_year is outside the supported range")
        if (
            self.start_year is not None
            and self.end_year is not None
            and self.start_year > self.end_year
        ):
            raise ValidationError("public project start_year cannot exceed end_year")
        if self.latitude is not None and not -90 <= self.latitude <= 90:
            raise ValidationError("public project latitude is invalid")
        if self.longitude is not None and not -180 <= self.longitude <= 180:
            raise ValidationError("public project longitude is invalid")
        if self.project_url:
            _https_url(self.project_url, "project_url")
        _iso_date(self.as_of_date, "as_of_date")
        if self.source_evidence_status is EvidenceStatus.SCENARIO:
            raise ValidationError("scenario records cannot enter the public-project layer")


@dataclass(frozen=True)
class ScenarioRecord:
    scenario_id: str
    geography_id: str
    investment_total_cad: float
    currency_year: int
    start_year: int
    end_year: int
    construction_share: float
    local_capture_share: float
    evidence_status: EvidenceStatus = EvidenceStatus.SCENARIO

    def validate(self) -> None:
        if self.evidence_status is not EvidenceStatus.SCENARIO:
            raise ValidationError("scenario overlays must carry scenario evidence status")
        if self.investment_total_cad < 0:
            raise ValidationError("investment_total_cad cannot be negative")
        if self.start_year > self.end_year:
            raise ValidationError("start_year cannot be after end_year")
        for name, value in (
            ("construction_share", self.construction_share),
            ("local_capture_share", self.local_capture_share),
        ):
            if not 0 <= value <= 1:
                raise ValidationError(f"{name} must be within [0, 1]")
