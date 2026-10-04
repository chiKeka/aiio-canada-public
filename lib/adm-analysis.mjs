import { resolveConstructionBenchmark } from './alberta-evidence-summary.mjs';
// Transparent stress cases. These are analyst selections, not estimated probabilities or licensed productivity rates.
export const ADM_CASES = [
  {
    name: 'Low',
    realization: 0.25,
    constructionShare: 0.3,
    labourShare: 0.3,
    paidHourlyCost: 100,
    years: 5,
    electricalPayrollShare: 0.2,
    hvacPayrollShare: 0.1,
    paidHoursPerYear: 1840,
  },
  {
    name: 'High',
    realization: 0.75,
    constructionShare: 0.5,
    labourShare: 0.4,
    paidHourlyCost: 80,
    years: 5,
    electricalPayrollShare: 0.2,
    hvacPayrollShare: 0.1,
    paidHoursPerYear: 1840,
  },
];
export function labourSizing(capex, c) {
  if (
    !Number.isFinite(capex) ||
    capex < 0 ||
    ![c.years, c.paidHourlyCost, c.paidHoursPerYear].every(
      (n) => Number.isFinite(n) && n > 0,
    ) ||
    ![
      c.realization,
      c.constructionShare,
      c.labourShare,
      c.electricalPayrollShare,
      c.hvacPayrollShare,
    ].every((n) => Number.isFinite(n) && n >= 0 && n <= 1) ||
    c.electricalPayrollShare + c.hvacPayrollShare > 1
  )
    throw new Error('Invalid sizing assumptions');
  const construction = capex * c.realization * c.constructionShare;
  const paidHours = (construction * c.labourShare) / c.paidHourlyCost;
  return {
    construction,
    paidHours,
    electricalFTE:
      (paidHours * c.electricalPayrollShare) / c.paidHoursPerYear / c.years,
    hvacFTE: (paidHours * c.hvacPayrollShare) / c.paidHoursPerYear / c.years,
  };
}
export function planSensitivity(planMillions, exposedShare, shockPct) {
  if (
    ![planMillions, exposedShare, shockPct].every(Number.isFinite) ||
    planMillions < 0 ||
    exposedShare < 0 ||
    exposedShare > 1 ||
    shockPct < 0
  )
    throw new Error('Invalid budget sensitivity');
  return {
    costMillions: (planMillions * exposedShare * shockPct) / 100,
    planPct: exposedShare * shockPct,
  };
}
export function buildAdmAnalysis(data) {
  const capex = data.projects.reduce((s, p) => s + (p.cost ?? 0), 0);
  const plan = resolveConstructionBenchmark(
    data.benchmarks,
    'public_capital_q1_fy2026_27',
  ).value;
  return {
    capex,
    plan,
    cases: ADM_CASES.map((c) => ({ ...c, ...labourSizing(capex, c) })),
    sensitivities: [0.1, 0.25, 0.5, 1].map((share) => ({
      share,
      ...planSensitivity(plan, share, 10),
    })),
    onePercent: plan / 100,
    tenPercent: plan / 10,
  };
}
