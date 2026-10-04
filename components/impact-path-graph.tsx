'use client';

import { useMemo, useState } from 'react';
import { ArrowRight, GitBranch, Info } from 'lucide-react';

import graphData from '@/data/model/alberta_graph_v0.2.json';

type GraphNode = (typeof graphData.nodes)[number];

const TYPE_ORDER = ['shock', 'resource', 'material', 'signal', 'outcome'];
const TYPE_LABELS: Record<string, string> = {
  shock: 'AI demand',
  resource: 'Trades',
  material: 'Materials',
  signal: 'Cost signal',
  outcome: 'Delivery outcome',
};
const TYPE_COLORS: Record<
  string,
  { fill: string; stroke: string; text: string }
> = {
  shock: { fill: '#fff0e4', stroke: '#d38252', text: '#713c24' },
  resource: { fill: '#e0f0eb', stroke: '#45988d', text: '#164f4a' },
  material: { fill: '#e6edf1', stroke: '#7597a8', text: '#294d5c' },
  signal: { fill: '#f3ecd8', stroke: '#b99a42', text: '#614f1f' },
  outcome: { fill: '#e9e4f0', stroke: '#8d79a5', text: '#453754' },
};

const X_BY_TYPE: Record<string, number> = {
  shock: 10,
  resource: 220,
  material: 430,
  signal: 640,
  outcome: 840,
};

export function ImpactPathGraph({
  assetLabel,
  outcomeNodeId,
}: {
  assetLabel: string;
  outcomeNodeId: string;
}) {
  const [view, setView] = useState<'schedule' | 'cost'>('schedule');
  const targetNodeId =
    view === 'schedule' ? outcomeNodeId : 'NONRES_CONSTRUCTION_COST';
  const graph = useMemo(() => buildRelevantGraph(targetNodeId), [targetNodeId]);
  const defaultNode =
    graph.nodes.find((node) => node.node_type === 'resource') ??
    graph.nodes.find((node) => node.node_type === 'material') ??
    graph.nodes[0];
  const [selectedNodeId, setSelectedNodeId] = useState(defaultNode.node_id);
  const selectedNode =
    graph.nodes.find((node) => node.node_id === selectedNodeId) ?? defaultNode;
  const selectedEdges = graph.edges.filter(
    (edge) =>
      edge.source === selectedNode.node_id ||
      edge.target === selectedNode.node_id,
  );
  const positions = layoutNodes(graph.nodes);

  return (
    <section
      className="bg-surface border-y border-line text-ink"
      id="dependency-graph"
    >
      <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8">
        <div className="flex flex-col justify-between gap-5 border-b border-line pb-7 lg:flex-row lg:items-end">
          <div>
            <div className="flex items-center gap-2 text-brand">
              <GitBranch className="size-4" />
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em]">
                Dependency graph
              </p>
            </div>
            <h2 className="mt-3 max-w-3xl text-2xl font-medium tracking-[-0.035em] sm:text-2xl">
              Inspect the declared mechanisms and sticky assumptions.
            </h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-subtle">
              Schedule and cost are separate graph branches. The schedule view
              isolates ancestors of the {assetLabel.toLowerCase()} outcome; the
              cost view shows the common non-residential cost-signal branch.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {TYPE_ORDER.map((type) => (
              <span
                className="inline-flex items-center gap-1.5 rounded-full border border-line bg-workspace px-2.5 py-1 text-[10px] text-subtle"
                key={type}
              >
                <span
                  className="size-2 rounded-full"
                  style={{ background: TYPE_COLORS[type].stroke }}
                />
                {TYPE_LABELS[type]}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <div
            className="inline-flex rounded-lg border border-line bg-black/10 p-1"
            aria-label="Graph branch"
          >
            <button
              aria-pressed={view === 'schedule'}
              className={`rounded-md px-3 py-2 text-xs font-medium ${view === 'schedule' ? 'bg-workspace text-brand' : 'text-subtle'}`}
              onClick={() => setView('schedule')}
              type="button"
            >
              Project schedule path
            </button>
            <button
              aria-pressed={view === 'cost'}
              className={`rounded-md px-3 py-2 text-xs font-medium ${view === 'cost' ? 'bg-workspace text-caution' : 'text-subtle'}`}
              onClick={() => setView('cost')}
              type="button"
            >
              Common cost-signal path
            </button>
          </div>
          <span className="font-mono text-[10px] text-subtle">
            {view === 'schedule'
              ? 'asset-specific outcome ancestry'
              : 'common model cost branch · not a project cost forecast'}
          </span>
        </div>

        <div className="mt-7 grid gap-5 xl:grid-cols-[minmax(0,1fr)_300px]">
          <div className="overflow-x-auto rounded-lg border border-line bg-surface p-2 sm:p-4">
            <svg
              aria-labelledby="impact-graph-title"
              className="min-w-[920px]"
              viewBox="0 0 1030 520"
            >
              <title id="impact-graph-title">{`Dependency graph for ${assetLabel}`}</title>
              <defs>
                <marker
                  id="impact-arrow"
                  markerHeight="7"
                  markerWidth="7"
                  orient="auto"
                  refX="6"
                  refY="3.5"
                  viewBox="0 0 7 7"
                >
                  <path d="M0,0 L7,3.5 L0,7 Z" fill="#78a49f" />
                </marker>
              </defs>
              {graph.edges.map((edge) => {
                const source = positions[edge.source];
                const target = positions[edge.target];
                const active =
                  edge.source === selectedNode.node_id ||
                  edge.target === selectedNode.node_id;
                if (!source || !target) return null;
                return (
                  <path
                    d={`M ${source.x + 190} ${source.y + 28} C ${source.x + 225} ${source.y + 28}, ${target.x - 35} ${target.y + 28}, ${target.x} ${target.y + 28}`}
                    fill="none"
                    key={edge.edge_id}
                    markerEnd="url(#impact-arrow)"
                    opacity={active ? 0.95 : 0.22}
                    stroke={active ? '#8fd5c9' : '#6d9694'}
                    strokeWidth={active ? 2.5 : 1.25}
                  />
                );
              })}
              {graph.nodes.map((node) => {
                const position = positions[node.node_id];
                const colors = TYPE_COLORS[node.node_type];
                const selected = node.node_id === selectedNode.node_id;
                return (
                  <foreignObject
                    height="56"
                    key={node.node_id}
                    width="190"
                    x={position.x}
                    y={position.y}
                  >
                    <button
                      aria-pressed={selected}
                      className="h-full w-full rounded-[10px] border px-3 text-left text-[11px] font-semibold leading-4 outline-none focus-visible:ring-2 focus-visible:ring-caution/30"
                      onClick={() => setSelectedNodeId(node.node_id)}
                      style={{
                        background: colors.fill,
                        borderColor: selected ? '#f2bf78' : colors.stroke,
                        borderWidth: selected ? 3 : 1.5,
                        color: colors.text,
                      }}
                      type="button"
                    >
                      {node.label}
                    </button>
                  </foreignObject>
                );
              })}
            </svg>
          </div>

          <aside className="rounded-lg border border-line bg-surface p-5">
            <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-brand">
              Selected node
            </p>
            <h3 className="mt-3 text-xl font-medium">{selectedNode.label}</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              <GraphPill>{TYPE_LABELS[selectedNode.node_type]}</GraphPill>
              <GraphPill>{selectedNode.evidence_status}</GraphPill>
              <GraphPill>{selectedNode.unit}</GraphPill>
            </div>
            <div className="mt-6 border-t border-line pt-5">
              <div className="mb-5 grid grid-cols-3 gap-2 rounded-lg border border-line bg-black/10 p-3 text-center">
                <StickyMetric
                  label="Retention"
                  value={selectedNode.retention_central}
                />
                <StickyMetric label="Low" value={selectedNode.retention_low} />
                <StickyMetric
                  label="High"
                  value={selectedNode.retention_high}
                />
              </div>
              <p className="text-xs font-medium text-subtle">
                Direct mechanisms
              </p>
              <div className="mt-3 space-y-3">
                {selectedEdges.length ? (
                  selectedEdges.map((edge) => (
                    <div
                      className="rounded-lg border border-line bg-black/10 p-3"
                      key={edge.edge_id}
                    >
                      <p className="text-xs leading-5 text-subtle">
                        {edge.mechanism.replaceAll('_', ' ')}
                      </p>
                      <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.08em] text-subtle">
                        {edge.source === selectedNode.node_id
                          ? 'outgoing'
                          : 'incoming'}{' '}
                        · {edge.lag_periods}-year lag · weight{' '}
                        {edge.weight_central.toFixed(2)} · absorption{' '}
                        {edge.absorption.toFixed(2)} · {edge.confidence}{' '}
                        confidence
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs leading-5 text-subtle">
                    No direct edges in the selected project view.
                  </p>
                )}
              </div>
            </div>
            <div className="mt-5 flex gap-2 rounded-lg bg-surface p-3 text-[11px] leading-5 text-subtle">
              <Info className="mt-0.5 size-3.5 shrink-0 text-brand" />
              Graph weights, retention and absorption are declared assumptions.
              The graph ranks mechanisms; it does not estimate dollars or days.
            </div>
          </aside>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-2 text-xs text-subtle">
          <span className="font-medium text-subtle">Reading the flow:</span>
          <span>AI demand</span>
          <ArrowRight className="size-3.5" />
          <span>shared trades and materials</span>
          <ArrowRight className="size-3.5" />
          <span>
            {view === 'schedule'
              ? 'selected delivery-pressure outcome'
              : 'non-residential cost signal'}
          </span>
        </div>
        <details className="mt-5 rounded-lg border border-line bg-workspace p-4 text-xs text-subtle">
          <summary className="cursor-pointer font-medium text-subtle">
            Accessible path list · {graph.edges.length} declared edges
          </summary>
          <ul className="mt-4 space-y-2">
            {graph.edges.map((edge) => {
              const source =
                graph.nodes.find((node) => node.node_id === edge.source)
                  ?.label ?? edge.source;
              const target =
                graph.nodes.find((node) => node.node_id === edge.target)
                  ?.label ?? edge.target;
              return (
                <li key={edge.edge_id}>
                  {source} → {target} · {edge.mechanism.replaceAll('_', ' ')} ·{' '}
                  {edge.lag_periods}-year lag · assumed, low confidence
                </li>
              );
            })}
          </ul>
        </details>
      </div>
    </section>
  );
}

function buildRelevantGraph(targetNodeId: string) {
  const includedIds = new Set([targetNodeId]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const edge of graphData.edges) {
      if (includedIds.has(edge.target) && !includedIds.has(edge.source)) {
        includedIds.add(edge.source);
        changed = true;
      }
    }
  }
  const nodes = graphData.nodes.filter((node) => includedIds.has(node.node_id));
  const edges = graphData.edges.filter(
    (edge) => includedIds.has(edge.source) && includedIds.has(edge.target),
  );
  return { nodes, edges };
}

function StickyMetric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="font-mono text-sm font-semibold text-subtle">
        {value.toFixed(2)}
      </p>
      <p className="mt-1 text-[8px] uppercase tracking-[0.08em] text-subtle">
        {label}
      </p>
    </div>
  );
}

function layoutNodes(nodes: GraphNode[]) {
  const positions: Record<string, { x: number; y: number }> = {};
  for (const type of TYPE_ORDER) {
    const members = nodes.filter((node) => node.node_type === type);
    const step = 445 / Math.max(members.length, 1);
    members.forEach((node, index) => {
      positions[node.node_id] = {
        x: X_BY_TYPE[type],
        y: 18 + index * step,
      };
    });
  }
  return positions;
}

function GraphPill({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-line bg-workspace px-2 py-1 font-mono text-[9px] uppercase tracking-[0.08em] text-subtle">
      {children}
    </span>
  );
}
