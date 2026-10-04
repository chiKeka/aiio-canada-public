import evidence from '../data/pilots/alberta-cal3-windsong-v0.1.json' with { type: 'json' };
import type { PilotStressInput } from './pilot-stress';
export type PilotField<T> = { value: T | null; status: 'observed' | 'derived' | 'assumption' | 'unknown'; sourceIds: string[]; note: string };
function freezeEvidence<T>(value: T): Readonly<T> {
  if (value && typeof value === 'object') {
    for (const child of Object.values(value)) freezeEvidence(child);
    Object.freeze(value);
  }
  return value;
}
export const pilotEvidence = freezeEvidence(evidence);
export const pilotDefaults = { capacity: null as number | null, privateMultiplier: 1, mobility: 0, policy: 'pro-rata' as const, dcShiftMonths: 0 };
export type PilotControls = {
  capacity: number | null;
  privateMultiplier: number;
  mobility: number;
  policy: 'pro-rata' | 'protect-background' | 'prefer-dc';
  dcShiftMonths: number;
};
export const pilotResourceKey = 'Rocky View–Airdrie:Electrical';
export function pilotMonthLabel(index: number) {
  if (!Number.isInteger(index)) throw new Error('Pilot month must be an integer');
  return new Date(Date.UTC(2026, index, 1)).toLocaleDateString('en-CA', { month: 'short', year: 'numeric', timeZone: 'UTC' });
}
/** Factory copies assumptions; source facts are never used as package quantities. */
export function buildPilotInput(controls: Partial<PilotControls> = {}): PilotStressInput {
  const c = { ...pilotDefaults, ...controls };
  if ((c.capacity !== null && (!Number.isFinite(c.capacity) || c.capacity < 0)) || !Number.isFinite(c.privateMultiplier) || c.privateMultiplier < 0 || !Number.isFinite(c.mobility) || c.mobility < 0 || !Number.isInteger(c.dcShiftMonths) || c.dcShiftMonths < 0 || !['pro-rata', 'protect-background', 'prefer-dc'].includes(c.policy)) throw new Error('Invalid pilot scenario controls');
  return {
    packages: [
      { id: 'windsong-electrical-assumed', region: 'Rocky View–Airdrie', trade: 'Electrical', kind: 'background', hours: 100, releaseMonth: 0, plannedFinishMonth: 20, predecessors: [] },
      { id: 'other-private-electrical-assumed', region: 'Rocky View–Airdrie', trade: 'Electrical', kind: 'background', hours: 50, releaseMonth: 0, plannedFinishMonth: 20, predecessors: [] },
      { id: 'cal3-phase1-electrical-assumed', region: 'Rocky View–Airdrie', trade: 'Electrical', kind: 'dc', hours: 100, releaseMonth: 0, plannedFinishMonth: 8, predecessors: [] },
    ],
    schedule: { startMonth: 0, endMonth: 36, capacity: { [pilotResourceKey]: c.capacity }, policy: c.policy, annualEscalation: 0 },
    protectedPackageId: 'windsong-electrical-assumed', protectedFinishMonth: 20,
    resourceKey: pilotResourceKey, capacityCandidates: [c.capacity],
    dcReleaseOffsetsMonths: [c.dcShiftMonths],
    privateBackgroundPackageIds: ['other-private-electrical-assumed'], privateBackgroundMultipliers: [c.privateMultiplier],
    mobilityCapacityHours: [c.mobility], policies: [c.policy],
    hoursBasis: { unit: 'normalized-paid-hours', paidHoursPerUnit: null, assumption: 'Scenario only: school 100, other-private 50 and CAL-3 electrical 100 normalized paid-work units. No measured hours or workforce conversion. Shared Rocky View–Airdrie electrical catchment and Jan2026 releases assumed; school package finish Sep2027 is a planning interpretation of fall2027 opening, not a contractual milestone. CAL-3 package finish Sep2026 is assumed, not an observed package date. No uncommitted school cost or site overhead supplied: dollar impacts remain null.' },
  };
}
export function buildPilotSensitivityInput(): PilotStressInput {
  return { ...buildPilotInput({ capacity: 10 }), capacityCandidates: [null, 0, 5, 7.5, 10, 12.5, 15, 20, 25, 30], dcReleaseOffsetsMonths: [0, 3, 6, 9, 12, 21], privateBackgroundMultipliers: [.5, 1, 1.5], mobilityCapacityHours: [0, 2, 5], policies: ['pro-rata', 'protect-background', 'prefer-dc'] };
}
