import { modelProjectDemand, DEMAND_POLICY } from './project-demand-model.mjs';
/** Deterministic sensitivities, not probabilities. Shared by briefing and dashboard.
 * @param {Parameters<typeof modelProjectDemand>[0]} projects
 * @param {{asOf?: string, exposure?: Array<{project_id: string, name: string, municipality: string, start_year: string | null, end_year: string | null}>}} options
 */
export function buildDemandRisk(projects, { asOf, exposure = [] } = {}) {
  const full = modelProjectDemand(projects, { asOf });
  const half = modelProjectDemand(projects, { asOf, proposedRealisation: 0.5 });
  const longer = modelProjectDemand(projects, {
    asOf,
    policy: { ...DEMAND_POLICY, undatedDurationMonths: 48 },
  });
  const anchored = new Set(
    full.phases
      .filter((p) => p.start !== null || p.end !== null)
      .map((p) => p.id),
  );
  const annual = full.scenarios[1].annual.map((row) => ({
    year: row.year,
    anchored: full.scenarios[1].contributors
      .filter((p) => anchored.has(p.id))
      .reduce(
        (s, p) => s + p.annual.find((a) => a.year === row.year).electricalFTE,
        0,
      ),
    fallback: full.scenarios[1].contributors
      .filter((p) => !anchored.has(p.id))
      .reduce(
        (s, p) => s + p.annual.find((a) => a.year === row.year).electricalFTE,
        0,
      ),
  }));
  const cases = [
    {name: 'Full realization / 36 months', m: full},
    {name: '50% proposed volume / 36 months', m: half},
    {name: 'Full realization / 48 months', m: longer},
  ].map(({name, m}) => {
    const e = m.scenarios[1].peak,
      h = m.scenarios[1].annual.reduce((a, b) =>
        b.hvacFTE > a.hvacFTE ? b : a,
      );
    return {
      name,
      electricalFTE: e.electricalFTE,
      electricalYear: e.year,
      hvacFTE: h.hvacFTE,
      hvacYear: h.year,
      electricalStockRatio: e.electricalFTE / 13375,
      hvacStockRatio: h.hvacFTE / 3095,
    };
  });
  const window = {
    start: Math.min(cases[0].electricalYear, cases[0].hvacYear),
    end: Math.max(cases[0].electricalYear, cases[0].hvacYear),
  };
  return {
    version: 'demand-risk-1',
    full,
    annual,
    cases,
    window,
    fallbackCapex: full.phases
      .filter((p) => !anchored.has(p.id))
      .reduce((s, p) => s + p.cost, 0),
    exposure: exposure.filter(
      (p) =>
        p.start_year !== null &&
        p.end_year !== null &&
        Number(p.start_year) <= window.end &&
        Number(p.end_year) >= window.start,
    ),
    interpretation:
      '50% is a uniform volume reduction on proposed projects, not a calibrated probability or a selected half of projects. Construction-stage volumes are retained. The 48-month case changes only wholly undated durations. Reported anchors can still require inferred endpoints. Historical workforce ratios are scale comparisons, not available capacity.',
  };
}
