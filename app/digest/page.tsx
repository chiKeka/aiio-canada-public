import { ArrowUpRight, BookOpen, CalendarDays } from 'lucide-react';

import {
  EvidencePill,
  PageIntro,
  SiteFooter,
  ResearchShell,
} from '@/components/site-shell';
import releaseData from '@/public/data/latest.json';
import reviewedDigest from '@/public/data/reviewed-digest.json';

export default function DigestPage() {
  const digest = reviewedDigest;
  return (
    <ResearchShell>
      <PageIntro
        eyebrow="Weekly evidence digest"
        title="Evidence digest"
        description="The digest records what changed in public sources and what it might mean for the research. It never changes a model value automatically; promotion requires validation, review and a versioned release."
      />
      <section className="mx-auto max-w-5xl px-5 py-8 sm:px-8 lg:py-8">
        <div className="mb-8 flex flex-col justify-between gap-4 border-b border-line pb-6 sm:flex-row sm:items-end">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen className="size-4 text-brand" />
              <span className="font-mono text-xs uppercase tracking-[0.13em] text-brand">
                Reviewed evidence edition
              </span>
            </div>
            <h2 className="mt-3 text-2xl font-medium tracking-[-0.03em]">
              Alberta evidence watch
            </h2>
          </div>
          <p
            data-testid="reviewed-digest-status"
            className="flex items-center gap-2 font-mono text-xs text-subtle"
          >
            <CalendarDays className="size-4" />
            {digest.edition_date} · {digest.status}
          </p>
        </div>
        <aside
          className="mb-6 rounded-lg border border-line bg-workspace p-4 text-sm leading-6 text-subtle"
          aria-label="Evidence review and frozen model vintage"
        >
          <p>
            Approved for this evidence digest through internal editorial review.
            This is not independent model validation or approval to change model
            parameters.
          </p>
          <p className="mt-2" data-testid="frozen-model-vintage">
            Frozen model release: {releaseData.manifest.version} · created{' '}
            {releaseData.manifest.created_at.slice(0, 10)} · embedded digest
            vintage {releaseData.digest.edition_date}. These frozen model inputs
            are separate from the reviewed evidence edition above.
          </p>
          <p className="mt-2">{digest.review_scope}</p>
        </aside>
        <div className="space-y-5">
          {digest.items.map((item) => (
            <article
              className="rounded-lg border border-line bg-surface p-5 sm:p-7"
              key={item.headline}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <EvidencePill status={item.evidence_status} />
                <span className="font-mono text-[10px] text-subtle">
                  {item.sources.map((source) => source.source_id).join(' · ')}
                </span>
              </div>
              <h2 className="mt-5 text-xl font-medium tracking-[-0.015em]">
                {item.headline}
              </h2>
              <div className="mt-5 grid gap-5 md:grid-cols-2">
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-brand">
                    Observed change
                  </p>
                  <p className="mt-2 text-sm leading-6 text-subtle">
                    {item.observed_change}
                  </p>
                </div>
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-caution">
                    Potential model implication
                  </p>
                  <p className="mt-2 text-sm leading-6 text-subtle">
                    {item.model_implication}
                  </p>
                </div>
              </div>
              <ul
                className="mt-6 flex flex-wrap gap-x-5 gap-y-3"
                aria-label={`Official sources for ${item.headline}`}
              >
                {item.sources.map((source) => (
                  <li key={`${source.source_id}-${source.source_url}`}>
                    <a
                      className="inline-flex items-center gap-1 text-xs font-medium text-brand hover:underline"
                      href={source.source_url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      {source.source_id}{' '}
                      <ArrowUpRight className="size-3" aria-hidden="true" />
                      <span className="sr-only"> (opens in a new tab)</span>
                    </a>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
        <p className="mt-8 rounded-lg border border-line bg-workspace p-4 text-sm text-subtle">
          Evidence-digest approval does not automatically change model values.
          Any proposed model promotion requires validation, the applicable
          review gate and a separate versioned release.
        </p>
      </section>
      <SiteFooter />
    </ResearchShell>
  );
}
