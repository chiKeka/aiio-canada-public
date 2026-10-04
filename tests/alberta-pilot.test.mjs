import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { buildPilotInput, buildPilotSensitivityInput, pilotEvidence, pilotMonthLabel } from '../lib/alberta-pilot.ts';
import { reverseStress } from '../lib/pilot-stress.ts';
test('unknown empirical fields and zero dollar authorization preserved', () => {
 const r = reverseStress(buildPilotInput());
 assert.equal(r.cases[0].protectedTargetMet, null);
 assert.equal(r.cases[0].incrementalEscalationCAD, null);
 assert.equal(pilotEvidence.dollarImpact, null);
 assert.equal(pilotEvidence.facts.aiWholeFacilityEstimateCad.value, 750e6);
 assert.equal(pilotEvidence.facts.aiPhaseCostCad.value, null);
 assert.equal(pilotEvidence.facts.publicUncommittedExposureCad.value, null);
 assert.ok(buildPilotInput().packages.every(p => p.uncommittedExposureCAD === undefined));
 assert.equal(pilotEvidence.scenarioAssumptions.workUnits.status, 'assumption');
 assert.equal(buildPilotInput().hoursBasis.paidHoursPerUnit, null);
});
test('adequate normalized capacity makes incremental delay zero', () => {
 const c=reverseStress(buildPilotInput({capacity:30})).cases[0];
 assert.equal(c.protectedTargetMet,true);
 assert.equal(c.incrementalDelayMonths,0);
 assert.equal(c.incrementalEscalationCAD,null);
});
test('protecting public background avoids DC increment at sufficient background capacity', () => {
 const c=reverseStress(buildPilotInput({capacity:7.5,policy:'protect-background'})).cases[0];
 assert.equal(c.protectedTargetMet,true);
 assert.equal(c.incrementalDelayMonths,0);
});
test('dates preserve scenario calendar instead of converting target to fact', () => {
 assert.equal(pilotMonthLabel(0),'Jan 2026');
 assert.equal(pilotMonthLabel(20),'Sep 2027');
 assert.equal(pilotEvidence.scenarioAssumptions.calendar.status,'assumption');
 assert.equal(pilotEvidence.facts.publicConstructionInterval.status,'observed');
});
test('source pointers preserve receipt hashes and review-only status', () => {
 for (const source of Object.values(pilotEvidence.sources)) {
  assert.match(source.sha256,/^[0-9a-f]{64}$/);
  if(source.receiptPath) {
   const receipt=JSON.parse(readFileSync(new URL(`../${source.receiptPath}`,import.meta.url)));
   assert.equal(receipt.sha256 ?? receipt.web_extract_sha256 ?? receipt.content_hash.replace('sha256:',''),source.sha256);
   assert.equal(source.reviewStatus,'candidate_only');
  }
 }
 for(const fact of Object.values(pilotEvidence.facts)) for(const sourceId of fact.sourceIds) assert.ok(pilotEvidence.sources[sourceId]);
 assert.ok(pilotEvidence.enablingAssets.every(a=>a.costCad.value===null&&a.payer.value===null&&a.aiCapexMembership.value===null));
});
test('scenario factory never mutates fact data or shares mutable packages', () => {
 const before=JSON.stringify(pilotEvidence);
 assert.equal(Object.isFrozen(pilotEvidence.facts.aiPhaseCostCad), true);
 assert.throws(() => { pilotEvidence.facts.aiPhaseCostCad.value = 100; });
 const a=buildPilotInput(),b=buildPilotInput();a.packages[0].hours=1;
 assert.equal(b.packages[0].hours,100);
 assert.equal(JSON.stringify(pilotEvidence),before);
 for(const bad of [{capacity:-1},{dcShiftMonths:.5},{privateMultiplier:NaN},{mobility:-1}]) assert.throws(()=>buildPilotInput(bad));
});
test('full sensitivity is reproducible and never emits dollar impact', () => {
 const r=reverseStress(buildPilotSensitivityInput());
 assert.equal(r.cases.length,1620);
 assert.ok(r.cases.every(c=>c.incrementalEscalationCAD===null&&c.incrementalSiteOverheadCAD===null));
 assert.deepEqual(r,reverseStress(buildPilotSensitivityInput()));
});

test('frozen artifact matches implementation and reproduced case hashes', () => {
 const artifact=JSON.parse(readFileSync(new URL('../data/pilots/alberta-cal3-windsong-thresholds-v0.1.json',import.meta.url)));
 for(const [path, hash] of Object.entries(artifact.sha256)) assert.equal(createHash('sha256').update(readFileSync(new URL(`../${path}`,import.meta.url))).digest('hex'),hash);
 const r=reverseStress(buildPilotSensitivityInput());
 assert.equal(createHash('sha256').update(JSON.stringify(r.cases)).digest('hex'),artifact.casesSha256);
 assert.deepEqual(r.thresholds,artifact.thresholds);
});

test("new payer and workforce context never becomes priced scope or measured capacity", () => {
 assert.equal(pilotEvidence.facts.publicWholeProjectEstimateCad.value, 64300000);
 assert.equal(pilotEvidence.facts.publicUncommittedExposureCad.value, null);
 assert.equal(pilotEvidence.facts.actualTradeCapacity.value, null);
 assert.equal(pilotEvidence.facts.calgaryElectricalEmploymentContext.value.stockBaseYear, null);
 const water=pilotEvidence.enablingAssets.find(a=>a.id==="CAL3_HIGH_PLAINS_WATER_WASTEWATER");
 assert.equal(water.payerObligations.status, "observed");
 assert.equal(water.payer.value, null);
 assert.equal(water.costCad.value, null);
 assert.deepEqual(water.aiPhaseIds, []);
});
