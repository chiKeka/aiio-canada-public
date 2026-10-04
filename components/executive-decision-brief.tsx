'use client';
import Link from 'next/link';

import {
  scenarioMoney as money,
  scenarioRate,
} from '@/lib/public-presentation.mjs';

import { type AssessmentRecord } from '@/lib/assessment-record';
import { SPENDING_PROFILES } from '@/lib/project-cashflow';

export function ExecutiveDecisionBrief({
  record,
  visible,
}: {
  record: AssessmentRecord | null;
  visible: boolean;
}) {
  if (!record)
    return (
      <article
        id="executive-decision-brief"
        className={
          visible
            ? 'rounded-xl bg-white p-6 text-ink'
            : 'executive-print-record'
        }
      >
        <h1>Decision brief withheld</h1>
        <p>
          Correct the project inputs and resolve missing monthly prices before
          printing or exporting a result.
        </p>
      </article>
    );
  const { project, result, focus } = record;
  const selected = result.monthly.find((row) => row.month === focus.month);
  const ranked = [...record.drivers].sort(
    (a, b) =>
      (b.selected_month_allocation_pp ?? -1) -
      (a.selected_month_allocation_pp ?? -1),
  );
  const mitigation = record.mitigations.filter(
    (item) => item.driver_id === focus.driverId,
  );
  return (
    <article
      id="executive-decision-brief"
      className={`decision-brief ${visible ? 'rounded-lg border border-line bg-white p-6 text-ink' : 'executive-print-record'}`}
    >
      <header>
        <p className="text-sm">
          AI Infrastructure Impact Observatory · Executive decision brief
        </p>
        <h1 className="mt-2 text-3xl">{project.name || 'Untitled project'}</h1>
        <p className="mt-2 text-sm">
          {project.asset} · {project.market} · Jan {project.inputs.projectStart}
          –Dec {project.inputs.projectStart + project.inputs.durationYears - 1}
        </p>
        <p className="mt-2 text-sm">
          {record.model.is_scope_matched_calibration
            ? 'Scope-matched calibration'
            : 'Assumption scenario · not a validated estimate'}{' '}
          · {project.approval_stage.replaceAll('_', ' ')}
        </p>
      </header>
      <section className="mt-5">
        <h2 className="text-lg">
          Cost exposure · {project.inputs.priceBasis} price basis
        </h2>
        <dl className="mt-3 grid grid-cols-2 gap-3">
          {[
            ['Base budget', money(project.inputs.budgetMillions)],
            ['Baseline escalation', money(result.baselineEscalation)],
            ['AI scenario increment', money(result.aiIncrement)],
            ['Total scenario spend', money(result.combinedSpend)],
            [
              'Low–high scenario spend',
              `${money(result.lowSpend)}–${money(result.highSpend)}`,
            ],
            ['Contingency · separate', money(project.contingency_millions)],
          ].map(([label, value]) => (
            <div className="rounded-lg border border-line p-3" key={label}>
              <dt className="text-sm">{label}</dt>
              <dd className="mt-1 text-xl">{value}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-2 text-sm">
          {SPENDING_PROFILES[project.inputs.spendingProfile]} spending. Range is
          scenario sensitivity, not a statistical confidence interval.
        </p>
      </section>
      <section className="mt-5">
        <h2 className="text-lg">Selected month · {focus.month}</h2>
        <p className="mt-2 text-sm">
          Base spend {money(selected?.baseSpend)} · baseline escalation{' '}
          {money(selected?.baselineEscalation)} · AI increment{' '}
          {money(selected?.aiIncrement)}. Dollar exposure compounds from the
          price basis.
        </p>
        <ul className="mt-3 space-y-1 text-sm">
          {ranked.slice(0, 3).map((driver) => (
            <li key={driver.driver_id}>
              {driver.label} · {driver.tier} ·{' '}
              {driver.selected_month_allocation_pp === null
                ? 'allocation withheld'
                : `${scenarioRate(driver.selected_month_allocation_pp)} pp assumed monthly allocation`}
            </li>
          ))}
        </ul>
      </section>
      <section className="mt-5">
        <h2 className="text-lg">Decision and next actions</h2>
        <p className="print-decision mt-2 text-xl">{record.decision.title}</p>
        <p className="mt-2 text-sm">
          {record.decision.when}. {record.decision.why}
        </p>
        <ul className="mt-2 text-sm">
          {mitigation.slice(0, 2).map((item, index) => (
            <li key={index}>
              {item.label} · {item.timing} · {item.evidence_status}; feasibility
              to be confirmed.
            </li>
          ))}
        </ul>
      </section>
      {record.comparison ? (
        <section className="mt-5">
          <h2 className="text-lg">Pinned alternative</h2>
          <p className="mt-2 text-sm">
            {record.comparison.market} · {record.comparison.inputs.projectStart}{' '}
            start · {record.comparison.inputs.durationYears} years ·{' '}
            {money(record.comparison.inputs.budgetMillions)} base ·{' '}
            {record.comparison.inputs.priceBasis} prices.
          </p>
          <p className="mt-2 text-sm">
            Current minus pinned scenario spend:{' '}
            {money(record.comparison.scenario_spend_delta_millions)}.{' '}
            {record.comparison.delta_status.replaceAll('_', ' ')}; not an
            isolated causal effect.
          </p>
        </section>
      ) : null}
      <section className="mt-5">
        <h2 className="text-lg">Evidence and limitations</h2>
        <p className="mt-2 text-sm">
          <Link href="/methods#planning-gates" className="underline">
            Planning checks: {record.planning_validation.passed_check_count}/
            {record.planning_validation.check_count}
          </Link>
          . {record.boundary.note}
        </p>
        <ul className="mt-2 space-y-2 text-sm">
          {record.evidence.map((signal) => (
            <li key={signal.id}>
              <strong>{signal.label}: </strong>
              {signal.value} · {signal.period} · {signal.scope} · context only.{' '}
              {signal.limitation}
              {signal.sources.map(({ id, record: source }) =>
                source ? (
                  <a
                    key={id}
                    className="ml-2 underline"
                    href={source.canonical_url}
                  >
                    {source.publisher} [{id}; registry {source.as_of_date}]
                  </a>
                ) : (
                  <span key={id}> Source unresolved: {id}</span>
                ),
              )}
            </li>
          ))}
        </ul>
      </section>
      <section className="mt-5 brief-assumptions">
        <h2 className="text-lg">Calculation record</h2>
        <p className="mt-2 text-sm">
          Baseline {project.inputs.assumptions.annualBaselinePct}% annually ·
          peak AI {project.inputs.assumptions.peakAiAnnualPctPoints} pp annually
          · capture {project.inputs.assumptions.localCapturePct}% · lag{' '}
          {project.inputs.assumptions.lagMonths} months · uncertainty ±
          {project.inputs.assumptions.uncertaintyPct}%.{' '}
          {record.model.is_scope_matched_calibration
            ? 'These user rate assumptions are inactive; scope-matched calibration supplies monthly prices.'
            : 'These are user assumptions, not estimated causal effects.'}
        </p>
        <p className="mt-2 break-all text-xs">
          {record.schema_version} · {record.model.calibration_id} ·{' '}
          {record.model.calculation_contract} · research release{' '}
          {record.model.release_manifest.version}
        </p>
        <p className="mt-2 text-xs">{record.boundary.reproduction}</p>
      </section>
    </article>
  );
}
