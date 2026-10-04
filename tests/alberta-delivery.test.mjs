import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  evidenceChanges,
  procurementDeadline,
  capacityBalance,
  validateDeliveryRegister,
} from '../lib/alberta-delivery.mjs';
const registry = JSON.parse(
  readFileSync('data/governance/alberta-delivery-register.json', 'utf8'),
);
const base = {
  projects: [{ id: 'one', name: 'One', cost: null, end: null }],
  evidence: { labour: [], prices: [], capital: {} },
  benchmarks: {},
};
test('no changes for identical evidence; missing cost is not zero', () => {
  assert.deepEqual(evidenceChanges(base, structuredClone(base)), []);
  const updated = structuredClone(base);
  updated.projects[0].cost = 0;
  assert.match(evidenceChanges(base, updated)[0].detail, /Not published → 0/);
});
test('new, removed, revised and benchmark records are detected', () => {
  const updated = structuredClone(base);
  updated.projects = [{ id: 'two', name: 'Two' }];
  updated.benchmarks = { period: 'new' };
  assert.deepEqual(
    evidenceChanges(base, updated).map((x) => x.kind),
    ['New record', 'Removed from inventory', 'Updated benchmarks'],
  );
});
test('procurement subtracts every duration, rejects missing and invalid dates', () => {
  assert.equal(procurementDeadline('2027-03-01', 2, 1, 1), '2027-02-01');
  assert.equal(procurementDeadline('2027-02-30', 2), null);
  assert.equal(procurementDeadline('', 2), null);
  assert.equal(procurementDeadline('2027-03-01', -2), null);
});
test('capacity never converts missing inputs to available labour', () => {
  assert.equal(capacityBalance(null, 0, 1), null);
  assert.deepEqual(capacityBalance(100, 120, 30), { available: 0, gap: 30 });
  assert.deepEqual(capacityBalance(100, 20, 90), { available: 80, gap: 10 });
});
test('review register rejects unsupported milestones, duplicates and completed actions', () => {
  assert.equal(validateDeliveryRegister(registry), registry);
  const duplicate = structuredClone(registry);
  duplicate.projects.push(duplicate.projects[0]);
  assert.throws(() => validateDeliveryRegister(duplicate));
  const milestone = structuredClone(registry);
  milestone.projects[0].milestones.permit = { status: 'Approved' };
  assert.throws(() => validateDeliveryRegister(milestone));
  const action = structuredClone(registry);
  action.actions[0].status = 'complete';
  assert.throws(() => validateDeliveryRegister(action));
});
