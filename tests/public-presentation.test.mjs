import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
  scenarioMoney,
  scenarioRate,
  publicReviews,
  uniqueMaterialSignals,
} from '../lib/public-presentation.mjs';
test('uncalibrated display does not imply cents or erase small positive effects', () => {
  assert.equal(scenarioMoney(1453.004), '$1,453M');
  assert.equal(scenarioMoney(24.6), '$25M');
  assert.equal(scenarioMoney(0.2), '<$1M');
  assert.equal(scenarioMoney(null), 'Withheld');
  assert.equal(scenarioRate(0.0091), '<0.01');
  assert.equal(scenarioRate(0), '0.00');
});
test('public review output retains blocked status without forwarding internal diagnostics', () => {
  const r = publicReviews({
    review: {
      status: 'blocked',
      reason: 'Internal CLI failure',
      evidence: '/private/path',
    },
  });
  assert.equal(r.review.status, 'blocked');
  assert.ok(!JSON.stringify(r).includes('CLI'));
  assert.ok(!JSON.stringify(r).includes('/private'));
});
test('same observed series is shown once while distinct measurements remain separate', () => {
  const p = {
    geography_id: 'CMA_835',
    component: 'steel',
    index_value: 110,
    year_over_year_percent_change: 10.4,
    archetype: 'school',
  };
  const grouped = uniqueMaterialSignals([
    p,
    { ...p, archetype: 'hospital' },
    { ...p, archetype: 'factory', index_value: 111 },
  ]);
  assert.equal(grouped.length, 2);
  assert.deepEqual(grouped[0].archetypes, ['school', 'hospital']);
});
test('historical worked example uses same-quarter index ratios, without changing scenarios', () => {
  const a = JSON.parse(fs.readFileSync('public/data/alberta-boom-analog.json'));
  assert.ok(a.observations.every((r) => r.period.endsWith('Q2')));
  assert.equal(
    Math.round((100 * a.observations.at(-1).value) / a.observations[0].value),
    146,
  );
});
