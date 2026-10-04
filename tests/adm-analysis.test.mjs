import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ADM_CASES,
  labourSizing,
  planSensitivity,
} from '../lib/adm-analysis.mjs';
test('budget sensitivity uses exposed share and does not apply shock to all spending', () => {
  assert.deepEqual(planSensitivity(10687, 0.25, 10), {
    costMillions: 267.175,
    planPct: 2.5,
  });
  assert.equal(planSensitivity(10687, 0, 10).costMillions, 0);
  assert.throws(() => planSensitivity(10687, 1.1, 10));
});
test('labour sizing retains assumptions, hourly units and duration', () => {
  const low = labourSizing(49.01e9, ADM_CASES[0]);
  assert.equal(low.construction, 3.67575e9);
  assert.ok(Math.abs(low.electricalFTE - 239.7228260869565) < 1e-6);
  const short = labourSizing(49.01e9, { ...ADM_CASES[0], years: 3 });
  assert.ok(Math.abs(short.electricalFTE / low.electricalFTE - 5 / 3) < 1e-8);
  assert.equal(labourSizing(0, ADM_CASES[0]).hvacFTE, 0);
  assert.throws(() => labourSizing(1, { ...ADM_CASES[0], years: 0 }));
});
