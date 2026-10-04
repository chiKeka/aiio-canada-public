import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildDemandRisk } from '../lib/demand-risk-analysis.mjs';
const data = JSON.parse(
  JSON.parse(fs.readFileSync('public/data/construction/snapshot.json', 'utf8'))
    .payload,
);
const evidence = JSON.parse(
  fs.readFileSync('public/data/construction/adm-evidence.json', 'utf8'),
);
const risk = buildDemandRisk(data.projects, {
  asOf: data.manifest.asOf,
  exposure: evidence.exposure,
});
test('schedule attribution conserves every annual total', () => {
  risk.annual.forEach((r, i) =>
    assert.ok(
      Math.abs(
        r.anchored +
          r.fallback -
          risk.full.scenarios[1].annual[i].electricalFTE,
      ) < 1e-8,
    ),
  );
  assert.equal(risk.fallbackCapex, 32e9);
});
test('exposure screen intersects the stress window, not the whole horizon', () => {
  assert.deepEqual(risk.window, { start: 2029, end: 2030 });
  assert.equal(risk.exposure.length, 7);
  assert.ok(risk.exposure.every((p) => Number(p.end_year) >= 2029));
});
test('realization reduces proposed volume; longer duration shifts concentration', () => {
  assert.ok(
    Math.abs(risk.cases[1].electricalFTE / risk.cases[0].electricalFTE - 0.5) <
      1e-8,
  );
  assert.ok(risk.cases[2].electricalFTE < risk.cases[0].electricalFTE);
  assert.ok(risk.cases[0].hvacStockRatio > 0.6);
});
