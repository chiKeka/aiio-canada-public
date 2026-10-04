export type SpendingProfile = 'uniform' | 'front_loaded' | 'back_loaded' | 'bell';
export const SPENDING_PROFILES: Record<SpendingProfile, string> = {
  uniform: 'Even spending', front_loaded: 'Front-loaded', back_loaded: 'Back-loaded', bell: 'Mid-project peak',
};

export function monthNumber(value: string): number | null {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) return null;
  const [year, month] = value.split('-').map(Number);
  return year * 12 + month - 1;
}

/** Missing, malformed and out-of-range URL values preserve the caller's default. */
export function queryNumber(query: URLSearchParams, key: string, min: number, max: number, integer = false): number | undefined {
  const raw = query.get(key);
  if (raw === null || raw.trim() === '') return undefined;
  const value = Number(raw);
  return Number.isFinite(value) && value >= min && value <= max && (!integer || Number.isInteger(value)) ? value : undefined;
}

export function spendingShares(count: number, profile: SpendingProfile): number[] {
  if (!Number.isInteger(count) || count < 1 || count > 120 || !Object.hasOwn(SPENDING_PROFILES, profile)) throw new Error('Invalid spending profile');
  const weights = Array.from({ length: count }, (_, i) => profile === 'front_loaded' ? count - i : profile === 'back_loaded' ? i + 1 : profile === 'bell' ? (i + 1) * (count - i) : 1);
  const total = weights.reduce((sum, value) => sum + value, 0);
  return weights.map((value) => value / total);
}

export function allocateMonthlyDrivers(weights: Array<number | null>, increment: number | null): Array<number | null> {
  if (increment === null || !Number.isFinite(increment) || weights.some((weight) => weight === null || !Number.isFinite(weight) || weight < 0)) return weights.map(() => null);
  if (increment === 0) return weights.map(() => 0);
  const total = weights.reduce<number>((sum, weight) => sum + weight!, 0);
  return weights.map((weight) => total > 0 ? weight! / total * increment : null);
}

type PriceRow = {
  month: string;
  cumulative_baseline_pct?: number | null;
  cumulative_combined_pct?: number | null;
  cumulative_lower_pct?: number | null;
  cumulative_upper_pct?: number | null;
};

/** Budget excludes contingency. Price levels are anchored to the supplied basis month.
 * No rounded intermediate arithmetic. Unknown rates withhold the whole result.
 */
export function buildCashflowOutlook(rows: PriceRow[], budgetMillions: number, profile: SpendingProfile) {
  if (!Number.isFinite(budgetMillions) || budgetMillions <= 0 || !rows.length) return null;
  const shares = spendingShares(rows.length, profile);
  const months = rows.map((row) => monthNumber(row.month));
  if (months.some((month, i) => month === null || (i > 0 && month !== months[i - 1]! + 1))) return null;
  if (rows.some((row) => {
    const values = [row.cumulative_baseline_pct, row.cumulative_combined_pct, row.cumulative_lower_pct, row.cumulative_upper_pct];
    return values.some((value) => value == null || !Number.isFinite(value) || value <= -100)
      || row.cumulative_lower_pct! > row.cumulative_combined_pct! || row.cumulative_combined_pct! > row.cumulative_upper_pct!;
  })) return null;
  const monthly = rows.map((row, i) => {
    const baseSpend = budgetMillions * shares[i];
    const baselineEscalation = baseSpend * row.cumulative_baseline_pct! / 100;
    const combinedEscalation = baseSpend * row.cumulative_combined_pct! / 100;
    return {
      month: row.month, share: shares[i], baseSpend, baselineEscalation,
      aiIncrement: combinedEscalation - baselineEscalation,
      combinedSpend: baseSpend + combinedEscalation,
      lowSpend: baseSpend * (1 + row.cumulative_lower_pct! / 100),
      highSpend: baseSpend * (1 + row.cumulative_upper_pct! / 100),
    };
  });
  const total = (key: 'baselineEscalation' | 'aiIncrement' | 'combinedSpend' | 'lowSpend' | 'highSpend') => monthly.reduce((sum, row) => sum + row[key], 0);
  return { monthly, baselineEscalation: total('baselineEscalation'), aiIncrement: total('aiIncrement'), combinedSpend: total('combinedSpend'), lowSpend: total('lowSpend'), highSpend: total('highSpend') };
}
