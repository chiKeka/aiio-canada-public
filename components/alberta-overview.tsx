import {
  summarizeAlbertaProjects,
  resolveConstructionBenchmark,
  constructionBenchmarkPeriods,
} from '@/lib/alberta-evidence-summary.mjs';
import type { ReactNode } from 'react';
import {
  constructionFreshness,
  type ConstructionData,
} from '@/lib/construction-snapshot';
import { ConstructionLiveUpdate } from '@/components/construction-live-update';

const format = (n: number | null | undefined) =>
  n == null ? 'Not published' : n.toLocaleString('en-CA');
const money = (n: number | null) =>
  n === null ? 'Not published' : `$${(n / 1e9).toFixed(2)}B`;
const quarter = (date: string) =>
  `Q${Math.ceil(Number(date.slice(5, 7)) / 3)} ${date.slice(0, 4)}`;
const inventoryUrl = 'https://www.majorprojects.alberta.ca/';
const statcan = (id: string) =>
  `https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=${id}`;

function Source({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-brand underline underline-offset-2"
    >
      {children}
    </a>
  );
}
function Section({
  id,
  title,
  tag,
  note,
  children,
}: {
  id: string;
  title: string;
  tag: string;
  note: ReactNode;
  children: ReactNode;
}) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-title`}
      className="scroll-mt-8 rounded-lg border border-line bg-surface p-5 sm:p-7"
    >
      <p className="text-xs font-medium uppercase tracking-wider text-brand">
        {tag}
      </p>
      <h2
        id={`${id}-title`}
        className="mt-2 text-xl font-semibold tracking-tight text-ink sm:text-2xl"
      >
        {title}
      </h2>
      <div className="mt-5 space-y-5">{children}</div>
      <div className="mt-5 border-t border-line pt-3 text-xs leading-5 text-subtle">
        {note}
      </div>
    </section>
  );
}
function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-md border border-line bg-workspace p-4">
      <p className="text-xs text-subtle">{label}</p>
      <p className="mt-2 font-mono text-2xl font-semibold text-brand">
        {value}
      </p>
      <p className="mt-2 text-xs leading-5 text-subtle">{detail}</p>
    </div>
  );
}
/* oxlint-disable jsx-a11y/no-noninteractive-tabindex -- Keyboard focus enables horizontal scrolling of wide evidence tables. */
function Table({
  caption,
  headers,
  rows,
}: {
  caption: string;
  headers: string[];
  rows: ReactNode[][];
}) {
  return (
    <section
      className="overflow-x-auto rounded-md border border-line"
      tabIndex={0}
      aria-label={caption}
    >
      <table className="w-full min-w-[600px] text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="bg-workspace">
          <tr>
            {headers.map((h) => (
              <th
                scope="col"
                key={h}
                className="px-4 py-3 font-semibold text-ink"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((row, i) => (
            <tr key={i} className="align-top">
              {row.map((cell, j) =>
                j === 0 ? (
                  <th
                    scope="row"
                    key={j}
                    className="px-4 py-3 font-medium text-ink"
                  >
                    {cell}
                  </th>
                ) : (
                  <td key={j} className="px-4 py-3 text-subtle">
                    {cell}
                  </td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
/* oxlint-enable jsx-a11y/no-noninteractive-tabindex */
function Bar({
  value,
  max,
  label,
}: {
  value: number;
  max: number;
  label: string;
}) {
  return (
    <div className="min-w-28">
      <span className="font-mono text-ink">{label}</span>
      <div aria-hidden="true" className="mt-2 h-1.5 rounded bg-workspace">
        <div
          className="h-full rounded bg-brand"
          style={{
            width: `${Math.min(100, Math.max(0, (value / Math.max(1, max)) * 100))}%`,
          }}
        />
      </div>
    </div>
  );
}

export function AlbertaOverview({
  data,
  revision,
}: {
  data: ConstructionData;
  revision: string;
}) {
  const { projects, benchmarks, evidence, manifest } = data;
  const periods = constructionBenchmarkPeriods(benchmarks);
  const parameter = (id: string) =>
    resolveConstructionBenchmark(benchmarks, id);
  const scalar = (id: string) => {
    const p = parameter(id);
    return p &&
      typeof p.value === 'number' &&
      /^(observed|published)/.test(p.status)
      ? p.value
      : null;
  };
  const source = (id: string) => benchmarks.sources.find((s) => s.id === id);

  const { costed, scheduled, costTotal, stages } =
    summarizeAlbertaProjects(projects);
  const inventoryDates = [...new Set(projects.map((p) => p.asOf))]
    .sort((a, b) => a.localeCompare(b))
    .join(' / ');
  const recruitment = scalar('recruitment_requirement_to2035'),
    entrants = scalar('first_time_local_entrants_to2035');
  const shortfall =
    recruitment === null || entrants === null
      ? null
      : Math.max(0, recruitment - entrants);
  const capital = evidence.capital;
  const overlap = capital.asset_class_summaries.reduce(
    (s, r) => s + r.overlap_project_count,
    0,
  );
  const classes: Record<string, string> = {
    schools_and_postsecondary: 'Schools / postsecondary',
    roads_transit_and_airports: 'Roads / transit / airports',
    health_facilities: 'Health facilities',
    power_sector_infrastructure: 'Power infrastructure',
    municipal_water_and_resilience: 'Water / resilience',
    government_and_civic_facilities: 'Government / civic',
  };
  const occupations: Record<string, string> = {
    '72200': 'Electricians, excluding industrial / power',
    '72201': 'Industrial electricians',
    '72202': 'Power-system electricians',
    '72203': 'Power-line and cable workers',
    '72402': 'HVAC mechanics',
    '73100': 'Concrete finishers',
  };
  const components = [
    ['concrete', 'Concrete'],
    ['structural_steel_framing', 'Structural steel'],
    ['electrical_systems', 'Electrical systems'],
    ['hvac', 'HVAC'],
  ];
  const equipment: Record<string, string> = {
    cooling_tower: 'Cooling towers',
    air_cooled_chiller: 'Air-cooled chillers',
    water_cooled_chiller: 'Water-cooled chillers',
    ahu: 'Air handling units',
    generator: 'Generators',
    lv_switchgear: 'Low-voltage switchgear',
    mv_switchgear: 'Medium-voltage switchgear',
    ups: 'UPS',
  };
  const procurementScale = Math.max(
    20,
    Math.ceil(
      Math.max(
        ...Object.keys(equipment).map((id) => {
          const value = parameter(`procurement_${id}`)?.value;
          return Array.isArray(value) ? Math.max(...value.map(Number)) : 0;
        }),
      ) / 20,
    ) * 20,
  );
  const guidance = evidence.guidance;
  const buildforce = source('BUILDFORCE'),
    fiscal = source('AB_Q1'),
    procurement = source('SOURCEBLUE');
  return (
    <div className="space-y-5" data-testid="alberta-overview">
      <div className="rounded-lg bg-workspace p-5 text-sm leading-6 text-ink">
        <p className="font-semibold">Alberta construction evidence</p>
        <p className="mt-1 text-subtle">
          Evidence through {manifest.asOf}. Key market indicators are shown
          below, alongside their source periods. Reported observations,
          published forecasts and analytical recommendations retain their
          separate meanings.
        </p>
        <nav
          aria-label="Alberta overview sections"
          className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-brand"
        >
          {[
            ['pipeline', 'Pipeline'],
            ['workforce', 'Labour'],
            ['materials', 'Materials'],
            ['capital', 'Competing projects'],
            ['procurement', 'Procurement'],
            ['delivery', 'Schedule & cost'],
            ['mitigation', 'Mitigation'],
          ].map(([id, label]) => (
            <a
              key={id}
              href={`#alberta-${id}`}
              className="underline underline-offset-4"
            >
              {label}
            </a>
          ))}
        </nav>
      </div>
      <ConstructionLiveUpdate revision={revision} />
      <details className="rounded-lg border border-line bg-surface p-5">
        <summary className="cursor-pointer font-semibold text-ink">
          Source updates and freshness
        </summary>
        <p className="my-3 text-sm leading-6 text-subtle">
          Structured feeds are checked by the platform’s weekly refresh. New
          observations and revisions flow through the existing review and
          publication process. Census and benchmark reports retain reviewed
          values until a replacement is accepted.
        </p>
        <Table
          caption="Alberta source update cadence and freshness"
          headers={[
            'Source / publication cadence',
            'Data period',
            'Last checked / verified',
            'Next check / review due',
            'Status',
          ]}
          rows={constructionFreshness(data).map((s) => [
            <span key={s.id}>
              <Source href={s.sourceUrl}>{s.label}</Source>
              <span className="mt-1 block text-xs">
                {s.publicationCadence} ·{' '}
                {s.mode === 'structured_feed' ? 'check' : 'review'} every{' '}
                {s.checkEveryDays} days
              </span>
            </span>,
            s.observationPeriod,
            <span key={s.id}>
              {s.lastChecked}
              <span className="mt-1 block text-xs">{s.checkBasis}</span>
            </span>,
            s.nextCheckDue,
            s.status,
          ])}
        />
        <p className="mt-3 text-xs leading-5 text-subtle">
          A successful check can find no new publication. It does not change an
          observation’s reference period. Failed checks retain the last valid
          evidence. The refresh intervals are operating policy, not promised
          source publication dates.
        </p>
      </details>
      <Section
        id="alberta-pipeline"
        title="Alberta’s data-centre pipeline"
        tag="Landscape · reported inventory"
        note={
          <>
            <Source href={inventoryUrl}>Alberta Major Projects</Source> ·
            snapshot {inventoryDates}. Records can represent phases or
            programmes rather than unique campuses. Announcements are not
            commitments; investment scopes vary and may include servers, land
            and enabling works.
          </>
        }
      >
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric
            label="Core data-centre records"
            value={format(projects.length)}
            detail="All identified core phases and programmes"
          />
          <Metric
            label="Reported investment"
            value={costed.length ? money(costTotal) : 'Not published'}
            detail={`${costed.length} costed records · ${projects.length - costed.length} missing costs`}
          />
          <Metric
            label="Reported completion years"
            value={`${scheduled.length} / ${projects.length}`}
            detail={`${projects.length - scheduled.length} records lack completion years`}
          />
          <Metric
            label={`Alberta capital plan · ${periods.fiscalYear}`}
            value={
              scalar('public_capital_q1_fy2026_27') === null
                ? 'Not published'
                : `$${(scalar('public_capital_q1_fy2026_27')! / 1000).toFixed(3)}B`
            }
            detail="Published first-quarter forecast · broad infrastructure"
          />
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {stages.map((s) => (
            <Metric
              key={s.stage}
              label={s.stage}
              value={format(s.count)}
              detail="Reported project status"
            />
          ))}
        </div>
        <Table
          caption="Reported data-centre investment by project"
          headers={['Project / phase', 'Reported investment · CAD']}
          rows={
            costed.length
              ? costed.map((p) => [
                  p.name,
                  <Bar
                    key={p.id}
                    value={p.cost!}
                    max={costed[0].cost!}
                    label={money(p.cost)}
                  />,
                ])
              : [['No costs reported', 'Not published']]
          }
        />
        <Table
          caption="Reported data-centre completion years"
          headers={['Project / phase', 'Stage', 'Completion year']}
          rows={
            scheduled.length
              ? scheduled.map((p) => [
                  p.name,
                  p.stage,
                  p.end == null ? 'Not published' : String(p.end),
                ])
              : [['No completion years reported', '—', 'Not published']]
          }
        />
        <p className="text-sm text-subtle">
          Reported completion years are estimates, not verified operating dates.
          No dates or construction durations have been inferred.
        </p>
        {fiscal && (
          <p className="text-xs text-subtle">
            <Source href={fiscal.url}>Alberta fiscal update</Source> ·{' '}
            {fiscal.period}. The capital plan is not solely construction labour
            and is not added to the named project inventory.
          </p>
        )}
        <details className="rounded-md border border-line p-4">
          <summary className="cursor-pointer font-medium text-ink">
            Full project register · {projects.length} records
          </summary>
          <div className="mt-4">
            <Table
              caption="Full Alberta data-centre register"
              headers={[
                'Project / location',
                'Stage',
                'Reported start',
                'Reported end',
                'Reported CAD',
              ]}
              rows={projects.map((p) => [
                <span key={p.id}>
                  {p.source ? (
                    <Source href={p.source}>{p.name}</Source>
                  ) : (
                    p.name
                  )}
                  <span className="mt-1 block text-xs text-subtle">
                    {p.region}
                  </span>
                </span>,
                p.stage,
                p.start == null ? 'Not published' : String(p.start),
                p.end == null ? 'Not published' : String(p.end),
                money(p.cost),
              ])}
            />
          </div>
        </details>
      </Section>
      <Section
        id="alberta-packages"
        title="Where construction resources intersect"
        tag="Engineering interpretation"
        note="Typical scope classification, not measured quantities or incremental job demand. Location, package timing, cooling design, electrical architecture and prefabrication determine actual resource overlap."
      >
        <Table
          caption="Civil electrical mechanical and utility resource intersections"
          headers={guidance.packages.headers}
          rows={guidance.packages.rows}
        />
      </Section>
      <Section
        id="alberta-workforce"
        title="Alberta labour supply and recruitment pressure"
        tag="Observed workforce · published forecast"
        note={
          <>
            <Source href={statcan('9810044901')}>Census employment</Source> ·
            Reference period {evidence.labour[0].workforce_period_start}–
            {evidence.labour[0].workforce_period_end}.{' '}
            <Source href={statcan('1410044401')}>
              Job Vacancy and Wage Survey
            </Source>{' '}
            · {quarter(evidence.labour[0].vacancy_period_end)}. Employment is a
            historical stock across industries, not available construction
            crews. The different survey periods do not support a current vacancy
            rate.
          </>
        }
      >
        <Table
          caption="Alberta trade employment and vacancies"
          headers={[
            'Occupation',
            `Employed persons · ${evidence.labour[0].workforce_period_end.slice(0, 4)}`,
            `Vacancies · ${quarter(evidence.labour[0].vacancy_period_end)}`,
            'Vacancy quality',
          ]}
          rows={evidence.labour.map((r) => [
            occupations[r.noc_code] ?? r.occupation_label,
            format(r.workforce_stock),
            format(r.vacancies),
            r.vacancies === null
              ? 'Missing / suppressed'
              : r.vacancy_quality_flags.includes('status:E')
                ? 'E · use with caution'
                : r.vacancy_quality_flags.join(', ') || 'Published',
          ])}
        />
        <h3 className="font-semibold text-ink">
          Construction recruitment outlook · {periods.recruitment}
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric
            label="Recruitment requirement"
            value={format(recruitment)}
            detail="Cumulative forecast workers"
          />
          <Metric
            label="First-time local entrants"
            value={format(entrants)}
            detail="Cumulative forecast workers"
          />
          <Metric
            label="Retirements"
            value={format(scalar('retirements_to2035'))}
            detail="Part of recruitment context; not additional demand"
          />
          <Metric
            label="Potential recruitment shortfall"
            value={format(shortfall)}
            detail="Requirement minus entrants, floored at zero"
          />
        </div>
        <p className="text-sm leading-6 text-subtle">
          {buildforce && (
            <>
              <Source href={buildforce.url}>BuildForce Alberta outlook</Source>{' '}
              · {buildforce.period}.{' '}
            </>
          )}
          These forecasts cover the whole construction market. They do not
          measure current spare labour or attribute the potential shortfall to
          data centres.
        </p>
      </Section>
      <Section
        id="alberta-materials"
        title="Construction material and system price signals"
        tag="Observed indexes · calculated changes"
        note={
          <>
            <Source href={statcan('1810028901')}>
              Statistics Canada, Table 18-10-0289-01
            </Source>{' '}
            · {quarter(evidence.prices[0].period_end)}. Industrial-factory
            construction is a proxy, not a data-centre price index. Contractor
            bid-price changes do not measure raw-material prices, physical
            quantities, supplier spare capacity or a data-centre-caused premium.
          </>
        }
      >
        <p className="text-sm text-subtle">
          Eight component changes, compared with the same quarter one year
          earlier.
        </p>
        <Table
          caption="Calgary and Edmonton year-over-year construction price changes"
          headers={['Component', 'Calgary · YoY', 'Edmonton · YoY']}
          rows={components.map(([id, label]) => [
            label,
            ...['CMA_825', 'CMA_835'].map((city) => {
              const r = evidence.prices.find(
                (r) => r.geography_id === city && r.component === id,
              );
              const value = r?.year_over_year_percent_change;
              return value == null ? 'Not published' : `${value.toFixed(2)}%`;
            }),
          ])}
        />
      </Section>
      <Section
        id="alberta-capital"
        title="Other Alberta capital projects sharing resources"
        tag="Inventory · analytical classification"
        note={
          <>
            <Source href={inventoryUrl}>Alberta Major Projects</Source> ·{' '}
            {capital.as_of_date}. AI and enabling-power records are excluded
            from this screen. Some screened projects have private owners.
            Missing schedules do not imply no overlap; overlap is not evidence
            of resource competition or project delay.
          </>
        }
      >
        <div className="grid gap-3 sm:grid-cols-2">
          <Metric
            label="Screened infrastructure records"
            value={format(capital.screened_project_count)}
            detail="Six infrastructure categories"
          />
          <Metric
            label="Known schedule overlap"
            value={format(overlap)}
            detail={`${capital.window.start_year}–${capital.window.end_year} · sum across categories`}
          />
        </div>
        <Table
          caption="Alberta infrastructure project categories and schedule overlap"
          headers={[
            'Infrastructure category',
            'Records',
            'Known schedule overlap',
          ]}
          rows={Object.entries(classes).map(([id, label]) => {
            const r = capital.asset_class_summaries.find(
              (r) => r.asset_class === id,
            );
            return [
              label,
              r ? (
                <Bar
                  key={id}
                  value={r.project_count}
                  max={Math.max(
                    ...capital.asset_class_summaries.map(
                      (r) => r.project_count,
                    ),
                  )}
                  label={format(r.project_count)}
                />
              ) : (
                'Not published'
              ),
              format(r?.overlap_project_count),
            ];
          })}
        />
      </Section>
      <Section
        id="alberta-procurement"
        title="Equipment procurement lead times"
        tag="External benchmark · US market"
        note={
          <>
            {procurement && (
              <>
                <Source href={procurement.url}>SourceBlue</Source> ·{' '}
                {procurement.period}.{' '}
              </>
            )}
            These ranges are not Alberta supplier commitments or weeks of
            project delay. Confirm product specifications, manufacturing
            release, freight, testing and installation with suppliers.
          </>
        }
      >
        <figure
          aria-label="Equipment lead-time ranges in weeks; exact values follow in the table"
          className="space-y-3"
        >
          <p className="text-xs text-subtle">
            Published US benchmark ranges · common scale 0–{procurementScale}{' '}
            weeks
          </p>
          {Object.entries(equipment).map(([id, label]) => {
            const value = parameter(`procurement_${id}`)?.value;
            if (!Array.isArray(value) || value.length !== 2) return null;
            const low = Number(value[0]),
              high = Number(value[1]);
            return (
              <div
                key={id}
                className="grid grid-cols-[8rem_1fr] items-center gap-3 text-xs sm:grid-cols-[12rem_1fr]"
              >
                <span>{label}</span>
                <div className="relative h-4 rounded bg-workspace">
                  <div
                    className="absolute h-full rounded bg-brand"
                    style={{
                      left: `${(low / procurementScale) * 100}%`,
                      width: `${((high - low) / procurementScale) * 100}%`,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </figure>
        <Table
          caption="Published equipment procurement lead-time ranges"
          headers={[
            'Equipment',
            'Published lead time',
            'Delivery consideration',
          ]}
          rows={Object.entries(equipment).map(([id, label]) => {
            const p = parameter(`procurement_${id}`);
            return [
              label,
              p && Array.isArray(p.value)
                ? `${p.value.join('–')} weeks`
                : 'Not published',
              (guidance.procurementConsiderations as Record<string, string>)[
                label
              ],
            ];
          })}
        />
      </Section>
      <Section
        id="alberta-delivery"
        title="Potential schedule and cost impacts"
        tag="Analytical pathways · not quantified effects"
        note={
          <>
            <Source href="https://www.dpr.com/media/blog/supply-chain-insights-shaping-tomorrows-data-centers">
              DPR supply-chain insights
            </Source>
            {procurement && (
              <>
                {' '}
                ·{' '}
                <Source href={procurement.url}>
                  SourceBlue equipment benchmarks
                </Source>
              </>
            )}
            . Delay depends on critical-path float and resequencing. Cost
            exposure depends on procurement timing and contract terms. No
            numerical Alberta delay or cost premium is inferred.
          </>
        }
      >
        <Table
          caption="Construction pressure schedule and cost pathways"
          headers={guidance.pathways.headers}
          rows={guidance.pathways.rows}
        />
      </Section>
      <Section
        id="alberta-mitigation"
        title="Mitigation and delivery priorities"
        tag="Recommendations · project-specific assessment"
        note={
          <>
            <Source href="https://www.dpr.com/construction/expertise/supply-chain-management">
              DPR supply-chain management
            </Source>
            {buildforce && (
              <>
                {' '}
                ·{' '}
                <Source href={buildforce.url}>
                  BuildForce Alberta outlook
                </Source>
              </>
            )}
            . Recommendations are applications to Alberta, without assumed
            savings or schedule recovery.
          </>
        }
      >
        <Table
          caption="Construction mitigation strategies and trade-offs"
          headers={guidance.mitigations.headers}
          rows={guidance.mitigations.rows}
        />
        <div className="grid gap-3 sm:grid-cols-2">
          {guidance.priorities.map(([title, description]) => (
            <article
              className="rounded-md border border-line bg-workspace p-4"
              key={title}
            >
              <h3 className="font-semibold text-brand">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-subtle">
                {description}
              </p>
            </article>
          ))}
        </div>
      </Section>
      <details className="rounded-lg border border-line bg-surface p-5">
        <summary className="cursor-pointer font-semibold text-ink">
          Definitions, calculations and evidence coverage
        </summary>
        <div className="mt-4 space-y-3 text-sm leading-6 text-subtle">
          <p>
            Reported investment = sum of non-missing core project costs.
            Missing-cost and missing-year counts = all core records minus
            records with that reported field. Known schedule overlap = sum of
            category overlap counts for the published window.
          </p>
          <p>
            Potential recruitment shortfall = max(0, published recruitment
            requirement − published first-time entrants). Year-over-year price
            change = (current index ÷ same-quarter prior-year index − 1) × 100;
            the table uses the published research calculation, rounded to two
            decimals.
          </p>
          <p>
            Available Alberta crew hours, supplier spare throughput, material
            quantities and causal delay/cost estimates remain unmeasured. The
            Demand model contains separate conditional calculations and does not
            change this evidence overview.
          </p>
          <p>
            <Source href="/data/construction/manifest.json">
              Evidence manifest
            </Source>{' '}
            ·{' '}
            <Source href="/data/construction/briefing.json">
              Underlying Alberta observations
            </Source>{' '}
            ·{' '}
            <Source href="/data/construction/benchmarks.json">
              Benchmark register
            </Source>
          </p>
        </div>
      </details>
    </div>
  );
}
