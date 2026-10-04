'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  buildPilotInput,
  pilotEvidence,
  pilotMonthLabel,
} from '@/lib/alberta-pilot';
import { reverseStress } from '@/lib/pilot-stress';

const controlClass =
  'mt-2 block w-full rounded border border-line bg-surface p-2 text-ink';
const panelClass = 'rounded-lg border border-line bg-surface p-5';

export function AlbertaPilot() {
  const [capacity, setCapacity] = useState<string>('unknown');
  const [privateMultiplier, setPrivateMultiplier] = useState(1);
  const [mobility, setMobility] = useState(0);
  const [policy, setPolicy] = useState<
    'pro-rata' | 'protect-background' | 'prefer-dc'
  >('pro-rata');
  const [dcShiftMonths, setDCShiftMonths] = useState(0);
  const input = buildPilotInput({
    capacity: capacity === 'unknown' ? null : Number(capacity),
    privateMultiplier,
    mobility,
    policy,
    dcShiftMonths,
  });
  const result = reverseStress(input);
  const scenario = result.cases[0];
  const thresholdInput = {
    ...input,
    capacityCandidates: [5, 7.5, 10, 12.5, 15, 20, 25, 100],
    dcReleaseOffsetsMonths: [0, 6, 12, 21],
  };
  const thresholdResult = reverseStress(thresholdInput);
  function exportPilot() {
    const blob = new Blob(
      [
        JSON.stringify(
          {
            evidence: pilotEvidence,
            input,
            result,
            thresholdInput,
            thresholdResult,
          },
          null,
          2,
        ),
      ],
      { type: 'application/json' },
    );
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'alberta-cal3-windsong-pilot.json';
    anchor.click();
    URL.revokeObjectURL(url);
  }
  const completion = (month: number | null) =>
    month === null
      ? 'Unknown or unfinished in horizon'
      : pilotMonthLabel(month);
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6 sm:px-8">
      <Link href="/construction" className="text-brand underline">
        Back to construction workspace
      </Link>
      <section className={panelClass} aria-labelledby="pilot-facts">
        <h2 id="pilot-facts" className="text-lg font-semibold">
          Observed project accounting
        </h2>
        <p className="mt-3 text-sm leading-6">
          CoreWeave has signed for a portion of CAL-3 Phase 1. The operator
          reports a 90 MW full facility with a second-half 2026 launch target.
          The government inventory’s $750 million estimate covers the whole
          facility; Phase 1 expenditure and its AI share are unknown. Regional
          investment exceeding $1 billion is a different scope.
        </p>
        <p className="mt-3 text-sm leading-6">
          CAL-3 utility feeds and emergency standby generators are identifiable
          enabling assets. Their incremental cost, baseline scope and payer
          allocation are unresolved. South Windsong is an awarded P3 school
          project with a fall 2027 opening target. No uncommitted electrical
          scope or pricing basis has been established, so this pilot omits
          dollar impacts.
        </p>
        <p className="mt-3 text-sm leading-6">
          Source receipts and field-level evidence classes are included in the
          JSON export. Capture dates verify what was available; they do not
          establish new project observations or completed milestones.
        </p>
        <p className="mt-3 text-sm leading-6">
          The municipal permit assigns meter fees and conditional extra
          water-service capacity purchases to the Applicant/Owner. It requires
          site water and wastewater ties, but supplies no incremental asset
          budget, ultimate cost shares or Phase 1 allocation. South Windsong’s
          official $64.3 million estimate covers the whole school; its exposed
          electrical scope remains unknown.
        </p>
        <p className="mt-3 text-sm leading-6">
          Job Bank reports approximately 6,290 Calgary installation
          electricians, with 88% in construction. This is employment context,
          with an unspecified stock base year, not available contractor hours.
          Historical shortage assessments and forward outlooks do not establish
          spare crews for these projects.
        </p>
        <ul className="mt-3 space-y-2 text-sm">
          <li>
            <a
              className="text-brand underline"
              href="https://gis.rockyview.ca/planning/PRDP/PRDP20251314_Online_Package.pdf"
            >
              County: CAL-3 service and payment conditions
            </a>
          </li>
          <li>
            <a
              className="text-brand underline"
              href="https://majorprojects.alberta.ca/details/New-K-8-School-in-Windsong-SW-Airdrie/11248"
            >
              Alberta inventory: South Windsong estimated project envelope
            </a>
          </li>
          <li>
            <a
              className="text-brand underline"
              href="https://www.jobbank.gc.ca/marketreport/outlook-occupation/20684/geo25411"
            >
              Job Bank: Calgary electrical employment context
            </a>
          </li>
          <li>
            <a
              className="text-brand underline"
              href="https://www.estruxture.com/press-releases/estruxture-announces-coreweave-as-anchor-tenant-for-cal-3-its-landmark-ai-ready-facility-in-alberta"
            >
              Operator: CoreWeave Phase 1 agreement, May 14, 2026
            </a>
          </li>
          <li>
            <a
              className="text-brand underline"
              href="https://majorprojects.alberta.ca/details/eStruxture-CAL-3-Data-Centre/11416"
            >
              Alberta inventory: whole-facility estimate
            </a>
          </li>
          <li>
            <a
              className="text-brand underline"
              href="https://www.rockyview.ab.ca/download/513802"
            >
              School board: South Windsong award and opening target, June 3,
              2025
            </a>
          </li>
        </ul>
      </section>
      <section className={panelClass} aria-labelledby="pilot-planning">
        <h2 id="pilot-planning" className="text-lg font-semibold">
          Conditional planning demonstration
        </h2>
        <p className="mt-3 text-sm leading-6">
          Assumed shared Rocky View–Airdrie electrical catchment; January 2026
          onward. School work is 100 normalized paid-work units, other private
          work 50, and AI work 100. These are scenario ratios, with no
          conversion to actual paid hours or workers. The school package window
          and September 2027 protection boundary are planning assumptions within
          the reported project window, not a disclosed subcontract schedule or
          contractual deadline.
        </p>
        <p className="mt-3 text-sm leading-6">
          Capacity means assumed total monthly supply for these packages, not
          measured spare capacity. Mobility adds assumed supply. Staggering
          shifts AI work and can miss its assumed phase target; it is not a
          recommendation to change a documented commitment.
        </p>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <label className="text-sm">
            Monthly shared capacity (normalized units)
            <select
              aria-label="Monthly shared capacity (normalized units)"
              className={controlClass}
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
            >
              {['unknown', '5', '10', '15', '25', '100'].map((v) => (
                <option key={v} value={v}>
                  {v === 'unknown' ? 'Unknown' : v}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Other private demand multiplier
            <select
              aria-label="Other private demand multiplier"
              className={controlClass}
              value={privateMultiplier}
              onChange={(e) => setPrivateMultiplier(Number(e.target.value))}
            >
              {[0, 1, 2].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Mobility supply (normalized units)
            <select
              aria-label="Mobility supply (normalized units)"
              className={controlClass}
              value={mobility}
              onChange={(e) => setMobility(Number(e.target.value))}
            >
              {[0, 5, 10].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Allocation policy
            <select
              aria-label="Allocation policy"
              className={controlClass}
              value={policy}
              onChange={(e) => setPolicy(e.target.value as typeof policy)}
            >
              <option value="pro-rata">Share proportionally</option>
              <option value="protect-background">
                Protect public and existing work
              </option>
              <option value="prefer-dc">Prioritize AI work</option>
            </select>
          </label>
          <label className="text-sm">
            AI work shift (months)
            <select
              aria-label="AI work shift (months)"
              className={controlClass}
              value={dcShiftMonths}
              onChange={(e) => setDCShiftMonths(Number(e.target.value))}
            >
              {[0, 6, 12, 21].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
        </div>
        <div
          data-testid="pilot-result"
          className="mt-5 rounded border border-line bg-workspace p-4"
          aria-live="polite"
        >
          <h3 className="font-semibold">Paired scenario result</h3>
          <p className="mt-2 text-sm">
            Zero incremental delay can still mean both cases miss the planning
            date. Read the protection result alongside the paired comparison.
          </p>
          <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt>School completion without AI work</dt>
              <dd>{completion(scenario.baselineCompletionMonth)}</dd>
            </div>
            <div>
              <dt>School completion with AI work</dt>
              <dd>{completion(scenario.withDCCompletionMonth)}</dd>
            </div>
            <div>
              <dt>Incremental delay (months)</dt>
              <dd>
                {scenario.incrementalDelayMonths ??
                  'Unknown or unresolved horizon tail'}
              </dd>
            </div>
            <div>
              <dt>School protection target met</dt>
              <dd>
                {scenario.protectedTargetMet === null
                  ? 'Unknown capacity'
                  : scenario.protectedTargetMet
                    ? 'Yes, in this scenario'
                    : 'No, in this scenario'}
              </dd>
            </div>
          </dl>
          <p className="mt-3 text-sm">
            Remaining work with AI: {scenario.withDCTailHours} normalized units.
            Tail work is retained, never assumed complete.
          </p>
        </div>
        <button
          type="button"
          onClick={exportPilot}
          className="mt-4 rounded bg-brand px-4 py-2 text-sm font-medium text-white"
        >
          Export pilot JSON
        </button>
        <p className="mt-3 text-sm">
          Assumed mobility adds {mobility} normalized units per month to the
          base supply below.
        </p>
        <h3 className="mt-6 font-semibold">
          Capacity required to protect the planning date
        </h3>
        <p className="mt-2 text-sm leading-6">
          Minimum successful tested base supply before mobility, in normalized
          units per month, under the selected private demand, mobility and
          allocation assumptions. This is a discrete grid threshold, not
          measured shortage or a continuous optimum. A shift beyond the assumed
          AI work target is a tradeoff, not a feasible commitment established by
          evidence.
        </p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {thresholdResult.thresholds[0].capacityByAIShift.map((t) => (
            <div
              key={t.dcReleaseOffsetMonths}
              className="rounded border border-line p-3 text-sm"
            >
              <p>AI shift: {t.dcReleaseOffsetMonths} months</p>
              <p className="mt-1 font-semibold">
                {t.minimumTestedCapacityHours === null
                  ? 'Target not met in grid'
                  : `${t.minimumTestedCapacityHours} units/month`}
              </p>
            </div>
          ))}
        </div>
      </section>
      <section className={panelClass} aria-labelledby="pilot-research">
        <h2 id="pilot-research" className="text-lg font-semibold">
          Later causal research
        </h2>
        <p className="mt-3 text-sm leading-6">
          Co-location does not demonstrate shared crews or causation. Actual
          phase hours, procurement dates, contractor capacity, enabling-asset
          allocations and public exposure are needed before calibration. The
          existing AI proxy benchmark is 2.35% worse than its baseline; this
          pilot does not change that result. Independent review remains pending.
        </p>
      </section>
    </div>
  );
}
