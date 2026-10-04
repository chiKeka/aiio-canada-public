import { buildPlanningCalibration, type MonthlyEscalationCalibration, type PlanningAssumptions } from './planning-calibration';
import { buildCashflowOutlook, monthNumber, type SpendingProfile } from './project-cashflow';

export type DecisionInputs = { assumptions: PlanningAssumptions; budgetMillions: number; priceBasis: string; projectStart: number; durationYears: number; assetOutcome: string; spendingProfile: SpendingProfile };

export function buildDecisionOutlook(input: DecisionInputs, calibration: MonthlyEscalationCalibration) {
  const { assumptions, budgetMillions, priceBasis, projectStart, durationYears, assetOutcome, spendingProfile } = input;
  const basis = monthNumber(priceBasis);
  if (basis === null || basis < 2000 * 12 || basis > projectStart * 12 || !Number.isInteger(projectStart) || projectStart < 2026 || projectStart > 2040 || !Number.isInteger(durationYears) || durationYears < 2 || durationYears > 10 || !Number.isFinite(budgetMillions) || budgetMillions <= 0) return null;
  const planning = buildPlanningCalibration({ assetOutcome, durationYears, projectStart, assumptions, priceBasis });
  const isOfficial = calibration.status === 'calibrated' && calibration.publication_boundary.monthly_ai_increment_authorized && calibration.publication_boundary.combined_project_escalation_authorized && calibration.price_basis_month === priceBasis && calibration.asset_outcome === assetOutcome && calibration.geography_id === 'PR_48' && calibration.monthly_series.length === durationYears * 12 && calibration.monthly_series[0]?.month === `${projectStart}-01` && calibration.monthly_series.at(-1)?.month === `${projectStart + durationYears - 1}-12`;
  const active = isOfficial ? calibration : planning;
  const cashflow = buildCashflowOutlook(active.monthly_series, budgetMillions, spendingProfile);
  return { active, cashflow, isOfficial };
}

export function decisionAction(stage: string) {
  const actions: Record<string, { title: string; why: string; when: string }> = {
    concept: { title: 'Test options before locking scope', why: 'Scope and timing are still adjustable.', when: 'Before concept selection' },
    business_case: { title: 'Market-test the business case', why: 'Scenario exposure is not a tender estimate.', when: 'Before business-case approval' },
    treasury_board: { title: 'Present sensitivity, not an AI premium', why: 'Decision-makers need an independent estimate and explicit uncertainty.', when: 'At the approval gate' },
    procurement: { title: 'Validate bids and long-lead capacity', why: 'Supplier quotes can test the assumed constraints.', when: 'Before tender award' },
    delivery: { title: 'Monitor changes against the baseline', why: 'Actual commitments and schedule changes can replace assumptions.', when: 'At each monthly review' },
  };
  return actions[stage] ?? actions.business_case;
}

export function deliveryYears(start: number, end: number, scenarioStart: number, scenarioEnd: number) {
  if (![start, end, scenarioStart, scenarioEnd].every(Number.isInteger) || end < start || end - start > 10) return [];
  return Array.from({ length: end - start + 1 }, (_, i) => ({ year: start + i, overlap: start + i >= scenarioStart && start + i <= scenarioEnd }));
}
