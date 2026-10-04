/** Display precision only: calculations and downloaded records retain original values. */
export function scenarioMoney(value) {
  if (value == null || !Number.isFinite(value)) return 'Withheld';
  if (value !== 0 && Math.abs(value) < 1) return `${value < 0 ? '−' : ''}<$1M`;
  return `$${Math.round(value).toLocaleString('en-CA')}M`;
}
export function scenarioRate(value) {
  if (value == null || !Number.isFinite(value)) return 'Withheld';
  if (value !== 0 && Math.abs(value) < 0.01)
    return `${value < 0 ? '−' : ''}<0.01`;
  return value.toFixed(2);
}
/** Publish review outcomes without forwarding execution diagnostics. */
export function publicReviews(reviews) {
  return Object.fromEntries(
    Object.entries(reviews).map(([id, gate]) => [
      id,
      {
        status: gate.status,
        reason:
          gate.status === 'blocked'
            ? 'Independent review is incomplete; no verdict is available.'
            : 'Review status is recorded; forecast authorization is assessed separately.',
      },
    ]),
  );
}
/** Deduplicate identical observed series reused across asset mappings; retain differing observations. */
export function uniqueMaterialSignals(observations) {
  const groups = new Map();
  for (const item of observations) {
    const key = JSON.stringify([
      item.geography_id,
      item.component,
      item.index_value,
      item.year_over_year_percent_change,
    ]);
    const existing = groups.get(key);
    if (existing) existing.archetypes.push(item.archetype);
    else groups.set(key, { ...item, archetypes: [item.archetype] });
  }
  return [...groups.values()];
}
