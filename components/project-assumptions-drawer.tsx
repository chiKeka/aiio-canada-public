'use client';

import { useState } from 'react';
import { SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  NativeSelect,
  NativeSelectOption,
} from '@/components/ui/native-select';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  ASSETS,
  METROS,
  type AssetId,
  type MetroId,
} from '@/lib/decision-analysis';
import {
  monthNumber,
  SPENDING_PROFILES,
  type SpendingProfile,
} from '@/lib/project-cashflow';
import type { PlanningAssumptions } from '@/lib/planning-calibration';

export type ProjectConfiguration = {
  projectName: string;
  assetId: AssetId;
  metroId: MetroId;
  budgetMillions: number;
  startYear: number;
  duration: number;
  priceBasis: string;
  approvalStage: string;
  contingencyPct: number;
  spendingProfile: SpendingProfile;
  assumptions: PlanningAssumptions;
};

const rateFields = [
  ['annualBaselinePct', 'Baseline (% / year)', 0, 12, 0.1],
  ['peakAiAnnualPctPoints', 'AI peak (pp / year)', 0, 8, 0.05],
  ['localCapturePct', 'Local capture (%)', 0, 80, 1],
  ['lagMonths', 'Lag (months)', 0, 24, 1],
  ['uncertaintyPct', 'AI sensitivity (±%)', 0, 100, 1],
] as const;

export function ProjectAssumptionsDrawer({
  value,
  onApply,
  mode = 'legacy',
}: {
  value: ProjectConfiguration;
  onApply: (next: ProjectConfiguration) => void;
  mode?: 'legacy' | 'assessment';
}) {
  const [open, setOpen] = useState(false);
  const [draftDefaults, setDraftDefaults] = useState(value);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  return (
    <Sheet
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (next) {
          setDraftDefaults(structuredClone(value));
          setRevision((v) => v + 1);
          setError('');
        }
      }}
    >
      <SheetTrigger
        render={<Button variant="outline" className="h-10 bg-surface" />}
      >
        <SlidersHorizontal className="size-4" />
        {mode === 'assessment' ? 'Edit project' : 'Edit assumptions'}
      </SheetTrigger>
      <SheetContent className="gap-0 border-line bg-surface text-ink data-[side=right]:w-full data-[side=right]:sm:max-w-[480px]">
        <SheetHeader className="border-b border-line px-6 py-6 pr-12">
          <SheetTitle className="text-lg">
            {mode === 'assessment' ? 'Your project' : 'Project & assumptions'}
          </SheetTitle>
          <SheetDescription>
            Changes update the assessment only when you apply them.
          </SheetDescription>
        </SheetHeader>
        <form
          key={revision}
          className="flex min-h-0 flex-1 flex-col"
          onSubmit={(event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            const number = (key: string) => Number(data.get(key));
            const text = (key: string) => {
              const entry = data.get(key);
              return typeof entry === 'string' ? entry : '';
            };
            const basis = monthNumber(text('priceBasis'));
            if (
              basis === null ||
              basis > monthNumber(`${number('startYear')}-01`)!
            ) {
              setError(
                'Price basis must be a valid month no later than the project start.',
              );
              return;
            }
            const assumptions = { ...draftDefaults.assumptions };
            if (mode === 'legacy')
              for (const [key] of rateFields) assumptions[key] = number(key);
            onApply({
              projectName: text('projectName').trim(),
              assetId: text('assetId') as AssetId,
              metroId: text('metroId') as MetroId,
              budgetMillions: number('budgetMillions'),
              startYear: number('startYear'),
              duration: number('duration'),
              priceBasis: text('priceBasis'),
              approvalStage: text('approvalStage'),
              contingencyPct: number('contingencyPct'),
              spendingProfile: text('spendingProfile') as SpendingProfile,
              assumptions,
            });
            setOpen(false);
          }}
        >
          <div className="min-h-0 flex-1 space-y-6 overflow-y-auto px-6 py-5">
            <fieldset className="grid gap-4">
              <legend className="mb-4 font-semibold">Project context</legend>
              <Field label="Project">
                <Input
                  name="projectName"
                  defaultValue={draftDefaults.projectName}
                  maxLength={160}
                  required
                />
              </Field>
              <Field label="Asset class">
                <NativeSelect
                  name="assetId"
                  defaultValue={draftDefaults.assetId}
                  className="w-full"
                >
                  {Object.entries(ASSETS).map(([id, asset]) => (
                    <NativeSelectOption key={id} value={id}>
                      {asset.label}
                    </NativeSelectOption>
                  ))}
                </NativeSelect>
              </Field>
              <Field label="Market">
                <NativeSelect
                  name="metroId"
                  defaultValue={draftDefaults.metroId}
                  className="w-full"
                >
                  {Object.entries(METROS).map(([id, label]) => (
                    <NativeSelectOption key={id} value={id}>
                      {label}
                    </NativeSelectOption>
                  ))}
                </NativeSelect>
              </Field>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Base budget ($M)">
                  <Input
                    name="budgetMillions"
                    type="number"
                    min={1}
                    max={1000000}
                    step="any"
                    defaultValue={draftDefaults.budgetMillions}
                    required
                  />
                </Field>
                <Field label="Contingency (%)">
                  <Input
                    name="contingencyPct"
                    type="number"
                    min={0}
                    max={40}
                    step="any"
                    defaultValue={draftDefaults.contingencyPct}
                    required
                  />
                </Field>
                <Field label="Start year">
                  <Input
                    name="startYear"
                    type="number"
                    min={2026}
                    max={2040}
                    defaultValue={draftDefaults.startYear}
                    required
                  />
                </Field>
                <Field label="Delivery duration (years)">
                  <Input
                    name="duration"
                    type="number"
                    min={2}
                    max={10}
                    defaultValue={draftDefaults.duration}
                    required
                  />
                </Field>
              </div>
              <Field label="Price basis">
                <Input
                  name="priceBasis"
                  type="month"
                  defaultValue={draftDefaults.priceBasis}
                  required
                />
              </Field>
              <Field label="Approval stage">
                <NativeSelect
                  name="approvalStage"
                  defaultValue={draftDefaults.approvalStage}
                  className="w-full"
                >
                  {[
                    ['concept', 'Concept'],
                    ['business_case', 'Business case'],
                    ['treasury_board', 'Treasury Board'],
                    ['procurement', 'Procurement'],
                    ['delivery', 'Delivery'],
                  ].map(([id, label]) => (
                    <NativeSelectOption key={id} value={id}>
                      {label}
                    </NativeSelectOption>
                  ))}
                </NativeSelect>
              </Field>
              <Field label="Spending profile">
                <NativeSelect
                  name="spendingProfile"
                  defaultValue={draftDefaults.spendingProfile}
                  className="w-full"
                >
                  {Object.entries(SPENDING_PROFILES).map(([id, label]) => (
                    <NativeSelectOption key={id} value={id}>
                      {label}
                    </NativeSelectOption>
                  ))}
                </NativeSelect>
              </Field>
            </fieldset>
            {mode === 'legacy' ? (
              <fieldset className="grid grid-cols-2 gap-4 border-t border-line pt-5">
                <legend className="pr-2 font-semibold">
                  Scenario assumptions
                </legend>
                <p className="col-span-2 text-xs leading-5 text-subtle">
                  These are planning assumptions, not measured AI effects.
                  Scope-matched calibration takes precedence when available.
                </p>
                {rateFields.map(([key, label, min, max, step]) => (
                  <Field key={key} label={label}>
                    <Input
                      name={key}
                      type="number"
                      min={min}
                      max={max}
                      step={step}
                      defaultValue={draftDefaults.assumptions[key]}
                      required
                    />
                  </Field>
                ))}
              </fieldset>
            ) : null}
            <p className="rounded-lg bg-caution-soft p-3 text-xs leading-5 text-caution">
              {mode === 'assessment'
                ? 'Contingency stays separate. Project budget does not establish package quantities, available crews or data-centre impacts.'
                : 'Contingency stays separate. Sensitivity is not a confidence interval, and no mitigation savings are credited.'}
            </p>
            {error ? (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            ) : null}
          </div>
          <div className="flex justify-end gap-3 border-t border-line px-6 py-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit">Apply changes</Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="grid content-start gap-2 text-[13px] text-subtle">
      {label}
      {children}
    </label>
  );
}
