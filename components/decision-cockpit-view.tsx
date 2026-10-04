'use client';

import { scenarioMoney as money } from '@/lib/public-presentation.mjs';

import { useState } from 'react';
import { WorkspaceMetric } from '@/components/workspace-metric';
import Link from 'next/link';
import graph from '@/data/model/alberta_graph_v0.2.json';
import { type buildDecisionAnalysis, METROS } from '@/lib/decision-analysis';
import {
  buildDecisionOutlook,
  decisionAction,
  deliveryYears,
  type DecisionInputs,
} from '@/lib/decision-outlook';

type Assessment = ReturnType<typeof buildDecisionOutlook>;
export type PinnedDecision = {
  inputs: DecisionInputs;
  assessment: Assessment;
  market: string;
};
const panel = 'rounded-lg border border-line bg-surface p-4';

export function DecisionCockpitView({
  analysis,
  assessment,
  inputs,
  approvalStage,
  projectName,
  comparison,
  planningChecks,
}: {
  analysis: ReturnType<typeof buildDecisionAnalysis>;
  assessment: Assessment;
  inputs: DecisionInputs;
  approvalStage: string;
  projectName: string;
  comparison: PinnedDecision | null;
  planningChecks: string;
}) {
  const [tab, setTab] = useState('decision');
  const action = decisionAction(approvalStage);
  if (!assessment)
    return (
      <section className={panel} role="alert">
        Results withheld. Correct the project dates, price basis or budget in
        the project controls.
      </section>
    );
  const { active, cashflow, isOfficial } = assessment;
  const drivers = [...active.drivers].sort(
    (a, b) =>
      (b.contribution_pct_points ?? -1) - (a.contribution_pct_points ?? -1),
  );
  const peak = cashflow?.monthly.reduce((best, row) =>
    row.aiIncrement > best.aiIncrement ? row : best,
  );
  const years = deliveryYears(
    analysis.startYear,
    analysis.endYear,
    analysis.scenarioWindowStart,
    analysis.scenarioWindowEnd,
  );
  const label = (id: string) =>
    graph.nodes.find((node) => node.node_id === id)?.label ?? id;
  const max = Math.max(
    ...drivers.map((driver) => driver.contribution_pct_points ?? 0),
    0.001,
  );
  return (
    <section className=" rounded-lg border border-line bg-surface p-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs text-subtle">
            {projectName} · {approvalStage.replaceAll('_', ' ')}
          </p>
          <h2 className="mt-1 text-2xl">Scenario comparison</h2>
        </div>
        <span className="rounded-full border border-caution/30 px-3 py-1 text-xs text-caution">
          {isOfficial
            ? 'Scope-matched calibration'
            : 'Assumption scenario · not validated'}
        </span>
      </header>
      <nav className="my-4 flex gap-2" aria-label="Decision details">
        {['decision', 'pathways', 'evidence'].map((id) => (
          <button
            key={id}
            type="button"
            aria-pressed={tab === id}
            onClick={() => setTab(id)}
            className={`rounded-lg px-4 py-2 text-sm capitalize ${tab === id ? 'bg-brand-soft text-brand' : 'border border-line'}`}
          >
            {id}
          </button>
        ))}
      </nav>
      {tab === 'decision' ? (
        <div className="grid gap-4 xl:grid-cols-2">
          <div className="space-y-4">
            <div className={panel}>
              <p className="text-xs text-brand">
                Next decision · {action.when}
              </p>
              <h3 className="mt-2 text-2xl">{action.title}</h3>
              <p className="mt-2 text-sm text-subtle">{action.why}</p>
              <p className="mt-2 text-xs text-caution">
                <Link href="/methods#planning-gates" className="underline">
                  Planning checks: {planningChecks}
                </Link>
                . No causal attribution or quantified mitigation savings.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                ['Baseline escalation', money(cashflow?.baselineEscalation)],
                ['AI scenario increment', money(cashflow?.aiIncrement)],
                ['Total scenario spend', money(cashflow?.combinedSpend)],
                [
                  'Peak AI dollar exposure',
                  peak && peak.aiIncrement > 0
                    ? peak.month
                    : 'No positive increment',
                ],
              ].map(([title, value]) => (
                <WorkspaceMetric
                  key={title}
                  label={title}
                  value={value}
                  emphasized={title === 'Total scenario spend'}
                />
              ))}
            </div>
            <p className="text-xs text-subtle">
              {inputs.priceBasis} prices ·{' '}
              {inputs.spendingProfile.replaceAll('_', ' ')} spending ·
              contingency excluded. Range: {money(cashflow?.lowSpend)}–
              {money(cashflow?.highSpend)}.
            </p>
            {comparison ? (
              <div className={panel}>
                <h3 className="text-sm">Against pinned configuration</h3>
                <p className="mt-2 text-xs">
                  {comparison.market} → {METROS[analysis.metroId]} · start{' '}
                  {comparison.inputs.projectStart} → {inputs.projectStart} ·
                  duration {comparison.inputs.durationYears} →{' '}
                  {inputs.durationYears} years
                </p>
                <p className="mt-2 text-sm">
                  {comparison.inputs.priceBasis !== inputs.priceBasis
                    ? 'Dollar delta withheld: different price bases.'
                    : cashflow && comparison.assessment?.cashflow
                      ? `Scenario spend change: ${money(cashflow.combinedSpend - comparison.assessment.cashflow.combinedSpend)}`
                      : 'Dollar comparison unavailable.'}
                </p>
                <p className="mt-2 text-xs">
                  Leading driver:{' '}
                  {comparison.assessment?.active.drivers
                    .slice()
                    .sort(
                      (a, b) =>
                        (b.contribution_pct_points ?? 0) -
                        (a.contribution_pct_points ?? 0),
                    )[0]?.label ?? 'Unavailable'}{' '}
                  → {drivers[0]?.label ?? 'Unavailable'}
                </p>
                <p className="mt-2 text-xs text-subtle">
                  Configuration comparison, not isolated causal effect. Market
                  selection changes evidence, not provincial scenario rates.
                </p>
              </div>
            ) : null}
          </div>
          <div className="space-y-4">
            <div className={panel}>
              <h3 className="text-sm">Driver ranking · assumed peak weights</h3>
              <p className="mt-1 text-xs text-subtle">
                Relative allocation, not measured cost contribution.
              </p>
              {drivers.slice(0, 6).map((driver) => (
                <div className="mt-3" key={driver.driver_id}>
                  <div className="mb-1 flex justify-between gap-3 text-sm">
                    <span>{driver.label}</span>
                    <span className="text-xs text-subtle">{driver.tier}</span>
                  </div>
                  <div className="h-2 rounded bg-workspace">
                    <div
                      className="h-2 rounded bg-brand"
                      style={{
                        width: `${Math.max(0, ((driver.contribution_pct_points ?? 0) / max) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className={panel}>
              <h3 className="text-sm">
                Delivery: Jan {analysis.startYear} – Dec {analysis.endYear}
              </h3>
              <div className="mt-3 flex gap-1">
                {years.map(({ year, overlap }) => (
                  <div key={year} className="flex-1 text-center">
                    <div
                      className={`h-8 rounded ${overlap ? 'bg-brand' : 'bg-caution'}`}
                    />
                    <span className="text-xs">{year}</span>
                  </div>
                ))}
              </div>
              <p className="mt-2 text-xs text-subtle">
                Teal: scenario overlap · Orange: outside scenario window (
                {analysis.scenarioWindowStart}–{analysis.scenarioWindowEnd}).
                Outside-window rates are not evidence of no risk; prior price
                effects can persist.
              </p>
            </div>
            <details className={panel}>
              <summary className="cursor-pointer text-sm">
                Mitigation options · test before adopting
              </summary>
              {active.mitigations.slice(0, 4).map((item, i) => (
                <p className="mt-3 text-sm" key={`${item.driver_id}-${i}`}>
                  {item.label}
                  <span className="block text-xs text-subtle">
                    {item.timing} · {item.evidence_status} · confirm feasibility
                    with the project team.
                  </span>
                </p>
              ))}
            </details>
          </div>
        </div>
      ) : tab === 'pathways' ? (
        <div className="space-y-3">
          <p className="text-sm text-subtle">
            Declared graph mechanisms → constraints → {analysis.asset.label}.
            Weights and lags are assumptions, not calibrated cost or delay
            estimates.
          </p>
          {analysis.directEdges.map((edge) => (
            <details className={panel} key={edge.edge_id}>
              <summary className="cursor-pointer text-sm">
                {label(edge.source)} → {label(edge.target)}
              </summary>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                {[
                  `Weight ${edge.weight_low}–${edge.weight_central}–${edge.weight_high}`,
                  `Lag ${edge.lag_periods} years (graph)`,
                  edge.evidence_status,
                  edge.assumption_id,
                ].map((value) => (
                  <span key={value} className="rounded border border-line p-2">
                    {value}
                  </span>
                ))}
              </div>
              <p className="mt-2 text-sm">
                {edge.mechanism.replaceAll('_', ' ')}
              </p>
              <p className="mt-2 text-xs">
                Source:{' '}
                {edge.source_id ??
                  'No empirical source attached; assumption only'}
                . Annual graph lags are distinct from the monthly scenario lag.
              </p>
              {graph.edges
                .filter((upstream) => upstream.target === edge.source)
                .map((upstream) => (
                  <p
                    key={upstream.edge_id}
                    className="mt-3 border-l-2 border-brand pl-3 text-sm"
                  >
                    {label(upstream.source)} → {label(upstream.target)}
                    <span className="block text-xs text-subtle">
                      {upstream.evidence_status} · weight{' '}
                      {upstream.weight_central} · lag {upstream.lag_periods}{' '}
                      years · {upstream.assumption_id}
                    </span>
                  </p>
                ))}
            </details>
          ))}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          <div className={panel}>
            <h3>Materials · {METROS[analysis.metroId]}</h3>
            <p className="my-3 text-3xl text-brand">
              {analysis.materials[0]?.year_over_year_percent_change ??
                'Unavailable'}
              % YoY
            </p>
            <p className="text-sm">
              {analysis.materials[0]?.component ?? 'No component'} ·{' '}
              {analysis.materials[0]?.period_end ?? 'Date unavailable'}
            </p>
            <p className="mt-2 text-xs text-subtle">
              {analysis.asset.profileNote} Highest absolute YoY component
              change; not an AI effect.
            </p>
            <p className="mt-2 break-all text-xs">
              {analysis.materials[0]?.source_id}
            </p>
          </div>
          <div className={panel}>
            <h3>Labour · Alberta</h3>
            <p className="my-3 text-3xl text-brand">
              {
                analysis.labourRows.filter(
                  (row) => row.vacancies_per_1_000_2021_employed !== null,
                ).length
              }{' '}
              usable trades
            </p>
            <p className="text-sm">
              Vacancies relative to 2021 workforce stock; not available workers.
            </p>
            <p className="mt-2 text-xs text-subtle">
              Vacancies: {analysis.labourDates.vacancy} · workforce:{' '}
              {analysis.labourDates.workforce}. Provincial scope, not local
              contractor capacity.
            </p>
          </div>
          <div className={panel}>
            <h3>Power requests · Alberta</h3>
            <p className="my-3 text-3xl text-brand">
              {analysis.powerEvidence.requested_load.latest_requested_load_mw /
                1000}{' '}
              GW
            </p>
            <p className="text-sm">
              {analysis.powerEvidence.requested_load.latest_application_period}{' '}
              · AESO
            </p>
            <p className="mt-2 text-xs text-subtle">
              Requested, not connected load. Cannot determine transmission
              additions for this project.
            </p>
          </div>
          <div className={panel}>
            <h3>Concurrent public projects · Alberta</h3>
            <p className="my-3 text-3xl text-brand">
              {analysis.concurrentProjectCount}
            </p>
            <p className="text-sm">
              Same-class records with overlapping dates.
            </p>
            <p className="mt-2 text-xs text-subtle">
              Release baseline as of {analysis.analysisDate}; not a local
              bid-demand or realized expenditure estimate.
            </p>
          </div>
          <Link href="/evidence" className="text-sm text-brand underline">
            Open source registry and evidence dates →
          </Link>
        </div>
      )}
    </section>
  );
}
