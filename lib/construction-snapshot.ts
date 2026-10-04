import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import type projects from '@/public/data/construction/projects.json';
import type benchmarks from '@/public/data/construction/benchmarks.json';
import type evidence from '@/public/data/construction/briefing.json';
import type manifest from '@/public/data/construction/manifest.json';

export type ConstructionData = {
  projects: typeof projects;
  benchmarks: typeof benchmarks;
  evidence: typeof evidence;
  manifest: typeof manifest;
};

export async function loadConstructionSnapshot(
  snapshotPath = path.join(
    process.cwd(),
    'public/data/construction/snapshot.json',
  ),
) {
  const raw = await readFile(snapshotPath, 'utf8');
  const bundle = JSON.parse(raw) as { revision: string; payload: string };
  if (
    typeof bundle.payload !== 'string' ||
    createHash('sha256').update(bundle.payload).digest('hex') !==
      bundle.revision
  ) {
    throw new Error('Construction evidence integrity check failed');
  }
  const data = JSON.parse(bundle.payload) as ConstructionData;
  if (
    !data.projects?.length ||
    !data.evidence?.labour?.length ||
    !data.manifest?.refresh?.sources?.length
  )
    throw new Error('Construction evidence is incomplete');
  return { revision: bundle.revision, data };
}

export function constructionFreshness(
  data: ConstructionData,
  now = new Date(),
) {
  const today = now.toISOString().slice(0, 10);
  return data.manifest.refresh.sources.map((s) => ({
    ...s,
    status: s.lastCheckFailed
      ? 'Last check failed'
      : today >= s.nextCheckDue
        ? s.mode === 'review_required'
          ? 'Review due'
          : 'Check overdue'
        : s.mode === 'review_required'
          ? 'Reviewed reference'
          : 'Within check interval',
  }));
}
