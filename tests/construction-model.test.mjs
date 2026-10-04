import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import {
  calculate,
  defaults,
  escalation,
  publicAnnual,
} from '../lib/construction-model.ts';
const project = {
  id: 'test',
  name: 'Test phase',
  region: 'Alberta',
  stage: 'Proposed',
  cost: 100e6,
  start: null,
  end: 2029,
  source: '',
  asOf: '2026-09-05',
};
const selection = { test: { included: true, cost: 100e6, online: 2029 } };
test('reported start is retained when online year is assumed', () => {
  const r = calculate(
    [{ ...project, start: 2027, end: null }],
    selection,
    defaults,
  );
  assert.equal(r.phases[0].startMonth, 2027 * 12);
  assert.match(r.phases[0].basis, /assumed online/);
});
test('export provenance matches model and published inputs', () => {
  const m = JSON.parse(
    readFileSync(
      new URL('../public/data/construction/manifest.json', import.meta.url),
    ),
  );
  for (const [name, hash] of Object.entries(m.sha256)) {
    const path = name.startsWith('lib/')
      ? `../${name}`
      : `../public/data/construction/${name}`;
    assert.equal(
      createHash('sha256')
        .update(readFileSync(new URL(path, import.meta.url)))
        .digest('hex'),
      hash,
    );
  }
});
test('empty DC baseline preserves unknown capacity', () => {
  const r = calculate([project], {}, defaults);
  assert.equal(r.totalHours, 0);
  assert.ok(r.rows.every((x) => x.gap === null && x.ratio === null));
});
test('full-window paid hours conserved and concurrent phases add', () => {
  const r = calculate([project], selection, defaults);
  const expected =
    100e6 *
    0.5 *
    defaults.shares.reduce(
      (s, x, i) => s + (x * defaults.labour[i]) / defaults.wages[i],
      0,
    );
  assert.ok(Math.abs(r.totalHours - expected) < 1e-6);
  const doubled = calculate(
    [project, { ...project, id: 'two' }],
    { ...selection, two: selection.test },
    defaults,
  );
  assert.ok(Math.abs(doubled.totalHours - 2 * r.totalHours) < 1e-6);
});
test('horizon truncation retains tail and total job-years', () => {
  const r = calculate(
    [project],
    { test: { included: true, cost: 100e6, online: 2031 } },
    { ...defaults, years: 3 },
  );
  assert.ok(r.totalHours > 0);
  assert.ok(r.outsideWindowHours > 0);
  assert.ok(
    Math.abs(
      r.totalHours +
        r.outsideWindowHours -
        r.phases[0].hours.reduce((a, b) => a + b, 0),
    ) < 1e-6,
  );
});
test('past proposed starts shift forward without inventing history', () => {
  const r = calculate(
    [project],
    { test: { included: true, cost: 100e6, online: 2026 } },
    defaults,
  );
  assert.equal(r.phases[0].startMonth, 2026 * 12 + 8);
  assert.ok(r.phases[0].basis.includes('shifted'));
});
test('fiscal cash conserved by initialized annual cohorts', () => {
  for (const cohortYears of [4, 5]) {
    const o = { ...defaults, cohortYears };
    const r = calculate([], {}, o);
    for (let y = 2026; y <= 2032; y++) {
      const cash = r.cohorts
        .filter((c) => c.year <= y && c.year > y - cohortYears)
        .reduce((s, c) => s + c.commitment / cohortYears, 0);
      assert.ok(Math.abs(cash - publicAnnual(y, o)) < 0.01);
    }
  }
});
test('zero capacity reports full gap, ample capacity no gap', () => {
  const r = calculate([project], selection, {
    ...defaults,
    capacity: [0, 1e9, null],
  });
  assert.ok(
    r.rows
      .filter((x) => x.trade === 'Civil')
      .every((x) => x.gap === x.dcHours + x.publicHours),
  );
  assert.ok(
    r.rows.filter((x) => x.trade === 'Electrical').every((x) => x.gap === 0),
  );
  assert.ok(
    r.rows.filter((x) => x.trade === 'Mechanical').every((x) => x.gap === null),
  );
});
test('validation rejects invalid shares and missing selected costs', () => {
  assert.throws(() => calculate([], {}, { ...defaults, shares: [1, 1, 1] }));
  assert.throws(() =>
    calculate([project], { test: { ...selection.test, cost: 0 } }, defaults),
  );
  assert.throws(() => calculate([], {}, { ...defaults, wages: [0, 1, 1] }));
});
test('escalation applies only to exposure and elapsed delay', () => {
  assert.equal(escalation(60e6, 0.035, 0), 0);
  assert.equal(escalation(0, 0.035, 6), 0);
  assert.ok(Math.abs(escalation(60e6, 0.035, 6) - 1040969.85) < 0.01);
});
test('platform register equals research source and references resolve', () => {
  const r = JSON.parse(
    readFileSync(
      new URL('../public/data/construction/benchmarks.json', import.meta.url),
    ),
  );
  assert.deepEqual(
    r,
    JSON.parse(
      readFileSync(
        new URL(
          '../docs/research/construction-benchmark-register.json',
          import.meta.url,
        ),
      ),
    ),
  );
  assert.equal(
    new Set(r.parameters.map((p) => p.id)).size,
    r.parameters.length,
  );
  for (const p of r.parameters)
    for (const id of p.source_ids)
      assert.ok(r.sources.some((s) => s.id === id));
});

const task = (id, kind = 'background', extra = {}) => ({ id, kind, region: 'Calgary', trade: 'Electrical', hours: 100, releaseMonth: 0, plannedFinishMonth: 1, predecessors: [], ...extra });
const scheduleOptions = { startMonth: 0, endMonth: 6, capacity: { 'Calgary:Electrical': 100 }, policy: 'pro-rata', annualEscalation: 0.12 };
test('paired capacity allocation conserves hours, carries backlog and exposes only commitments', async () => {
  const { pairedSchedule } = await import('../lib/construction-model.ts');
  const r = pairedSchedule([task('school', 'background', { uncommittedExposureCAD: 1000 }), task('dc', 'dc')], scheduleOptions);
  assert.equal(r.baseline.packages[0].completionMonth, 1);
  assert.equal(r.withDC.packages[0].completionMonth, 2);
  assert.equal(r.impacts[0].incrementalDelayMonths, 1);
  assert.ok(Math.abs(r.impacts[0].incrementalEscalationCAD - escalation(1000, 0.12, 1)) < 1e-8);
  for (const row of r.withDC.monthly) assert.ok(row.allocatedHours <= row.capacityHours + 1e-8);
  for (const p of r.withDC.packages) assert.ok(Math.abs(p.servedHours + p.remainingHours - p.hours) < 1e-8);
  assert.equal(r.withDC.monthly[0].backlogHours, 100);
});
test('precedence, catchments, allocation policies and unknown capacity remain explicit', async () => {
  const { schedulePackages } = await import('../lib/construction-model.ts');
  const r = schedulePackages([task('civil'), task('fitout', 'dc', { predecessors: ['civil'] }), task('remote', 'dc', { region: 'Edmonton' })], scheduleOptions);
  const first = r.allocations.find((a) => a.packageId === 'fitout');
  assert.ok(first.month >= r.packages[0].completionMonth);
  assert.equal(r.packages[2].completionMonth, null);
  assert.equal(r.packages[2].remainingHours, 100);
  const protectedRun = schedulePackages([task('school'), task('dc', 'dc')], { ...scheduleOptions, policy: 'protect-background' });
  assert.equal(protectedRun.packages[0].completionMonth, 1);
  assert.throws(() => schedulePackages([task('a', 'dc', { predecessors: ['b'] }), task('b', 'dc', { predecessors: ['a'] })], scheduleOptions), /Cyclic/);
});
test('zero DC has zero paired effect and unfinished horizon retains all unserved work', async () => {
  const { pairedSchedule } = await import('../lib/construction-model.ts');
  const r = pairedSchedule([task('school', 'background', { uncommittedExposureCAD: 1000 })], scheduleOptions);
  assert.equal(r.impacts[0].incrementalDelayMonths, 0);
  assert.equal(r.impacts[0].incrementalEscalationCAD, 0);
  const blocked = pairedSchedule([task('school'), task('dc', 'dc')], { ...scheduleOptions, capacity: { 'Calgary:Electrical': 0 } });
  assert.equal(blocked.withDC.tailHours, 200);
  assert.equal(blocked.impacts[0].incrementalDelayMonths, null);
  assert.equal(blocked.withDC.packages[0].escalationCAD, null);
});
test('private demand is additional background in both paired cases', () => {
  const r = calculate([], {}, { ...defaults, privateHours: [1200, 2400, 3600] });
  assert.equal(r.rows[0].privateHours, 300);
  assert.deepEqual(r.scheduling.baseline, r.scheduling.withDC);
});
test('responsive monthly supply is explicit and missing trajectory capacity remains unknown', async () => {
  const { schedulePackages } = await import('../lib/construction-model.ts');
  const r = schedulePackages([task('school')], { ...scheduleOptions, capacity: { 'Calgary:Electrical': 0 }, monthlyCapacity: { 'Calgary:Electrical': { 0: null, 1: 100 } } });
  assert.equal(r.monthly[0].allocatedHours, null);
  assert.equal(r.packages[0].completionMonth, 2);
});
