import {
  Building2,
  BriefcaseBusiness,
  Database,
  ExternalLink,
  Layers3,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';

import { EvidenceExplorer } from '@/components/evidence-explorer';
import {
  LabourMarketExplorer,
  type NationalLabourAvailability,
  type NationalLabourPressure,
  type NationalWorkforceStock,
} from '@/components/labour-market-explorer';
import { RegionalMacroExplorer } from '@/components/regional-macro-explorer';
import {
  EvidencePill,
  PageIntro,
  SiteFooter,
  ResearchShell,
  SectionNavigation,
} from '@/components/site-shell';
import releaseData from '@/public/data/latest.json';
import informationSectorCapex from '@/data/model-runs/information_sector_construction_capex_screen_v0.1.json';
import cmaReferenceBaseline from '@/data/model-runs/vancouver_toronto_montreal_bcpi_reference_baseline_v0.1.json';
import provinceLinkedBaseline from '@/data/model-runs/bc_on_qc_province_linked_reference_baseline_v0.1.json';
import aiCapexLedger from '@/data/model-runs/alberta_ai_capex_announcement_ledger_v0.1.json';

export default function EvidencePage() {
  const pipeline = releaseData.baseline.ai_project_pipeline;
  const ledger = aiCapexLedger.coverage_summary;
  const labour = (
    releaseData.baseline as typeof releaseData.baseline & {
      labour_availability?: LabourAvailability;
    }
  ).labour_availability;
  const labourCanada = (
    releaseData.baseline as typeof releaseData.baseline & {
      labour_availability_canada?: NationalLabourAvailability;
    }
  ).labour_availability_canada;
  const workforceCanada = (
    releaseData.baseline as typeof releaseData.baseline & {
      labour_workforce_stock_canada?: NationalWorkforceStock;
    }
  ).labour_workforce_stock_canada;
  const labourPressure = (
    releaseData as typeof releaseData & {
      labour_pressure?: NationalLabourPressure;
    }
  ).labour_pressure;
  return (
    <ResearchShell>
      <PageIntro
        eyebrow="Evidence register"
        title="Evidence register"
        description="Every project, indicator and claim retains its public source, time stamp, geography and evidence status. The current view is Alberta-first and deliberately distinguishes reported fields from research classifications."
      />
      <SectionNavigation
        items={[
          ['projects', 'Projects'],
          ['labour', 'Labour'],
          ['regional', 'Regional context'],
          ['references', 'Cost references'],
          ['sources', 'Sources'],
        ]}
      />
      <section className="border-b border-line bg-surface text-ink">
        <div className="mx-auto grid max-w-[1440px] gap-px bg-workspace sm:grid-cols-2 lg:grid-cols-4">
          <Metric
            label="AI-relevant records"
            value={String(aiCapexLedger.record_count)}
            note={`${ledger.core_data_centre_record_count} core · ${ledger.enabling_power_record_count} enabling power`}
          />
          <Metric
            label="Partial known estimates"
            value={`$${(ledger.known_reported_estimated_cost_cad / 1_000_000_000).toFixed(2)}B`}
            note={`${ledger.reported_estimated_cost_record_count} of ${aiCapexLedger.record_count} records report a value`}
          />
          <Metric
            label="Construction-stage candidates"
            value={String(ledger.publisher_construction_stage_candidate_count)}
            note="Publisher stage only · onset unverified"
          />
          <Metric
            label="Authorizing treatment"
            value={`${ledger.authorizing_treatment_onset_count} / ${aiCapexLedger.record_count}`}
            note="No realized onset or regional-period dose"
          />
        </div>
      </section>
      <section
        id="projects"
        className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8"
      >
        <div className="mb-8 grid gap-4 rounded-lg border border-caution/30 bg-workspace p-5 md:grid-cols-[auto_1fr]">
          <ShieldCheck className="mt-0.5 size-5 text-caution" />
          <div>
            <p className="font-medium text-caution">
              Announcement pipeline, not committed investment
            </p>
            <p className="mt-1 text-sm leading-6 text-caution">
              {pipeline.warning} The formal ledger keeps the $49.01B of known
              core estimates separate from $6.40B of enabling-power estimates.
              Missing values are not zero, no stage probabilities are applied,
              and the $50B scenario remains a separate counterfactual.
            </p>
          </div>
        </div>
        <EvidenceExplorer projects={releaseData.baseline.projects} />
      </section>
      <div id="labour">
        {labourCanada ? (
          <LabourMarketExplorer
            labour={labourCanada}
            pressure={labourPressure}
            workforce={workforceCanada}
          />
        ) : labour ? (
          <LabourAvailabilityPanel labour={labour} />
        ) : null}
      </div>
      <div id="regional">
        <RegionalMacroExplorer />
      </div>
      <InformationSectorCapexPanel />
      <div id="references">
        <CmaReferenceCostPanel />
      </div>
      <ProvinceLinkedBackcastPanel />
      <section id="sources" className="border-t border-line bg-workspace">
        <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8">
          <div className="mb-6 flex items-center gap-2">
            <Database className="size-4 text-brand" />
            <h2 className="text-xl font-medium">Registered public sources</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {releaseData.sources.map((source) => (
              <article
                className="rounded-lg border border-line bg-surface p-4"
                key={source.source_id}
              >
                <div className="flex items-start justify-between gap-3">
                  <EvidencePill status={source.evidence_status} />
                  <span className="font-mono text-[10px] text-subtle">
                    as of {source.as_of_date}
                  </span>
                </div>
                <h3 className="mt-3 text-sm font-medium">{source.title}</h3>
                <p className="mt-1 text-xs text-subtle">
                  {source.publisher} · {source.domain.replaceAll('_', ' ')}
                </p>
                <a
                  className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-brand hover:underline"
                  href={source.canonical_url}
                  rel="noreferrer"
                  target="_blank"
                >
                  Open official source <ExternalLink className="size-3" />
                </a>
              </article>
            ))}
          </div>
        </div>
      </section>
      <SiteFooter />
    </ResearchShell>
  );
}

function ProvinceLinkedBackcastPanel() {
  const provinces = ['PR_59', 'PR_35', 'PR_24'].map((geographyId) => {
    const results = provinceLinkedBaseline.reference_class_results.filter(
      (item) => item.geography_id === geographyId,
    );
    const diagnostics =
      provinceLinkedBaseline.backcast_method.diagnostics.filter(
        (item) => item.province_id === geographyId,
      );
    let passedHorizons = 0;
    for (const result of results) {
      const horizons = result.horizons as readonly { status: string }[];
      for (const horizon of horizons) {
        if (horizon.status === 'gate_passed') passedHorizons += 1;
      }
    }
    return {
      geographyId,
      geographyLabel: results[0]?.geography_label ?? geographyId,
      passedHorizons,
      maximumOverlapMape: Math.max(
        ...diagnostics.map((item) => item.overlap_mape_percent),
      ),
      inferredObservations: diagnostics.reduce(
        (total, item) => total + item.backcast_observation_count,
        0,
      ),
    };
  });
  return (
    <section className="border-t border-line bg-workspace">
      <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8">
        <div className="flex items-center gap-2 text-caution">
          <Layers3 className="size-4" />
          <h2 className="text-xl font-medium">
            Province-linked historical reference bridge
          </h2>
        </div>
        <p className="mt-3 max-w-4xl text-sm leading-6 text-subtle">
          Official provincial BCPI observations are preserved from 2017 onward.
          Earlier institutional, school and office histories are inferred by
          scaling Montréal, Toronto or Vancouver to the first official
          provincial quarter. The bridge extends model-validation history
          without presenting CMA values as official provincial observations.
        </p>
        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {provinces.map((item) => (
            <article
              className="rounded-lg border border-line bg-surface p-5"
              key={item.geographyId}
            >
              <p className="text-xs font-medium text-subtle">
                {item.geographyLabel}
              </p>
              <p className="mt-3 font-mono text-2xl font-semibold text-ink">
                {item.passedHorizons} / 20
              </p>
              <p className="mt-1 text-xs leading-5 text-subtle">
                internally gate-passing horizons · {item.inferredObservations}{' '}
                pre-2017 inferred observations
              </p>
              <p className="mt-4 border-t border-line pt-3 font-mono text-[10px] uppercase tracking-[0.08em] text-caution">
                max overlap MAPE {item.maximumOverlapMape.toFixed(2)}%
              </p>
            </article>
          ))}
        </div>
        <div className="mt-5 rounded-lg border border-caution/30 bg-workspace p-4 text-sm leading-6 text-caution">
          Research display only. Nine horizons pass the unchanged internal
          forecast gates, all in British Columbia-linked reference classes.
          Ontario and Quebec remain gate-failed, the municipal-operations series
          remains too short, and no result is authorized for public projection,
          project-cost translation or AI attribution.
        </div>
      </div>
    </section>
  );
}

function CmaReferenceCostPanel() {
  const geographies = ['CMA_933', 'CMA_535', 'CMA_462'].map((geographyId) => {
    const results = cmaReferenceBaseline.reference_class_results.filter(
      (item) => item.geography_id === geographyId,
    );
    let passedHorizons = 0;
    for (const result of results) {
      for (const horizon of result.horizons) {
        if (horizon.status === 'gate_passed') passedHorizons += 1;
      }
    }
    return {
      geographyId,
      geographyLabel: results[0]?.geography_label ?? geographyId,
      passedHorizons,
      seriesCount: results.length,
      firstLongHistoryQuarter: results
        .filter((item) => item.observation_count > 100)
        .map((item) => item.first_period_end)
        .sort()[0],
    };
  });
  const statusCounts =
    cmaReferenceBaseline.publication_summary.horizon_status_counts;
  return (
    <section className="border-t border-line bg-workspace">
      <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8">
        <div className="flex items-center gap-2 text-brand">
          <Building2 className="size-4" />
          <h2 className="text-xl font-medium">
            City-market reference-cost validation
          </h2>
        </div>
        <p className="mt-3 max-w-4xl text-sm leading-6 text-subtle">
          The same locked BCPI validation protocol used for Alberta now runs on
          long Vancouver, Toronto and Montréal histories. These are CMA market
          references, not provincial forecasts or AI-attributable effects.
        </p>
        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {geographies.map((item) => (
            <article
              className="rounded-lg border border-line bg-white p-5"
              key={item.geographyId}
            >
              <p className="text-xs text-subtle">{item.geographyLabel}</p>
              <p className="mt-2 font-mono text-2xl font-semibold text-ink">
                {item.passedHorizons} / 20
              </p>
              <p className="mt-1 text-xs leading-5 text-subtle">
                internally gate-passing horizons · {item.seriesCount} reference
                classes · long histories begin {item.firstLongHistoryQuarter}
              </p>
            </article>
          ))}
        </div>
        <div className="mt-5 grid gap-3 rounded-lg border border-caution/30 bg-workspace p-4 text-sm leading-6 text-caution sm:grid-cols-[auto_1fr]">
          <span className="font-mono font-semibold">WITHHELD</span>
          <span>
            {statusCounts.gate_passed} horizons pass internally,{' '}
            {statusCounts.gate_failed} fail and {statusCounts.not_assessed} are
            not assessed. All nine passes are Vancouver results, but no public
            projection is authorized until independent modelling review.
          </span>
        </div>
      </div>
    </section>
  );
}

function InformationSectorCapexPanel() {
  const selected = ['PR_48', 'PR_59', 'PR_35', 'PR_24']
    .map((geographyId) =>
      informationSectorCapex.geography_summaries.find(
        (item) => item.geography_id === geographyId,
      ),
    )
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
  return (
    <section className="border-t border-line bg-surface">
      <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8">
        <div className="flex items-center gap-2 text-brand">
          <TrendingUp className="size-4" />
          <h2 className="text-xl font-medium">
            Broad information-sector construction context
          </h2>
        </div>
        <p className="mt-3 max-w-4xl text-sm leading-6 text-subtle">
          Statistics Canada table 34-10-0035-01 · latest published actual or
          revised year by province. These values cover all NAICS 51 information
          and cultural industries—not data centres or AI construction alone.
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {selected.map((item) => (
            <article
              className="rounded-lg border border-line bg-white p-5"
              key={item.geography_id}
            >
              <p className="text-xs text-subtle">{item.geography_label}</p>
              <p className="mt-2 font-mono text-2xl font-semibold text-brand">
                {formatCompactCad(item.latest_actual_or_revised_value_cad)}
              </p>
              <p className="mt-1 text-xs text-subtle">
                {item.latest_actual_or_revised_year} actual/revised ·{' '}
                {item.withheld_or_unavailable_count} suppressed or unavailable
                years
              </p>
            </article>
          ))}
        </div>
        <div className="mt-5 rounded-lg border border-caution/30 bg-workspace p-4 text-sm leading-6 text-caution">
          Descriptive proxy only. NAICS 518210 is not separately published in
          this provincial table, the series is annual rather than quarterly, and
          it cannot define AI treatment onset or dose. AI-attributable cost and
          schedule effects remain null.
        </div>
      </div>
    </section>
  );
}

function formatCompactCad(value: number | null) {
  if (value === null) return 'Not published';
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  return `$${(value / 1_000_000).toFixed(1)}M`;
}

type LabourObservation = {
  noc_code: string;
  occupation_label: string;
  trade_node_id: string;
  statistic: string;
  value: number | null;
  unit: string;
  period_end: string;
  quality_flags: string[];
};

type LabourAvailability = {
  period_end: string;
  warning: string;
  observations: LabourObservation[];
};

function LabourAvailabilityPanel({ labour }: { labour: LabourAvailability }) {
  const occupations = Array.from(
    labour.observations
      .reduce((groups, observation) => {
        const existing = groups.get(observation.noc_code) ?? {
          nocCode: observation.noc_code,
          occupation: observation.occupation_label,
          tradeNode: observation.trade_node_id,
          vacancies: null as LabourObservation | null,
          wage: null as LabourObservation | null,
        };
        if (observation.statistic === 'Job vacancies')
          existing.vacancies = observation;
        if (observation.statistic === 'Average offered hourly wage')
          existing.wage = observation;
        groups.set(observation.noc_code, existing);
        return groups;
      }, new Map<string, { nocCode: string; occupation: string; tradeNode: string; vacancies: LabourObservation | null; wage: LabourObservation | null }>())
      .values(),
  );

  return (
    <section className="border-t border-line bg-white">
      <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8">
        <div className="mb-3 flex items-center gap-2">
          <BriefcaseBusiness className="size-4 text-brand" />
          <h2 className="text-xl font-medium">Alberta trade labour snapshot</h2>
        </div>
        <p className="max-w-4xl text-sm leading-6 text-subtle">
          Statistics Canada table 14-10-0444-01 · quarter ending{' '}
          {labour.period_end}. Values are observed survey estimates; quality
          codes are retained.
        </p>
        <div className="mt-6 overflow-x-auto rounded-lg border border-line">
          <table className="w-full min-w-[820px] border-collapse text-left text-sm">
            <caption className="sr-only">
              Alberta trade labour observations
            </caption>
            <thead className="bg-workspace text-xs uppercase tracking-wide text-brand">
              <tr>
                <th className="px-4 py-3" scope="col">
                  Model trade
                </th>
                <th className="px-4 py-3" scope="col">
                  Occupation
                </th>
                <th className="px-4 py-3" scope="col">
                  Vacancies
                </th>
                <th className="px-4 py-3" scope="col">
                  Offered wage
                </th>
                <th className="px-4 py-3" scope="col">
                  StatCan quality
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line bg-surface">
              {occupations.map((item) => (
                <tr key={item.nocCode}>
                  <td className="px-4 py-3 font-mono text-xs text-brand">
                    {item.tradeNode.replace('trade_', '').replaceAll('_', ' ')}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-medium">{item.occupation}</span>
                    <span className="ml-2 font-mono text-xs text-subtle">
                      NOC {item.nocCode}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {formatLabourValue(item.vacancies, 'vacancies')}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {formatLabourValue(item.wage, 'wage')}
                  </td>
                  <td className="px-4 py-3 text-xs text-subtle">
                    {qualitySummary(item.vacancies, item.wage)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 rounded-lg border border-caution/30 bg-workspace p-4 text-sm leading-6 text-caution">
          {labour.warning}
        </div>
      </div>
    </section>
  );
}

function formatLabourValue(
  observation: LabourObservation | null,
  kind: 'vacancies' | 'wage',
) {
  if (!observation || observation.value === null) return 'Not published';
  return kind === 'wage'
    ? `$${observation.value.toFixed(2)}/hr`
    : Math.round(observation.value).toLocaleString('en-CA');
}

function qualitySummary(...observations: Array<LabourObservation | null>) {
  const statuses = observations
    .flatMap((observation) => observation?.quality_flags ?? [])
    .filter((flag) => flag.startsWith('status:'))
    .map((flag) => flag.replace('status:', ''));
  return statuses.length ? `Codes ${statuses.join(' / ')}` : 'No code reported';
}

function Metric({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="bg-surface p-6 sm:p-8">
      <p className="font-mono text-2xl font-semibold text-subtle">{value}</p>
      <p className="mt-2 text-sm font-medium">{label}</p>
      <p className="mt-1 text-xs text-subtle">{note}</p>
    </div>
  );
}
