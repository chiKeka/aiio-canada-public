'use client';
import { DeliveryReviewEditor } from '@/components/delivery-review-editor';
import { useState } from 'react';
import type { ConstructionData } from '@/lib/construction-snapshot';
import type { DeliveryRegister } from '@/lib/delivery-types';
import {
  procurementDeadline,
  capacityBalance,
} from '@/lib/alberta-delivery.mjs';

const box = 'rounded-lg border border-line bg-surface p-5 space-y-4';
function GridTable({
  headers,
  rows,
}: {
  headers: string[];
  rows: (string | number)[][];
}) {
  return (
    // Keyboard users must be able to scroll the table at narrow viewports.
    // oxlint-disable-next-line jsx-a11y/no-noninteractive-tabindex
    <div className="overflow-x-auto" tabIndex={0}>
      <table className="w-full text-left text-sm">
        <thead>
          <tr>
            {headers.map((h) => (
              <th className="p-2" key={h}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-line">
              {r.map((v, j) => (
                <td key={j} className="p-2 align-top">
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function DeliveryWorkspace({
  projects,
  register,
}: {
  projects: ConstructionData['projects'];
  register: DeliveryRegister;
}) {
  const [region, setRegion] = useState('All');
  const [required, setRequired] = useState('');
  const [lead, setLead] = useState('');
  const [freight, setFreight] = useState('');
  const [testing, setTesting] = useState('');
  const selected = projects.filter(
    (p) => region === 'All' || p.region === region,
  );
  const packages = register.packages.filter(
    (p) => region === 'All' || p.region === region,
  );
  const capacity = register.capacity.filter(
    (p) => region === 'All' || p.region === region,
  );
  const suppliers = register.suppliers.filter(
    (p) => region === 'All' || p.region === region,
  );
  const deadline = [lead, freight, testing].every((v) => v.trim() !== '')
    ? procurementDeadline(
        required,
        Number(lead),
        Number(freight),
        Number(testing),
      )
    : null;
  const quarters = [
    ...new Set(
      packages.flatMap((p) => {
        const result = [];
        let y = Number(p.start.slice(0, 4)),
          q = Number(p.start.at(-1));
        while (`${y}-Q${q}` <= p.end && result.length < 80) {
          result.push(`${y}-Q${q}`);
          if (++q === 5) {
            q = 1;
            y++;
          }
        }
        return result;
      }),
    ),
  ].sort();
  const download = () => {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(register, null, 2)], {
        type: 'application/json',
      }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = 'alberta-delivery-register.json';
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <label className="text-sm">
          Municipality / region
          <select
            className="ml-3 rounded border border-line bg-surface p-2"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            <option>All</option>
            {[
              ...new Set([
                ...projects.map((p) => p.region),
                ...register.packages.map((p) => p.region),
                ...register.capacity.map((p) => p.region),
                ...register.suppliers.map((p) => p.region),
              ]),
            ]
              .sort()
              .map((r) => (
                <option key={r}>{r}</option>
              ))}
          </select>
        </label>
        <button
          className="rounded border border-line px-4 py-2 text-sm"
          onClick={download}
        >
          Export reviewed delivery register
        </button>
      </div>
      <section className={box}>
        <h2 className="text-xl font-semibold">Pipeline certainty</h2>
        <p className="text-sm text-subtle">
          Reported stage is not verification of financing, permits or utility
          readiness. “Unverified” is a coverage gap, not a negative finding.
          Campus totals remain withheld until phase relationships are verified.
        </p>
        <GridTable
          headers={[
            'Project / record',
            'Reported stage',
            'Record type / campus',
            'Construction-only cost',
            'Funding',
            'Permit',
            'Utility',
            'Construction milestone',
          ]}
          rows={selected.map((p) => {
            const r = register.projects.find((r) => r.id === p.id);
            return [
              p.name,
              p.stage,
              `${r?.recordKind ?? 'unverified'} / ${r?.campusId ?? 'unverified'}`,
              r?.constructionCost
                ? `$${(r.constructionCost.value / 1e6).toLocaleString('en-CA')}M CAD`
                : 'Not verified',
              ...['financing', 'permit', 'utility', 'construction'].map(
                (k) => r?.milestones[k]?.status ?? 'Unverified',
              ),
            ];
          })}
        />
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Quarterly package overlap</h2>
        <p className="text-sm text-subtle">
          Packages are classified as civil, electrical, mechanical, utility or
          commissioning. Reported and inferred schedules are counted separately;
          no package dates are inferred from an opening year.
        </p>
        {packages.length ? (
          <GridTable
            headers={[
              'Quarter',
              'Trade',
              'Reported DC packages',
              'Reported infrastructure packages',
              'Inferred packages',
            ]}
            rows={quarters.flatMap((q) =>
              [
                'civil',
                'electrical',
                'mechanical',
                'utility',
                'commissioning',
              ].map((trade) => [
                q,
                trade,
                packages.filter(
                  (p) =>
                    p.trade === trade &&
                    p.start <= q &&
                    p.end >= q &&
                    p.basis === 'reported' &&
                    p.projectKind === 'data_centre',
                ).length,
                packages.filter(
                  (p) =>
                    p.trade === trade &&
                    p.start <= q &&
                    p.end >= q &&
                    p.basis === 'reported' &&
                    p.projectKind === 'infrastructure',
                ).length,
                packages.filter(
                  (p) =>
                    p.trade === trade &&
                    p.start <= q &&
                    p.end >= q &&
                    p.basis === 'inferred',
                ).length,
              ]),
            )}
          />
        ) : (
          <p className="rounded bg-workspace p-4">
            Package-level overlap is not yet quantifiable. Add sourced start/end
            quarters and regional trade packages for both data centres and
            competing projects.
          </p>
        )}
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">
          Contractor capacity and labour availability
        </h2>
        <p className="text-sm text-subtle">
          Available paid hours = max(0, deployable paid hours − committed paid
          hours), within the same contractor, trade, region and quarter.
          Employment stocks and vacancies are not substituted for capacity.
        </p>
        {capacity.length ? (
          <GridTable
            headers={[
              'Contractor',
              'Region / trade',
              'Quarter',
              'Deployable hours',
              'Committed',
              'Available',
              'Verified',
            ]}
            rows={capacity.map((c) => [
              c.contractor,
              `${c.region} / ${c.trade}`,
              c.quarter,
              c.paidHours,
              c.committedHours,
              capacityBalance(c.paidHours, c.committedHours, 0)?.available ??
                'Unknown',
              c.verifiedOn,
            ])}
          />
        ) : (
          <p className="rounded bg-workspace p-4">
            No reviewed contractor capacity records. Required: contractor,
            trade, region, quarter, deployable hours, backlog commitments,
            source and verification date. Mobilization and qualification
            constraints must be documented with the source.
          </p>
        )}
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Supplier commitments</h2>
        {suppliers.length ? (
          <GridTable
            headers={[
              'Supplier / equipment',
              'Specification',
              'Region / slot',
              'Required on site',
              'Latest release',
              'Verified',
            ]}
            rows={suppliers.map((s) => [
              `${s.supplier} / ${s.equipment}`,
              s.specification,
              `${s.region} / ${s.slotStatus}`,
              s.requiredOnSite,
              procurementDeadline(
                s.requiredOnSite,
                s.leadWeeks,
                s.freightWeeks,
                s.testingWeeks,
              ) ?? 'Invalid inputs',
              s.verifiedOn,
            ])}
          />
        ) : (
          <p className="rounded bg-workspace p-4">
            No reviewed Alberta supplier confirmations. Capture equipment
            specifications, quote and verification dates, manufacturing slots,
            shipping, testing and required-on-site dates. External benchmarks
            remain available in Construction demand.
          </p>
        )}
        <h3 className="font-semibold">Procurement release planner</h3>
        <p className="text-sm text-subtle">
          Conditional planning only. Latest release = required-on-site date −
          manufacturing, freight and testing durations. Excludes design
          approvals and procurement administration; allow for these separately.
          This does not calculate project delay.
        </p>
        <div className="grid gap-3 sm:grid-cols-4">
          {[
            ['Required on site', required, setRequired, 'date'],
            ['Manufacturing · weeks', lead, setLead, 'number'],
            ['Freight · weeks', freight, setFreight, 'number'],
            ['Testing · weeks', testing, setTesting, 'number'],
          ].map(([label, value, set, type]) => (
            <label key={String(label)} className="text-sm">
              {String(label)}
              <input
                className="mt-1 w-full rounded border border-line bg-surface p-2"
                type={String(type)}
                min="0"
                value={String(value)}
                onChange={(e) => (set as (v: string) => void)(e.target.value)}
              />
            </label>
          ))}
        </div>
        <output aria-live="polite" className="font-semibold text-brand">
          {deadline
            ? `Latest manufacturing release: ${deadline}`
            : 'Enter all dates and durations; use explicit zero where a duration does not apply.'}
        </output>
      </section>
      <section className={box}>
        <h2 className="text-xl font-semibold">Action register</h2>
        <p className="text-sm text-subtle">
          Reviewed records · {register.asOf}. Unassigned owners and dates
          require a project decision. No savings or schedule recovery are
          credited without supporting evidence.
        </p>
        <GridTable
          headers={[
            'Action',
            'Project',
            'Owner',
            'Due',
            'Status',
            'Evidence / benefit',
          ]}
          rows={register.actions.map((a) => [
            a.title,
            projects.find((p) => p.id === a.projectId)?.name ?? 'Portfolio',
            a.owner ?? 'Unassigned',
            a.due ?? 'Not set',
            a.status,
            a.evidence
              ? `${a.evidence} · ${a.benefit ? `${a.benefit.value} (${a.benefit.basis})` : 'No benefit credited'}`
              : 'No supporting evidence; no benefit credited',
          ])}
        />
        <details>
          <summary className="cursor-pointer text-brand">
            How records are updated
          </summary>
          <p className="mt-3 text-sm">
            Records are versioned with the evidence review process. Export the
            register, add sourced observations or agreed action owners and
            dates, and submit it for review. The published dashboard changes
            after validation and approval; this page does not claim to save
            shared edits.
          </p>
        </details>
      </section>
      <details className={box}>
        <summary className="cursor-pointer font-semibold">
          Delivery record provenance
        </summary>
        <p className="text-sm text-subtle">
          Verification dates describe reviewed records, not guarantees of
          current availability. Reconfirm contractor hours and supplier slots
          before commitment.
        </p>
        {[
          ...register.projects.flatMap((p) => [
            ...Object.entries(p.milestones).flatMap(([kind, m]) =>
              m ? [{ label: `${p.id} · ${kind}`, ...m }] : [],
            ),
            ...(p.recordEvidence
              ? [{ label: `${p.id} · classification`, ...p.recordEvidence }]
              : []),
          ]),
          ...packages.map((p) => ({
            label: `${p.projectName} · ${p.trade}`,
            source: p.source,
            verifiedOn: p.verifiedOn,
          })),
          ...capacity.map((c) => ({
            label: `${c.contractor} · ${c.quarter}`,
            source: c.source,
            verifiedOn: c.verifiedOn,
          })),
          ...suppliers.map((s) => ({
            label: `${s.supplier} · ${s.equipment}`,
            source: s.source,
            verifiedOn: s.verifiedOn,
          })),
        ].map((s, i) => (
          <p key={i} className="text-sm">
            <a
              href={s.source}
              target="_blank"
              rel="noreferrer"
              className="text-brand underline"
            >
              {s.label}
            </a>{' '}
            · verified {s.verifiedOn}
          </p>
        ))}
        <p className="text-xs text-subtle">
          Unknown fields have no supporting citation and remain unverified.
        </p>
      </details>
      <DeliveryReviewEditor register={register} />
      <section className={box}>
        <h2 className="text-xl font-semibold">Model assurance</h2>
        <GridTable
          headers={['Decision', 'Evidence required', 'Current boundary']}
          rows={[
            [
              'Quantify labour shortage',
              'Regional package demand and available contractor hours',
              'Not established by provincial headcounts',
            ],
            [
              'Quantify materials pressure',
              'Physical quantities, technical eligibility and uncommitted supplier output',
              'Price indices alone are insufficient',
            ],
            [
              'Attribute additional cost to data centres',
              'Calibrated model, counterfactual evidence and independent review',
              'Conditional scenarios only',
            ],
            [
              'Translate lead time into project delay',
              'Required dates, critical-path float and resequencing options',
              'Lead time is not project delay',
            ],
          ]}
        />
      </section>
    </div>
  );
}
