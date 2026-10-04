import Link from 'next/link';
import { ScenarioLab } from '@/components/scenario-lab';
import {
  EvidencePill,
  PageIntro,
  SiteFooter,
  ResearchShell,
} from '@/components/site-shell';
import releaseData from '@/public/data/latest.json';

type PowerEvidence = {
  requested_load: {
    latest_application_period: string;
    latest_requested_load_mw: number;
  };
  phase1: {
    allocated_mw: number;
  };
  transmission_boundary: {
    additional_transmission_required_for_50b_counterfactual_mw: number | null;
  };
};

export default async function ScenarioPage({
  searchParams,
}: {
  searchParams: Promise<{ power?: string; variant?: string }>;
}) {
  const params = await searchParams;
  const initialVariant = [
    'staggered',
    'front_loaded',
    'constrained_delivery',
    'high_local_capture',
  ].includes(params.variant ?? '')
    ? (params.variant as
        | 'staggered'
        | 'front_loaded'
        | 'constrained_delivery'
        | 'high_local_capture')
    : 'staggered';
  const initialPower = ['low', 'central', 'high'].includes(params.power ?? '')
    ? (params.power as 'low' | 'central' | 'high')
    : 'central';
  const evidence = (
    releaseData as typeof releaseData & { power_evidence?: PowerEvidence }
  ).power_evidence;
  return (
    <ResearchShell>
      <div className="border-b border-line bg-brand-soft px-8 py-3 text-sm">
        <Link href="/construction" className="font-medium text-brand underline">
          Construction demand workspace: quarterly scenarios, benchmarks,
          formulas and presentation downloads
        </Link>
      </div>
      <PageIntro
        eyebrow="Scenario laboratory"
        title="Scenario lab"
        description="Compare four versioned stress cases that isolate timing and local capture while keeping the total program, component mix and graph fixed. Each choice is a reproducible structural run—not a forecast, finding, cost-escalation estimate or project-delay prediction."
      />
      {evidence ? <ObservedPowerBoundary evidence={evidence} /> : null}
      <section className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8">
        <ScenarioLab
          initialPower={initialPower}
          initialVariant={initialVariant}
        />
      </section>
      <SiteFooter />
    </ResearchShell>
  );
}

function ObservedPowerBoundary({ evidence }: { evidence: PowerEvidence }) {
  const transmission =
    evidence.transmission_boundary
      .additional_transmission_required_for_50b_counterfactual_mw;
  return (
    <section className="border-b border-line bg-white">
      <div className="mx-auto max-w-[1440px] px-5 py-10 sm:px-8 lg:px-8">
        <div className="mb-6 flex flex-wrap items-center gap-2">
          <EvidencePill status="observed" />
          <span className="font-mono text-xs text-subtle">
            AESO-published quantities · independently checked against archived
            sources
          </span>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <PowerMetric
            label={`Requested load · ${evidence.requested_load.latest_application_period}`}
            value={`${(evidence.requested_load.latest_requested_load_mw / 1_000).toFixed(1)} GW`}
            note="Requests, not contracts or a forecast"
          />
          <PowerMetric
            label="Phase 1 allocated limit"
            value={`${(evidence.phase1.allocated_mw / 1_000).toFixed(1)} GW`}
            note="Executed load contracts; not connected or in-service load"
          />
          <PowerMetric
            label="$50B additional transmission"
            value={transmission === null ? 'Unknown' : `${transmission} MW`}
            note="Requires locations and system studies"
          />
        </div>
        <div className="mt-4 rounded-lg border border-caution/30 bg-workspace p-4 text-sm leading-6 text-caution">
          Requested load, allocated limits, executed contracts, connected load,
          and forecasts are different quantities. AESO&apos;s statement that no
          new transmission system reinforcement was required applies only to its
          1.2 GW interim approach through 2028 on the existing transmission
          system. It does not establish transmission needs for remaining
          requests, Phase 2, other locations, or the separate $50B
          counterfactual.
        </div>
      </div>
    </section>
  );
}

function PowerMetric({
  label,
  note,
  value,
}: {
  label: string;
  note: string;
  value: string;
}) {
  return (
    <article className="rounded-lg border border-line bg-surface p-5">
      <p className="font-mono text-2xl font-semibold text-brand">{value}</p>
      <h2 className="mt-3 text-sm font-medium">{label}</h2>
      <p className="mt-1 text-xs text-subtle">{note}</p>
    </article>
  );
}
