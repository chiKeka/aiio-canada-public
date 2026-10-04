'use client';

import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Check, GitBranch, Link2, Zap } from 'lucide-react';

import { EvidencePill } from '@/components/site-shell';
import scenarioSuite from '@/data/model-runs/alberta_50b_scenario_suite_v0.1.json';
import releaseData from '@/public/data/latest.json';
import { boundedDisplayScore } from '@/lib/decision-analysis';

type PowerCase = 'low' | 'central' | 'high';
type VariantId =
  | 'staggered'
  | 'front_loaded'
  | 'constrained_delivery'
  | 'high_local_capture';

const VARIANT_IDS: VariantId[] = [
  'staggered',
  'front_loaded',
  'constrained_delivery',
  'high_local_capture',
];

export function ScenarioLab({
  initialPower = 'central',
  initialVariant = 'staggered',
}: {
  initialPower?: PowerCase;
  initialVariant?: VariantId;
}) {
  const [variantId, setVariantId] = useState<VariantId>(initialVariant);
  const [powerCase, setPowerCase] = useState<PowerCase>(initialPower);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set('variant', variantId);
    url.searchParams.set('power', powerCase);
    window.history.replaceState(null, '', url);
  }, [variantId, powerCase]);

  async function shareScenario() {
    const url = window.location.href;
    try {
      if (navigator.share)
        await navigator.share({ title: 'AIIO Canada scenario', url });
      else await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return;
      console.error('Scenario link could not be shared', error);
    }
  }
  const selected = scenarioSuite.variant_summaries.find(
    (item) => item.variant_id === variantId,
  )!;
  const power = releaseData.power_overlay.cases[powerCase];
  const tradeRows = useMemo(
    () =>
      scenarioSuite.comparison_matrix
        .filter((item) => item.node_type === 'resource')
        .map((item) => {
          const value = item.values.find(
            (entry) => entry.variant_id === variantId,
          )!;
          return {
            ...item,
            ...value,
            displayed: boundedDisplayScore(value.raw_central_pressure_score),
          };
        })
        .sort(
          (a, b) => b.raw_central_pressure_score - a.raw_central_pressure_score,
        ),
    [variantId],
  );
  const maxTrade = Math.max(...tradeRows.map((item) => item.displayed), 0.01);
  const maxAnnual = Math.max(
    ...selected.annual_capex_profile.map((item) => item.total_capex_cad),
  );
  const selectedHospital = scenarioValue(
    'SCHEDULE_HOSPITALS_DELAY_PRESSURE',
    variantId,
  );
  const referenceHospital = scenarioValue(
    'SCHEDULE_HOSPITALS_DELAY_PRESSURE',
    'staggered',
  );
  const selectedElectrician = scenarioValue('TRADE_ELECTRICIANS', variantId);
  const referenceElectrician = scenarioValue('TRADE_ELECTRICIANS', 'staggered');

  return (
    <div className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="self-start rounded-lg border border-line bg-surface p-5 xl:sticky xl:top-6">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Scenario variants</h2>
          <EvidencePill status="scenario" />
        </div>
        <p className="mt-2 text-xs leading-5 text-subtle">
          Four versioned $50B stress cases isolate timing and local capture.
          Each selection is a reproducible model run.
        </p>
        <div className="mt-6 space-y-2" aria-label="Alberta scenario variant">
          {VARIANT_IDS.map((id) => {
            const variant = scenarioSuite.variant_summaries.find(
              (item) => item.variant_id === id,
            )!;
            const active = variantId === id;
            return (
              <button
                aria-pressed={active}
                className={`w-full rounded-lg border p-3 text-left transition ${active ? 'border-brand/30 bg-brand-soft text-brand' : 'border-line bg-white text-subtle hover:border-line'}`}
                key={id}
                onClick={() => setVariantId(id)}
                type="button"
              >
                <span className="block text-xs font-semibold">
                  {variant.label}
                </span>
                <span className="mt-1 block text-[10px] leading-4">
                  {variant.declared_change}
                </span>
              </button>
            );
          })}
        </div>
        <div className="mt-7">
          <p className="mb-3 text-xs font-medium">Independent power case</p>
          <div className="grid grid-cols-3 gap-2">
            {(['low', 'central', 'high'] as PowerCase[]).map((option) => (
              <button
                aria-pressed={powerCase === option}
                className={`rounded-lg border py-2 text-xs capitalize ${powerCase === option ? 'border-caution/30 bg-caution-soft text-caution' : 'border-line bg-white text-subtle'}`}
                key={option}
                onClick={() => setPowerCase(option)}
                type="button"
              >
                {option}
              </button>
            ))}
          </div>
        </div>
        <button
          className="mt-7 flex w-full items-center justify-center gap-2 rounded-lg bg-brand px-4 py-3 text-sm font-medium text-white transition hover:bg-brand/90"
          onClick={shareScenario}
          type="button"
        >
          {copied ? <Check className="size-4" /> : <Link2 className="size-4" />}
          {copied ? 'Link copied' : 'Share this view'}
        </button>
        <div className="mt-3 rounded-lg bg-workspace p-4">
          <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-subtle">
            Run status
          </p>
          <p className="mt-2 text-sm font-medium text-brand">
            Versioned structural run
          </p>
          <p className="mt-1 break-words text-xs leading-5 text-subtle">
            {selected.scenario_id} · no forecast authorization
          </p>
          <p className="mt-2 text-[10px] leading-4 text-subtle">
            The URL records the selected variant and power case; it stores no
            project or personal data.
          </p>
        </div>
      </aside>

      <div className="min-w-0 space-y-6">
        <section className="rounded-lg border border-caution/30 bg-caution-soft p-5 text-sm leading-6 text-caution">
          <strong className="text-caution">
            Uncalibrated structural diagnostic.
          </strong>{' '}
          Scores compare declared pressure pathways; they are not forecasts,
          probabilities, cost escalation percentages or delay durations. A score
          of 0.24 does not mean a 24% delay, and 54% of capex remains outside
          the graph.
        </section>

        <section className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-4">
          <Summary
            label="Peak annual capex"
            value={formatBillions(selected.peak_annual_capex_cad)}
            note={`${selected.peak_annual_capex_year} · fixed $50B total`}
          />
          <Summary
            label="Local modelled envelope"
            value={formatBillions(selected.local_modelled_capex_cad)}
            note={`46% build share × ${(selected.local_capture_share * 100).toFixed(0)}% local capture`}
          />
          <Summary
            label="Delivery window"
            value={`${selected.delivery_year_count} yrs`}
            note={`${selected.delivery_start_year}–${selected.delivery_end_year}`}
          />
          <Summary
            label="First-five-year share"
            value={`${(selected.first_five_year_capex_share * 100).toFixed(1)}%`}
            note="Timing concentration diagnostic"
          />
        </section>

        <section className="overflow-hidden rounded-lg border border-line bg-surface">
          <div className="grid gap-6 p-5 sm:p-7 xl:grid-cols-[1.15fr_0.85fr]">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-brand">
                Executive read
              </p>
              <h2 className="mt-2 text-xl font-medium text-brand">
                {selected.decision_question}
              </h2>
              <p className="mt-3 text-sm leading-6 text-subtle">
                {selected.declared_change}
              </p>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <DeltaCard
                  label="Building electricians"
                  score={selectedElectrician.raw_central_pressure_score}
                  scoreDelta={
                    selectedElectrician.raw_central_pressure_score -
                    referenceElectrician.raw_central_pressure_score
                  }
                  peakYear={selectedElectrician.central_peak_year}
                  yearDelta={
                    selectedElectrician.central_peak_year -
                    referenceElectrician.central_peak_year
                  }
                  reference={variantId === 'staggered'}
                />
                <DeltaCard
                  label="Hospital delivery pressure"
                  score={selectedHospital.raw_central_pressure_score}
                  scoreDelta={
                    selectedHospital.raw_central_pressure_score -
                    referenceHospital.raw_central_pressure_score
                  }
                  peakYear={selectedHospital.central_peak_year}
                  yearDelta={
                    selectedHospital.central_peak_year -
                    referenceHospital.central_peak_year
                  }
                  reference={variantId === 'staggered'}
                />
              </div>
            </div>
            <div className="rounded-lg border border-line bg-white p-4">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-medium">Annual capex profile</p>
                  <p className="mt-1 text-[10px] text-subtle">
                    CAD billions · {selected.label}
                  </p>
                </div>
                <p className="font-mono text-xs text-brand">
                  peak {formatBillions(selected.peak_annual_capex_cad)}
                </p>
              </div>
              <div
                className="mt-5 flex h-32 items-end gap-1.5"
                aria-label={`${selected.label} annual capital expenditure profile`}
              >
                {selected.annual_capex_profile.map((item) => (
                  <div
                    className="group flex h-full min-w-0 flex-1 flex-col items-center justify-end"
                    key={item.year}
                  >
                    <span className="mb-1 hidden font-mono text-[8px] text-subtle group-hover:block">
                      {(item.total_capex_cad / 1_000_000_000).toFixed(1)}
                    </span>
                    <div
                      className="w-full rounded-t-sm bg-brand"
                      style={{
                        height: `${Math.max((item.total_capex_cad / maxAnnual) * 100, 4)}%`,
                      }}
                      title={`${item.year}: ${formatBillions(item.total_capex_cad)}`}
                    />
                    <span className="mt-2 origin-center -rotate-45 font-mono text-[8px] text-subtle">
                      {String(item.year).slice(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-line bg-surface p-5 sm:p-7">
          <div className="flex flex-col justify-between gap-3 border-b border-line pb-5 sm:flex-row sm:items-center">
            <div>
              <div className="flex items-center gap-2">
                <GitBranch className="size-4 text-brand" />
                <h2 className="font-medium">Which trades pinch first?</h2>
              </div>
              <p className="mt-1 text-xs text-subtle">
                Selected variant · bounded display index [0,1) · raw scores
                retained in the evidence artifact
              </p>
            </div>
            <span className="font-mono text-xs text-subtle">
              peak year shown at right
            </span>
          </div>
          <div className="mt-6 space-y-5">
            {tradeRows.map((item, index) => (
              <div key={item.node_id}>
                <div className="mb-2 flex justify-between text-xs">
                  <span>
                    <span className="mr-2 font-mono text-subtle">
                      0{index + 1}
                    </span>
                    {item.label}
                  </span>
                  <span className="font-mono text-brand">
                    {item.displayed.toFixed(3)} · {item.central_peak_year}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-workspace">
                  <div
                    className={`h-full rounded-full ${index === 0 ? 'bg-caution' : 'bg-brand'}`}
                    style={{ width: `${(item.displayed / maxTrade) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-line bg-workspace p-5 sm:p-7">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-brand">
                Cross-variant scan
              </p>
              <h2 className="mt-1 font-medium">
                Same program, different pressure profile
              </h2>
            </div>
            <span className="rounded-full bg-white px-3 py-1 font-mono text-[10px] text-subtle">
              4 model runs
            </span>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-2 2xl:grid-cols-4">
            {scenarioSuite.variant_summaries.map((item) => (
              <button
                className={`rounded-lg border p-4 text-left ${variantId === item.variant_id ? 'border-brand/30 bg-workspace' : 'border-line bg-white hover:border-line'}`}
                key={item.variant_id}
                onClick={() => setVariantId(item.variant_id as VariantId)}
                type="button"
              >
                <p className="text-xs font-semibold text-brand">{item.label}</p>
                <p className="mt-3 font-mono text-xl text-brand">
                  {boundedDisplayScore(
                    item.top_trade.raw_central_pressure_score,
                  ).toFixed(3)}
                </p>
                <p className="mt-1 text-[10px] leading-4 text-subtle">
                  Top trade: {item.top_trade.label} · peaks{' '}
                  {item.top_trade.central_peak_year}
                </p>
                <div className="mt-3 border-t border-line pt-3 text-[10px] text-subtle">
                  <span>
                    Cost signal{' '}
                    {boundedDisplayScore(
                      item.nonresidential_cost_signal
                        .raw_central_pressure_score,
                    ).toFixed(3)}
                  </span>
                  <span className="float-right">
                    {item.delivery_year_count} years
                  </span>
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-line bg-surface p-5">
            <div className="flex items-center gap-2">
              <Zap className="size-4 text-caution" />
              <h2 className="font-medium">Independent power overlay</h2>
            </div>
            <p className="mt-2 text-xs text-subtle">
              Selected {powerCase} MW case; it does not respond to the CAD
              variants above.
            </p>
            <dl className="mt-5 space-y-3 text-sm">
              <PowerRow
                label="IT load at full buildout"
                value={`${(power.assumptions.it_load_mw_at_full_buildout / 1000).toFixed(1)} GW`}
              />
              <PowerRow
                label="Facility peak"
                value={`${(power.full_buildout.facility_peak_mw / 1000).toFixed(1)} GW`}
              />
              <PowerRow
                label="Annual facility energy"
                value={`${(power.full_buildout.annual_energy_gwh / 1000).toFixed(1)} TWh`}
              />
              <PowerRow
                label="Grid-coincident demand"
                value={`${(power.full_buildout.grid_coincident_mw / 1000).toFixed(2)} GW`}
              />
              <PowerRow
                label="Planning transfer proxy"
                value={`${(power.full_buildout.planning_transfer_proxy_mw / 1000).toFixed(2)} GW`}
              />
            </dl>
          </div>
          <div className="rounded-lg border border-caution/30 bg-caution-soft p-5">
            <div className="flex items-center gap-2 text-caution">
              <AlertTriangle className="size-4" />
              <h2 className="font-medium">Interpretation boundary</h2>
            </div>
            <p className="mt-4 text-sm leading-6 text-caution">
              Power is independent of capex. Energy PUE affects annual energy,
              while a separate peak-to-IT factor affects peak demand. The
              transfer proxy is not a project plan, available-capacity statement
              or AESO needs assessment.
            </p>
            <p className="mt-4 text-xs text-caution">
              {releaseData.power_overlay.structural_test_banner}
            </p>
          </div>
        </section>

        <section className="rounded-lg border border-line bg-surface p-5 sm:p-7">
          <h2 className="font-medium">Dominant structural path</h2>
          <div className="mt-5 flex flex-wrap items-center gap-2">
            {releaseData.scenario.dominant_outcome_paths[0].node_path.map(
              (node, index) => (
                <span className="contents" key={`${node}-${index}`}>
                  <span className="rounded-full border border-line bg-white px-3 py-1.5 text-xs">
                    {node.replaceAll('_', ' ').toLowerCase()}
                  </span>
                  {index <
                  releaseData.scenario.dominant_outcome_paths[0].node_path
                    .length -
                    1 ? (
                    <span className="text-subtle">→</span>
                  ) : null}
                </span>
              ),
            )}
          </div>
          <p className="mt-4 text-xs leading-5 text-subtle">
            This declared demand-to-resource-to-delay-pressure mechanism
            explains the graph pathway. It does not predict a specific project
            cost or delay.
          </p>
        </section>
      </div>
    </div>
  );
}

function scenarioValue(nodeId: string, variantId: VariantId) {
  return scenarioSuite.comparison_matrix
    .find((item) => item.node_id === nodeId)!
    .values.find((item) => item.variant_id === variantId)!;
}

function formatBillions(value: number) {
  return `$${(value / 1_000_000_000).toFixed(value % 1_000_000_000 === 0 ? 0 : 2)}B`;
}

function signed(value: number, suffix = '') {
  return `${value > 0 ? '+' : ''}${value}${suffix}`;
}

function DeltaCard({
  label,
  score,
  scoreDelta,
  peakYear,
  yearDelta,
  reference,
}: {
  label: string;
  score: number;
  scoreDelta: number;
  peakYear: number;
  yearDelta: number;
  reference: boolean;
}) {
  return (
    <div className="rounded-lg border border-line bg-white p-4">
      <p className="text-xs font-medium">{label}</p>
      <div className="mt-3 flex items-end justify-between">
        <p className="font-mono text-xl text-brand">
          {boundedDisplayScore(score).toFixed(3)}
        </p>
        <p className="font-mono text-[10px] text-subtle">peak {peakYear}</p>
      </div>
      <p className="mt-2 text-[10px] leading-4 text-subtle">
        {reference
          ? 'Reference structural run'
          : `${signed(Number(scoreDelta.toFixed(2)))} raw pressure · ${signed(yearDelta, yearDelta === 1 || yearDelta === -1 ? ' year' : ' years')}`}
      </p>
    </div>
  );
}

function Summary({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <p className="font-mono text-2xl font-semibold text-brand">{value}</p>
      <p className="mt-2 text-xs font-medium">{label}</p>
      <p className="mt-1 text-[10px] leading-4 text-subtle">{note}</p>
    </div>
  );
}
function PowerRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-line pb-3 last:border-0">
      <dt className="text-subtle">{label}</dt>
      <dd className="font-mono font-medium text-brand">{value}</dd>
    </div>
  );
}
