import test from 'node:test';
import assert from 'node:assert/strict';
import {
  modelProjectDemand,
  monthlyShare,
} from '../lib/project-demand-model.mjs';
const p = {
  id: 'a',
  name: 'A',
  region: 'Edmonton',
  stage: 'Proposed',
  cost: 1e9,
  start: 2027,
  end: 2030,
};
test('monthly allocation conserves all package hours', () => {
  let sum = 0;
  for (let m = 0; m < 20; m++) sum += monthlyShare(m, 2.5, 15.2);
  assert.ok(Math.abs(sum - 1) < 1e-12);
});
test('dated project retains years, missing cost excluded and zero is explicit', () => {
  const r = modelProjectDemand([p, { ...p, id: 'b', cost: null }]);
  assert.equal(r.phases[0].startMonth, 2027 * 12);
  assert.equal(r.phases[0].endMonth, 2031 * 12);
  assert.equal(r.excluded.length, 1);
  for (const c of r.scenarios)
    assert.ok(
      Math.abs(
        c.annual.reduce((s, r) => s + r.electricalHours, 0) +
          c.preElectricalHours +
          c.postElectricalHours -
          c.allElectricalHours,
      ) < 1e-6,
    );
});
test('shifting dates changes timing but not total demand', () => {
  const a = modelProjectDemand([p]),
    b = modelProjectDemand([{ ...p, start: 2029, end: 2032 }]);
  assert.equal(
    a.scenarios[1].allElectricalHours,
    b.scenarios[1].allElectricalHours,
  );
  assert.equal(b.scenarios[1].peak.year - a.scenarios[1].peak.year, 2);
});
test('undated projects disclose assigned timing and are not assigned observed dates', () => {
  const r = modelProjectDemand([{ ...p, start: null, end: null }]);
  assert.match(r.phases[0].basis, /Model-assigned/);
  assert.equal(r.phases[0].start, null);
  assert.equal(r.scheduleAnchored, 0);
  assert.throws(() => modelProjectDemand([p, p]));
});

test('realization retains construction-stage work and scales only proposed work', () => {
  const rows = [p, { ...p, id: 'built', stage: 'Under Construction' }];
  const full = modelProjectDemand(rows);
  const half = modelProjectDemand(rows, { proposedRealisation: 0.5 });
  assert.ok(Math.abs(half.scenarios[1].allElectricalHours / full.scenarios[1].allElectricalHours - 0.75) < 1e-10);
  assert.throws(() => modelProjectDemand(rows, { proposedRealisation: 1.1 }));
});

test('longer undated schedules conserve total trade hours', async () => {
  const { DEMAND_POLICY } = await import('../lib/project-demand-model.mjs');
  const rows = [{ ...p, start: null, end: null }];
  const base = modelProjectDemand(rows);
  const longer = modelProjectDemand(rows, { policy: { ...DEMAND_POLICY, undatedDurationMonths: 48 } });
  assert.equal(longer.scenarios[1].allElectricalHours, base.scenarios[1].allElectricalHours);
  assert.equal(longer.phases[0].endMonth - longer.phases[0].startMonth, 48);
});
