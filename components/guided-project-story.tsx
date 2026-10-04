'use client';
import Link from 'next/link';

import {
  scenarioMoney as money,
  scenarioRate,
} from '@/lib/public-presentation.mjs';

import { useState } from 'react';
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from 'recharts';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart';
import { Button } from '@/components/ui/button';
import { type buildDecisionAnalysis, METROS } from '@/lib/decision-analysis';
import {
  type buildDecisionOutlook,
  type DecisionInputs,
  decisionAction,
} from '@/lib/decision-outlook';
import {
  allocateMonthlyDrivers,
  SPENDING_PROFILES,
} from '@/lib/project-cashflow';

const steps = [
  'Your project',
  'Monthly exposure',
  'Why it happens',
  'What to do',
];
const card = 'rounded-lg border border-line bg-surface p-4';
const config = {
  baseline_mom_pct: { label: 'Baseline % MoM', color: '#446c99' },
  ai_increment_mom_pct: { label: 'AI scenario pp MoM', color: '#8b5916' },
};

export function GuidedProjectStory({
  selectedMonth,
  setSelectedMonth,
  selectedDriver,
  setSelectedDriver,
  analysis,
  assessment,
  inputs,
  projectName,
  approvalStage,
  planningChecks,
  onExplore,
}: {
  selectedMonth: string | null;
  setSelectedMonth: (value: string) => void;
  selectedDriver: string | null;
  setSelectedDriver: (value: string) => void;
  analysis: ReturnType<typeof buildDecisionAnalysis>;
  assessment: ReturnType<typeof buildDecisionOutlook>;
  inputs: DecisionInputs;
  projectName: string;
  approvalStage: string;
  planningChecks: string;
  onExplore: (view: 'outlook' | 'cockpit' | 'evidence') => void;
}) {
  const [step, setStep] = useState(0);
  if (!assessment)
    return (
      <section className={card} role="alert">
        Correct the project dates, price basis or budget to build this briefing.
      </section>
    );
  const { active, cashflow, isOfficial } = assessment;
  const monthIndex = Math.max(
    0,
    active.monthly_series.findIndex((row) => row.month === selectedMonth),
  );
  const month = active.monthly_series[monthIndex];
  const spend = cashflow?.monthly[monthIndex];
  const allocations = allocateMonthlyDrivers(
    active.drivers.map((driver) => driver.contribution_pct_points),
    isOfficial ? null : month.ai_increment_mom_pct,
  );
  const drivers = active.drivers
    .map((driver, index) => ({ ...driver, allocation: allocations[index] }))
    .sort((a, b) => (b.allocation ?? -1) - (a.allocation ?? -1));
  const driver =
    drivers.find((item) => item.driver_id === selectedDriver) ?? drivers[0];
  const nodeIds = new Set(driver?.node_ids ?? []);
  const edges = active.edges.filter(
    (edge) => nodeIds.has(edge.source) || nodeIds.has(edge.target),
  );
  const label = (id: string) =>
    active.nodes.find((node) => node.node_id === id)?.label ?? id;
  const mitigations = active.mitigations.filter(
    (item) => item.driver_id === driver?.driver_id,
  );
  const action = decisionAction(approvalStage);
  return (
    <section className="flex h-full min-h-[540px] flex-col overflow-y-auto rounded-lg border border-line bg-surface lg:min-h-0">
      <nav
        className="grid grid-cols-2 gap-1 border-b border-line p-2 sm:grid-cols-4"
        aria-label="Briefing steps"
      >
        {steps.map((name, index) => (
          <button
            key={name}
            type="button"
            aria-current={step === index ? 'step' : undefined}
            onClick={() => setStep(index)}
            className={`rounded-lg px-3 py-3 text-left text-sm ${step === index ? 'bg-brand-soft text-brand' : 'text-subtle hover:bg-workspace'}`}
          >
            <span className="mr-2 font-mono">0{index + 1}</span>
            {name}
          </button>
        ))}
      </nav>
      <div className="flex flex-1 flex-col p-5 sm:p-6">
        <header className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-2xl">{steps[step]}</h2>
          <span className="text-xs text-caution">
            {isOfficial
              ? 'Scope-matched calibration'
              : 'Assumption scenario · not a validated estimate'}
          </span>
        </header>
        {step === 0 ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className={`${card} sm:col-span-2`}>
              <p className="text-sm text-brand">
                {analysis.asset.label} · {METROS[analysis.metroId]}
              </p>
              <h3 className="mt-3 break-words text-3xl">
                {projectName || 'Untitled project'}
              </h3>
              <p className="mt-3 text-sm text-subtle">
                {approvalStage.replaceAll('_', ' ')} · provincial scenario
                rates, local evidence context
              </p>
            </div>
            <Metric
              label="Base budget · contingency excluded"
              value={money(inputs.budgetMillions)}
            />
            <Metric
              label="Full delivery window"
              value={`${inputs.projectStart}–${inputs.projectStart + inputs.durationYears - 1}`}
            />
            <Metric
              label="Duration · not just scenario overlap"
              value={`${inputs.durationYears} years`}
            />
            <Metric label="Price basis" value={inputs.priceBasis} />
            <p className="text-sm text-subtle sm:col-span-2">
              Spending: {SPENDING_PROFILES[inputs.spendingProfile]}.{' '}
              {analysis.scenarioWindowYears.length} delivery years overlap the
              scenario; outside-window exposure remains uncertain.
            </p>
          </div>
        ) : null}
        {step === 1 ? (
          <div>
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric
                label="Baseline escalation · full project"
                value={money(cashflow?.baselineEscalation)}
              />
              <Metric
                label="AI scenario increment · full project"
                value={money(cashflow?.aiIncrement)}
              />
              <Metric
                label="Total scenario spend"
                value={money(cashflow?.combinedSpend)}
              />
            </div>
            <div className="mt-4 h-[230px]">
              <ChartContainer
                config={config}
                className="h-full w-full aspect-auto"
              >
                <AreaChart
                  data={active.monthly_series}
                  margin={{ left: 0, right: 12, top: 10, bottom: 0 }}
                >
                  <CartesianGrid stroke="#dde4e9" vertical={false} />
                  <XAxis
                    dataKey="month"
                    interval="preserveStartEnd"
                    tick={{ fill: '#586b78', fontSize: 12 }}
                  />
                  <YAxis
                    width={65}
                    tick={{ fill: '#586b78', fontSize: 12 }}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Area
                    dataKey="baseline_mom_pct"
                    stroke="#446c99"
                    fill="#446c99"
                    fillOpacity={0.15}
                    isAnimationActive={false}
                  />
                  <Area
                    dataKey="ai_increment_mom_pct"
                    stroke="#8b5916"
                    fill="#8b5916"
                    fillOpacity={0.15}
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ChartContainer>
            </div>
            <div className="mt-3 flex flex-wrap gap-4 text-sm">
              <span className="text-[#446c99]">Baseline % MoM</span>
              <span className="text-caution">
                AI scenario increment · pp MoM
              </span>
            </div>
            <label className="mt-4 block text-sm">
              Inspect month · {month.month}
              <input
                className="scenario-range mt-2 w-full"
                aria-label="Briefing month"
                type="range"
                min={0}
                max={active.monthly_series.length - 1}
                value={monthIndex}
                onChange={(event) =>
                  setSelectedMonth(
                    active.monthly_series[Number(event.target.value)].month,
                  )
                }
              />
            </label>
            <p className="mt-3 text-sm">
              {month.month}: baseline escalation{' '}
              {money(spend?.baselineEscalation)} + AI scenario increment{' '}
              {money(spend?.aiIncrement)} on base spend{' '}
              {money(spend?.baseSpend)}.
            </p>
            <p className="mt-2 text-xs text-subtle">
              Rates describe monthly price movement; dollar amounts include
              cumulative escalation since {inputs.priceBasis}, weighted by that
              month’s spending.
            </p>
          </div>
        ) : null}
        {step === 2 ? (
          <div className="grid gap-4 xl:grid-cols-2">
            <div>
              <p className="mb-3 text-sm text-subtle">
                {month.month} · assumed allocation of the AI increment
              </p>
              {drivers.map((item) => (
                <button
                  key={item.driver_id}
                  type="button"
                  aria-pressed={driver?.driver_id === item.driver_id}
                  onClick={() => setSelectedDriver(item.driver_id)}
                  className={`mb-2 w-full rounded-lg border p-3 text-left ${driver?.driver_id === item.driver_id ? 'border-brand bg-brand-soft' : 'border-line bg-surface'}`}
                >
                  <span className="flex justify-between gap-3 text-sm">
                    <span>{item.label}</span>
                    <span>
                      {item.allocation === null
                        ? 'Withheld'
                        : `${scenarioRate(item.allocation)} pp`}
                    </span>
                  </span>
                  <span className="mt-1 block text-xs text-subtle">
                    {item.tier} · {item.confidence ?? 'unassessed'} confidence
                  </span>
                </button>
              ))}
            </div>
            <div className={card}>
              <h3 className="text-lg">
                {driver?.label ?? 'No driver available'}
              </h3>
              <p className="mt-2 text-xs text-subtle">
                Structural relationships—not additional cost to sum.
              </p>
              {edges.length ? (
                edges.map((edge) => (
                  <div
                    key={`${edge.source}-${edge.target}`}
                    className="mt-4 grid gap-2 rounded-lg border border-brand/25 p-3 text-center text-sm"
                  >
                    <span>{label(edge.source)}</span>
                    <span aria-hidden="true" className="text-xl text-brand">
                      ↓
                    </span>
                    <span>{label(edge.target)}</span>
                  </div>
                ))
              ) : (
                <p className="mt-4 text-sm">
                  No declared graph path for this driver. It is a scenario
                  allocation assumption.
                </p>
              )}
              <Button
                className="mt-4 border border-line bg-workspace text-ink"
                onClick={() => onExplore('cockpit')}
              >
                Inspect weights and sources
              </Button>
            </div>
          </div>
        ) : null}
        {step === 3 ? (
          <div className="space-y-4">
            <div className={card}>
              <p className="text-sm text-brand">{action.when}</p>
              <h3 className="mt-2 text-3xl">{action.title}</h3>
              <p className="mt-3 text-base text-subtle">{action.why}</p>
            </div>
            <h3 className="text-sm">
              Options for {driver?.label ?? 'the project'}
            </h3>
            <div className="grid gap-3 sm:grid-cols-2">
              {mitigations.length ? (
                mitigations.map((item, index) => (
                  <div key={`${item.driver_id}-${index}`} className={card}>
                    <p className="text-xs uppercase text-brand">
                      {item.timing}
                    </p>
                    <p className="mt-2 text-lg">{item.label}</p>
                    <p className="mt-2 text-xs text-subtle">
                      {item.evidence_status} · confirm feasibility and obtain
                      project-specific quotes before adoption.
                    </p>
                  </div>
                ))
              ) : (
                <div className={card}>
                  No driver-specific mitigation is recorded. Seek
                  project-specific market advice.
                </div>
              )}
            </div>
            <div className={card}>
              <p className="text-sm">
                <Link
                  href="/methods#planning-gates"
                  className="text-brand underline"
                >
                  Planning checks: {planningChecks} passed
                </Link>
                .
              </p>
              <p className="mt-2 text-sm text-subtle">
                Obtain an independent estimate and supplier capacity evidence
                before the next approval.
              </p>
              <Button
                className="mt-3 border border-line bg-workspace text-ink"
                onClick={() => onExplore('evidence')}
              >
                See evidence gaps
              </Button>
            </div>
          </div>
        ) : null}
        <footer className="mt-auto flex items-center justify-between gap-3 border-t border-line pt-4">
          <Button
            className="mt-4 border border-line bg-workspace text-ink"
            disabled={step === 0}
            onClick={() => setStep((current) => Math.max(0, current - 1))}
          >
            Back
          </Button>
          <p className="mt-4 text-xs text-subtle">
            {step + 1} / 4 · live project inputs
          </p>
          <Button
            className="mt-4 bg-brand-soft text-brand"
            onClick={() =>
              step === 3
                ? onExplore('cockpit')
                : setStep((current) => Math.min(3, current + 1))
            }
          >
            {step === 3 ? 'Open decision cockpit' : 'Next'}
          </Button>
        </footer>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className={card}>
      <p className="text-sm text-subtle">{label}</p>
      <p className="mt-3 text-2xl text-brand">{value}</p>
    </div>
  );
}
