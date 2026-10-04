'use client';

import { useMemo, useState } from 'react';
import { WorkspaceScrollRegion } from '@/components/workspace-scroll-region';
import Link from 'next/link';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Building2,
  CircleCheck,
  CircleX,
  ChevronRight,
  Clock3,
  Database,
  GitBranch,
  LockKeyhole,
  MapPin,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import releaseData from '@/public/data/latest.json';
import attributionReadiness from '@/data/model-runs/ai_attribution_identification_readiness_v0.1.json';
import panelPreflight from '@/data/model-runs/ai_attribution_panel_preflight_v0.1.json';
import treatmentSourceFeasibility from '@/data/model-runs/ai_attribution_treatment_source_feasibility_v0.1.json';
import buildingInvestmentControls from '@/data/model-runs/building_investment_controls_canada_v0.1.json';
import regionalMacroControls from '@/data/model-runs/regional_macro_controls_canada_v0.1.json';
import procurementOutcomeFeasibility from '@/data/model-runs/canadabuys_construction_outcome_feasibility_v0.1.json';
import edmontonPermitProxy from '@/data/model-runs/edmonton_data_centre_permit_proxy_v0.1.json';
import auditedProjectOutcomes from '@/data/model-runs/oago_audited_project_outcomes_v0.1.json';
import quebecProjectRevisions from '@/data/model-runs/quebec_pqi_authorized_project_revisions_v0.1.json';
import quebecFullArchive from '@/data/model-runs/quebec_pqi_full_archive_longitudinal_v0.1.json';
import quebecParserReview from '@/data/model-runs/quebec_pqi_parser_review_package_v0.1.json';
import canadaCoverage from '@/data/model-runs/canada_cross_domain_coverage_v0.1.json';
import {
  ResearchShell,
  PageIntro,
  SiteFooter,
  SectionNavigation,
} from '@/components/site-shell';
import { boundedDisplayScore } from '@/lib/decision-analysis';

const tradeTones = ['bg-brand', 'bg-[#446c99]', 'bg-caution', 'bg-[#73838f]'];

const researchLayers = [
  {
    icon: Database,
    title: 'Evidence pipeline',
    text: 'Capex announcements, construction costs, labour-demand signals, workforce stock and power scenarios—with source and retrieval history.',
  },
  {
    icon: GitBranch,
    title: 'Propagation engine',
    text: 'A signed, typed graph traces demand through trades, building materials, construction-cost signals and public-delivery pressure.',
  },
  {
    icon: Activity,
    title: 'Scenario laboratory',
    text: 'Test investment size, timing and composition without presenting scenarios as forecasts.',
  },
];

const coverageColumns = [
  ['labour', 'Labour'],
  ['materials', 'Materials'],
  ['building_investment', 'Investment'],
  ['regional_macro', 'Macro'],
  ['public_projects', 'Projects'],
  ['power_planning', 'Power'],
  ['information_sector_capex', 'Sector capex'],
] as const;

const treatmentGateLabels: Record<string, string> = {
  ai_or_data_centre_specific: 'AI / data centre',
  construction_activity_specific: 'Construction',
  realized_not_intended: 'Realized',
  region_or_project_linkable: 'Linked',
  quarterly_or_finer: 'Quarterly+',
  publicly_retrievable: 'Public',
  revision_provenance_available: 'Revisions',
};

const attributionDomainMeta = [
  {
    id: 'REALIZED_AI_CONSTRUCTION_TREATMENT',
    label: 'AI construction treatment',
    role: 'Authorizing treatment',
    summary: `The Edmonton screen identifies ${edmontonPermitProxy.data_centre_candidate_count} permit candidates, but no explicit AI references or candidate occupancy dates. Realized spend or construction labour hours are still required.`,
  },
  {
    id: 'PUBLIC_PROJECT_COST_OUTCOMES',
    label: 'Public cost outcome',
    role: 'Authorizing outcome',
    summary: `CanadaBuys linkages and ${auditedProjectOutcomes.coverage_summary.named_completed_project_count} audited named cases remain incomplete. Quebec now contributes ${quebecProjectRevisions.coverage_summary.cost_revision_chain_reconciled_project_count} reconciled authorized-cost revision chains plus ${quebecFullArchive.snapshot_date_count} complete-catalog selection snapshots, making this a candidate domain—but price basis, final outturn and multi-region coverage remain missing.`,
  },
  {
    id: 'PUBLIC_PROJECT_SCHEDULE_OUTCOMES',
    label: 'Public schedule outcome',
    role: 'Authorizing outcome',
    summary: `The audited intake supplies ${auditedProjectOutcomes.coverage_summary.exact_day_substantial_completion_pair_count} exact-day planned/actual pair. Quebec adds ${quebecProjectRevisions.coverage_summary.schedule_revision_chain_reconciled_project_count} reconciled month-precision authorized completion chains and ${quebecFullArchive.publisher_declared_retirement_disappearance_event_count} source-declared retirement transitions, but those transitions are not audited completions and exact actual histories remain missing.`,
  },
  {
    id: 'REGIONAL_CONSTRUCTION_ACTIVITY_CONTROLS',
    label: 'Regional activity controls',
    role: 'Control domain',
    summary:
      'Quarterly building investment and construction prices are available as controls, not as an AI treatment or public-project outcome.',
  },
];

const attributionDomains = attributionDomainMeta.map((meta) => ({
  ...meta,
  domain: attributionReadiness.domain_status.find(
    (domain) => domain.domain_id === meta.id,
  ),
}));

export function ObservatoryDashboard() {
  const [capex, setCapex] = useState(50);
  const [years, setYears] = useState(10);

  const scenario = useMemo(() => {
    const annual = capex / years;
    const localConstruction =
      capex *
      releaseData.scenario.modelled_component_share *
      releaseData.scenario.local_capture_share;
    const outsideGraph =
      capex * (1 - releaseData.scenario.modelled_component_share);
    const scale = (capex / 50) * (10 / years);
    const baseRawPressure = Math.max(
      ...releaseData.scenario.trade_pressure_order.map(
        (trade) =>
          (trade as typeof trade & { raw_central?: number }).raw_central ??
          trade.central,
      ),
    );

    return {
      annual,
      localConstruction,
      outsideGraph,
      scale,
      pressure: boundedDisplayScore(baseRawPressure * scale),
    };
  }, [capex, years]);

  const tradeMix = releaseData.scenario.trade_pressure_order
    .slice(0, 4)
    .map((trade, index) => ({
      name: trade.label,
      rawScore:
        (trade as typeof trade & { raw_central?: number }).raw_central ??
        trade.central,
      tone: tradeTones[index],
    }));
  const maxTradeScore = Math.max(
    ...tradeMix.map((trade) =>
      boundedDisplayScore(trade.rawScore * scenario.scale),
    ),
    0.01,
  );

  return (
    <ResearchShell>
      <PageIntro
        eyebrow="Research workspace"
        title="Research observatory"
        description="Inspect the evidence, explore structural scenarios and track research readiness across Canadian infrastructure markets."
      />
      <SectionNavigation
        items={[
          ['top', 'Sandbox'],
          ['pressure', 'Pressure paths'],
          ['identification-gate', 'Research readiness'],
          ['canada-coverage', 'Canada coverage'],
        ]}
      />
      <section
        id="top"
        className="relative border-b border-line bg-surface text-ink"
      >
        <div className="relative mx-auto grid max-w-[1440px] gap-6 px-5 py-8 sm:px-8 sm:py-8 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:px-8 lg:py-8">
          <div className="inline-flex items-center gap-2 rounded-lg border border-caution/30 bg-caution-soft px-3 py-2 text-xs font-semibold text-caution xl:col-span-2">
            <AlertTriangle className="size-4" /> Counterfactual structural
            diagnostic · not a finding or forecast
          </div>
          <div className="max-w-4xl">
            <div className="mb-7 flex flex-wrap items-center gap-2">
              <Badge className="border-line bg-workspace text-brand">
                Alberta pilot
              </Badge>
              <Badge
                variant="outline"
                className="border-line bg-white text-subtle"
              >
                Release {releaseData.manifest.version}
              </Badge>
              <span className="ml-1 inline-flex items-center gap-1.5 text-xs text-subtle">
                <span className="size-1.5 rounded-full bg-brand" /> Canada
                expansion plan documented
              </span>
            </div>
            <p className="mb-4 font-mono text-xs font-semibold uppercase tracking-[0.16em] text-brand">
              Framing question
            </p>
            <h2 className="text-xl font-semibold leading-7 text-ink">
              Where could AI capital spending create{' '}
              <span className="">pressure</span> on public infrastructure
              delivery?
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-subtle">
              An uncalibrated research prototype for testing possible mechanisms
              through labour, materials and project schedules—beginning in
              Alberta, then expanding across Canada. It does not measure
              realized effects.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Button
                size="lg"
                className="h-11 bg-brand px-4 text-white hover:bg-brand/90"
                onClick={() =>
                  document
                    .querySelector('#scenario')
                    ?.scrollIntoView({ behavior: 'smooth' })
                }
              >
                Explore Alberta scenario <ArrowRight data-icon="inline-end" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="h-11 border-line bg-white px-4 text-brand hover:border-line hover:bg-workspace hover:text-brand"
                onClick={() =>
                  document
                    .querySelector('#method')
                    ?.scrollIntoView({ behavior: 'smooth' })
                }
              >
                Read the research method
              </Button>
            </div>
          </div>

          <Card
            id="scenario"
            className="self-start rounded-lg border border-line bg-surface shadow-none ring-0"
          >
            <CardHeader className="border-b border-line pb-4">
              <CardTitle className="flex items-center gap-2 text-ink">
                <Sparkles className="size-4 text-caution" /> Alberta
                counterfactual sandbox
              </CardTitle>
              <CardDescription>
                Explore a linear interface interpolation of the published $50B
                diagnostic.
              </CardDescription>
              <CardAction>
                <Badge
                  variant="outline"
                  className="border-caution/30 bg-caution-soft text-caution"
                >
                  Uncalibrated · not a forecast
                </Badge>
              </CardAction>
            </CardHeader>
            <CardContent className="space-y-7 pt-1">
              <label className="block">
                <span className="mb-3 flex items-center justify-between text-xs font-semibold uppercase tracking-[0.08em] text-subtle">
                  AI infrastructure investment
                  <output className="font-mono text-base tracking-normal text-subtle">
                    ${capex}B
                  </output>
                </span>
                <input
                  aria-label="AI infrastructure investment in billions of dollars"
                  className="scenario-range w-full"
                  max="100"
                  min="10"
                  onChange={(event) => setCapex(Number(event.target.value))}
                  step="5"
                  type="range"
                  value={capex}
                />
                <span className="mt-2 flex justify-between font-mono text-[10px] text-subtle">
                  <span>$10B</span>
                  <span>$100B</span>
                </span>
              </label>
              <div>
                <span className="mb-3 block text-xs font-semibold uppercase tracking-[0.08em] text-subtle">
                  Delivery window
                </span>
                <div className="grid grid-cols-3 gap-2">
                  {[5, 10, 15].map((option) => (
                    <button
                      aria-pressed={years === option}
                      className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${years === option ? 'border-brand/30 bg-workspace text-brand' : 'border-line bg-white text-subtle hover:border-line'}`}
                      key={option}
                      onClick={() => setYears(option)}
                      type="button"
                    >
                      {option} years
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 border-t border-line pt-5">
                <Metric
                  label="Annual flow"
                  value={`$${scenario.annual.toFixed(1)}B`}
                />
                <Metric
                  label="Local build flow"
                  value={`$${scenario.localConstruction.toFixed(1)}B`}
                />
                <Metric
                  label="Outside graph"
                  value={`$${scenario.outsideGraph.toFixed(1)}B`}
                />
              </div>
            </CardContent>
            <CardFooter className="border-line bg-workspace text-xs leading-5 text-subtle">
              Controls are an interface interpolation, not a new model run.
              Scores are bounded display indices—not percentages, probabilities,
              measured effects or delay estimates. The power overlay is kept
              separate in the Scenario Lab.
            </CardFooter>
          </Card>
        </div>
      </section>

      <section id="pressure" className="bg-surface text-ink">
        <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8">
          <div className="flex flex-col justify-between gap-5 border-b border-line pb-8 md:flex-row md:items-end">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.16em] text-brand">
                Propagation preview
              </p>
              <h2 className="mt-3 max-w-2xl text-2xl font-medium tracking-[-0.035em] sm:text-2xl">
                Follow pressure from investment to public delivery.
              </h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-subtle">
              The graph is the analysis engine: each link has a mechanism,
              direction, time lag, geography and evidence grade.
            </p>
          </div>

          <div className="grid gap-6 py-8 lg:grid-cols-[1.1fr_.9fr]">
            <div className="grid min-h-[320px] grid-cols-[1fr_auto_1fr_auto_1fr] items-center gap-2 rounded-lg border border-line bg-surface p-5 sm:p-8">
              <FlowNode
                icon={Building2}
                eyebrow="Shock"
                label={`$${capex}B AI capex`}
              />
              <FlowArrow />
              <FlowNode
                icon={Zap}
                eyebrow="Constraint"
                label="Trades + materials"
                active
              />
              <FlowArrow />
              <FlowNode
                icon={Clock3}
                eyebrow="Exposure"
                label="Public schedules"
              />
            </div>

            <Card className="border-line bg-surface text-ink ring-0">
              <CardHeader>
                <CardTitle>Illustrative trade pressure</CardTitle>
                <CardDescription className="text-subtle">
                  Relative signal under the selected scenario
                </CardDescription>
                <CardAction>
                  <span className="font-mono text-xs text-caution">
                    score {scenario.pressure.toFixed(2)}
                  </span>
                </CardAction>
              </CardHeader>
              <CardContent className="space-y-5">
                {tradeMix.map((trade, index) => {
                  const displayed = boundedDisplayScore(
                    trade.rawScore * scenario.scale,
                  );
                  const scaled = Math.min(
                    98,
                    Math.round((displayed / maxTradeScore) * 100),
                  );
                  return (
                    <div key={trade.name}>
                      <div className="mb-2 flex justify-between text-xs">
                        <span className="text-subtle">{trade.name}</span>
                        <span className="font-mono text-subtle">
                          0{index + 1}
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-workspace">
                        <div
                          className={`h-full rounded-full ${trade.tone}`}
                          style={{ width: `${scaled}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
              <CardFooter className="border-line bg-workspace text-xs text-subtle">
                Published v0.2 ordering is an uncalibrated structural
                diagnostic. Weights, retention and denominators remain
                assumptions pending occupational calibration.
              </CardFooter>
            </Card>
          </div>
        </div>
      </section>

      <section id="method" className="bg-workspace">
        <div className="mx-auto max-w-[1440px] px-5 py-14 sm:px-8 lg:px-8 lg:py-8">
          <div className="grid gap-12 lg:grid-cols-[.72fr_1.28fr]">
            <div>
              <div className="flex items-center gap-2 text-brand">
                <ShieldCheck className="size-4" />
                <span className="font-mono text-xs font-semibold uppercase tracking-[0.14em]">
                  Research architecture
                </span>
              </div>
              <h2 className="mt-4 text-2xl font-medium tracking-[-0.045em] text-ink">
                One observatory.
                <br />
                Three connected layers.
              </h2>
              <p className="mt-5 max-w-md text-sm leading-6 text-subtle">
                The website and workbook are publication surfaces. The
                underlying source register, graph model and scenario protocol
                remain the system of record.
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {researchLayers.map((layer, index) => (
                <Card
                  key={layer.title}
                  className="border-line bg-surface ring-0"
                >
                  <CardHeader>
                    <span className="mb-6 grid size-10 place-items-center rounded-full bg-workspace text-brand">
                      <layer.icon className="size-4" />
                    </span>
                    <p className="font-mono text-[10px] text-subtle">
                      0{index + 1}
                    </p>
                    <CardTitle className="text-ink">{layer.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm leading-6 text-subtle">
                      {layer.text}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section
        id="identification-gate"
        className="border-y border-line bg-surface"
      >
        <div className="mx-auto max-w-[1440px] px-5 py-14 sm:px-8 lg:px-8 lg:py-8">
          <div className="grid gap-8 lg:grid-cols-[minmax(0,.78fr)_minmax(520px,1.22fr)] lg:items-end">
            <div>
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.15em] text-brand">
                Causal identification gate
              </p>
              <h2 className="mt-4 max-w-2xl text-balance text-2xl font-medium tracking-[-0.045em] text-ink sm:text-2xl">
                The model may explain pressure before it may claim an AI effect.
              </h2>
            </div>
            <div className="border-l-2 border-caution/30 pl-5">
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-caution">
                Current publication state · withheld
              </p>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-subtle">
                {attributionReadiness.publication_authorization.reason} Cost
                escalation and schedule-delay fields remain null—not zero.
              </p>
            </div>
          </div>

          <div className="mt-10 grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(380px,.75fr)]">
            <div
              className="grid gap-3 sm:grid-cols-2"
              aria-label="Causal attribution evidence domains"
            >
              {attributionDomains.map(
                ({ domain, id, label, role, summary }) => (
                  <AttributionDomainCard
                    key={id}
                    label={label}
                    role={role}
                    sourceCount={domain?.source_ids.length ?? 0}
                    status={domain?.status ?? 'not_assessed'}
                    summary={summary}
                  />
                ),
              )}
            </div>

            <article className="rounded-lg border border-line bg-white p-6 sm:p-7">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-subtle">
                    Preregistered analysis contract
                  </p>
                  <h3 className="mt-2 text-xl font-medium tracking-[-0.025em] text-ink">
                    Staggered group-time effect design
                  </h3>
                </div>
                <Badge
                  variant="outline"
                  className="border-caution/30 bg-caution-soft text-caution"
                >
                  Not assessed
                </Badge>
              </div>

              <dl className="mt-7 grid grid-cols-2 gap-x-5 gap-y-6 border-y border-line py-6">
                <ContractMetric
                  label="Pre-treatment history"
                  value={`${attributionReadiness.design.minimum_pre_treatment_quarters} quarters`}
                />
                <ContractMetric
                  label="Post-treatment history"
                  value={`${attributionReadiness.design.minimum_post_treatment_quarters} quarters`}
                />
                <ContractMetric
                  label="Treated regions"
                  value={`At least ${attributionReadiness.design.minimum_treated_regions}`}
                />
                <ContractMetric
                  label="Controls per cohort"
                  value={`At least ${attributionReadiness.design.minimum_control_regions_per_cohort}`}
                />
              </dl>

              <div className="mt-6 space-y-4">
                <div>
                  <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-subtle">
                    Diagnostics required
                  </p>
                  <p className="mt-2 text-sm leading-6 text-subtle">
                    Pre-trend equivalence, placebo dates, a negative-control
                    outcome, and leave-one-region and leave-one-event
                    sensitivity.
                  </p>
                </div>
                <div className="rounded-lg bg-workspace p-4">
                  <p className="text-sm font-medium text-ink">Graph boundary</p>
                  <p className="mt-1 text-xs leading-5 text-subtle">
                    {attributionReadiness.graph_role}
                  </p>
                </div>
              </div>
            </article>
          </div>

          <TreatmentSourceGateboard />

          <article className="mt-5 overflow-hidden rounded-lg border border-line bg-surface text-ink">
            <div className="grid gap-8 border-b border-line p-6 lg:grid-cols-[minmax(0,.78fr)_minmax(520px,1.22fr)] lg:items-end sm:p-8">
              <div>
                <div className="flex items-center gap-2 text-brand">
                  <GitBranch className="size-4" />
                  <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em]">
                    Panel acquisition preflight · operational
                  </p>
                </div>
                <h3 className="mt-3 text-2xl font-medium tracking-[-0.035em] sm:text-2xl">
                  The candidate map is large enough. The evidence is not yet
                  eligible.
                </h3>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-subtle">
                  Eleven hash-locked evidence receipts are assigned to every
                  treatment and outcome gap. Candidate regions are planning
                  scope only; no partial row enters an estimator.
                </p>
              </div>
              <dl className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-5">
                <ContractMetric
                  inverted
                  label="Candidate CMAs"
                  value={panelPreflight.candidate_scope.region_count.toString()}
                />
                <ContractMetric
                  inverted
                  label="Treated eligible"
                  value={`${panelPreflight.current_eligibility.authorizing_treated_region_count} / ${panelPreflight.design_thresholds.minimum_treated_regions}`}
                />
                <ContractMetric
                  inverted
                  label="Controls eligible"
                  value={`${panelPreflight.current_eligibility.eligible_control_region_count} / ${panelPreflight.design_thresholds.minimum_control_regions_per_cohort}`}
                />
                <ContractMetric
                  inverted
                  label="Fields queued"
                  value={`${panelPreflight.field_gap_summary.acquisition_task_field_instance_count} / ${panelPreflight.field_gap_summary.required_field_instance_count}`}
                />
                <ContractMetric
                  inverted
                  label="Panel rows"
                  value={panelPreflight.current_eligibility.assembled_panel_row_count.toString()}
                />
              </dl>
            </div>
            <div className="grid divide-y divide-white/10 sm:grid-cols-2 sm:divide-x sm:divide-y-0 xl:grid-cols-4">
              {panelPreflight.acquisition_queue.map((task) => (
                <div className="p-5 sm:p-6" key={task.task_id}>
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-caution">
                      {task.priority}
                    </span>
                    <span className="text-[10px] uppercase tracking-[0.08em] text-subtle">
                      {task.required_fields.length} fields
                    </span>
                  </div>
                  <p className="mt-4 text-sm font-medium leading-5 text-subtle">
                    {task.task_id.replace('E2_', '').replaceAll('_', ' ')}
                  </p>
                  <p className="mt-2 text-xs leading-5 text-subtle">
                    {task.current_status.replaceAll('_', ' ')}
                  </p>
                </div>
              ))}
            </div>
            <div className="border-t border-line bg-workspace px-6 py-4 text-xs leading-5 text-subtle">
              {panelPreflight.pspe_role}
            </div>
          </article>

          <div className="mt-5 grid gap-5 rounded-lg border border-line bg-workspace p-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:p-6">
            <div>
              <div className="flex items-center gap-2 text-brand">
                <CircleCheck className="size-4" />
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em]">
                  Regional control panel ready
                </p>
              </div>
              <p className="mt-2 text-sm leading-6 text-brand">
                Statistics Canada building-investment observations now provide a
                common quarterly activity control across Canada. They do not
                authorize an AI-attributable estimate.
              </p>
            </div>
            <dl className="grid grid-cols-3 gap-5 border-t border-line pt-5 sm:border-l sm:border-t-0 sm:pl-6 sm:pt-0">
              <ContractMetric
                label="Observations"
                value={buildingInvestmentControls.observation_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Geographies"
                value={buildingInvestmentControls.geography_count.toString()}
              />
              <ContractMetric
                label="Quarters"
                value={buildingInvestmentControls.quarter_count.toString()}
              />
            </dl>
          </div>

          <div className="mt-5 grid gap-5 rounded-lg border border-line bg-workspace p-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:p-6">
            <div>
              <div className="flex items-center gap-2 text-subtle">
                <Activity className="size-4" />
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em]">
                  Regional macro controls · descriptive only
                </p>
              </div>
              <p className="mt-2 text-sm leading-6 text-subtle">
                Seven separate Statistics Canada controls now track consumer
                prices, population, payroll earnings, housing starts and
                non-residential investment through{' '}
                {regionalMacroControls.common_latest_period_end}. They provide
                regional context, not an AI effect or composite pressure score.
              </p>
            </div>
            <dl className="grid grid-cols-3 gap-5 border-t border-line pt-5 sm:border-l sm:border-t-0 sm:pl-6 sm:pt-0">
              <ContractMetric
                label="Observations"
                value={regionalMacroControls.observation_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Series"
                value={regionalMacroControls.series_count.toString()}
              />
              <ContractMetric
                label="Quarters"
                value={regionalMacroControls.quarter_count.toString()}
              />
            </dl>
          </div>

          <div className="mt-5 grid gap-5 rounded-lg border border-line bg-workspace p-5 lg:grid-cols-[minmax(0,.9fr)_minmax(520px,1.1fr)] lg:items-center sm:p-6">
            <div>
              <div className="flex items-center gap-2 text-subtle">
                <Building2 className="size-4" />
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em]">
                  Municipal permit treatment proxy · not authorizing
                </p>
              </div>
              <p className="mt-2 text-sm leading-6 text-subtle">
                {edmontonPermitProxy.publication_boundary.reason}
              </p>
            </div>
            <dl className="grid grid-cols-2 gap-5 border-t border-line pt-5 sm:grid-cols-4 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
              <ContractMetric
                label="Broad screen"
                value={edmontonPermitProxy.broad_screen_row_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Data-centre candidates"
                value={edmontonPermitProxy.data_centre_candidate_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Explicit AI references"
                value={edmontonPermitProxy.explicit_ai_reference_count.toString()}
              />
              <ContractMetric
                label="Candidate occupancy dates"
                value={edmontonPermitProxy.data_centre_candidate_occupancy_date_available_count.toString()}
              />
            </dl>
          </div>

          <div className="mt-5 grid gap-5 rounded-lg border border-line bg-workspace p-5 lg:grid-cols-[minmax(0,.9fr)_minmax(520px,1.1fr)] lg:items-center sm:p-6">
            <div>
              <div className="flex items-center gap-2 text-subtle">
                <GitBranch className="size-4" />
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em]">
                  Quebec complete archive + revision panel · candidate
                </p>
              </div>
              <p className="mt-2 text-sm leading-6 text-subtle">
                All {quebecFullArchive.snapshot_date_count} official catalog
                dates expose{' '}
                {quebecFullArchive.disappearance_event_count.toLocaleString(
                  'en-CA',
                )}{' '}
                adjacent-snapshot disappearances and{' '}
                {quebecFullArchive.project_with_catalog_reentry_count}{' '}
                re-entering projects. Publisher-declared service-and-retirement
                markers precede{' '}
                {quebecFullArchive.publisher_declared_retirement_disappearance_event_count.toLocaleString(
                  'en-CA',
                )}{' '}
                transitions;{' '}
                {quebecFullArchive.unclassified_disappearance_event_count.toLocaleString(
                  'en-CA',
                )}{' '}
                remain unclassified. A {quebecParserReview.sample_project_count}
                -project review packet is prepared; independent review is still
                pending.
              </p>
            </div>
            <dl className="grid grid-cols-2 gap-5 border-t border-line pt-5 sm:grid-cols-3 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
              <ContractMetric
                label="Archive dates"
                value={quebecFullArchive.snapshot_date_count.toString()}
              />
              <ContractMetric
                label="Unique projects"
                value={quebecFullArchive.unique_project_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Disappearances"
                value={quebecFullArchive.disappearance_event_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Declared retirements"
                value={quebecFullArchive.publisher_declared_retirement_disappearance_event_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Cost chains"
                value={quebecProjectRevisions.coverage_summary.cost_revision_chain_reconciled_project_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Schedule chains"
                value={quebecProjectRevisions.coverage_summary.schedule_revision_chain_reconciled_project_count.toLocaleString(
                  'en-CA',
                )}
              />
            </dl>
          </div>

          <div className="mt-5 grid gap-5 rounded-lg border border-caution/30 bg-caution-soft p-5 lg:grid-cols-[minmax(0,.9fr)_minmax(520px,1.1fr)] lg:items-center sm:p-6">
            <div>
              <div className="flex items-center gap-2 text-caution">
                <AlertTriangle className="size-4" />
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em]">
                  Procurement outcome feasibility · not authorizing
                </p>
              </div>
              <p className="mt-2 text-sm leading-6 text-caution">
                {procurementOutcomeFeasibility.publication_boundary.reason}
              </p>
            </div>
            <dl className="grid grid-cols-2 gap-5 border-t border-caution/30 pt-5 sm:grid-cols-4 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
              <ContractMetric
                label="Construction linkages"
                value={procurementOutcomeFeasibility.construction_linkage_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Tender + award"
                value={procurementOutcomeFeasibility.linked_tender_award_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="Tender + contract"
                value={procurementOutcomeFeasibility.linked_tender_contract_count.toLocaleString(
                  'en-CA',
                )}
              />
              <ContractMetric
                label="CMA locations"
                value={procurementOutcomeFeasibility.cma_geography_count.toString()}
              />
            </dl>
          </div>

          <div className="mt-5 grid gap-5 rounded-lg border border-line bg-workspace p-5 lg:grid-cols-[minmax(0,.9fr)_minmax(520px,1.1fr)] lg:items-center sm:p-6">
            <div>
              <div className="flex items-center gap-2 text-subtle">
                <BookOpen className="size-4" />
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.1em]">
                  Audited outcome references · transcription review pending
                </p>
              </div>
              <p className="mt-2 text-sm leading-6 text-subtle">
                Two Ontario audit cases now preserve scope-checked cost and
                substantial-completion histories plus source cost components.
                They improve reference design but do not form an outcome panel
                or authorize an AI effect.
              </p>
            </div>
            <dl className="grid grid-cols-2 gap-5 border-t border-line pt-5 sm:grid-cols-4 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
              <ContractMetric
                label="Named cases"
                value={auditedProjectOutcomes.coverage_summary.named_completed_project_count.toString()}
              />
              <ContractMetric
                label="Completed total cost"
                value={auditedProjectOutcomes.coverage_summary.completed_total_cost_case_count.toString()}
              />
              <ContractMetric
                label="Exact-day schedule pairs"
                value={auditedProjectOutcomes.coverage_summary.exact_day_substantial_completion_pair_count.toString()}
              />
              <ContractMetric
                label="Price-basis dates"
                value={auditedProjectOutcomes.coverage_summary.price_basis_date_case_count.toString()}
              />
            </dl>
          </div>

          <div className="mt-7 flex flex-wrap items-center gap-4 text-xs text-subtle">
            <span className="font-mono">
              Contract {attributionReadiness.contract_id}
            </span>
            <span aria-hidden="true">·</span>
            <span>As of {buildingInvestmentControls.as_of_date}</span>
            <Link
              className="font-medium text-brand underline decoration-[#8fbeb4] underline-offset-4 hover:text-brand"
              href="/methods"
            >
              Inspect the full methodology
            </Link>
          </div>
        </div>
      </section>

      <section
        id="canada-coverage"
        className="border-y border-line bg-workspace"
      >
        <div className="mx-auto max-w-[1440px] px-5 py-14 sm:px-8 lg:px-8 lg:py-8">
          <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
            <div>
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.15em] text-brand">
                Canada expansion map
              </p>
              <h2 className="mt-3 max-w-3xl text-2xl font-medium tracking-[-0.04em] text-ink sm:text-2xl">
                Coverage first. Comparison only when the quantities agree.
              </h2>
            </div>
            <p className="max-w-lg text-sm leading-6 text-subtle">
              This matrix shows research readiness, not provincial performance.
              Expansion-source records remain outside Decision Mode until their
              validation and review gates pass.
            </p>
          </div>

          <div className="mt-9 overflow-hidden rounded-lg border border-line bg-surface">
            <p className="border-b border-line bg-white px-4 py-3 font-mono text-[9px] uppercase tracking-[0.08em] text-subtle sm:hidden">
              Swipe horizontally to inspect all evidence layers
            </p>
            <WorkspaceScrollRegion label="Research evidence table">
              <table className="w-full min-w-[820px] border-collapse text-left">
                <caption className="sr-only">
                  Research evidence coverage by province and evidence layer
                </caption>
                <thead>
                  <tr className="border-b border-line bg-workspace font-mono text-[10px] uppercase tracking-[0.1em] text-brand">
                    <th className="px-5 py-4 font-semibold" scope="col">
                      Province
                    </th>
                    {coverageColumns.map(([domain, label]) => (
                      <th
                        className="px-4 py-4 font-semibold"
                        key={domain}
                        scope="col"
                      >
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {canadaCoverage.geographies.map((row) => (
                    <tr
                      className="border-b border-line last:border-0"
                      key={row.geography_id}
                    >
                      <th className="px-5 py-5" scope="row">
                        <span className="block text-sm font-semibold text-ink">
                          {row.geography_label}
                        </span>
                        <span className="mt-1 block font-mono text-[9px] uppercase tracking-[0.08em] text-subtle">
                          {row.geography_id === 'PR_48'
                            ? 'Alberta pilot'
                            : 'Coverage inventory'}
                        </span>
                      </th>
                      {coverageColumns.map(([domain]) => (
                        <td
                          className="px-4 py-5"
                          key={`${row.geography_id}-${domain}`}
                        >
                          <CoverageStatus status={row.domains[domain].status} />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </WorkspaceScrollRegion>
            <div className="flex flex-wrap gap-x-5 gap-y-2 border-t border-line bg-white px-5 py-4 font-mono text-[9px] uppercase tracking-[0.07em] text-subtle">
              <span className="inline-flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-brand" /> Available
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-workspace" />{' '}
                Available with published gaps
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-caution" /> Not
                available · not imputed
              </span>
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <article className="rounded-lg border border-line bg-workspace p-5 sm:p-6">
              <div className="flex items-center gap-2 text-brand">
                <CircleCheck className="size-4" />
                <h3 className="text-sm font-semibold">Comparable now</h3>
              </div>
              <p className="mt-3 text-sm leading-6 text-brand">
                Coverage status, source vintage, within-publisher scenario
                spread, and like-for-like quantities with aligned units, periods
                and system boundaries.
              </p>
            </article>
            <article className="rounded-lg border border-caution/30 bg-caution-soft p-5 sm:p-6">
              <div className="flex items-center gap-2 text-caution">
                <LockKeyhole className="size-4" />
                <h3 className="text-sm font-semibold">Held behind the gate</h3>
              </div>
              <p className="mt-3 text-sm leading-6 text-caution">
                Ontario data-centre energy versus Quebec winter peak, B.C.
                supply actions as spare capacity, or any conversion of
                province-wide capex into a transmission build requirement.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section id="evidence" className="border-y border-line bg-workspace">
        <div className="mx-auto grid max-w-[1440px] gap-6 px-5 py-8 sm:px-8 lg:grid-cols-[1fr_auto] lg:px-8">
          <div className="flex gap-4">
            <span className="grid size-11 shrink-0 place-items-center rounded-full bg-white text-brand">
              <BookOpen className="size-4" />
            </span>
            <div>
              <p className="text-lg font-medium text-ink">
                {releaseData.baseline.ai_project_pipeline.core_project_count}{' '}
                core data-centre records are in the current Alberta evidence
                view.
              </p>
              <p className="mt-1 max-w-2xl text-sm leading-6 text-subtle">
                Projects with reported values total $
                {(
                  releaseData.baseline.ai_project_pipeline
                    .known_core_capex_cad / 1_000_000_000
                ).toFixed(2)}
                B, but these are announcements—not commitments or realized
                spend. The weekly digest feeds review, never the model
                automatically.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 lg:justify-end">
            <MapPin className="size-4 text-caution" />
            <span className="font-mono text-xs text-subtle">
              PILOT: ALBERTA · SCALE: CANADA
            </span>
          </div>
        </div>
      </section>

      <SiteFooter />
    </ResearchShell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-mono text-lg font-semibold text-ink">{value}</p>
      <p className="mt-1 text-[10px] leading-4 text-subtle">{label}</p>
    </div>
  );
}

function FlowNode({
  active,
  eyebrow,
  icon: Icon,
  label,
}: {
  active?: boolean;
  eyebrow: string;
  icon: typeof Zap;
  label: string;
}) {
  return (
    <div
      className={`rounded-lg border p-4 text-center ${active ? 'border-brand/30 bg-surface' : 'border-line bg-surface'}`}
    >
      <span
        className={`mx-auto mb-4 grid size-10 place-items-center rounded-full ${active ? 'bg-workspace text-brand' : 'bg-workspace text-subtle'}`}
      >
        <Icon className="size-4" />
      </span>
      <p className="font-mono text-[9px] uppercase tracking-[0.14em] text-subtle">
        {eyebrow}
      </p>
      <p className="mt-2 text-sm font-medium leading-5">{label}</p>
    </div>
  );
}

function FlowArrow() {
  return (
    <div className="flex items-center text-brand" aria-hidden="true">
      <span className="h-px w-2 bg-current sm:w-5" />
      <ChevronRight className="-ml-1 size-4" />
    </div>
  );
}

function CoverageStatus({ status }: { status: string }) {
  const available = status === 'available';
  const incomplete = status === 'available_with_missingness';
  const tone = available
    ? 'border-line bg-workspace text-brand'
    : incomplete
      ? 'border-line bg-workspace text-subtle'
      : 'border-caution/30 bg-caution-soft text-caution';
  const label = available
    ? 'Available'
    : incomplete
      ? 'With gaps'
      : 'Not available';
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.06em] ${tone}`}
    >
      <span className="size-1.5 rounded-full bg-current opacity-70" />
      {label}
    </span>
  );
}

function AttributionDomainCard({
  label,
  role,
  sourceCount,
  status,
  summary,
}: {
  label: string;
  role: string;
  sourceCount: number;
  status: string;
  summary: string;
}) {
  const available = status === 'available';
  const candidate = status === 'candidate';
  const panelTone = available
    ? 'border-line bg-workspace'
    : candidate
      ? 'border-line bg-workspace'
      : 'border-caution/30 bg-caution-soft';
  const textTone = available
    ? 'text-brand'
    : candidate
      ? 'text-subtle'
      : 'text-caution';
  return (
    <article className={`rounded-lg border p-5 sm:p-6 ${panelTone}`}>
      <div className="flex items-start justify-between gap-3">
        <p
          className={`font-mono text-[10px] font-semibold uppercase tracking-[0.1em] ${textTone}`}
        >
          {role}
        </p>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border bg-workspace px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.07em] ${available ? 'border-brand/30 text-brand' : candidate ? 'border-line text-subtle' : 'border-caution/30 text-caution'}`}
        >
          {available ? (
            <CircleCheck className="size-3" />
          ) : candidate ? (
            <BookOpen className="size-3" />
          ) : (
            <LockKeyhole className="size-3" />
          )}
          {status.replaceAll('_', ' ')}
        </span>
      </div>
      <h3 className="mt-5 text-lg font-medium tracking-[-0.02em] text-ink">
        {label}
      </h3>
      <p className="mt-2 text-sm leading-6 text-subtle">{summary}</p>
      <p className="mt-5 border-t border-current/15 pt-3 font-mono text-[9px] uppercase tracking-[0.08em] text-subtle">
        {sourceCount} registry-bound source{sourceCount === 1 ? '' : 's'}
      </p>
    </article>
  );
}

function ContractMetric({
  inverted = false,
  label,
  value,
}: {
  inverted?: boolean;
  label: string;
  value: string;
}) {
  return (
    <div>
      <dt
        className={`font-mono text-[9px] uppercase tracking-[0.08em] ${inverted ? 'text-subtle' : 'text-subtle'}`}
      >
        {label}
      </dt>
      <dd
        className={`mt-1 text-sm font-semibold ${inverted ? 'text-ink' : 'text-ink'}`}
      >
        {value}
      </dd>
    </div>
  );
}

function TreatmentSourceGateboard() {
  const gates = treatmentSourceFeasibility.required_authorizing_gates;
  return (
    <article className="mt-5 overflow-hidden rounded-lg border border-line bg-surface text-ink shadow-none">
      <div className="grid gap-6 border-b border-line p-6 sm:p-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div>
          <div className="flex items-center gap-2 text-brand">
            <ShieldCheck className="size-4" />
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em]">
              Treatment source qualification
            </p>
          </div>
          <h3 className="mt-3 max-w-3xl text-2xl font-medium tracking-[-0.035em] sm:text-2xl">
            A plausible source must pass every gate before it can identify
            treatment.
          </h3>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-subtle">
            The matrix makes the withholding decision inspectable. A failed gate
            changes what the measure means; passing several gates cannot be
            averaged into eligibility.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-line bg-workspace">
          <div className="bg-surface px-5 py-4">
            <p className="font-mono text-2xl font-semibold text-ink">
              {treatmentSourceFeasibility.authorizing_candidate_count}
            </p>
            <p className="mt-1 text-[10px] uppercase tracking-[0.08em] text-subtle">
              qualifying sources
            </p>
          </div>
          <div className="bg-surface px-5 py-4">
            <p className="font-mono text-2xl font-semibold text-ink">
              {treatmentSourceFeasibility.candidate_count}
            </p>
            <p className="mt-1 text-[10px] uppercase tracking-[0.08em] text-subtle">
              sources screened
            </p>
          </div>
        </div>
      </div>

      <div className="border-b border-line bg-surface px-5 py-3 sm:hidden">
        <p className="font-mono text-[9px] uppercase tracking-[0.08em] text-subtle">
          Swipe horizontally to inspect all seven gates
        </p>
      </div>
      <WorkspaceScrollRegion label="Research evidence table">
        <table className="w-full min-w-[1040px] border-collapse text-left">
          <caption className="sr-only">
            Public source eligibility against the seven AI construction
            treatment gates
          </caption>
          <thead>
            <tr className="border-b border-line bg-white/[0.035] font-mono text-[9px] uppercase tracking-[0.08em] text-subtle">
              <th className="w-[310px] px-6 py-4 font-medium" scope="col">
                Candidate source
              </th>
              {gates.map((gate) => (
                <th
                  className="px-3 py-4 text-center font-medium"
                  key={gate}
                  scope="col"
                >
                  {treatmentGateLabels[gate] ?? gate}
                </th>
              ))}
              <th className="px-6 py-4 text-right font-medium" scope="col">
                Result
              </th>
            </tr>
          </thead>
          <tbody>
            {treatmentSourceFeasibility.candidates.map((candidate) => (
              <tr
                className="border-b border-line last:border-0 hover:bg-white/[0.025]"
                key={candidate.candidate_id}
              >
                <th className="px-6 py-4" scope="row">
                  <span className="block text-sm font-medium text-subtle">
                    {candidate.source_title}
                  </span>
                  <span className="mt-1 block max-w-[280px] text-[10px] leading-4 text-subtle">
                    {candidate.analytical_role.replaceAll('_', ' ')}
                  </span>
                </th>
                {gates.map((gate) => {
                  const passed =
                    candidate.gate_assessment[
                      gate as keyof typeof candidate.gate_assessment
                    ];
                  return (
                    <td className="px-3 py-4 text-center" key={gate}>
                      <span
                        className={`mx-auto grid size-6 place-items-center rounded-full border ${passed ? 'border-brand/30 bg-surface text-brand' : 'border-caution/30 bg-caution text-caution'}`}
                        title={`${treatmentGateLabels[gate]}: ${passed ? 'passes' : 'fails'}`}
                      >
                        {passed ? (
                          <CircleCheck className="size-3.5" />
                        ) : (
                          <CircleX className="size-3.5" />
                        )}
                        <span className="sr-only">
                          {passed ? 'Pass' : 'Fail'}
                        </span>
                      </span>
                    </td>
                  );
                })}
                <td className="px-6 py-4 text-right">
                  <span className="inline-flex rounded-full border border-caution/30 bg-caution px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.07em] text-caution">
                    excluded
                  </span>
                  <span className="mt-1 block font-mono text-[9px] text-subtle">
                    {candidate.passed_gate_count} /{' '}
                    {candidate.required_gate_count} gates
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </WorkspaceScrollRegion>
      <div className="grid gap-4 border-t border-line bg-white/[0.035] px-6 py-5 text-xs leading-5 text-subtle sm:grid-cols-[1fr_auto] sm:items-center">
        <p>
          <strong className="text-subtle">Next evidence required:</strong>{' '}
          {treatmentSourceFeasibility.acquisition_decision.next_evidence_needed}
        </p>
        <Link
          className="font-medium text-brand underline decoration-[#4f8e85] underline-offset-4 hover:text-ink"
          href="/methods"
        >
          Read the treatment protocol
        </Link>
      </div>
    </article>
  );
}
