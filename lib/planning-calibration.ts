import graphData from '@/data/model/alberta_graph_v0.2.json';
import releaseData from '@/public/data/latest.json';
import { monthNumber } from './project-cashflow';

export type MonthlyEscalationCalibration = {
  schema_version: '1.0.0';
  calibration_id: string;
  status: 'awaiting_calibration' | 'planning_sandbox' | 'calibrated' | 'superseded';
  as_of_date: string | null;
  geography_id: string;
  model_version: string | null;
  price_basis_month?: string;
  asset_outcome?: string;
  monthly_series: Array<{ month: string; baseline_mom_pct: number | null; ai_increment_mom_pct: number | null; combined_mom_pct: number | null; lower_bound_pct: number | null; upper_bound_pct: number | null; cumulative_baseline_pct?: number | null; cumulative_ai_increment_pct?: number | null; cumulative_combined_pct?: number | null; cumulative_lower_pct?: number | null; cumulative_upper_pct?: number | null }>;
  drivers: Array<{ driver_id: string; label: string; tier: 'primary' | 'secondary'; contribution_pct_points: number | null; peak_month: string | null; confidence: 'low' | 'medium' | 'high' | null; node_ids: string[] }>;
  nodes: Array<{ node_id: string; label: string; layer: string; pressure_score: number | null }>;
  edges: Array<{ source: string; target: string; contribution_pct_points: number | null }>;
  mitigations: Array<{ driver_id: string; label: string; timing: 'now' | 'design' | 'procurement' | 'delivery'; evidence_status: string }>;
  expected_driver_slots: Array<{ driver_id: string; label: string; tier: 'primary' | 'secondary' }>;
  publication_boundary: { monthly_ai_increment_authorized: boolean; combined_project_escalation_authorized: boolean; driver_contribution_authorized: boolean; note: string };
};

export type PlanningAssumptions = {
  annualBaselinePct: number;
  peakAiAnnualPctPoints: number;
  localCapturePct: number;
  lagMonths: number;
  uncertaintyPct: number;
};

const LABELS = new Map(graphData.nodes.map((node) => [node.node_id, node.label]));
const MITIGATIONS: Record<string, Array<[string, 'now' | 'design' | 'procurement' | 'delivery']>> = {
  TRADE_ELECTRICIANS: [['Engage electrical market early', 'now'], ['Prequalify alternate contractors', 'procurement']],
  TRADE_HVAC: [['Freeze cooling scope earlier', 'design'], ['Package mechanical work early', 'procurement']],
  TRADE_CONCRETE: [['Sequence pours around peak demand', 'delivery'], ['Test precast alternatives', 'design']],
  TRADE_POWERLINE: [['Coordinate utility interfaces', 'now'], ['Reserve outage and connection windows', 'delivery']],
  MATERIAL_BUILDING_ELECTRICAL: [['Reserve long-lead equipment', 'procurement'], ['Approve equivalent equipment families', 'design']],
  MATERIAL_POWER_EQUIPMENT: [['Place transformer orders early', 'procurement'], ['Standardize equipment specifications', 'design']],
  MATERIAL_MECHANICAL: [['Lock major mechanical equipment', 'procurement'], ['Design for approved alternates', 'design']],
  MATERIAL_CONCRETE: [['Index or bulk-buy concrete inputs', 'procurement'], ['Optimize structural quantities', 'design']],
};

export function buildPlanningCalibration({ assetOutcome, durationYears, projectStart, assumptions, priceBasis = `${projectStart}-01` }: {
  assetOutcome: string;
  durationYears: number;
  projectStart: number;
  assumptions: PlanningAssumptions;
  priceBasis?: string;
}): MonthlyEscalationCalibration {
  const basis = monthNumber(priceBasis);
  const start = projectStart * 12;
  if (basis === null || basis > start || basis < 2000 * 12 || !Number.isInteger(durationYears) || durationYears < 2 || durationYears > 10) throw new Error('Invalid price basis or project duration');
  const months = start + durationYears * 12 - basis;
  const annualFlows = releaseData.scenario.annual_flows;
  const peakFlow = Math.max(...annualFlows.map((row) => row.local_civil_cad + row.local_electrical_mechanical_cad + row.local_grid_construction_cad));
  const baselineMom = (Math.pow(1 + assumptions.annualBaselinePct / 100, 1 / 12) - 1) * 100;
  const captureScale = assumptions.localCapturePct / (releaseData.scenario.local_capture_share * 100);
  const inbound = graphData.edges.filter((edge) => edge.target === assetOutcome && edge.sign > 0);
  const weightTotal = inbound.reduce((sum, edge) => sum + edge.weight_central, 0) || 1;
  const peakMonthIndex = Array.from({ length: months }, (_, index) => {
    const date = new Date(Date.UTC(Math.floor(basis / 12), basis % 12 + index, 1));
    const lagged = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() - assumptions.lagMonths, 1));
    const flow = annualFlows.find((row) => row.year === lagged.getUTCFullYear());
    return flow ? (flow.local_civil_cad + flow.local_electrical_mechanical_cad + flow.local_grid_construction_cad) / peakFlow : 0;
  });
  const peakIndex = Math.max(...peakMonthIndex);
  const peakAnnualIncrement = assumptions.peakAiAnnualPctPoints * captureScale;
  let baselineIndex = 1;
  let combinedIndex = 1;
  let lowerIndex = 1;
  let upperIndex = 1;
  const monthly_series = peakMonthIndex.map((flowIndex, index) => {
    const date = new Date(Date.UTC(Math.floor(basis / 12), basis % 12 + index, 1));
    const aiAnnual = peakAnnualIncrement * flowIndex;
    const aiMom = (Math.pow(1 + aiAnnual / 100, 1 / 12) - 1) * 100;
    const uncertainty = aiMom * assumptions.uncertaintyPct / 100;
    const lowerMom = baselineMom + Math.max(0, aiMom - uncertainty);
    const upperMom = baselineMom + aiMom + uncertainty;
    // Month-level prices: the basis month is index 1; later months compound.
    if (index > 0) {
      baselineIndex *= 1 + baselineMom / 100;
      combinedIndex *= 1 + (baselineMom + aiMom) / 100;
      lowerIndex *= 1 + lowerMom / 100;
      upperIndex *= 1 + upperMom / 100;
    }
    return {
      month: date.toISOString().slice(0, 7),
      baseline_mom_pct: baselineMom, ai_increment_mom_pct: aiMom, combined_mom_pct: baselineMom + aiMom,
      lower_bound_pct: round(lowerMom), upper_bound_pct: round(upperMom),
      cumulative_baseline_pct: (baselineIndex - 1) * 100,
      cumulative_ai_increment_pct: (combinedIndex - baselineIndex) * 100,
      cumulative_combined_pct: (combinedIndex - 1) * 100,
      cumulative_lower_pct: (lowerIndex - 1) * 100,
      cumulative_upper_pct: (upperIndex - 1) * 100,
    };
  }).filter((row) => row.month >= `${projectStart}-01`);
  const peakMonth = monthly_series.reduce((best, row) => (row.ai_increment_mom_pct ?? 0) > (best.ai_increment_mom_pct ?? 0) ? row : best, monthly_series[0]);
  const primaryShare = 0.82;
  const primary = inbound.map((edge) => {
    const upstream = graphData.edges.filter((candidate) => candidate.target === edge.source && candidate.sign > 0).sort((a, b) => b.weight_central - a.weight_central)[0]?.source;
    return {
    driver_id: edge.source, label: LABELS.get(edge.source) ?? edge.source, tier: 'primary' as const,
    contribution_pct_points: peakAnnualIncrement * peakIndex * primaryShare * edge.weight_central / weightTotal, peak_month: peakMonth?.month ?? null,
    confidence: 'low' as const, node_ids: [upstream, edge.source, assetOutcome].filter((value): value is string => Boolean(value)),
  }; });
  const secondaryShare = peakAnnualIncrement * peakIndex * 0.18;
  const secondary = [
    ['SECONDARY_WAGE', 'Wage spillover'], ['SECONDARY_PROCUREMENT', 'Procurement congestion'], ['SECONDARY_SCHEDULE', 'Schedule extension'],
  ].map(([driver_id, label]) => ({ driver_id, label, tier: 'secondary' as const, contribution_pct_points: secondaryShare / 3, peak_month: peakMonth?.month ?? null, confidence: 'low' as const, node_ids: [driver_id, assetOutcome] }));
  const drivers = [...primary, ...secondary];
  const nodes = Array.from(new Set(drivers.flatMap((driver) => driver.node_ids))).map((nodeId) => ({
    node_id: nodeId, label: LABELS.get(nodeId) ?? drivers.find((driver) => driver.driver_id === nodeId)?.label ?? nodeId,
    layer: nodeId === assetOutcome ? 'outcome' : nodeId.startsWith('AI_') ? 'AI demand' : nodeId.startsWith('SECONDARY') ? 'secondary' : nodeId.startsWith('TRADE') ? 'labour' : nodeId.startsWith('SCHEDULE') ? 'schedule' : 'material',
    pressure_score: nodeId === assetOutcome ? round(peakIndex) : round((drivers.find((driver) => driver.driver_id === nodeId)?.contribution_pct_points ?? 0) / Math.max(peakAnnualIncrement, 0.01)),
  }));
  const edges = drivers.map((driver) => ({ source: driver.driver_id, target: assetOutcome, contribution_pct_points: driver.contribution_pct_points }));
  const mitigations = primary.flatMap((driver) => (MITIGATIONS[driver.driver_id] ?? [['Run targeted market sounding', 'now'] as const]).map(([label, timing]) => ({ driver_id: driver.driver_id, label, timing, evidence_status: 'strategy candidate' })));
  return {
    schema_version: '1.0.0', calibration_id: `planning-${releaseData.scenario.scenario_id}`, status: 'planning_sandbox', as_of_date: releaseData.baseline.as_of_date,
    geography_id: 'PR_48', price_basis_month: priceBasis, asset_outcome: assetOutcome, model_version: graphData.model_id, monthly_series, drivers, nodes, edges, mitigations,
    expected_driver_slots: drivers.map(({ driver_id, label, tier }) => ({ driver_id, label, tier })),
    publication_boundary: {
      monthly_ai_increment_authorized: false, combined_project_escalation_authorized: false, driver_contribution_authorized: false,
      note: 'Assumption-driven planning output. Not an empirical forecast or an authorized decision estimate.',
    },
  };
}

function round(value: number) { return Math.round(value * 1000) / 1000; }
