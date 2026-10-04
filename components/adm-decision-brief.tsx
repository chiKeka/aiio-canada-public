import { createHash } from 'node:crypto';
import deck from '@/public/data/construction/adm-deck.json';
import { ProjectDemandView } from '@/components/project-demand-view';
import { buildDemandRisk } from '@/lib/demand-risk-analysis.mjs';
import Link from 'next/link';
import type { ConstructionData } from '@/lib/construction-snapshot';
import evidence from '@/public/data/construction/adm-evidence.json';
import { planSensitivity, buildAdmAnalysis } from '@/lib/adm-analysis.mjs';
export function AdmDecisionBrief({
  data,
  revision,
}: {
  data: ConstructionData;
  revision: string;
}) {
  const a = buildAdmAnalysis(data);
  const signature = createHash('sha256')
    .update(
      JSON.stringify({
        revision,
        analysis: a,
        evidence,
        risk: buildDemandRisk(data.projects, {
          asOf: data.manifest.asOf,
          exposure: evidence.exposure,
        }),
      }),
    )
    .digest('hex');
  const fmt = (n: number) => Math.round(n).toLocaleString('en-CA');
  const cls = 'rounded-lg border border-line bg-surface p-5 space-y-4';
  return (
    <section className="space-y-5" aria-label="ADM decision briefing">
      <div className={cls}>
        <h2 className="text-xl font-semibold">ADM decision briefing</h2>
        {signature === deck.signature ? (
          <div className="flex flex-wrap gap-4">
            <a className="text-brand underline" href={deck.path}>
              Download the decision briefing · {deck.date} (.pptx)
            </a>
            <a className="text-brand underline" href={deck.appendixPath}>
              Download the evidence appendix (.pptx)
            </a>
          </div>
        ) : (
          <p className="text-sm">
            Evidence or assumptions have changed since the dated decision deck.
            Regenerate it before use. The current calculations remain below.
          </p>
        )}
        <p className="text-sm text-subtle">
          13 briefing slides, with full project registers in a separate
          appendix. This dated decision deck is separate from the automatically
          generated evidence-only export.
        </p>
      </div>
      <div className={cls}>
        <h2 className="text-xl font-semibold">
          Sizing the capital-plan exposure
        </h2>
        <p className="text-sm">
          Each 1% of the ${a.plan / 1000}B capital plan is about $
          {fmt(a.onePercent)}M. A 10% price movement on a quarter of the plan is
          ${fmt(a.plan * 0.25 * 0.1)}M, or 2.5% of the whole plan.
        </p>
        <p className="text-sm text-subtle">
          Consolidated provincial plan, not Infrastructure’s vertical envelope.
          The same test is $25M per $1B of scope at 25% exposure and a 10%
          shock. Infrastructure’s uncommitted envelope requires confirmation.
          The exposed share is an assumption and must exclude committed,
          protected or unaffected spending. This is not an additional
          data-centre premium or a proposed contingency allocation.
        </p>
        <div className="overflow-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">
              Ten percent price shock sensitivity
            </caption>
            <thead>
              <tr>
                <th>Assumed exposed share</th>
                <th>10% price shock</th>
                <th>Whole-plan equivalent</th>
              </tr>
            </thead>
            <tbody>
              {a.sensitivities.map((r) => (
                <tr className="border-t border-line" key={r.share}>
                  <td className="py-3">{r.share * 100}%</td>
                  <td>${fmt(r.costMillions)}M</td>
                  <td>{r.planPct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <details className={cls}>
        <summary className="cursor-pointer font-semibold">
          Observed component movements applied to 25% of the plan
        </summary>
        <p className="text-sm">
          Independent component tests, not additive. Industrial-factory
          bid-price movements, Q2 2026 versus Q2 2025, are applied as a stress
          rather than a forecast.
        </p>
        <div className="overflow-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Component price sensitivity</caption>
            <thead>
              <tr>
                <th>City</th>
                <th>Component</th>
                <th>Observed YoY</th>
                <th>25% exposure stress</th>
              </tr>
            </thead>
            <tbody>
              {data.evidence.prices.map((p) => (
                <tr
                  key={`${p.geography_id}-${p.component}`}
                  className="border-t border-line"
                >
                  <td className="py-2">
                    {p.geography_id === 'CMA_825' ? 'Calgary' : 'Edmonton'}
                  </td>
                  <td>{p.component.replaceAll('_', ' ')}</td>
                  <td>{p.year_over_year_percent_change.toFixed(2)}%</td>
                  <td>
                    $
                    {fmt(
                      planSensitivity(
                        a.plan,
                        0.25,
                        p.year_over_year_percent_change,
                      ).costMillions,
                    )}
                    M
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      <ProjectDemandView data={data} />
      <details className={cls}>
        <summary className="cursor-pointer text-xl font-semibold">
          Infrastructure exposure register · {evidence.exposure.length} records
        </summary>
        <p className="text-sm">
          {evidence.scope} Snapshot {evidence.inventoryAsOf}.{' '}
          {evidence.missingScheduleCount} additional Infrastructure-developer
          records have incomplete schedules. Package intersections below are
          engineering screening categories, not verified work phases.
        </p>
        <div className="max-h-[32rem] overflow-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">
              Infrastructure developer projects overlapping 2027–2036
            </caption>
            <thead>
              <tr>
                <th>Project</th>
                <th>Municipality</th>
                <th>Reported stage</th>
                <th>Years</th>
                <th>Package screen</th>
              </tr>
            </thead>
            <tbody>
              {evidence.exposure.map((p) => (
                <tr key={p.project_id} className="border-t border-line">
                  <th className="py-3 pr-3 font-normal">{p.name}</th>
                  <td>{p.municipality}</td>
                  <td>{p.stage}</td>
                  <td>
                    {p.start_year}–{p.end_year}
                  </td>
                  <td>Electrical, cooling, commissioning</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      <div className={cls}>
        <h2 className="text-xl font-semibold">Power and connection exposure</h2>
        <p className="text-sm">
          {evidence.power.length} enabling-power proposals total $
          {(evidence.power.reduce((s, p) => s + p.cost, 0) / 1e9).toFixed(1)}B.
          These are examined separately from the core data-centre investment to
          avoid treating generation as data-centre construction.
        </p>
        {evidence.power.map((p) => (
          <p className="text-sm" key={p.name}>
            <a className="text-brand underline" href={p.source}>
              {p.name}
            </a>
            : {p.region}, {p.mw} MW, proposed completion {p.end}.
          </p>
        ))}
        <p className="text-sm">
          <a
            className="text-brand underline"
            href={evidence.powerContext.source}
          >
            AESO Phase 1
          </a>
          : 1,200 MW allocated to executed load contracts, verified{' '}
          {evidence.powerContext.verifiedOn}.{' '}
          {evidence.powerContext.interpretation}
        </p>
        <p className="text-sm font-semibold">
          Planning ask: reconcile facility power-on dates with utilities and
          AESO connection milestones, including distribution constraints and
          equipment availability.
        </p>
      </div>
      <div className={cls}>
        <h2 className="text-xl font-semibold">Proposed ADM decisions</h2>
        <ol className="list-decimal space-y-3 pl-5 text-sm">
          <li>
            Commission a 30-day review of uncommitted capital packages. Return a
            cost-weighted exposure and contingency recommendation, rather than
            applying a blanket uplift now.
          </li>
          <li>
            Direct project teams to confirm switchgear and chiller release dates
            within 60 days. Bring forward procurement only where design
            readiness and cancellation terms support it.
          </li>
          <li>
            Convene Infrastructure, Technology and Innovation, utilities and
            AESO to reconcile power-on milestones. Include trade contractors and
            training partners in a regional workforce workstream.
          </li>
        </ol>
        <Link
          className="inline-block text-sm text-brand underline"
          href="/delivery"
        >
          Track delivery evidence and actions
        </Link>
      </div>
    </section>
  );
}
