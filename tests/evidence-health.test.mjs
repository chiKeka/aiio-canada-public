import test from 'node:test';
import assert from 'node:assert/strict';
import {
  evaluateFreshness,
  evaluateEvidenceHealth,
} from '../lib/evidence-health.mjs';
const report = {
  as_of_date: '2026-09-03',
  sources: [
    {
      source_id: 'A',
      last_verified: '2026-09-01',
      last_success: '2026-09-03',
      last_attempt: '2026-09-20',
      last_attempt_status: 'error',
      observation_date: '2026-08-01',
      maximum_age_days: 10,
    },
  ],
};
test('clock ages receipts without changing observation, failed attempt does not verify', () => {
  const fresh = evaluateFreshness(report, new Date('2026-09-13T00:00:00Z'));
  const stale = evaluateFreshness(report, new Date('2026-09-14T00:00:00Z'));
  assert.equal(fresh.current_count, 1);
  assert.equal(stale.stale_count, 1);
  assert.equal(stale.sources[0].observation_date, '2026-08-01');
  assert.equal(stale.release_vintage, '2026-09-03');
});
test('stale evidence is degraded readiness with retained artifact integrity', () => {
  const result = evaluateEvidenceHealth(
    { edition_date: '2026-09-03' },
    report,
    { artifact_count: 2, artifact_manifest_sha256: 'abc' },
    new Date('2026-10-03T00:00:00Z'),
  );
  assert.equal(result.integrity, true);
  assert.equal(result.ready, false);
  assert.deepEqual(result.reasons, [
    'digest_review_cadence_overdue',
    'source_verification_overdue',
  ]);
});
