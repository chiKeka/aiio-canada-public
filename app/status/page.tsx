import { evaluateEvidenceHealth } from '@/lib/evidence-health.mjs';
import {
  Activity,
  CheckCircle2,
  Clock3,
  Database,
  ShieldCheck,
  TriangleAlert,
} from 'lucide-react';
import Link from 'next/link';

import { PageIntro, SiteFooter, ResearchShell } from '@/components/site-shell';
import digest from '@/public/data/latest-digest.json';
import gates from '@/data/governance/program-gates.json';
import surface from '@/public/data/research-surface.json';
import release from '@/public/data/latest.json';
import freshness from '@/public/data/source-freshness.json';
import receipts from '@/public/data/source-receipts.json';
import practicalRoute from '@/data/model-runs/practical_evidence_route_current.json';

export const dynamic = 'force-dynamic';

export default function StatusPage() {
  const {
    freshness: currentFreshness,
    ageDays,
    cadence,
  } = evaluateEvidenceHealth(digest, { ...receipts, release_vintage: freshness.as_of_date }, surface);
  const checks = [
    {
      icon: Database,
      label: 'Evidence surface',
      value: `${surface.artifact_count} hash-locked artifacts`,
      ok: surface.artifact_count > 0,
    },
    {
      icon: Clock3,
      label: 'Latest evidence digest',
      value: `${digest.edition_date} · ${cadence} · ${ageDays} days old`,
      ok: cadence === 'current',
    },
    {
      icon: Database,
      label: 'Registered source freshness',
      value: `${currentFreshness.current_count}/${currentFreshness.source_count} current`,
      ok: currentFreshness.status === 'operational',
    },
    {
      icon: Activity,
      label: 'Prospective outcome tracking',
      value: `${practicalRoute.tracks.prospective_public_project_tracking.project_count.toLocaleString()} projects · ${practicalRoute.tracks.prospective_public_project_tracking.province_count} provinces`,
      ok: practicalRoute.gate_evaluation.prospective_baseline_implemented,
    },
    {
      icon: ShieldCheck,
      label: 'Deployment gate',
      value: gates.deployment.status,
      ok: gates.deployment.status === 'authorized',
    },
    {
      icon: Activity,
      label: 'Forecast authorization',
      value: 'Withheld pending calibration',
      ok: false,
    },
  ];

  return (
    <ResearchShell>
      <PageIntro
        eyebrow="System status"
        title="System status"
        description="Operational health is separate from research authorization. The website can be healthy while decision-grade model outputs remain deliberately withheld."
      />
      <section className="mx-auto max-w-[1200px] px-5 py-8 sm:px-8 lg:px-8">
        <div className="grid gap-4 md:grid-cols-2">
          {checks.map(({ icon: Icon, label, value, ok }) => (
            <article
              className="rounded-lg border border-line bg-white p-6"
              key={label}
            >
              <div className="flex items-start justify-between gap-4">
                <Icon className="size-5 text-brand" />
                <span
                  className={`rounded-full px-2.5 py-1 font-mono text-[9px] uppercase ${ok ? 'bg-workspace text-brand' : 'bg-workspace text-caution'}`}
                >
                  {ok ? 'ready' : 'withheld'}
                </span>
              </div>
              <p className="mt-8 text-xs text-subtle">{label}</p>
              <p className="mt-1 text-xl font-medium text-ink">{value}</p>
            </article>
          ))}
        </div>
        <div className="mt-6 grid gap-4 lg:grid-cols-[1.2fr_.8fr]">
          <div className="rounded-lg bg-surface p-6 text-ink">
            <CheckCircle2 className="size-6 text-brand" />
            <h2 className="mt-6 text-2xl font-medium">
              Release {release.manifest.version}
            </h2>
            <p className="mt-2 text-sm leading-6 text-subtle">
              Application, public evidence, graph scenarios, and reproducibility
              controls are available. Automated evidence changes enter review
              before publication.
            </p>
          </div>
          <div className="rounded-lg border border-caution/30 bg-workspace p-6 text-caution">
            <TriangleAlert className="size-6" />
            <h2 className="mt-6 text-lg font-medium">Research boundary</h2>
            <p className="mt-2 text-sm leading-6">
              No AI-attributable cost premium or project delay is authorized.
              This is a visible safeguard, not an outage.
            </p>
          </div>
        </div>
        <p className="mt-6 text-xs text-subtle">
          Last-good evidence is retained when a refresh fails or review is
          overdue. Frozen release vintage: {freshness.as_of_date}; freshness
          evaluated {currentFreshness.as_of_date}. Successful unchanged fetches
          advance verification only. Machine-readable status:{' '}
          <Link className="underline" href="/api/health">
            /api/health
          </Link>
        </p>
      </section>
      <SiteFooter />
    </ResearchShell>
  );
}
