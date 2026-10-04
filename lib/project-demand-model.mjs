/** Project-resolved, monthly labour allocation. Model inputs remain distinct from source observations. */
export const DEMAND_CASES = [
  {
    name: 'Low',
    constructionShare: 0.3,
    labourShare: 0.3,
    paidHourlyCost: 100,
  },
  {
    name: 'Central',
    constructionShare: 0.4,
    labourShare: 0.35,
    paidHourlyCost: 90,
  },
  {
    name: 'High',
    constructionShare: 0.5,
    labourShare: 0.4,
    paidHourlyCost: 80,
  },
];
export const DEMAND_POLICY = {
  durationMonths: 36,
  undatedDurationMonths: 36,
  undatedLeadMonths: 18,
  annualPaidHours: 1840,
  electricalPayrollShare: 0.2,
  hvacPayrollShare: 0.1,
  electricalWindow: [0.25, 1],
  hvacWindow: [0.3, 1],
};
const cdf = (x) =>
  x <= 0 ? 0 : x >= 1 ? 1 : x <= 0.5 ? 2 * x * x : 1 - 2 * (1 - x) * (1 - x);
export function monthlyShare(month, start, end) {
  if (!(end > start)) throw new Error('Invalid package window');
  return (
    cdf((month + 1 - start) / (end - start)) -
    cdf((month - start) / (end - start))
  );
}
export function modelProjectDemand(
  projects,
  {
    asOf = '2026-09-06',
    firstYear = 2027,
    years = 10,
    policy = DEMAND_POLICY,
    proposedRealisation = 1,
  } = {},
) {
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(asOf) ||
    !Number.isInteger(firstYear) ||
    !Number.isInteger(years) ||
    years < 1 ||
    years > 20 ||
    !(policy.durationMonths > 0) ||
    !Number.isFinite(proposedRealisation) ||
    proposedRealisation < 0 ||
    proposedRealisation > 1 ||
    !(policy.undatedDurationMonths > 0) ||
    !(policy.annualPaidHours > 0) ||
    policy.undatedLeadMonths < 0
  )
    throw new Error('Invalid model configuration');
  if (
    ![policy.electricalPayrollShare, policy.hvacPayrollShare].every(
      (n) => Number.isFinite(n) && n >= 0 && n <= 1,
    ) ||
    policy.electricalPayrollShare + policy.hvacPayrollShare > 1 ||
    ![policy.electricalWindow, policy.hvacWindow].every(
      (w) =>
        Array.isArray(w) &&
        w.length === 2 &&
        Number.isFinite(w[0]) &&
        Number.isFinite(w[1]) &&
        w[0] >= 0 &&
        w[1] <= 1 &&
        w[1] > w[0],
    )
  )
    throw new Error('Invalid trade allocation');
  const now = Number(asOf.slice(0, 4)) * 12 + Number(asOf.slice(5, 7)) - 1;
  const phases = [],
    excluded = [];
  const ids = new Set();
  for (const p of projects) {
    if (ids.has(p.id)) throw new Error('Duplicate project');
    ids.add(p.id);
    if (p.cost === null) {
      excluded.push({
        id: p.id,
        name: p.name,
        reason: 'No reported cost; no cost imputed',
      });
      continue;
    }
    if (!Number.isFinite(p.cost) || p.cost < 0) throw new Error('Invalid cost');
    let start = p.start === null ? null : p.start * 12;
    let end = p.end === null ? null : (p.end + 1) * 12;
    let basis = 'Reported start/end years; January/December conventions';
    if (start === null && end === null) {
      start = now + policy.undatedLeadMonths;
      end = start + policy.undatedDurationMonths;
      basis = `Model-assigned start: as-of + ${policy.undatedLeadMonths} months; ${policy.undatedDurationMonths}-month duration`;
    } else if (start === null) {
      start = end - policy.durationMonths;
      basis = `Reported end year; model-inferred start from ${policy.durationMonths}-month duration`;
    } else if (end === null) {
      end = start + policy.durationMonths;
      basis = `Reported start year; model-inferred end from ${policy.durationMonths}-month duration`;
    }
    if (end <= start) throw new Error('Invalid source schedule');
    if (p.stage !== 'Under Construction' && start < now) {
      const duration = end - start;
      start = now;
      end = start + duration;
      basis += '; past proposed start shifted to as-of month';
    }
    phases.push({ ...p, startMonth: start, endMonth: end, basis });
  }
  const scenarios = DEMAND_CASES.map((c) => {
    const annual = Array.from({ length: years }, (_, i) => ({
      year: firstYear + i,
      electricalHours: 0,
      hvacHours: 0,
      electricalFTE: 0,
      hvacFTE: 0,
    }));
    let allElectricalHours = 0,
      allHvacHours = 0,
      preElectricalHours = 0,
      postElectricalHours = 0;
    const contributors = [];
    for (const p of phases) {
      const realisation =
        p.stage === 'Under Construction' ? 1 : proposedRealisation;
      const payroll =
        p.cost * c.constructionShare * c.labourShare * realisation;
      const electricalHours =
        (payroll / c.paidHourlyCost) * policy.electricalPayrollShare;
      const hvacHours = (payroll / c.paidHourlyCost) * policy.hvacPayrollShare;
      allElectricalHours += electricalHours;
      allHvacHours += hvacHours;
      const span = p.endMonth - p.startMonth;
      const ea = p.startMonth + span * policy.electricalWindow[0],
        eb = p.startMonth + span * policy.electricalWindow[1];
      const ha = p.startMonth + span * policy.hvacWindow[0],
        hb = p.startMonth + span * policy.hvacWindow[1];
      preElectricalHours +=
        electricalHours * cdf((firstYear * 12 - ea) / (eb - ea));
      postElectricalHours +=
        electricalHours *
        (1 - cdf(((firstYear + years) * 12 - ea) / (eb - ea)));
      const byYear = [];
      for (const row of annual) {
        let e = 0,
          h = 0;
        for (let m = row.year * 12; m < (row.year + 1) * 12; m++) {
          e += electricalHours * monthlyShare(m, ea, eb);
          h += hvacHours * monthlyShare(m, ha, hb);
        }
        row.electricalHours += e;
        row.hvacHours += h;
        byYear.push({
          year: row.year,
          electricalFTE: e / policy.annualPaidHours,
          hvacFTE: h / policy.annualPaidHours,
        });
      }
      contributors.push({
        id: p.id,
        name: p.name,
        region: p.region,
        basis: p.basis,
        annual: byYear,
      });
    }
    for (const row of annual) {
      row.electricalFTE = row.electricalHours / policy.annualPaidHours;
      row.hvacFTE = row.hvacHours / policy.annualPaidHours;
    }
    const peak = annual.reduce(
      (a, b) => (b.electricalFTE > a.electricalFTE ? b : a),
      annual[0],
    );
    return {
      ...c,
      annual,
      peak,
      contributors,
      allElectricalHours,
      allHvacHours,
      preElectricalHours,
      postElectricalHours,
    };
  });
  return {
    version: 'project-demand-2',
    asOf,
    firstYear,
    years,
    policy,
    proposedRealisation,
    phases,
    excluded,
    scenarios,
    costedCapex: phases.reduce((s, p) => s + p.cost, 0),
    scheduleAnchored: phases.filter((p) => p.start !== null || p.end !== null)
      .length,
    scope: `Proposed-project volume factor ${proposedRealisation}; construction-stage projects retained at 100%. Unknown costs excluded. Volume factors and timing are scenarios, not calibrated probabilities.`,
  };
}
