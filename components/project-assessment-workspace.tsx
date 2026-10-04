'use client';

import {
  cloneElement,
  useId,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  ProjectAssumptionsDrawer,
  type ProjectConfiguration,
} from '@/components/project-assumptions-drawer';
import { ASSETS, METROS } from '@/lib/decision-analysis';
import { monthNumber } from '@/lib/project-cashflow';
import {
  assessProject,
  type ProjectAssessmentInput,
  type OwnerPackage,
} from '@/lib/project-assessment';
import { dcPhaseCatalogue } from '@/lib/project-assessment-catalogue';

const storageKey = 'aiio-project-owner-draft-v1';
const trades = ['Civil', 'Electrical', 'Mechanical', 'Other'] as const;
const fieldClass =
  'mt-1 w-full rounded-md border border-line bg-surface px-3 py-2 text-ink';
const buttonClass = 'rounded-md border border-line px-4 py-2 text-sm text-ink';
const panelClass = 'rounded-xl border border-line bg-surface p-5 sm:p-6';
type Basis = 'unknown' | 'assumption' | 'evidence';
type PackageDraft = OwnerPackage & {
  basis: Basis;
  source: string;
  material: string;
  equipment: string;
  supplier: string;
  utility: string;
};
type Draft = {
  location: string;
  catchment: string;
  confirmedPool: boolean;
  contract: 'unknown' | 'fixed' | 'variable';
  packages: PackageDraft[];
  dcId: string;
  dcCatchment: string;
  dcTrade: (typeof trades)[number];
  dcHours: number | null;
  dcRelease: number | null;
  dcFinish: number | null;
  dcBasis: Basis;
  dcSource: string;
  capacity: Record<(typeof trades)[number], number | null>;
  privateHours: number | null;
  thresholdCandidates: string;
  floatMonths: number;
  overhead: number | null;
  annualRate: number | null;
  stagger: number;
  early: number;
  addedCapacity: number;
  storage: boolean;
};
function freshDraft(): Draft {
  return {
    location: '',
    catchment: '',
    confirmedPool: false,
    contract: 'unknown',
    packages: trades.map((trade) => ({
      id: trade.toLowerCase(),
      name: `${trade} package`,
      scope: trade,
      trade,
      catchment: null,
      hours: null,
      releaseMonth: null,
      finishMonth: null,
      predecessors: [],
      budgetCAD: null,
      uncommittedCAD: null,
      commitment: 'unknown',
      cashMonth: null,
      basis: 'unknown',
      source: '',
      material: '',
      equipment: '',
      supplier: '',
      utility: '',
    })),
    dcId: '',
    dcCatchment: '',
    dcTrade: 'Electrical',
    dcHours: null,
    dcRelease: null,
    dcFinish: null,
    dcBasis: 'unknown',
    dcSource: '',
    capacity: { Civil: null, Electrical: null, Mechanical: null, Other: null },
    privateHours: null,
    thresholdCandidates: '',
    floatMonths: 0,
    overhead: null,
    annualRate: null,
    stagger: 0,
    early: 0,
    addedCapacity: 0,
    storage: false,
  };
}
type SavedDraft = {
  version: 1;
  configuration: ProjectConfiguration;
  draft: Draft;
};
const memoryDraft = { current: null as SavedDraft | null };
function validShape(template: unknown, candidate: unknown): boolean {
  if (template === null)
    return (
      candidate === null ||
      (typeof candidate === 'number' &&
        Number.isFinite(candidate) &&
        candidate >= 0)
    );
  if (typeof template === 'number')
    return (
      typeof candidate === 'number' &&
      Number.isFinite(candidate) &&
      candidate >= 0
    );
  if (typeof template === 'string' || typeof template === 'boolean')
    return typeof candidate === typeof template;
  if (Array.isArray(template))
    return (
      Array.isArray(candidate) &&
      (template.length
        ? candidate.length === template.length &&
          candidate.every((item, i) => validShape(template[i], item))
        : candidate.every((item) => typeof item === 'string'))
    );
  if (typeof template === 'object' && template !== null) {
    if (
      typeof candidate !== 'object' ||
      candidate === null ||
      Array.isArray(candidate)
    )
      return false;
    return Object.entries(template).every(([key, value]) =>
      validShape(value, (candidate as Record<string, unknown>)[key]),
    );
  }
  return false;
}
function validSaved(
  value: unknown,
  configuration: ProjectConfiguration,
): value is SavedDraft {
  if (typeof value !== 'object' || value === null) return false;
  const saved = value as Record<string, unknown>;
  if (
    saved.version !== 1 ||
    !validShape(freshDraft(), saved.draft) ||
    !validShape(configuration, saved.configuration)
  )
    return false;
  const d = saved.draft as Draft;
  const c = saved.configuration as ProjectConfiguration;
  return (
    Object.hasOwn(ASSETS, c.assetId) &&
    Object.hasOwn(METROS, c.metroId) &&
    c.budgetMillions > 0 &&
    Number.isInteger(c.startYear) &&
    Number.isInteger(c.duration) &&
    c.duration >= 2 &&
    c.duration <= 10 &&
    monthNumber(c.priceBasis) !== null &&
    ['unknown', 'fixed', 'variable'].includes(d.contract) &&
    trades.includes(d.dcTrade) &&
    ['unknown', 'assumption', 'evidence'].includes(d.dcBasis) &&
    d.packages.every(
      (item, i) =>
        item.id === trades[i].toLowerCase() &&
        item.scope === trades[i] &&
        (item.trade === null ||
          trades.includes(item.trade as (typeof trades)[number])) &&
        ['unknown', 'fixed', 'variable'].includes(item.commitment) &&
        ['unknown', 'assumption', 'evidence'].includes(item.basis),
    )
  );
}
function numberOrUnknown(value: string) {
  return value.trim() === '' ? null : Number(value);
}
function monthText(value: number | null) {
  return value === null
    ? ''
    : `${Math.floor(value / 12)}-${String((value % 12) + 1).padStart(2, '0')}`;
}
function displayMonth(value: number | null) {
  return value === null
    ? 'Unknown'
    : new Date(
        Date.UTC(Math.floor(value / 12), value % 12, 1),
      ).toLocaleDateString('en-CA', {
        month: 'short',
        year: 'numeric',
        timeZone: 'UTC',
      });
}
function money(value: number | null) {
  return value === null
    ? 'Not quantified'
    : new Intl.NumberFormat('en-CA', {
        style: 'currency',
        currency: 'CAD',
        maximumFractionDigits: 0,
      }).format(value);
}
function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactElement<{ id?: string }>;
}) {
  const id = useId();
  return (
    <div className="text-sm font-medium text-ink">
      <label className="block" htmlFor={id}>
        {label}
      </label>
      {cloneElement(children, { id })}
    </div>
  );
}
function Numeric({
  label,
  value,
  onChange,
  step = 'any',
  suffix = '',
}: {
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
  step?: string;
  suffix?: string;
}) {
  return (
    <Field label={label}>
      <input
        className={fieldClass}
        type="number"
        min="0"
        step={step}
        value={value ?? ''}
        placeholder={`Unknown${suffix}`}
        onChange={(event) => onChange(numberOrUnknown(event.target.value))}
      />
    </Field>
  );
}

export function ProjectAssessmentWorkspace({
  configuration,
  onApply,
  readiness,
}: {
  configuration: ProjectConfiguration;
  onApply: (next: ProjectConfiguration) => void;
  readiness?: {
    currentSources: number;
    totalSources: number;
    proxyPlanning: unknown;
    releaseVintage?: string;
    freshnessAsOf?: string;
  };
}) {
  const [draft, setDraft] = useState<Draft>(freshDraft);
  const [storageMessage, setStorageMessage] = useState('');
  const [error, setError] = useState('');
  const restored = useRef(false);
  useEffect(() => {
    if (restored.current) return;
    restored.current = true;
    try {
      const raw = localStorage.getItem(storageKey);
      const saved: unknown =
        memoryDraft.current ?? (raw ? JSON.parse(raw) : null);
      if (!saved) return;
      if (!validSaved(saved, configuration)) {
        queueMicrotask(() =>
          setStorageMessage(
            'Saved draft has an unsupported shape. Current project inputs are retained.',
          ),
        );
        return;
      }
      queueMicrotask(() => {
        setDraft(saved.draft);
        onApply(saved.configuration);
        setStorageMessage(
          saved.draft.storage
            ? 'Restored your draft saved in this browser.'
            : 'Restored this visit’s draft after navigation.',
        );
      });
    } catch {
      queueMicrotask(() =>
        setStorageMessage(
          'Saved draft could not be read. Your current inputs remain available.',
        ),
      );
    }
  }, [onApply, configuration]);
  useEffect(() => {
    if (!restored.current) return;
    memoryDraft.current = { version: 1, configuration, draft };
    if (!draft.storage) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(memoryDraft.current));
    } catch {
      /* Export remains available when browser storage is unavailable. */
    }
  }, [configuration, draft]);
  const change = <K extends keyof Draft>(key: K, value: Draft[K]) =>
    setDraft((current) => ({ ...current, [key]: value }));
  const packageChange = <K extends keyof PackageDraft>(
    id: string,
    key: K,
    value: PackageDraft[K],
  ) =>
    setDraft((current) => ({
      ...current,
      packages: current.packages.map((item) =>
        item.id === id
          ? {
              ...item,
              [key]: value,
              ...(key === 'commitment' && value === 'fixed'
                ? { uncommittedCAD: 0 }
                : {}),
            }
          : item,
      ),
    }));
  const candidate = dcPhaseCatalogue.find((phase) => phase.id === draft.dcId);
  const input = useMemo<ProjectAssessmentInput>(() => {
    const start = configuration.startYear * 12;
    const end = start + configuration.duration * 12 - 1;
    const eligibleCatchment =
      draft.confirmedPool && configuration.metroId !== 'OTHER'
        ? draft.catchment.trim() || null
        : null;
    const packages = draft.packages.map((item) => ({
      ...item,
      catchment: eligibleCatchment,
    }));
    const resource = `${draft.catchment.trim()}:${draft.dcTrade}`;
    const capacity = Object.fromEntries(
      trades.map((trade) => [
        `${draft.catchment.trim()}:${trade}`,
        draft.capacity[trade],
      ]),
    );
    return {
      project: {
        id: 'owner-project',
        name: configuration.projectName,
        province:
          configuration.metroId === 'OTHER'
            ? 'Unknown / unsupported'
            : 'Alberta',
        assetType: configuration.assetId,
        supportedContext:
          ['school', 'hospital', 'government'].includes(
            configuration.assetId,
          ) && configuration.metroId !== 'OTHER',
        catchment: eligibleCatchment,
        budgetCAD: configuration.budgetMillions * 1e6,
        plannedFinishMonth: end,
        floatMonths: draft.floatMonths,
        overheadCADPerMonth: draft.overhead,
        priceBasisMonth: monthNumber(configuration.priceBasis) ?? start,
      },
      packages,
      dcPackages: draft.dcId
        ? [
            {
              id: draft.dcId,
              name: candidate?.name ?? draft.dcId,
              trade: draft.dcTrade,
              catchment: draft.confirmedPool
                ? draft.dcCatchment.trim() || null
                : null,
              hours: draft.dcHours,
              releaseMonth: draft.dcRelease,
              finishMonth: draft.dcFinish,
              predecessors: [],
            },
          ]
        : [],
      backgroundPackages:
        draft.privateHours === null
          ? []
          : [
              {
                id: 'other-private',
                name: 'Other private demand assumption',
                trade: draft.dcTrade,
                catchment: draft.catchment.trim() || null,
                hours: draft.privateHours,
                releaseMonth: start,
                finishMonth: end,
                predecessors: [],
              },
            ],
      capacity,
      startMonth: start,
      endMonth: end + 60,
      policy: 'pro-rata',
      annualEscalation:
        draft.annualRate === null ? null : draft.annualRate / 100,
      mitigation: {
        dcShiftMonths: draft.stagger,
        additionalCapacity: { [resource]: draft.addedCapacity },
        earlyProcurementMonths: draft.early,
        procurementPackageIds: packages
          .filter((item) => item.commitment === 'variable')
          .map((item) => item.id),
      },
      capacityThresholds: draft.thresholdCandidates.trim()
        ? [
            {
              resourceKey: resource,
              candidates: draft.thresholdCandidates
                .split(',')
                .map((value) => Number(value.trim()))
                .slice(0, 20),
            },
          ]
        : [],
      assumptions: [
        `Location description: ${draft.location || 'unknown'}. Proximity alone does not establish competition.`,
        `Project contract context: ${draft.contract}; package commitments govern exposure.`,
        'Budgets never supply labour hours or material quantities. Capacity and package work are user inputs, not measured workforce shortages.',
        `DC package basis: ${draft.dcBasis}; source: ${draft.dcSource || 'not supplied'}.`,
        ...packages.map(
          (item) =>
            `${item.name}: ${item.basis}; source ${item.source || 'not supplied'}. Material ${item.material || 'unknown'}; equipment ${item.equipment || 'unknown'}; supplier ${item.supplier || 'unknown'}; utility ${item.utility || 'unknown'}.`,
        ),
      ],
      qualitativeLinks: packages.flatMap((item) => [
        ...(item.supplier
          ? [
              {
                channel: 'supplier' as const,
                label: `${item.name}: ${item.supplier}`,
                source: item.source || null,
              },
            ]
          : []),
        ...(item.utility
          ? [
              {
                channel: 'utility' as const,
                label: `${item.name}: ${item.utility}`,
                source: item.source || null,
              },
            ]
          : []),
      ]),
    };
  }, [configuration, draft, candidate]);
  const evaluated = useMemo(() => {
    try {
      return { result: assessProject(input), error: '' };
    } catch (cause) {
      return {
        result: null,
        error:
          cause instanceof Error
            ? cause.message
            : 'Inputs could not be assessed.',
      };
    }
  }, [input]);
  const result = evaluated.result;
  const exposed = draft.packages.reduce(
    (sum, item) =>
      sum + (item.commitment === 'variable' ? (item.uncommittedCAD ?? 0) : 0),
    0,
  );
  const knownExposure = draft.packages.some(
    (item) => item.uncommittedCAD !== null && item.commitment === 'variable',
  );
  const record = (createdAt?: string) => ({
    schemaVersion: 'project-owner-assessment-v1',
    ...(createdAt ? { createdAt } : {}),
    configuration,
    draft,
    inputs: input,
    result,
    catalogueCandidate: candidate ?? null,
    readiness: readiness ?? null,
    qualification:
      'Conditional planning scenario; unsupported inputs remain unknown. No generic AI premium or causal cost attribution.',
  });
  const exportJSON = () => {
    try {
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(record(new Date().toISOString()), null, 2)], {
          type: 'application/json',
        }),
      );
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'aiio-project-assessment.json';
      anchor.click();
      URL.revokeObjectURL(url);
      setError('');
    } catch {
      setError('Export failed. Your inputs remain available; please retry.');
    }
  };
  const loadExample = () => {
    const example = freshDraft();
    example.location = 'Hypothetical Airdrie school';
    example.catchment = 'hypothetical-shared-electrical-pool';
    example.confirmedPool = true;
    example.contract = 'variable';
    example.packages = example.packages.map((item) => ({
      ...item,
      basis: 'assumption',
      source: 'Hypothetical browser fixture; not a real project quantity',
      hours: item.scope === 'Electrical' ? 100 : 0,
      budgetCAD: item.scope === 'Electrical' ? 8e6 : null,
      uncommittedCAD: item.scope === 'Electrical' ? 8e6 : 0,
      commitment: item.scope === 'Electrical' ? 'variable' : 'fixed',
      releaseMonth: 2026 * 12,
      finishMonth: 2027 * 12 + 8,
      cashMonth: 2026 * 12,
    }));
    example.dcId =
      dcPhaseCatalogue.find((phase) => phase.id === 'CAL3_PHASE1')?.id ??
      dcPhaseCatalogue[0]?.id ??
      '';
    example.dcCatchment = example.catchment;
    example.dcHours = 100;
    example.dcRelease = 2026 * 12;
    example.dcFinish = 2026 * 12 + 8;
    example.dcBasis = 'assumption';
    example.dcSource =
      'Hypothetical 100 paid hours; no measured CAL-3 phase demand';
    example.capacity.Electrical = 10;
    example.privateHours = 50;
    example.annualRate = 5;
    example.overhead = 0;
    setDraft(example);
    onApply({
      ...configuration,
      projectName: 'Hypothetical $50M school',
      assetId: 'school',
      metroId: 'CMA_825',
      budgetMillions: 50,
      startYear: 2026,
      duration: 2,
      priceBasis: '2026-01',
    });
    setStorageMessage(
      'Loaded a hypothetical school scenario. All work quantities, capacity and exposure are assumptions.',
    );
  };
  const reset = () => {
    memoryDraft.current = null;
    setDraft(freshDraft());
    localStorage.removeItem(storageKey);
    setStorageMessage('Package draft reset. Your project context is retained.');
  };
  return (
    <div className="space-y-6" data-testid="project-assessment-workspace">
      <section className={panelClass} aria-labelledby="owner-project-heading">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm text-subtle">Assess my project</p>
            <h2 id="owner-project-heading" className="text-2xl font-semibold">
              Project inputs
            </h2>
          </div>
          <div className="print:hidden">
            <ProjectAssumptionsDrawer
              value={configuration}
              onApply={onApply}
              mode="assessment"
            />
          </div>
        </div>
        <p className="mt-3 text-subtle">
          {ASSETS[configuration.assetId].label} ·{' '}
          {METROS[configuration.metroId]} ·{' '}
          {money(configuration.budgetMillions * 1e6)} base budget ·{' '}
          {configuration.startYear} start · {configuration.duration} years ·{' '}
          {configuration.approvalStage}
        </p>
        <button
          type="button"
          className={`${buttonClass} mt-4 print:hidden`}
          onClick={loadExample}
        >
          Load hypothetical $50M school example
        </button>
        <p className="mt-3 max-w-3xl leading-7">
          Replace the sample inputs with your project. Add supported package
          quantities below.
        </p>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Field label="Project location">
            <input
              className={fieldClass}
              value={draft.location}
              placeholder="City, site or unknown"
              onChange={(event) => change('location', event.target.value)}
            />
          </Field>
          <Field label="Project contract status">
            <select
              className={fieldClass}
              value={draft.contract}
              onChange={(event) =>
                change('contract', event.target.value as Draft['contract'])
              }
            >
              <option value="unknown">Unknown</option>
              <option value="fixed">Fixed commitments</option>
              <option value="variable">Uncommitted or variable</option>
            </select>
          </Field>
        </div>
      </section>
      <section
        className={panelClass}
        aria-labelledby="owner-result-heading"
        data-testid="project-assessment-result"
      >
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="rounded-full bg-paper px-3 py-1 font-medium">
            {result?.qualified === 'conditional'
              ? 'Conditional scenario'
              : 'Evidence needed'}
          </span>
          <span className="text-subtle">User inputs · not a forecast</span>
        </div>
        <h2 id="owner-result-heading" className="mt-3 text-xl font-semibold">
          {input.project.supportedContext === false
            ? 'Unsupported context · qualitative only'
            : result?.qualified === 'conditional'
              ? 'Cost & schedule comparison'
              : 'AI effect not established'}
        </h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-sm text-subtle">Base budget</dt>
            <dd className="mt-1 text-xl font-semibold">
              {money(configuration.budgetMillions * 1e6)}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-subtle">Entered variable exposure</dt>
            <dd className="mt-1 text-xl font-semibold">
              {knownExposure ? money(exposed) : 'Unknown'}
              <p className="text-xs font-normal text-subtle">At risk, not added cost</p>
            </dd>
          </div>
          <div>
            <dt className="text-sm text-subtle">Contingency reserve</dt>
            <dd className="mt-1 text-xl font-semibold">
              {configuration.contingencyPct}%
              <p className="text-xs font-normal text-subtle">Separate from added cost</p>
            </dd>
          </div>
        </dl>
        <p className="mt-4 text-sm text-subtle">
          {result?.qualified === 'conditional'
            ? 'Hours, shared capacity and pricing are entered assumptions. Confirm them before committing.'
            : input.project.supportedContext === false
              ? 'Quantified use supports Alberta schools, hospitals and government buildings only.'
              : 'Add work hours, shared capacity and remaining commitments to quantify.'}
        </p>
        <p
          className="mt-2 text-xs text-subtle"
          data-testid="assessment-evidence-status"
        >
          Sources verified:{' '}
          {readiness
            ? `${readiness.currentSources}/${readiness.totalSources}`
            : 'unknown'}
          {readiness?.freshnessAsOf ? ` as of ${readiness.freshnessAsOf}` : ''}{' '}
          · Release: {readiness?.releaseVintage ?? 'unknown'} · Independent
          review pending
        </p>
        {evaluated.error ? (
          <p className="mt-3 text-danger">{evaluated.error}</p>
        ) : null}
        {result ? (
          <>
            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              {(
                [
                  ['baseline', 'Baseline', null],
                  ['withDC', 'With selected AI work', result.impacts.withDC],
                  [
                    'mitigation',
                    'With your mitigation',
                    result.impacts.mitigation,
                  ],
                ] as const
              ).map(([key, label, impact]) => (
                <article
                  key={key}
                  className="rounded-lg border border-line p-4"
                  aria-label={label}
                >
                  <h3 className="font-semibold">{label}</h3>
                  <dl className="mt-3 space-y-3 text-sm">
                    <div>
                      <dt className="text-subtle">Conditional completion</dt>
                      <dd>{displayMonth(result.cases[key].completionMonth)}</dd>
                    </div>
                    <div>
                      <dt className="text-subtle">Delay vs baseline</dt>
                      <dd data-testid={`${key}-delay`}>
                        {key !== 'baseline' && !draft.dcId
                          ? 'No AI work selected'
                          : impact?.delayMonths === null ||
                              (impact === null &&
                                result.cases.baseline.completionMonth === null)
                            ? 'Not quantified'
                            : `${impact?.delayMonths ?? 0} months`}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-subtle">Added cost vs baseline</dt>
                      <dd data-testid={`${key}-cost`}>
                        {key !== 'baseline' && !draft.dcId
                          ? 'No AI work selected'
                          : impact
                            ? money(impact.totalAdditionalCAD)
                            : result.cases.baseline.financial
                                  .totalAdditionalCAD === null
                              ? 'Not quantified'
                              : money(0)}
                      </dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
            <details className="mt-5">
              <summary className="cursor-pointer font-medium">
                Package results & cost breakdown
              </summary>
              <div className="mt-3 overflow-x-auto">
                <a
                  href="#owner-result-heading"
                  className="mb-2 inline-block text-brand underline"
                >
                  Return to result summary
                </a>
                <table className="w-full text-left text-sm">
                  <caption className="mb-3 text-left font-medium">
                    Package results by case
                  </caption>
                  <thead>
                    <tr>
                      {[
                        'Case',
                        'Package',
                        'Completion',
                        'Delay',
                        'Unserved hours',
                        'Escalation',
                        'Scarcity sensitivity',
                        'Exposure',
                      ].map((label) => (
                        <th
                          key={label}
                          className="border-b border-line p-2 font-medium"
                        >
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(['baseline', 'withDC', 'mitigation'] as const).flatMap(
                      (key) =>
                        result.cases[key].packageResults.map((item) => (
                          <tr key={`${key}-${item.id}`}>
                            <td className="border-b border-line p-2">
                              {
                                {
                                  baseline: 'Baseline',
                                  withDC: 'With AI',
                                  mitigation: 'Mitigation',
                                }[key]
                              }
                            </td>
                            <td className="border-b border-line p-2">
                              {draft.packages.find(
                                (pack) => pack.id === item.id,
                              )?.name ?? item.id}
                            </td>
                            <td className="border-b border-line p-2">
                              {displayMonth(item.completionMonth)}
                            </td>
                            <td className="border-b border-line p-2">
                              {item.delayMonths === null
                                ? 'Unknown'
                                : `${item.delayMonths} months`}
                            </td>
                            <td className="border-b border-line p-2">
                              {item.remainingHours ?? 'Unknown'}
                            </td>
                            <td className="border-b border-line p-2">
                              {money(item.escalationCAD)}
                            </td>
                            <td className="border-b border-line p-2">
                              {money(item.scarcityCAD)}
                            </td>
                            <td className="border-b border-line p-2">
                              {money(item.exposureCAD)}
                            </td>
                          </tr>
                        )),
                    )}
                  </tbody>
                </table>
              </div>
              <p className="mt-3 text-sm text-subtle">
                Baseline escalation:{' '}
                {money(result.cases.baseline.financial.escalationCAD)}. Baseline
                site overhead:{' '}
                {money(result.cases.baseline.financial.overheadCAD)}.
                Incremental escalation with AI:{' '}
                {money(result.impacts.withDC.escalationCAD)}. Incremental site
                overhead: {money(result.impacts.withDC.overheadCAD)}. Scarcity
                sensitivity: {money(result.impacts.withDC.scarcityCAD)}. No
                scarcity premium is inferred from capacity. Overhead is counted
                once at the project milestone.
              </p>
            </details>
            <details className="mt-5">
              <summary className="cursor-pointer font-medium">
                Assumptions, evidence & next steps
              </summary>
              <div className="mt-3 space-y-3 text-sm leading-6">
                <p>
                  Shared trade demand → package completion → exposed commitments
                  → cost. Baseline excludes selected AI work; mitigation changes
                  only your selected controls. Proximity alone does not
                  establish competition. Unknown quantities and capacity stay
                  unknown. Supplier and utility impacts remain qualitative
                  without costed commitments.
                </p>
                <p>
                  {result.matches.length} explicit package match
                  {result.matches.length === 1 ? '' : 'es'}. No match is
                  inferred from a project’s location description.
                </p>
                <p>
                  Entered packages:{' '}
                  {draft.packages
                    .map(
                      (item) =>
                        `${item.name}: ${item.hours === null ? 'hours unknown' : `${item.hours} paid hours`}, ${item.commitment}, remaining exposure ${money(item.uncommittedCAD)}`,
                    )
                    .join('; ')}
                  .
                </p>
                <ul className="list-disc space-y-1 pl-5">
                  {result.unknowns.map((unknown, i) => (
                    <li key={i}>{unknown}</li>
                  ))}
                </ul>
                <ol className="list-decimal space-y-1 pl-5">
                  {result.assumptionChain.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
                {result.capacityThresholds.map((grid) => (
                  <p key={grid.resourceKey}>
                    Conditional capacity threshold for {grid.resourceKey}:{' '}
                    {grid.minimumTestedCapacityHours === null
                      ? 'No successful threshold established in the entered grid'
                      : `${grid.minimumTestedCapacityHours} assumed paid hours / month`}
                    . {grid.qualification}
                  </p>
                ))}
                <p>
                  Next actions: confirm package quantities and contractor pools,
                  obtain supplier delivery dates, verify utility milestones, and
                  review procurement terms before treating scenario costs as
                  commitments.
                </p>
              </div>
            </details>
          </>
        ) : null}
      </section>
      <details className={panelClass}>
        <summary className="cursor-pointer text-lg font-semibold">
          1. Packages & commitments
        </summary>
        <p className="mt-3 text-sm leading-6 text-subtle">
          Leave unknowns blank. Budgets do not supply work quantities.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Field label="Confirmed shared contractor catchment">
            <input
              className={fieldClass}
              value={draft.catchment}
              placeholder="Unknown; enter a pool you can support"
              onChange={(event) => change('catchment', event.target.value)}
            />
          </Field>
          <Numeric
            label="Project schedule float (months)"
            step="1"
            value={draft.floatMonths}
            onChange={(value) => change('floatMonths', value ?? 0)}
          />
        </div>
        <label className="mt-4 flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            className="mt-1"
            checked={draft.confirmedPool}
            onChange={(event) => change('confirmedPool', event.target.checked)}
          />
          I explicitly assume or have evidence that these packages use the
          entered contractor pool. A city or nearby site alone does not confirm
          this.
        </label>
        <div className="mt-4 space-y-3">
          {draft.packages.map((item) => (
            <details
              key={item.id}
              className="rounded-lg border border-line p-4"
            >
              <summary className="cursor-pointer font-semibold">
                {item.name}
              </summary>
              <p className="mt-3 text-sm text-subtle">
                Fixed terms set variable exposure to $0. Re-enter exposure when
                terms change.
              </p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <Numeric
                  label={`${item.scope} package budget (CAD)`}
                  value={item.budgetCAD}
                  onChange={(value) =>
                    packageChange(item.id, 'budgetCAD', value)
                  }
                />
                <Numeric
                  label={`${item.scope} remaining exposed value (CAD)`}
                  value={item.uncommittedCAD}
                  onChange={(value) =>
                    packageChange(item.id, 'uncommittedCAD', value)
                  }
                />
                <Field label={`${item.scope} commitment`}>
                  <select
                    className={fieldClass}
                    value={item.commitment}
                    onChange={(event) =>
                      packageChange(
                        item.id,
                        'commitment',
                        event.target.value as OwnerPackage['commitment'],
                      )
                    }
                  >
                    <option value="unknown">Unknown</option>
                    <option value="fixed">Fixed / committed</option>
                    <option value="variable">Uncommitted / variable</option>
                  </select>
                </Field>
                <Numeric
                  label={`${item.scope} paid labour hours`}
                  value={item.hours}
                  onChange={(value) => packageChange(item.id, 'hours', value)}
                />
                <Field label={`${item.scope} work starts`}>
                  <input
                    type="month"
                    className={fieldClass}
                    value={monthText(item.releaseMonth)}
                    onChange={(event) =>
                      packageChange(
                        item.id,
                        'releaseMonth',
                        monthNumber(event.target.value),
                      )
                    }
                  />
                </Field>
                <Field label={`${item.scope} planned work finish`}>
                  <input
                    type="month"
                    className={fieldClass}
                    value={monthText(item.finishMonth)}
                    onChange={(event) =>
                      packageChange(
                        item.id,
                        'finishMonth',
                        monthNumber(event.target.value),
                      )
                    }
                  />
                </Field>
                <Field label={`${item.scope} procurement month`}>
                  <input
                    type="month"
                    className={fieldClass}
                    value={monthText(item.cashMonth)}
                    onChange={(event) =>
                      packageChange(
                        item.id,
                        'cashMonth',
                        monthNumber(event.target.value),
                      )
                    }
                  />
                </Field>
                <Field label={`${item.scope} predecessor`}>
                  <select
                    className={fieldClass}
                    value={item.predecessors[0] ?? ''}
                    onChange={(event) =>
                      packageChange(
                        item.id,
                        'predecessors',
                        event.target.value ? [event.target.value] : [],
                      )
                    }
                  >
                    <option value="">None supplied</option>
                    {draft.packages
                      .filter((other) => other.id !== item.id)
                      .map((other) => (
                        <option key={other.id} value={other.id}>
                          {other.name}
                        </option>
                      ))}
                  </select>
                </Field>
                <Field label={`${item.scope} input basis`}>
                  <select
                    className={fieldClass}
                    value={item.basis}
                    onChange={(event) =>
                      packageChange(
                        item.id,
                        'basis',
                        event.target.value as Basis,
                      )
                    }
                  >
                    <option value="unknown">Unknown</option>
                    <option value="assumption">User assumption</option>
                    <option value="evidence">Supported evidence</option>
                  </select>
                </Field>
                {(
                  [
                    'source',
                    'material',
                    'equipment',
                    'supplier',
                    'utility',
                  ] as const
                ).map((key) => (
                  <Field key={key} label={`${item.scope} ${key}`}>
                    <input
                      className={fieldClass}
                      value={item[key]}
                      placeholder="Unknown"
                      onChange={(event) =>
                        packageChange(item.id, key, event.target.value)
                      }
                    />
                  </Field>
                ))}
              </div>
            </details>
          ))}
        </div>
      </details>
      <details className={panelClass}>
        <summary className="cursor-pointer text-lg font-semibold">
          2. Shared resources & AI phase
        </summary>
        <p className="mt-3 text-sm text-subtle">
          Nearby projects need a shared resource pool to create competition.
          Phase demand is unverified.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Selected data-centre phase">
            <select
              className={fieldClass}
              value={draft.dcId}
              onChange={(event) => change('dcId', event.target.value)}
            >
              <option value="">None selected</option>
              {dcPhaseCatalogue.map((phase) => (
                <option key={phase.id} value={phase.id}>
                  {phase.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="AI phase contractor catchment">
            <input
              className={fieldClass}
              value={draft.dcCatchment}
              placeholder="Unknown; proximity is insufficient"
              onChange={(event) => change('dcCatchment', event.target.value)}
            />
          </Field>
          <Field label="AI phase trade">
            <select
              className={fieldClass}
              value={draft.dcTrade}
              onChange={(event) =>
                change('dcTrade', event.target.value as Draft['dcTrade'])
              }
            >
              {trades.map((trade) => (
                <option key={trade}>{trade}</option>
              ))}
            </select>
          </Field>
          <Numeric
            label="AI phase paid labour hours"
            value={draft.dcHours}
            onChange={(value) => change('dcHours', value)}
          />
          <Field label="AI phase work starts">
            <input
              type="month"
              className={fieldClass}
              value={monthText(draft.dcRelease)}
              onChange={(event) =>
                change('dcRelease', monthNumber(event.target.value))
              }
            />
          </Field>
          <Field label="AI phase planned work finish">
            <input
              type="month"
              className={fieldClass}
              value={monthText(draft.dcFinish)}
              onChange={(event) =>
                change('dcFinish', monthNumber(event.target.value))
              }
            />
          </Field>
          <Field label="AI phase input basis">
            <select
              className={fieldClass}
              value={draft.dcBasis}
              onChange={(event) =>
                change('dcBasis', event.target.value as Basis)
              }
            >
              <option value="unknown">Unknown</option>
              <option value="assumption">User assumption</option>
              <option value="evidence">Supported evidence</option>
            </select>
          </Field>
          <Field label="AI phase source or assumption">
            <input
              className={fieldClass}
              value={draft.dcSource}
              onChange={(event) => change('dcSource', event.target.value)}
            />
          </Field>
          <Numeric
            label="Other private paid hours in the shared trade"
            value={draft.privateHours}
            onChange={(value) => change('privateHours', value)}
          />
          {trades.map((trade) => (
            <Numeric
              key={trade}
              label={`${trade} shared capacity (paid hours / month)`}
              value={draft.capacity[trade]}
              onChange={(value) =>
                change('capacity', { ...draft.capacity, [trade]: value })
              }
            />
          ))}
        </div>
        <div className="mt-4">
          <Field label="Optional assumed capacity test grid (hours / month, comma separated)">
            <input
              className={fieldClass}
              value={draft.thresholdCandidates}
              placeholder="For example: 5, 10, 20; actual capacity stays unknown"
              onChange={(event) =>
                change('thresholdCandidates', event.target.value)
              }
            />
          </Field>
        </div>
        {candidate ? (
          <div
            className="mt-4 space-y-3 text-sm leading-6"
            data-testid="assessment-phase-evidence"
          >
            <p>
              Candidate: {candidate.name} · {candidate.location} ·{' '}
              {candidate.stage} · registry as of {candidate.registryAsOf}.
              Hours, phase costs and capacity are unverified.
            </p>
            <details>
              <summary className="cursor-pointer font-medium">
                Phase sources & scope
              </summary>
              <p>
                {candidate.reportedWindowQualification}{' '}
                {candidate.costQualification}
              </p>
              <ul className="list-disc space-y-2 pl-5">
                {candidate.sourceRefs.map((source) => (
                  <li key={source.id}>
                    <a href={source.href} className="text-brand underline">
                      {source.id}
                    </a>{' '}
                    · {source.status} · {source.reviewStatus}. {source.note}
                  </li>
                ))}
              </ul>
              {candidate.enablingAssetLinks.length ? (
                <details>
                  <summary className="cursor-pointer font-semibold">
                    Linked enabling infrastructure and payer evidence
                  </summary>
                  <div className="mt-3 space-y-4">
                    {candidate.enablingAssetLinks.map((asset) => (
                      <article
                        className="rounded-lg border border-line p-3"
                        key={asset.id}
                      >
                        <h4 className="font-semibold">{asset.id}</h4>
                        <p>
                          {asset.aiPhaseIds.length
                            ? `Linked phase: ${asset.aiPhaseIds.join(', ')}`
                            : 'Site-level evidence; exact phase attribution unresolved.'}{' '}
                          · {asset.publicationStatus}
                        </p>
                        <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                          {(
                            [
                              'scope',
                              'incrementality',
                              'costCad',
                              'payer',
                              'funding',
                              'aiCapexMembership',
                              'inServiceMilestone',
                            ] as const
                          ).map((key) => (
                            <div key={key}>
                              <dt className="text-subtle">
                                {
                                  {
                                    scope: 'Scope',
                                    incrementality: 'Baseline or additional',
                                    costCad: 'Cost (CAD)',
                                    payer: 'Payer',
                                    funding: 'Funding',
                                    aiCapexMembership: 'Included in AI CAPEX',
                                    inServiceMilestone: 'Service milestone',
                                  }[key]
                                }
                              </dt>
                              <dd>
                                {asset[key].value === null
                                  ? 'Unknown'
                                  : typeof asset[key].value === 'string' ||
                                      typeof asset[key].value === 'number'
                                    ? String(asset[key].value)
                                    : JSON.stringify(asset[key].value)}{' '}
                                · {asset[key].status}. {asset[key].note}
                              </dd>
                            </div>
                          ))}
                        </dl>
                        <p className="mt-2">
                          {asset.sourceRefs.map((source, i) => (
                            <span key={source.id}>
                              {i ? ' · ' : ''}
                              <a
                                href={source.href}
                                className="text-brand underline"
                              >
                                {source.id}
                              </a>{' '}
                              ({source.reviewStatus})
                            </span>
                          ))}
                        </p>
                      </article>
                    ))}
                  </div>
                </details>
              ) : null}
              <p>
                The JSON export retains this record, its evidence statuses and
                provenance. Linked enabling costs are not automatically added to
                your budget or counted again within AI CAPEX.
              </p>
            </details>
          </div>
        ) : null}
      </details>
      <details className={panelClass}>
        <summary className="cursor-pointer text-lg font-semibold">
          3. Mitigation & pricing
        </summary>
        <p className="mt-3 text-sm leading-6 text-subtle">
          Test timing, procurement or capacity changes. Improvement is not
          assumed.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Numeric
            label="Exposed commitment escalation (% / year)"
            value={draft.annualRate}
            onChange={(value) => change('annualRate', value)}
          />
          <Numeric
            label="Site overhead exposure (CAD / month)"
            value={draft.overhead}
            onChange={(value) => change('overhead', value)}
          />
          <Numeric
            label="Stagger AI work (months)"
            step="1"
            value={draft.stagger}
            onChange={(value) => change('stagger', value ?? 0)}
          />
          <Numeric
            label="Earlier variable-package procurement (months)"
            step="1"
            value={draft.early}
            onChange={(value) => change('early', value ?? 0)}
          />
          <Numeric
            label="Added shared-trade capacity (paid hours / month)"
            value={draft.addedCapacity}
            onChange={(value) => change('addedCapacity', value ?? 0)}
          />
        </div>
      </details>
      <section
        className={`${panelClass} print:hidden`}
        aria-label="Save and export assessment"
      >
        <div className="flex flex-wrap gap-3">
          <button type="button" className={buttonClass} onClick={exportJSON}>
            Export current assessment JSON
          </button>
          <button
            type="button"
            className={buttonClass}
            onClick={() => window.print()}
          >
            Print assessment / save PDF
          </button>
          <button type="button" className={buttonClass} onClick={reset}>
            Reset package draft
          </button>
        </div>
        <label className="mt-4 flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            className="mt-1"
            checked={draft.storage}
            onChange={(event) => {
              change('storage', event.target.checked);
              if (!event.target.checked) localStorage.removeItem(storageKey);
            }}
          />
          Save this draft in this browser across navigation. No project inputs
          are sent to an external service.
        </label>
        <output className="mt-2 block text-sm text-subtle">
          {storageMessage}
        </output>
        {error ? <p className="mt-2 text-danger">{error}</p> : null}
      </section>
      <section
        id="project-assessment-print-record"
        className="hidden break-before-page print:block"
        aria-label="Printed assessment inputs"
      >
        <h2 className="text-xl font-semibold">
          Current assessment inputs and result
        </h2>
        <p>
          Same configuration and package inputs as the displayed assessment.
          Conditional planning scenario; no causal AI premium.
        </p>
        <pre className="mt-4 whitespace-pre-wrap break-words text-xs">
          {JSON.stringify(record(), null, 2)}
        </pre>
      </section>
    </div>
  );
}
