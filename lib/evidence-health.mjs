/** Evaluate frozen receipt facts against an injected clock; never advance observations. */
export function evaluateFreshness(report, now = new Date()) {
  const evaluatedAt = now.toISOString();
  const sources = report.sources.map((source) => {
    const success = source.last_success ?? source.last_verified;
    const ageDays = Math.max(
      0,
      Math.floor(
        (now.getTime() - Date.parse(`${success}T00:00:00Z`)) / 86400000,
      ),
    );
    const state =
      Number.isFinite(ageDays) && ageDays <= source.maximum_age_days
        ? 'current'
        : 'stale';
    return { ...source, age_days: ageDays, freshness_state: state };
  });
  const stale = sources.filter((source) => source.freshness_state === 'stale');
  return {
    ...report,
    evaluated_at: evaluatedAt,
    as_of_date: evaluatedAt.slice(0, 10),
    release_vintage: report.release_vintage ?? report.as_of_date,
    sources,
    current_count: sources.length - stale.length,
    stale_count: stale.length,
    stale_source_ids: stale.map((source) => source.source_id),
    status: stale.length ? 'degraded' : 'operational',
  };
}

export function evaluateEvidenceHealth(
  digest,
  report,
  surface,
  now = new Date(),
) {
  const freshness = evaluateFreshness(report, now);
  const ageDays = Math.max(
    0,
    Math.floor(
      (now.getTime() - Date.parse(`${digest.edition_date}T00:00:00Z`)) /
        86400000,
    ),
  );
  const cadence = ageDays <= 10 ? 'current' : 'stale';
  const integrity =
    surface.artifact_count > 0 && Boolean(surface.artifact_manifest_sha256);
  const reasons = [];
  if (!integrity) reasons.push('artifact_manifest_missing');
  if (cadence === 'stale') reasons.push('digest_review_cadence_overdue');
  if (freshness.stale_count) reasons.push('source_verification_overdue');
  return {
    freshness,
    ageDays,
    cadence,
    integrity,
    ready: reasons.length === 0,
    reasons,
  };
}
