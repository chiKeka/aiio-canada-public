import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { summarizeEnablingLedger } from '../lib/enabling-infrastructure.ts';
const asset = (overrides = {}) => ({ id: 'substation', aiPhaseIds: ['phase-1'], assetClass: 'substation', scope: 'Fixture only', incrementality: 'incremental', funding: 'uncommitted', costCad: { low: 10, high: 20 }, costBasis: 'scenario', timing: { startYear: 2027, endYear: 2028 }, evidence: { status: 'scenario', sourceIds: [], note: 'Test assumption' }, payerShares: { developer: .4, ratepayer: .3, government: .2, unknown: .1 }, aiCapexMembership: 'excluded', capexComponent: null, ...overrides });
const ledger = (assets) => ({ schemaVersion: '1.0', scenarioId: 'test', aiPhaseIds: ['phase-1', 'phase-2'], currency: 'CAD', priceYear: 2026, aiCapexCad: 100, componentBudgetsCad: { grid: 25 }, assets });
test('incremental range and mutually exclusive payer allocations reconcile', () => {
 const r = summarizeEnablingLedger(ledger([asset()]));
 assert.equal(r.valid, true);
 assert.deepEqual(r.totalProgramCad, { low: 110, high: 120 });
 for (const edge of ['low', 'high']) assert.equal(Object.values(r.allocatedIncrementalCad).reduce((sum, row) => sum + row[edge], 0), r.additionalIncrementalCad[edge]);
});
test('included AI cost and already-funded baseline are not added twice', () => {
 const r = summarizeEnablingLedger(ledger([asset({ aiCapexMembership: 'included', capexComponent: 'grid' }), asset({ id: 'road', incrementality: 'baseline', funding: 'already_funded' })]));
 assert.deepEqual(r.totalProgramCad, { low: 100, high: 100 });
 assert.deepEqual(r.includedByComponent.grid, { low: 10, high: 20 });
});
test('shared enabling asset is accounted once across phases', () => {
 const r = summarizeEnablingLedger(ledger([asset({ aiPhaseIds: ['phase-1', 'phase-2'] })]));
 assert.deepEqual(r.additionalIncrementalCad, { low: 10, high: 20 });
 assert.equal(summarizeEnablingLedger(ledger([asset(), asset()])).valid, false);
});
test('invalid allocations budgets links ranges and evidence fail closed', () => {
 for (const bad of [ { payerShares: { government: .5 } }, { costCad: { low: 20, high: 10 } }, { aiPhaseIds: ['unregistered'] }, { aiCapexMembership: 'included', capexComponent: 'grid', costCad: { low: 10, high: 30 } }, { costBasis: 'observed' }, { costCad: { low: NaN, high: 20 } } ]) {
  const r = summarizeEnablingLedger(ledger([asset(bad)]));
  assert.equal(r.valid, false);
  assert.equal(r.additionalIncrementalCad, null);
  assert.equal(r.totalProgramCad, null);
 }
});
test('unknown cost or incrementality or capex membership prevents total', () => {
 for (const unknown of [ { costCad: null, costBasis: 'unknown' }, { incrementality: 'unknown' }, { aiCapexMembership: 'unknown' } ]) {
  const r = summarizeEnablingLedger(ledger([asset(unknown)]));
  assert.equal(r.valid, true);
  assert.equal(r.complete, false);
  assert.equal(r.totalProgramCad, null);
 }
});
test('Alberta diligence placeholders contain no invented observed cost', () => {
 const data = JSON.parse(readFileSync(new URL('../data/scenarios/alberta_enabling_infrastructure_v0.1.json', import.meta.url)));
 const r = summarizeEnablingLedger(data);
 assert.equal(r.valid, true);
 assert.equal(r.unresolvedAssets, 4);
 assert.equal(r.totalProgramCad, null);
 assert.equal(data.componentBudgetsCad.grid_and_generation, 4e9);
 assert.ok(data.assets.every(x => x.costCad === null && x.payerShares.unknown === 1 && x.evidence.status === 'scenario'));
 const scenario = JSON.parse(readFileSync(new URL('../data/scenarios/alberta_50b_counterfactual_v0.2.json', import.meta.url)));
 assert.equal(data.aiCapexCad, scenario.investment_total_cad);
 for (const [component, share] of Object.entries(scenario.components)) assert.equal(data.componentBudgetsCad[component], data.aiCapexCad * share);
});
