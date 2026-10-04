import Link from 'next/link';
import { ResearchShell, PageIntro, SiteFooter } from '@/components/site-shell';
import analog from '@/public/data/alberta-boom-analog.json';
export default function HistoricalAnalogPage() {
  const start = analog.observations[0].value;
  const end = analog.observations.at(-1)!.value;
  const increase = (end / start - 1) * 100;
  return (
    <ResearchShell>
      <PageIntro
        eyebrow="Historical evidence · Alberta"
        title="What happened during Alberta’s previous investment boom?"
        description="A worked comparison of construction prices and labour response during 2005–2008, using contemporaneous public sources."
      />
      <div className="mx-auto max-w-[1440px] space-y-7 px-5 py-8 sm:px-8">
        <section className="space-y-4 rounded-lg border border-line bg-surface p-5">
          <h2 className="text-2xl font-semibold">
            Edmonton institutional construction prices rose about{' '}
            {Math.round(increase)}%
          </h2>
          <p className="text-sm">
            Q2 2005 to Q2 2008, using the same quarter each year. The
            institutional index represents a school building model; it is a
            price benchmark rather than a record of actual public tenders.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="pb-3 text-left text-subtle">
                Observed institutional index · 1997=100
              </caption>
              <thead>
                <tr>
                  <th scope="col">Period</th>
                  <th scope="col">Published index</th>
                  <th scope="col">Change since Q2 2005</th>
                </tr>
              </thead>
              <tbody>
                {analog.observations.map((row) => (
                  <tr className="border-t border-line" key={row.period}>
                    <th scope="row" className="py-3 font-normal">
                      {row.period}
                    </th>
                    <td>{row.value.toFixed(1)}</td>
                    <td
                      aria-label={`${((row.value / start - 1) * 100).toFixed(1)} percent change since Q2 2005`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-14">
                          {((row.value / start - 1) * 100).toFixed(1)}%
                        </span>
                        <span
                          aria-hidden="true"
                          className="h-3 rounded bg-brand"
                          style={{
                            width: `${(row.value / start - 1) * 200}px`,
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-subtle">
            Source:{' '}
            <a className="underline" href={analog.source}>
              Statistics Canada, Table 7-8, Edmonton (2008 vintage)
            </a>
            . Values retain the published index precision.
          </p>
        </section>
        <section className="space-y-3 rounded-lg border border-line bg-surface p-5">
          <h2 className="text-xl font-semibold">
            Worked example: repricing the same scope
          </h2>
          <p>
            A $100M scope priced in Q2 2005 would reprice to approximately{' '}
            <strong>${Math.round((100 * end) / start)}M</strong> in Q2 2008
            under this index.
          </p>
          <p className="text-sm text-subtle">
            $100M × 193.1 ÷ 131.9 ≈ $146M. This is an index calculation, not an
            observed project overrun. It excludes scope changes, financing and
            project-specific procurement choices.
          </p>
        </section>
        <section
          className="grid gap-4 md:grid-cols-3"
          aria-label="Historical context"
        >
          <article className="space-y-3 rounded-lg border border-line bg-surface p-5">
            <h2 className="font-semibold">Investment scale</h2>
            <p>
              In June 2008, the Bank of Canada reported over $150B of oil sands
              investment proposed or under way. This was a multi-year pipeline,
              not annual spending.
            </p>
            <a
              className="text-sm text-brand underline"
              href={analog.context[2].source}
            >
              Bank of Canada, June 2008
            </a>
          </article>
          <article className="space-y-3 rounded-lg border border-line bg-surface p-5">
            <h2 className="font-semibold">Construction prices</h2>
            <p>
              Q2 2007 non-residential prices rose 20.6% year-over-year in
              Calgary and 18.9% in Edmonton. These broad indexes include
              commercial, industrial and institutional models.
            </p>
            <a
              className="text-sm text-brand underline"
              href={analog.context[0].source}
            >
              Statistics Canada, August 2007
            </a>
          </article>
          <article className="space-y-3 rounded-lg border border-line bg-surface p-5">
            <h2 className="font-semibold">Labour response</h2>
            <p>
              The Bank reported Alberta labour shortages and 4.5% average annual
              wage growth in 2003–2007. Migration helped expand supply; the
              review also described contained wage spillovers across sectors.
            </p>
            <a
              className="text-sm text-brand underline"
              href={analog.context[1].source}
            >
              Bank of Canada Review, Autumn 2008, p. 45
            </a>
          </article>
        </section>
        <section className="space-y-3 rounded-lg border border-line bg-surface p-5">
          <h2 className="text-xl font-semibold">
            What this changes in the decision
          </h2>
          <p>
            Large price movements have occurred alongside Alberta investment
            booms. A small default AI increment therefore needs market testing;
            it cannot settle whether future pressure is immaterial.
          </p>
          <p className="text-sm text-subtle">
            Interpretation boundary: this selected episode is a comparison, not
            a statistical base rate or an oil-sands-to-AI multiplier. Commodity
            prices, housing, migration and other investment moved together.
            Today’s trade mix, imported equipment, modular construction and
            available capacity differ. Scenario coefficients remain unchanged.
          </p>
          <details>
            <summary className="cursor-pointer text-brand">
              Evidence needed to calibrate the comparison
            </summary>
            <p className="mt-3 text-sm">
              Link annual realized construction investment to trade hours,
              migration and vacancies; assemble public tender/package prices and
              scope revisions; use comparable regions and control for commodity
              and housing cycles. Test timing and out-of-sample performance
              before translating demand into a public-project premium.
            </p>
          </details>
        </section>
        <div className="flex flex-wrap gap-5 text-sm text-brand">
          <a
            download
            href="/data/alberta-boom-analog.json"
            className="underline"
          >
            Download observations and calculation (.json)
          </a>
          <Link className="underline" href="/project-scenario?view=walkthrough">
            Open the guided scenario
          </Link>
          <Link className="underline" href="/methods#planning-gates">
            See validation gates
          </Link>
        </div>
      </div>
      <SiteFooter />
    </ResearchShell>
  );
}
