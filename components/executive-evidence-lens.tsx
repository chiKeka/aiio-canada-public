'use client';

import { useState } from 'react';
import { Building2, Factory, Users, Zap } from 'lucide-react';
import Link from 'next/link';
import { buildExecutiveEvidence } from '@/lib/executive-evidence';
import { METROS, type buildDecisionAnalysis } from '@/lib/decision-analysis';
import {
  type buildDecisionOutlook,
  type DecisionInputs,
} from '@/lib/decision-outlook';
import { SPENDING_PROFILES } from '@/lib/project-cashflow';

type PlanningReadiness = {
  status: string;
  passed_check_count: number;
  check_count: number;
  checks: {
    id: string;
    status: string;
    finding: string;
    next_step: string | null;
  }[];
};
const icons = [Factory, Users, Zap, Building2];
const panel = 'rounded-lg border border-line bg-surface p-4';

export function ExecutiveEvidenceLens({
  analysis,
  assessment,
  inputs,
  planning,
  projectName,
}: {
  analysis: ReturnType<typeof buildDecisionAnalysis>;
  assessment: ReturnType<typeof buildDecisionOutlook>;
  inputs: DecisionInputs;
  planning: PlanningReadiness;
  projectName: string;
}) {
  const [selected, setSelected] = useState('materials');
  const signals = buildExecutiveEvidence(analysis);
  const signal = signals.find((item) => item.id === selected) ?? signals[0];
  return (
    <section className=" rounded-lg border border-line bg-surface p-5">
      <header>
        <p className="text-sm text-brand">
          {projectName || 'Your project'} · {METROS[analysis.metroId]}
        </p>
        <h2 className="mt-1 text-2xl">What supports this assessment?</h2>
      </header>
      <div
        className="my-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4"
        aria-label="Evidence signals"
      >
        {signals.map((item, index) => {
          const Icon = icons[index];
          return (
            <button
              type="button"
              key={item.id}
              aria-pressed={selected === item.id}
              aria-controls="selected-evidence"
              onClick={() => setSelected(item.id)}
              className={`rounded-lg border p-4 text-left ${selected === item.id ? 'border-brand bg-brand-soft' : 'border-line bg-surface hover:bg-workspace'}`}
            >
              <div className="flex items-center gap-2 text-sm">
                <Icon aria-hidden="true" className="size-4 text-brand" />
                {item.label}
              </div>
              <p className="mt-3 text-2xl text-ink">{item.value}</p>
              <p className="mt-1 text-xs text-subtle">{item.unit}</p>
              <p className="mt-3 text-xs text-caution">{item.role}</p>
            </button>
          );
        })}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <div className={panel} id="selected-evidence">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-lg">{signal.detail}</h3>
            <span className="text-xs text-brand">{signal.status}</span>
          </div>
          <dl className="mt-4 space-y-3 text-sm">
            <div>
              <dt className="text-subtle">Geographic fit</dt>
              <dd>{signal.scope}</dd>
            </div>
            <div>
              <dt className="text-subtle">Observation period</dt>
              <dd>{signal.period}</dd>
            </div>
            <div>
              <dt className="text-brand">Supports</dt>
              <dd>{signal.supports}</dd>
            </div>
            <div>
              <dt className="text-caution">Does not establish</dt>
              <dd>{signal.limitation}</dd>
            </div>
          </dl>
          <details className="mt-4 rounded-lg border border-line p-3">
            <summary className="cursor-pointer text-sm">
              Sources and record dates · {signal.sources.length}
            </summary>
            {signal.sources.length ? (
              signal.sources.map(({ id, record }) => (
                <div key={id} className="mt-3 border-t border-line pt-3">
                  <p className="text-xs text-subtle">
                    {record?.publisher ?? 'Unresolved source'} · registry as of{' '}
                    {record?.as_of_date ?? 'unavailable'}
                  </p>
                  {record ? (
                    <a
                      className="mt-1 block text-sm text-brand underline"
                      href={record.canonical_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {record.title} ↗
                    </a>
                  ) : (
                    <p className="break-all text-sm">{id}</p>
                  )}
                </div>
              ))
            ) : (
              <p className="mt-3 text-sm">
                No matching observation source. Missing is not zero.
              </p>
            )}
            <p className="mt-3 text-xs text-subtle">
              Registry dates are not observation periods or a live freshness
              guarantee.
            </p>
          </details>
        </div>
        <div className="space-y-3">
          <div className={panel}>
            <h3 className="text-lg">How the number reaches your result</h3>
            <div className="mt-4 grid gap-2 text-sm">
              <div className="rounded-lg border border-[#446c99]/40 p-3">
                Observed signals → market context
              </div>
              <div className="rounded-lg border border-caution/30 p-3">
                {assessment?.isOfficial
                  ? 'Scope-matched monthly calibration'
                  : 'Scenario assumptions'}{' '}
                → monthly price path
              </div>
              <div className="rounded-lg border border-brand/40 p-3">
                Project budget + spending profile → dollar exposure
              </div>
            </div>
            <p className="mt-3 text-sm text-subtle">
              These four signal cards do not directly set the monthly escalation
              rates. They are not measured causes of the scenario dollars.
            </p>
            {!assessment ? (
              <p className="mt-3 text-sm text-caution" role="alert">
                Invalid project inputs: scenario results withheld; observed
                context remains available.
              </p>
            ) : null}
            <details className="mt-3">
              <summary className="cursor-pointer text-sm">
                Actual calculation inputs
              </summary>
              {assessment?.isOfficial ? (
                <p className="mt-3 text-sm">
                  Calibration {assessment.active.calibration_id} · as of{' '}
                  {assessment.active.as_of_date ?? 'unavailable'} ·{' '}
                  {assessment.active.geography_id}. User rate assumptions are
                  not applied.
                </p>
              ) : (
                <p className="mt-3 text-sm">
                  Assumed baseline {inputs.assumptions.annualBaselinePct}%
                  annually · peak AI increment{' '}
                  {inputs.assumptions.peakAiAnnualPctPoints} pp annually · local
                  capture {inputs.assumptions.localCapturePct}% · lag{' '}
                  {inputs.assumptions.lagMonths} months · uncertainty ±
                  {inputs.assumptions.uncertaintyPct}%. The stored
                  counterfactual annual flow shapes the monthly scenario; graph
                  weights allocate drivers, not observed causal effects.
                </p>
              )}
              <p className="mt-2 text-sm">
                ${inputs.budgetMillions.toLocaleString()}M base budget ·{' '}
                {inputs.priceBasis} prices ·{' '}
                {SPENDING_PROFILES[inputs.spendingProfile]} spending ·{' '}
                {inputs.durationYears} years. Contingency is separate.
              </p>
            </details>
          </div>
          <div className={panel}>
            <h3 className="text-lg">Next practical check</h3>
            <p className="mt-2 text-base">{signal.next}</p>
            <p className="mt-3 text-sm text-caution">
              Use for market screening and scenario sensitivity—not an approved
              AI premium, causal effect, or quantified mitigation saving.
            </p>
          </div>
        </div>
      </div>
      <details className="mt-4 rounded-lg border border-line p-4">
        <summary className="cursor-pointer text-sm">
          Research validation · {planning.passed_check_count}/
          {planning.check_count} checks passed ·{' '}
          {planning.status.replaceAll('_', ' ')}
        </summary>
        <p className="mt-3 text-sm text-subtle">
          Public-data proxy planning and causal attribution have separate gates.
          A check count is not confidence in your estimate.
        </p>
        <ul className="mt-4 grid gap-3 sm:grid-cols-2">
          {planning.checks.map((check) => (
            <li className={panel} key={check.id}>
              <h4 className="text-sm">
                {check.id.replaceAll('_', ' ')} ·{' '}
                {check.status.replaceAll('_', ' ')}
              </h4>
              <p className="mt-2 text-sm text-subtle">{check.finding}</p>
              {check.next_step ? (
                <p className="mt-2 text-sm">Next: {check.next_step}</p>
              ) : null}
            </li>
          ))}
        </ul>
        <Link
          href="/research"
          className="mt-4 inline-block text-sm text-brand underline"
        >
          Full research method and causal-identification status →
        </Link>
      </details>
    </section>
  );
}
