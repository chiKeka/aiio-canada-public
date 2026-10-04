import Link from 'next/link';
import { scenarioMoney } from '@/lib/public-presentation.mjs';
import type {
  buildDecisionOutlook,
  DecisionInputs,
} from '@/lib/decision-outlook';
export function ScenarioInterpretation({
  assessment,
  inputs,
  contingencyPct,
}: {
  assessment: ReturnType<typeof buildDecisionOutlook>;
  inputs: DecisionInputs;
  contingencyPct: number;
}) {
  const cashflow = assessment?.cashflow;
  if (!cashflow || assessment?.isOfficial) return null;
  const share = (cashflow.aiIncrement / inputs.budgetMillions) * 100;
  return (
    <section
      className="mb-5 space-y-3 rounded-lg border border-line bg-surface p-5"
      aria-label="How to interpret this scenario"
    >
      <h2 className="text-lg font-semibold">What this scenario says</h2>
      <p className="text-sm">
        Your inputs generate about {scenarioMoney(cashflow.aiIncrement)} of
        additional spending, or {share.toFixed(1)}% of the base budget. This is
        an assumption-driven result; it does not establish Alberta’s actual AI
        cost impact.
      </p>
      <dl className="grid gap-3 sm:grid-cols-3">
        {[
          ['Baseline escalation', cashflow.baselineEscalation],
          ['Assumed AI increment', cashflow.aiIncrement],
          [
            'Separate contingency',
            (inputs.budgetMillions * contingencyPct) / 100,
          ],
        ].map(([label, value]) => (
          <div key={String(label)}>
            <dt className="text-xs text-subtle">{label}</dt>
            <dd className="text-xl font-semibold">
              {scenarioMoney(Number(value))}
            </dd>
          </div>
        ))}
      </dl>
      <p className="text-sm text-subtle">
        {cashflow.aiIncrement < cashflow.baselineEscalation
          ? 'The increment is smaller than baseline escalation under these inputs. '
          : 'The increment exceeds baseline escalation under these inputs. '}
        Contingency is shown for scale and is excluded from scenario spend; it
        is not evidence that this exposure is covered.
      </p>
      <details className="text-sm">
        <summary className="cursor-pointer text-brand">
          Why this result is assumption-driven
        </summary>
        <p className="mt-2">
          The {inputs.assumptions.peakAiAnnualPctPoints} percentage-point annual
          peak is scaled by local capture ({inputs.assumptions.localCapturePct}
          %), the spending path and a {inputs.assumptions.lagMonths}-month lag,
          then compounded against monthly project spending. Capture is
          normalized to the reference scenario, rather than multiplied as a
          standalone percentage. The ±{inputs.assumptions.uncertaintyPct}% band
          varies the monthly AI increment; it is not a confidence interval and
          does not cover all model uncertainty.
        </p>
      </details>
      <p className="text-xs text-subtle">
        Decision boundary: use this sensitivity to target market testing.
        Forecast authorization remains withheld pending calibration.{' '}
        <Link href="/methods#planning-gates" className="underline">
          Review the validation gates
        </Link>{' '}
        ·{' '}
        <Link href="/historical-analog" className="underline">
          Compare Alberta’s previous investment boom
        </Link>
      </p>
    </section>
  );
}
