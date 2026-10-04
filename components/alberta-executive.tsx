import Link from 'next/link';
import { WorkspaceScrollRegion } from '@/components/workspace-scroll-region';
import baseline from '@/data/governance/alberta-comparison-baseline.json';
import register from '@/data/governance/alberta-delivery-register.json';
import { evidenceChanges } from '@/lib/alberta-delivery.mjs';
import { summarizeAlbertaProjects } from '@/lib/alberta-evidence-summary.mjs';
import {
  constructionFreshness,
  type ConstructionData,
} from '@/lib/construction-snapshot';

export function AlbertaExecutive({ data }: { data: ConstructionData }) {
  const summary = summarizeAlbertaProjects(data.projects);
  const changes = evidenceChanges(baseline.data, data);
  const due = constructionFreshness(data).filter((s) =>
    ['Last check failed', 'Review due', 'Check overdue'].includes(s.status),
  );
  const years = [
    ...new Set(data.projects.flatMap((p) => (p.end === null ? [] : [p.end]))),
  ].sort((a, b) => a - b);
  const regions = [...new Set(data.projects.map((p) => p.region))];
  return (
    <section className="space-y-6" aria-label="Alberta executive overview">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          [
            'Pipeline records',
            String(data.projects.length),
            'Phases and programmes; not unique campuses',
          ],
          [
            'Reported investment',
            summary.costTotal === null
              ? 'Not published'
              : `$${(summary.costTotal / 1e9).toFixed(1)}B`,
            `${summary.costed.length} costed records · scope varies`,
          ],
          [
            'Completion coverage',
            `${summary.scheduled.length} / ${data.projects.length}`,
            'Reported years; not committed opening dates',
          ],
          [
            'Source attention',
            String(due.length),
            'Overdue checks, failed checks or reviews due',
          ],
        ].map(([label, value, note]) => (
          <div
            className="rounded-lg border border-line bg-surface p-5"
            key={label}
          >
            <p className="text-sm text-subtle">{label}</p>
            <p className="my-2 text-3xl font-semibold text-brand">{value}</p>
            <p className="text-xs text-subtle">{note}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <section className="rounded-lg border border-line bg-surface p-6">
          <h2 className="text-xl font-semibold">What changed</h2>
          <p className="mt-2 text-sm text-subtle">
            Compared with the reviewed evidence baseline dated{' '}
            {baseline.data.manifest.asOf}. Publication dates do not imply new
            observations.
          </p>
          {changes.length ? (
            <ul className="mt-4 space-y-3">
              {changes.map((c, i) => (
                <li key={i}>
                  <strong>
                    {c.kind}: {c.name}
                  </strong>
                  <p className="text-sm text-subtle">{c.detail}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 rounded-md bg-workspace p-4">
              No evidence changes relative to this baseline.
            </p>
          )}
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-brand">
              Source checks requiring attention ({due.length})
            </summary>
            {due.length ? (
              due.map((s) => (
                <p className="mt-2 text-sm" key={s.id}>
                  {s.label ?? s.id}: {s.status} · due {s.nextCheckDue}
                </p>
              ))
            ) : (
              <p className="mt-2 text-sm">
                No checks or reviews currently due.
              </p>
            )}
          </details>
        </section>
        <section className="rounded-lg border border-line bg-surface p-6">
          <h2 className="text-xl font-semibold">
            Decisions requiring evidence
          </h2>
          <ol className="mt-4 space-y-4 text-sm">
            <li>
              <strong>1. Establish the committed pipeline.</strong> Verify
              funding, permits and utility milestones before treating
              announcements as construction starts.
            </li>
            <li>
              <strong>2. Secure specialist resources.</strong>{' '}
              {register.capacity.length} reviewed contractor capacity records
              and {register.suppliers.length} supplier confirmations are
              available.
            </li>
            <li>
              <strong>3. Test project exposure.</strong> Compare package timing
              and regional resources before assigning cost or delay effects.
            </li>
          </ol>
          <div className="mt-5 flex flex-wrap gap-4 text-sm font-semibold text-brand">
            <Link href="/delivery">Open delivery decisions →</Link>
            <Link href="/project-scenario?view=assessment">
              Assess my project →
            </Link>
          </div>
        </section>
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <section className="rounded-lg border border-line bg-surface p-6">
          <h2 className="text-xl font-semibold">
            Reported completion timeline
          </h2>
          <p className="my-3 text-sm text-subtle">
            Records by completion year; {summary.missingCompletionYears} undated
            records are excluded. This is not a construction activity forecast.
          </p>
          {years.map((year) => {
            const count = data.projects.filter((p) => p.end === year).length;
            return (
              <div
                key={year}
                className="my-4 grid grid-cols-[3rem_1fr_2rem] items-center gap-3"
              >
                <span>{year}</span>
                <div className="h-5 rounded bg-workspace">
                  <div
                    className="h-full rounded bg-brand"
                    style={{
                      width: `${(100 * count) / Math.max(1, summary.scheduled.length)}%`,
                    }}
                  />
                </div>
                <span>{count}</span>
              </div>
            );
          })}
        </section>
        <section className="rounded-lg border border-line bg-surface p-6">
          <h2 className="text-xl font-semibold">Regional footprint</h2>
          <p className="my-3 text-sm text-subtle">
            Reported municipalities, with schedule coverage. Geography alone
            does not demonstrate shared crews.
          </p>
          <WorkspaceScrollRegion
            label="Regional footprint table"
            className="max-h-72 overflow-auto focus-visible:outline-2 focus-visible:outline-brand"
          >
            <table className="w-full text-left text-sm">
              <caption className="sr-only">
                Municipality and pipeline coverage
              </caption>
              <thead>
                <tr>
                  <th>Municipality</th>
                  <th>Records</th>
                  <th>Dated</th>
                </tr>
              </thead>
              <tbody>
                {regions.map((region) => {
                  const ps = data.projects.filter((p) => p.region === region);
                  return (
                    <tr className="border-t border-line" key={region}>
                      <th className="py-2 font-normal">
                        {region || 'Not published'}
                      </th>
                      <td>{ps.length}</td>
                      <td>{ps.filter((p) => p.end !== null).length}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </WorkspaceScrollRegion>
        </section>
      </div>
    </section>
  );
}
