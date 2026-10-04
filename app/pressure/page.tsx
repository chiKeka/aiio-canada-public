import { uniqueMaterialSignals } from '@/lib/public-presentation.mjs';
import { AlertTriangle } from 'lucide-react';

import {
  EvidencePill,
  PageIntro,
  SiteFooter,
  ResearchShell,
} from '@/components/site-shell';
import releaseData from '@/public/data/latest.json';

export default function PressurePage() {
  const prices = releaseData.baseline.construction_prices;
  const materialScreen = (
    releaseData as typeof releaseData & {
      material_cost_screen?: MaterialCostScreen;
    }
  ).material_cost_screen;
  const projectExposure = (
    releaseData as typeof releaseData & {
      public_project_exposure?: PublicProjectExposure;
    }
  ).public_project_exposure;
  const trades = releaseData.scenario.trade_pressure_order;
  const outcomes = releaseData.scenario.public_delivery_pressure_order;
  const maxTrade = Math.max(...trades.map((item) => item.high));
  const maxOutcome = Math.max(...outcomes.map((item) => item.high));
  return (
    <ResearchShell>
      <PageIntro
        eyebrow="Pressure monitor"
        title="Market pressure"
        description="Observed construction-price signals establish the baseline. The graph layer then traces a clearly labelled scenario through resources and public delivery without converting a diagnostic index into unsupported dollars, workers or delay days."
      />
      <section className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <EvidencePill status="observed" />
              <span className="font-mono text-xs text-subtle">
                STATCAN_BCPI_18100289
              </span>
            </div>
            <h2 className="mt-3 text-2xl font-medium tracking-[-0.025em]">
              Latest Alberta construction-price baseline
            </h2>
          </div>
          <span className="hidden font-mono text-xs text-subtle sm:block">
            2023=100 · not seasonally adjusted
          </span>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {prices.map((price) => (
            <article
              className="rounded-lg border border-line bg-surface p-5"
              key={`${price.indicator_id}-${price.geography_id}`}
            >
              <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-subtle">
                {price.geography_id === 'CMA_825' ? 'Calgary' : 'Edmonton'} ·{' '}
                {price.indicator_id.includes('SCHOOL')
                  ? 'School'
                  : 'Non-residential'}
              </p>
              <p className="mt-5 font-mono text-2xl font-semibold text-brand">
                {price.value.toFixed(1)}
              </p>
              <p className="mt-1 text-xs text-subtle">
                {price.quarter_over_quarter_percent > 0 ? '+' : ''}
                {price.quarter_over_quarter_percent.toFixed(2)}% quarter over
                quarter
              </p>
              <p className="mt-4 border-t border-line pt-3 text-[10px] text-subtle">
                Period ending {price.period_end}
              </p>
            </article>
          ))}
        </div>
      </section>
      {materialScreen ? <MaterialCostPanel screen={materialScreen} /> : null}
      {projectExposure ? (
        <PublicProjectExposurePanel exposure={projectExposure} />
      ) : null}
      <section className="bg-surface text-ink">
        <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8">
          <div className="mb-10 grid gap-5 border-b border-line pb-8 lg:grid-cols-[1fr_auto]">
            <div>
              <div className="flex items-center gap-2">
                <EvidencePill status="scenario" />
                <EvidencePill status="assumed" />
              </div>
              <h2 className="mt-4 text-2xl font-medium tracking-[-0.035em]">
                $50B counterfactual diagnostic · pressure ordering
              </h2>
            </div>
            <p className="max-w-md text-sm leading-6 text-subtle">
              Low, central and high cases vary assumed pathway weights and local
              retention. Read them alongside the interpretation boundary below.
            </p>
          </div>
          <div className="grid gap-8 lg:grid-cols-2">
            <PressureList
              title="Trades pinched first"
              items={trades}
              max={maxTrade}
            />
            <PressureList
              title="Public delivery exposure"
              items={outcomes}
              max={maxOutcome}
            />
          </div>
          <div className="mt-10 flex gap-3 rounded-lg border border-caution/30 bg-caution-soft p-5 text-sm leading-6 text-caution">
            <AlertTriangle className="mt-0.5 size-5 shrink-0" />
            <p>
              The graph receives 46% of scenario capex; 54% is deliberately
              outside it. Display values use raw ÷ (1 + raw) only to keep the
              index in [0,1). They cannot be read as probabilities, percentage
              cost increases or schedule delays. Calibration is a release gate.
            </p>
          </div>
        </div>
      </section>
      <SiteFooter />
    </ResearchShell>
  );
}

type MaterialObservation = {
  geography_id: string;
  archetype: string;
  component: string;
  index_value: number;
  year_over_year_percent_change: number | null;
};

type MaterialCostScreen = {
  period_end: string;
  observations: MaterialObservation[];
};

type ExposureSummary = {
  asset_class: string;
  project_count: number;
  unresolved_sponsor_signal_count: number;
  reported_cost_project_count: number;
  overlap_project_count: number;
  overlap_with_cost_and_complete_schedule_count: number;
  indicative_cost_allocated_to_window_cad: number;
};

type PublicProjectExposure = {
  window: { start_year: number; end_year: number };
  screened_project_count: number;
  asset_class_summaries: ExposureSummary[];
};

function MaterialCostPanel({ screen }: { screen: MaterialCostScreen }) {
  const observations = uniqueMaterialSignals(screen.observations)
    .filter((item) => item.year_over_year_percent_change !== null)
    .sort(
      (left, right) =>
        Math.abs(right.year_over_year_percent_change ?? 0) -
        Math.abs(left.year_over_year_percent_change ?? 0),
    )
    .slice(0, 8);
  return (
    <section className="border-t border-line bg-white">
      <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8">
        <div className="grid gap-4 border-b border-line pb-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <div className="flex items-center gap-2">
              <EvidencePill status="observed" />
              <EvidencePill status="inferred" />
            </div>
            <h2 className="mt-3 text-2xl font-medium tracking-[-0.025em]">
              Shared material-cost signals
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-subtle">
              Largest absolute year-over-year movements. Each identical
              city/component series appears once, with its asset mappings
              listed.
            </p>
          </div>
          <span className="font-mono text-xs text-subtle">
            Period ending {screen.period_end}
          </span>
        </div>
        <div className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {observations.map((item) => {
            const change = item.year_over_year_percent_change ?? 0;
            return (
              <article
                className="rounded-lg border border-line bg-surface p-5"
                key={`${item.geography_id}-${item.archetype}-${item.component}`}
              >
                <p className="font-mono text-[10px] uppercase tracking-[0.08em] text-subtle">
                  {item.geography_id === 'CMA_825' ? 'Calgary' : 'Edmonton'} ·{' '}
                  {item.archetypes.map(humanize).join(' / ')}
                </p>
                <h3 className="mt-3 text-sm font-medium text-ink">
                  {humanize(item.component)}
                </h3>
                <div className="mt-5 flex items-end justify-between">
                  <span className="font-mono text-2xl font-semibold text-brand">
                    {item.index_value.toFixed(1)}
                  </span>
                  <span
                    className={`font-mono text-xs ${change >= 0 ? 'text-caution' : 'text-brand'}`}
                  >
                    {change >= 0 ? '+' : ''}
                    {change.toFixed(1)}% YoY
                  </span>
                </div>
              </article>
            );
          })}
        </div>
        <p className="mt-5 text-xs leading-5 text-subtle">
          Factory is an industrial-building proxy, not a data-centre index. BCPI
          does not measure commodity quantities, lead times, or physical
          capacity.
        </p>
      </div>
    </section>
  );
}

function PublicProjectExposurePanel({
  exposure,
}: {
  exposure: PublicProjectExposure;
}) {
  return (
    <section className="border-t border-line bg-workspace">
      <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8 lg:py-8">
        <div className="grid gap-4 border-b border-line pb-7 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <div className="flex items-center gap-2">
              <EvidencePill status="observed" />
              <EvidencePill status="inferred" />
            </div>
            <h2 className="mt-3 text-2xl font-medium tracking-[-0.025em]">
              Public-delivery asset overlap
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-subtle">
              {exposure.screened_project_count} delivery-relevant Alberta
              records, excluding classified AI and enabling-power projects.
              Overlap is a scheduling screen, not proof of competition or delay.
            </p>
          </div>
          <span className="font-mono text-xs text-subtle">
            Window {exposure.window.start_year}–{exposure.window.end_year}
          </span>
        </div>
        <div className="mt-7 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {exposure.asset_class_summaries.map((item) => (
            <article
              className="rounded-lg border border-line bg-surface p-5"
              key={item.asset_class}
            >
              <h3 className="text-sm font-medium">
                {humanize(item.asset_class)}
              </h3>
              <div className="mt-5 grid grid-cols-3 gap-3">
                <ExposureMetric
                  label="records"
                  value={item.project_count.toLocaleString('en-CA')}
                />
                <ExposureMetric
                  label="overlap"
                  value={item.overlap_project_count.toLocaleString('en-CA')}
                />
                <ExposureMetric
                  label="costed + dated"
                  value={item.overlap_with_cost_and_complete_schedule_count.toLocaleString(
                    'en-CA',
                  )}
                />
              </div>
              <p className="mt-5 border-t border-line pt-4 font-mono text-sm font-semibold text-brand">
                {formatCad(item.indicative_cost_allocated_to_window_cad)}{' '}
                <span className="font-sans text-[10px] font-normal text-subtle">
                  indicatively allocated to window
                </span>
              </p>
              <p className="mt-2 text-[10px] text-subtle">
                {item.unresolved_sponsor_signal_count} sponsor signals
                unresolved · {item.reported_cost_project_count} records report
                cost
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function ExposureMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-mono text-lg font-semibold text-ink">{value}</p>
      <p className="mt-1 text-[10px] text-subtle">{label}</p>
    </div>
  );
}

function humanize(value: string) {
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatCad(value: number) {
  return value >= 1_000_000_000
    ? `$${(value / 1_000_000_000).toFixed(2)}B`
    : `$${(value / 1_000_000).toFixed(0)}M`;
}

function PressureList({
  title,
  items,
  max,
}: {
  title: string;
  items: Array<{
    node_id: string;
    label: string;
    low: number;
    central: number;
    high: number;
  }>;
  max: number;
}) {
  return (
    <div>
      <h3 className="mb-5 text-sm font-medium text-subtle">{title}</h3>
      <div className="space-y-5">
        {items.map((item, index) => (
          <div key={item.node_id}>
            <div className="mb-2 flex items-center justify-between text-xs">
              <span className="flex items-center gap-2">
                <span className="font-mono text-subtle">0{index + 1}</span>
                {item.label}
              </span>
              <span className="font-mono text-subtle">
                {item.low.toFixed(2)}–{item.high.toFixed(2)}
              </span>
            </div>
            <div className="relative h-2 rounded-full bg-workspace">
              <div
                className="absolute h-full rounded-full bg-brand"
                style={{ width: `${(item.central / max) * 100}%` }}
              />
              <span
                className="absolute top-1/2 size-3 -translate-y-1/2 rounded-full border-2 border-line bg-caution-soft"
                style={{ left: `calc(${(item.high / max) * 100}% - 6px)` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
