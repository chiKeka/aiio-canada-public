import release from '@/public/data/latest.json';
import { buildExecutiveEvidence } from './executive-evidence';
import { decisionAction, type buildDecisionOutlook, type DecisionInputs } from './decision-outlook';
import { type buildDecisionAnalysis, METROS } from './decision-analysis';
import { allocateMonthlyDrivers } from './project-cashflow';

export const RECORD_VERSION = 'AIIO_EXECUTIVE_RECORD_1.0';
type Assessment = ReturnType<typeof buildDecisionOutlook>;
export type RecordComparison = { inputs: DecisionInputs; assessment: Assessment; market: string };
export function resolveFocus(assessment: Assessment, month: string | null, driverId: string | null) {
  const active = assessment?.active;
  return { month: active?.monthly_series.find((row) => row.month === month)?.month ?? active?.monthly_series[0]?.month ?? null,
    driverId: active?.drivers.find((row) => row.driver_id === driverId)?.driver_id ?? active?.drivers[0]?.driver_id ?? null };
}

export function buildAssessmentRecord({ inputs, assessment, analysis, projectName, approvalStage, contingencyPct, comparison, selectedMonth, selectedDriver, generatedAt, planning }: {
  inputs: DecisionInputs; assessment: Assessment; analysis: ReturnType<typeof buildDecisionAnalysis>; projectName: string; approvalStage: string; contingencyPct: number;
  comparison: RecordComparison | null; selectedMonth: string | null; selectedDriver: string | null; generatedAt: string;
  planning: { status: string; passed_check_count: number; check_count: number };
}) {
  if (!assessment?.cashflow || !Number.isFinite(contingencyPct) || contingencyPct < 0 || !Number.isFinite(Date.parse(generatedAt))) return null;
  const focus = resolveFocus(assessment, selectedMonth, selectedDriver);
  const price = assessment.active.monthly_series.find((row) => row.month === focus.month)!;
  const contributions = allocateMonthlyDrivers(assessment.active.drivers.map((driver) => driver.contribution_pct_points), assessment.isOfficial ? null : price.ai_increment_mom_pct);
  const drivers = assessment.active.drivers.map((driver, index) => ({ ...driver, selected_month_allocation_pp: contributions[index] }));
  const comparable = comparison?.assessment?.cashflow && comparison.inputs.priceBasis === inputs.priceBasis;
  // Detach the record from live state: later UI changes must not rewrite an export.
  return JSON.parse(JSON.stringify({
    schema_version: RECORD_VERSION, generated_at: generatedAt,
    project: { name: projectName, asset: analysis.asset.label, market: METROS[analysis.metroId], geography_id: analysis.metroId, approval_stage: approvalStage, inputs, contingency_pct: contingencyPct, contingency_millions: inputs.budgetMillions * contingencyPct / 100 },
    model: { record_version: RECORD_VERSION, calculation_contract: 'AIIO_PRICE_BASIS_CASHFLOW_1.0', calibration_id: assessment.active.calibration_id, model_version: assessment.active.model_version, status: assessment.active.status, is_scope_matched_calibration: assessment.isOfficial, release_manifest: release.manifest },
    focus, result: assessment.cashflow, monthly_prices: assessment.active.monthly_series,
    drivers, graph: { nodes: assessment.active.nodes, edges: assessment.active.edges }, mitigations: assessment.active.mitigations,
    decision: decisionAction(approvalStage), evidence: buildExecutiveEvidence(analysis), planning_validation: planning,
    comparison: comparison ? { ...comparison, scenario_spend_delta_millions: comparable ? assessment.cashflow.combinedSpend - comparison.assessment!.cashflow!.combinedSpend : null, delta_status: comparable ? 'same_price_basis_configuration_comparison' : 'withheld_missing_results_or_different_price_basis' } : null,
    boundary: { causal_ai_effect_authorized: false, mitigation_savings_authorized: false, note: 'Scenario sensitivity, not an approved estimate adjustment or a causal AI effect. Context signals do not set scenario rates. Contingency is separate. Driver allocations are not extra costs to add.', reproduction: 'Stored monthly prices and spending inputs reproduce cash-flow results. This export preserves the displayed model output, not an executable archive of the model. The release manifest identifies the underlying research release, not the current application commit.' },
  })) as {
    schema_version: string; generated_at: string;
    project: { name: string; asset: string; market: string; geography_id: string; approval_stage: string; inputs: DecisionInputs; contingency_pct: number; contingency_millions: number };
    model: { record_version: string; calculation_contract: string; calibration_id: string; model_version: string | null; status: string; is_scope_matched_calibration: boolean; release_manifest: typeof release.manifest };
    focus: ReturnType<typeof resolveFocus>; result: NonNullable<NonNullable<Assessment>['cashflow']>; monthly_prices: NonNullable<Assessment>['active']['monthly_series'];
    drivers: typeof drivers; graph: { nodes: NonNullable<Assessment>['active']['nodes']; edges: NonNullable<Assessment>['active']['edges'] }; mitigations: NonNullable<Assessment>['active']['mitigations'];
    decision: ReturnType<typeof decisionAction>; evidence: ReturnType<typeof buildExecutiveEvidence>; planning_validation: typeof planning;
    comparison: (RecordComparison & { scenario_spend_delta_millions: number | null; delta_status: string }) | null;
    boundary: { causal_ai_effect_authorized: false; mitigation_savings_authorized: false; note: string; reproduction: string };
  };
}
export type AssessmentRecord = NonNullable<ReturnType<typeof buildAssessmentRecord>>;

/** Integrity checksum, not a signature or proof of validation. */
export async function encodeAssessmentRecord(record: AssessmentRecord) {
  const payload = JSON.stringify(record);
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(payload));
  const sha256 = Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('');
  return JSON.stringify({ format: 'AIIO_SNAPSHOT_ENVELOPE_1.0', sha256, payload }, null, 2);
}
