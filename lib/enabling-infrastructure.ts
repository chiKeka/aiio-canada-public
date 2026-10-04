/** An accounting contract, not an estimate of AI-induced public expenditure. */
export type Payer = 'developer' | 'utility' | 'ratepayer' | 'government' | 'unknown';
export type CostRange = { low: number; high: number };
export type EnablingAsset = {
  id: string;
  aiPhaseIds: string[];
  assetClass: 'transmission' | 'substation' | 'roads' | 'water' | 'generation';
  scope: string;
  incrementality: 'incremental' | 'baseline' | 'unknown';
  funding: 'already_funded' | 'uncommitted' | 'unknown';
  costCad: CostRange | null;
  costBasis: 'observed' | 'scenario' | 'unknown';
  timing: { startYear: number | null; endYear: number | null };
  evidence: { status: 'observed' | 'inferred' | 'scenario'; sourceIds: string[]; note: string };
  payerShares: Partial<Record<Payer, number>>;
  // Explicit accounting boundary; unknown membership is never added to capex.
  aiCapexMembership: 'included' | 'excluded' | 'unknown';
  capexComponent: string | null;
};
export type EnablingLedger = {
  schemaVersion: '1.0';
  scenarioId: string;
  aiPhaseIds: string[];
  currency: 'CAD';
  priceYear: number;
  aiCapexCad: number;
  componentBudgetsCad: Record<string, number>;
  assets: EnablingAsset[];
};
const payers: Payer[] = ['developer', 'utility', 'ratepayer', 'government', 'unknown'];
const emptyRange = (): CostRange => ({ low: 0, high: 0 });
const add = (total: CostRange, value: CostRange, weight = 1) => {
  total.low += value.low * weight;
  total.high += value.high * weight;
};
export function summarizeEnablingLedger(ledger: EnablingLedger) {
  const errors: string[] = [];
  const ids = new Set<string>();
  const includedByComponent: Record<string, CostRange> = {};
  const additionalIncrementalCad = emptyRange();
  const allocatedIncrementalCad = Object.fromEntries(payers.map(p => [p, emptyRange()])) as Record<Payer, CostRange>;
  let unresolvedAssets = 0;
  const validMoney = (n: number) => Number.isFinite(n) && n >= 0;
  if (!validMoney(ledger.aiCapexCad)) errors.push('AI capex must be finite and nonnegative');
  for (const [component, budget] of Object.entries(ledger.componentBudgetsCad)) {
    if (!validMoney(budget)) errors.push(`${component}: invalid component budget`);
  }
  if (Object.values(ledger.componentBudgetsCad).reduce((a, b) => a + b, 0) > ledger.aiCapexCad + 0.01) errors.push('Component budgets exceed AI capex');
  for (const asset of ledger.assets) {
    if (ids.has(asset.id)) errors.push(`${asset.id}: duplicate asset (shared assets must have one row)`);
    ids.add(asset.id);
    if (!asset.aiPhaseIds.length || asset.aiPhaseIds.some(id => !ledger.aiPhaseIds.includes(id))) errors.push(`${asset.id}: unknown or missing AI phase link`);
    const shares = Object.entries(asset.payerShares);
    if (shares.some(([payer, share]) => !payers.includes(payer as Payer) || !Number.isFinite(share) || share < 0 || share > 1) || Math.abs(shares.reduce((sum, [, share]) => sum + share, 0) - 1) > 1e-9) errors.push(`${asset.id}: payer shares must reconcile to one (use unknown explicitly)`);
    if (asset.timing.startYear !== null && asset.timing.endYear !== null && asset.timing.endYear < asset.timing.startYear) errors.push(`${asset.id}: timing is reversed`);
    if (asset.costCad && (!validMoney(asset.costCad.low) || !validMoney(asset.costCad.high) || asset.costCad.low > asset.costCad.high)) errors.push(`${asset.id}: invalid cost range`);
    if ((asset.costCad === null) !== (asset.costBasis === 'unknown')) errors.push(`${asset.id}: unknown cost must remain null`);
    if (asset.costBasis === 'observed' && (asset.evidence.status !== 'observed' || !asset.evidence.sourceIds.length)) errors.push(`${asset.id}: observed cost requires observed source evidence`);
    if (!asset.costCad || asset.incrementality === 'unknown' || asset.aiCapexMembership === 'unknown') unresolvedAssets++;
    if (asset.aiCapexMembership === 'included') {
      if (!asset.capexComponent || !(asset.capexComponent in ledger.componentBudgetsCad)) errors.push(`${asset.id}: included asset requires a component budget`);
      else if (asset.costCad) add(includedByComponent[asset.capexComponent] ??= emptyRange(), asset.costCad);
    }
    if (asset.costCad && asset.incrementality === 'incremental') {
      for (const payer of payers) add(allocatedIncrementalCad[payer], asset.costCad, asset.payerShares[payer] ?? 0);
      if (asset.aiCapexMembership === 'excluded') add(additionalIncrementalCad, asset.costCad);
    }
  }
  for (const [component, cost] of Object.entries(includedByComponent)) if (cost.high > ledger.componentBudgetsCad[component] + 0.01) errors.push(`${component}: included assets exceed component budget`);
  // Fail closed: an invalid ledger cannot emit usable totals.
  return {
    valid: errors.length === 0, errors, unresolvedAssets,
    complete: errors.length === 0 && unresolvedAssets === 0,
    additionalIncrementalCad: errors.length ? null : additionalIncrementalCad,
    allocatedIncrementalCad: errors.length ? null : allocatedIncrementalCad,
    includedByComponent: errors.length ? null : includedByComponent,
    totalProgramCad: errors.length || unresolvedAssets ? null : { low: ledger.aiCapexCad + additionalIncrementalCad.low, high: ledger.aiCapexCad + additionalIncrementalCad.high },
    boundary: 'Known scoped ranges only. Unknown assets are not zero. Payer shares are assumptions unless supported by evidence; utility and ratepayer allocations must describe mutually exclusive ultimate incidence. Already-funded baseline work is excluded from additional AI cost. No causal or fiscal forecast is authorized.',
  };
}
