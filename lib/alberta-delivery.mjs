/** Published evidence comparison: stable IDs, null preserved, no imputed observations. */
export function evidenceChanges(previous, current) {
  const changes = [];
  const before = new Map(previous.projects.map((p) => [p.id, p]));
  const after = new Map(current.projects.map((p) => [p.id, p]));
  for (const p of current.projects) {
    const old = before.get(p.id);
    if (!old)
      changes.push({ kind: 'New record', name: p.name, detail: p.stage });
    else
      for (const field of ['name', 'region', 'stage', 'cost', 'start', 'end']) {
        if (old[field] !== p[field])
          changes.push({
            kind: `Revised ${field}`,
            name: p.name,
            detail: `${old[field] ?? 'Not published'} → ${p[field] ?? 'Not published'}`,
          });
      }
  }
  for (const p of previous.projects)
    if (!after.has(p.id))
      changes.push({
        kind: 'Removed from inventory',
        name: p.name,
        detail: 'Removal does not establish cancellation.',
      });
  for (const key of ['labour', 'prices', 'capital'])
    if (
      JSON.stringify(previous.evidence[key]) !==
      JSON.stringify(current.evidence[key])
    )
      changes.push({
        kind: 'Updated evidence',
        name: key,
        detail:
          'Source observations or coverage changed; inspect the current evidence table.',
      });
  if (
    JSON.stringify(previous.benchmarks) !== JSON.stringify(current.benchmarks)
  )
    changes.push({
      kind: 'Updated benchmarks',
      name: 'Reviewed benchmark register',
      detail: 'Values, reference periods or source documentation changed.',
    });
  return changes;
}
export function procurementDeadline(
  requiredOnSite,
  leadWeeks,
  freightWeeks = 0,
  testingWeeks = 0,
) {
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(requiredOnSite) ||
    ![leadWeeks, freightWeeks, testingWeeks].every(
      (n) => Number.isFinite(n) && n >= 0,
    )
  )
    return null;
  const date = new Date(`${requiredOnSite}T00:00:00Z`);
  if (
    !Number.isFinite(date.getTime()) ||
    date.toISOString().slice(0, 10) !== requiredOnSite
  )
    return null;
  date.setUTCDate(
    date.getUTCDate() -
      Math.ceil((leadWeeks + freightWeeks + testingWeeks) * 7),
  );
  return date.toISOString().slice(0, 10);
}
export function capacityBalance(capacity, committed, demand) {
  if (
    ![capacity, committed, demand].every(
      (n) => typeof n === 'number' && Number.isFinite(n) && n >= 0,
    )
  )
    return null;
  return {
    available: Math.max(0, capacity - committed),
    gap: Math.max(0, demand - Math.max(0, capacity - committed)),
  };
}
export function validateDeliveryRegister(r) {
  for (const key of [
    'projects',
    'packages',
    'capacity',
    'suppliers',
    'actions',
  ])
    if (!Array.isArray(r[key])) throw new Error(`Missing ${key} array`);
  if (r.version !== 1 || !/^\d{4}-\d{2}-\d{2}$/.test(r.asOf))
    throw new Error('Register version and review date required');
  const ids = new Set();
  const cited = (v) =>
    v &&
    typeof v.source === 'string' &&
    v.source.startsWith('https://') &&
    /^\d{4}-\d{2}-\d{2}$/.test(v.verifiedOn);
  for (const p of r.projects) {
    if (!p.id || ids.has(p.id)) throw new Error('Project IDs must be unique');
    ids.add(p.id);
    if (!['unverified', 'campus', 'phase', 'programme'].includes(p.recordKind))
      throw new Error('Invalid record kind');
    if (
      (p.recordKind !== 'unverified' || p.campusId !== null) &&
      !cited(p.recordEvidence)
    )
      throw new Error('Campus and phase classification require evidence');
    for (const m of Object.values(p.milestones))
      if (m !== null && (!cited(m) || !m.status))
        throw new Error('Milestones need status, source and verification date');
    if (
      p.constructionCost !== null &&
      (!cited(p.constructionCost) ||
        !Number.isFinite(p.constructionCost.value) ||
        p.constructionCost.value < 0)
    )
      throw new Error('Construction costs need source and verification date');
  }
  for (const p of r.packages)
    if (
      !p.projectId ||
      !p.projectName ||
      !['data_centre', 'infrastructure'].includes(p.projectKind) ||
      !p.region ||
      ![
        'civil',
        'electrical',
        'mechanical',
        'commissioning',
        'utility',
      ].includes(p.trade) ||
      !['reported', 'inferred'].includes(p.basis) ||
      !/^\d{4}-Q[1-4]$/.test(p.start) ||
      !/^\d{4}-Q[1-4]$/.test(p.end) ||
      p.end < p.start ||
      Number(p.end.slice(0, 4)) - Number(p.start.slice(0, 4)) >= 20 ||
      !cited(p)
    )
      throw new Error(
        'Package needs valid project, region, trade, quarter range, basis and citation',
      );
  for (const records of [
    r.packages.map((p) =>
      [p.projectId, p.trade, p.start, p.end, p.basis].join('|'),
    ),
    r.capacity.map((c) =>
      [c.contractor, c.region, c.trade, c.quarter].join('|'),
    ),
  ])
    if (new Set(records).size !== records.length)
      throw new Error(
        'Duplicate package or contractor-period records require reconciliation',
      );
  for (const c of r.capacity)
    if (
      !c.region ||
      !c.trade ||
      !c.contractor ||
      !/^\d{4}-Q[1-4]$/.test(c.quarter) ||
      capacityBalance(c.paidHours, c.committedHours, 0) === null ||
      !cited(c)
    )
      throw new Error(
        'Capacity needs contractor, region, trade, quarter, hours and citation',
      );
  for (const s of r.suppliers)
    if (
      !s.supplier ||
      !s.equipment ||
      !s.specification ||
      !s.region ||
      !s.slotStatus ||
      !cited(s) ||
      !procurementDeadline(
        s.requiredOnSite,
        s.leadWeeks,
        s.freightWeeks,
        s.testingWeeks,
      )
    )
      throw new Error(
        'Supplier needs specification, region, slot status, dates, durations and citation',
      );
  const actionIds = new Set();
  for (const a of r.actions) {
    if (
      !a.id ||
      actionIds.has(a.id) ||
      !a.title ||
      !['open', 'in_progress', 'blocked', 'complete'].includes(a.status)
    )
      throw new Error('Invalid action');
    actionIds.add(a.id);
    if (a.due !== null && !/^\d{4}-\d{2}-\d{2}$/.test(a.due))
      throw new Error('Invalid action due date');
    if (a.projectId !== null && !ids.has(a.projectId))
      throw new Error('Unknown action project');
    if (a.status === 'complete' && (!a.owner || !a.evidence))
      throw new Error('Completed actions need an owner and evidence');
    if (
      a.benefit !== null &&
      (!a.evidence || !a.benefit.basis || !Number.isFinite(a.benefit.value))
    )
      throw new Error('Benefits need evidence, value and basis');
  }
  return r;
}
