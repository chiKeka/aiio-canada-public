import Link from 'next/link';
import { publicReviews } from '@/lib/public-presentation.mjs';
import practicalRoute from '@/data/model-runs/practical_evidence_route_current.json';
import { CheckCircle2, GitBranch, Layers3, ShieldCheck } from 'lucide-react';

import {
  EvidencePill,
  PageIntro,
  SiteFooter,
  ResearchShell,
} from '@/components/site-shell';
import releaseData from '@/public/data/latest.json';
import historicalEnvelope from '@/data/model-runs/alberta_bcpi_historical_envelope_v0.1.json';
import historicalAnalogMatrix from '@/data/model-runs/alberta_project_historical_analog_matrix_v0.1.json';
import referenceCostReview from '@/data/model-runs/alberta_reference_cost_review_package_v0.1.json';
import programGates from '@/data/governance/program-gates.json';
import informationSectorCapex from '@/data/model-runs/information_sector_construction_capex_screen_v0.1.json';
import cmaReferenceBaseline from '@/data/model-runs/vancouver_toronto_montreal_bcpi_reference_baseline_v0.1.json';
import regionalMacroControls from '@/data/model-runs/regional_macro_controls_canada_v0.1.json';
import provinceLinkedBaseline from '@/data/model-runs/bc_on_qc_province_linked_reference_baseline_v0.1.json';
import aiCapexLedger from '@/data/model-runs/alberta_ai_capex_announcement_ledger_v0.1.json';
import panelPreflight from '@/data/model-runs/ai_attribution_panel_preflight_v0.1.json';
import pspeLineage from '@/data/model-runs/pspe_method_lineage_v0.1.json';

const methodSteps = [
  [
    '01',
    'Register',
    'Identify an authoritative public source and record its publisher, URL, vintage, access method, licence note and update frequency.',
  ],
  [
    '02',
    'Retrieve',
    'Archive the raw response by content hash and add a retrieval manifest. Revisions become new records.',
  ],
  [
    '03',
    'Normalize',
    'Transform into stable observations with units, geography, period, source ID, quality flags and evidence status.',
  ],
  [
    '04',
    'Model',
    'Apply a sealed scenario to a typed graph. Lag, sign, magnitude range and absorption remain explicit on every edge; state retention is explicit on nodes.',
  ],
  [
    '05',
    'Validate',
    'Run identity, persistence, sign, lag, mass-bound, additivity, cycle, sensitivity, determinism and golden-release tests.',
  ],
  [
    '06',
    'Release',
    'Website, downloads and workbook consume the same immutable manifest and file hashes.',
  ],
];

export default function MethodsPage() {
  const reviewerStates = Object.entries(
    publicReviews(programGates.independent_review),
  );
  const evidenceScreens = releaseData as typeof releaseData & {
    material_cost_screen?: { limitations: string[] };
    public_project_exposure?: { limitations: string[] };
    power_evidence?: { limitations: string[] };
  };
  const limitations = [
    ...releaseData.scenario.limitations,
    ...releaseData.labour_pressure.limitations,
    ...(evidenceScreens.material_cost_screen?.limitations ?? []),
    ...(evidenceScreens.public_project_exposure?.limitations ?? []),
    ...(evidenceScreens.power_evidence?.limitations ?? []),
    ...historicalEnvelope.limitations,
    ...historicalAnalogMatrix.limitations,
    ...informationSectorCapex.limitations,
    ...cmaReferenceBaseline.limitations,
    ...regionalMacroControls.limitations,
    ...provinceLinkedBaseline.limitations,
    ...aiCapexLedger.limitations,
  ];
  return (
    <ResearchShell>
      <div className="border-b border-line bg-brand-soft px-8 py-3 text-sm">
        <Link href="/construction" className="font-medium text-brand underline">
          Construction demand workspace: quarterly scenarios, benchmarks,
          formulas and presentation downloads
        </Link>
      </div>
      <PageIntro
        eyebrow="Research method"
        title="Methods & limitations"
        description="The graph is the analysis engine inside a larger reproducible program. Source records, transformations, scenarios, tests and publication artifacts are versioned so a reader can follow a result back to its origin."
      />
      <section className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {methodSteps.map(([number, title, text]) => (
            <article
              className="rounded-lg border border-line bg-surface p-5"
              key={number}
            >
              <span className="font-mono text-xs text-brand">{number}</span>
              <h2 className="mt-5 text-lg font-medium">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-subtle">{text}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="border-y border-line bg-workspace">
        <div className="mx-auto grid max-w-[1440px] gap-8 px-5 py-10 sm:px-8 lg:grid-cols-[.8fr_1.2fr] lg:px-8">
          <div>
            <div className="flex items-center gap-2 text-subtle">
              <GitBranch className="size-4" />
              <span className="font-mono text-xs uppercase tracking-[0.14em]">
                E2 panel acquisition preflight
              </span>
            </div>
            <h2 className="mt-4 text-2xl font-medium tracking-[-0.025em]">
              Scope can be planned before evidence is eligible.
            </h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-subtle">
              The preflight binds ten evidence receipts to five candidate CMAs
              and every locked treatment/outcome field. It creates no partial
              observations and runs no estimator.
            </p>
          </div>
          <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ['Candidate CMAs', panelPreflight.candidate_scope.region_count],
              [
                'Asset classes',
                panelPreflight.candidate_scope.asset_class_count,
              ],
              [
                'Fields queued',
                panelPreflight.field_gap_summary.required_field_instance_count,
              ],
              [
                'Eligible panel rows',
                panelPreflight.current_eligibility.assembled_panel_row_count,
              ],
            ].map(([label, value]) => (
              <div
                className="rounded-lg border border-line bg-white p-4"
                key={label}
              >
                <dt className="text-xs text-subtle">{label}</dt>
                <dd className="mt-2 font-mono text-2xl text-ink">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>
      <section className="border-y border-caution/30 bg-workspace">
        <div className="mx-auto max-w-[1440px] px-5 py-10 sm:px-8 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[.8fr_1.2fr]">
            <div>
              <div className="flex items-center gap-2 text-caution">
                <ShieldCheck className="size-5" />
                <span className="font-mono text-xs uppercase tracking-[0.14em]">
                  Independent modelling gate
                </span>
              </div>
              <h2 className="mt-4 text-2xl font-medium tracking-[-0.025em]">
                The packet is ready. The verdict is not.
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-caution">
                The Alberta E1 review instrument hash-locks the model artifact,
                implementation, tests and claim boundaries. It cannot authorize
                publication itself, and a future pass would apply only to an
                individually validated reference-index horizon.
              </p>
              <dl className="mt-6 grid grid-cols-3 gap-3">
                {[
                  ['Locked inputs', referenceCostReview.input_manifest.length],
                  [
                    'Required criteria',
                    referenceCostReview.required_criteria.length,
                  ],
                  [
                    'Eligible horizons',
                    referenceCostReview.facts_to_reconcile.gate_passing_horizons
                      .length,
                  ],
                ].map(([label, value]) => (
                  <div
                    className="rounded-lg border border-caution/30 bg-surface p-3"
                    key={label}
                  >
                    <dt className="text-xs text-caution">{label}</dt>
                    <dd className="mt-1 font-mono text-xl text-caution">
                      {value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
            <div className="space-y-3">
              {reviewerStates.map(([reviewer, gate]) => (
                <article
                  className="rounded-lg border border-caution/30 bg-surface p-4"
                  key={reviewer}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="font-mono text-xs uppercase tracking-[0.12em] text-caution">
                      {reviewer} review
                    </h3>
                    <span className="rounded-full border border-caution/30 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.1em] text-caution">
                      {gate.status}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-caution">
                    {gate.reason}
                  </p>
                </article>
              ))}
              <p className="text-xs leading-5 text-caution">
                No reviewer output, approval or replacement parameter is
                inferred from tool availability. All public projection,
                project-cost and AI-attribution fields remain withheld.
              </p>
            </div>
          </div>
        </div>
      </section>
      <section className="bg-surface text-ink">
        <div className="mx-auto grid max-w-[1440px] gap-10 px-5 py-8 sm:px-8 lg:grid-cols-[.7fr_1.3fr] lg:px-8 lg:py-8">
          <div>
            <div className="flex items-center gap-2 text-brand">
              <GitBranch className="size-4" />
              <span className="font-mono text-xs uppercase tracking-[0.14em]">
                PSPE/S3 adaptation
              </span>
            </div>
            <h2 className="mt-4 text-2xl font-medium tracking-[-0.035em]">
              Signed paths with explicit limits.
            </h2>
            <p className="mt-4 text-sm leading-6 text-subtle">
              The local Git-backed PSPE mathematics repository contributes the
              documented concepts of directed graph propagation, damping and
              path interpretation. AIIO independently implements five bounded
              mappings and adds evidence lineage, frozen edge semantics,
              temporal lags, retained states, scenario isolation and release
              controls.
            </p>
            <dl className="mt-6 grid grid-cols-3 gap-2">
              <div className="rounded-lg border border-line bg-workspace p-3">
                <dt className="text-[9px] text-subtle">Mapped concepts</dt>
                <dd className="mt-1 font-mono text-xl text-brand">
                  {pspeLineage.mapping_count}
                </dd>
              </div>
              <div className="rounded-lg border border-line bg-workspace p-3">
                <dt className="text-[9px] text-subtle">Source receipt</dt>
                <dd className="mt-1 font-mono text-xs text-brand">
                  hash-locked
                </dd>
              </div>
              <div className="rounded-lg border border-line bg-workspace p-3">
                <dt className="text-[9px] text-subtle">Method repo</dt>
                <dd className="mt-1 font-mono text-xs text-brand">
                  commit locked
                </dd>
              </div>
            </dl>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              'Dense-graph centrality is not used as a proxy for importance.',
              'Prior notes describe a conserved-mass origin ranking; the separate engine source is unavailable and is not claimed as verified, reproduced or used.',
              'Positive and negative paths are retained separately.',
              'Absorption and retention receive explicit sensitivity tests.',
              'Raw pressure is transformed as raw ÷ (1 + raw) for bounded public display only.',
              'CAD pressure and MW power quantities use separate artifacts.',
              'Historical index envelopes are descriptive; predictive and causal calibration remain gated.',
              'Historical project analogs preserve complete past trajectories; their dollar equivalents are stress tests, not forecasts or AI premiums.',
              'The AI-capex ledger tracks reported estimates and publisher stages without stage weighting; zero records currently authorize realized treatment onset or dose.',
              'The panel preflight assigns all 27 authorizing field instances to acquisition tasks but assembles zero rows until every required treatment and outcome gate passes.',
              'Bayesian, continuous-time ODE, curvature and other later PSPE curriculum layers are not claimed as implemented.',
            ].map((item) => (
              <div
                className="flex gap-3 rounded-lg border border-line bg-workspace p-4 text-sm leading-5 text-subtle"
                key={item}
              >
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8">
        <div className="grid gap-8 lg:grid-cols-2">
          <div>
            <div className="flex items-center gap-2">
              <Layers3 className="size-4 text-brand" />
              <h2 className="text-xl font-medium">Epistemic contract</h2>
            </div>
            <div className="mt-5 space-y-3">
              {[
                ['observed', 'Directly reported by a public source.'],
                ['inferred', 'Derived through a disclosed transformation.'],
                [
                  'assumed',
                  'Selected parameter with rationale and sensitivity range.',
                ],
                [
                  'scenario',
                  'Counterfactual input or output; never a forecast.',
                ],
              ].map(([status, text]) => (
                <div
                  className="flex items-start gap-3 rounded-lg border border-line bg-surface p-4"
                  key={status}
                >
                  <EvidencePill status={status} />
                  <p className="text-sm text-subtle">{text}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-lg border border-caution/30 bg-workspace p-6">
            <div className="flex items-center gap-2 text-caution">
              <ShieldCheck className="size-5" />
              <h2 className="text-xl font-medium">Current model limitations</h2>
            </div>
            <p className="mt-3 text-sm leading-6 text-caution">
              Scenario and evidence-screen boundaries are published together
              here; none is a forecast.
            </p>
            <ul className="mt-5 space-y-3">
              {[...new Set(limitations)].map((item) => (
                <li
                  className="flex gap-3 text-sm leading-6 text-caution"
                  key={item}
                >
                  <span className="mt-2 size-1.5 shrink-0 rounded-full bg-caution" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
      <section
        id="planning-gates"
        className="mx-auto max-w-[1440px] scroll-mt-24 px-5 py-8 sm:px-8"
      >
        <h2 className="text-2xl font-semibold">Planning validation gates</h2>
        <p className="mt-3 text-sm">
          {practicalRoute.proxy_planning_validation.passed_check_count} of{' '}
          {practicalRoute.proxy_planning_validation.check_count} checks pass.
          Each remaining check identifies the evidence needed; this count is not
          a confidence score.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {practicalRoute.proxy_planning_validation.checks.map((check) => (
            <article
              className="rounded-lg border border-line bg-surface p-4"
              key={check.id}
            >
              <h3 className="font-semibold">
                {check.id.replaceAll('_', ' ')} ·{' '}
                {check.status.replaceAll('_', ' ')}
              </h3>
              <p className="mt-2 text-sm">{check.finding}</p>
              {check.next_step ? (
                <p className="mt-2 text-sm text-subtle">
                  Next: {check.next_step}
                </p>
              ) : null}
            </article>
          ))}
        </div>
      </section>
      <SiteFooter />
    </ResearchShell>
  );
}
