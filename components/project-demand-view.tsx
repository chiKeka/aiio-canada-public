import type { ConstructionData } from '@/lib/construction-snapshot';
import { buildDemandRisk } from '@/lib/demand-risk-analysis.mjs';
import evidence from '@/public/data/construction/adm-evidence.json';
export function ProjectDemandView({ data }: { data: ConstructionData }) {
  const risk = buildDemandRisk(data.projects, {
    asOf: data.manifest.asOf,
    exposure: evidence.exposure,
  });
  const m = risk.full;
  const central = m.scenarios[1];
  const regional = [...new Set(central.contributors.map((p) => p.region))].map(
    (region) => ({
      region,
      electrical: central.contributors
        .filter((p) => p.region === region)
        .reduce(
          (sum, p) =>
            sum +
            (p.annual.find((r) => r.year === central.peak.year)
              ?.electricalFTE ?? 0),
          0,
        ),
    }),
  );
  const fmt = (n: number) => Math.round(n).toLocaleString('en-CA');
  const date = (n: number) =>
    `${Math.floor(n / 12)}-${String((n % 12) + 1).padStart(2, '0')}`;
  return (
    <section className="space-y-4 rounded-lg border border-line bg-surface p-5">
      <a
        href="/api/construction/demand"
        download
        className="text-sm text-brand underline"
      >
        Download model inputs and results (.json)
      </a>
      <h2 className="text-xl font-semibold">
        Modelled construction labour demand
      </h2>
      <p className="text-sm">
        The {central.peak.year} electrical peak is a scheduling stress case, not
        a forecast. {m.phases.length - m.scheduleAnchored} undated phases account for $
        {fmt(risk.fallbackCapex / 1e9)}B of the costed pipeline and share a
        fallback start. At central intensity and full realization, HVAC demand
        reaches {Math.round(risk.cases[0].hvacStockRatio * 100)}% of the 2021
        workforce stock; electrical demand reaches{' '}
        {Math.round(risk.cases[0].electricalStockRatio * 100)}%. These
        historical stocks do not measure available capacity.
      </p>
      <div className="overflow-auto">
        <table className="w-full text-left text-sm">
          <caption>
            Realization and timing sensitivities · central intensity
          </caption>
          <thead>
            <tr>
              <th>Test</th>
              <th>Electrical peak / year</th>
              <th>HVAC peak / year</th>
            </tr>
          </thead>
          <tbody>
            {risk.cases.map((r) => (
              <tr className="border-t border-line" key={r.name}>
                <th className="py-3 font-normal">{r.name}</th>
                <td>
                  {fmt(r.electricalFTE)} / {r.electricalYear}
                </td>
                <td>
                  {fmt(r.hvacFTE)} / {r.hvacYear}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-subtle">{risk.interpretation}</p>
      <div className="overflow-auto">
        <table className="w-full text-left text-sm">
          <caption>Central electrical FTE by schedule evidence</caption>
          <thead>
            <tr>
              <th>Year</th>
              <th>Reported year anchor</th>
              <th>Fully fallback-scheduled</th>
            </tr>
          </thead>
          <tbody>
            {risk.annual.slice(0, 6).map((r) => (
              <tr className="border-t border-line" key={r.year}>
                <th className="py-2">{r.year}</th>
                <td>{fmt(r.anchored)}</td>
                <td>{fmt(r.fallback)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <details>
        <summary>
          {risk.exposure.length} Infrastructure records intersect{' '}
          {risk.window.start}–{risk.window.end}
        </summary>
        <ul className="mt-3 space-y-2">
          {risk.exposure.map((p) => (
            <li key={p.project_id}>
              {p.name.replaceAll('�cole', 'École')} · {p.municipality} ·{' '}
              {p.start_year}–{p.end_year}
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-subtle">
          Regional screening: Calgary ↔ Beacon Foothills, Crusoe Rocky View and
          TNE Calgary; Red Deer ↔ Crusoe Red Deer; Edmonton / St. Albert ↔ Meta
          Sturgeon and TNE Edmonton. Proximity does not establish shared
          contractors. Package dates require confirmation.
        </p>
      </details>
      <p className="text-sm text-subtle">
        {m.scheduleAnchored} costed phases have a reported year anchor;{' '}
        {m.phases.length - m.scheduleAnchored} are fully fallback-scheduled.{' '}
        {m.excluded.length} uncosted records remain unquantified. The table
        below retains the separate intensity sensitivities.
      </p>
      <div className="overflow-auto">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">Modelled annual trade demand</caption>
          <thead>
            <tr>
              <th>Year</th>
              <th>Electrical low</th>
              <th>Electrical central</th>
              <th>Electrical high</th>
              <th>HVAC central</th>
            </tr>
          </thead>
          <tbody>
            {central.annual.slice(0, 6).map((r, i) => (
              <tr className="border-t border-line" key={r.year}>
                <th className="py-3">{r.year}</th>
                <td>{fmt(m.scenarios[0].annual[i].electricalFTE)}</td>
                <td>{fmt(r.electricalFTE)}</td>
                <td>{fmt(m.scenarios[2].annual[i].electricalFTE)}</td>
                <td>{fmt(r.hvacFTE)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-subtle">
        Annual average FTE, not headcount on the busiest day. Decline reflects
        completion of this modelled cohort; later projects are not forecast.
      </p>
      <details>
        <summary className="cursor-pointer font-semibold">
          Regional contributions in the central electrical peak year
        </summary>
        <table className="mt-3 w-full text-left text-sm">
          <caption className="sr-only">Regional model demand</caption>
          <thead>
            <tr>
              <th>Reported municipality</th>
              <th>Modelled electrician FTE · {central.peak.year}</th>
            </tr>
          </thead>
          <tbody>
            {regional.map((r) => (
              <tr className="border-t border-line" key={r.region}>
                <th className="py-2 font-normal">{r.region}</th>
                <td>{fmt(r.electrical)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-2 text-xs text-subtle">
          Project location is not worker residence or proof of a shared labour
          catchment.
        </p>
      </details>
      <details>
        <summary className="cursor-pointer font-semibold">
          Project schedule inputs and model parameters
        </summary>
        <div className="overflow-auto">
          <table className="mt-3 w-full text-left text-xs">
            <caption className="sr-only">Project model schedule audit</caption>
            <thead>
              <tr>
                <th>Project</th>
                <th>Model start</th>
                <th>Model finish</th>
                <th>Basis</th>
              </tr>
            </thead>
            <tbody>
              {m.phases.map((p) => (
                <tr key={p.id} className="border-t border-line">
                  <th className="py-3 pr-2 font-normal">{p.name}</th>
                  <td>{date(p.startMonth)}</td>
                  <td>{date(p.endMonth - 1)}</td>
                  <td>{p.basis}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-sm">
          Low / central / high construction shares: 30 / 40 / 50%; labour
          shares: 30 / 35 / 40%; loaded paid-hour costs: $100 / $90 / $80. All
          cases use 1,840 paid hours/FTE-year and electrician/HVAC payroll
          shares of 20% / 10%. Undated phases start 18 months after the evidence
          date and run for 36 months. Monthly triangular profiles allocate
          electrical work to 25–100% of the field period and HVAC to 30–100%.
          These coefficients and fallback schedules are uncalibrated model
          inputs.
        </p>
        <p className="mt-3 text-sm">
          Total trade hours = project cost × construction share × labour share ÷
          hourly cost × trade payroll share. Each monthly profile integrates to
          one; annual FTE = annual allocated hours ÷ 1,840. The proposed-project
          volume factor multiplies hours before allocation. No calibrated
          probability, spare crew capacity or cost elasticity is inferred.
        </p>
      </details>
    </section>
  );
}
