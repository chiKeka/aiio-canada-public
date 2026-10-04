from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .scenario import ScenarioDefinition, file_hash, run_scenario
from .schemas import ValidationError


REQUIRED_VARIANT_ROLES = {
    "reference",
    "timing_front_loaded",
    "timing_constrained",
    "local_capture_high",
}


def run_scenario_suite(
    root: Path,
    contract_path: Path,
    output_path: Path,
    *,
    variant_output_dir: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    contract_path = contract_path.resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    _validate_contract(contract)

    graph_path = _resolve_repo_path(root, contract["graph_path"])
    variants = contract["variants"]
    definitions: dict[str, ScenarioDefinition] = {}
    runs: dict[str, dict[str, Any]] = {}
    run_receipts: list[dict[str, Any]] = []

    for variant in variants:
        variant_id = variant["variant_id"]
        scenario_path = _resolve_repo_path(root, variant["scenario_path"])
        committed_run_path = _resolve_repo_path(root, variant["model_run_path"])
        actual_run_path = (
            variant_output_dir.resolve() / committed_run_path.name
            if variant_output_dir is not None
            else committed_run_path
        )
        definition = ScenarioDefinition.from_json(scenario_path)
        run = run_scenario(graph_path, scenario_path, actual_run_path)
        definitions[variant_id] = definition
        runs[variant_id] = run
        run_receipts.append(
            {
                "variant_id": variant_id,
                "scenario_path": variant["scenario_path"],
                "scenario_sha256": file_hash(scenario_path),
                "model_run_path": variant["model_run_path"],
                "model_run_sha256": file_hash(actual_run_path),
            }
        )

    reference_id = contract["reference_variant_id"]
    reference = definitions[reference_id]
    _validate_variant_invariants(contract, definitions, runs, reference)

    summaries = [
        _variant_summary(variant, definitions[variant["variant_id"]], runs[variant["variant_id"]])
        for variant in variants
    ]
    comparison_matrix = _comparison_matrix(
        contract["comparison_node_ids"], variants, runs, reference_id
    )

    output = {
        "schema_version": "1.0.0",
        "suite_id": contract["suite_id"],
        "evidence_status": "scenario",
        "framing_question": contract["framing_question"],
        "reference_variant_id": reference_id,
        "contract_sha256": file_hash(contract_path),
        "graph_path": contract["graph_path"],
        "graph_sha256": file_hash(graph_path),
        "code_hashes": {
            "scenario_engine": file_hash(Path(__file__).with_name("scenario.py")),
            "scenario_suite": file_hash(Path(__file__)),
        },
        "variant_count": len(variants),
        "variant_run_receipts": run_receipts,
        "variant_summaries": summaries,
        "comparison_matrix": comparison_matrix,
        "publication_boundary": contract["publication_boundary"],
        "limitations": [
            "Every variant is a declared counterfactual assumption set, not a forecast or observed investment path.",
            "Raw pressure scores are dimensionless and unbounded; they are not percentages, probabilities, cost escalation or delay duration.",
            "The constrained-delivery annual cap is a scenario rule, not an estimate of Alberta labour, connection or construction capacity.",
            "Local capture is uniform across modelled construction components and is not a measured regional retention rate.",
            "Power-system quantities remain in the independent MW overlay and do not respond to these CAD scenario variants.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output


def _validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("evidence_status") != "scenario":
        raise ValidationError("scenario suite must carry scenario evidence status")
    variants = contract.get("variants")
    if not isinstance(variants, list) or len(variants) != 4:
        raise ValidationError("scenario suite requires exactly four declared variants")
    variant_ids = [item.get("variant_id") for item in variants]
    if len(set(variant_ids)) != len(variant_ids) or any(not item for item in variant_ids):
        raise ValidationError("scenario suite variant IDs must be present and unique")
    roles = {item.get("comparison_role") for item in variants}
    if roles != REQUIRED_VARIANT_ROLES:
        raise ValidationError("scenario suite comparison roles are incomplete")
    if contract.get("reference_variant_id") not in variant_ids:
        raise ValidationError("scenario suite reference variant is missing")
    for variant in variants:
        for field in (
            "label",
            "scenario_path",
            "model_run_path",
            "decision_question",
            "declared_change",
        ):
            if not str(variant.get(field, "")).strip():
                raise ValidationError(f"scenario suite variant requires {field}")
    node_ids = contract.get("comparison_node_ids")
    if not isinstance(node_ids, list) or not node_ids or len(node_ids) != len(set(node_ids)):
        raise ValidationError("scenario suite comparison nodes must be present and unique")
    boundary = contract.get("publication_boundary", {})
    forbidden_authorizations = (
        "forecast_authorized",
        "ai_attributable_effect_authorized",
        "project_cost_or_delay_translation_authorized",
        "power_requirement_inference_authorized",
    )
    if any(boundary.get(field) is not False for field in forbidden_authorizations):
        raise ValidationError("scenario suite publication boundary must fail closed")


def _validate_variant_invariants(
    contract: dict[str, Any],
    definitions: dict[str, ScenarioDefinition],
    runs: dict[str, dict[str, Any]],
    reference: ScenarioDefinition,
) -> None:
    invariants = contract["invariants"]
    for variant in contract["variants"]:
        variant_id = variant["variant_id"]
        definition = definitions[variant_id]
        run = runs[variant_id]
        if definition.investment_total_cad != invariants["investment_total_cad"]:
            raise ValidationError(f"{variant_id} changes the locked investment total")
        if definition.currency != invariants["currency"]:
            raise ValidationError(f"{variant_id} changes the locked currency")
        if definition.currency_year != invariants["currency_year"]:
            raise ValidationError(f"{variant_id} changes the locked currency year")
        if definition.geography_id != invariants["geography_id"]:
            raise ValidationError(f"{variant_id} changes the locked geography")
        if round(definition.modelled_component_share, 9) != round(
            invariants["modelled_component_share"], 9
        ):
            raise ValidationError(f"{variant_id} changes the locked modelled share")
        if round(1 - definition.modelled_component_share, 9) != round(
            invariants["excluded_component_share"], 9
        ):
            raise ValidationError(f"{variant_id} changes the locked excluded share")
        if run["evidence_status"] != "scenario":
            raise ValidationError(f"{variant_id} run is not scenario evidence")
        if sum(row["total_capex_cad"] for row in run["annual_flows"]) != round(
            invariants["investment_total_cad"]
        ):
            raise ValidationError(f"{variant_id} annual flows do not reconcile")

        role = variant["comparison_role"]
        if role == "reference":
            continue
        if definition.components != reference.components:
            raise ValidationError(f"{variant_id} changes component mix")
        if definition.normalization_denominators_cad != reference.normalization_denominators_cad:
            raise ValidationError(f"{variant_id} changes normalization denominators")
        if role in {"timing_front_loaded", "timing_constrained"}:
            if definition.local_capture_share != reference.local_capture_share:
                raise ValidationError(f"{variant_id} changes local capture in a timing-only test")
        if role == "timing_front_loaded":
            if (definition.start_year, definition.end_year) != (
                reference.start_year,
                reference.end_year,
            ):
                raise ValidationError("front-loaded variant must retain the reference window")
            if sum(definition.annual_profile[:5]) <= sum(reference.annual_profile[:5]):
                raise ValidationError("front-loaded variant does not increase first-five-year share")
        if role == "timing_constrained":
            if definition.end_year <= reference.end_year:
                raise ValidationError("constrained-delivery variant must extend the delivery window")
            if max(definition.annual_profile) > invariants["constrained_max_annual_profile_share"]:
                raise ValidationError("constrained-delivery variant exceeds its annual cap")
        if role == "local_capture_high":
            if definition.annual_profile != reference.annual_profile:
                raise ValidationError("high-capture variant must retain reference timing")
            if definition.local_capture_share <= reference.local_capture_share:
                raise ValidationError("high-capture variant must increase local capture")


def _variant_summary(
    variant: dict[str, Any],
    definition: ScenarioDefinition,
    run: dict[str, Any],
) -> dict[str, Any]:
    annual_flows = run["annual_flows"]
    peak_flow = max(annual_flows, key=lambda item: (item["total_capex_cad"], -item["year"]))
    local_modelled = [
        row["local_civil_cad"]
        + row["local_electrical_mechanical_cad"]
        + row["local_grid_construction_cad"]
        for row in annual_flows
    ]
    top_trade = next(item for item in run["pressure_peaks"] if item["node_type"] == "resource")
    top_material = next(item for item in run["pressure_peaks"] if item["node_type"] == "material")
    top_outcome = next(item for item in run["pressure_peaks"] if item["node_type"] == "outcome")
    cost_signal = next(
        item for item in run["pressure_peaks"] if item["node_id"] == "NONRES_CONSTRUCTION_COST"
    )
    return {
        "variant_id": variant["variant_id"],
        "label": variant["label"],
        "comparison_role": variant["comparison_role"],
        "decision_question": variant["decision_question"],
        "declared_change": variant["declared_change"],
        "scenario_id": run["scenario_id"],
        "parameter_set_id": run["parameter_set_id"],
        "delivery_start_year": annual_flows[0]["year"],
        "delivery_end_year": annual_flows[-1]["year"],
        "delivery_year_count": len(annual_flows),
        "investment_total_cad": run["investment_total_cad"],
        "first_five_year_capex_share": round(sum(definition.annual_profile[:5]), 4),
        "peak_annual_capex_cad": peak_flow["total_capex_cad"],
        "peak_annual_capex_year": peak_flow["year"],
        "annual_capex_profile": [
            {
                "year": row["year"],
                "total_capex_cad": row["total_capex_cad"],
                "local_modelled_capex_cad": local_modelled[index],
            }
            for index, row in enumerate(annual_flows)
        ],
        "local_capture_share": definition.local_capture_share,
        "local_modelled_capex_cad": sum(local_modelled),
        "peak_annual_local_modelled_capex_cad": max(local_modelled),
        "top_trade": _peak_record(top_trade),
        "top_material": _peak_record(top_material),
        "nonresidential_cost_signal": _peak_record(cost_signal),
        "top_public_delivery_outcome": _peak_record(top_outcome),
    }


def _comparison_matrix(
    node_ids: list[str],
    variants: list[dict[str, Any]],
    runs: dict[str, dict[str, Any]],
    reference_id: str,
) -> list[dict[str, Any]]:
    by_variant = {
        variant_id: {item["node_id"]: item for item in run["pressure_peaks"]}
        for variant_id, run in runs.items()
    }
    missing = {
        variant_id: sorted(set(node_ids) - set(records))
        for variant_id, records in by_variant.items()
        if set(node_ids) - set(records)
    }
    if missing:
        raise ValidationError(f"scenario comparison nodes are missing: {missing}")
    rows: list[dict[str, Any]] = []
    for node_id in node_ids:
        reference_score = by_variant[reference_id][node_id]["central"]
        reference_record = by_variant[reference_id][node_id]
        values: list[dict[str, Any]] = []
        for variant in variants:
            record = by_variant[variant["variant_id"]][node_id]
            values.append(
                {
                    "variant_id": variant["variant_id"],
                    "raw_central_pressure_score": record["central"],
                    "central_peak_year": record["central_peak_year"],
                    "raw_delta_from_reference": round(record["central"] - reference_score, 4),
                }
            )
        rows.append(
            {
                "node_id": node_id,
                "label": reference_record["label"],
                "node_type": reference_record["node_type"],
                "values": values,
            }
        )
    return rows


def _peak_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": record["node_id"],
        "label": record["label"],
        "raw_central_pressure_score": record["central"],
        "central_peak_year": record["central_peak_year"],
    }


def _resolve_repo_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValidationError("scenario suite paths must be repository-relative")
    resolved = (root / path).resolve()
    if root not in resolved.parents:
        raise ValidationError("scenario suite path escapes the repository")
    return resolved
