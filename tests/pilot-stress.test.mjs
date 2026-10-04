import test from 'node:test';
import assert from 'node:assert/strict';
import { reverseStress } from '../lib/pilot-stress.ts';

const publicWork = {
  id: 'named-school',
  region: 'Airdrie',
  trade: 'Electrical',
  kind: 'background',
  hours: 100,
  releaseMonth: 0,
  plannedFinishMonth: 1,
  predecessors: [],
  uncommittedExposureCAD: 1000,
};
const aiWork = {
  ...publicWork,
  id: 'cal3-phase1',
  kind: 'dc',
  uncommittedExposureCAD: undefined,
};
const input = {
  packages: [publicWork, aiWork],
  schedule: {
    startMonth: 0,
    endMonth: 6,
    capacity: { 'Airdrie:Electrical': 100 },
    policy: 'pro-rata',
    annualEscalation: 0.12,
  },
  protectedPackageId: publicWork.id,
  protectedFinishMonth: 1,
  resourceKey: 'Airdrie:Electrical',
  capacityCandidates: [100, 150, 200, 400],
  dcReleaseOffsetsMonths: [0, 1, 2],
  hoursBasis: {
    unit: 'normalized-paid-hours',
    paidHoursPerUnit: null,
    assumption:
      'Illustrative equal 100-unit packages; no empirical hours calibration.',
  },
};

test('reverse stress identifies tested capacity and staggering thresholds, with no-impact controls', () => {
  const r = reverseStress(input);
  const proRata = r.thresholds.find((g) => g.policy === 'pro-rata');
  assert.equal(proRata.capacityByAIShift[0].minimumTestedCapacityHours, 200);
  assert.equal(
    proRata.capacityByAIShift[0].minimumTestedAdditionalCapacityHours,
    100,
  );
  assert.equal(proRata.aiShiftByCapacity[0].minimumTestedAIShiftMonths, 1);
  assert.equal(
    r.cases.find(
      (c) =>
        c.policy === 'pro-rata' &&
        c.capacityHours === 100 &&
        c.dcReleaseOffsetMonths === 0,
    ).incrementalDelayMonths,
    1,
  );
  assert.equal(
    r.cases.find(
      (c) =>
        c.policy === 'pro-rata' &&
        c.capacityHours === 400 &&
        c.dcReleaseOffsetMonths === 0,
    ).incrementalDelayMonths,
    0,
  );
  assert.equal(
    r.cases.find(
      (c) =>
        c.policy === 'protect-background' &&
        c.capacityHours === 100 &&
        c.dcReleaseOffsetMonths === 0,
    ).incrementalDelayMonths,
    0,
  );
  assert.match(r.qualification, /not measured contractor shortages/);
});

test('private demand and mobility scenarios preserve public exposure and change conditional thresholds', () => {
  const privateWork = {
    ...publicWork,
    id: 'other-private',
    uncommittedExposureCAD: undefined,
  };
  const r = reverseStress({
    ...input,
    packages: [...input.packages, privateWork],
    privateBackgroundPackageIds: [privateWork.id],
    privateBackgroundMultipliers: [0, 1],
    mobilityCapacityHours: [0, 100],
    policies: ['pro-rata'],
    capacityCandidates: [100, 200, 300],
    dcReleaseOffsetsMonths: [0],
  });
  const group = (privateMultiplier, mobilityHours) =>
    r.thresholds.find(
      (g) =>
        g.privateMultiplier === privateMultiplier &&
        g.mobilityHours === mobilityHours,
    ).capacityByAIShift[0];
  assert.equal(group(0, 0).minimumTestedCapacityHours, 200);
  assert.equal(group(1, 0).minimumTestedCapacityHours, 300);
  assert.equal(group(1, 100).minimumTestedCapacityHours, 200);
  assert.ok(
    r.cases.find(
      (c) =>
        c.privateMultiplier === 1 &&
        c.mobilityHours === 0 &&
        c.capacityHours === 100,
    ).incrementalEscalationCAD > 0,
  );
});

test('unknown actual capacity is never replaced by zero or inferred from mobility', () => {
  const r = reverseStress({
    ...input,
    schedule: { ...input.schedule, capacity: { 'Airdrie:Electrical': null } },
    capacityCandidates: [null, 200],
    dcReleaseOffsetsMonths: [0],
    mobilityCapacityHours: [100],
    policies: ['pro-rata'],
  });
  const unknown = r.cases.find((c) => c.capacityHours === null);
  assert.equal(unknown.totalCapacityHours, null);
  assert.equal(unknown.protectedTargetMet, null);
  assert.equal(unknown.incrementalDelayMonths, null);
  assert.equal(unknown.additionalCapacityHours, null);
  const normalized = r.cases.find((c) => c.capacityHours === 200);
  assert.equal(normalized.protectedTargetMet, true);
  assert.equal(normalized.additionalCapacityHours, null);
});

test('finite constrained horizon fails target and retains hours; no successful threshold is invented', () => {
  const r = reverseStress({
    ...input,
    capacityCandidates: [0],
    dcReleaseOffsetsMonths: [0],
    policies: ['pro-rata'],
  });
  assert.equal(r.cases[0].protectedTargetMet, false);
  assert.equal(r.cases[0].baselineTailHours, 100);
  assert.equal(r.cases[0].withDCTailHours, 200);
  assert.equal(
    r.thresholds[0].capacityByAIShift[0].minimumTestedCapacityHours,
    null,
  );
  assert.equal(
    r.thresholds[0].capacityByAIShift[0].status,
    'target-not-met-in-grid',
  );
});

test('unknown predecessor trade is preserved, other capacity trajectories remain intact', () => {
  const predecessor = {
    ...publicWork,
    id: 'civil',
    trade: 'Civil',
    uncommittedExposureCAD: undefined,
  };
  const r = reverseStress({
    ...input,
    packages: [predecessor, { ...publicWork, predecessors: ['civil'] }, aiWork],
    protectedFinishMonth: 2,
    schedule: {
      ...input.schedule,
      monthlyCapacity: {
        'Airdrie:Electrical': { 0: 0 },
        'Airdrie:Civil': { 0: null },
      },
    },
    policies: ['pro-rata'],
    capacityCandidates: [200],
    dcReleaseOffsetsMonths: [0],
  });
  assert.equal(r.cases[0].protectedTargetMet, null);
  assert.equal(r.cases[0].withDCCompletionMonth, null);
});

test('grid does not mutate inputs or public schedule and validates assumptions and private identities', () => {
  const copy = structuredClone(input);
  reverseStress(input);
  assert.deepEqual(input, copy);
  assert.throws(
    () =>
      reverseStress({ ...input, privateBackgroundPackageIds: [publicWork.id] }),
    /Private demand/,
  );
  assert.throws(
    () =>
      reverseStress({
        ...input,
        hoursBasis: { ...input.hoursBasis, assumption: '' },
      }),
    /assumption/,
  );
  assert.throws(
    () => reverseStress({ ...input, dcReleaseOffsetsMonths: [-1] }),
    /grid/,
  );
  assert.throws(
    () => reverseStress({ ...input, capacityCandidates: [] }),
    /grid/,
  );
  assert.throws(
    () => reverseStress({ ...input, protectedPackageId: aiWork.id }),
    /background/,
  );
});
