'use client';

import { useMemo, useState, type ReactNode } from 'react';
import { BriefingDownload } from '@/components/briefing-download';
import {
  calculate,
  defaults,
  escalation,
  formulas,
  trades,
  type Options,
  type Selection,
} from '@/lib/construction-model';
import projects from '@/public/data/construction/projects.json';
import benchmarks from '@/public/data/construction/benchmarks.json';
import manifest from '@/public/data/construction/manifest.json';
import enablingLedgerData from '@/data/scenarios/alberta_enabling_infrastructure_v0.1.json';
import { summarizeEnablingLedger, type EnablingLedger } from '@/lib/enabling-infrastructure';
const enablingLedger = enablingLedgerData as EnablingLedger;
const enablingSummary = summarizeEnablingLedger(enablingLedger);

const number = (x: number) => Math.round(x).toLocaleString('en-CA');
const panel = 'rounded-lg border border-line bg-surface p-5';
const input =
  'mt-1 w-full rounded-md border border-line bg-workspace px-3 py-2 text-sm text-ink';
function Field({
  label,
  value,
  onChange,
  min = 0,
  max,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (n: number) => void;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <label className="block text-xs text-subtle">
      {label}
      <input
        className={input}
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}
function download(name: string, value: unknown) {
  const blob = new Blob(
    [typeof value === 'string' ? value : JSON.stringify(value, null, 2)],
    {
      type:
        typeof value === 'string'
          ? 'text/csv;charset=utf-8'
          : 'application/json',
    },
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function ConstructionWorkspace({
  overview,
  evidenceAsOf,
}: {
  overview: ReactNode;
  evidenceAsOf: string;
}) {
  const [tab, setTab] = useState('Alberta overview');
  const [options, setOptions] = useState<Options>(defaults);
  const [selected, setSelected] = useState<Record<string, Selection>>(() =>
    Object.fromEntries(
      projects.map((p) => [
        p.id,
        { included: false, cost: p.cost ?? 0, online: p.end ?? 2030 },
      ]),
    ),
  );
  const [query, setQuery] = useState('');
  const [delay, setDelay] = useState(6);
  const [exposure, setExposure] = useState(60);
  const [rate, setRate] = useState(3.5);
  const [need, setNeed] = useState(40);
  const result = useMemo(() => {
    try {
      return { run: calculate(projects, selected, options), error: null };
    } catch (e) {
      return {
        run: null,
        error: e instanceof Error ? e.message : 'Invalid inputs',
      };
    }
  }, [selected, options]);
  const update = (key: keyof Options, value: number) =>
    setOptions((o) => ({ ...o, [key]: value }));
  const listUpdate = (
    key: 'shares' | 'labour' | 'wages' | 'capacity',
    i: number,
    value: number | null,
  ) =>
    setOptions((o) => ({
      ...o,
      [key]: o[key].map((v, j) => (j === i ? value : v)),
    }));
  const run = result.run;
  const exportRun = () => {
    if (run)
      download('construction-presentation-inputs.json', {
        createdAt: new Date().toISOString(),
        ...run,
        selected,
        benchmarks,
        manifest,
        formulas,
        enablingInfrastructure: { ledger: enablingLedger, summary: enablingSummary, relationshipToSelection: 'Separate fixed $50B counterfactual diligence ledger; not scaled by selected project phases or added to their demand.' },
        procurementWeeksUntilRequired: need,
        illustrativeEscalation: {
          uncommittedCAD: exposure * 1e6,
          delayMonths: delay,
          annualRate: rate / 100,
          additionalCAD: escalation(exposure * 1e6, rate / 100, delay),
        },
      });
  };
  const annual = run
    ? Array.from({ length: options.years }, (_, i) => {
        const year = 2027 + i;
        return {
          year,
          hours: run.rows
            .filter((r) => r.quarter.startsWith(String(year)))
            .reduce((s, r) => s + r.dcHours, 0),
        };
      })
    : [];
  const largest = Math.max(1, ...annual.map((x) => x.hours));
  return (
    <div className="mx-auto max-w-[1440px] space-y-5 px-4 py-6 sm:px-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-subtle">
          Evidence snapshot ·{' '}
          {tab === 'Alberta overview' ? evidenceAsOf : manifest.asOf} ·{' '}
          {tab === 'Alberta overview'
            ? 'Published evidence & analysis'
            : 'Conditional estimates & reference inputs'}
        </p>
        <div className="flex flex-wrap gap-3">
          <a
            className="text-sm text-brand underline"
            href="/data/construction/requirements.md"
            download
          >
            Requirements
          </a>
          {tab !== 'Alberta overview' && (
            <button
              className="rounded-md bg-brand px-4 py-2 text-sm text-white disabled:opacity-40"
              disabled={!run}
              onClick={exportRun}
            >
              Download scenario inputs (.json)
            </button>
          )}
        </div>
      </div>
      <nav aria-label="Construction sections" className="flex flex-wrap gap-2">
        {[
          'Alberta overview',
          'Demand model',
          'Benchmarks & sources',
          'Formulas',
          'Procurement & cost',
        ].map((t) => (
          <button
            key={t}
            aria-pressed={tab === t}
            onClick={() => setTab(t)}
            className={`rounded-md px-4 py-2 text-sm ${tab === t ? 'bg-brand text-white' : 'border border-line bg-surface text-subtle'}`}
          >
            {t}
          </button>
        ))}
      </nav>
      {tab === 'Alberta overview' && overview}
      {tab === 'Demand model' && (
        <>
          <div className="rounded-md border border-caution/30 bg-workspace p-4 text-sm leading-6">
            Select phases to calculate demand. Cost scope, package shares and
            labour rates below are analyst assumptions, not licensed estimating
            rates. The background is Alberta’s public capital envelope only;
            other private construction is omitted. No project delay or causal
            price premium is inferred.
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              ['Selected phases', String(run?.phases.length ?? 0)],
              ['DC job-years in window', number(run?.jobYears ?? 0)],
              [
                'Capacity evidence',
                options.capacity.every((x) => x === null)
                  ? 'Not entered'
                  : 'Assumed capacity',
              ],
            ].map(([label, value]) => (
              <article className={panel} key={label}>
                <p className="text-xs text-subtle">{label}</p>
                <p className="mt-3 text-2xl font-semibold text-brand">
                  {value}
                </p>
              </article>
            ))}
          </div>
          <section className={panel}>
            <h2 className="text-lg font-semibold">Scenario assumptions</h2>
            <p className="my-2 text-xs text-subtle">
              All controls in this section are scenario choices. Values are
              stored in the downloaded run; editing does not change the evidence
              snapshot.
            </p>
            <div className="mt-4 grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
              <label className="text-xs text-subtle">
                Reporting horizon
                <select
                  className={input}
                  value={options.years}
                  onChange={(e) => update('years', Number(e.target.value))}
                >
                  {[3, 5, 10].map((y) => (
                    <option key={y} value={y}>
                      {y} years · 2027–{2026 + y}
                    </option>
                  ))}
                </select>
              </label>
              <Field
                label="Fallback duration (months)"
                value={options.duration}
                onChange={(n) => update('duration', n)}
                min={1}
              />
              <label className="text-xs text-subtle">
                Capital cohort duration
                <select
                  className={input}
                  value={options.cohortYears}
                  onChange={(e) =>
                    update('cohortYears', Number(e.target.value))
                  }
                >
                  <option value={4}>4 years</option>
                  <option value={5}>5 years</option>
                </select>
              </label>
              <Field
                label="Tail real growth (% / year)"
                value={options.growth * 100}
                min={-10}
                step={0.5}
                onChange={(n) => update('growth', n / 100)}
              />
              <Field
                label="Tail price inflation (% / year)"
                value={options.inflation * 100}
                min={-5}
                step={0.5}
                onChange={(n) => update('inflation', n / 100)}
              />
              <Field
                label="DC construction scope (% of input cost)"
                value={options.constructionShare * 100}
                max={100}
                onChange={(n) => update('constructionShare', n / 100)}
              />
              <Field
                label="Public construction scope (% of envelope)"
                value={options.publicShare * 100}
                max={100}
                onChange={(n) => update('publicShare', n / 100)}
              />
              <Field
                label="Annual paid hours / FTE"
                value={options.annualHours}
                min={1}
                onChange={(n) => update('annualHours', n)}
              />
              <Field
                label="Incremental hours multiplier"
                value={options.hoursFactor}
                min={0.1}
                step={0.05}
                onChange={(n) => update('hoursFactor', n)}
              />
            </div>
            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              {trades.map((t, i) => (
                <fieldset className="rounded-md border border-line p-4" key={t}>
                  <legend className="px-1 text-sm font-medium">{t}</legend>
                  <div className="grid grid-cols-2 gap-3">
                    <Field
                      label="Package share (%)"
                      value={options.shares[i] * 100}
                      max={100}
                      onChange={(n) => listUpdate('shares', i, n / 100)}
                    />
                    <Field
                      label="Labour cost fraction (%)"
                      value={options.labour[i] * 100}
                      max={100}
                      onChange={(n) => listUpdate('labour', i, n / 100)}
                    />
                    <Field
                      label="Loaded CAD / paid hour"
                      value={options.wages[i]}
                      min={1}
                      onChange={(n) => listUpdate('wages', i, n)}
                    />
                    <Field
                      label="Other private annual paid hours (assumption)"
                      value={options.privateHours?.[i] ?? 0}
                      min={0}
                      onChange={(n) => setOptions((o) => ({ ...o, privateHours: trades.map((_, j) => j === i ? n : (o.privateHours?.[j] ?? 0)) }))}
                    />
                    <label className="text-xs text-subtle">
                      Total available FTE (blank = unknown)
                      <input
                        className={input}
                        type="number"
                        min={0}
                        value={options.capacity[i] ?? ''}
                        onChange={(e) =>
                          listUpdate(
                            'capacity',
                            i,
                            e.target.value === ''
                              ? null
                              : Number(e.target.value),
                          )
                        }
                      />
                    </label>
                  </div>
                </fieldset>
              ))}
            </div>
            <p className="mt-3 text-xs text-subtle">
              Package shares must sum to 100%. Public and DC work use the same
              provisional package mix here; this simplification is exported.
              Capacity is constant across the reporting window and covers broad
              trade groups, not certified individual occupations.
            </p>
          </section>
          <section className={panel}>
            <h2 className="text-lg font-semibold">Alberta phase register</h2>
            <p className="mt-2 text-sm text-subtle">
              {projects.length} core records · 31 August 2026 snapshot. Unknown
              online years default to 2030 as an editable scenario. Unknown
              costs remain zero and must be supplied before inclusion. This is
              not a complete Canada inventory.
            </p>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-xs">
                <thead>
                  <tr className="border-b border-line">
                    {[
                      'Include',
                      'Phase / location',
                      'Reported stage / years',
                      'Input investment (CAD M)',
                      'Scenario online year',
                    ].map((x) => (
                      <th className="p-2" key={x}>
                        {x}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr key={p.id} className="border-b border-line">
                      <td className="p-2">
                        <input
                          aria-label={`Include ${p.name}`}
                          type="checkbox"
                          checked={selected[p.id].included}
                          onChange={(e) =>
                            setSelected((s) => ({
                              ...s,
                              [p.id]: {
                                ...s[p.id],
                                included: e.target.checked,
                              },
                            }))
                          }
                        />
                      </td>
                      <td className="p-2">
                        <p className="font-medium">{p.name}</p>
                        <p className="mt-1 text-subtle">{p.region}</p>
                        {p.source && (
                          <a
                            className="text-brand underline"
                            href={p.source}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Project source
                          </a>
                        )}
                      </td>
                      <td className="p-2">
                        {p.stage}
                        <br />
                        {p.start ?? '?'}–{p.end ?? '?'}
                      </td>
                      <td className="p-2">
                        <input
                          aria-label={`${p.name} cost CAD million`}
                          className={input}
                          type="number"
                          min={0}
                          value={selected[p.id].cost / 1e6}
                          onChange={(e) =>
                            setSelected((s) => ({
                              ...s,
                              [p.id]: {
                                ...s[p.id],
                                cost: Number(e.target.value) * 1e6,
                              },
                            }))
                          }
                        />
                      </td>
                      <td className="p-2">
                        <input
                          aria-label={`${p.name} online year`}
                          className={input}
                          type="number"
                          min={2020}
                          max={2050}
                          value={selected[p.id].online}
                          onChange={(e) =>
                            setSelected((s) => ({
                              ...s,
                              [p.id]: {
                                ...s[p.id],
                                online: Number(e.target.value),
                              },
                            }))
                          }
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          {result.error && (
            <p
              role="alert"
              className="rounded-md border border-caution p-4 text-caution"
            >
              {result.error}
            </p>
          )}
          {run && (
            <>
              <section className={panel}>
                <h2 className="text-lg font-semibold">Annual DC demand</h2>
                {run.phases.length === 0 ? (
                  <p className="mt-3 text-sm text-subtle">
                    Choose phases above to populate the demand profile.
                  </p>
                ) : (
                  <div className="mt-4 space-y-3">
                    {annual.map((a) => (
                      <div
                        key={a.year}
                        className="grid grid-cols-[40px_1fr_100px] items-center gap-3 text-xs"
                      >
                        <span>{a.year}</span>
                        <div className="h-5 rounded bg-workspace">
                          <div
                            className="h-5 rounded bg-brand"
                            style={{ width: `${(a.hours / largest) * 100}%` }}
                          />
                        </div>
                        <span className="text-right">{number(a.hours)} h</span>
                      </div>
                    ))}
                  </div>
                )}
                <p className="mt-4 text-xs text-subtle">
                  {number(run.outsideWindowHours)} paid hours fall outside this
                  window and remain in the exported phase totals.
                </p>
                {run.phases.map((p) => (
                  <p key={p.id} className="mt-2 text-xs text-subtle">
                    {p.name}: {p.basis}.
                  </p>
                ))}
              </section>
              <section className={panel} aria-label="Enabling infrastructure cost allocation">
                <h2 className="text-lg font-semibold">Enabling infrastructure &amp; cost allocation</h2>
                <p className="mt-2 text-sm text-subtle">
                  Separate $50B counterfactual diligence ledger: the $4B grid-and-generation
                  assumption is already inside AI CAPEX. It is not an additional public cost
                  and is not scaled by the selected project phases.
                </p>
                <p className="mt-2 text-sm">
                  {enablingSummary.unresolvedAssets} enabling asset scopes remain unresolved.
                  Incremental costs, funding, timing and ultimate payers are unknown.
                  Combined program cost: {enablingSummary.totalProgramCad === null ? 'withheld' : 'available as a scenario range'}.
                </p>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-subtle">
                  {enablingLedger.assets.map(asset => <li key={asset.id}>
                    {asset.assetClass}: cost {asset.costCad === null ? 'unknown' : `$${number(asset.costCad.low)}–$${number(asset.costCad.high)} CAD (${asset.costBasis})`};
                    payer {Object.entries(asset.payerShares).map(([payer, share]) => `${payer} ${Math.round(share * 100)}%`).join(', ')};
                    AI CAPEX membership {asset.aiCapexMembership}.
                  </li>)}
                </ul>
                <p className="mt-2 text-xs text-subtle">
                  These are scenario dependency placeholders, not observed assets or commitments.
                  Baseline work is excluded from incremental cost; included costs cannot be counted
                  twice. Unknown assets do not supply measured demand to the schedule.
                  The JSON export preserves phase links, evidence, payer shares and reconciliation.
                </p>
              </section>
              <section className={panel}>
                <h2 className="text-lg font-semibold">Paired resource schedule</h2>
                <p className="mt-2 text-sm text-subtle">
                  Same background demand in both cases; pro-rata allocation by Alberta trade,
                  with civil enabling works preceding electrical and mechanical packages.
                  This precedence is a scenario assumption, not an observed project network.
                  Other private demand defaults to zero and therefore remains omitted until entered.
                </p>
                <p className="mt-2 text-sm">
                  Unfinished paid hours at the extended horizon: baseline {number(run.scheduling.baseline.tailHours)},
                  with DC {number(run.scheduling.withDC.tailHours)}.
                  {run.scheduling.impacts.filter((p) => (p.incrementalDelayMonths ?? 0) > 0).length} background
                  packages have a modelled incremental delay;
                  {run.scheduling.impacts.filter((p) => p.incrementalDelayMonths === null).length} have unknown completion.
                </p>
                <p className="mt-2 text-xs text-subtle">
                  Monthly allocations, carried backlog, completion dates, paired impacts and
                  horizon tails are included in the JSON export. Capacity is an assumption;
                  unknown capacity produces unknown completion. No public package cost
                  exposure is supplied, so this run does not estimate owner cost escalation.
                  The separate delay illustration remains user entered.
                </p>
              </section>
              <section className={panel}>
                <div className="flex flex-wrap justify-between gap-3">
                  <h2 className="text-lg font-semibold">
                    Quarterly demand & conditional gap
                  </h2>
                  <button
                    className="text-sm text-brand underline"
                    onClick={() =>
                      download(
                        'construction-quarterly.csv',
                        [
                          'quarter,trade,dc_hours,public_hours,private_hours,dc_fte,capacity_hours,ratio,unmet_hours',
                          ...run.rows.map((r) =>
                            [
                              r.quarter,
                              r.trade,
                              r.dcHours,
                              r.publicHours,
                              r.privateHours,
                              r.dcFte,
                              r.capacityHours ?? '',
                              r.ratio ?? '',
                              r.gap ?? '',
                            ].join(','),
                          ),
                        ].join('\n'),
                      )
                    }
                  >
                    Download quarterly CSV
                  </button>
                </div>
                <p className="mt-2 text-xs text-subtle">
                  FY anchors: $10.687B / $9.998B / $8.349B. April–March cash is
                  allocated evenly across months. Named projects are not added
                  on top. Cohort commitments are in the export; changing cohort
                  duration changes starts, not the fixed cash envelope.
                </p>
                {run.invalidCohorts && (
                  <p role="alert" className="mt-2 text-caution">
                    This spending trajectory requires negative cohort
                    commitments. Use the cash envelope only; revise the cohort
                    assumptions before presenting cohort starts.
                  </p>
                )}
                <div className="mt-4 max-h-[440px] overflow-auto">
                  <table className="w-full min-w-[730px] text-left text-xs">
                    <thead className="sticky top-0 bg-workspace">
                      <tr>
                        {[
                          'Quarter',
                          'Trade',
                          'DC hours',
                          'Public hours',
                          'Private hours',
                          'DC FTE',
                          'Demand / capacity',
                          'Unmet hours',
                        ].map((h) => (
                          <th key={h} className="p-3">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {run.rows.map((r) => (
                        <tr
                          className="border-b border-line"
                          key={r.quarter + r.trade}
                        >
                          <td className="p-3">{r.quarter}</td>
                          <td>{r.trade}</td>
                          <td>{number(r.dcHours)}</td>
                          <td>{number(r.publicHours)}</td>
                          <td>{number(r.privateHours)}</td>
                          <td>{number(r.dcFte)}</td>
                          <td>
                            {r.ratio === null
                              ? r.capacityHours === 0
                                ? 'Zero capacity'
                                : 'Unknown'
                              : `${r.ratio.toFixed(2)}×`}
                          </td>
                          <td>{r.gap === null ? 'Unknown' : number(r.gap)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </>
      )}
      {tab === 'Benchmarks & sources' && (
        <section className={panel}>
          <div className="flex flex-wrap justify-between gap-3">
            <h2 className="text-lg font-semibold">
              Evidence & assumption register
            </h2>
            <a
              href="/data/construction/benchmarks.json"
              download
              className="text-sm text-brand underline"
            >
              Download full register
            </a>
          </div>
          <p className="mt-2 text-sm text-subtle">
            {benchmarks.parameters.length} entries · {benchmarks.sources.length}{' '}
            original sources. Historical benchmarks and forecasts retain their
            original dates. Missing values are not zero.
          </p>
          <label className="mt-4 block text-xs">
            Find a benchmark
            <input
              className={input}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search labour, transformer, capital…"
            />
          </label>
          <div className="mt-4 space-y-3">
            {benchmarks.parameters
              .filter((p) =>
                JSON.stringify(p).toLowerCase().includes(query.toLowerCase()),
              )
              .map((p) => (
                <article
                  className="rounded-md border border-line p-4"
                  key={p.id}
                >
                  <div className="flex flex-wrap justify-between gap-2">
                    <h3 className="font-medium">{p.id.replaceAll('_', ' ')}</h3>
                    <span className="text-xs text-subtle">
                      {p.status.replaceAll('_', ' ')}
                    </span>
                  </div>
                  <p className="mt-2 font-mono text-brand">
                    {p.value === null
                      ? 'Not available'
                      : Array.isArray(p.value)
                        ? p.value.join(' / ')
                        : String(p.value)}{' '}
                    <span className="text-xs">{p.unit}</span>
                  </p>
                  <p className="mt-2 text-sm text-subtle">{p.notes}</p>
                  {p.source_ids.map((id) => {
                    const s = benchmarks.sources.find((s) => s.id === id);
                    return s ? (
                      <p key={id} className="mt-2 text-xs">
                        <a
                          className="text-brand underline"
                          href={s.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {id} · {s.period}
                        </a>
                        <br />
                        {s.scope}
                      </p>
                    ) : null;
                  })}
                </article>
              ))}
          </div>
          <h3 className="mt-6 text-lg font-semibold">All original sources</h3>
          <div className="mt-3 space-y-3">
            {benchmarks.sources.map((s) => (
              <p key={s.id} className="text-sm">
                <a
                  className="text-brand underline"
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {s.id} · {s.period}
                </a>
                <br />
                <span className="text-subtle">{s.scope}</span>
              </p>
            ))}
          </div>
        </section>
      )}
      {tab === 'Formulas' && (
        <section className={panel}>
          <h2 className="text-lg font-semibold">
            Presentation formula library
          </h2>
          <p className="mt-2 text-sm text-subtle">
            F02–F06 power the quarterly screen. F07–F08 power the separate
            illustrations. F01 is the specified quantity route awaiting
            authorized item rates; F09 explains efficiency conversion.
          </p>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {formulas.map(([id, title, equation, note]) => (
              <article key={id} className="rounded-md border border-line p-4">
                <p className="text-xs text-brand">{id}</p>
                <h3 className="mt-1 font-semibold">{title}</h3>
                <p className="mt-3 break-words rounded bg-workspace p-3 font-mono text-sm">
                  {equation}
                </p>
                <p className="mt-3 text-sm text-subtle">{note}</p>
              </article>
            ))}
          </div>
        </section>
      )}
      {tab === 'Procurement & cost' && (
        <>
          <section className={panel}>
            <h2 className="text-lg font-semibold">
              Equipment procurement windows
            </h2>
            <p className="mt-2 text-sm text-subtle">
              SourceBlue Q2 2026 · US national ranges, not Alberta quotes.
              Exposure is measured before package float or critical-path
              assessment.
            </p>
            <div className="my-4 max-w-xs">
              <Field
                label="Weeks until required on site"
                value={need}
                onChange={(n) => setNeed(Math.max(0, n))}
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {benchmarks.parameters
                .filter((p) => p.id.startsWith('procurement_'))
                .map((p) => {
                  const v = p.value as number[];
                  return (
                    <article
                      key={p.id}
                      className="rounded border border-line p-4"
                    >
                      <h3 className="text-sm font-medium">
                        {p.id.replace('procurement_', '').replaceAll('_', ' ')}
                      </h3>
                      <p className="mt-2 text-xl text-brand">
                        {v.join('–')} weeks
                      </p>
                      <p className="mt-2 text-xs text-subtle">
                        Potential delivery exposure: {Math.max(0, v[0] - need)}–
                        {Math.max(0, v[1] - need)} weeks
                      </p>
                    </article>
                  );
                })}
            </div>
          </section>
          <section className={panel}>
            <h2 className="text-lg font-semibold">
              Delay escalation illustration
            </h2>
            <p className="mt-2 text-sm text-subtle">
              Enter a hypothetical delay. This calculation does not derive delay
              from workforce pressure, and applies only to uncommitted exposed
              cost.
            </p>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <Field
                label="Uncommitted exposure (CAD M)"
                value={exposure}
                onChange={(n) => setExposure(Math.max(0, n))}
              />
              <Field
                label="Delay (months)"
                value={delay}
                onChange={(n) => setDelay(Math.max(0, n))}
              />
              <Field
                label="Annual escalation (%)"
                value={rate}
                step={0.1}
                onChange={(n) => setRate(Math.max(0, n))}
              />
            </div>
            <p className="mt-5 text-2xl font-semibold text-brand">
              CAD {number(escalation(exposure * 1e6, rate / 100, delay))}
            </p>
            <p className="mt-1 text-xs text-subtle">
              Additional escalation under these assumptions · Formula F08
            </p>
          </section>
        </>
      )}
      <section className={panel} aria-label="Alberta presentation export">
        <h2 className="mb-2 font-semibold text-ink">
          Alberta delivery briefing
        </h2>
        <BriefingDownload />
      </section>
    </div>
  );
}
