from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .graph import GraphModel, PropagationResult, Shock, propagate
from .schemas import ValidationError


ENGINE_VERSION = "AIIO_GRAPH_ENGINE_0.2.0"
CASE_NAMES = ("low", "central", "high")


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    parameter_set_id: str
    name: str
    description: str
    geography_id: str
    evidence_status: str
    currency: str
    currency_year: int
    investment_total_cad: float
    start_year: int
    end_year: int
    local_capture_share: float
    components: dict[str, float]
    annual_profile: tuple[float, ...]
    normalization_denominators_cad: dict[str, float]

    @classmethod
    def from_json(cls, path: Path) -> "ScenarioDefinition":
        raw = json.loads(path.read_text(encoding="utf-8"))
        scenario = cls(
            scenario_id=raw["scenario_id"],
            parameter_set_id=raw["parameter_set_id"],
            name=raw["name"],
            description=raw["description"],
            geography_id=raw["geography_id"],
            evidence_status=raw["evidence_status"],
            currency=raw["currency"],
            currency_year=raw["currency_year"],
            investment_total_cad=float(raw["investment_total_cad"]),
            start_year=raw["start_year"],
            end_year=raw["end_year"],
            local_capture_share=float(raw["local_capture_share"]),
            components={key: float(value) for key, value in raw["components"].items()},
            annual_profile=tuple(float(value) for value in raw["annual_profile"]),
            normalization_denominators_cad={
                key: float(value) for key, value in raw["normalization_denominators_cad"].items()
            },
        )
        scenario.validate()
        return scenario

    def validate(self) -> None:
        if self.evidence_status != "scenario":
            raise ValidationError("scenario definition must carry scenario evidence status")
        if self.currency != "CAD":
            raise ValidationError("initial engine accepts CAD scenarios only")
        years = self.end_year - self.start_year + 1
        if years <= 0 or len(self.annual_profile) != years:
            raise ValidationError("annual_profile length must match the inclusive scenario window")
        if abs(sum(self.annual_profile) - 1) > 1e-9:
            raise ValidationError("annual_profile must sum to one")
        if abs(sum(self.components.values()) - 1) > 1e-9:
            raise ValidationError("scenario component shares must sum to one")
        if not 0 <= self.local_capture_share <= 1:
            raise ValidationError("local_capture_share must be within [0, 1]")
        required_components = {
            "site_development",
            "building_and_civil",
            "electrical_and_mechanical",
            "grid_and_generation",
            "computing_and_networking",
            "professional_and_other",
        }
        if set(self.components) != required_components:
            raise ValidationError("scenario components do not match the frozen v1 decomposition")
        required_denominators = {"civil", "electrical_mechanical", "grid_construction"}
        if set(self.normalization_denominators_cad) != required_denominators:
            raise ValidationError("scenario normalization denominators are incomplete")
        if any(value <= 0 for value in self.normalization_denominators_cad.values()):
            raise ValidationError("normalization denominators must be positive")

    @property
    def modelled_component_share(self) -> float:
        return (
            self.components["site_development"]
            + self.components["building_and_civil"]
            + self.components["electrical_and_mechanical"]
            + self.components["grid_and_generation"]
        )


def scenario_shocks(
    scenario: ScenarioDefinition,
    *,
    local_capture_share: float | None = None,
    denominator_multiplier: float = 1.0,
) -> tuple[list[Shock], list[dict[str, int]]]:
    if denominator_multiplier <= 0:
        raise ValidationError("denominator_multiplier must be positive")
    capture = scenario.local_capture_share if local_capture_share is None else local_capture_share
    if not 0 <= capture <= 1:
        raise ValidationError("local capture override must be within [0, 1]")

    shocks: list[Shock] = []
    annual_flows: list[dict[str, int]] = []
    excluded_share = 1 - scenario.modelled_component_share
    for period, profile_share in enumerate(scenario.annual_profile):
        total = scenario.investment_total_cad * profile_share
        civil_cad = total * (
            scenario.components["site_development"] + scenario.components["building_and_civil"]
        ) * capture
        electrical_cad = total * scenario.components["electrical_and_mechanical"] * capture
        grid_cad = total * scenario.components["grid_and_generation"] * capture
        year = scenario.start_year + period
        annual_flows.append(
            {
                "year": year,
                "total_capex_cad": round(total),
                "local_civil_cad": round(civil_cad),
                "local_electrical_mechanical_cad": round(electrical_cad),
                "local_grid_construction_cad": round(grid_cad),
                "excluded_from_graph_capex_cad": round(total * excluded_share),
            }
        )
        shocks.extend(
            [
                Shock(
                    "AI_CIVIL_DEMAND",
                    period,
                    civil_cad
                    / (scenario.normalization_denominators_cad["civil"] * denominator_multiplier),
                    f"{scenario.scenario_id}:{year}:civil",
                ),
                Shock(
                    "AI_ELECTRICAL_MECHANICAL_DEMAND",
                    period,
                    electrical_cad
                    / (
                        scenario.normalization_denominators_cad["electrical_mechanical"]
                        * denominator_multiplier
                    ),
                    f"{scenario.scenario_id}:{year}:electrical_mechanical",
                ),
                Shock(
                    "AI_GRID_CONSTRUCTION_DEMAND",
                    period,
                    grid_cad
                    / (
                        scenario.normalization_denominators_cad["grid_construction"]
                        * denominator_multiplier
                    ),
                    f"{scenario.scenario_id}:{year}:grid_construction",
                ),
            ]
        )
    return shocks, annual_flows


def run_scenario(graph_path: Path, scenario_path: Path, output_path: Path) -> dict[str, Any]:
    graph = GraphModel.from_json(graph_path)
    scenario = ScenarioDefinition.from_json(scenario_path)
    shocks, annual_flows = scenario_shocks(scenario)
    horizon = len(scenario.annual_profile) + 5
    results = {
        case: propagate(
            graph,
            shocks,
            horizon=horizon,
            weight_case=case,
            retention_case=case,
        )
        for case in CASE_NAMES
    }
    code_hashes = {
        "graph_engine": file_hash(Path(__file__).with_name("graph.py")),
        "scenario_engine": file_hash(Path(__file__)),
    }
    engine_hash = "sha256:" + hashlib.sha256(
        json.dumps(code_hashes, sort_keys=True).encode("utf-8")
    ).hexdigest()
    output = {
        "schema_version": "1.1.0",
        "engine_version": ENGINE_VERSION,
        "engine_hash": engine_hash,
        "code_hashes": code_hashes,
        "model_id": graph.model_id,
        "scenario_id": scenario.scenario_id,
        "parameter_set_id": scenario.parameter_set_id,
        "scenario_name": scenario.name,
        "scenario_description": scenario.description,
        "geography_id": scenario.geography_id,
        "evidence_status": "scenario",
        "structural_test_banner": (
            "UNCALIBRATED STRUCTURAL DIAGNOSTIC — not an empirical finding, forecast, "
            "probability interval, or project-level delay estimate."
        ),
        "scenario_file_hash": file_hash(scenario_path),
        "graph_file_hash": file_hash(graph_path),
        "horizon_start_year": scenario.start_year,
        "horizon_end_year": scenario.start_year + horizon,
        "investment_total_cad": round(scenario.investment_total_cad),
        "modelled_component_share": round(scenario.modelled_component_share, 2),
        "excluded_component_share": round(1 - scenario.modelled_component_share, 2),
        "local_capture_share": scenario.local_capture_share,
        "annual_flows": annual_flows,
        "pressure_peaks": pressure_peaks(graph, results, scenario.start_year),
        "dominant_outcome_paths": dominant_outcome_paths(
            graph, results["central"], scenario.start_year
        ),
        "sensitivity": run_sensitivity(graph, scenario, horizon),
        "propagation": {
            case: result.to_dict(include_paths=False) for case, result in results.items()
        },
        "case_note": (
            "Low, central and high are co-moving structural weight-and-retention cases. "
            "They are not confidence bounds or a probability distribution."
        ),
        "limitations": [
            "Pressure scores are dimensionless diagnostic indices; 0.24 does not mean a 24% delay.",
            "The graph excludes 54% of capex assigned to computing, networking, professional and other costs.",
            "All graph weights, retention factors, absorption values, local capture and normalization denominators are declared assumptions pending calibration.",
            "Uniform local capture is a simplifying assumption tested at 0.40, 0.72 and 0.90.",
            "Power-system quantities are excluded from this CAD propagation model and published in an independent MW-based overlay.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output


def pressure_peaks(
    graph: GraphModel,
    results: dict[str, PropagationResult],
    start_year: int,
) -> list[dict[str, Any]]:
    labels = {node.node_id: node.label for node in graph.nodes}
    types = {node.node_id: node.node_type for node in graph.nodes}
    output: list[dict[str, Any]] = []
    for node_id in sorted(labels):
        if types[node_id] == "shock":
            continue
        row: dict[str, Any] = {
            "node_id": node_id,
            "label": labels[node_id],
            "node_type": types[node_id],
        }
        for case, result in results.items():
            candidates = [
                (period, values.get(node_id, {}).get("absolute", 0.0))
                for period, values in result.states.items()
            ]
            peak_period, peak_value = max(candidates, key=lambda item: (item[1], -item[0]))
            row[case] = round(peak_value, 2)
            row[f"{case}_peak_year"] = start_year + peak_period
        output.append(row)
    return sorted(output, key=lambda item: (-item["central"], item["node_id"]))


def dominant_outcome_paths(
    graph: GraphModel,
    result: PropagationResult,
    start_year: int,
    limit: int = 12,
) -> list[dict[str, Any]]:
    outcome_ids = {node.node_id for node in graph.nodes if node.node_type == "outcome"}
    paths = [path for path in result.paths if path.node_id in outcome_ids and path.edge_path]
    selected = sorted(
        paths,
        key=lambda item: (-abs(item.value), item.period, item.edge_path, item.shock_label),
    )[:limit]
    return [
        {
            "period": item.period,
            "calendar_year": start_year + item.period,
            "target_node_id": item.node_id,
            "contribution": round(item.value, 4),
            "node_path": item.node_path,
            "edge_path": item.edge_path,
            "shock_label": item.shock_label,
            "persistence_steps": item.persistence_steps,
        }
        for item in selected
    ]


def run_sensitivity(
    graph: GraphModel,
    scenario: ScenarioDefinition,
    horizon: int,
) -> list[dict[str, Any]]:
    definitions = (
        ("baseline", "Central structural assumptions", "central", "central", 1.0, 0.0, scenario.local_capture_share),
        ("denominator_half", "All denominators ×0.5", "central", "central", 0.5, 0.0, scenario.local_capture_share),
        ("denominator_double", "All denominators ×2.0", "central", "central", 2.0, 0.0, scenario.local_capture_share),
        ("absorption_minus_0_10", "All edge absorption −0.10", "central", "central", 1.0, -0.10, scenario.local_capture_share),
        ("absorption_plus_0_10", "All edge absorption +0.10", "central", "central", 1.0, 0.10, scenario.local_capture_share),
        ("capture_0_40", "Local capture = 0.40", "central", "central", 1.0, 0.0, 0.40),
        ("capture_0_90", "Local capture = 0.90", "central", "central", 1.0, 0.0, 0.90),
        ("retention_low", "Low retention only", "central", "low", 1.0, 0.0, scenario.local_capture_share),
        ("retention_high", "High retention only", "central", "high", 1.0, 0.0, scenario.local_capture_share),
        ("joint_lower_pressure", "Joint lower-pressure diagnostic", "low", "low", 2.0, 0.10, 0.40),
        ("joint_higher_pressure", "Joint higher-pressure diagnostic", "high", "high", 0.5, -0.10, 0.90),
    )
    rows: list[dict[str, Any]] = []
    for (
        sensitivity_id,
        label,
        weight_case,
        retention_case,
        denominator_multiplier,
        absorption_adjustment,
        capture,
    ) in definitions:
        shocks, _ = scenario_shocks(
            scenario,
            local_capture_share=capture,
            denominator_multiplier=denominator_multiplier,
        )
        result = propagate(
            graph,
            shocks,
            horizon=horizon,
            weight_case=weight_case,
            retention_case=retention_case,
            absorption_adjustment=absorption_adjustment,
        )
        resource_peak = peak_for_type(graph, result, "resource", scenario.start_year)
        outcome_peak = peak_for_type(graph, result, "outcome", scenario.start_year)
        rows.append(
            {
                "sensitivity_id": sensitivity_id,
                "label": label,
                "weight_case": weight_case,
                "retention_case": retention_case,
                "denominator_multiplier": denominator_multiplier,
                "absorption_adjustment": absorption_adjustment,
                "local_capture_share": capture,
                "top_resource": resource_peak,
                "top_public_delivery_outcome": outcome_peak,
            }
        )
    return rows


def peak_for_type(
    graph: GraphModel,
    result: PropagationResult,
    node_type: str,
    start_year: int,
) -> dict[str, Any]:
    labels = {node.node_id: node.label for node in graph.nodes if node.node_type == node_type}
    candidates: list[tuple[float, int, str]] = []
    for period, states in result.states.items():
        for node_id in labels:
            candidates.append((states.get(node_id, {}).get("absolute", 0.0), period, node_id))
    value, period, node_id = max(candidates, key=lambda item: (item[0], -item[1], item[2]))
    return {
        "node_id": node_id,
        "label": labels[node_id],
        "pressure_score": round(value, 2),
        "calendar_year": start_year + period,
    }


def file_hash(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
