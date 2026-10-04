export type Trade = 'Civil' | 'Electrical' | 'Mechanical';
export const trades: Trade[] = ['Civil', 'Electrical', 'Mechanical'];
export type Project = {
  id: string;
  name: string;
  region: string;
  stage: string;
  cost: number | null;
  start: number | null;
  end: number | null;
  source: string;
  asOf: string;
};
export type Selection = { included: boolean; cost: number; online: number };
export type Options = {
  years: number;
  duration: number;
  cohortYears: number;
  growth: number;
  inflation: number;
  constructionShare: number;
  publicShare: number;
  hoursFactor: number;
  annualHours: number;
  shares: number[];
  labour: number[];
  wages: number[];
  capacity: (number | null)[];
  privateHours?: number[];
};
export const defaults: Options = {
  years: 5,
  duration: 24,
  cohortYears: 4,
  growth: 0,
  inflation: 0.025,
  constructionShare: 0.5,
  publicShare: 0.7,
  hoursFactor: 1,
  annualHours: 1840,
  shares: [0.2, 0.45, 0.35],
  labour: [0.35, 0.25, 0.3],
  wages: [85, 105, 100],
  capacity: [null, null, null],
  privateHours: [0, 0, 0],
};
export const formulas = [
  [
    'F01',
    'Quantity estimate',
    'Paid hours = quantity × paid hours/unit × incremental conditions',
    'Authorized item rates required; normal handling allowances are already included.',
  ],
  [
    'F02',
    'Preliminary cost estimate',
    'Trade hours = scoped construction cost × package share × labour fraction ÷ loaded hourly cost × conditions',
    'Active route in this workspace. Shares and loaded rates are editable analyst assumptions.',
  ],
  [
    'F03',
    'Quarterly FTE',
    'Average FTE = quarterly paid hours ÷ (annual paid hours / 4)',
    'Average equivalent workforce, not peak workers or permanent operating jobs.',
  ],
  [
    'F04',
    'Recurring capital',
    'Annual cash = sum of active cohort commitments × annual cohort weight',
    'Published cash envelopes include named projects. They are not added again. Pre-horizon cohorts are initialized.',
  ],
  [
    'F05',
    'Conditional pressure',
    'Ratio = (background hours + DC hours) ÷ total available hours',
    'Capacity is unknown until entered. Private competing paid hours are an explicit annual scenario input; zero means omitted, not observed absence.',
  ],
  [
    'F06',
    'Conditional gap',
    'Unmet hours = max(0, total demand − total capacity)',
    'Demand screening only; this is not a calculated project delay.',
  ],
  [
    'F07',
    'Procurement',
    'Schedule exposure = max(0, lead weeks − weeks until required)',
    'Product-specific scenario; confirm order-release basis, logistics and package float.',
  ],
  [
    'F08',
    'Exposed-cost delay',
    'Additional escalation = uncommitted cost × ((1 + annual rate)^(delay months / 12) − 1)',
    'User-entered delay illustration. No shortage-to-delay or scarcity-price coefficient is inferred.',
  ],
  [
    'F09',
    'Efficiency loss',
    'Required hours multiplier = 1 / (1 − efficiency loss)',
    'Do not stack overlapping overtime, weather and normal estimating allowances.',
  ],
  [
    'F10',
    'Monthly package allocation',
    'Month hours = package hours × overlapping fraction of the package window',
    'Assumed uniform windows as fractions of field duration: civil 0–50%, electrical 25–100%, mechanical 30–100%. These overlap and include late commissioning effort; they are not observed schedules.',
  ],
];
const month = (year: number, offset = 0) => year * 12 + offset;
export function publicAnnual(year: number, o: Options) {
  const budget: Record<number, number> = {
    2026: 10687e6,
    2027: 9998e6,
    2028: 8349e6,
  };
  // FY April–March amounts: retain each published nominal vintage. Tail grows in real terms plus explicit price inflation.
  return (
    budget[year] ??
    (year < 2026
      ? budget[2026]
      : budget[2028] * ((1 + o.growth) * (1 + o.inflation)) ** (year - 2028))
  );
}
export function escalation(cost: number, annual: number, months: number) {
  if (
    ![cost, annual, months].every(Number.isFinite) ||
    cost < 0 ||
    annual <= -1 ||
    months < 0
  )
    throw new Error('Invalid escalation inputs');
  return cost * ((1 + annual) ** (months / 12) - 1);
}
export function calculate(
  projects: Project[],
  selected: Record<string, Selection>,
  o: Options,
) {
  const numeric = [
    o.years,
    o.duration,
    o.cohortYears,
    o.growth,
    o.inflation,
    o.constructionShare,
    o.publicShare,
    o.hoursFactor,
    o.annualHours,
    ...o.shares,
    ...o.labour,
    ...o.wages,
  ];
  if (
    !numeric.every(Number.isFinite) ||
    [o.shares, o.labour, o.wages, o.capacity, o.privateHours ?? [0, 0, 0]].some((values) => values.length !== 3) ||
    ![3, 5, 10].includes(o.years) ||
    o.duration < 1 ||
    ![4, 5].includes(o.cohortYears) ||
    o.annualHours <= 0 ||
    o.hoursFactor <= 0 ||
    o.wages.some((x) => x <= 0) ||
    o.growth <= -1 ||
    o.inflation <= -1 ||
    [o.constructionShare, o.publicShare, ...o.shares, ...o.labour].some(
      (x) => x < 0 || x > 1,
    ) ||
    Math.abs(o.shares.reduce((a, b) => a + b, 0) - 1) > 0.00001 ||
    (o.privateHours ?? [0, 0, 0]).some((x) => !Number.isFinite(x) || x < 0) ||
    o.capacity.some((x) => x !== null && (!Number.isFinite(x) || x < 0))
  )
    throw new Error(
      'Check shares (must total 100%), positive wages, durations and capacity.',
    );
  const phases = projects
    .filter((p) => selected[p.id]?.included)
    .map((p) => {
      const s = selected[p.id];
      if (
        !Number.isFinite(s.cost) ||
        s.cost <= 0 ||
        !Number.isInteger(s.online) ||
        s.online < 2020 ||
        s.online > 2050
      )
        throw new Error(
          'Included phases need positive cost and an online year between 2020 and 2050.',
        );
      const reportedEnd = p.end === s.online;
      let end = month(s.online, 6);
      let start = p.start !== null ? month(p.start) : end - o.duration;
      let basis =
        p.start !== null
          ? reportedEnd
            ? 'Reported years; Jan start / July finish convention'
            : 'Reported start year; assumed online year, Jan start / July finish convention'
          : 'Inferred from July online midpoint and assumed duration';
      if (end <= start) throw new Error('A phase must finish after its start.');
      if (p.stage !== 'Under Construction' && start < month(2026, 8)) {
        const duration = end - start;
        start = month(2026, 8);
        end = start + duration;
        basis += '; infeasible past proposal start shifted to September 2026';
      }
      const hours = trades.map(
        (_, i) =>
          ((s.cost * o.constructionShare * o.shares[i] * o.labour[i]) /
            o.wages[i]) *
          o.hoursFactor,
      );
      return {
        ...p,
        scenarioCost: s.cost,
        startMonth: start,
        endMonth: end,
        basis,
        hours,
      };
    });
  // A constant-duration cohort model calibrated exactly to each FY cash envelope.
  // Initialize D−1 prior commitments; new commitments solve the remaining envelope.
  const cohorts: { year: number; commitment: number }[] = [];
  for (let y = 2026 - o.cohortYears + 1; y < 2026; y++)
    cohorts.push({ year: y, commitment: publicAnnual(2026, o) });
  for (let y = 2026; y <= 2027 + o.years; y++) {
    const active = cohorts
      .filter((c) => c.year > y - o.cohortYears)
      .reduce((s, c) => s + c.commitment / o.cohortYears, 0);
    cohorts.push({
      year: y,
      commitment: (publicAnnual(y, o) - active) * o.cohortYears,
    });
  }
  const invalidCohorts = cohorts.some((c) => c.commitment < 0);
  const rows = [];
  const packages: ResourcePackage[] = [];
  let totalHours = 0;
  const windows: [number, number][] = [
    [0, 0.5],
    [0.25, 1],
    [0.3, 1],
  ];
  for (let y = 2027; y < 2027 + o.years; y++)
    for (let q = 0; q < 4; q++)
      for (let i = 0; i < 3; i++) {
        let dc = 0,
          background = 0;
        for (let m = month(y, q * 3); m < month(y, q * 3 + 3); m++) {
          const fy = Math.floor(m / 12) - (m % 12 < 3 ? 1 : 0);
          background +=
            (((publicAnnual(fy, o) / 12) *
              o.publicShare *
              o.shares[i] *
              o.labour[i]) /
              o.wages[i]) *
            o.hoursFactor;
          for (const p of phases) {
            const a =
                p.startMonth + (p.endMonth - p.startMonth) * windows[i][0],
              b = p.startMonth + (p.endMonth - p.startMonth) * windows[i][1];
            dc +=
              (p.hours[i] * Math.max(0, Math.min(m + 1, b) - Math.max(m, a))) /
              (b - a);
          }
        }
        const privateHours = (o.privateHours?.[i] ?? 0) / 4;
        background += privateHours;
        totalHours += dc;
        const cap =
          o.capacity[i] === null ? null : (o.capacity[i]! * o.annualHours) / 4;
        rows.push({
          quarter: `${y} Q${q + 1}`,
          trade: trades[i],
          dcHours: dc,
          publicHours: background - privateHours,
          privateHours,
          dcFte: dc / (o.annualHours / 4),
          capacityHours: cap,
          ratio: cap === null || cap === 0 ? null : (dc + background) / cap,
          gap: cap === null ? null : Math.max(0, dc + background - cap),
        });
      }
  // Named public outcomes need package take-offs before assigning owner cost exposure.
  // Anonymous envelope tasks represent competing work, never additional commitments.
  const firstMonth = Math.min(month(2026, 8), ...phases.map((p) => p.startMonth));
  const finalMonth = Math.max(month(2027 + o.years), ...phases.map((p) => p.endMonth));
  for (let m = firstMonth; m < finalMonth; m++) {
    const fy = Math.floor(m / 12) - (m % 12 < 3 ? 1 : 0);
    for (let i = 0; i < 3; i++) packages.push({
      id: `background:${m}:${i}`, region: 'Alberta', trade: trades[i], kind: 'background',
      releaseMonth: m, plannedFinishMonth: m + 1, predecessors: [],
      hours: publicAnnual(fy, o) / 12 * o.publicShare * o.shares[i] * o.labour[i] / o.wages[i] * o.hoursFactor + (o.privateHours?.[i] ?? 0) / 12,
    });
  }
  for (const p of phases) for (let i = 0; i < 3; i++) packages.push({
    id: `${p.id}:${i}`, region: 'Alberta', trade: trades[i], kind: 'dc', hours: p.hours[i],
    releaseMonth: Math.ceil(p.startMonth + (p.endMonth - p.startMonth) * windows[i][0]),
    plannedFinishMonth: Math.ceil(p.startMonth + (p.endMonth - p.startMonth) * windows[i][1]),
    predecessors: i === 0 ? [] : [`${p.id}:0`],
  });
  const scheduling = pairedSchedule(packages, {
    startMonth: firstMonth, endMonth: finalMonth + 120,
    capacity: Object.fromEntries(trades.map((t, i) => [`Alberta:${t}`, o.capacity[i] === null ? null : o.capacity[i]! * o.annualHours / 12])),
    policy: 'pro-rata', annualEscalation: o.inflation,
  });
  return {
    version: 'construction-0.2',
    scheduling,
    options: o,
    phases,
    rows,
    cohorts,
    invalidCohorts,
    totalHours,
    jobYears: totalHours / o.annualHours,
    outsideWindowHours:
      phases.reduce((s, p) => s + p.hours.reduce((a, b) => a + b, 0), 0) -
      totalHours,
    scope:
      'Uncalibrated Alberta paired public-envelope + explicit private-demand + selected DC scenario; capacity assumptions and enabling-work precedence are conditional; no causal forecast',
  };
}

export type ResourcePackage = {
  id: string; region: string; trade: Trade; kind: 'background' | 'dc';
  hours: number; releaseMonth: number; plannedFinishMonth: number;
  predecessors: string[];
  // Only explicitly uncommitted, remaining package costs may reprice.
  uncommittedExposureCAD?: number;
  incrementalSiteOverheadCADPerMonth?: number;
};
export type ScheduleOptions = {
  startMonth: number; endMonth: number;
  capacity: Record<string, number | null>;
  monthlyCapacity?: Record<string, Record<number, number | null>>;
  policy: 'pro-rata' | 'protect-background' | 'prefer-dc';
  annualEscalation: number;
};
export function schedulePackages(packages: ResourcePackage[], options: ScheduleOptions) {
  const ids = new Set(packages.map((p) => p.id));
  if (ids.size !== packages.length || !Number.isInteger(options.startMonth) || !Number.isInteger(options.endMonth) || options.endMonth <= options.startMonth || !Number.isFinite(options.annualEscalation) || options.annualEscalation <= -1 || !['pro-rata', 'protect-background', 'prefer-dc'].includes(options.policy)) throw new Error('Invalid schedule contract');
  for (const p of packages) {
    if (![p.hours, p.releaseMonth, p.plannedFinishMonth, p.uncommittedExposureCAD ?? 0, p.incrementalSiteOverheadCADPerMonth ?? 0].every(Number.isFinite) || p.hours < 0 || (p.uncommittedExposureCAD ?? 0) < 0 || (p.incrementalSiteOverheadCADPerMonth ?? 0) < 0 || !Number.isInteger(p.releaseMonth) || !Number.isInteger(p.plannedFinishMonth) || p.releaseMonth < options.startMonth || p.plannedFinishMonth <= p.releaseMonth || p.predecessors.some((id) => !ids.has(id))) throw new Error('Invalid resource package');
  }
  const visiting = new Set<string>(), visited = new Set<string>();
  const visit = (id: string) => {
    if (visiting.has(id)) throw new Error('Cyclic package precedence');
    if (visited.has(id)) return;
    visiting.add(id);
    for (const predecessor of packages.find((p) => p.id === id)!.predecessors) visit(predecessor);
    visiting.delete(id); visited.add(id);
  };
  packages.forEach((p) => visit(p.id));
  for (const cap of Object.values(options.capacity)) if (cap !== null && (!Number.isFinite(cap) || cap < 0)) throw new Error('Invalid monthly capacity');
  for (const series of Object.values(options.monthlyCapacity ?? {})) for (const cap of Object.values(series)) if (cap !== null && (!Number.isFinite(cap) || cap < 0)) throw new Error('Invalid monthly capacity trajectory');
  const state = packages.map((p) => ({ ...p, remainingHours: p.hours, servedHours: 0, completionMonth: null as number | null }));
  const allocations: { month: number; packageId: string; region: string; trade: Trade; hours: number }[] = [];
  const monthly: { month: number; resource: string; capacityHours: number | null; allocatedHours: number | null; backlogHours: number | null }[] = [];
  for (let m = options.startMonth; m < options.endMonth; m++) {
    for (const p of state) if (p.hours === 0 && p.releaseMonth <= m && p.completionMonth === null && p.predecessors.every((id) => { const previous = state.find((x) => x.id === id)!; return previous.completionMonth !== null && previous.completionMonth <= m; })) p.completionMonth = m;
    const active = state.filter((p) => p.releaseMonth <= m && p.remainingHours > 1e-8 && p.predecessors.every((id) => {
      const predecessor = state.find((x) => x.id === id)!;
      return predecessor.completionMonth !== null && predecessor.completionMonth <= m;
    }));
    for (const resource of new Set(state.map((p) => `${p.region}:${p.trade}`))) {
      const trajectory = options.monthlyCapacity?.[resource];
      const cap = trajectory && Object.hasOwn(trajectory, m) ? trajectory[m] : (options.capacity[resource] ?? null);
      const candidates = active.filter((p) => `${p.region}:${p.trade}` === resource);
      let available = cap ?? 0, used = 0;
      const tiers = options.policy === 'pro-rata' ? [candidates] : [
        candidates.filter((p) => p.kind === (options.policy === 'protect-background' ? 'background' : 'dc')),
        candidates.filter((p) => p.kind !== (options.policy === 'protect-background' ? 'background' : 'dc')),
      ];
      for (const tier of tiers) {
        const requests = tier.map((p) => p.remainingHours / Math.max(1, p.plannedFinishMonth - m));
        const total = requests.reduce((a, b) => a + b, 0);
        const factor = total === 0 ? 0 : Math.min(1, available / total);
        tier.forEach((p, i) => {
          const served = requests[i] * factor;
          p.remainingHours = Math.max(0, p.remainingHours - served); p.servedHours += served;
          available -= served; used += served;
          if (served > 0) allocations.push({ month: m, packageId: p.id, region: p.region, trade: p.trade, hours: served });
          if (p.remainingHours < 1e-8) { p.remainingHours = 0; p.completionMonth = m + 1; }
        });
      }
      monthly.push({ month: m, resource, capacityHours: cap, allocatedHours: cap === null ? null : used,
        backlogHours: cap === null ? null : state.filter((p) => `${p.region}:${p.trade}` === resource && p.releaseMonth <= m).reduce((sum, p) => sum + p.remainingHours, 0) });
    }
  }
  return { packages: state.map((p) => {
    const delayMonths = p.completionMonth === null ? null : Math.max(0, p.completionMonth - p.plannedFinishMonth);
    return { ...p, delayMonths, escalationCAD: delayMonths === null || p.uncommittedExposureCAD === undefined ? null : escalation(p.uncommittedExposureCAD, options.annualEscalation, delayMonths),
      siteOverheadCAD: delayMonths === null || p.incrementalSiteOverheadCADPerMonth === undefined ? null : delayMonths * p.incrementalSiteOverheadCADPerMonth };
  }), allocations, monthly, tailHours: state.reduce((sum, p) => sum + p.remainingHours, 0),
    qualification: 'Uncalibrated monthly resource scenario; missing capacity leaves completion and costs unknown. Unfinished hours remain in the horizon tail.' };
}
export function pairedSchedule(packages: ResourcePackage[], options: ScheduleOptions) {
  const baseline = schedulePackages(packages.filter((p) => p.kind === 'background'), options);
  const withDC = schedulePackages(packages, options);
  const zeroDC = !packages.some((p) => p.kind === 'dc' && p.hours > 0);
  const impacts = baseline.packages.map((base) => {
    const added = withDC.packages.find((p) => p.id === base.id)!;
    return { packageId: base.id,
      incrementalDelayMonths: zeroDC ? 0 : base.completionMonth === null || added.completionMonth === null ? null : added.completionMonth - base.completionMonth,
      incrementalEscalationCAD: zeroDC ? 0 : base.escalationCAD === null || added.escalationCAD === null ? null : added.escalationCAD - base.escalationCAD,
      incrementalSiteOverheadCAD: zeroDC ? 0 : base.siteOverheadCAD === null || added.siteOverheadCAD === null ? null : added.siteOverheadCAD - base.siteOverheadCAD };
  });
  return { options, baseline, withDC, impacts };
}
