import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runInNewContext } from 'node:vm';
import test from 'node:test';
import ts from 'typescript';
import { webcrypto, createHash } from 'node:crypto';

const root = fileURLToPath(new URL('../', import.meta.url));
function load(path) {
  const source = readFileSync(resolve(root, path), 'utf8');
  const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true } }).outputText;
  const testModule = { exports: {} };
  runInNewContext(compiled, { crypto: webcrypto, TextEncoder, module: testModule, exports: testModule.exports, require: (name) => {
    if (name === './project-cashflow') return load('lib/project-cashflow.ts');
    if (name === './planning-calibration') return load('lib/planning-calibration.ts');
    if (name === './decision-analysis') return load('lib/decision-analysis.ts');
    if (name === './executive-evidence') return load('lib/executive-evidence.ts');
    if (name === './decision-outlook') return load('lib/decision-outlook.ts');
    if (name.startsWith('@/') && name.endsWith('.json')) return JSON.parse(readFileSync(resolve(root, name.slice(2)), 'utf8'));
    throw new Error(`Unexpected test import: ${name}`);
  } });
  return testModule.exports;
}
const { queryNumber, monthNumber, spendingShares, buildCashflowOutlook, allocateMonthlyDrivers } = load('lib/project-cashflow.ts');
const { buildPlanningCalibration } = load('lib/planning-calibration.ts');
const { buildDecisionOutlook, decisionAction, deliveryYears } = load('lib/decision-outlook.ts');
const { buildDecisionAnalysis } = load('lib/decision-analysis.ts');
const { buildExecutiveEvidence } = load('lib/executive-evidence.ts');
const { buildAssessmentRecord, encodeAssessmentRecord, resolveFocus } = load('lib/assessment-record.ts');

test('snapshot detaches inputs, reconciles recorded cashflow, and carries an integrity checksum', async () => {
  const analysis = buildDecisionAnalysis({ assetId: 'hospital', metroId: 'CMA_835', startYear: 2029, duration: 2 });
  const inputs = { ...config, budgetMillions: 1200, spendingProfile: 'bell', assumptions: { ...assumptions } };
  const assessment = buildDecisionOutlook(inputs, buildPlanningCalibration(config));
  const args = { inputs, assessment, analysis, projectName: 'Test hospital', approvalStage: 'treasury_board', contingencyPct: 12, comparison: { inputs, assessment, market: 'Edmonton region' }, selectedMonth: '2030-03', selectedDriver: 'missing', generatedAt: '2026-09-04T12:00:00Z', planning: { status: 'incomplete', passed_check_count: 2, check_count: 7 } };
  const record = buildAssessmentRecord(args);
  const restored = buildCashflowOutlook(record.monthly_prices, record.project.inputs.budgetMillions, record.project.inputs.spendingProfile);
  near(restored.combinedSpend, record.result.combinedSpend);
  near(record.comparison.scenario_spend_delta_millions, 0);
  assert.equal(record.focus.month, '2030-03');
  assert.equal(record.boundary.causal_ai_effect_authorized, false);
  inputs.assumptions.annualBaselinePct = 11;
  assert.notEqual(record.project.inputs.assumptions.annualBaselinePct, 11);
  const envelope = JSON.parse(await encodeAssessmentRecord(record));
  assert.equal(createHash('sha256').update(envelope.payload).digest('hex'), envelope.sha256);
  assert.notEqual(createHash('sha256').update(envelope.payload + ' ').digest('hex'), envelope.sha256);
  assert.equal(buildAssessmentRecord({ ...args, assessment: null }), null);
  assert.equal(buildAssessmentRecord({ ...args, comparison: { ...args.comparison, inputs: { ...inputs, priceBasis: '2027-01' } } }).comparison.scenario_spend_delta_millions, null);
  assert.equal(resolveFocus(assessment, '2050-01', 'missing').month, '2029-01');
});

test('executive evidence is scoped context with resolvable sources, not rate inputs', () => {
  const analysis = buildDecisionAnalysis({ assetId: 'hospital', metroId: 'CMA_835', startYear: 2029, duration: 5 });
  const signals = buildExecutiveEvidence(analysis);
  assert.equal(signals.length, 4);
  assert.ok(signals.every((signal) => signal.role === 'Context only'));
  assert.ok(signals.flatMap((signal) => signal.sources).every((source) => source.record?.canonical_url.startsWith('https://')));
  assert.equal(signals[0].scope, 'Edmonton region');
  assert.equal(signals[3].value, String(analysis.concurrentProjectCount));
  const missing = buildExecutiveEvidence({ ...analysis, materials: [], labourRows: [], concurrentProjectCount: 0 });
  assert.equal(missing[0].value, 'Unavailable');
  assert.equal(missing[1].value, 'Unavailable');
  assert.equal(missing[3].value, '0');
  assert.equal(missing[0].sources.length, 0);
  const road = buildExecutiveEvidence(buildDecisionAnalysis({ assetId: 'road', metroId: 'CMA_825', startYear: 2038, duration: 5 }));
  assert.equal(road[0].scope, 'Calgary region');
  assert.match(road[0].limitation, /must not be read as a road-construction index/);
  assert.match(road[3].detail, /2038–2042/);
});
const assumptions = { annualBaselinePct: 6, peakAiAnnualPctPoints: 1.25, localCapturePct: 36, lagMonths: 3, uncertaintyPct: 40 };
const config = { assetOutcome: 'SCHEDULE_HOSPITALS_DELAY_PRESSURE', durationYears: 2, projectStart: 2029, priceBasis: '2028-01', assumptions };
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);
const priceRow = (month, baseline, combined) => ({ month, cumulative_baseline_pct: baseline, cumulative_combined_pct: combined, cumulative_lower_pct: baseline, cumulative_upper_pct: combined + 1 });

test('shared cockpit calculation reconciles to monthly outlook and responds to assumptions', () => {
  const calibration = buildPlanningCalibration(config);
  const input = { ...config, budgetMillions: 1200, spendingProfile: 'bell' };
  const result = buildDecisionOutlook(input, calibration);
  near(result.cashflow.combinedSpend, buildCashflowOutlook(calibration.monthly_series, 1200, 'bell').combinedSpend);
  assert.equal(result.isOfficial, false);
  assert.ok(buildDecisionOutlook({ ...input, assumptions: { ...assumptions, peakAiAnnualPctPoints: 3 } }, calibration).cashflow.aiIncrement > result.cashflow.aiIncrement);
  assert.equal(buildDecisionOutlook({ ...input, priceBasis: '2031-01' }, calibration), null);
  const official = { ...calibration, status: 'calibrated', publication_boundary: { ...calibration.publication_boundary, monthly_ai_increment_authorized: true, combined_project_escalation_authorized: true } };
  assert.equal(buildDecisionOutlook(input, official).isOfficial, true);
  assert.equal(buildDecisionOutlook({ ...input, assetOutcome: 'OTHER' }, official).isOfficial, false);
});

test('decision changes with approval stage and timeline retains uncovered delivery years', () => {
  assert.notEqual(decisionAction('procurement').title, decisionAction('concept').title);
  const partial = deliveryYears(2034, 2038, 2026, 2035);
  assert.equal(partial.length, 5);
  assert.equal(partial[0].year, 2034);
  assert.equal(partial.filter((row) => row.overlap).length, 2);
  assert.equal(deliveryYears(2038, 2042, 2026, 2035).filter((row) => row.overlap).length, 0);
  assert.equal(deliveryYears(2029.5, 2034, 2026, 2035).length, 0);
});

test('empty/partial links preserve defaults; explicit zero is valid', () => {
  for (const value of [new URLSearchParams(), new URLSearchParams('baseline='), new URLSearchParams('baseline=Infinity'), new URLSearchParams('baseline=-1'), new URLSearchParams('baseline=13')]) assert.equal(queryNumber(value, 'baseline', 0, 12) ?? 3.5, 3.5);
  assert.equal(queryNumber(new URLSearchParams('baseline=0'), 'baseline', 0, 12), 0);
  assert.equal(queryNumber(new URLSearchParams('start=2029.5'), 'start', 2026, 2040, true), undefined);
});
test('dates reject malformed months', () => {
  assert.equal(monthNumber('2029-13'), null); assert.equal(monthNumber('2029-1'), null);
  assert.equal(monthNumber('2029-01') - monthNumber('2028-12'), 1);
});
test('profiles allocate the entire base budget exactly', () => {
  for (const profile of ['uniform', 'front_loaded', 'back_loaded', 'bell']) near(spendingShares(60, profile).reduce((a, b) => a + b, 0), 1);
});
test('cashflow weighting is not end-loaded whole-budget escalation', () => {
  const result = buildCashflowOutlook([priceRow('2029-01', 0, 0), priceRow('2029-02', 0, 10)], 100, 'uniform');
  near(result.aiIncrement, 5); near(result.combinedSpend, 105);
  near(result.monthly.reduce((sum, row) => sum + row.baseSpend, 0), 100);
});
test('back-loaded spending carries greater positive-growth exposure', () => {
  const rows = [priceRow('2029-01', 0, 0), priceRow('2029-02', 5, 10)];
  assert.ok(buildCashflowOutlook(rows, 100, 'back_loaded').combinedSpend > buildCashflowOutlook(rows, 100, 'front_loaded').combinedSpend);
});
test('price basis anchors first month and pre-construction escalation', () => {
  const same = buildPlanningCalibration({ ...config, priceBasis: '2029-01' });
  near(same.monthly_series[0].cumulative_combined_pct, 0);
  const earlier = buildPlanningCalibration(config);
  near(earlier.monthly_series[0].cumulative_baseline_pct, 6);
  assert.equal(earlier.monthly_series.length, 24);
  assert.equal(earlier.monthly_series.at(-1).month, '2030-12');
  assert.throws(() => buildPlanningCalibration({ ...config, priceBasis: '2030-01' }));
});
test('no AI and zero baseline preserve original budget', () => {
  const model = buildPlanningCalibration({ ...config, assumptions: { ...assumptions, annualBaselinePct: 0, peakAiAnnualPctPoints: 0 } });
  const result = buildCashflowOutlook(model.monthly_series, 1200, 'bell');
  near(result.combinedSpend, 1200); near(result.aiIncrement, 0);
});
test('totals reconcile and sensitivity remains ordered', () => {
  const result = buildCashflowOutlook(buildPlanningCalibration(config).monthly_series, 1200, 'bell');
  near(result.combinedSpend, 1200 + result.baselineEscalation + result.aiIncrement);
  assert.ok(result.lowSpend <= result.combinedSpend && result.combinedSpend <= result.highSpend);
});
test('missing, nonfinite or discontinuous monthly prices withhold dollars', () => {
  assert.equal(buildCashflowOutlook([priceRow('2029-01', null, 10)], 100, 'uniform'), null);
  assert.equal(buildCashflowOutlook([priceRow('2029-01', 0, NaN)], 100, 'uniform'), null);
  assert.equal(buildCashflowOutlook([priceRow('2029-01', 0, 0), priceRow('2029-03', 0, 1)], 100, 'uniform'), null);
});
test('monthly driver allocation reconciles without adding upstream cost', () => {
  const contributions = allocateMonthlyDrivers([82, 6, 6, 6], 0.1);
  near(contributions.reduce((a, b) => a + b, 0), 0.1);
  near(contributions[0], 0.082);
  assert.ok(allocateMonthlyDrivers([0, 0], 0).every((value) => value === 0));
  assert.ok(allocateMonthlyDrivers([null, 1], 0.1).every((value) => value === null));
});
