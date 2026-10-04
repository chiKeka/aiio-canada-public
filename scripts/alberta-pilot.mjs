import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { buildPilotSensitivityInput, pilotEvidence } from '../lib/alberta-pilot.ts';
import { reverseStress } from '../lib/pilot-stress.ts';
const hash = path => createHash('sha256').update(readFileSync(new URL(`../${path}`, import.meta.url))).digest('hex');
const input = buildPilotSensitivityInput();
const report = reverseStress(input);
const result = {
 schemaVersion: '1.0', pilotId: pilotEvidence.pilotId,
 evidenceCutoff: pilotEvidence.evidenceCutoff, publicationStatus: 'scenario_demonstration_not_release_promoted',
 sha256: Object.fromEntries(['data/pilots/alberta-cal3-windsong-v0.1.json','lib/alberta-pilot.ts','lib/pilot-stress.ts','lib/construction-model.ts','scripts/alberta-pilot.mjs'].map(p=>[p,hash(p)])),
 sourceHashes: Object.fromEntries(Object.entries(pilotEvidence.sources).map(([id,s])=>[id,s.sha256])),
 input, caseCount: report.cases.length,
 casesSha256: createHash('sha256').update(JSON.stringify(report.cases)).digest('hex'),
 thresholds: report.thresholds,
 illustrativeCases: report.cases.filter(c=>c.privateMultiplier===1&&c.mobilityHours===0&&c.dcReleaseOffsetMonths===0),
 qualification: report.qualification,
 monetaryImpact: null,
 costBoundary: 'No measured paid hours, capacity, AI phase budget, enabling asset costs, payer commitments or uncommitted public package costs. No dollar impact or causal estimate is authorized.',
};
writeFileSync(new URL('../data/pilots/alberta-cal3-windsong-thresholds-v0.1.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
console.log(`Wrote reproducible pilot threshold artifact (${result.caseCount} discrete scenario cases; monetary impact null).`);
