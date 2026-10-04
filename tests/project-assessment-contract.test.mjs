import test from 'node:test';
import assert from 'node:assert/strict';
import { assessProject } from '../lib/project-assessment.ts';

function fixture() {
  return {
    project: { id: 'school', name: 'Owner school', province: 'Alberta', assetType: 'school', catchment: 'Calgary', budgetCAD: 1000, plannedFinishMonth: 10, floatMonths: 0, overheadCADPerMonth: 100, priceBasisMonth: 0 },
    packages: [{ id: 'owner-electrical', name: 'Owner electrical', scope: 'Electrical', trade: 'Electrical', catchment: 'Calgary', hours: 100, releaseMonth: 0, finishMonth: 1, predecessors: [], budgetCAD: 200, uncommittedCAD: 100, commitment: 'variable', cashMonth: 12 }],
    dcPackages: [{ id: 'dc-electrical', name: 'Assumed DC electrical', trade: 'Electrical', catchment: 'Calgary', hours: 100, releaseMonth: 0, finishMonth: 1, predecessors: [] }],
    capacity: { 'Calgary:Electrical': 100 }, startMonth: 0, endMonth: 36, policy: 'pro-rata', annualEscalation: .12,
    mitigation: { dcShiftMonths: 0, additionalCapacity: {}, earlyProcurementMonths: 0, procurementPackageIds: [] },
    assumptions: ['All quantities and resource sharing are owner assumptions; no empirical effect.'],
  };
}

const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-8, `${actual} != ${expected}`);

test('same background, capacity, policy and price basis define the paired counterfactual', () => {
  const input = fixture();
  input.backgroundPackages = [{ ...input.dcPackages[0], id: 'other-private', hours: 25 }];
  const report = assessProject(input);
  const base = report.cases.baseline.schedule;
  const added = report.cases.withDC.schedule;
  for (const p of base.packages) {
    const match = added.packages.find((q) => q.id === p.id);
    for (const field of ['region', 'trade', 'hours', 'releaseMonth', 'plannedFinishMonth', 'kind']) assert.deepEqual(match[field], p[field]);
    assert.deepEqual(match.predecessors, p.predecessors);
  }
  assert.equal(report.inputs.project.priceBasisMonth, 0);
  assert.deepEqual(report.inputs.capacity, input.capacity);
  assert.deepEqual(report.cases.mitigation.financial, report.cases.withDC.financial);
});

test('baseline inflation is counted once and the AI difference is not a budget premium', () => {
  const report = assessProject(fixture());
  near(report.cases.baseline.financial.escalationCAD, 12);
  const withEscalation = 100 * (1.12 ** (13 / 12) - 1);
  near(report.cases.withDC.financial.escalationCAD, withEscalation);
  near(report.impacts.withDC.escalationCAD, withEscalation - 12);
  near(report.cases.withDC.financial.revisedBudgetCAD, 1000 + withEscalation + 100);
});

test('float absorbs package slippage before project delay and overhead are priced', () => {
  const input = fixture(); input.project.floatMonths = 1;
  const report = assessProject(input);
  assert.equal(report.cases.withDC.packageResults[0].delayMonths, 1);
  assert.equal(report.impacts.withDC.delayMonths, 0);
  assert.equal(report.impacts.withDC.overheadCAD, 0);
  assert.equal(report.cases.withDC.completionMonth, 10);
});

test('overlapping owner packages incur project overhead once', () => {
  const input = fixture();
  input.packages.push({ ...input.packages[0], id: 'owner-second', predecessors: [] });
  input.capacity['Calgary:Electrical'] = 200; input.dcPackages[0].hours = 200;
  const report = assessProject(input);
  assert.equal(report.cases.withDC.packageResults.length, 2);
  assert.equal(report.impacts.withDC.delayMonths, 1);
  assert.equal(report.impacts.withDC.overheadCAD, 100);
});

test('fixed commitments do not reprice and unknown exposure or capacity withholds totals', () => {
  const fixed = fixture(); fixed.packages[0].commitment = 'fixed'; fixed.packages[0].uncommittedCAD = 0;
  assert.equal(assessProject(fixed).impacts.withDC.escalationCAD, 0);
  const unknown = fixture(); unknown.packages[0].uncommittedCAD = null;
  assert.equal(assessProject(unknown).cases.withDC.financial.totalAdditionalCAD, null);
  unknown.capacity['Calgary:Electrical'] = null; unknown.mitigation.additionalCapacity['Calgary:Electrical'] = 100;
  const report = assessProject(unknown);
  assert.equal(report.cases.baseline.completionMonth, null);
  assert.equal(report.cases.withDC.completionMonth, null);
  assert.equal(report.cases.mitigation.completionMonth, null);
  assert.equal(report.cases.mitigation.financial.revisedBudgetCAD, null);
});

test('zero DC produces identical monetary cases, including an explicit scarcity sensitivity', () => {
  const input = fixture(); input.dcPackages = [];
  input.scarcity = { label: 'Explicit hypothetical AI-sensitive exposure', premiumRate: .1, exposureCADByPackage: { 'owner-electrical': 20 } };
  const report = assessProject(input);
  assert.deepEqual(report.cases.withDC.financial, report.cases.baseline.financial);
  assert.deepEqual(report.impacts.withDC, { delayMonths: 0, escalationCAD: 0, overheadCAD: 0, scarcityCAD: 0, totalAdditionalCAD: 0 });
});

test('earlier DC demand can carry backlog into a later owner window', () => {
  const input = fixture();
  input.packages[0].releaseMonth = 1; input.packages[0].finishMonth = 2;
  input.dcPackages[0].hours = 200;
  const report = assessProject(input);
  assert.equal(report.cases.baseline.packageResults[0].completionMonth, 2);
  assert.equal(report.cases.withDC.packageResults[0].completionMonth, 3);
  assert.equal(report.impacts.withDC.delayMonths, 1);
});

test('unsupported region stays qualitative; assessment detaches inputs and retains claim boundaries', () => {
  const input = fixture(); input.project.province = 'Ontario';
  const report = assessProject(input);
  assert.equal(report.qualified, 'qualitative');
  assert.equal(report.cases.withDC.completionMonth, null);
  assert.equal(report.impacts.withDC.totalAdditionalCAD, null);
  assert.match(report.assumptionChain.join(' '), /not observed delay/);
  input.packages[0].hours = 999;
  input.project.budgetCAD = 999;
  assert.equal(report.inputs.packages[0].hours, 100);
  assert.equal(report.inputs.project.budgetCAD, 1000);
});

test('unknown selected AI scope and incomplete owner packages withhold absolute and incremental results', () => {
  const selectedUnknown = fixture(); selectedUnknown.dcPackages[0].hours = null;
  const unknownDC = assessProject(selectedUnknown);
  assert.equal(unknownDC.qualified, 'qualitative');
  assert.equal(unknownDC.cases.withDC.completionMonth, null);
  assert.equal(unknownDC.impacts.withDC.totalAdditionalCAD, null);
  assert.match(unknownDC.unknowns.join(' '), /every included package/);
  const incomplete = fixture(); incomplete.packages[0].hours = null;
  const unknownOwner = assessProject(incomplete);
  assert.equal(unknownOwner.cases.baseline.completionMonth, null);
  assert.equal(unknownOwner.cases.withDC.tailHours, null);
  assert.equal(unknownOwner.cases.withDC.financial.revisedBudgetCAD, null);
});

test('partial financial components stay visible while a full total remains unknown', () => {
  const input = fixture();
  input.project.overheadCADPerMonth = null;
  const report = assessProject(input);
  assert.ok(report.cases.withDC.financial.escalationCAD > 0);
  assert.equal(report.cases.withDC.financial.overheadCAD, null);
  assert.equal(report.cases.withDC.financial.totalAdditionalCAD, null);
  assert.equal(report.cases.withDC.financial.revisedBudgetCAD, null);
  assert.equal(report.impacts.withDC.delayMonths, 1);
  assert.equal(report.impacts.withDC.totalAdditionalCAD, null);
});

test('unsupported asset and explicitly unsupported context cannot unlock numeric results', () => {
  const input = fixture();
  for (const unsupported of ['other', 'road', 'municipal', 'utility', 'unsupported-string']) {
    input.project.assetType = unsupported;
    assert.equal(assessProject(input).qualified, 'qualitative', unsupported);
    assert.equal(assessProject(input).cases.withDC.financial.revisedBudgetCAD, null, unsupported);
  }
  input.project.assetType = 'school'; input.project.supportedContext = false;
  assert.equal(assessProject(input).cases.withDC.completionMonth, null);
});

test('incomplete horizon retains work and withholds project milestone and cost forecasts', () => {
  const input = fixture(); input.capacity['Calgary:Electrical'] = 1;
  const report = assessProject(input);
  assert.equal(report.cases.withDC.completionMonth, null);
  assert.ok(report.cases.withDC.tailHours > 0);
  assert.ok(report.cases.withDC.packageResults[0].remainingHours > 0);
  assert.equal(report.cases.withDC.financial.totalAdditionalCAD, null);
  assert.equal(report.impacts.withDC.delayMonths, null);
});

test('early procurement changes only identified cash exposure while schedule remains matched', () => {
  const input = fixture();
  input.mitigation.earlyProcurementMonths = 6;
  input.mitigation.procurementPackageIds = ['owner-electrical'];
  const report = assessProject(input);
  assert.equal(report.cases.mitigation.completionMonth, report.cases.withDC.completionMonth);
  assert.equal(report.cases.mitigation.packageResults[0].cashMonth, report.cases.withDC.packageResults[0].cashMonth - 6);
  assert.ok(report.cases.mitigation.financial.escalationCAD < report.cases.withDC.financial.escalationCAD);
  assert.equal(report.cases.mitigation.financial.overheadCAD, report.cases.withDC.financial.overheadCAD);
});

test('known total budget bounds exposed scope even when package budget is unknown', () => {
  const input = fixture(); input.packages[0].budgetCAD = null; input.packages[0].uncommittedCAD = 1001;
  assert.throws(() => assessProject(input), /budget|exposure/i);
});
