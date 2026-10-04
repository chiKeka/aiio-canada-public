'use client';

import {
  scenarioMoney as money,
  scenarioRate,
} from '@/lib/public-presentation.mjs';

import { useMemo, useState } from 'react';
import { WorkspaceMetric } from '@/components/workspace-metric';
import { ArrowRight, CircleAlert } from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  XAxis,
  YAxis,
} from 'recharts';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';
import {
  type MonthlyEscalationCalibration,
  type PlanningAssumptions,
} from '@/lib/planning-calibration';
import { buildDecisionOutlook } from '@/lib/decision-outlook';
import {
  allocateMonthlyDrivers,
  type SpendingProfile,
} from '@/lib/project-cashflow';
export type { MonthlyEscalationCalibration } from '@/lib/planning-calibration';

const chartConfig = {
  baseline_mom_pct: { label: 'Baseline % MoM', color: '#446c99' },
  ai_increment_mom_pct: { label: 'AI scenario (pp MoM)', color: '#8b5916' },
  combined_mom_pct: { label: 'Combined % MoM', color: '#086d64' },
  cumulative_baseline_pct: {
    label: 'Baseline % since price basis',
    color: '#446c99',
  },
  cumulative_lower_pct: { label: 'Low combined %', color: '#73838f' },
  cumulative_upper_pct: { label: 'High combined %', color: '#8b5916' },
  cumulative_combined_pct: { label: 'Central combined %', color: '#086d64' },
  baseSpend: { label: 'Base spend ($M)', color: '#446c99' },
  combinedSpend: { label: 'Scenario spend ($M)', color: '#086d64' },
} satisfies ChartConfig;

type Props = {
  selectedMitigations: string[];
  setSelectedMitigations: (value: string[]) => void;
  selectedMonth: string | null;
  setSelectedMonth: (value: string) => void;
  selectedDriver: string | null;
  setSelectedDriver: (value: string) => void;
  calibration: MonthlyEscalationCalibration;
  assumptions: PlanningAssumptions;
  budgetMillions: number;
  contingencyPct: number;
  spendingProfile: SpendingProfile;
  priceBasis: string;
  projectStart: number;
  durationYears: number;
  assetOutcome: string;
};

export function MonthlyEscalationOutlook({
  selectedMitigations,
  setSelectedMitigations,
  selectedMonth,
  setSelectedMonth,
  selectedDriver,
  setSelectedDriver,
  assumptions,
  budgetMillions,
  calibration,
  contingencyPct,
  spendingProfile,
  priceBasis,
  projectStart,
  durationYears,
  assetOutcome,
}: Props) {
  const [chartMode, setChartMode] = useState<
    'monthly' | 'cumulative' | 'spending'
  >('spending');
  const assessment = useMemo(
    () =>
      buildDecisionOutlook(
        {
          assetOutcome,
          durationYears,
          projectStart,
          assumptions,
          priceBasis,
          budgetMillions,
          spendingProfile,
        },
        calibration,
      ),
    [
      assetOutcome,
      assumptions,
      durationYears,
      projectStart,
      priceBasis,
      budgetMillions,
      spendingProfile,
      calibration,
    ],
  );
  if (!assessment)
    return (
      <section
        className="rounded-lg border border-caution/30 bg-surface p-6"
        role="alert"
      >
        Results withheld: enter a valid project window, positive budget and
        price basis no later than project start.
      </section>
    );
  const { active, cashflow, isOfficial } = assessment;
  const rows = active.monthly_series.map((row, i) => ({
    ...row,
    ...cashflow?.monthly[i],
  }));
  const selectedIndex = Math.max(
    0,
    rows.findIndex((row) => row.month === selectedMonth),
  );
  const month = rows[selectedIndex];
  // Proportional assumption allocation, not empirical monthly attribution.
  const contributions = allocateMonthlyDrivers(
    active.drivers.map((driver) => driver.contribution_pct_points),
    isOfficial ? null : month.ai_increment_mom_pct,
  );
  const drivers = active.drivers.map((driver, i) => ({
    ...driver,
    contribution_pct_points: contributions[i],
  }));
  const driver =
    drivers.find((row) => row.driver_id === selectedDriver) ?? drivers[0];
  const chartKeys =
    chartMode === 'spending'
      ? ['baseSpend', 'combinedSpend']
      : chartMode === 'monthly'
        ? ['baseline_mom_pct', 'ai_increment_mom_pct', 'combined_mom_pct']
        : [
            'cumulative_lower_pct',
            'cumulative_upper_pct',
            'cumulative_baseline_pct',
            'cumulative_combined_pct',
          ];
  return (
    <div className="grid min-h-0 gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(310px,.6fr)]">
      <section className="flex min-w-0 flex-col rounded-lg border border-line bg-surface p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Monthly outlook</h2>
          <span className="rounded-full border border-caution/30 px-3 py-1 text-xs text-caution">
            {isOfficial
              ? 'Scope-matched calibrated input'
              : 'Assumption scenario · not a validated estimate'}
          </span>
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-2 2xl:grid-cols-4">
          <WorkspaceMetric label="Base budget" value={money(budgetMillions)} />
          <WorkspaceMetric
            label="Total baseline escalation"
            value={money(cashflow?.baselineEscalation)}
          />
          <WorkspaceMetric
            label="Total AI scenario increment"
            value={money(cashflow?.aiIncrement)}
          />
          <WorkspaceMetric
            emphasized
            label="Total scenario spend"
            value={money(cashflow?.combinedSpend)}
          />
        </div>
        <p className="mt-2 text-xs leading-5 text-subtle">
          {priceBasis} price basis · budget excludes contingency. Low–high
          spend: {money(cashflow?.lowSpend)}–{money(cashflow?.highSpend)}.
          Contingency: {money((budgetMillions * contingencyPct) / 100)}{' '}
          (separate; not netted against escalation).
        </p>
        <div className="mt-4 flex flex-wrap gap-2" aria-label="Chart view">
          {(['spending', 'monthly', 'cumulative'] as const).map((mode) => (
            <button
              aria-pressed={chartMode === mode}
              className={`rounded-lg px-3 py-2 text-sm ${chartMode === mode ? 'bg-brand-soft text-brand' : 'border border-line text-subtle'}`}
              key={mode}
              onClick={() => setChartMode(mode)}
              type="button"
            >
              {mode === 'spending'
                ? 'Monthly spend'
                : mode === 'monthly'
                  ? 'MoM rates'
                  : 'Price indices'}
            </button>
          ))}
        </div>
        <div className="mt-3 h-[260px] min-w-0 rounded-lg bg-surface p-2">
          <ChartContainer
            className="h-full w-full aspect-auto"
            config={chartConfig}
          >
            <AreaChart
              data={rows}
              onClick={(state) => {
                const label = String(state?.activeLabel ?? '');
                if (rows.some((row) => row.month === label))
                  setSelectedMonth(label);
              }}
              margin={{ left: 0, right: 12, top: 12, bottom: 0 }}
            >
              <CartesianGrid stroke="#dde4e9" vertical={false} />
              <XAxis
                dataKey="month"
                interval="preserveStartEnd"
                tick={{ fill: '#586b78', fontSize: 12 }}
                tickFormatter={(value) => String(value).slice(2)}
              />
              <YAxis
                tick={{ fill: '#586b78', fontSize: 12 }}
                tickFormatter={(value) =>
                  chartMode === 'spending' ? `$${value}M` : `${value}%`
                }
                width={60}
              />
              <ChartTooltip
                content={
                  <ChartTooltipContent
                    formatter={(value, name) => (
                      <span className="flex w-full justify-between gap-4 text-xs">
                        <span>
                          {chartConfig[String(name) as keyof typeof chartConfig]
                            ?.label ?? String(name)}
                        </span>
                        <b>
                          {chartMode === 'spending'
                            ? money(Number(value))
                            : scenarioRate(Number(value))}
                        </b>
                      </span>
                    )}
                  />
                }
              />
              {chartKeys.map((key, i) => (
                <Area
                  dataKey={key}
                  fill={i === chartKeys.length - 1 ? '#086d64' : 'transparent'}
                  fillOpacity={0.12}
                  key={key}
                  stroke={`var(--color-${key})`}
                  strokeDasharray={i === 0 ? '5 4' : undefined}
                  strokeWidth={i === chartKeys.length - 1 ? 2.5 : 1.5}
                  type="stepAfter"
                />
              ))}
              <ReferenceLine
                stroke="#586b78"
                strokeDasharray="4 4"
                x={month.month}
              />
            </AreaChart>
          </ChartContainer>
        </div>
        <div
          className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-subtle"
          aria-label="Chart legend"
        >
          {chartKeys.map((key, i) => (
            <span className="flex items-center gap-2" key={key}>
              <span
                aria-hidden="true"
                className="w-5 border-t-2"
                style={{
                  borderColor:
                    chartConfig[key as keyof typeof chartConfig].color,
                  borderStyle: i === 0 ? 'dashed' : 'solid',
                }}
              />
              {chartConfig[key as keyof typeof chartConfig].label}
            </span>
          ))}
        </div>
        <p className="mt-2 text-xs text-subtle">
          Monthly scenario rates are held constant within each annual scenario
          period, shifted by the assumed lag—not observed monthly activity.
          Low/high paths are sensitivity cases, not confidence intervals.
        </p>
        <label className="mt-4 block text-sm">
          <span className="flex justify-between">
            <strong>Selected month · {month.month}</strong>
            <span>
              {selectedIndex + 1} / {rows.length}
            </span>
          </span>
          <input
            aria-label="Selected project month"
            aria-valuetext={month.month}
            className="scenario-range mt-3 w-full"
            max={rows.length - 1}
            min={0}
            onChange={(event) =>
              setSelectedMonth(rows[Number(event.target.value)].month)
            }
            type="range"
            value={selectedIndex}
          />
        </label>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <WorkspaceMetric
            label="Base spend this month"
            value={money(month.baseSpend)}
          />
          <WorkspaceMetric
            label="AI scenario dollars this month"
            value={money(month.aiIncrement)}
          />
          <WorkspaceMetric
            label="Scenario spend this month"
            value={money(month.combinedSpend)}
          />
          <WorkspaceMetric
            label="Combined MoM this month"
            value={
              month.combined_mom_pct === null
                ? '—'
                : `${scenarioRate(month.combined_mom_pct)}%`
            }
          />
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {(['primary', 'secondary'] as const).map((tier) => (
            <div key={tier}>
              <h3 className="text-sm font-medium">
                {tier === 'primary' ? 'Primary drivers' : 'Secondary effects'} ·{' '}
                {month.month}
              </h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {drivers
                  .filter((row) => row.tier === tier)
                  .map((row) => (
                    <button
                      aria-pressed={driver?.driver_id === row.driver_id}
                      className={`rounded-lg border px-3 py-2 text-left text-xs ${driver?.driver_id === row.driver_id ? 'border-caution/30 bg-caution-soft text-caution' : 'border-line text-subtle'}`}
                      key={row.driver_id}
                      onClick={() => setSelectedDriver(row.driver_id)}
                      type="button"
                    >
                      {row.label}
                      <span className="block font-mono">
                        {row.contribution_pct_points === null
                          ? 'Not allocated'
                          : `${scenarioRate(row.contribution_pct_points)} pp MoM`}
                      </span>
                    </button>
                  ))}
              </div>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-subtle">
          Driver allocation assumes 82% primary / 18% secondary; graph weights
          split the primary share. This explains the scenario, not measured
          causation. No observed market index is added again to the assumed
          baseline.
        </p>
      </section>
      <section className="flex min-w-0 flex-col gap-4">
        <NodalPanel calibration={active} driver={driver} month={month.month} />
        <MitigationPanel
          calibration={active}
          driver={driver}
          month={month.month}
          selected={selectedMitigations}
          setSelected={setSelectedMitigations}
        />
      </section>
    </div>
  );
}

type Driver = MonthlyEscalationCalibration['drivers'][number] | undefined;
function NodalPanel({
  calibration,
  driver,
  month,
}: {
  calibration: MonthlyEscalationCalibration;
  driver: Driver;
  month: string;
}) {
  const nodes =
    driver?.node_ids
      .map((id) => calibration.nodes.find((node) => node.node_id === id))
      .filter((node) => node !== undefined) ?? [];
  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <h3 className="text-sm text-brand">Driver path · {month}</h3>
      <div className="mt-5 flex items-center gap-2">
        {nodes.slice(0, 3).map((node, i) => (
          <div className="contents" key={node.node_id}>
            {i > 0 ? (
              <ArrowRight className="size-4 shrink-0 text-caution" />
            ) : null}
            <div className="flex min-h-24 min-w-0 flex-1 items-center justify-center rounded-lg border border-brand/30 bg-surface p-2 text-center text-xs">
              {node.label}
            </div>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm">{driver?.label ?? 'Select a driver'}</p>
      <p className="mt-1 font-mono text-caution">
        {driver?.contribution_pct_points == null
          ? 'Monthly allocation unavailable'
          : `${scenarioRate(driver.contribution_pct_points)} pp MoM (assumed)`}
      </p>
      <p className="mt-2 text-xs text-subtle">
        Path structure is illustrative; upstream arrows do not add another cost
        contribution.
      </p>
    </div>
  );
}

function MitigationPanel({
  calibration,
  driver,
  month,
  selected,
  setSelected,
}: {
  calibration: MonthlyEscalationCalibration;
  driver: Driver;
  month: string;
  selected: string[];
  setSelected: (value: string[]) => void;
}) {
  const rows = calibration.mitigations.filter(
    (item) => item.driver_id === driver?.driver_id,
  );
  const owners = {
    now: 'Project sponsor',
    design: 'Design lead',
    procurement: 'Procurement lead',
    delivery: 'Construction manager',
  };
  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <h3 className="text-sm text-brand">Decision response · {month}</h3>
      <p className="mt-3 text-lg">{driver?.label ?? 'Select a driver'}</p>
      <p className="mt-1 text-xs text-subtle">
        Consider before exposure in this month. Timing and owners are suggested,
        not assigned.
      </p>
      <div className="mt-4 grid gap-3">
        {rows.length ? (
          rows.map((item) => {
            const key = `${driver?.driver_id}:${item.label}`;
            const checked = selected.includes(key);
            return (
              <button
                aria-pressed={checked}
                className={`rounded-lg border p-3 text-left ${checked ? 'border-brand bg-brand-soft' : 'border-line bg-surface'}`}
                key={key}
                onClick={() =>
                  setSelected(
                    checked
                      ? selected.filter((value) => value !== key)
                      : [...selected, key],
                  )
                }
                type="button"
              >
                <span className="block text-sm">
                  {checked ? '✓ ' : ''}
                  {item.label}
                </span>
                <span className="mt-2 block text-xs text-subtle">
                  {item.timing} · {owners[item.timing]}
                </span>
                <span className="mt-1 block text-xs text-subtle">
                  Evidence needed: supplier capacity/lead-time confirmation and
                  a costed feasibility review.
                </span>
              </button>
            );
          })
        ) : (
          <p className="text-sm text-subtle">
            No reviewed strategy mapped to this secondary effect. Escalate to
            the project risk review.
          </p>
        )}
      </div>
      <p className="mt-4 flex items-center gap-2 text-xs text-caution">
        <CircleAlert className="size-4 shrink-0" />
        {selected.length} actions selected in this session · no savings
        credited.
      </p>
    </div>
  );
}
