import { evaluateEvidenceHealth } from '@/lib/evidence-health.mjs';
import { publicReviews } from '@/lib/public-presentation.mjs';
import digest from '@/public/data/latest-digest.json';
import gates from '@/data/governance/program-gates.json';
import surface from '@/public/data/research-surface.json';
import release from '@/public/data/latest.json';
import freshness from '@/public/data/source-freshness.json';
import receipts from '@/public/data/source-receipts.json';

export const dynamic = 'force-dynamic';

export function GET() {
  const {
    freshness: currentFreshness,
    ageDays,
    cadence,
    integrity,
    ready,
    reasons,
  } = evaluateEvidenceHealth(digest, { ...receipts, release_vintage: freshness.as_of_date }, surface);

  return Response.json(
    {
      status: integrity ? 'operational' : 'degraded',
      availability: 'available',
      readiness: ready ? 'ready' : 'degraded',
      readiness_reasons: reasons,
      last_good_evidence_retained: true,
      checked_at: new Date().toISOString(),
      application: {
        service: 'AIIO Canada',
        environment: process.env.VERCEL_ENV ?? 'local',
      },
      evidence: {
        digest_edition: digest.edition_date,
        digest_status: digest.status,
        age_days: ageDays,
        cadence,
        artifact_count: surface.artifact_count,
        manifest_sha256: surface.artifact_manifest_sha256,
        source_freshness: {
          as_of_date: currentFreshness.as_of_date,
          release_vintage: currentFreshness.release_vintage,
          sources: currentFreshness.sources,
          status: currentFreshness.status,
          current_count: currentFreshness.current_count,
          stale_count: currentFreshness.stale_count,
          stale_source_ids: currentFreshness.stale_source_ids,
        },
      },
      release: {
        version: release.manifest.version,
        status: release.manifest.status,
        model_version: release.manifest.model_version,
        forecast_authorized: false,
      },
      governance: {
        deployment: gates.deployment.status,
        independent_review: publicReviews(gates.independent_review),
      },
    },
    {
      status: integrity ? 200 : 503,
      headers: {
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
      },
    },
  );
}
