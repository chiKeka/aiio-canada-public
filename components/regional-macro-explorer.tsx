'use client';

import { useMemo, useState } from 'react';
import { Activity, ExternalLink } from 'lucide-react';
import { EvidencePill } from '@/components/site-shell';

import {
  NativeSelect,
  NativeSelectOption,
} from '@/components/ui/native-select';
import regionalMacroControls from '@/data/model-runs/regional_macro_controls_canada_v0.1.json';

const metricOrder = [
  'MACRO_CPI_ALL_ITEMS_QAVG',
  'MACRO_CPI_SHELTER_QAVG',
  'MACRO_WEEKLY_EARNINGS_ALL_INDUSTRIES_QAVG',
  'MACRO_WEEKLY_EARNINGS_CONSTRUCTION_QAVG',
  'MACRO_POPULATION_QUARTERLY',
  'MACRO_HOUSING_STARTS_SAAR_QAVG',
  'MACRO_NON_RESIDENTIAL_BUILDING_INVESTMENT_QSUM',
] as const;

const shortLabels: Record<(typeof metricOrder)[number], string> = {
  MACRO_CPI_ALL_ITEMS_QAVG: 'All-items CPI',
  MACRO_CPI_SHELTER_QAVG: 'Shelter CPI',
  MACRO_WEEKLY_EARNINGS_ALL_INDUSTRIES_QAVG: 'All-industry earnings',
  MACRO_WEEKLY_EARNINGS_CONSTRUCTION_QAVG: 'Construction earnings',
  MACRO_POPULATION_QUARTERLY: 'Population',
  MACRO_HOUSING_STARTS_SAAR_QAVG: 'Housing starts',
  MACRO_NON_RESIDENTIAL_BUILDING_INVESTMENT_QSUM: 'Non-residential investment',
};

type MetricId = (typeof metricOrder)[number];
type LatestControl = (typeof regionalMacroControls.latest_controls)[number];

export function RegionalMacroExplorer() {
  const geographies = useMemo(() => {
    const labels = new Map<string, string>();
    for (const item of regionalMacroControls.latest_controls) {
      labels.set(item.geography_id, item.geography_label);
    }
    return Array.from(labels, ([id, label]) => ({ id, label })).sort((a, b) =>
      a.label.localeCompare(b.label, 'en-CA'),
    );
  }, []);
  const [geographyId, setGeographyId] = useState('PR_48');
  const selected = regionalMacroControls.latest_controls.filter(
    (item) => item.geography_id === geographyId,
  );
  const selectedByMetric = new Map(
    selected.map((item) => [item.indicator_id, item]),
  );
  const geographyLabel = geographies.find(
    (item) => item.id === geographyId,
  )?.label;
  const coverage = regionalMacroControls.metric_coverage as Record<
    MetricId,
    { source_url: string }
  >;

  return (
    <section className="border-t border-line bg-workspace">
      <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px] lg:items-end">
          <div>
            <div className="flex items-center gap-2 text-brand">
              <Activity className="size-4" />
              <h2 className="text-xl font-medium">
                Regional macro control panel
              </h2>
            </div>
            <p className="mt-3 max-w-4xl text-sm leading-6 text-subtle">
              Seven separate Statistics Canada indicators provide dated regional
              context through {regionalMacroControls.common_latest_period_end}.
              Select a jurisdiction to compare the latest year-over-year
              movement without collapsing unlike measures into a score.
            </p>
          </div>
          <label className="block">
            <span className="mb-2 block font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-subtle">
              Jurisdiction
            </span>
            <NativeSelect
              value={geographyId}
              onChange={(event) => setGeographyId(event.target.value)}
              aria-label="Regional macro jurisdiction"
            >
              {geographies.map((item) => (
                <NativeSelectOption key={item.id} value={item.id}>
                  {item.label}
                </NativeSelectOption>
              ))}
            </NativeSelect>
          </label>
        </div>

        <div className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {metricOrder.map((metricId) => {
            const item = selectedByMetric.get(metricId) as
              | LatestControl
              | undefined;
            return (
              <article
                className="rounded-lg border border-line bg-white p-5"
                key={metricId}
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-xs font-medium text-subtle">
                    {shortLabels[metricId]}
                  </p>
                  <EvidencePill
                    status={item?.evidence_status ?? 'unavailable'}
                  />
                </div>
                <p
                  className={`mt-4 font-mono text-2xl font-semibold ${item?.year_over_year_change_percent !== undefined && item?.year_over_year_change_percent !== null && item.year_over_year_change_percent < 0 ? 'text-caution' : 'text-brand'}`}
                >
                  {formatChange(item?.year_over_year_change_percent)}
                </p>
                <p className="mt-1 min-h-10 text-[11px] leading-5 text-subtle">
                  {item
                    ? formatValue(item)
                    : `${geographyLabel ?? geographyId}: not published in the selected source table`}
                </p>
                <a
                  className="mt-4 inline-flex items-center gap-1 text-[10px] font-medium text-brand hover:underline"
                  href={item?.source_url ?? coverage[metricId].source_url}
                  rel="noreferrer"
                  target="_blank"
                >
                  Official source <ExternalLink className="size-3" />
                </a>
              </article>
            );
          })}
        </div>

        <div className="mt-5 rounded-lg border border-caution/30 bg-workspace p-4 text-sm leading-6 text-caution">
          Descriptive controls only. CPI is not a construction bid-price index;
          earnings are not labour availability; housing starts are not
          affordability; population is not construction capacity; and investment
          is not a public-project outcome. These values do not identify an AI
          effect, calibrate the scenario, or translate into project cost or
          delay.
        </div>
      </div>
    </section>
  );
}

function formatChange(value: number | null | undefined) {
  if (value === null || value === undefined) return 'Not published';
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}% YoY`;
}

function formatValue(item: LatestControl) {
  if (item.value === null)
    return `${item.geography_label}: source value unavailable`;
  if (item.indicator_id === 'MACRO_POPULATION_QUARTERLY') {
    return `${item.value.toLocaleString('en-CA', { maximumFractionDigits: 0 })} persons`;
  }
  if (item.indicator_id === 'MACRO_NON_RESIDENTIAL_BUILDING_INVESTMENT_QSUM') {
    return `$${(item.value / 1_000_000_000).toFixed(2)}B in the quarter`;
  }
  if (item.indicator_id === 'MACRO_HOUSING_STARTS_SAAR_QAVG') {
    return `${item.value.toLocaleString('en-CA', { maximumFractionDigits: 0 })} units at SAAR`;
  }
  if (item.indicator_id.includes('EARNINGS')) {
    return `$${item.value.toLocaleString('en-CA', { maximumFractionDigits: 2 })} per week`;
  }
  return `${item.value.toFixed(1)} · index 2002=100`;
}
