import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { tmpdir } from 'node:os';
import path from 'node:path';
import {
  loadConstructionSnapshot,
  constructionFreshness,
} from '../lib/construction-snapshot.ts';
import {
  resolveConstructionBenchmark,
  constructionBenchmarkPeriods,
} from '../lib/alberta-evidence-summary.mjs';

test('request-time reader observes a replacement without rebuilding and rejects corrupt bundles', async () => {
  const directory = await mkdtemp(
    path.join(tmpdir(), 'construction-snapshot-'),
  );
  try {
    const file = path.join(directory, 'snapshot.json');
    const original = JSON.parse(
      await readFile(
        new URL('../public/data/construction/snapshot.json', import.meta.url),
        'utf8',
      ),
    );
    await writeFile(file, JSON.stringify(original));
    const first = await loadConstructionSnapshot(file);
    const data = JSON.parse(original.payload);
    data.projects[0].cost = 123456789;
    const payload = JSON.stringify(data);
    await writeFile(
      file,
      JSON.stringify({
        revision: createHash('sha256').update(payload).digest('hex'),
        payload,
      }),
    );
    const next = await loadConstructionSnapshot(file);
    assert.notEqual(first.revision, next.revision);
    assert.equal(next.data.projects[0].cost, 123456789);
    await writeFile(file, JSON.stringify({ ...original, payload }));
    await assert.rejects(() => loadConstructionSnapshot(file), /integrity/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
test('freshness distinguishes publication periods, overdue checks and failed checks', async () => {
  const { data } = await loadConstructionSnapshot();
  const rows = constructionFreshness(data, new Date('2030-01-01T00:00:00Z'));
  assert.equal(
    rows.find((s) => s.id === 'STATCAN_BCPI_18100289').status,
    'Check overdue',
  );
  assert.equal(rows.find((s) => s.id === 'BUILDFORCE').status, 'Review due');
  data.manifest.refresh.sources[0].lastCheckFailed = true;
  assert.equal(constructionFreshness(data)[0].status, 'Last check failed');
});
test('new benchmark horizons and fiscal years update both values and labels', async () => {
  const { data } = await loadConstructionSnapshot();
  const b = data.benchmarks;
  b.parameters.push({
    id: 'recruitment_requirement_to2040',
    value: 60000,
    status: 'published_forecast',
  });
  b.parameters.push({
    id: 'first_time_local_entrants_to2040',
    value: 50000,
    status: 'published_forecast',
  });
  b.parameters.push({
    id: 'public_capital_q1_fy2027_28',
    value: 11000,
    status: 'observed_published_forecast',
  });
  assert.equal(
    resolveConstructionBenchmark(b, 'recruitment_requirement_to2035').value,
    60000,
  );
  assert.equal(
    resolveConstructionBenchmark(b, 'public_capital_q1_fy2026_27').value,
    11000,
  );
  assert.equal(
    resolveConstructionBenchmark(b, 'retirements_to2035'),
    undefined,
  );
  assert.equal(constructionBenchmarkPeriods(b).fiscalYear, 'FY2027–28');
  assert.equal(constructionBenchmarkPeriods(b).recruitment, 'Through 2040');
});
