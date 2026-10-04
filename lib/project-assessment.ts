// Source extension is required by the portable Node strip-types numerical runner.
// @ts-expect-error TS5097: Next bundler and Node resolve this TypeScript source.
import { pairedSchedule } from './construction-model.ts';
import type {
  ResourcePackage,
  ScheduleOptions,
  Trade,
} from './construction-model';

export type AssessmentTrade = Trade | 'Other';
export type AllocationPolicy = ScheduleOptions['policy'];
export type DemandPackage = {
  id: string;
  name: string;
  trade: AssessmentTrade | null;
  catchment: string | null;
  hours: number | null;
  releaseMonth: number | null;
  finishMonth: number | null;
  predecessors: string[];
};
export type OwnerPackage = DemandPackage & {
  scope: AssessmentTrade;
  budgetCAD: number | null;
  uncommittedCAD: number | null;
  commitment: 'unknown' | 'fixed' | 'variable';
  cashMonth: number | null;
};
export type OwnerProject = {
  id: string;
  name: string;
  province: string;
  assetType: string;
  catchment: string | null;
  budgetCAD: number | null;
  plannedFinishMonth: number;
  floatMonths: number;
  overheadCADPerMonth: number | null;
  priceBasisMonth: number;
  supportedContext?: boolean;
};
export type ProjectAssessmentInput = {
  project: OwnerProject;
  packages: OwnerPackage[];
  dcPackages: DemandPackage[];
  backgroundPackages?: DemandPackage[];
  capacity: Record<string, number | null>;
  startMonth: number;
  endMonth: number;
  policy: AllocationPolicy;
  annualEscalation: number | null;
  mitigation: {
    dcShiftMonths: number;
    additionalCapacity: Record<string, number>;
    earlyProcurementMonths: number;
    procurementPackageIds: string[];
    policy?: AllocationPolicy;
  };
  /** Explicit, non-overlapping exposure; these amounts are excluded from escalation. */
  scarcity?: {
    label: string;
    premiumRate: number;
    exposureCADByPackage: Record<string, number>;
  };
  capacityThresholds?: { resourceKey: string; candidates: number[] }[];
  qualitativeLinks?: {
    channel: 'supplier' | 'utility';
    label: string;
    source: string | null;
  }[];
  assumptions: string[];
};

export function calendarMonth(value: string) {
  const match = /^(\d{4})-(\d{2})$/.exec(value);
  if (!match || Number(match[2]) < 1 || Number(match[2]) > 12)
    throw new Error('Use YYYY-MM');
  return Number(match[1]) * 12 + Number(match[2]) - 1;
}

const nonnegative = (n: number | null) =>
  n === null || (Number.isFinite(n) && n >= 0);
const integer = (n: number | null) => n === null || Number.isInteger(n);
const resource = (p: DemandPackage) => `${p.catchment}:${p.trade}`;
const moneyTotal = (values: (number | null)[]) =>
  values.some((v) => v === null)
    ? null
    : values.reduce<number>((sum, v) => sum + v!, 0);

type ScheduleRun = ReturnType<typeof pairedSchedule>['baseline'];
export type AssessmentFinancial = {
  escalationCAD: number | null;
  overheadCAD: number | null;
  scarcityCAD: number | null;
  totalAdditionalCAD: number | null;
  revisedBudgetCAD: number | null;
};
export type AssessmentCase = {
  completionMonth: number | null;
  lateMonths: number | null;
  tailHours: number | null;
  packageResults: {
    id: string;
    completionMonth: number | null;
    delayMonths: number | null;
    remainingHours: number | null;
    escalationCAD: number | null;
    scarcityCAD: number | null;
    cashMonth: number | null;
    exposureCAD: number | null;
  }[];
  financial: AssessmentFinancial;
  schedule: ScheduleRun | null;
};
export type AssessmentImpact = {
  delayMonths: number | null;
  escalationCAD: number | null;
  overheadCAD: number | null;
  scarcityCAD: number | null;
  totalAdditionalCAD: number | null;
};

function validate(input: ProjectAssessmentInput) {
  const { project, mitigation } = input;
  if (
    !project.id ||
    !project.name ||
    !input.packages.length ||
    !Number.isInteger(input.startMonth) ||
    !Number.isInteger(input.endMonth) ||
    input.endMonth <= input.startMonth ||
    !Number.isInteger(project.plannedFinishMonth) ||
    project.plannedFinishMonth < input.startMonth ||
    project.plannedFinishMonth > input.endMonth ||
    !Number.isInteger(project.priceBasisMonth) ||
    !nonnegative(project.budgetCAD) ||
    !nonnegative(project.overheadCADPerMonth) ||
    !Number.isInteger(project.floatMonths) ||
    project.floatMonths < 0 ||
    (input.annualEscalation !== null &&
      (!Number.isFinite(input.annualEscalation) ||
        input.annualEscalation <= -1))
  )
    throw new Error('Invalid owner project, price basis or simulation horizon');
  const policies = ['pro-rata', 'protect-background', 'prefer-dc'];
  if (
    !policies.includes(input.policy) ||
    (mitigation.policy && !policies.includes(mitigation.policy)) ||
    !Number.isInteger(mitigation.dcShiftMonths) ||
    mitigation.dcShiftMonths < 0 ||
    !Number.isInteger(mitigation.earlyProcurementMonths) ||
    mitigation.earlyProcurementMonths < 0
  )
    throw new Error('Invalid mitigation or allocation policy');
  for (const n of [
    ...Object.values(input.capacity),
    ...Object.values(mitigation.additionalCapacity),
  ])
    if (!nonnegative(n))
      throw new Error('Capacity must be non-negative or unknown');
  const all = [
    ...input.packages,
    ...input.dcPackages,
    ...(input.backgroundPackages ?? []),
  ];
  const ids = new Set(all.map((p) => p.id));
  if (ids.size !== all.length)
    throw new Error('Package IDs must be unique across the paired cases');
  const legalTrades = ['Civil', 'Electrical', 'Mechanical', 'Other'];
  for (const p of all) {
    if (
      !p.id ||
      !p.name ||
      !nonnegative(p.hours) ||
      !integer(p.releaseMonth) ||
      !integer(p.finishMonth) ||
      (p.trade !== null && !legalTrades.includes(p.trade)) ||
      (p.releaseMonth !== null && p.releaseMonth < input.startMonth) ||
      (p.releaseMonth !== null &&
        p.finishMonth !== null &&
        p.finishMonth <= p.releaseMonth) ||
      p.predecessors.some((id) => !ids.has(id))
    )
      throw new Error(`Invalid work package: ${p.id}`);
  }
  const baseIds = new Set(
    [...input.packages, ...(input.backgroundPackages ?? [])].map((p) => p.id),
  );
  for (const p of [...input.packages, ...(input.backgroundPackages ?? [])])
    if (p.predecessors.some((id) => !baseIds.has(id)))
      throw new Error('Background work cannot depend on incremental DC work');
  for (const p of input.packages) {
    if (
      !legalTrades.includes(p.scope) ||
      !['unknown', 'fixed', 'variable'].includes(p.commitment) ||
      !nonnegative(p.budgetCAD) ||
      !nonnegative(p.uncommittedCAD) ||
      !integer(p.cashMonth) ||
      (p.budgetCAD !== null &&
        p.uncommittedCAD !== null &&
        p.uncommittedCAD > p.budgetCAD) ||
      (p.commitment === 'fixed' && (p.uncommittedCAD ?? 0) > 0)
    )
      throw new Error(`Invalid budget or commitment exposure: ${p.id}`);
  }
  const knownExposure = input.packages.reduce(
    (sum, p) => sum + (p.uncommittedCAD ?? 0),
    0,
  );
  if (project.budgetCAD !== null && knownExposure > project.budgetCAD + 0.01)
    throw new Error(
      'Remaining package exposure exceeds the owner project budget',
    );
  const namedBudget = input.packages.reduce(
    (sum, p) => sum + (p.budgetCAD ?? 0),
    0,
  );
  if (project.budgetCAD !== null && namedBudget > project.budgetCAD + 0.01)
    throw new Error('Package budgets exceed the owner project budget');
  const ownerIds = new Set(input.packages.map((p) => p.id));
  if (mitigation.procurementPackageIds.some((id) => !ownerIds.has(id)))
    throw new Error('Early procurement must identify owner packages');
  if (input.scarcity) {
    if (
      !input.scarcity.label.trim() ||
      !nonnegative(input.scarcity.premiumRate)
    )
      throw new Error(
        'Scarcity premium requires an explicit assumption label and non-negative rate',
      );
    for (const [id, amount] of Object.entries(
      input.scarcity.exposureCADByPackage,
    )) {
      const p = input.packages.find((p) => p.id === id);
      if (
        !p ||
        p.commitment !== 'variable' ||
        p.uncommittedCAD === null ||
        !nonnegative(amount) ||
        amount > p.uncommittedCAD
      )
        throw new Error(
          'Scarcity exposure must be a disjoint subset of explicit variable exposure',
        );
    }
  }
  for (const grid of input.capacityThresholds ?? [])
    if (
      !grid.resourceKey ||
      !grid.candidates.length ||
      grid.candidates.length > 100 ||
      grid.candidates.some((n) => !Number.isFinite(n) || n < 0)
    )
      throw new Error('Invalid normalized capacity grid');
  // Check cycles even for incomplete packages, before deciding whether numeric use is possible.
  const visiting = new Set<string>(),
    visited = new Set<string>();
  const visit = (id: string) => {
    if (visiting.has(id)) throw new Error('Cyclic package precedence');
    if (visited.has(id)) return;
    visiting.add(id);
    all.find((p) => p.id === id)!.predecessors.forEach(visit);
    visiting.delete(id);
    visited.add(id);
  };
  all.forEach((p) => visit(p.id));
}

function resultCase(
  input: ProjectAssessmentInput,
  schedule: ScheduleRun | null,
  variant: 'baseline' | 'withDC' | 'mitigation',
  quantitative: boolean,
): AssessmentCase {
  const owners = input.packages.map((p) => {
    const actual = schedule?.packages.find((a) => a.id === p.id);
    const completionMonth = quantitative
      ? (actual?.completionMonth ?? null)
      : null;
    const delayMonths =
      p.hours === 0 && quantitative
        ? 0
        : completionMonth === null || p.finishMonth === null
          ? null
          : Math.max(0, completionMonth - p.finishMonth);
    const exposureCAD =
      p.commitment === 'fixed'
        ? 0
        : p.commitment === 'variable'
          ? p.uncommittedCAD
          : null;
    const scarcityExposure = input.scarcity?.exposureCADByPackage[p.id] ?? 0;
    const cashMonth =
      p.cashMonth === null || delayMonths === null
        ? null
        : p.cashMonth +
          delayMonths -
          (variant === 'mitigation' &&
          input.mitigation.procurementPackageIds.includes(p.id)
            ? input.mitigation.earlyProcurementMonths
            : 0);
    let escalationCAD: number | null = null;
    if (quantitative && completionMonth !== null && exposureCAD !== null) {
      if (exposureCAD === 0 || exposureCAD === scarcityExposure)
        escalationCAD = 0;
      else if (cashMonth !== null && input.annualEscalation !== null)
        escalationCAD =
          (exposureCAD - scarcityExposure) *
          ((1 + input.annualEscalation) **
            ((cashMonth - input.project.priceBasisMonth) / 12) -
            1);
    }
    const scarcityCAD =
      quantitative && completionMonth !== null
        ? variant === 'baseline' ||
          !schedule?.packages.some(
            (work) => work.kind === 'dc' && work.hours > 0,
          )
          ? 0
          : scarcityExposure * (input.scarcity?.premiumRate ?? 0)
        : null;
    return {
      id: p.id,
      completionMonth,
      delayMonths,
      remainingHours: quantitative ? (actual?.remainingHours ?? null) : null,
      escalationCAD,
      scarcityCAD,
      cashMonth,
      exposureCAD,
    };
  });
  const milestonePackages = owners.filter(
    (p) => input.packages.find((source) => source.id === p.id)!.hours !== 0,
  );
  const maxShift =
    !quantitative || milestonePackages.some((p) => p.completionMonth === null)
      ? null
      : milestonePackages.length === 0
        ? 0
        : Math.max(
            0,
            Math.max(...milestonePackages.map((p) => p.completionMonth!)) -
              Math.max(
                ...input.packages
                  .filter((p) => p.hours !== 0)
                  .map((p) => p.finishMonth!),
              ),
          );
  const lateMonths =
    maxShift === null
      ? null
      : Math.max(0, maxShift - input.project.floatMonths);
  const completionMonth =
    lateMonths === null ? null : input.project.plannedFinishMonth + lateMonths;
  const escalationCAD = moneyTotal(owners.map((p) => p.escalationCAD));
  const scarcityCAD = moneyTotal(owners.map((p) => p.scarcityCAD));
  const overheadCAD =
    lateMonths === null || input.project.overheadCADPerMonth === null
      ? null
      : lateMonths * input.project.overheadCADPerMonth;
  const totalAdditionalCAD = moneyTotal([
    escalationCAD,
    scarcityCAD,
    overheadCAD,
  ]);
  return {
    completionMonth,
    lateMonths,
    tailHours: quantitative ? (schedule?.tailHours ?? null) : null,
    packageResults: owners,
    financial: {
      escalationCAD,
      overheadCAD,
      scarcityCAD,
      totalAdditionalCAD,
      revisedBudgetCAD:
        input.project.budgetCAD === null || totalAdditionalCAD === null
          ? null
          : input.project.budgetCAD + totalAdditionalCAD,
    },
    schedule,
  };
}

export function assessProject(input: ProjectAssessmentInput) {
  validate(input);
  const inputs = structuredClone(input);
  const unknowns: string[] = [];
  const supported =
    input.project.province === 'Alberta' &&
    input.project.supportedContext !== false &&
    ['school', 'hospital', 'government'].includes(input.project.assetType);
  if (!supported)
    unknowns.push(
      'The supported conditional assessment domain is Alberta; this context receives qualitative pathways only.',
    );
  const all = [
    ...input.packages,
    ...input.dcPackages,
    ...(input.backgroundPackages ?? []),
  ];
  const complete = all.every(
    (p) =>
      p.hours === 0 ||
      (p.trade !== null &&
        p.catchment !== null &&
        p.catchment.trim() &&
        p.hours !== null &&
        p.releaseMonth !== null &&
        p.finishMonth !== null),
  );
  if (!complete)
    unknowns.push(
      'Enter explicit trade, catchment, paid hours and monthly work windows for every included package; budgets never generate quantities.',
    );
  const matches = input.packages.flatMap((owner) =>
    input.dcPackages.flatMap((dc) => {
      if (
        owner.catchment === null ||
        dc.catchment === null ||
        owner.trade === null ||
        dc.trade === null ||
        owner.catchment !== dc.catchment ||
        owner.trade !== dc.trade ||
        owner.releaseMonth === null ||
        owner.finishMonth === null ||
        dc.releaseMonth === null ||
        dc.finishMonth === null
      )
        return [];
      const overlapMonths = Math.max(
        0,
        Math.min(owner.finishMonth, dc.finishMonth) -
          Math.max(owner.releaseMonth, dc.releaseMonth),
      );
      return overlapMonths > 0
        ? [{ ownerPackageId: owner.id, dcPackageId: dc.id, overlapMonths }]
        : [];
    }),
  );
  // Planned overlap is a diagnostic. Earlier work can carry a backlog into a later
  // owner window, and competition can delay a background predecessor indirectly.
  const baselineWork = [...input.packages, ...(input.backgroundPackages ?? [])];
  const includedDCIds = new Set(
    input.dcPackages
      .filter((dc) =>
        baselineWork.some(
          (base) =>
            dc.catchment !== null &&
            dc.trade !== null &&
            base.catchment === dc.catchment &&
            base.trade === dc.trade,
        ),
      )
      .map((dc) => dc.id),
  );
  const addPredecessors = (id: string) => {
    for (const predecessor of input.dcPackages.find((p) => p.id === id)
      ?.predecessors ?? [])
      if (
        input.dcPackages.some((p) => p.id === predecessor) &&
        !includedDCIds.has(predecessor)
      ) {
        includedDCIds.add(predecessor);
        addPredecessors(predecessor);
      }
  };
  [...includedDCIds].forEach(addPredecessors);
  const included = [
    ...input.packages,
    ...(input.backgroundPackages ?? []),
    ...input.dcPackages.filter((p) => includedDCIds.has(p.id)),
  ];
  const convert = (p: DemandPackage): ResourcePackage => ({
    id: p.id,
    region: p.catchment ?? 'inactive-explicit-zero-hours',
    trade: (p.trade ?? 'Other') as Trade,
    kind: input.dcPackages.some((dc) => dc.id === p.id) ? 'dc' : 'background',
    hours: p.hours!,
    releaseMonth: p.releaseMonth ?? input.startMonth,
    plannedFinishMonth: p.finishMonth ?? input.startMonth + 1,
    predecessors: [...p.predecessors],
  });
  const available =
    complete &&
    included.every(
      (p) =>
        p.hours === 0 ||
        (input.capacity[resource(p)] !== undefined &&
          input.capacity[resource(p)] !== null),
    );
  if (!available)
    unknowns.push(
      'Actual deployable capacity is unknown for one or more included resources; any numeric capacity entry is a stated scenario assumption.',
    );
  for (const p of input.packages)
    if (
      p.commitment === 'unknown' ||
      (p.uncommittedCAD === null && p.commitment !== 'fixed')
    )
      unknowns.push(`Remaining repricing exposure is unknown for ${p.name}.`);
  if (input.project.overheadCADPerMonth === null)
    unknowns.push(
      'Separately incremental project overhead is unknown; no full financial total can be claimed.',
    );
  const scheduleOptions: ScheduleOptions = {
    startMonth: input.startMonth,
    endMonth: input.endMonth,
    capacity: { ...input.capacity },
    policy: input.policy,
    annualEscalation: input.annualEscalation ?? 0,
  };
  const canSchedule = supported && complete;
  const pair = canSchedule
    ? pairedSchedule(included.map(convert), scheduleOptions)
    : null;
  const shifted = included.map((p) => {
    const converted = convert(p);
    return converted.kind === 'dc'
      ? {
          ...converted,
          releaseMonth: converted.releaseMonth + input.mitigation.dcShiftMonths,
          plannedFinishMonth:
            converted.plannedFinishMonth + input.mitigation.dcShiftMonths,
        }
      : converted;
  });
  const actionCapacity = Object.fromEntries(
    Object.entries(input.capacity).map(([key, cap]) => [
      key,
      cap === null
        ? null
        : cap + (input.mitigation.additionalCapacity[key] ?? 0),
    ]),
  );
  // Missing supply cannot be made numeric by adding an assumed recruitment increment.
  const action = canSchedule
    ? pairedSchedule(shifted, {
        ...scheduleOptions,
        policy: input.mitigation.policy ?? input.policy,
        capacity: actionCapacity,
      })
    : null;
  const baseline = resultCase(
    input,
    pair?.baseline ?? null,
    'baseline',
    supported && available,
  );
  const withDC = resultCase(
    input,
    pair?.withDC ?? null,
    'withDC',
    supported && available,
  );
  const mitigation = resultCase(
    input,
    action?.withDC ?? null,
    'mitigation',
    supported && available,
  );
  const noIncrementalDC =
    !input.dcPackages.some((p) => p.hours !== 0) ||
    (complete && includedDCIds.size === 0);
  const subtract = (a: number | null, b: number | null) =>
    a === null || b === null ? null : a - b;
  const impact = (
    scenario: AssessmentCase,
    zero: boolean,
  ): AssessmentImpact => ({
    delayMonths:
      zero && supported
        ? 0
        : subtract(scenario.completionMonth, baseline.completionMonth),
    escalationCAD:
      zero && supported
        ? 0
        : subtract(
            scenario.financial.escalationCAD,
            baseline.financial.escalationCAD,
          ),
    overheadCAD:
      zero && supported
        ? 0
        : subtract(
            scenario.financial.overheadCAD,
            baseline.financial.overheadCAD,
          ),
    scarcityCAD:
      zero && supported
        ? 0
        : subtract(
            scenario.financial.scarcityCAD,
            baseline.financial.scarcityCAD,
          ),
    totalAdditionalCAD:
      zero && supported
        ? 0
        : subtract(
            scenario.financial.totalAdditionalCAD,
            baseline.financial.totalAdditionalCAD,
          ),
  });
  const noAction =
    input.mitigation.dcShiftMonths === 0 &&
    input.mitigation.earlyProcurementMonths === 0 &&
    !Object.values(input.mitigation.additionalCapacity).some((n) => n > 0) &&
    (!input.mitigation.policy || input.mitigation.policy === input.policy);
  const thresholds = (input.capacityThresholds ?? []).map((grid) => {
    const cases = [...new Set(grid.candidates)]
      .sort((a, b) => a - b)
      .map((capacityHours) => {
        const options = {
          ...scheduleOptions,
          capacity: { ...input.capacity, [grid.resourceKey]: capacityHours },
        };
        const gridAvailable =
          complete &&
          included.every(
            (p) =>
              p.hours === 0 ||
              (options.capacity[resource(p)] !== undefined &&
                options.capacity[resource(p)] !== null),
          );
        const run = canSchedule
          ? pairedSchedule(included.map(convert), options)
          : null;
        const computed = resultCase(
          input,
          run?.withDC ?? null,
          'withDC',
          supported && gridAvailable,
        );
        return {
          capacityHours,
          completionMonth: computed.completionMonth,
          targetMet:
            supported && gridAvailable
              ? computed.completionMonth !== null &&
                computed.completionMonth <= input.project.plannedFinishMonth
              : null,
          tailHours: computed.tailHours,
        };
      });
    const first = cases.find((c) => c.targetMet === true);
    return {
      resourceKey: grid.resourceKey,
      cases,
      minimumTestedCapacityHours: first?.capacityHours ?? null,
      qualification:
        'Minimum successful total capacity in the entered discrete grid; assumed paid hours per month, not measured spare capacity or a continuous optimum.',
    };
  });
  return {
    version: 'project-assessment-0.1',
    inputs,
    qualified:
      supported && complete && available
        ? ('conditional' as const)
        : ('qualitative' as const),
    unknowns,
    matches,
    qualitativeLinks: inputs.qualitativeLinks ?? [],
    cases: { baseline, withDC, mitigation },
    impacts: {
      withDC: impact(withDC, noIncrementalDC),
      mitigation: impact(mitigation, noIncrementalDC && noAction),
    },
    capacityThresholds: thresholds,
    assumptionChain: [
      'Owner and DC paid hours, catchments, trades and work windows are explicit inputs, never inferred from investment or operating MW.',
      'Direct planned overlap requires the same entered catchment and trade and intersecting work windows. Shared-pool packages are retained for backlog and predecessor effects; the resource schedule determines actual intersection. Ancestors preserve package precedence.',
      'Both paired cases retain the same background, paid-hour basis, price basis, capacity and allocation policy. Mitigation changes only its recorded actions.',
      'Project completion is the entered milestone plus the shift of the latest actual owner-package finish relative to the latest planned owner-package finish, after subtracting project float once. Unfinished packages retain hours and withhold completion.',
      'Package escalation applies only to explicit variable uncommitted exposure at shifted cash dates; fixed commitments do not automatically reprice.',
      'Project overhead is priced once against project milestone lateness, never summed across overlapping packages. Enter overhead net of package budgets and exposure.',
      'An optional labelled scarcity sensitivity consumes a disjoint subset of exposure excluded from escalation; it is never inferred from demand/capacity or compounded with escalation.',
      'Supplier and utility links remain qualitative independent constraints, never labour shortage percentages or automatic cost additions.',
      'Conditional scenario arithmetic is not observed delay, a calibrated AI premium, probabilities or authorization to publish empirical claims.',
      ...inputs.assumptions,
    ],
  };
}
