from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .constants import EvidenceStatus
from .schemas import ValidationError


WeightCase = Literal["low", "central", "high"]
RetentionCase = Literal["low", "central", "high"]


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    label: str
    geography_id: str
    unit: str
    evidence_status: EvidenceStatus
    source_id: str | None = None
    retention_low: float = 0.0
    retention_central: float = 0.0
    retention_high: float = 0.0
    valid_from: str | None = None
    valid_to: str | None = None
    author: str | None = None
    version: str | None = None

    def retention(self, retention_case: RetentionCase) -> float:
        return getattr(self, f"retention_{retention_case}")


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source: str
    target: str
    mechanism: str
    sign: int
    weight_low: float
    weight_central: float
    weight_high: float
    lag_periods: int
    absorption: float
    evidence_status: EvidenceStatus
    confidence: str
    source_id: str | None = None
    assumption_id: str | None = None
    author: str | None = None
    version: str | None = None

    def weight(self, weight_case: WeightCase) -> float:
        return getattr(self, f"weight_{weight_case}")


@dataclass(frozen=True)
class Shock:
    node_id: str
    period: int
    value: float
    label: str


@dataclass(frozen=True)
class PathContribution:
    period: int
    node_id: str
    value: float
    node_path: tuple[str, ...]
    edge_path: tuple[str, ...]
    shock_label: str
    persistence_steps: int = 0


@dataclass(frozen=True)
class PropagationResult:
    weight_case: WeightCase
    retention_case: RetentionCase
    absorption_adjustment: float
    horizon: int
    states: dict[int, dict[str, dict[str, float]]]
    paths: tuple[PathContribution, ...]

    def to_dict(self, *, include_paths: bool = True) -> dict[str, Any]:
        output = {
            "weight_case": self.weight_case,
            "retention_case": self.retention_case,
            "absorption_adjustment": self.absorption_adjustment,
            "horizon": self.horizon,
            "states": self.states,
        }
        if include_paths:
            output["paths"] = [asdict(path) for path in self.paths]
        return output


@dataclass(frozen=True)
class GraphModel:
    schema_version: str
    model_id: str
    period_unit: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]

    @classmethod
    def from_json(cls, path: Path) -> "GraphModel":
        raw = json.loads(path.read_text(encoding="utf-8"))
        nodes = tuple(
            GraphNode(
                **{
                    **item,
                    "evidence_status": EvidenceStatus(item["evidence_status"]),
                }
            )
            for item in raw["nodes"]
        )
        edges = tuple(
            GraphEdge(
                **{
                    **item,
                    "evidence_status": EvidenceStatus(item["evidence_status"]),
                }
            )
            for item in raw["edges"]
        )
        model = cls(
            schema_version=raw["schema_version"],
            model_id=raw["model_id"],
            period_unit=raw["period_unit"],
            nodes=nodes,
            edges=edges,
        )
        model.validate()
        return model

    def validate(self) -> None:
        if self.schema_version not in {"1.0.0", "1.1.0"}:
            raise ValidationError("graph schema_version must be 1.0.0 or 1.1.0")
        node_ids = [node.node_id for node in self.nodes]
        edge_ids = [edge.edge_id for edge in self.edges]
        if len(node_ids) != len(set(node_ids)):
            raise ValidationError("graph node IDs must be unique")
        if len(edge_ids) != len(set(edge_ids)):
            raise ValidationError("graph edge IDs must be unique")
        node_id_set = set(node_ids)
        for node in self.nodes:
            if node.unit != "pressure_index":
                raise ValidationError(
                    f"{node.node_id} has unit {node.unit}; propagation graph accepts pressure_index only"
                )
            if not 0 <= node.retention_low <= node.retention_central <= node.retention_high < 1:
                raise ValidationError(
                    f"{node.node_id} retention values must be ordered within [0, 1)"
                )
            if bool(node.valid_from) != bool(node.valid_to):
                raise ValidationError(
                    f"{node.node_id} must provide both valid_from and valid_to or neither"
                )
            if node.valid_from and node.valid_to and node.valid_from > node.valid_to:
                raise ValidationError(f"{node.node_id} validity dates are inverted")
        for edge in self.edges:
            if edge.source not in node_id_set or edge.target not in node_id_set:
                raise ValidationError(f"{edge.edge_id} references an unknown node")
            if edge.source == edge.target:
                raise ValidationError(f"{edge.edge_id} self-loops are not allowed")
            if edge.sign not in {-1, 1}:
                raise ValidationError(f"{edge.edge_id} sign must be -1 or 1")
            if not 0 <= edge.weight_low <= edge.weight_central <= edge.weight_high <= 1:
                raise ValidationError(f"{edge.edge_id} weights must be ordered within [0, 1]")
            if edge.lag_periods < 1:
                raise ValidationError(f"{edge.edge_id} lag_periods must be at least one")
            if not 0 <= edge.absorption <= 1:
                raise ValidationError(f"{edge.edge_id} absorption must be within [0, 1]")
            if edge.confidence not in {"low", "medium", "high"}:
                raise ValidationError(f"{edge.edge_id} confidence is invalid")
        self._validate_acyclic()

    def _validate_acyclic(self) -> None:
        adjacency: dict[str, list[str]] = defaultdict(list)
        indegree = {node.node_id: 0 for node in self.nodes}
        for edge in self.edges:
            adjacency[edge.source].append(edge.target)
            indegree[edge.target] += 1
        queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
        visited = 0
        while queue:
            node_id = queue.popleft()
            visited += 1
            for target in sorted(adjacency.get(node_id, [])):
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        if visited != len(self.nodes):
            raise ValidationError("graph must be a directed acyclic graph")

    def outgoing(self) -> dict[str, tuple[GraphEdge, ...]]:
        grouped: dict[str, list[GraphEdge]] = defaultdict(list)
        for edge in self.edges:
            grouped[edge.source].append(edge)
        return {
            key: tuple(sorted(value, key=lambda edge: edge.edge_id))
            for key, value in grouped.items()
        }


def propagate(
    graph: GraphModel,
    shocks: list[Shock],
    horizon: int,
    weight_case: WeightCase = "central",
    retention_case: RetentionCase | None = None,
    absorption_adjustment: float = 0.0,
    max_path_depth: int = 12,
    contribution_floor: float = 1e-10,
) -> PropagationResult:
    """Propagate signed pressure contributions through a lagged, acyclic graph.

    Retention is explicit state carry-over: an arrival at a retained node contributes
    again in the next period after multiplication by that node's retention factor.
    It is not a graph edge and therefore does not consume path depth.
    """

    graph.validate()
    selected_retention = retention_case or weight_case
    nodes = {node.node_id: node for node in graph.nodes}
    outgoing = graph.outgoing()
    raw_states: dict[int, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(lambda: [0.0, 0.0, 0.0])
    )
    contributions: list[PathContribution] = []
    queue: deque[
        tuple[str, int, float, tuple[str, ...], tuple[str, ...], str, int]
    ] = deque()

    for shock in sorted(shocks, key=lambda item: (item.period, item.node_id, item.label)):
        if shock.node_id not in nodes:
            raise ValidationError(f"shock references unknown node: {shock.node_id}")
        if not 0 <= shock.period <= horizon:
            raise ValidationError("shock period must fall within the propagation horizon")
        queue.append((shock.node_id, shock.period, shock.value, (shock.node_id,), (), shock.label, 0))

    while queue:
        node_id, period, value, node_path, edge_path, shock_label, persistence_steps = queue.popleft()
        bucket = raw_states[period][node_id]
        bucket[0] += value
        bucket[1] += max(value, 0.0)
        bucket[2] += abs(min(value, 0.0))
        contributions.append(
            PathContribution(
                period,
                node_id,
                value,
                node_path,
                edge_path,
                shock_label,
                persistence_steps,
            )
        )

        retained_value = value * nodes[node_id].retention(selected_retention)
        if period + 1 <= horizon and abs(retained_value) >= contribution_floor:
            queue.append(
                (
                    node_id,
                    period + 1,
                    retained_value,
                    node_path,
                    edge_path,
                    shock_label,
                    persistence_steps + 1,
                )
            )

        if len(edge_path) >= max_path_depth:
            continue
        for edge in outgoing.get(node_id, ()):
            next_period = period + edge.lag_periods
            if next_period > horizon:
                continue
            effective_absorption = min(1.0, max(0.0, edge.absorption + absorption_adjustment))
            next_value = (
                value
                * edge.sign
                * edge.weight(weight_case)
                * (1 - effective_absorption)
            )
            if abs(next_value) < contribution_floor:
                continue
            queue.append(
                (
                    edge.target,
                    next_period,
                    next_value,
                    (*node_path, edge.target),
                    (*edge_path, edge.edge_id),
                    shock_label,
                    persistence_steps,
                )
            )

    states: dict[int, dict[str, dict[str, float]]] = {}
    for period in sorted(raw_states):
        states[period] = {}
        for node_id in sorted(raw_states[period]):
            net, positive, negative = raw_states[period][node_id]
            states[period][node_id] = {
                "net": round(net, 12),
                "positive": round(positive, 12),
                "negative": round(negative, 12),
                "absolute": round(positive + negative, 12),
            }
    return PropagationResult(
        weight_case,
        selected_retention,
        absorption_adjustment,
        horizon,
        states,
        tuple(contributions),
    )
