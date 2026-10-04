import test from 'node:test';
import assert from 'node:assert/strict';
import { assessProject, calendarMonth } from '../lib/project-assessment.ts';
const owner = {
  id: 'electrical',
  name: 'School electrical',
  scope: 'Electrical',
  trade: 'Electrical',
  catchment: 'Calgary',
  hours: 100,
  releaseMonth: 0,
  finishMonth: 1,
  predecessors: [],
  budgetCAD: 10e6,
  uncommittedCAD: 8e6,
  commitment: 'variable',
  cashMonth: 0,
};
const dc = {
  id: 'dc',
  name: 'DC phase',
  trade: 'Electrical',
  catchment: 'Calgary',
  hours: 100,
  releaseMonth: 0,
  finishMonth: 1,
  predecessors: [],
};
const fixture = () => ({
  project: {
    id: 'school',
    name: 'School',
    province: 'Alberta',
    assetType: 'school',
    catchment: 'Calgary',
    budgetCAD: 50e6,
    plannedFinishMonth: 1,
    floatMonths: 0,
    overheadCADPerMonth: 100,
    priceBasisMonth: 0,
  },
  packages: [structuredClone(owner)],
  dcPackages: [structuredClone(dc)],
  capacity: { 'Calgary:Electrical': 100 },
  startMonth: 0,
  endMonth: 12,
  policy: 'pro-rata',
  annualEscalation: 0.12,
  mitigation: {
    dcShiftMonths: 0,
    additionalCapacity: {},
    earlyProcurementMonths: 0,
    procurementPackageIds: [],
  },
  assumptions: ['Hypothetical paid hours, capacity and cash exposure.'],
});
const close = (actual, expected) =>
  assert.ok(Math.abs(actual - expected) < 1e-6, `${actual} != ${expected}`);

test('paired case conserves paid hours and capacity and reprices only remaining exposure', () => {
  const input = fixture(),
    r = assessProject(input);
  assert.equal(r.cases.baseline.completionMonth, 1);
  assert.equal(r.cases.withDC.completionMonth, 2);
  assert.equal(r.impacts.withDC.delayMonths, 1);
  close(r.impacts.withDC.escalationCAD, 8e6 * (1.12 ** (1 / 12) - 1));
  assert.equal(r.impacts.withDC.overheadCAD, 100);
  for (const p of r.cases.withDC.schedule.packages)
    close(p.hours, p.servedHours + p.remainingHours);
  for (const m of r.cases.withDC.schedule.monthly)
    assert.ok(m.allocatedHours <= m.capacityHours + 1e-8);
  assert.equal(r.matches[0].overlapMonths, 1);
  assert.deepEqual(r.inputs, input);
  r.inputs.packages[0].hours = 999;
  assert.equal(input.packages[0].hours, 100);
});

test('separate price basis includes baseline once and uses its paired difference', () => {
  const input = fixture();
  input.packages[0].cashMonth = 12;
  const r = assessProject(input);
  close(r.cases.baseline.financial.escalationCAD, 8e6 * 0.12);
  close(r.impacts.withDC.escalationCAD, 8e6 * (1.12 ** (13 / 12) - 1.12));
  close(
    r.cases.withDC.financial.revisedBudgetCAD,
    50e6 + 8e6 * (1.12 ** (13 / 12) - 1) + 100,
  );
});

test('float absorbs package slip once and project overhead is charged once', () => {
  const input = fixture();
  input.project.floatMonths = 1;
  let r = assessProject(input);
  assert.equal(r.impacts.withDC.delayMonths, 0);
  assert.equal(r.impacts.withDC.overheadCAD, 0);
  input.project.floatMonths = 0;
  input.packages.push({
    ...owner,
    id: 'mechanical',
    name: 'Mechanical',
    scope: 'Mechanical',
    trade: 'Mechanical',
    budgetCAD: 10e6,
    uncommittedCAD: 2e6,
  });
  input.dcPackages.push({ ...dc, id: 'dc-mechanical', trade: 'Mechanical' });
  input.capacity['Calgary:Mechanical'] = 100;
  r = assessProject(input);
  assert.equal(r.impacts.withDC.delayMonths, 1);
  assert.equal(r.impacts.withDC.overheadCAD, 100);
});

test('zero DC has zero increments while unknown absolute capacity remains unknown', () => {
  const input = fixture();
  input.dcPackages = [];
  input.capacity['Calgary:Electrical'] = null;
  const r = assessProject(input);
  assert.equal(r.cases.baseline.completionMonth, null);
  assert.equal(r.cases.withDC.financial.totalAdditionalCAD, null);
  assert.deepEqual(r.impacts.withDC, {
    delayMonths: 0,
    escalationCAD: 0,
    overheadCAD: 0,
    scarcityCAD: 0,
    totalAdditionalCAD: 0,
  });
  input.dcPackages = [{ ...dc, hours: null }];
  const unknown = assessProject(input);
  assert.equal(unknown.impacts.withDC.delayMonths, null);
  assert.equal(unknown.impacts.withDC.totalAdditionalCAD, null);
});

test('location, trade and non-intersection do not create a premium', () => {
  for (const change of [
    { catchment: 'Edmonton' },
    { trade: 'Civil' },
    { releaseMonth: 4, finishMonth: 5 },
  ]) {
    const input = fixture();
    Object.assign(input.dcPackages[0], change);
    const r = assessProject(input);
    assert.equal(r.matches.length, 0);
    assert.equal(r.impacts.withDC.delayMonths, 0);
    assert.equal(r.impacts.withDC.escalationCAD, 0);
  }
});

test('early work backlog can intersect a later owner window even without planned overlap', () => {
  const input = fixture();
  input.packages[0].releaseMonth = 1;
  input.packages[0].finishMonth = 2;
  input.project.plannedFinishMonth = 2;
  input.dcPackages[0].hours = 200;
  const r = assessProject(input);
  assert.equal(r.matches.length, 0);
  assert.ok(r.impacts.withDC.delayMonths > 0);
});

test('precedence and retained tails prevent treating unfinished work as completed', () => {
  const input = fixture();
  input.packages.push({
    ...owner,
    id: 'civil',
    name: 'Civil enabling',
    scope: 'Civil',
    trade: 'Civil',
    finishMonth: 1,
    budgetCAD: 1e6,
    uncommittedCAD: 0,
    commitment: 'fixed',
  });
  input.packages[0].predecessors = ['civil'];
  input.packages[0].finishMonth = 2;
  input.project.plannedFinishMonth = 2;
  input.capacity['Calgary:Civil'] = 100;
  let r = assessProject(input);
  const allocations = r.cases.withDC.schedule.allocations;
  const civil = r.cases.withDC.schedule.packages.find((p) => p.id === 'civil');
  assert.ok(
    allocations.find((a) => a.packageId === 'electrical').month >=
      civil.completionMonth,
  );
  input.capacity['Calgary:Electrical'] = 0;
  r = assessProject(input);
  assert.equal(r.cases.withDC.completionMonth, null);
  assert.ok(r.cases.withDC.tailHours > 0);
  assert.equal(r.cases.withDC.financial.totalAdditionalCAD, null);
});

test('mitigation records staggering, extra capacity and earlier explicit procurement independently', () => {
  const input = fixture();
  input.packages[0].cashMonth = 6;
  input.mitigation.dcShiftMonths = 1;
  input.mitigation.earlyProcurementMonths = 2;
  input.mitigation.procurementPackageIds = ['electrical'];
  let r = assessProject(input);
  assert.equal(r.impacts.mitigation.delayMonths, 0);
  assert.ok(r.impacts.mitigation.escalationCAD < 0);
  assert.equal(r.cases.mitigation.packageResults[0].cashMonth, 4);
  input.mitigation.dcShiftMonths = 0;
  input.mitigation.earlyProcurementMonths = 0;
  input.mitigation.additionalCapacity = { 'Calgary:Electrical': 100 };
  r = assessProject(input);
  assert.equal(r.impacts.mitigation.delayMonths, 0);
  input.mitigation.additionalCapacity = {};
  input.mitigation.policy = 'protect-background';
  r = assessProject(input);
  assert.equal(r.impacts.mitigation.delayMonths, 0);
});

test('fixed and unknown commitments preserve different financial boundaries', () => {
  const input = fixture();
  input.packages[0].commitment = 'fixed';
  input.packages[0].uncommittedCAD = 0;
  input.packages[0].cashMonth = null;
  input.annualEscalation = null;
  let r = assessProject(input);
  assert.equal(r.impacts.withDC.escalationCAD, 0);
  assert.equal(r.impacts.withDC.overheadCAD, 100);
  input.packages[0].commitment = 'unknown';
  input.packages[0].uncommittedCAD = null;
  r = assessProject(input);
  assert.equal(r.cases.withDC.financial.escalationCAD, null);
  assert.equal(r.impacts.withDC.totalAdditionalCAD, null);
});

test('explicit scarcity sensitivity is disjoint, never compounded or inferred', () => {
  const input = fixture();
  input.scarcity = {
    label: 'Separate 1M exposed purchase; hypothetical 10% premium',
    premiumRate: 0.1,
    exposureCADByPackage: { electrical: 1e6 },
  };
  let r = assessProject(input);
  assert.equal(r.impacts.withDC.scarcityCAD, 100000);
  close(r.impacts.withDC.escalationCAD, 7e6 * (1.12 ** (1 / 12) - 1));
  input.dcPackages = [];
  r = assessProject(input);
  assert.equal(r.cases.withDC.financial.scarcityCAD, 0);
  assert.equal(r.impacts.withDC.scarcityCAD, 0);
  input.scarcity.exposureCADByPackage.electrical = 9e6;
  assert.throws(() => assessProject(input), /Scarcity exposure/);
});

test('unknown capacity thresholds are conditional totals and cannot supply missing quantities', () => {
  const input = fixture();
  input.capacity['Calgary:Electrical'] = null;
  input.capacityThresholds = [
    { resourceKey: 'Calgary:Electrical', candidates: [100, 150, 200] },
  ];
  let r = assessProject(input);
  assert.equal(r.cases.withDC.completionMonth, null);
  assert.equal(r.capacityThresholds[0].minimumTestedCapacityHours, 200);
  assert.match(r.capacityThresholds[0].qualification, /not measured/);
  input.dcPackages[0].hours = null;
  r = assessProject(input);
  assert.equal(r.capacityThresholds[0].minimumTestedCapacityHours, null);
  assert.ok(r.capacityThresholds[0].cases.every((c) => c.targetMet === null));
});

test('unsupported context and independent procurement/utility links suppress unsupported dollars', () => {
  const input = fixture();
  input.project.assetType = 'other';
  input.qualitativeLinks = [
    {
      channel: 'supplier',
      label: 'Transformer lead time unknown',
      source: null,
    },
    { channel: 'utility', label: 'Connection not confirmed', source: null },
  ];
  const r = assessProject(input);
  assert.equal(r.qualified, 'qualitative');
  assert.equal(r.cases.withDC.financial.totalAdditionalCAD, null);
  assert.equal(r.impacts.withDC.totalAdditionalCAD, null);
  assert.equal(r.qualitativeLinks.length, 2);
});

test('contracts reject invalid budgets, cycles and non-finite assumptions', () => {
  for (const mutate of [
    (i) => (i.packages[0].uncommittedCAD = 11e6),
    (i) => (i.packages[0].hours = NaN),
    (i) => (i.project.floatMonths = -1),
    (i) => (i.packages[0].predecessors = ['electrical']),
    (i) => (i.packages[0].commitment = 'fixed'),
    (i) => (i.annualEscalation = Infinity),
  ]) {
    const input = fixture();
    mutate(input);
    assert.throws(() => assessProject(input));
  }
  assert.equal(calendarMonth('2027-01'), 2027 * 12);
  assert.throws(() => calendarMonth('2027-13'));
});

test('an early noncritical package slip does not move the latest project milestone', () => {
  const input = fixture();
  input.project.plannedFinishMonth = 10;
  input.packages.push({
    ...owner,
    id: 'late-phase',
    name: 'Later civil phase',
    scope: 'Civil',
    trade: 'Civil',
    releaseMonth: 9,
    finishMonth: 10,
    budgetCAD: 1e6,
    uncommittedCAD: 0,
    commitment: 'fixed',
  });
  input.capacity['Calgary:Civil'] = 100;
  const r = assessProject(input);
  assert.equal(r.cases.withDC.packageResults[0].delayMonths, 1);
  assert.equal(r.cases.withDC.completionMonth, 10);
  assert.equal(r.impacts.withDC.delayMonths, 0);
  assert.equal(r.impacts.withDC.overheadCAD, 0);
  assert.ok(r.impacts.withDC.escalationCAD > 0);
});

test('unsupported asset strings fail closed while explicit zero remaining work needs no assumed capacity', () => {
  const input = fixture();
  input.project.assetType = 'airport';
  let r = assessProject(input);
  assert.equal(r.qualified, 'qualitative');
  assert.equal(r.cases.withDC.financial.totalAdditionalCAD, null);
  input.project.assetType = 'school';
  input.dcPackages = [];
  Object.assign(input.packages[0], {
    hours: 0,
    trade: null,
    catchment: null,
    releaseMonth: null,
    finishMonth: null,
    commitment: 'fixed',
    uncommittedCAD: 0,
    cashMonth: null,
  });
  input.capacity = {};
  input.capacityThresholds = [
    { resourceKey: 'Calgary:Electrical', candidates: [0] },
  ];
  r = assessProject(input);
  assert.equal(r.cases.withDC.completionMonth, 1);
  assert.equal(r.cases.withDC.financial.totalAdditionalCAD, 0);
  assert.equal(r.capacityThresholds[0].cases[0].targetMet, true);
});
