import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
 assessmentAssetTypes, catchmentOptions, assessmentSupportBoundary,
 buildOwnerPhaseTemplates, buildOwnerPackageTemplates, buildDCPhaseCatalogue, buildCAL3EnablingLinks, dcPhaseCatalogue,
} from '../lib/project-assessment-catalogue.ts';
test('institutional templates supply headings only, never budget-derived work',()=>{
 for(const type of assessmentAssetTypes){
  const phases=buildOwnerPhaseTemplates(type);assert.equal(phases.length,4);
  assert.ok(phases.every(p=>p.paidHours===null&&p.budgetShare===null&&p.remainingExposureCAD===null&&p.releaseMonth===null&&p.plannedFinishMonth===null&&p.basis==='assumption'));
  assert.ok(phases.every(p=>p.sourceRefs.every(s=>s.status==='assumption'&&s.reviewStatus==='owner_input_required')));
  const packages=buildOwnerPackageTemplates(type);assert.ok(packages.every(p=>p.hours===null&&p.budgetCAD===null&&p.uncommittedCAD===null&&p.commitment==='unknown'&&p.catchment===null&&p.predecessors.length===0));
 }
 const first=buildOwnerPackageTemplates('school');first[0].predecessors.push('custom');
 assert.equal(buildOwnerPackageTemplates('school')[0].predecessors.length,0);
});
test('DC project envelopes and dates stay separate from phase construction scope',()=>{
 const cal3=dcPhaseCatalogue.find(p=>p.id==='CAL3_PHASE1');
 assert.equal(cal3.projectId,'ABMP_11416');assert.equal(cal3.wholeProjectEstimateCAD,750e6);
 assert.equal(cal3.phaseConstructionCostCAD,null);assert.equal(cal3.paidHours,null);assert.equal(cal3.defaultCatchment,'unknown');
 assert.equal(cal3.serviceTarget,'H2 2026');assert.match(cal3.reportedWindowQualification,/not observed/);
 assert.ok(dcPhaseCatalogue.every(p=>p.defaultCatchment==='unknown'&&p.phaseConstructionCostCAD===null&&p.paidHours===null));
 const unknown=buildDCPhaseCatalogue([{id:'custom',name:'Custom',region:'Nearby',stage:'Proposed',cost:1e9,start:null,end:null,source:'',asOf:'2026-01-01'}])[0];
 assert.equal(unknown.sourceRefs[0].sha256,undefined);assert.equal(unknown.sourceRefs[0].reviewStatus,'owner_input_required');assert.equal(unknown.reportedStartYear,null);assert.equal(unknown.reportedEndYear,null);assert.equal(unknown.enablingAssetLinks.length,0);
});
test('site-linked enabling evidence preserves unresolved incidence and candidate gate',()=>{
 const links=dcPhaseCatalogue.find(p=>p.id==='CAL3_PHASE1').enablingAssetLinks;
 assert.ok(links.length>=3);assert.ok(links.some(a=>a.id.includes('WATER')));
 for(const asset of links){assert.equal(asset.costCad.value,null);assert.equal(asset.payer.value,null);assert.equal(asset.incrementality.value,null);assert.equal(asset.publicationStatus,'candidate_only');assert.ok(asset.sourceRefs.length>0);assert.ok(asset.sourceRefs.every(s=>s.reviewStatus==='candidate_only'&&s.sha256?.length===64));}
 const water=links.find(a=>a.id.includes('WATER'));assert.equal(water.payerObligations.status,'observed');assert.match(water.payerObligations.note,/not quantified/);
});
test('resource sharing and unsupported uses remain qualified',()=>{
 assert.deepEqual(catchmentOptions.map(c=>c.id),['unknown','Calgary','Edmonton','manual']);
 assert.match(assessmentSupportBoundary.competitionBoundary,/not evidence/);
 assert.match(assessmentSupportBoundary.otherLocationsAndTypes,/Qualitative/);
 assert.match(assessmentSupportBoundary.costBoundary,/never automatically/);
});

test('source field copies are detached and published selection hash retained',()=>{
 const a=buildCAL3EnablingLinks(),b=buildCAL3EnablingLinks();a[0].scope.sourceIds.push('changed');
 assert.ok(!b[0].scope.sourceIds.includes('changed'));
 assert.ok(dcPhaseCatalogue.every(p=>p.sourceRefs[0].sha256?.length===64));
 assert.match(assessmentSupportBoundary.quantitativeUse,/no empirical/);
});
