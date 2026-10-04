'use client';

import { useMemo, useState } from 'react';
import { WorkspaceScrollRegion } from '@/components/workspace-scroll-region';

export type NationalLabourObservation = {
  noc_code: string;
  occupation_label: string;
  trade_node_id: string;
  statistic: string;
  value: number | null;
  unit: string;
  geography_id: string;
  geography_label: string;
  period_end: string;
  quality_flags: string[];
};

export type NationalLabourAvailability = {
  period_end: string;
  geography_scope: string;
  warning: string;
  coverage: Array<{
    geography_id: string;
    geography_label: string;
    observed_cells: number;
    not_published_cells: number;
    total_cells: number;
    coverage_percent: number;
  }>;
  observations: NationalLabourObservation[];
};

export type NationalWorkforceObservation = {
  noc_code: string;
  occupation_label: string;
  trade_node_id: string;
  statistic: string;
  value: number;
  unit: string;
  geography_id: string;
  geography_label: string;
  period_start: string;
  period_end: string;
  quality_flags: string[];
};

export type NationalWorkforceStock = {
  period_start: string;
  period_end: string;
  release_date: string;
  warning: string;
  coverage: Array<{
    geography_id: string;
    geography_label: string;
    published_cells: number;
    zero_filler_cells: number;
    total_cells: number;
    coverage_percent: number;
  }>;
  observations: NationalWorkforceObservation[];
};

export type NationalLabourPressure = {
  metric_label: string;
  vacancy_period_end: string;
  workforce_period_end: string;
  interpretation: string;
  occupation_diagnostics: Array<{
    geography_id: string;
    noc_code: string;
    vacancies_per_1_000_2021_employed: number | null;
    availability: string;
  }>;
};

type OccupationRow = {
  nocCode: string;
  occupation: string;
  tradeNode: string;
  vacancies: NationalLabourObservation | null;
  wage: NationalLabourObservation | null;
  workforce: NationalWorkforceObservation | null;
  pressure: NationalLabourPressure['occupation_diagnostics'][number] | null;
};

export function LabourMarketExplorer({
  labour,
  workforce,
  pressure,
}: {
  labour: NationalLabourAvailability;
  workforce?: NationalWorkforceStock;
  pressure?: NationalLabourPressure;
}) {
  const initialGeography = labour.coverage.some(
    (item) => item.geography_id === 'PR_48',
  )
    ? 'PR_48'
    : labour.coverage[0]?.geography_id;
  const [geographyId, setGeographyId] = useState(initialGeography);
  const coverage = labour.coverage.find(
    (item) => item.geography_id === geographyId,
  );
  const workforceCoverage = workforce?.coverage.find(
    (item) => item.geography_id === geographyId,
  );
  const occupations = useMemo(() => {
    const groups = new Map<string, OccupationRow>();
    for (const observation of labour.observations) {
      if (observation.geography_id !== geographyId) continue;
      const existing = groups.get(observation.noc_code) ?? {
        nocCode: observation.noc_code,
        occupation: observation.occupation_label,
        tradeNode: observation.trade_node_id,
        vacancies: null,
        wage: null,
        workforce: null,
        pressure: null,
      };
      if (observation.statistic === 'Job vacancies')
        existing.vacancies = observation;
      if (observation.statistic === 'Average offered hourly wage')
        existing.wage = observation;
      groups.set(observation.noc_code, existing);
    }
    for (const observation of workforce?.observations ?? []) {
      if (observation.geography_id !== geographyId) continue;
      const existing = groups.get(observation.noc_code) ?? {
        nocCode: observation.noc_code,
        occupation: observation.occupation_label,
        tradeNode: observation.trade_node_id,
        vacancies: null,
        wage: null,
        workforce: null,
        pressure: null,
      };
      existing.workforce = observation;
      groups.set(observation.noc_code, existing);
    }
    for (const diagnostic of pressure?.occupation_diagnostics ?? []) {
      if (diagnostic.geography_id !== geographyId) continue;
      const existing = groups.get(diagnostic.noc_code);
      if (existing) existing.pressure = diagnostic;
    }
    return Array.from(groups.values());
  }, [
    geographyId,
    labour.observations,
    pressure?.occupation_diagnostics,
    workforce?.observations,
  ]);

  return (
    <section className="border-t border-line bg-white">
      <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px] lg:items-end">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.14em] text-brand">
              Common provincial labour evidence
            </p>
            <h2 className="mt-2 text-2xl font-medium">
              Provincial trade labour snapshot
            </h2>
            <p className="mt-3 max-w-4xl text-sm leading-6 text-subtle">
              Current vacancy and offered-wage signals come from Statistics
              Canada table 14-10-0444-01 · quarter ending {labour.period_end}.
              The structural employed stock comes from the 2021 Census reference
              week. Select a province or territory without substituting a
              Canada-wide average.
            </p>
          </div>
          <label className="text-sm font-medium" htmlFor="labour-geography">
            Province or territory
            <select
              className="mt-2 w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-sm"
              id="labour-geography"
              onChange={(event) => setGeographyId(event.target.value)}
              value={geographyId}
            >
              {labour.coverage.map((item) => (
                <option key={item.geography_id} value={item.geography_id}>
                  {item.geography_label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {coverage ? (
          <div className="mt-6 grid gap-px overflow-hidden rounded-lg border border-line bg-workspace sm:grid-cols-2 lg:grid-cols-4">
            <CoverageMetric
              label="Cells reported"
              value={`${coverage.observed_cells} of ${coverage.total_cells}`}
            />
            <CoverageMetric
              label="Current-signal coverage"
              value={`${coverage.coverage_percent.toFixed(1)}%`}
            />
            <CoverageMetric
              label="Not published"
              value={String(coverage.not_published_cells)}
            />
            <CoverageMetric
              label="2021 workforce cells"
              value={
                workforceCoverage
                  ? `${workforceCoverage.published_cells} of ${workforceCoverage.total_cells}`
                  : 'Not loaded'
              }
            />
          </div>
        ) : null}

        <WorkspaceScrollRegion
          label="Trade labour observations"
          live="polite"
          className="mt-6 rounded-lg border border-line"
        >
          <table className="w-full min-w-[1080px] border-collapse text-left text-sm">
            <caption className="sr-only">
              Trade labour observations for{' '}
              {coverage?.geography_label ?? 'the selected geography'}
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
                  2021 employed stock
                </th>
                <th className="px-4 py-3" scope="col">
                  Current vacancies
                </th>
                <th className="px-4 py-3" scope="col">
                  Cross-vintage /1,000
                </th>
                <th className="px-4 py-3" scope="col">
                  Offered wage
                </th>
                <th className="px-4 py-3" scope="col">
                  JVWS quality
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
                    {formatWorkforceValue(item.workforce)}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {formatLabourValue(item.vacancies, 'vacancies')}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {formatPressureValue(item.pressure)}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    {formatLabourValue(item.wage, 'wage')}
                  </td>
                  <td className="px-4 py-3 text-xs text-subtle">
                    Vacancies: {qualityCode(item.vacancies)} · Wage:{' '}
                    {qualityCode(item.wage)}
                  </td>
                </tr>
              ))}
              {occupations.length === 0 ? (
                <tr>
                  <td className="px-4 py-5 text-subtle" colSpan={7}>
                    No observations are available for this geography.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </WorkspaceScrollRegion>
        <div className="mt-4 rounded-lg border border-caution/30 bg-workspace p-4 text-sm leading-6 text-caution">
          {labour.warning}
        </div>
        {workforce ? (
          <div className="mt-3 rounded-lg border border-line bg-workspace p-4 text-sm leading-6 text-brand">
            {workforce.warning}
          </div>
        ) : null}
        {pressure ? (
          <div className="mt-3 rounded-lg border border-line bg-workspace p-4 text-sm leading-6 text-subtle">
            <span className="font-medium">Screening metric:</span>{' '}
            {pressure.interpretation} Numerator: {pressure.vacancy_period_end};
            denominator: {pressure.workforce_period_end}.
          </div>
        ) : null}
      </div>
    </section>
  );
}

function CoverageMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface p-4">
      <p className="font-mono text-xl font-semibold text-brand">{value}</p>
      <p className="mt-1 text-xs text-subtle">{label}</p>
    </div>
  );
}

function formatLabourValue(
  observation: NationalLabourObservation | null,
  kind: 'vacancies' | 'wage',
) {
  if (!observation) return 'Not available';
  if (observation.value === null) return missingValueLabel(observation);
  return kind === 'wage'
    ? `$${observation.value.toFixed(2)}/hr`
    : Math.round(observation.value).toLocaleString('en-CA');
}

function formatWorkforceValue(
  observation: NationalWorkforceObservation | null,
) {
  if (!observation) return 'Not available';
  const value = Math.round(observation.value).toLocaleString('en-CA');
  return observation.quality_flags.includes('census_zero_filler')
    ? `${value} (published zero filler)`
    : value;
}

function formatPressureValue(
  diagnostic: NationalLabourPressure['occupation_diagnostics'][number] | null,
) {
  if (!diagnostic || diagnostic.vacancies_per_1_000_2021_employed === null)
    return 'Not comparable';
  return diagnostic.vacancies_per_1_000_2021_employed.toFixed(1);
}

function qualityCode(observation: NationalLabourObservation | null) {
  return (
    observation?.quality_flags
      .find((flag) => flag.startsWith('status:'))
      ?.replace('status:', '') ?? 'not reported'
  );
}

function missingValueLabel(observation: NationalLabourObservation) {
  const code = qualityCode(observation);
  if (code === 'F') return 'Unreliable (F)';
  if (code.toLowerCase() === 'x') return 'Confidential (x)';
  if (code === '..') return 'Not available (..)';
  return 'Not published';
}
