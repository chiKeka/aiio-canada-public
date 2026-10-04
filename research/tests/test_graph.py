from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aiio.constants import EvidenceStatus
from aiio.graph import GraphEdge, GraphModel, GraphNode, Shock, propagate
from aiio.power import PowerOverlayDefinition, run_power_overlay
from aiio.release import bounded_display_score
from aiio.scenario import ScenarioDefinition, run_scenario, scenario_shocks
from aiio.schemas import ValidationError


def node(node_id: str, node_type: str, retention: float = 0.0) -> GraphNode:
    return GraphNode(
        node_id,
        node_type,
        node_id,
        "PR_48",
        "pressure_index",
        EvidenceStatus.ASSUMED,
        retention_low=retention,
        retention_central=retention,
        retention_high=retention,
    )


def edge(
    edge_id: str,
    source: str,
    target: str,
    *,
    sign: int = 1,
    low: float = 0.25,
    central: float = 0.5,
    high: float = 0.75,
    absorption: float = 0.0,
) -> GraphEdge:
    return GraphEdge(
        edge_id,
        source,
        target,
        "test",
        sign,
        low,
        central,
        high,
        1,
        absorption,
        EvidenceStatus.ASSUMED,
        "low",
    )


def synthetic_graph() -> GraphModel:
    nodes = (node("A", "shock"), node("B", "resource"), node("C", "outcome"))
    edges = (
        edge("E1", "A", "B"),
        edge("E2", "B", "C", sign=-1, low=0.2, central=0.4, high=0.6),
    )
    return GraphModel("1.0.0", "TEST", "year", nodes, edges)


class GraphInvariantTests(unittest.TestCase):
    def test_identity_and_zero_shock(self) -> None:
        result = propagate(synthetic_graph(), [Shock("A", 0, 0, "zero")], horizon=3)
        self.assertEqual(result.states[0]["A"]["absolute"], 0)
        self.assertNotIn(1, result.states)
        unit = propagate(synthetic_graph(), [Shock("A", 0, 1, "unit")], horizon=0)
        self.assertEqual(unit.states[0]["A"]["net"], 1)

    def test_lag_sign_and_path_are_preserved(self) -> None:
        result = propagate(synthetic_graph(), [Shock("A", 0, 1, "unit")], horizon=3)
        self.assertEqual(result.states[1]["B"]["net"], 0.5)
        self.assertEqual(result.states[2]["C"]["net"], -0.2)
        self.assertEqual(result.states[2]["C"]["negative"], 0.2)
        path = next(item for item in result.paths if item.node_id == "C")
        self.assertEqual(path.node_path, ("A", "B", "C"))
        self.assertEqual(path.edge_path, ("E1", "E2"))

    def test_weight_cases_are_monotonic_for_positive_edge(self) -> None:
        graph = synthetic_graph()
        values = [
            propagate(graph, [Shock("A", 0, 1, "unit")], 1, case).states[1]["B"]["net"]
            for case in ("low", "central", "high")
        ]
        self.assertEqual(values, sorted(values))

    def test_persistent_state_decays_and_repropagates(self) -> None:
        graph = GraphModel(
            "1.1.0",
            "PERSISTENCE_TEST",
            "year",
            (node("A", "shock"), node("B", "resource", 0.5), node("C", "outcome")),
            (edge("E1", "A", "B"), edge("E2", "B", "C")),
        )
        result = propagate(graph, [Shock("A", 0, 1, "unit")], horizon=4)
        self.assertEqual(result.states[1]["B"]["net"], 0.5)
        self.assertEqual(result.states[2]["B"]["net"], 0.25)
        self.assertEqual(result.states[3]["B"]["net"], 0.125)
        self.assertEqual(result.states[2]["C"]["net"], 0.25)
        self.assertEqual(result.states[3]["C"]["net"], 0.125)
        retained = next(
            item for item in result.paths if item.node_id == "B" and item.period == 2
        )
        self.assertEqual(retained.persistence_steps, 1)

    def test_absorption_sensitivity_is_monotonic(self) -> None:
        graph = synthetic_graph()
        high_absorption = propagate(
            graph,
            [Shock("A", 0, 1, "unit")],
            1,
            absorption_adjustment=0.1,
        )
        low_absorption = propagate(
            graph,
            [Shock("A", 0, 1, "unit")],
            1,
            absorption_adjustment=-0.1,
        )
        self.assertLess(
            high_absorption.states[1]["B"]["absolute"],
            low_absorption.states[1]["B"]["absolute"],
        )

    def test_multi_shock_additivity(self) -> None:
        graph = synthetic_graph()
        first = propagate(graph, [Shock("A", 0, 1, "first")], 3)
        second = propagate(graph, [Shock("A", 0, 2, "second")], 3)
        combined = propagate(
            graph,
            [Shock("A", 0, 1, "first"), Shock("A", 0, 2, "second")],
            3,
        )
        for period in (0, 1, 2):
            for node_id in combined.states[period]:
                expected = (
                    first.states.get(period, {}).get(node_id, {}).get("net", 0)
                    + second.states.get(period, {}).get(node_id, {}).get("net", 0)
                )
                self.assertAlmostEqual(combined.states[period][node_id]["net"], expected)

    def test_signed_path_accounting(self) -> None:
        graph = GraphModel(
            "1.1.0",
            "SIGNED_TEST",
            "year",
            (node("A_POS", "shock"), node("A_NEG", "shock"), node("B", "outcome")),
            (
                edge("E_POS", "A_POS", "B", central=0.5),
                edge("E_NEG", "A_NEG", "B", sign=-1, central=0.5),
            ),
        )
        result = propagate(
            graph,
            [Shock("A_POS", 0, 1, "positive"), Shock("A_NEG", 0, 1, "negative")],
            1,
        )
        state = result.states[1]["B"]
        self.assertEqual(state["net"], 0)
        self.assertEqual(state["positive"], 0.5)
        self.assertEqual(state["negative"], 0.5)
        self.assertEqual(state["absolute"], state["positive"] + state["negative"])

    def test_mass_bound_for_single_unbranched_path(self) -> None:
        result = propagate(synthetic_graph(), [Shock("A", 0, 1, "unit")], horizon=3)
        for contribution in result.paths:
            self.assertLessEqual(abs(contribution.value), 1)

    def test_self_loop_is_rejected(self) -> None:
        graph = GraphModel(
            "1.1.0",
            "SELF_LOOP",
            "year",
            (node("A", "shock"),),
            (edge("E", "A", "A"),),
        )
        with self.assertRaisesRegex(ValidationError, "self-loops"):
            graph.validate()

    def test_cycle_is_rejected(self) -> None:
        graph = GraphModel(
            "1.1.0",
            "CYCLE",
            "year",
            (node("A", "shock"), node("B", "outcome")),
            (edge("E1", "A", "B"), edge("E2", "B", "A")),
        )
        with self.assertRaisesRegex(ValidationError, "acyclic"):
            graph.validate()

    def test_propagation_is_deterministic(self) -> None:
        graph = synthetic_graph()
        first = propagate(graph, [Shock("A", 0, 1, "unit")], 3).to_dict()
        second = propagate(graph, [Shock("A", 0, 1, "unit")], 3).to_dict()
        self.assertEqual(first, second)


class AlbertaScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[2]
        self.scenario_path = (
            self.root / "data" / "scenarios" / "alberta_50b_counterfactual_v0.2.json"
        )
        self.graph_path = self.root / "data" / "model" / "alberta_graph_v0.2.json"
        self.golden_path = (
            self.root / "data" / "model-runs" / "alberta_50b_counterfactual_v0.2.json"
        )
        self.power_input = (
            self.root / "data" / "scenarios" / "alberta_power_overlay_v0.1.json"
        )

    def test_scenario_decomposition_reconciles_to_total(self) -> None:
        scenario = ScenarioDefinition.from_json(self.scenario_path)
        _, flows = scenario_shocks(scenario)
        self.assertEqual(
            sum(item["total_capex_cad"] for item in flows),
            scenario.investment_total_cad,
        )
        self.assertEqual(flows[0]["year"], 2027)
        self.assertEqual(flows[-1]["year"], 2036)
        self.assertEqual(round(1 - scenario.modelled_component_share, 2), 0.54)

    def test_alberta_signal_and_outcome_high_fan_in_is_bounded(self) -> None:
        graph = GraphModel.from_json(self.graph_path)
        constrained = {
            node.node_id for node in graph.nodes if node.node_type in {"signal", "outcome"}
        }
        for node_id in constrained:
            effective_high = sum(
                edge.weight_high * (1 - edge.absorption)
                for edge in graph.edges
                if edge.target == node_id
            )
            self.assertLessEqual(effective_high, 1, node_id)

    def test_public_display_transform_is_bounded_and_monotonic(self) -> None:
        raw = [0, 0.1, 1, 2.49, 8.06, 1_000_000]
        displayed = [bounded_display_score(value) for value in raw]
        self.assertEqual(displayed, sorted(displayed))
        self.assertTrue(all(0 <= value < 1 for value in displayed))
        self.assertEqual(displayed[0], 0)

    def test_sensitivity_directions_are_coherent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = run_scenario(
                self.graph_path,
                self.scenario_path,
                Path(directory) / "run.json",
            )
        rows = {item["sensitivity_id"]: item for item in output["sensitivity"]}
        score = lambda row: row["top_resource"]["pressure_score"]
        self.assertGreater(score(rows["denominator_half"]), score(rows["baseline"]))
        self.assertLess(score(rows["denominator_double"]), score(rows["baseline"]))
        self.assertGreater(score(rows["capture_0_90"]), score(rows["capture_0_40"]))
        self.assertGreater(score(rows["retention_high"]), score(rows["retention_low"]))
        self.assertGreater(
            score(rows["joint_higher_pressure"]), score(rows["joint_lower_pressure"])
        )

    def test_power_overlay_is_independent_and_ordered(self) -> None:
        definition = PowerOverlayDefinition.from_json(self.power_input)
        self.assertEqual(definition.evidence_status, "scenario")
        with tempfile.TemporaryDirectory() as directory:
            output = run_power_overlay(self.power_input, Path(directory) / "power.json")
        values = [
            output["cases"][case]["full_buildout"]["planning_transfer_proxy_mw"]
            for case in ("low", "central", "high")
        ]
        self.assertEqual(values, sorted(values))
        central = output["cases"]["central"]
        self.assertEqual(central["full_buildout"]["facility_peak_mw"], 4400.0)
        self.assertEqual(central["annual"][-1]["calendar_year"], 2036)
        self.assertAlmostEqual(central["annual"][-1]["cumulative_commissioned_share"], 1)
        self.assertIn("independent", output["limitations"][0].lower())

    def test_committed_golden_run_matches_engine(self) -> None:
        expected = json.loads(self.golden_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            actual = run_scenario(
                self.graph_path,
                self.scenario_path,
                Path(directory) / "run.json",
            )
        self.assertEqual(json.loads(json.dumps(actual)), expected)
        self.assertEqual(actual["evidence_status"], "scenario")
        self.assertEqual(actual["engine_version"], "AIIO_GRAPH_ENGINE_0.2.0")

    def test_committed_power_golden_matches_engine(self) -> None:
        golden_path = (
            self.root / "data" / "model-runs" / "alberta_power_overlay_v0.1.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            actual_path = Path(directory) / "power.json"
            run_power_overlay(self.power_input, actual_path)
            self.assertEqual(actual_path.read_bytes(), golden_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
