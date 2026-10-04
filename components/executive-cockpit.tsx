'use client';

import Link from 'next/link';
import { ScenarioInterpretation } from '@/components/scenario-interpretation';
import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Clipboard,
  Gauge,
  Layers3,
  Route,
  Printer,
} from 'lucide-react';

import { WorkspaceShell } from '@/components/site-shell';
import { ExecutiveEvidenceLens } from '@/components/executive-evidence-lens';
import { GuidedProjectStory } from '@/components/guided-project-story';
import {
  DecisionCockpitView,
  type PinnedDecision,
} from '@/components/decision-cockpit-view';
import { buildDecisionOutlook } from '@/lib/decision-outlook';
import {
  buildAssessmentRecord,
  encodeAssessmentRecord,
  resolveFocus,
} from '@/lib/assessment-record';
import { ExecutiveDecisionBrief } from '@/components/executive-decision-brief';
import { ProjectAssessmentWorkspace } from '@/components/project-assessment-workspace';
import {
  ProjectAssumptionsDrawer,
  type ProjectConfiguration,
} from '@/components/project-assumptions-drawer';
import { Button } from '@/components/ui/button';
import {
  MonthlyEscalationOutlook,
  type MonthlyEscalationCalibration,
} from '@/components/monthly-escalation-outlook';
import {
  ASSETS,
  buildDecisionAnalysis,
  METROS,
  type AssetId,
  type MetroId,
} from '@/lib/decision-analysis';
import monthlyCalibration from '@/data/model-runs/executive_monthly_escalation_current.json';
import releaseData from '@/public/data/latest.json';
import type { PlanningAssumptions } from '@/lib/planning-calibration';
import {
  monthNumber,
  queryNumber,
  SPENDING_PROFILES,
  type SpendingProfile,
} from '@/lib/project-cashflow';

type View =
  | 'assessment'
  | 'outlook'
  | 'cockpit'
  | 'walkthrough'
  | 'evidence'
  | 'brief';

const views: { id: View; label: string; icon: typeof Gauge }[] = [
  { id: 'assessment', label: 'Assess my project', icon: Route },
  { id: 'walkthrough', label: 'Guided story', icon: Route },
  { id: 'outlook', label: 'Overview', icon: Activity },
  { id: 'cockpit', label: 'Scenario comparison', icon: Gauge },
  { id: 'evidence', label: 'Evidence', icon: Layers3 },
  { id: 'brief', label: 'Decision brief', icon: Printer },
];

type ExecutiveReadiness = {
  proxyPlanning: {
    status: string;
    passed_check_count: number;
    check_count: number;
    checks: {
      id: string;
      status: string;
      finding: string;
      next_step: string | null;
    }[];
  };
  releaseVintage?: string;
  freshnessAsOf?: string;
  currentSources: number;
  totalSources: number;
  trackedProjects: number;
  representedRegions: number;
  targetRegions: number;
  passedIdentificationChecks: number;
  totalIdentificationChecks: number;
};

export function ExecutiveCockpit({
  readiness,
}: {
  readiness: ExecutiveReadiness;
}) {
  const [view, setView] = useState<View>('assessment');
  const [assetId, setAssetId] = useState<AssetId>('hospital');
  const [metroId, setMetroId] = useState<MetroId>('CMA_835');
  const [budgetMillions, setBudgetMillions] = useState(1200);
  const [startYear, setStartYear] = useState(2029);
  const [duration, setDuration] = useState(5);
  const [projectName, setProjectName] = useState('Regional health centre');
  const [priceBasis, setPriceBasis] = useState('2026-06');
  const [approvalStage, setApprovalStage] = useState('business_case');
  const [contingencyPct, setContingencyPct] = useState(12);
  const [spendingProfile, setSpendingProfile] =
    useState<SpendingProfile>('bell');
  const [assumptions, setAssumptions] = useState<PlanningAssumptions>({
    annualBaselinePct: 3.5,
    peakAiAnnualPctPoints: 1.25,
    localCapturePct: 36,
    lagMonths: 3,
    uncertaintyPct: 40,
  });
  const [shareState, setShareState] = useState('Share inputs');
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [selectedDriver, setSelectedDriver] = useState<string | null>(null);
  const [selectedMitigations, setSelectedMitigations] = useState<string[]>([]);
  const [exportStatus, setExportStatus] = useState('');
  const [comparison, setComparison] = useState<PinnedDecision | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const query = new URLSearchParams(window.location.search);
      const requestedView = query.get('view');
      if (views.some((v) => v.id === requestedView))
        setView(requestedView as View);
      const asset = query.get('asset') as AssetId | null;
      const metro = query.get('metro') as MetroId | null;
      if (asset && Object.hasOwn(ASSETS, asset)) setAssetId(asset);
      if (metro && Object.hasOwn(METROS, metro)) setMetroId(metro);
      const budget = queryNumber(query, 'budget', 1, 1_000_000);
      if (budget !== undefined) setBudgetMillions(budget);
      const start = queryNumber(query, 'start', 2026, 2040, true);
      if (start !== undefined) setStartYear(start);
      const years = queryNumber(query, 'years', 2, 10, true);
      if (years !== undefined) setDuration(years);
      if (query.get('name')) setProjectName(query.get('name')!.slice(0, 160));
      const basis = query.get('basis');
      if (basis && monthNumber(basis) !== null) setPriceBasis(basis);
      const stage = query.get('stage');
      if (
        stage &&
        [
          'concept',
          'business_case',
          'treasury_board',
          'procurement',
          'delivery',
        ].includes(stage)
      )
        setApprovalStage(stage);
      const profile = query.get('profile');
      if (profile && Object.hasOwn(SPENDING_PROFILES, profile))
        setSpendingProfile(profile as SpendingProfile);
      const contingency = queryNumber(query, 'contingency', 0, 40);
      if (contingency !== undefined) setContingencyPct(contingency);
      setAssumptions((current) => ({
        annualBaselinePct:
          queryNumber(query, 'baseline', 0, 12) ?? current.annualBaselinePct,
        peakAiAnnualPctPoints:
          queryNumber(query, 'peak', 0, 8) ?? current.peakAiAnnualPctPoints,
        localCapturePct:
          queryNumber(query, 'capture', 0, 80) ?? current.localCapturePct,
        lagMonths: queryNumber(query, 'lag', 0, 24, true) ?? current.lagMonths,
        uncertaintyPct:
          queryNumber(query, 'uncertainty', 0, 100) ?? current.uncertaintyPct,
      }));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);
  const analysis = useMemo(
    () => buildDecisionAnalysis({ assetId, duration, metroId, startYear }),
    [assetId, duration, metroId, startYear],
  );

  const decisionInputs = {
    assumptions,
    budgetMillions,
    priceBasis,
    projectStart: startYear,
    durationYears: duration,
    assetOutcome: analysis.asset.outcome,
    spendingProfile,
  };
  const assessment = buildDecisionOutlook(
    decisionInputs,
    monthlyCalibration as MonthlyEscalationCalibration,
  );
  const focus = resolveFocus(assessment, selectedMonth, selectedDriver);
  const record = buildAssessmentRecord({
    inputs: decisionInputs,
    assessment,
    analysis,
    projectName,
    approvalStage,
    contingencyPct,
    comparison,
    selectedMonth: focus.month,
    selectedDriver: focus.driverId,
    generatedAt: new Date().toISOString(),
    planning: readiness.proxyPlanning,
  });
  const downloadSnapshot = async () => {
    if (!record) return;
    try {
      const data = await encodeAssessmentRecord({
        ...record,
        generated_at: new Date().toISOString(),
      });
      const url = URL.createObjectURL(
        new Blob([data], { type: 'application/json' }),
      );
      const link = document.createElement('a');
      link.href = url;
      link.download = 'aiio-assessment-snapshot.json';
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setExportStatus(
        'Snapshot downloaded. Store it with the brief; it is not uploaded.',
      );
    } catch {
      setExportStatus(
        'Snapshot export failed. Your assessment is unchanged; try again.',
      );
    }
  };
  const shareAssessment = async () => {
    const url = new URL(window.location.href);
    const values = {
      asset: assetId,
      metro: metroId,
      budget: String(budgetMillions),
      start: String(startYear),
      years: String(duration),
      name: projectName,
      basis: priceBasis,
      stage: approvalStage,
      contingency: String(contingencyPct),
      baseline: String(assumptions.annualBaselinePct),
      peak: String(assumptions.peakAiAnnualPctPoints),
      capture: String(assumptions.localCapturePct),
      lag: String(assumptions.lagMonths),
      uncertainty: String(assumptions.uncertaintyPct),
    };
    Object.entries(values).forEach(([key, value]) =>
      url.searchParams.set(key, value),
    );
    url.searchParams.set('profile', spendingProfile);
    url.searchParams.set('view', view);
    window.history.replaceState(null, '', url);
    try {
      await navigator.clipboard.writeText(url.toString());
      setShareState('Link copied');
    } catch {
      setShareState('Copy link from address bar');
    }
    window.setTimeout(() => setShareState('Share inputs'), 1800);
  };

  const configuration: ProjectConfiguration = {
    projectName,
    assetId,
    metroId,
    budgetMillions,
    startYear,
    duration,
    priceBasis,
    approvalStage,
    contingencyPct,
    spendingProfile,
    assumptions,
  };
  const applyConfiguration = (next: ProjectConfiguration) => {
    setProjectName(next.projectName);
    setAssetId(next.assetId);
    setMetroId(next.metroId);
    setBudgetMillions(next.budgetMillions);
    setStartYear(next.startYear);
    setDuration(next.duration);
    setPriceBasis(next.priceBasis);
    setApprovalStage(next.approvalStage);
    setContingencyPct(next.contingencyPct);
    setSpendingProfile(next.spendingProfile);
    setAssumptions(next.assumptions);
  };
  return (
    <WorkspaceShell
      context={
        <>
          <span className="font-medium text-ink">Alberta pilot</span>
          <span className="mx-2">/</span>
          {view === 'assessment' ? 'Project assessment' : 'Executive workspace'}
        </>
      }
      navigation={
        <nav
          className="flex gap-1 overflow-x-auto lg:flex-col"
          aria-label="Executive dashboard views"
        >
          <Link href="/" className="px-3 py-3 text-sm text-white">
            ← Alberta overview
          </Link>
          <Link href="/delivery" className="px-3 py-3 text-sm text-white">
            Delivery decisions
          </Link>
          {views.map(({ id, label, icon: Icon }) => (
            <button
              aria-current={view === id ? 'page' : undefined}
              className={`flex shrink-0 items-center gap-3 rounded-md px-3 py-3 text-left text-[13px] font-medium transition-colors ${view === id ? 'bg-rail-active text-white' : 'text-white/75 hover:bg-rail-active hover:text-white'}`}
              key={id}
              onClick={() => setView(id)}
              type="button"
            >
              <Icon className="size-4" />
              {label}
            </button>
          ))}
        </nav>
      }
      actions={
        view === 'assessment' ? null : (
          <>
            <Button
              variant="outline"
              className="h-10 bg-surface"
              onClick={shareAssessment}
            >
              <Clipboard className="size-4" />
              {shareState}
            </Button>
            <Button
              aria-label="Open decision brief"
              className="h-10"
              onClick={() => setView('brief')}
            >
              <Printer className="size-4" />
              Prepare brief
            </Button>
          </>
        )
      }
    >
      <header className="workspace-heading mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="mb-1 text-xs text-subtle">
            {METROS[metroId]} · {ASSETS[assetId].label} ·{' '}
            {approvalStage.replaceAll('_', ' ')}
          </p>
          <h1 className="text-[26px] font-semibold">
            {projectName || 'Untitled project'}
          </h1>
          <p className="mt-2 text-[13px] text-subtle">
            Jan {startYear} – Dec {startYear + duration - 1} · {priceBasis}{' '}
            price basis · {releaseData.manifest.version}
          </p>
        </div>
        {view !== 'assessment' ? (
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              className="h-10 bg-surface"
              aria-pressed={Boolean(comparison)}
              onClick={() =>
                setComparison(
                  comparison
                    ? null
                    : {
                        inputs: structuredClone(decisionInputs),
                        assessment: structuredClone(assessment),
                        market: METROS[metroId],
                      },
                )
              }
            >
              {comparison ? 'Clear pinned configuration' : 'Pin configuration'}
            </Button>
            <ProjectAssumptionsDrawer
              value={{
                projectName,
                assetId,
                metroId,
                budgetMillions,
                startYear,
                duration,
                priceBasis,
                approvalStage,
                contingencyPct,
                spendingProfile,
                assumptions,
              }}
              onApply={(next) => {
                setProjectName(next.projectName);
                setAssetId(next.assetId);
                setMetroId(next.metroId);
                setBudgetMillions(next.budgetMillions);
                setStartYear(next.startYear);
                setDuration(next.duration);
                setPriceBasis(next.priceBasis);
                setApprovalStage(next.approvalStage);
                setContingencyPct(next.contingencyPct);
                setSpendingProfile(next.spendingProfile);
                setAssumptions(next.assumptions);
              }}
            />
          </div>
        ) : null}
      </header>
      {view !== 'assessment' ? (
        <p className="mb-4 rounded-lg border border-line bg-surface p-4 text-sm text-subtle">
          This view uses the separate budget sensitivity model. Return to Assess my project for package scheduling and exposed commitment results.
        </p>
      ) : null}
      {view !== 'assessment' ? (
        <ScenarioInterpretation
          assessment={assessment}
          inputs={decisionInputs}
          contingencyPct={contingencyPct}
        />
      ) : null}
      <div className="min-w-0">
        {view === 'assessment' ? (
          <ProjectAssessmentWorkspace
            configuration={configuration}
            onApply={applyConfiguration}
            readiness={readiness}
          />
        ) : view === 'outlook' ? (
          <MonthlyEscalationOutlook
            selectedMitigations={selectedMitigations}
            setSelectedMitigations={setSelectedMitigations}
            selectedMonth={focus.month}
            setSelectedMonth={setSelectedMonth}
            selectedDriver={focus.driverId}
            setSelectedDriver={setSelectedDriver}
            assumptions={assumptions}
            assetOutcome={analysis.asset.outcome}
            budgetMillions={budgetMillions}
            calibration={monthlyCalibration as MonthlyEscalationCalibration}
            contingencyPct={contingencyPct}
            durationYears={duration}
            priceBasis={priceBasis}
            projectStart={startYear}
            spendingProfile={spendingProfile}
          />
        ) : view === 'cockpit' ? (
          <DecisionCockpitView
            analysis={analysis}
            assessment={assessment}
            inputs={decisionInputs}
            approvalStage={approvalStage}
            projectName={projectName}
            comparison={comparison}
            planningChecks={`${readiness.proxyPlanning.passed_check_count}/${readiness.proxyPlanning.check_count}`}
          />
        ) : view === 'walkthrough' ? (
          <GuidedProjectStory
            selectedMonth={focus.month}
            setSelectedMonth={setSelectedMonth}
            selectedDriver={focus.driverId}
            setSelectedDriver={setSelectedDriver}
            analysis={analysis}
            assessment={assessment}
            inputs={decisionInputs}
            projectName={projectName}
            approvalStage={approvalStage}
            planningChecks={`${readiness.proxyPlanning.passed_check_count}/${readiness.proxyPlanning.check_count}`}
            onExplore={setView}
          />
        ) : view === 'brief' ? (
          <div className="flex min-h-0 flex-col gap-3">
            <div className="executive-export-controls flex flex-wrap items-center gap-2">
              <Button disabled={!record} onClick={() => window.print()}>
                Print / Save PDF
              </Button>
              <Button disabled={!record} onClick={downloadSnapshot}>
                Download snapshot
              </Button>
              <p className="text-xs text-subtle">
                Share inputs reopens the current model. Download preserves this
                result.
              </p>
              <output className="text-xs text-brand">{exportStatus}</output>
            </div>
            <ExecutiveDecisionBrief record={record} visible />
          </div>
        ) : (
          <ExecutiveEvidenceLens
            analysis={analysis}
            assessment={assessment}
            inputs={decisionInputs}
            planning={readiness.proxyPlanning}
            projectName={projectName}
          />
        )}
      </div>
      {view !== 'brief' && view !== 'assessment' ? (
        <ExecutiveDecisionBrief record={record} visible={false} />
      ) : null}
    </WorkspaceShell>
  );
}
