from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import ValidationError


@dataclass(frozen=True)
class PowerCase:
    it_load_mw_at_full_buildout: float
    energy_pue: float
    peak_to_it_factor: float
    load_factor: float
    grid_supply_share: float
    peak_coincidence: float
    planning_margin: float


@dataclass(frozen=True)
class PowerOverlayDefinition:
    overlay_id: str
    parameter_set_id: str
    name: str
    description: str
    geography_id: str
    evidence_status: str
    start_year: int
    end_year: int
    annual_commissioning_profile: tuple[float, ...]
    cases: dict[str, PowerCase]

    @classmethod
    def from_json(cls, path: Path) -> "PowerOverlayDefinition":
        raw = json.loads(path.read_text(encoding="utf-8"))
        definition = cls(
            overlay_id=raw["overlay_id"],
            parameter_set_id=raw["parameter_set_id"],
            name=raw["name"],
            description=raw["description"],
            geography_id=raw["geography_id"],
            evidence_status=raw["evidence_status"],
            start_year=raw["start_year"],
            end_year=raw["end_year"],
            annual_commissioning_profile=tuple(
                float(value) for value in raw["annual_commissioning_profile"]
            ),
            cases={
                case: PowerCase(**{key: float(value) for key, value in values.items()})
                for case, values in raw["cases"].items()
            },
        )
        definition.validate()
        return definition

    def validate(self) -> None:
        if self.evidence_status != "scenario":
            raise ValidationError("power overlay must carry scenario evidence status")
        years = self.end_year - self.start_year + 1
        if years <= 0 or len(self.annual_commissioning_profile) != years:
            raise ValidationError(
                "annual_commissioning_profile length must match the inclusive overlay window"
            )
        if abs(sum(self.annual_commissioning_profile) - 1) > 1e-9:
            raise ValidationError("annual_commissioning_profile must sum to one")
        if any(value < 0 for value in self.annual_commissioning_profile):
            raise ValidationError("annual commissioning shares cannot be negative")
        if set(self.cases) != {"low", "central", "high"}:
            raise ValidationError("power overlay must define low, central and high cases")
        for name, case in self.cases.items():
            if case.it_load_mw_at_full_buildout <= 0:
                raise ValidationError(f"{name} IT load must be positive")
            if case.energy_pue < 1:
                raise ValidationError(f"{name} energy PUE must be at least one")
            if case.peak_to_it_factor < 1:
                raise ValidationError(f"{name} peak-to-IT factor must be at least one")
            for field_name in ("load_factor", "grid_supply_share", "peak_coincidence"):
                value = getattr(case, field_name)
                if not 0 <= value <= 1:
                    raise ValidationError(f"{name} {field_name} must be within [0, 1]")
            if case.planning_margin < 0:
                raise ValidationError(f"{name} planning margin cannot be negative")


def run_power_overlay(input_path: Path, output_path: Path) -> dict[str, Any]:
    definition = PowerOverlayDefinition.from_json(input_path)
    cases: dict[str, Any] = {}
    for name in ("low", "central", "high"):
        case = definition.cases[name]
        facility_peak_mw = case.it_load_mw_at_full_buildout * case.peak_to_it_factor
        annual_energy_gwh = (
            case.it_load_mw_at_full_buildout
            * case.energy_pue
            * case.load_factor
            * 8760
            / 1000
        )
        grid_coincident_mw = (
            facility_peak_mw * case.grid_supply_share * case.peak_coincidence
        )
        planning_transfer_proxy_mw = grid_coincident_mw * (1 + case.planning_margin)
        cumulative_share = 0.0
        annual = []
        for offset, share in enumerate(definition.annual_commissioning_profile):
            cumulative_share += share
            annual.append(
                {
                    "calendar_year": definition.start_year + offset,
                    "commissioned_share": round(share, 3),
                    "cumulative_commissioned_share": round(cumulative_share, 3),
                    "it_load_mw": round(case.it_load_mw_at_full_buildout * cumulative_share, 1),
                    "grid_coincident_mw": round(grid_coincident_mw * cumulative_share, 1),
                    "planning_transfer_proxy_mw": round(
                        planning_transfer_proxy_mw * cumulative_share, 1
                    ),
                }
            )
        cases[name] = {
            "assumptions": {
                "it_load_mw_at_full_buildout": case.it_load_mw_at_full_buildout,
                "energy_pue": case.energy_pue,
                "peak_to_it_factor": case.peak_to_it_factor,
                "load_factor": case.load_factor,
                "grid_supply_share": case.grid_supply_share,
                "peak_coincidence": case.peak_coincidence,
                "planning_margin": case.planning_margin,
            },
            "full_buildout": {
                "facility_peak_mw": round(facility_peak_mw, 1),
                "annual_energy_gwh": round(annual_energy_gwh, 1),
                "grid_coincident_mw": round(grid_coincident_mw, 1),
                "planning_transfer_proxy_mw": round(planning_transfer_proxy_mw, 1),
            },
            "annual": annual,
        }

    output = {
        "schema_version": "1.0.0",
        "overlay_id": definition.overlay_id,
        "parameter_set_id": definition.parameter_set_id,
        "name": definition.name,
        "description": definition.description,
        "geography_id": definition.geography_id,
        "evidence_status": "scenario",
        "structural_test_banner": (
            "INDEPENDENT UNCALIBRATED POWER OVERLAY — not an AESO needs assessment, "
            "generation forecast, connection approval, or transmission plan."
        ),
        "input_file_hash": file_hash(input_path),
        "engine_file_hash": file_hash(Path(__file__)),
        "start_year": definition.start_year,
        "end_year": definition.end_year,
        "cases": cases,
        "limitations": [
            "The power overlay is independent of the CAD capex propagation model.",
            "Energy PUE is used only for annual energy; peak demand uses a separate peak-to-IT factor.",
            "The planning transfer proxy is a transparent arithmetic scenario, not a grid study.",
            "Actual requirements depend on siting, behind-the-meter supply, interconnection studies, reliability criteria and project realization.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output


def file_hash(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
