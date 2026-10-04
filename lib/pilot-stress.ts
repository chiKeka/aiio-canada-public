// Explicit extension supports the existing Node strip-types numerical test runner.
// @ts-expect-error TS5097: Next's bundler and Node strip-types resolve this source module.
import { pairedSchedule } from './construction-model.ts';
import type { ResourcePackage, ScheduleOptions } from './construction-model';

export type PilotStressInput = {
  packages: ResourcePackage[];
  schedule: ScheduleOptions;
  protectedPackageId: string;
  protectedFinishMonth: number;
  resourceKey: string;
  /** Scenario totals, never an estimate of measured spare workforce. null stays unknown. */
  capacityCandidates: (number | null)[];
  /** Common discrete shift of incremental AI packages, preserving duration and hours. */
  dcReleaseOffsetsMonths: number[];
  privateBackgroundPackageIds?: string[];
  privateBackgroundMultipliers?: number[];
  /** Additional assumed mobility supply, on the same paid-hour basis. */
  mobilityCapacityHours?: number[];
  policies?: ScheduleOptions['policy'][];
  hoursBasis: {
    unit: 'normalized-paid-hours';
    /** Null when no empirical mapping to actual paid hours exists. */
    paidHoursPerUnit: number | null;
    assumption: string;
  };
};

/** Exhaustive reverse stress over the supplied discrete grid; no monotonicity assumed. */
export function reverseStress(input: PilotStressInput) {
  const protectedPackage = input.packages.find(
    (p) => p.id === input.protectedPackageId,
  );
  if (!protectedPackage || protectedPackage.kind !== 'background')
    throw new Error('Protected package must be named background work');
  if (
    !Number.isInteger(input.protectedFinishMonth) ||
    input.protectedFinishMonth <= input.schedule.startMonth ||
    input.protectedFinishMonth > input.schedule.endMonth
  )
    throw new Error('Protected target must fall inside the simulated horizon');
  if (
    !input.packages.some((p) => `${p.region}:${p.trade}` === input.resourceKey)
  )
    throw new Error('Stress resource must exist in the package contract');
  if (
    input.hoursBasis.unit !== 'normalized-paid-hours' ||
    !input.hoursBasis.assumption.trim() ||
    (input.hoursBasis.paidHoursPerUnit !== null &&
      (!Number.isFinite(input.hoursBasis.paidHoursPerUnit) ||
        input.hoursBasis.paidHoursPerUnit <= 0))
  )
    throw new Error('An explicit normalized paid-hour assumption is required');
  const capacities = [...new Set(input.capacityCandidates)].sort(
    (a, b) => (a ?? Infinity) - (b ?? Infinity),
  );
  const offsets = [...new Set(input.dcReleaseOffsetsMonths)].sort(
    (a, b) => a - b,
  );
  const multipliers = [...new Set(input.privateBackgroundMultipliers ?? [1])];
  const mobility = [...new Set(input.mobilityCapacityHours ?? [0])];
  const policies: ScheduleOptions['policy'][] = [
    ...new Set<ScheduleOptions['policy']>(
      input.policies ?? ['pro-rata', 'protect-background'],
    ),
  ];
  if (
    !capacities.length ||
    !offsets.length ||
    !multipliers.length ||
    !mobility.length ||
    !policies.length ||
    capacities.some((v) => v !== null && (!Number.isFinite(v) || v < 0)) ||
    offsets.some((v) => !Number.isInteger(v) || v < 0) ||
    [...multipliers, ...mobility].some((v) => !Number.isFinite(v) || v < 0)
  )
    throw new Error('Invalid reverse-stress grid');
  if (
    capacities.length *
      offsets.length *
      multipliers.length *
      mobility.length *
      policies.length >
    10000
  )
    throw new Error('Reverse-stress grid exceeds 10,000 cases');
  const privateIds = new Set(input.privateBackgroundPackageIds ?? []);
  for (const id of privateIds)
    if (
      id === input.protectedPackageId ||
      !input.packages.some((p) => p.id === id && p.kind === 'background')
    )
      throw new Error(
        'Private demand must identify separate background packages',
      );
  const referenceCapacity = input.schedule.capacity[input.resourceKey] ?? null;
  const cases = [];
  for (const privateMultiplier of multipliers)
    for (const mobilityHours of mobility)
      for (const policy of policies)
        for (const capacityHours of capacities)
          for (const dcReleaseOffsetMonths of offsets) {
            const packages = input.packages.map((p) => ({
              ...p,
              hours: p.hours * (privateIds.has(p.id) ? privateMultiplier : 1),
              releaseMonth:
                p.releaseMonth + (p.kind === 'dc' ? dcReleaseOffsetMonths : 0),
              plannedFinishMonth:
                p.plannedFinishMonth +
                (p.kind === 'dc' ? dcReleaseOffsetMonths : 0),
              predecessors: [...p.predecessors],
            }));
            // The swept resource uses a constant candidate. Preserve trajectories for all others.
            const monthlyCapacity = { ...input.schedule.monthlyCapacity };
            delete monthlyCapacity[input.resourceKey];
            const totalCapacityHours =
              capacityHours === null ? null : capacityHours + mobilityHours;
            const run = pairedSchedule(packages, {
              ...input.schedule,
              policy,
              monthlyCapacity,
              capacity: {
                ...input.schedule.capacity,
                [input.resourceKey]: totalCapacityHours,
              },
            });
            const base = run.baseline.packages.find(
              (p) => p.id === input.protectedPackageId,
            )!;
            const added = run.withDC.packages.find(
              (p) => p.id === input.protectedPackageId,
            )!;
            const impact = run.impacts.find(
              (p) => p.packageId === input.protectedPackageId,
            )!;
            // Known non-completion through the target is a failed target, even if final completion is outside the horizon.
            // Unknown capacity in the protected dependency chain prevents claiming a measured outcome.
            const dependentIds = new Set<string>();
            const collect = (id: string) => {
              if (dependentIds.has(id)) return;
              dependentIds.add(id);
              packages.find((p) => p.id === id)!.predecessors.forEach(collect);
            };
            collect(input.protectedPackageId);
            const unknownCapacity = run.withDC.monthly.some(
              (row) =>
                row.month < input.protectedFinishMonth &&
                row.capacityHours === null &&
                packages.some(
                  (p) =>
                    dependentIds.has(p.id) &&
                    `${p.region}:${p.trade}` === row.resource &&
                    p.releaseMonth <= row.month,
                ),
            );
            cases.push({
              privateMultiplier,
              mobilityHours,
              policy,
              capacityHours,
              totalCapacityHours,
              additionalCapacityHours:
                referenceCapacity === null || capacityHours === null
                  ? null
                  : capacityHours - referenceCapacity,
              dcReleaseOffsetMonths,
              baselineCompletionMonth: base.completionMonth,
              withDCCompletionMonth: added.completionMonth,
              baselineTargetMet: unknownCapacity
                ? null
                : base.completionMonth !== null &&
                  base.completionMonth <= input.protectedFinishMonth,
              protectedTargetMet: unknownCapacity
                ? null
                : added.completionMonth !== null &&
                  added.completionMonth <= input.protectedFinishMonth,
              incrementalDelayMonths: impact.incrementalDelayMonths,
              incrementalEscalationCAD: impact.incrementalEscalationCAD,
              incrementalSiteOverheadCAD: impact.incrementalSiteOverheadCAD,
              baselineTailHours: run.baseline.tailHours,
              withDCTailHours: run.withDC.tailHours,
            });
          }
  const thresholds = [];
  for (const privateMultiplier of multipliers)
    for (const mobilityHours of mobility)
      for (const policy of policies) {
        const group = cases.filter(
          (c) =>
            c.privateMultiplier === privateMultiplier &&
            c.mobilityHours === mobilityHours &&
            c.policy === policy,
        );
        thresholds.push({
          privateMultiplier,
          mobilityHours,
          policy,
          capacityByAIShift: offsets.map((offset) => {
            const successful = group
              .filter(
                (c) =>
                  c.dcReleaseOffsetMonths === offset &&
                  c.protectedTargetMet === true &&
                  c.capacityHours !== null,
              )
              .sort((a, b) => a.capacityHours! - b.capacityHours!);
            const first = successful[0];
            return {
              dcReleaseOffsetMonths: offset,
              minimumTestedCapacityHours: first?.capacityHours ?? null,
              minimumTestedAdditionalCapacityHours:
                first?.additionalCapacityHours == null
                  ? null
                  : Math.max(0, first.additionalCapacityHours),
              status: first
                ? 'target-met-in-grid'
                : group.some(
                      (c) =>
                        c.dcReleaseOffsetMonths === offset &&
                        c.protectedTargetMet === false,
                    )
                  ? 'target-not-met-in-grid'
                  : 'unknown',
            };
          }),
          aiShiftByCapacity: capacities.map((capacity) => {
            const successful = group
              .filter(
                (c) =>
                  c.capacityHours === capacity && c.protectedTargetMet === true,
              )
              .sort(
                (a, b) => a.dcReleaseOffsetMonths - b.dcReleaseOffsetMonths,
              );
            return {
              capacityHours: capacity,
              minimumTestedAIShiftMonths:
                successful[0]?.dcReleaseOffsetMonths ?? null,
            };
          }),
        });
      }
  return {
    hoursBasis: input.hoursBasis,
    resourceKey: input.resourceKey,
    protectedPackageId: input.protectedPackageId,
    protectedFinishMonth: input.protectedFinishMonth,
    referenceCapacityHours: referenceCapacity,
    cases,
    thresholds,
    qualification:
      'Uncalibrated normalized paid-hour scenario thresholds on the tested discrete grid, not measured contractor shortages, continuous optima, causal estimates or probabilities. Mobility adds assumed supply; private background modifies only identified private packages. Capacity totals replace the swept resource trajectory. Other resources retain their input capacity. Unknown capacity remains unknown.',
  };
}
