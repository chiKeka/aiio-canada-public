import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(
  process.env.AIIO_PROJECT_ROOT ?? path.join(scriptDir, '..'),
);
const threadId = '01a0579f-936b-77b3-93e5-be6035628b16';
const outputDir = path.join(projectRoot, 'outputs', threadId);
const previewDir = path.join(projectRoot, 'workbook-work', 'previews');
const workbookBuildVersion = '0.27.0-dev';

const release = JSON.parse(
  await fs.readFile(
    path.join(projectRoot, 'public', 'data', 'latest.json'),
    'utf8',
  ),
);
const aiCapexLedger = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'alberta_ai_capex_announcement_ledger_v0.1.json',
    ),
    'utf8',
  ),
);
const outputPath = path.join(
  outputDir,
  `AIIO_Canada_Research_${workbookBuildVersion}.xlsx`,
);
const costBaseline = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'alberta_bcpi_reference_baseline_v0.1.json',
    ),
    'utf8',
  ),
);
const bcpiRows = parseCsv(
  await fs.readFile(
    path.join(projectRoot, 'data', 'processed', 'bcpi_alberta.csv'),
    'utf8',
  ),
);
const labourRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'labour_availability_alberta.csv',
    ),
    'utf8',
  ),
);
const labourCanadaRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'labour_availability_canada.csv',
    ),
    'utf8',
  ),
);
const workforceCanadaRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'labour_workforce_stock_canada.csv',
    ),
    'utf8',
  ),
);
const materialRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'bcpi_material_cost_screen_alberta.csv',
    ),
    'utf8',
  ),
);
const projectExposureRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'public_project_exposure_alberta.csv',
    ),
    'utf8',
  ),
);
const powerEvidenceRows = parseCsv(
  await fs.readFile(
    path.join(projectRoot, 'data', 'processed', 'power_evidence_alberta.csv'),
    'utf8',
  ),
);
const scenarioDefinition = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'scenarios',
      'alberta_50b_counterfactual_v0.2.json',
    ),
    'utf8',
  ),
);
const powerDefinition = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'scenarios',
      'alberta_power_overlay_v0.1.json',
    ),
    'utf8',
  ),
);
const provincialProjects = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'public_projects_bc_on_qc_intake_v0.1.json',
    ),
    'utf8',
  ),
);
const provincialCostBaseline = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'bc_on_qc_bcpi_reference_baseline_v0.1.json',
    ),
    'utf8',
  ),
);
const provincialPowerPlanning = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'provincial_power_planning_contract_v0.1.json',
    ),
    'utf8',
  ),
);
const digestManifest = JSON.parse(
  await fs.readFile(
    path.join(projectRoot, 'data', 'digests', '2026-09-01.manifest.json'),
    'utf8',
  ),
);
const currentSourceRegistry = JSON.parse(
  await fs.readFile(
    path.join(projectRoot, 'data', 'registry', 'sources.json'),
    'utf8',
  ),
);
const attributionReadiness = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'ai_attribution_identification_readiness_v0.1.json',
    ),
    'utf8',
  ),
);
const attributionContract = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model',
      'ai_attribution_panel_contract_v0.1.json',
    ),
    'utf8',
  ),
);
const attributionPanelPreflight = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'ai_attribution_panel_preflight_v0.1.json',
    ),
    'utf8',
  ),
);
const treatmentSourceFeasibility = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'ai_attribution_treatment_source_feasibility_v0.1.json',
    ),
    'utf8',
  ),
);
const investmentControlReport = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'building_investment_controls_canada_v0.1.json',
    ),
    'utf8',
  ),
);
const investmentControlRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'building_investment_controls_canada.csv',
    ),
    'utf8',
  ),
);
const regionalMacroReport = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'regional_macro_controls_canada_v0.1.json',
    ),
    'utf8',
  ),
);
const regionalMacroRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'regional_macro_controls_canada.csv',
    ),
    'utf8',
  ),
);
const procurementOutcomeReport = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'canadabuys_construction_outcome_feasibility_v0.1.json',
    ),
    'utf8',
  ),
);
const procurementOutcomeRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'canadabuys_construction_outcome_feasibility.csv',
    ),
    'utf8',
  ),
);
const permitProxyReport = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'edmonton_data_centre_permit_proxy_v0.1.json',
    ),
    'utf8',
  ),
);
const permitProxyRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'edmonton_data_centre_permit_proxy.csv',
    ),
    'utf8',
  ),
);
const auditedOutcomes = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'oago_audited_project_outcomes_v0.1.json',
    ),
    'utf8',
  ),
);
const quebecRevisions = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'quebec_pqi_authorized_project_revisions_v0.1.json',
    ),
    'utf8',
  ),
);
const quebecRevisionRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'quebec_pqi_authorized_project_revisions.csv',
    ),
    'utf8',
  ),
);
const quebecFullArchiveContract = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model',
      'quebec_pqi_full_archive_contract_v0.1.json',
    ),
    'utf8',
  ),
);
const quebecFullArchive = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'quebec_pqi_full_archive_longitudinal_v0.1.json',
    ),
    'utf8',
  ),
);
const quebecFullLifecycleRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'quebec_pqi_full_archive_project_lifecycles.csv',
    ),
    'utf8',
  ),
);
const quebecFullTransitionRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'quebec_pqi_full_archive_transitions.csv',
    ),
    'utf8',
  ),
);
const quebecParserReview = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'quebec_pqi_parser_review_package_v0.1.json',
    ),
    'utf8',
  ),
);
const scenarioSuite = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'alberta_50b_scenario_suite_v0.1.json',
    ),
    'utf8',
  ),
);
const historicalCostEnvelope = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'alberta_bcpi_historical_envelope_v0.1.json',
    ),
    'utf8',
  ),
);
const historicalAnalogMatrix = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'alberta_project_historical_analog_matrix_v0.1.json',
    ),
    'utf8',
  ),
);
const referenceCostReview = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'alberta_reference_cost_review_package_v0.1.json',
    ),
    'utf8',
  ),
);
const programGates = JSON.parse(
  await fs.readFile(
    path.join(projectRoot, 'data', 'governance', 'program-gates.json'),
    'utf8',
  ),
);
const informationSectorCapex = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'information_sector_construction_capex_screen_v0.1.json',
    ),
    'utf8',
  ),
);
const informationSectorCapexRows = parseCsv(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'processed',
      'information_sector_construction_capex_canada.csv',
    ),
    'utf8',
  ),
);
const cmaReferenceBaseline = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'vancouver_toronto_montreal_bcpi_reference_baseline_v0.1.json',
    ),
    'utf8',
  ),
);
const provinceLinkedBaseline = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'bc_on_qc_province_linked_reference_baseline_v0.1.json',
    ),
    'utf8',
  ),
);
const canadaCrossDomainCoverage = JSON.parse(
  await fs.readFile(
    path.join(
      projectRoot,
      'data',
      'model-runs',
      'canada_cross_domain_coverage_v0.1.json',
    ),
    'utf8',
  ),
);
const labourPressure = release.labour_pressure;

const workbook = Workbook.create();
const readme = workbook.worksheets.add('Read Me');
const dashboard = workbook.worksheets.add('Dashboard');
const assumptions = workbook.worksheets.add('Assumptions');
const timeline = workbook.worksheets.add('Scenario Timeline');
const pressure = workbook.worksheets.add('Pressure Results');
const sensitivity = workbook.worksheets.add('Sensitivity');
const scenarioVariants = workbook.worksheets.add('Scenario Variants');
const powerOverlay = workbook.worksheets.add('Power Overlay');
const projects = workbook.worksheets.add('AI Projects');
const bcpi = workbook.worksheets.add('BCPI Data');
const labour = workbook.worksheets.add('Labour Availability');
const labourCanada = workbook.worksheets.add('Labour Canada');
const workforceCanada = workbook.worksheets.add('Workforce Stock');
const labourDiagnostic = workbook.worksheets.add('Labour Diagnostic');
const materialScreen = workbook.worksheets.add('Material Screen');
const projectExposure = workbook.worksheets.add('Project Exposure');
const powerEvidence = workbook.worksheets.add('Power Evidence');
const costBaselineSheet = workbook.worksheets.add('Cost Baseline');
const historicalCostSheet = workbook.worksheets.add('Historical Envelope');
const historicalAnalogSheet = workbook.worksheets.add('Historical Analog');
const referenceReviewSheet = workbook.worksheets.add('Reference Review');
const sectorCapexSheet = workbook.worksheets.add('Sector Capex');
const cmaReferenceSheet = workbook.worksheets.add('CMA Reference');
const provinceBridgeSheet = workbook.worksheets.add('Province Bridge');
const projectCost = workbook.worksheets.add('Project Cost Check');
const canadaExpansion = workbook.worksheets.add('Canada Expansion');
const canadaCoverageSheet = workbook.worksheets.add('Canada Coverage');
const attributionGate = workbook.worksheets.add('Attribution Gate');
const panelPreflightSheet = workbook.worksheets.add('Panel Preflight');
const treatmentSourcesSheet = workbook.worksheets.add('Treatment Sources');
const investmentControls = workbook.worksheets.add('Investment Controls');
const regionalMacro = workbook.worksheets.add('Regional Macro');
const procurementIntake = workbook.worksheets.add('Procurement Intake');
const permitProxy = workbook.worksheets.add('Permit Proxy');
const auditedOutcomeSheet = workbook.worksheets.add('Audited Outcomes');
const quebecRevisionSheet = workbook.worksheets.add('Quebec Revisions');
const quebecVintageSheet = workbook.worksheets.add('Quebec Vintages');
const sources = workbook.worksheets.add('Sources');
const checks = workbook.worksheets.add('Release Checks');

const C = {
  navy: '#0B2A36',
  navy2: '#123746',
  teal: '#2F8F83',
  tealDark: '#155D58',
  tealLight: '#DDEDE8',
  paper: '#F5F3EC',
  white: '#FFFFFF',
  ink: '#17343D',
  muted: '#667873',
  line: '#D3DCD6',
  amber: '#D66B35',
  amberLight: '#FFF0E4',
  blueInput: '#0070C0',
  soft: '#EBEEE8',
};

for (const sheet of [
  readme,
  dashboard,
  assumptions,
  timeline,
  pressure,
  sensitivity,
  scenarioVariants,
  powerOverlay,
  projects,
  bcpi,
  labour,
  labourCanada,
  workforceCanada,
  labourDiagnostic,
  materialScreen,
  projectExposure,
  powerEvidence,
  costBaselineSheet,
  historicalCostSheet,
  historicalAnalogSheet,
  referenceReviewSheet,
  sectorCapexSheet,
  cmaReferenceSheet,
  provinceBridgeSheet,
  projectCost,
  canadaExpansion,
  canadaCoverageSheet,
  attributionGate,
  panelPreflightSheet,
  treatmentSourcesSheet,
  investmentControls,
  regionalMacro,
  procurementIntake,
  permitProxy,
  auditedOutcomeSheet,
  quebecRevisionSheet,
  quebecVintageSheet,
  sources,
  checks,
]) {
  sheet.showGridLines = false;
}

await workbook.comments.setSelf({ displayName: 'User' });

buildReadMe();
buildAssumptions();
buildScenarioTimeline();
buildPressureResults();
buildSensitivity();
buildScenarioVariants();
buildPowerOverlay();
buildProjects();
buildBcpi();
buildLabour();
buildLabourCanada();
buildWorkforceCanada();
buildLabourDiagnostic();
buildMaterialScreen();
buildProjectExposure();
buildPowerEvidence();
buildCostBaseline();
buildHistoricalCostEnvelope();
buildHistoricalAnalog();
buildReferenceReview();
buildSectorCapex();
buildCmaReference();
buildProvinceBridge();
buildProjectCostCheck();
buildCanadaExpansion();
buildCanadaCoverage();
buildAttributionGate();
buildPanelPreflight();
buildTreatmentSources();
buildInvestmentControls();
buildRegionalMacro();
buildProcurementIntake();
buildPermitProxy();
buildAuditedOutcomes();
buildQuebecRevisions();
buildQuebecVintages();
buildSources();
buildReleaseChecks();
buildDashboard();

await workbook.comments.addThread(
  { cell: assumptions.getRange('B5') },
  'Scenario-only input. This is not a forecast or a total of committed projects.',
);
await workbook.comments.addThread(
  { cell: assumptions.getRange('B10') },
  'Assumed share of locally captured construction and service demand. Test through sensitivity analysis before interpretation.',
);
await workbook.comments.addThread(
  { cell: assumptions.getRange('C24') },
  'IT load is an independent power-case assumption. It is not derived from capital expenditure.',
);
await workbook.comments.addThread(
  { cell: projectCost.getRange('B8') },
  'Demonstration input only. Replace it with a project estimate stated in the exact price-basis quarter shown below.',
);
await workbook.comments.addThread(
  { cell: projectCost.getRange('B9') },
  'Version 0.1 requires the estimate price basis to match the latest observed baseline quarter. Rebasing is not yet implemented.',
);
await workbook.comments.addThread(
  { cell: historicalAnalogSheet.getRange('B13') },
  'Illustrative price-basis estimate. Replace only with an estimate stated in the June 2026 basis and excluding future escalation already embedded elsewhere.',
);
await workbook.comments.addThread(
  { cell: historicalAnalogSheet.getRange('B14') },
  'YES enables only the historical-path arithmetic translation. It does not authorize a forecast, recommended allowance or AI-attributable increment.',
);

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
workbook.recalculate();

const inspectDashboard = await workbook.inspect({
  kind: 'table',
  range: 'Dashboard!A1:L48',
  include: 'values,formulas',
  tableMaxRows: 48,
  tableMaxCols: 12,
});
console.log(inspectDashboard.ndjson);

const inspectReadMe = await workbook.inspect({
  kind: 'table',
  range: 'Read Me!A1:H59',
  include: 'values,formulas',
  tableMaxRows: 58,
  tableMaxCols: 8,
});
console.log(inspectReadMe.ndjson);

const inspectProjectCost = await workbook.inspect({
  kind: 'table',
  range: 'Project Cost Check!A1:L38',
  include: 'values,formulas',
  tableMaxRows: 38,
  tableMaxCols: 12,
});
console.log(inspectProjectCost.ndjson);

const inspectChecks = await workbook.inspect({
  kind: 'table',
  range: 'Release Checks!A1:D60',
  include: 'values,formulas',
  tableMaxRows: 59,
  tableMaxCols: 4,
});
console.log(inspectChecks.ndjson);

const inspectPanelPreflight = await workbook.inspect({
  kind: 'table',
  range: 'Panel Preflight!A1:J46',
  include: 'values,formulas',
  tableMaxRows: 45,
  tableMaxCols: 10,
});
console.log(inspectPanelPreflight.ndjson);

const inspectTreatmentSources = await workbook.inspect({
  kind: 'table',
  range: 'Treatment Sources!A1:M35',
  include: 'values,formulas',
  tableMaxRows: 35,
  tableMaxCols: 13,
});
console.log(inspectTreatmentSources.ndjson);

const inspectScenarioVariants = await workbook.inspect({
  kind: 'table',
  range: 'Scenario Variants!A1:O42',
  include: 'values,formulas',
  tableMaxRows: 42,
  tableMaxCols: 15,
});
console.log(inspectScenarioVariants.ndjson);

const inspectHistoricalEnvelope = await workbook.inspect({
  kind: 'table',
  range: 'Historical Envelope!A1:S55',
  include: 'values,formulas',
  tableMaxRows: 55,
  tableMaxCols: 19,
});
console.log(inspectHistoricalEnvelope.ndjson);

const inspectHistoricalAnalog = await workbook.inspect({
  kind: 'table',
  range: 'Historical Analog!A1:U38',
  include: 'values,formulas',
  tableMaxRows: 38,
  tableMaxCols: 21,
});
console.log(inspectHistoricalAnalog.ndjson);

const inspectReferenceReview = await workbook.inspect({
  kind: 'table',
  range: 'Reference Review!A1:J40',
  include: 'values,formulas',
  tableMaxRows: 40,
  tableMaxCols: 10,
});
console.log(inspectReferenceReview.ndjson);

const inspectSectorCapex = await workbook.inspect({
  kind: 'table',
  range: 'Sector Capex!A1:T310',
  include: 'values,formulas',
  tableMaxRows: 310,
  tableMaxCols: 20,
});
console.log(inspectSectorCapex.ndjson);

const inspectCmaReference = await workbook.inspect({
  kind: 'table',
  range: 'CMA Reference!A1:W76',
  include: 'values,formulas',
  tableMaxRows: 76,
  tableMaxCols: 23,
});
console.log(inspectCmaReference.ndjson);

const inspectProvinceBridge = await workbook.inspect({
  kind: 'table',
  range: 'Province Bridge!A1:W32',
  include: 'values,formulas',
  tableMaxRows: 32,
  tableMaxCols: 23,
});
console.log(inspectProvinceBridge.ndjson);

const inspectCanadaExpansion = await workbook.inspect({
  kind: 'table',
  range: 'Canada Expansion!A1:J48',
  include: 'values,formulas',
  tableMaxRows: 48,
  tableMaxCols: 10,
});
console.log(inspectCanadaExpansion.ndjson);

const inspectAttributionGate = await workbook.inspect({
  kind: 'table',
  range: 'Attribution Gate!A1:J48',
  include: 'values,formulas',
  tableMaxRows: 48,
  tableMaxCols: 10,
});
console.log(inspectAttributionGate.ndjson);

const inspectInvestmentControls = await workbook.inspect({
  kind: 'table',
  range: 'Investment Controls!A1:R18',
  include: 'values,formulas',
  tableMaxRows: 18,
  tableMaxCols: 18,
});
console.log(inspectInvestmentControls.ndjson);

const inspectRegionalMacro = await workbook.inspect({
  kind: 'table',
  range: 'Regional Macro!A1:S28',
  include: 'values,formulas',
  tableMaxRows: 28,
  tableMaxCols: 19,
});
console.log(inspectRegionalMacro.ndjson);

const inspectProcurementIntake = await workbook.inspect({
  kind: 'table',
  range: 'Procurement Intake!A1:X18',
  include: 'values,formulas',
  tableMaxRows: 18,
  tableMaxCols: 24,
});
console.log(inspectProcurementIntake.ndjson);

const inspectPermitProxy = await workbook.inspect({
  kind: 'table',
  range: 'Permit Proxy!A1:M42',
  include: 'values,formulas',
  tableMaxRows: 42,
  tableMaxCols: 13,
});
console.log(inspectPermitProxy.ndjson);

const inspectAuditedOutcomes = await workbook.inspect({
  kind: 'table',
  range: 'Audited Outcomes!A1:O46',
  include: 'values,formulas',
  tableMaxRows: 46,
  tableMaxCols: 15,
});
console.log(inspectAuditedOutcomes.ndjson);

const inspectQuebecRevisions = await workbook.inspect({
  kind: 'table',
  range: 'Quebec Revisions!A1:R38',
  include: 'values,formulas',
  tableMaxRows: 38,
  tableMaxCols: 18,
});
console.log(inspectQuebecRevisions.ndjson);

const inspectQuebecVintages = await workbook.inspect({
  kind: 'table',
  range: 'Quebec Vintages!A1:V42',
  include: 'values,formulas',
  tableMaxRows: 42,
  tableMaxCols: 22,
});
console.log(inspectQuebecVintages.ndjson);

const errors = await workbook.inspect({
  kind: 'match',
  searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A',
  options: { useRegex: true, maxResults: 300 },
  summary: 'final formula error scan',
});
console.log(errors.ndjson);

const coverageCheck = checks.getRange('B55').values[0][0];
if (coverageCheck !== 'PASS') throw new Error('Canada coverage reconciliation failed');
const errorRecords = errors.ndjson.trim().split('\n').filter(Boolean).map((line) => JSON.parse(line));
if (!errorRecords.some((record) => record.kind === 'notice' && record.message === 'Cell search matched 0 entries.')) {
  throw new Error('Workbook formula scan did not confirm zero errors');
}

const previewRanges = {
  'Read Me': 'A1:H59',
  Dashboard: 'A1:L48',
  Assumptions: 'A1:K38',
  'Scenario Timeline': 'A1:H17',
  'Pressure Results': 'A1:L20',
  Sensitivity: 'A1:M18',
  'Scenario Variants': 'A1:O42',
  'Power Overlay': 'A1:J36',
  'AI Projects': 'A1:AC21',
  'BCPI Data': 'A1:I24',
  'Labour Availability': 'A1:O32',
  'Labour Canada': 'A1:Q28',
  'Workforce Stock': 'A1:S28',
  'Labour Diagnostic': 'A1:N28',
  'Material Screen': 'A1:R38',
  'Project Exposure': 'A1:Y24',
  'Power Evidence': 'A1:H28',
  'Cost Baseline': 'A1:P54',
  'Historical Envelope': 'A1:S55',
  'Historical Analog': 'A1:U38',
  'Reference Review': 'A1:J40',
  'Sector Capex': 'A1:T45',
  'CMA Reference': 'A1:W32',
  'Province Bridge': 'A1:W32',
  'Project Cost Check': 'A1:L38',
  'Canada Expansion': 'A1:J48',
  'Canada Coverage': 'A1:Q42',
  'Attribution Gate': 'A1:J48',
  'Panel Preflight': 'A1:J46',
  'Treatment Sources': 'A1:M35',
  'Investment Controls': 'A1:R28',
  'Regional Macro': 'A1:S28',
  'Procurement Intake': 'A1:X28',
  'Permit Proxy': 'A1:M42',
  'Audited Outcomes': 'A1:O46',
  'Quebec Revisions': 'A1:R38',
  'Quebec Vintages': 'A1:V42',
  Sources: 'A1:J44',
  'Release Checks': 'A1:D60',
};
for (const [sheetName, range] of Object.entries(previewRanges)) {
  const preview = await workbook.render({
    sheetName,
    range,
    scale: 1,
    format: 'png',
  });
  await fs.writeFile(
    path.join(
      previewDir,
      `${sheetName.replaceAll(' ', '_').toLowerCase()}.png`,
    ),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
const inspectPath = `${outputPath}.inspect.ndjson`;
const receiptPath = `${outputPath}.receipt.json`;
const workbookBytes = await fs.readFile(outputPath);
const inspectBytes = await fs.readFile(inspectPath);
const builderBytes = await fs.readFile(fileURLToPath(import.meta.url));
const coverageBytes = await fs.readFile(
  path.join(
    projectRoot,
    'data',
    'model-runs',
    'canada_cross_domain_coverage_v0.1.json',
  ),
);
const workbookReceipt = {
  schema_version: '1.0.0',
  receipt_id: 'AIIO_CANADA_WORKBOOK_BUILD_RECEIPT_0_1',
  workbook_version: workbookBuildVersion,
  public_release_basis: release.manifest.version,
  workbook_path: path.relative(projectRoot, outputPath),
  workbook_sha256: sha256(workbookBytes),
  inspection_path: path.relative(projectRoot, inspectPath),
  inspection_sha256: sha256(inspectBytes),
  builder_path: path.relative(projectRoot, fileURLToPath(import.meta.url)),
  builder_sha256: sha256(builderBytes),
  canada_coverage_path: 'data/model-runs/canada_cross_domain_coverage_v0.1.json',
  canada_coverage_sha256: sha256(coverageBytes),
  worksheet_count: 39,
  required_worksheet: 'Canada Coverage',
  coverage_reconciliation_check_cell: 'Release Checks!B55',
  coverage_reconciliation_status: 'PASS',
  formula_error_match_count: 0,
  publication_boundary: {
    is_frozen_public_release: false,
    research_workbook_only: true,
    cross_province_comparison_authorized: false,
    ai_attributable_effect_authorized: false,
  },
};
await fs.writeFile(receiptPath, `${JSON.stringify(workbookReceipt, null, 2)}\n`);
console.log(JSON.stringify({ outputPath, previewDir, receiptPath }));

function sha256(bytes) {
  return `sha256:${crypto.createHash('sha256').update(bytes).digest('hex')}`;
}

function buildReadMe() {
  titleBand(
    readme,
    'AI Infrastructure Impact Observatory Canada',
    `Canada development workbook ${workbookBuildVersion} · public release basis ${release.manifest.version}`,
    'H',
  );
  readme.getRange('A5:H5').merge();
  readme.getRange('A5').values = [['Purpose']];
  sectionHeader(readme.getRange('A5:H5'));
  readme.getRange('A6:H8').merge();
  readme.getRange('A6').values = [
    [
      'This workbook is an auditable analysis component of AIIO Canada. It reproduces selected public-release outputs, exposes scenario assumptions and carries internal validation plus clearly gated Canada-expansion evidence. The evidence registry, analytical code and immutable artifacts remain the system of record. Research-intake sheets do not change the public release basis, and cost outputs remain withheld until every required model and review gate passes.',
    ],
  ];
  noteBlock(readme.getRange('A6:H8'));

  readme.getRange('A10:B10').values = [['Evidence status', 'Meaning']];
  header(readme.getRange('A10:B10'));
  readme.getRange('A11:B15').values = [
    ['Observed', 'Directly reported by an identified public source.'],
    [
      'Inferred',
      'Derived through a disclosed transformation or classification.',
    ],
    ['Assumed', 'Selected parameter with rationale and sensitivity range.'],
    ['Scenario', 'Counterfactual input or output; not a forecast.'],
    [
      'Withheld',
      'Calculated output is intentionally blank because a required gate did not pass.',
    ],
  ];
  readme.getRange('A11:A15').format.font = { bold: true };
  readme.getRange('A11:B15').format.borders = {
    preset: 'inside',
    style: 'thin',
    color: C.line,
  };

  readme.getRange('A17:H17').merge();
  readme.getRange('A17').values = [['How to use this workbook']];
  sectionHeader(readme.getRange('A17:H17'));
  readme.getRange('A18:H55').values = [
    [
      '1',
      'Dashboard',
      'Read key observed and scenario outputs with their status labels.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '2',
      'Assumptions',
      'Edit blue-font scenario inputs only; formula cells remain black.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '3',
      'Scenario Timeline',
      'Inspect the annual capex decomposition and formula lineage.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '4',
      'Pressure Results',
      'Review the graph engine low/central/high pressure outputs.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '5',
      'Sensitivity',
      'Inspect denominator, absorption, capture, retention and joint stress tests.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '6',
      'Power Overlay',
      'Review the independent MW-based commissioning and transfer proxy.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '7',
      'AI Projects',
      'Inspect public project fields and the inferred AI classification.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '8',
      'BCPI Data',
      'Review the recent Calgary and Edmonton price-index observations.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '9',
      'Labour Availability',
      'Inspect Alberta vacancies, offered wages, quality flags and suppressed cells.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '10',
      'Labour Canada',
      'Compare latest-quarter publication coverage across all provinces and territories.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '11',
      'Workforce Stock',
      'Inspect 2021 Census employed-person counts, reference-week lineage and zero fillers.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '12',
      'Labour Diagnostic',
      'Review the guarded cross-vintage recruitment screen and formula reconciliation.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '13',
      'Material Screen',
      'Inspect selected BCPI component proxies and disclosed change calculations.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '14',
      'Project Exposure',
      'Inspect inferred asset classes, schedule overlap and cost-data coverage.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '15',
      'Power Evidence',
      'Separate AESO requests, limits and contracts from the independent power scenario.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '16',
      'Cost Baseline',
      'Inspect every asset, geography and horizon validation gate; failed projections stay blank.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '17',
      'Project Cost Check',
      'Enter a project and expenditure profile; outputs remain blank unless all gates pass.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '18',
      'Canada Expansion',
      'Inspect current provincial intake summaries and the gates that keep them outside Decision Mode.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '19',
      'Attribution Gate',
      'Inspect the preregistered treatment, outcome, control and diagnostic gates for an AI-attributable effect.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '20',
      'Investment Controls',
      'Inspect the Canada-wide quarterly building-investment control panel and its source lineage.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '21',
      'Procurement Intake',
      'Inspect the CanadaBuys construction linkage and the authorizing outcome fields that remain absent.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '22',
      'Permit Proxy',
      'Inspect Edmonton permit activity, conservative keyword classifications and the non-authorizing treatment boundary.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '23',
      'Audited Outcomes',
      'Inspect hash-locked named project outcomes, component bridges and the fields still missing for attribution.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '24',
      'Quebec Revisions',
      'Inspect stable lifecycle IDs and chain-reconciled authorized cost and completion-month changes; this is not final outturn evidence.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '25',
      'Quebec Vintages',
      'Inspect all 69 official archive dates, adjacent-snapshot disappearances and reentries, source-representation controls and pending parser-review status.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '26',
      'Scenario Variants',
      'Compare four invariant-controlled Alberta $50B stress runs across timing and local capture.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '27',
      'Historical Envelope',
      'Inspect realized one- through five-year BCPI distributions; these are descriptive history, not forecasts or project allowances.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '28',
      'Reference Review',
      'Inspect the hash-locked Alberta E1 reviewer packet, ten required criteria, channel status and the single narrowly eligible horizon.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '29',
      'Sector Capex',
      'Inspect the annual provincial NAICS 51 construction-capex screen and its explicit non-authorizing AI-treatment boundary.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '30',
      'CMA Reference',
      'Inspect the Vancouver, Toronto and Montréal held-out reference-cost results; all values remain withheld pending review.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '31',
      'Sources',
      'Open the current research source register, distinguish release sources and check source vintages.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '32',
      'Release Checks',
      'Confirm formula reconciliations and manifest identity.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '33',
      'Regional Macro',
      'Inspect seven separate Canada-wide quarterly controls and the explicit non-attribution boundary.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '34',
      'Province Bridge',
      'Inspect the CMA-linked pre-2017 provincial history, overlap diagnostics and still-withheld horizon validations.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '35',
      'Historical Analog',
      'Translate a declared Alberta building-project schedule through coherent observed BCPI paths; dollar equivalents are historical stress tests, not forecasts or AI premiums.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '36',
      'Panel Preflight',
      'Inspect the operational acquisition queue, candidate CMA scope, hash-locked evidence receipts and the zero-row estimation boundary.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '37',
      'Treatment Sources',
      'Inspect the eight-source, seven-gate feasibility screen; no candidate currently authorizes AI-attributable cost or delay estimation.',
      '',
      '',
      '',
      '',
      '',
    ],
    [
      '38',
      'Canada Coverage',
      'Inspect the 13-geography, seven-domain availability and missingness inventory; availability does not authorize comparison.',
      '',
      '',
      '',
      '',
      '',
    ],
  ];
  readme.getRange('A18:A55').format.font = { bold: true, color: C.tealDark };
  readme.getRange('B18:B55').format.font = { bold: true };
  readme.getRange('C18:H55').merge(true);
  readme.getRange('A57:H57').merge();
  readme.getRange('A57').values = [['Interpretation boundary']];
  sectionHeader(readme.getRange('A57:H57'), C.amber);
  readme.getRange('A58:H58').merge();
  readme.getRange('A58').values = [
    [
      `WITHHELD FORECAST + UNCALIBRATED AI DIAGNOSTIC. Only 1 of 40 Alberta asset/geography/horizon cost-baseline checks passes; every four- and five-year Alberta health and school reference projection is unavailable. The CMA expansion adds 60 Vancouver, Toronto and Montréal horizon checks: 9 pass internally, 36 fail and 15 are not assessed. The Province Bridge transparently relabels 1,296 pre-2017 CMA-linked values as inferred, preserves 456 official provincial observations and reproduces the same nine internal British Columbia-linked passes; none is an official pre-2017 province observation or an authorized projection. The ${referenceCostReview.required_criteria.length}-criterion Alberta review packet is prepared but has no verdict, and both reviewer channels remain blocked. No forward project-cost result is authorized. The Historical Envelope publishes realized BCPI-window distributions only. The Historical Analog sheet adds ${historicalAnalogMatrix.reference_class_results.reduce((total, item) => total + item.grid.length, 0)} coherent-path schedule combinations and may translate an explicitly confirmed price-basis estimate only as a historical what-if; its markers are not probabilities, forecasts, recommended allowances or AI premiums. The NAICS 51 Sector Capex screen adds ${informationSectorCapex.observation_count} annual Canada/province cells and reports Alberta 2024 actual/revised construction capital of $458.6M, but ${informationSectorCapex.quality_flag_counts.suppressed_confidentiality} cells are suppressed and the broad industry cannot identify AI/data-centre treatment. The Regional Macro sheet adds ${regionalMacroReport.series_count} separate quarterly control series through ${regionalMacroReport.common_latest_period_end}; they are descriptive context, not a composite score, scenario calibration or AI effect. The Edmonton screen finds ${permitProxyReport.data_centre_candidate_count} explicit data-centre permit candidates with ${permitProxyReport.explicit_ai_reference_count} explicit AI references and ${permitProxyReport.data_centre_candidate_occupancy_date_available_count} candidate occupancy dates; publisher-estimated permit values remain activity proxies, not AI capex or realized spend. The Treatment Sources screen tests ${treatmentSourceFeasibility.candidate_count} public-source candidates against ${treatmentSourceFeasibility.required_gate_count} required gates; ${treatmentSourceFeasibility.qualifying_source_count} qualify, so treatment estimation remains unauthorized. Quebec supplies ${quebecRevisions.coverage_summary.cost_revision_chain_reconciled_project_count} reconciled authorized-cost chains and ${quebecRevisions.coverage_summary.schedule_revision_chain_reconciled_project_count} completion-month chains. Its complete ${quebecFullArchive.snapshot_date_count}-date archive contains ${quebecFullArchive.unique_project_count} stable IDs and ${quebecFullArchive.disappearance_event_count} adjacent-snapshot disappearances; publisher-declared complete-service and retirement markers precede ${quebecFullArchive.publisher_declared_retirement_disappearance_event_count}, while ${quebecFullArchive.unclassified_disappearance_event_count} remain unclassified. These are selection diagnostics, not audited exit outcomes, and the ${quebecParserReview.sample_project_count}-project parser review is pending. All AI-attributable cost and delay fields remain null. Pressure scores are not findings, forecasts, probabilities or percentages. The graph is a mechanism layer and is not monetized. Additional transmission for the $50B case remains unknown.`,
    ],
  ];
  readme.getRange('A58:H58').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
  };
  readme.getRange('A58').format.rowHeight = 300;
  setWidths(
    readme,
    { A: 12, B: 30, C: 26, D: 16, E: 16, F: 16, G: 16, H: 16 },
    59,
  );
}

function buildAssumptions() {
  titleBand(
    assumptions,
    'Scenario assumptions',
    'Editable inputs are blue. CAD pressure and MW power remain separate.',
    'K',
  );
  assumptions.getRange('A5:B10').values = [
    [
      'Total AI infrastructure capex (CAD)',
      scenarioDefinition.investment_total_cad,
    ],
    ['Start year', scenarioDefinition.start_year],
    ['End year', scenarioDefinition.end_year],
    ['Delivery years', null],
    ['Currency year', scenarioDefinition.currency_year],
    ['Local capture share', scenarioDefinition.local_capture_share],
  ];
  assumptions.getRange('B8').formulas = [['=B7-B6+1']];
  inputStyle(assumptions.getRange('B5:B7'));
  inputStyle(assumptions.getRange('B9:B10'));
  assumptions.getRange('B5').format.numberFormat = '$#,##0';
  assumptions.getRange('B10').format.numberFormat = '0.0%';
  assumptions.getRange('A5:A10').format.font = { bold: true, color: C.ink };
  assumptions.dataValidations.add({
    range: 'B5',
    rule: { type: 'decimal', operator: 'greaterThanOrEqual', formula1: 0 },
  });
  assumptions.dataValidations.add({
    range: 'B6:B7',
    rule: {
      type: 'whole',
      operator: 'between',
      formula1: 2026,
      formula2: 2050,
    },
  });

  assumptions.getRange('A12:C12').values = [
    ['Capex component', 'Share', 'Evidence status'],
  ];
  header(assumptions.getRange('A12:C12'));
  const components = Object.entries(scenarioDefinition.components);
  assumptions.getRange(`A13:C${12 + components.length}`).values =
    components.map(([name, value]) => [labelize(name), value, 'scenario']);
  inputStyle(assumptions.getRange('B13:B18'));
  assumptions.getRange('B13:B18').format.numberFormat = '0.0%';
  assumptions.getRange('A19:C19').values = [
    ['Component share check', null, 'must equal 100%'],
  ];
  assumptions.getRange('B19').formulas = [['=SUM(B13:B18)']];
  assumptions.getRange('B19').format.numberFormat = '0.0%';
  assumptions.getRange('A19:C19').format = {
    fill: C.soft,
    font: { bold: true, color: C.ink },
    borders: { preset: 'doubleBottom', style: 'thin', color: C.teal },
  };

  assumptions.getRange('A22:K22').values = [
    [
      'Power case',
      'Case status',
      'IT load at full build (MW)',
      'Energy PUE',
      'Peak-to-IT factor',
      'Load factor',
      'Grid share',
      'Peak coincidence',
      'Planning margin',
      'Facility peak (MW)',
      'Transfer proxy (MW)',
    ],
  ];
  header(assumptions.getRange('A22:K22'));
  const powerCases = ['low', 'central', 'high'];
  assumptions.getRange('A23:I25').values = powerCases.map((caseName) => {
    const p = powerDefinition.cases[caseName];
    return [
      caseName,
      'scenario',
      p.it_load_mw_at_full_buildout,
      p.energy_pue,
      p.peak_to_it_factor,
      p.load_factor,
      p.grid_supply_share,
      p.peak_coincidence,
      p.planning_margin,
    ];
  });
  inputStyle(assumptions.getRange('C23:I25'));
  assumptions.getRange('J23').formulas = [['=C23*E23']];
  assumptions.getRange('J23:J25').fillDown();
  assumptions.getRange('K23').formulas = [['=J23*G23*H23*(1+I23)']];
  assumptions.getRange('K23:K25').fillDown();
  assumptions.getRange('C23:C25').format.numberFormat = '#,##0';
  assumptions.getRange('F23:I25').format.numberFormat = '0.0%';
  assumptions.getRange('D23:E25').format.numberFormat = '0.00';
  assumptions.getRange('J23:K25').format.numberFormat = '#,##0.0';

  assumptions.getRange('A28:D28').values = [
    ['Pressure shock denominator', 'CAD', 'Evidence status', 'Purpose'],
  ];
  header(assumptions.getRange('A28:D28'));
  const denominators = Object.entries(
    scenarioDefinition.normalization_denominators_cad,
  );
  assumptions.getRange('A29:D31').values = denominators.map(([name, value]) => [
    labelize(name),
    value,
    'assumed',
    'Converts annual local capex to a dimensionless shock',
  ]);
  inputStyle(assumptions.getRange('B29:B31'));
  assumptions.getRange('B29:B31').format.numberFormat = '$#,##0';

  assumptions.getRange('A34:K37').merge();
  assumptions.getRange('A34').values = [
    [
      `${scenarioDefinition.normalization_note} ${scenarioDefinition.capture_note} ${scenarioDefinition.exclusion_note} ${powerDefinition.assumption_note}`,
    ],
  ];
  noteBlock(assumptions.getRange('A34:K37'));
  assumptions.freezePanes.freezeRows(4);
  setWidths(
    assumptions,
    {
      A: 31,
      B: 16,
      C: 20,
      D: 13,
      E: 15,
      F: 13,
      G: 13,
      H: 15,
      I: 14,
      J: 18,
      K: 19,
    },
    38,
  );
}

function buildScenarioTimeline() {
  titleBand(
    timeline,
    'Alberta $50B scenario timeline',
    'Formula-driven annual decomposition · 2027–2036 counterfactual diagnostic',
    'H',
  );
  timeline.getRange('A4:H4').values = [
    [
      'Year',
      'Annual profile',
      'Total capex (CAD)',
      'Local civil (CAD)',
      'Local electrical & mechanical (CAD)',
      'Local grid construction (CAD)',
      'Excluded from graph (CAD)',
      'Evidence status',
    ],
  ];
  header(timeline.getRange('A4:H4'));
  const years = scenarioDefinition.annual_profile.length;
  timeline.getRange(`B5:B${4 + years}`).values =
    scenarioDefinition.annual_profile.map((value) => [value]);
  inputStyle(timeline.getRange(`B5:B${4 + years}`));
  for (let index = 0; index < years; index += 1) {
    const row = 5 + index;
    timeline.getRange(`A${row}`).formulas = [
      [index === 0 ? "='Assumptions'!B6" : `=A${row - 1}+1`],
    ];
    timeline.getRange(`C${row}`).formulas = [[`='Assumptions'!$B$5*B${row}`]];
    timeline.getRange(`D${row}`).formulas = [
      [
        `=C${row}*('Assumptions'!$B$13+'Assumptions'!$B$14)*'Assumptions'!$B$10`,
      ],
    ];
    timeline.getRange(`E${row}`).formulas = [
      [`=C${row}*'Assumptions'!$B$15*'Assumptions'!$B$10`],
    ];
    timeline.getRange(`F${row}`).formulas = [
      [`=C${row}*'Assumptions'!$B$16*'Assumptions'!$B$10`],
    ];
    timeline.getRange(`G${row}`).formulas = [
      [`=C${row}*('Assumptions'!$B$17+'Assumptions'!$B$18)`],
    ];
    timeline.getRange(`H${row}`).values = [['scenario']];
  }
  const totalRow = 5 + years;
  timeline.getRange(`A${totalRow}:H${totalRow}`).values = [
    ['Total / check', null, null, null, null, null, null, 'scenario'],
  ];
  for (const col of ['B', 'C', 'D', 'E', 'F', 'G'])
    timeline.getRange(`${col}${totalRow}`).formulas = [
      [`=SUM(${col}5:${col}${totalRow - 1})`],
    ];
  timeline.getRange(`A${totalRow}:H${totalRow}`).format = {
    fill: C.soft,
    font: { bold: true, color: C.ink },
    borders: { preset: 'doubleBottom', style: 'thin', color: C.teal },
  };
  timeline.getRange(`B5:B${totalRow}`).format.numberFormat = '0.0%';
  timeline.getRange(`C5:G${totalRow}`).format.numberFormat = '$#,##0';
  timeline.freezePanes.freezeRows(4);
  setWidths(
    timeline,
    { A: 12, B: 15, C: 22, D: 22, E: 30, F: 25, G: 23, H: 18 },
    17,
  );
}

function buildPressureResults() {
  titleBand(
    pressure,
    'Graph pressure results',
    'Uncalibrated structural cases from the immutable scenario release',
    'L',
  );
  pressure.getRange('A4:L4').values = [
    [
      'Node ID',
      'Label',
      'Node type',
      'Low',
      'Low peak year',
      'Central',
      'Central peak year',
      'High',
      'High peak year',
      'Evidence status',
      'Model ID',
      'Interpretation',
    ],
  ];
  header(pressure.getRange('A4:L4'));
  const rows = [
    ...release.scenario.trade_pressure_order,
    ...release.scenario.public_delivery_pressure_order,
  ];
  pressure.getRange(`A5:L${4 + rows.length}`).values = rows.map((item) => [
    item.node_id,
    item.label,
    item.node_type,
    item.low,
    item.low_peak_year,
    item.central,
    item.central_peak_year,
    item.high,
    item.high_peak_year,
    'scenario',
    release.manifest.model_version,
    'Dimensionless pressure score; not a percentage, finding, worker count, cost or delay',
  ]);
  pressure.getRange(`D5:D${4 + rows.length}`).format.numberFormat = '0.00';
  pressure.getRange(`F5:F${4 + rows.length}`).format.numberFormat = '0.00';
  pressure.getRange(`H5:H${4 + rows.length}`).format.numberFormat = '0.00';
  pressure
    .getRange(`F5:F${4 + rows.length}`)
    .conditionalFormats.add('dataBar', { color: C.teal, gradient: true });
  pressure.getRange(`J5:J${4 + rows.length}`).format = {
    fill: C.amberLight,
    font: { color: '#8A4826' },
  };
  pressure.freezePanes.freezeRows(4);
  setWidths(
    pressure,
    {
      A: 37,
      B: 35,
      C: 15,
      D: 10,
      E: 13,
      F: 10,
      G: 15,
      H: 10,
      I: 13,
      J: 18,
      K: 23,
      L: 48,
    },
    20,
  );
}

function buildSensitivity() {
  titleBand(
    sensitivity,
    'Scenario sensitivity',
    'One-at-a-time and joint structural diagnostics · not probability bounds',
    'M',
  );
  sensitivity.getRange('A4:M4').values = [
    [
      'Sensitivity ID',
      'Label',
      'Weight case',
      'Retention case',
      'Denominator multiplier',
      'Absorption adjustment',
      'Local capture',
      'Top resource',
      'Resource score',
      'Peak year',
      'Top public outcome',
      'Outcome score',
      'Peak year',
    ],
  ];
  header(sensitivity.getRange('A4:M4'));
  const rows = release.scenario.sensitivity;
  sensitivity.getRange(`A5:M${4 + rows.length}`).values = rows.map((item) => [
    item.sensitivity_id,
    item.label,
    item.weight_case,
    item.retention_case,
    item.denominator_multiplier,
    item.absorption_adjustment,
    item.local_capture_share,
    item.top_resource.label,
    item.top_resource.pressure_score,
    item.top_resource.calendar_year,
    item.top_public_delivery_outcome.label,
    item.top_public_delivery_outcome.pressure_score,
    item.top_public_delivery_outcome.calendar_year,
  ]);
  sensitivity.getRange(`E5:F${4 + rows.length}`).format.numberFormat = '0.00';
  sensitivity.getRange(`G5:G${4 + rows.length}`).format.numberFormat = '0%';
  sensitivity.getRange(`I5:I${4 + rows.length}`).format.numberFormat = '0.00';
  sensitivity.getRange(`L5:L${4 + rows.length}`).format.numberFormat = '0.00';
  sensitivity
    .getRange(`I5:I${4 + rows.length}`)
    .conditionalFormats.add('dataBar', { color: C.teal, gradient: true });
  sensitivity.freezePanes.freezeRows(4);
  setWidths(
    sensitivity,
    {
      A: 27,
      B: 32,
      C: 14,
      D: 16,
      E: 20,
      F: 20,
      G: 15,
      H: 28,
      I: 15,
      J: 12,
      K: 36,
      L: 15,
      M: 12,
    },
    18,
  );
}

function buildScenarioVariants() {
  titleBand(
    scenarioVariants,
    'Alberta $50B controlled scenario variants',
    'Four versioned stress tests · fixed total and graph · not forecasts or project cost estimates',
    'O',
  );
  scenarioVariants.getRange('A4:L4').values = [[
    'Variant ID',
    'Label',
    'Start year',
    'End year',
    'Delivery years',
    'First-five-year share',
    'Local capture',
    'Peak annual capex (CAD)',
    'Peak year',
    'Local modelled capex (CAD)',
    'Forecast authorized',
    'Cost/delay translation authorized',
  ]];
  header(scenarioVariants.getRange('A4:L4'));
  scenarioVariants.getRange('A5:L8').values = scenarioSuite.variant_summaries.map((item) => [
    item.variant_id,
    item.label,
    item.delivery_start_year,
    item.delivery_end_year,
    null,
    item.first_five_year_capex_share,
    item.local_capture_share,
    item.peak_annual_capex_cad,
    item.peak_annual_capex_year,
    item.local_modelled_capex_cad,
    scenarioSuite.publication_boundary.forecast_authorized ? 'YES' : 'NO',
    scenarioSuite.publication_boundary.project_cost_or_delay_translation_authorized ? 'YES' : 'NO',
  ]);
  scenarioVariants.getRange('E5').formulas = [['=D5-C5+1']];
  scenarioVariants.getRange('E5:E8').fillDown();
  scenarioVariants.getRange('F5:G8').format.numberFormat = '0.0%';
  scenarioVariants.getRange('H5:H8').format.numberFormat = '$#,##0';
  scenarioVariants.getRange('J5:J8').format.numberFormat = '$#,##0';
  scenarioVariants.getRange('K5:L8').format = {
    fill: C.amberLight,
    font: { color: '#8A4826', bold: true },
  };

  scenarioVariants.getRange('A10:O10').merge();
  scenarioVariants.getRange('A10').values = [[
    'Pressure comparison · bounded display = raw / (1 + ABS(raw)); raw scores are dimensionless and unbounded',
  ]];
  sectionHeader(scenarioVariants.getRange('A10:O10'));
  scenarioVariants.getRange('A11:O11').values = [[
    'Node ID', 'Node', 'Type',
    'Staggered raw', 'Staggered display', 'Peak',
    'Front-loaded raw', 'Front-loaded display', 'Peak',
    'Constrained raw', 'Constrained display', 'Peak',
    'High-capture raw', 'High-capture display', 'Peak',
  ]];
  header(scenarioVariants.getRange('A11:O11'));
  scenarioSuite.comparison_matrix.forEach((item, index) => {
    const row = 12 + index;
    const values = Object.fromEntries(item.values.map((value) => [value.variant_id, value]));
    scenarioVariants.getRange(`A${row}:O${row}`).values = [[
      item.node_id,
      item.label,
      item.node_type,
      values.staggered.raw_central_pressure_score,
      null,
      values.staggered.central_peak_year,
      values.front_loaded.raw_central_pressure_score,
      null,
      values.front_loaded.central_peak_year,
      values.constrained_delivery.raw_central_pressure_score,
      null,
      values.constrained_delivery.central_peak_year,
      values.high_local_capture.raw_central_pressure_score,
      null,
      values.high_local_capture.central_peak_year,
    ]];
    scenarioVariants.getRange(`E${row}`).formulas = [[`=D${row}/(1+ABS(D${row}))`]];
    scenarioVariants.getRange(`H${row}`).formulas = [[`=G${row}/(1+ABS(G${row}))`]];
    scenarioVariants.getRange(`K${row}`).formulas = [[`=J${row}/(1+ABS(J${row}))`]];
    scenarioVariants.getRange(`N${row}`).formulas = [[`=M${row}/(1+ABS(M${row}))`]];
  });
  scenarioVariants.getRange('D12:E21').format.numberFormat = '0.000';
  scenarioVariants.getRange('G12:H21').format.numberFormat = '0.000';
  scenarioVariants.getRange('J12:K21').format.numberFormat = '0.000';
  scenarioVariants.getRange('M12:N21').format.numberFormat = '0.000';
  for (const range of ['E12:E21', 'H12:H21', 'K12:K21', 'N12:N21']) {
    scenarioVariants.getRange(range).conditionalFormats.add('dataBar', {
      color: C.teal,
      gradient: true,
    });
  }

  scenarioVariants.getRange('A24:E24').merge();
  scenarioVariants.getRange('A24').values = [['Annual capex profiles (CAD billions)']];
  sectionHeader(scenarioVariants.getRange('A24:E24'));
  scenarioVariants.getRange('A25:E25').values = [[
    'Year', 'Staggered', 'Front-loaded', 'Constrained delivery', 'High local capture',
  ]];
  header(scenarioVariants.getRange('A25:E25'));
  const annualByVariant = Object.fromEntries(
    scenarioSuite.variant_summaries.map((item) => [
      item.variant_id,
      Object.fromEntries(item.annual_capex_profile.map((flow) => [flow.year, flow.total_capex_cad])),
    ]),
  );
  for (let year = 2027; year <= 2041; year += 1) {
    const row = 26 + (year - 2027);
    scenarioVariants.getRange(`A${row}:E${row}`).values = [[
      year,
      annualByVariant.staggered[year] ?? null,
      annualByVariant.front_loaded[year] ?? null,
      annualByVariant.constrained_delivery[year] ?? null,
      annualByVariant.high_local_capture[year] ?? null,
    ]];
  }
  scenarioVariants.getRange('B26:E40').format.numberFormat = '$0.00,,,"B"';
  scenarioVariants.getRange('B26:E40').conditionalFormats.add('dataBar', {
    color: C.teal,
    gradient: true,
  });
  scenarioVariants.getRange('G24:O24').merge();
  scenarioVariants.getRange('G24').values = [['Executive interpretation boundary']];
  sectionHeader(scenarioVariants.getRange('G24:O24'), C.amber);
  scenarioVariants.getRange('G25:O31').merge();
  scenarioVariants.getRange('G25').values = [[
    'Building electricians are the highest-pressure trade in all four declared runs. Front-loading moves their graph peak two years earlier; constrained delivery spreads and delays the peak; high local capture raises the local modelled envelope. These are structural comparisons inside the declared graph. They do not estimate inflation, workforce shortages, project cost escalation, delay duration, probability, power demand or transmission need.',
  ]];
  noteBlock(scenarioVariants.getRange('G25:O31'));
  scenarioVariants.getRange('G33:O38').merge();
  scenarioVariants.getRange('G33').values = [[
    `Source artifact: data/model-runs/alberta_50b_scenario_suite_v0.1.json · suite ${scenarioSuite.suite_id}. The constrained 7.5% annual share is a scenario rule, not a measured Alberta capacity estimate. Power remains in the independent MW overlay.`,
  ]];
  noteBlock(scenarioVariants.getRange('G33:O38'));
  scenarioVariants.freezePanes.freezeRows(11);
  setWidths(
    scenarioVariants,
    {
      A: 31, B: 31, C: 13, D: 15, E: 18,
      F: 13, G: 18, H: 20, I: 11, J: 20,
      K: 13, L: 15, M: 18, N: 18, O: 11,
    },
    42,
  );
}

function buildPowerOverlay() {
  titleBand(
    powerOverlay,
    'Independent Alberta power overlay',
    'MW-based commissioning scenario · separate from the CAD pressure graph',
    'J',
  );
  powerOverlay.getRange('A4:J4').values = [
    [
      'Case',
      'Calendar year',
      'Commissioned share',
      'Cumulative share',
      'IT load (MW)',
      'Grid-coincident demand (MW)',
      'Planning transfer proxy (MW)',
      'Full-build facility peak (MW)',
      'Full-build annual energy (GWh)',
      'Evidence status',
    ],
  ];
  header(powerOverlay.getRange('A4:J4'));
  const rows = [];
  for (const caseName of ['low', 'central', 'high']) {
    const caseRun = release.power_overlay.cases[caseName];
    for (const annual of caseRun.annual) {
      rows.push([
        caseName,
        annual.calendar_year,
        annual.commissioned_share,
        annual.cumulative_commissioned_share,
        annual.it_load_mw,
        annual.grid_coincident_mw,
        annual.planning_transfer_proxy_mw,
        caseRun.full_buildout.facility_peak_mw,
        caseRun.full_buildout.annual_energy_gwh,
        'scenario',
      ]);
    }
  }
  powerOverlay.getRange(`A5:J${4 + rows.length}`).values = rows;
  powerOverlay.getRange(`C5:D${4 + rows.length}`).format.numberFormat = '0.0%';
  powerOverlay.getRange(`E5:I${4 + rows.length}`).format.numberFormat =
    '#,##0.0';
  powerOverlay.getRange(`J5:J${4 + rows.length}`).format = {
    fill: C.amberLight,
    font: { color: '#8A4826' },
  };
  const table = powerOverlay.tables.add(
    `A4:J${4 + rows.length}`,
    true,
    'PowerOverlayTable',
  );
  table.style = 'TableStyleMedium2';
  powerOverlay.freezePanes.freezeRows(4);
  setWidths(
    powerOverlay,
    { A: 12, B: 14, C: 18, D: 18, E: 18, F: 28, G: 29, H: 28, I: 30, J: 18 },
    34,
  );
}

function buildProjects() {
  titleBand(
    projects,
    'Alberta AI-relevant project register',
    'Formal announcement ledger · observed project fields, inferred relevance, and a fail-closed treatment screen',
    'AC',
  );
  const headers = [
    'Project ID',
    'Name',
    'Reported cost (CAD)',
    'Municipality',
    'Start year',
    'End year',
    'Stage',
    'Developer',
    'Project URL',
    'Longitude',
    'Latitude',
    'Location precision',
    'AI relevance',
    'Source status',
    'Classification status',
    'As-of date',
    'Register source URL',
    'Schedule coverage',
    'Treatment screen',
    'Treatment onset available',
    'Treatment dose available',
    'Reported cost status',
    'Power capacity (MW)',
    'Ledger ID',
  ];
  projects.getRange('A4:X4').values = [headers];
  header(projects.getRange('A4:X4'));
  const rows = release.baseline.projects;
  const ledgerByProjectId = new Map(
    aiCapexLedger.records.map((item) => [item.project_id, item]),
  );
  projects.getRange(`A5:X${4 + rows.length}`).values = rows.map((item) => {
    const ledgerRecord = ledgerByProjectId.get(item.project_id);
    if (!ledgerRecord) {
      throw new Error(`AI-capex ledger is missing project ${item.project_id}`);
    }
    return [
      item.project_id,
      item.name,
      item.estimated_cost_cad,
      item.municipality,
      item.start_year,
      item.end_year,
      item.stage,
      item.developer,
      item.project_website,
      item.longitude,
      item.latitude,
      item.location_precision,
      item.ai_relevance,
      item.source_evidence_status,
      item.classification_evidence_status,
      new Date(`${item.as_of_date}T00:00:00Z`),
      'https://www.majorprojects.alberta.ca/',
      ledgerRecord.schedule_status,
      ledgerRecord.treatment_screen_status,
      ledgerRecord.authorizing_treatment_onset_available,
      ledgerRecord.authorizing_treatment_dose_available,
      ledgerRecord.reported_cost_status,
      ledgerRecord.power_generation_capacity_mw,
      aiCapexLedger.ledger_id,
    ];
  });
  projects.getRange(`C5:C${4 + rows.length}`).format.numberFormat = '$#,##0';
  projects.getRange(`J5:K${4 + rows.length}`).format.numberFormat = '0.0000';
  projects.getRange(`P5:P${4 + rows.length}`).format.numberFormat =
    'yyyy-mm-dd';
  projects.getRange(`W5:W${4 + rows.length}`).format.numberFormat = '#,##0.0';
  const table = projects.tables.add(
    `A4:X${4 + rows.length}`,
    true,
    'AIProjectsTable',
  );
  table.style = 'TableStyleMedium2';

  projects.getRange('Z4:AC4').merge();
  projects.getRange('Z4').values = [['Announcement-ledger controls']];
  sectionHeader(projects.getRange('Z4:AC4'));
  projects.getRange('Z5:AC5').values = [
    ['Metric', 'Workbook', 'Artifact', 'Check'],
  ];
  header(projects.getRange('Z5:AC5'));
  const summaryMetrics = [
    ['Ledger ID', null, aiCapexLedger.ledger_id],
    ['Project records', null, aiCapexLedger.record_count],
    [
      'Core data-centre records',
      null,
      aiCapexLedger.coverage_summary.core_data_centre_record_count,
    ],
    [
      'Enabling-power records',
      null,
      aiCapexLedger.coverage_summary.enabling_power_record_count,
    ],
    [
      'Reported estimate records',
      null,
      aiCapexLedger.coverage_summary.reported_estimated_cost_record_count,
    ],
    [
      'Partial known estimates (CAD)',
      null,
      aiCapexLedger.coverage_summary.known_reported_estimated_cost_cad,
    ],
    [
      'Publisher construction candidates',
      null,
      aiCapexLedger.coverage_summary.publisher_construction_stage_candidate_count,
    ],
    [
      'Authorizing treatment onset',
      null,
      aiCapexLedger.coverage_summary.authorizing_treatment_onset_count,
    ],
    [
      'Authorizing treatment dose',
      null,
      aiCapexLedger.coverage_summary.authorizing_treatment_dose_count,
    ],
    [
      'Partial aggregate authorized',
      null,
      aiCapexLedger.publication_boundary.partial_known_reported_cost_aggregate_authorized
        ? 'YES'
        : 'NO',
    ],
    [
      'Realized treatment authorized',
      null,
      aiCapexLedger.publication_boundary.realized_construction_treatment_authorized
        ? 'YES'
        : 'NO',
    ],
  ];
  projects.getRange('Z6:AB16').values = summaryMetrics;
  projects.getRange('AA6:AA16').formulas = [
    ['=X5'],
    [`=COUNTA(A5:A${4 + rows.length})`],
    [`=COUNTIF(M5:M${4 + rows.length},"core_data_centre")`],
    [`=COUNTIF(M5:M${4 + rows.length},"enabling_power")`],
    [`=COUNT(C5:C${4 + rows.length})`],
    [`=SUM(C5:C${4 + rows.length})`],
    [
      `=COUNTIF(S5:S${4 + rows.length},"publisher_stage_indicates_construction_activity_candidate")`,
    ],
    [`=COUNTIF(T5:T${4 + rows.length},TRUE)`],
    [`=COUNTIF(U5:U${4 + rows.length},TRUE)`],
    [
      aiCapexLedger.publication_boundary
        .partial_known_reported_cost_aggregate_authorized
        ? '="YES"'
        : '="NO"',
    ],
    [
      aiCapexLedger.publication_boundary.realized_construction_treatment_authorized
        ? '="YES"'
        : '="NO"',
    ],
  ];
  projects.getRange('AC6').formulas = [['=IF(AA6=AB6,"PASS","FAIL")']];
  projects.getRange('AC6:AC16').fillDown();
  projects.getRange('AA11:AB11').format.numberFormat = '$#,##0';
  projects.getRange('AA6:AC16').format.borders = {
    preset: 'inside',
    style: 'thin',
    color: C.line,
  };
  projects.getRange('AC6:AC16').conditionalFormats.add('containsText', {
    text: 'PASS',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  projects.getRange('AC6:AC16').conditionalFormats.add('containsText', {
    text: 'FAIL',
    format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
  });
  projects.getRange('Z18:AC21').merge();
  projects.getRange('Z18').values = [[
    'Boundary: the $55.41B total is a partial sum of reported estimates for 10 of 22 records. Missing costs are not zero; enabling power is separate; no probability weighting is applied; publisher stage does not establish realized construction onset or spend.',
  ]];
  noteBlock(projects.getRange('Z18:AC21'));
  projects.freezePanes.freezeRows(4);
  projects.freezePanes.freezeColumns(2);
  setWidths(
    projects,
    {
      A: 15,
      B: 39,
      C: 20,
      D: 22,
      E: 12,
      F: 12,
      G: 19,
      H: 31,
      I: 36,
      J: 13,
      K: 13,
      L: 17,
      M: 21,
      N: 15,
      O: 20,
      P: 14,
      Q: 36,
      R: 24,
      S: 34,
      T: 24,
      U: 23,
      V: 24,
      W: 20,
      X: 34,
      Y: 3,
      Z: 34,
      AA: 20,
      AB: 20,
      AC: 14,
    },
    30,
  );
}

function buildBcpi() {
  titleBand(
    bcpi,
    'Alberta construction-price evidence',
    'Recent Calgary and Edmonton observations from Statistics Canada table 18-10-0289-01',
    'I',
  );
  const selected = bcpiRows
    .filter((row) =>
      [
        'BCPI_NON_RESIDENTIAL_BUILDINGS_622_DIVISION_COMPOSITE',
        'BCPI_SCHOOL_DIVISION_COMPOSITE',
      ].includes(row.indicator_id),
    )
    .sort((a, b) =>
      `${a.indicator_id}|${a.geography_id}|${a.period_end}`.localeCompare(
        `${b.indicator_id}|${b.geography_id}|${b.period_end}`,
      ),
    );
  const recent = [];
  for (const key of new Set(
    selected.map((row) => `${row.indicator_id}|${row.geography_id}`),
  )) {
    recent.push(
      ...selected
        .filter((row) => `${row.indicator_id}|${row.geography_id}` === key)
        .slice(-12),
    );
  }
  bcpi.getRange('A4:I4').values = [
    [
      'Observation ID',
      'Indicator ID',
      'Geography ID',
      'Period end',
      'Value',
      'Unit',
      'Evidence status',
      'Source ID',
      'Source URL',
    ],
  ];
  header(bcpi.getRange('A4:I4'));
  bcpi.getRange(`A5:I${4 + recent.length}`).values = recent.map((row) => [
    row.observation_id,
    row.indicator_id,
    row.geography_id,
    new Date(`${row.period_end}T00:00:00Z`),
    Number(row.value),
    row.unit,
    row.evidence_status,
    row.source_id,
    'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810028901',
  ]);
  bcpi.getRange(`D5:D${4 + recent.length}`).format.numberFormat = 'yyyy-mm-dd';
  bcpi.getRange(`E5:E${4 + recent.length}`).format.numberFormat = '0.0';
  const table = bcpi.tables.add(
    `A4:I${4 + recent.length}`,
    true,
    'BCPIEvidenceTable',
  );
  table.style = 'TableStyleMedium2';
  bcpi.freezePanes.freezeRows(4);
  bcpi.freezePanes.freezeColumns(2);
  setWidths(
    bcpi,
    { A: 29, B: 48, C: 16, D: 14, E: 12, F: 22, G: 17, H: 28, I: 45 },
    24,
  );
}

function buildLabour() {
  titleBand(
    labour,
    'Alberta trade labour evidence',
    'Statistics Canada table 14-10-0444-01 · missing and suppressed values remain blank',
    'O',
  );
  const headers = [
    'Observation ID',
    'NOC',
    'Occupation',
    'Model trade node',
    'Statistic',
    'Value',
    'Unit',
    'Period start',
    'Period end',
    'Evidence status',
    'Source ID',
    'Transformation ID',
    'Quality flags',
    'Source URL',
    'Missingness check',
  ];
  labour.getRange('A4:O4').values = [headers];
  header(labour.getRange('A4:O4'));
  const ordered = [...labourRows].sort((a, b) => {
    const periodOrder = b.period_end.localeCompare(a.period_end);
    return (
      periodOrder ||
      `${a.trade_node_id}|${a.noc_code}|${a.statistic}`.localeCompare(
        `${b.trade_node_id}|${b.noc_code}|${b.statistic}`,
      )
    );
  });
  labour.getRange(`A5:O${4 + ordered.length}`).values = ordered.map((row) => [
    row.observation_id,
    row.noc_code,
    row.occupation_label,
    row.trade_node_id,
    row.statistic,
    row.value === '' ? null : Number(row.value),
    row.unit,
    new Date(`${row.period_start}T00:00:00Z`),
    new Date(`${row.period_end}T00:00:00Z`),
    row.evidence_status,
    row.source_id,
    row.transformation_id,
    row.quality_flags,
    'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410044401',
    row.value !== '' ||
    row.quality_flags.includes('value_missing_or_suppressed')
      ? 'PASS'
      : 'FAIL',
  ]);
  labour.getRange(`F5:F${4 + ordered.length}`).format.numberFormat = '0.00';
  labour.getRange(`H5:I${4 + ordered.length}`).format.numberFormat =
    'yyyy-mm-dd';
  labour
    .getRange(`O5:O${4 + ordered.length}`)
    .conditionalFormats.add('containsText', {
      text: 'PASS',
      format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
    });
  labour
    .getRange(`O5:O${4 + ordered.length}`)
    .conditionalFormats.add('containsText', {
      text: 'FAIL',
      format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
    });
  const table = labour.tables.add(
    `A4:O${4 + ordered.length}`,
    true,
    'LabourAvailabilityTable',
  );
  table.style = 'TableStyleMedium2';
  labour.freezePanes.freezeRows(4);
  labour.freezePanes.freezeColumns(3);
  setWidths(
    labour,
    {
      A: 29,
      B: 10,
      C: 46,
      D: 24,
      E: 31,
      F: 13,
      G: 13,
      H: 14,
      I: 14,
      J: 17,
      K: 28,
      L: 31,
      M: 38,
      N: 45,
      O: 18,
    },
    26,
  );
}

function buildLabourCanada() {
  const national = release.baseline.labour_availability_canada;
  titleBand(
    labourCanada,
    'Canada provincial trade labour evidence',
    `Statistics Canada table 14-10-0444-01 · latest quarter ${national.period_end} · national totals excluded`,
    'Q',
  );

  const coverage = [...national.coverage].sort((a, b) =>
    a.geography_label.localeCompare(b.geography_label),
  );
  labourCanada.getRange('A4:I4').values = [
    [
      'Geography ID',
      'Province / territory',
      'Reported cells',
      'Not published',
      'Total cells',
      'Coverage',
      'Expected reported',
      'Expected not published',
      'Reconciliation',
    ],
  ];
  header(labourCanada.getRange('A4:I4'));
  const coverageEnd = 4 + coverage.length;
  const latestRows = labourCanadaRows
    .filter((row) => row.period_end === national.period_end)
    .sort((a, b) =>
      `${a.geography_id}|${a.trade_node_id}|${a.noc_code}|${a.statistic}`.localeCompare(
        `${b.geography_id}|${b.trade_node_id}|${b.noc_code}|${b.statistic}`,
      ),
    );
  const warningRow = coverageEnd + 3;
  const headerRow = warningRow + 1;
  const observationStart = headerRow + 1;
  const observationEnd = observationStart + latestRows.length - 1;
  coverage.forEach((item, index) => {
    const row = 5 + index;
    labourCanada.getRange(`A${row}:B${row}`).values = [
      [item.geography_id, item.geography_label],
    ];
    labourCanada.getRange(`C${row}`).formulas = [
      [
        `=COUNTIFS($B$${observationStart}:$B$${observationEnd},$A${row},$I$${observationStart}:$I$${observationEnd},"<>")`,
      ],
    ];
    labourCanada.getRange(`D${row}`).formulas = [
      [
        `=COUNTIF($B$${observationStart}:$B$${observationEnd},$A${row})-C${row}`,
      ],
    ];
    labourCanada.getRange(`E${row}`).formulas = [[`=C${row}+D${row}`]];
    labourCanada.getRange(`F${row}`).formulas = [
      [`=IF(E${row}=0,0,C${row}/E${row})`],
    ];
    labourCanada.getRange(`G${row}:H${row}`).values = [
      [item.observed_cells, item.not_published_cells],
    ];
    labourCanada.getRange(`I${row}`).formulas = [
      [`=IF(AND(C${row}=G${row},D${row}=H${row}),"PASS","FAIL")`],
    ];
  });
  labourCanada.getRange(`F5:F${coverageEnd}`).format.numberFormat = '0.0%';
  labourCanada
    .getRange(`F5:F${coverageEnd}`)
    .conditionalFormats.add('colorScale', {
      colors: ['#F6D5C2', '#F4E7B2', '#B7DED3'],
      thresholds: ['min', '50%', 'max'],
    });
  labourCanada
    .getRange(`I5:I${coverageEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'PASS',
      format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
    });
  labourCanada
    .getRange(`I5:I${coverageEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'FAIL',
      format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
    });
  const coverageTable = labourCanada.tables.add(
    `A4:I${coverageEnd}`,
    true,
    'LabourCanadaCoverageTable',
  );
  coverageTable.style = 'TableStyleMedium2';

  labourCanada.getRange(`A${warningRow}:Q${warningRow}`).merge();
  labourCanada.getRange(`A${warningRow}`).values = [[national.warning]];
  noteBlock(labourCanada.getRange(`A${warningRow}:Q${warningRow}`));
  labourCanada.getRange(`A${warningRow}`).format.rowHeight = 42;
  labourCanada.getRange(`A${headerRow}:Q${headerRow}`).values = [
    [
      'Observation ID',
      'Geography ID',
      'Province / territory',
      'StatCan DGUID',
      'NOC',
      'Occupation',
      'Model trade node',
      'Statistic',
      'Value',
      'Unit',
      'Period end',
      'Evidence status',
      'Source ID',
      'Transformation ID',
      'Quality flags',
      'Source URL',
      'Missingness check',
    ],
  ];
  header(labourCanada.getRange(`A${headerRow}:Q${headerRow}`));
  labourCanada.getRange(`A${observationStart}:Q${observationEnd}`).values =
    latestRows.map((row) => [
      row.observation_id,
      row.geography_id,
      row.geography_label,
      row.statcan_dguid,
      row.noc_code,
      row.occupation_label,
      row.trade_node_id,
      row.statistic,
      row.value === '' ? null : Number(row.value),
      row.unit,
      new Date(`${row.period_end}T00:00:00Z`),
      row.evidence_status,
      row.source_id,
      row.transformation_id,
      row.quality_flags,
      'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410044401',
      row.value !== '' ||
      row.quality_flags.includes('value_missing_or_suppressed')
        ? 'PASS'
        : 'FAIL',
    ]);
  labourCanada.getRange(
    `I${observationStart}:I${observationEnd}`,
  ).format.numberFormat = '0.00';
  labourCanada.getRange(
    `K${observationStart}:K${observationEnd}`,
  ).format.numberFormat = 'yyyy-mm-dd';
  labourCanada
    .getRange(`Q${observationStart}:Q${observationEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'PASS',
      format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
    });
  labourCanada
    .getRange(`Q${observationStart}:Q${observationEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'FAIL',
      format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
    });
  const observationsTable = labourCanada.tables.add(
    `A${headerRow}:Q${observationEnd}`,
    true,
    'LabourCanadaLatestTable',
  );
  observationsTable.style = 'TableStyleMedium2';
  labourCanada.freezePanes.freezeRows(headerRow);
  labourCanada.freezePanes.freezeColumns(3);
  setWidths(
    labourCanada,
    {
      A: 28,
      B: 15,
      C: 28,
      D: 20,
      E: 10,
      F: 44,
      G: 24,
      H: 31,
      I: 13,
      J: 13,
      K: 14,
      L: 17,
      M: 28,
      N: 38,
      O: 40,
      P: 45,
      Q: 18,
    },
    28,
  );
}

function buildWorkforceCanada() {
  const national = release.baseline.labour_workforce_stock_canada;
  titleBand(
    workforceCanada,
    'Canada detailed-trade workforce stock',
    `2021 Census reference week ${national.period_start} to ${national.period_end} · six NOC unit groups · national totals excluded`,
    'S',
  );
  const coverage = [...national.coverage].sort((a, b) =>
    a.geography_label.localeCompare(b.geography_label),
  );
  workforceCanada.getRange('A4:J4').values = [
    [
      'Geography ID',
      'Province / territory',
      'Published cells',
      'Zero fillers',
      'Total cells',
      'Coverage',
      'Expected published',
      'Expected zero',
      'Expected total',
      'Reconciliation',
    ],
  ];
  header(workforceCanada.getRange('A4:J4'));
  const coverageEnd = 4 + coverage.length;
  const warningRow = coverageEnd + 3;
  const headerRow = warningRow + 1;
  const observationStart = headerRow + 1;
  const ordered = [...workforceCanadaRows].sort((a, b) =>
    `${a.geography_id}|${a.trade_node_id}|${a.noc_code}`.localeCompare(
      `${b.geography_id}|${b.trade_node_id}|${b.noc_code}`,
    ),
  );
  const observationEnd = observationStart + ordered.length - 1;
  coverage.forEach((item, index) => {
    const row = 5 + index;
    workforceCanada.getRange(`A${row}:B${row}`).values = [
      [item.geography_id, item.geography_label],
    ];
    workforceCanada.getRange(`C${row}`).formulas = [
      [`=COUNTIF($B$${observationStart}:$B$${observationEnd},$A${row})`],
    ];
    workforceCanada.getRange(`D${row}`).formulas = [
      [
        `=COUNTIFS($B$${observationStart}:$B$${observationEnd},$A${row},$R$${observationStart}:$R$${observationEnd},"YES")`,
      ],
    ];
    workforceCanada.getRange(`E${row}`).formulas = [[`=C${row}`]];
    workforceCanada.getRange(`F${row}`).formulas = [
      [`=IF(I${row}=0,0,C${row}/I${row})`],
    ];
    workforceCanada.getRange(`G${row}:I${row}`).values = [
      [item.published_cells, item.zero_filler_cells, item.total_cells],
    ];
    workforceCanada.getRange(`J${row}`).formulas = [
      [
        `=IF(AND(C${row}=G${row},D${row}=H${row},E${row}=I${row}),"PASS","FAIL")`,
      ],
    ];
  });
  workforceCanada.getRange(`F5:F${coverageEnd}`).format.numberFormat = '0.0%';
  workforceCanada
    .getRange(`J5:J${coverageEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'PASS',
      format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
    });
  workforceCanada
    .getRange(`J5:J${coverageEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'FAIL',
      format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
    });
  const coverageTable = workforceCanada.tables.add(
    `A4:J${coverageEnd}`,
    true,
    'WorkforceCanadaCoverageTable',
  );
  coverageTable.style = 'TableStyleMedium2';

  workforceCanada.getRange(`A${warningRow}:S${warningRow}`).merge();
  workforceCanada.getRange(`A${warningRow}`).values = [[national.warning]];
  noteBlock(workforceCanada.getRange(`A${warningRow}:S${warningRow}`));
  workforceCanada.getRange(`A${warningRow}`).format.rowHeight = 48;
  workforceCanada.getRange(`A${headerRow}:S${headerRow}`).values = [
    [
      'Observation ID',
      'Geography ID',
      'Province / territory',
      'StatCan DGUID',
      'NOC',
      'Occupation',
      'Model trade node',
      'Statistic',
      'Employed persons',
      'Unit',
      'Period start',
      'Period end',
      'Release date',
      'Evidence status',
      'Source ID',
      'Transformation ID',
      'Quality flags',
      'Zero filler',
      'Cell check',
    ],
  ];
  header(workforceCanada.getRange(`A${headerRow}:S${headerRow}`));
  workforceCanada.getRange(`A${observationStart}:R${observationEnd}`).values =
    ordered.map((row) => [
      row.observation_id,
      row.geography_id,
      row.geography_label,
      row.statcan_dguid,
      row.noc_code,
      row.occupation_label,
      row.trade_node_id,
      row.statistic,
      Number(row.value),
      row.unit,
      new Date(`${row.period_start}T00:00:00Z`),
      new Date(`${row.period_end}T00:00:00Z`),
      new Date(`${row.release_date}T00:00:00Z`),
      row.evidence_status,
      row.source_id,
      row.transformation_id,
      row.quality_flags,
      row.quality_flags.includes('census_zero_filler') ? 'YES' : 'NO',
    ]);
  workforceCanada.getRange(`S${observationStart}`).formulas = [
    [
      `=IF(OR(AND(I${observationStart}>0,R${observationStart}="NO"),AND(I${observationStart}=0,R${observationStart}="YES")),"PASS","FAIL")`,
    ],
  ];
  workforceCanada
    .getRange(`S${observationStart}:S${observationEnd}`)
    .fillDown();
  workforceCanada.getRange(
    `I${observationStart}:I${observationEnd}`,
  ).format.numberFormat = '#,##0';
  workforceCanada.getRange(
    `K${observationStart}:M${observationEnd}`,
  ).format.numberFormat = 'yyyy-mm-dd';
  workforceCanada
    .getRange(`S${observationStart}:S${observationEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'PASS',
      format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
    });
  workforceCanada
    .getRange(`S${observationStart}:S${observationEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'FAIL',
      format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
    });
  const observationsTable = workforceCanada.tables.add(
    `A${headerRow}:S${observationEnd}`,
    true,
    'WorkforceCanadaTable',
  );
  observationsTable.style = 'TableStyleMedium2';
  workforceCanada.freezePanes.freezeRows(headerRow);
  workforceCanada.freezePanes.freezeColumns(3);
  setWidths(
    workforceCanada,
    {
      A: 29,
      B: 15,
      C: 28,
      D: 20,
      E: 10,
      F: 46,
      G: 24,
      H: 15,
      I: 18,
      J: 12,
      K: 14,
      L: 14,
      M: 14,
      N: 17,
      O: 35,
      P: 41,
      Q: 45,
      R: 13,
      S: 15,
    },
    28,
  );
}

function buildLabourDiagnostic() {
  titleBand(
    labourDiagnostic,
    'Cross-vintage labour recruitment screen',
    `Current JVWS vacancies (${labourPressure.vacancy_period_end}) per 1,000 employed persons in the 2021 Census · inferred screening metric`,
    'N',
  );
  const albertaRows = labourPressure.trade_diagnostics
    .filter((item) => item.geography_id === 'PR_48')
    .sort((a, b) => {
      const aValue = a.vacancies_per_1_000_2021_employed;
      const bValue = b.vacancies_per_1_000_2021_employed;
      if (aValue === null && bValue !== null) return 1;
      if (aValue !== null && bValue === null) return -1;
      return (bValue ?? -1) - (aValue ?? -1);
    });
  labourDiagnostic.getRange('A4:G4').values = [
    [
      'Alberta model trade',
      'Current vacancies',
      '2021 employed stock',
      'Per 1,000',
      'Complete cells',
      'Availability',
      'Evidence status',
    ],
  ];
  header(labourDiagnostic.getRange('A4:G4'));
  labourDiagnostic.getRange(`A5:G${4 + albertaRows.length}`).values =
    albertaRows.map((item) => [
      tradeLabel(item.trade_node_id),
      item.vacancies,
      item.workforce_stock,
      item.vacancies_per_1_000_2021_employed,
      `${item.complete_cells} of ${item.component_cells}`,
      labelize(item.availability),
      item.evidence_status,
    ]);
  labourDiagnostic.getRange(
    `B5:C${4 + albertaRows.length}`,
  ).format.numberFormat = '#,##0';
  labourDiagnostic.getRange(
    `D5:D${4 + albertaRows.length}`,
  ).format.numberFormat = '0.00';
  const albertaTable = labourDiagnostic.tables.add(
    `A4:G${4 + albertaRows.length}`,
    true,
    'AlbertaLabourDiagnosticTable',
  );
  albertaTable.style = 'TableStyleMedium2';

  const warningRow = 4 + albertaRows.length + 2;
  labourDiagnostic.getRange(`A${warningRow}:N${warningRow}`).merge();
  labourDiagnostic.getRange(`A${warningRow}`).values = [
    [
      `${labourPressure.interpretation} ${labourPressure.limitations.join(' ')}`,
    ],
  ];
  labourDiagnostic.getRange(`A${warningRow}:N${warningRow}`).format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  labourDiagnostic.getRange(`A${warningRow}`).format.rowHeight = 70;

  const headerRow = warningRow + 2;
  const observationStart = headerRow + 1;
  const ordered = [...labourPressure.occupation_diagnostics].sort((a, b) =>
    `${a.geography_id}|${a.trade_node_id}|${a.noc_code}`.localeCompare(
      `${b.geography_id}|${b.trade_node_id}|${b.noc_code}`,
    ),
  );
  const observationEnd = observationStart + ordered.length - 1;
  labourDiagnostic.getRange(`A${headerRow}:N${headerRow}`).values = [
    [
      'Geography ID',
      'Province / territory',
      'NOC',
      'Occupation',
      'Model trade node',
      'Current vacancies',
      'Vacancy period end',
      '2021 employed stock',
      'Workforce period end',
      'Workbook per 1,000',
      'Published per 1,000',
      'Availability',
      'Evidence status',
      'Formula check',
    ],
  ];
  header(labourDiagnostic.getRange(`A${headerRow}:N${headerRow}`));
  labourDiagnostic.getRange(`A${observationStart}:I${observationEnd}`).values =
    ordered.map((item) => [
      item.geography_id,
      item.geography_label,
      item.noc_code,
      item.occupation_label,
      item.trade_node_id,
      item.vacancies,
      new Date(`${item.vacancy_period_end}T00:00:00Z`),
      item.workforce_stock,
      new Date(`${item.workforce_period_end}T00:00:00Z`),
    ]);
  labourDiagnostic.getRange(`K${observationStart}:M${observationEnd}`).values =
    ordered.map((item) => [
      item.vacancies_per_1_000_2021_employed,
      labelize(item.availability),
      item.evidence_status,
    ]);
  labourDiagnostic.getRange(`J${observationStart}`).formulas = [
    [
      `=IF(OR(F${observationStart}="",H${observationStart}<=0),"",ROUND(F${observationStart}/H${observationStart}*1000,2))`,
    ],
  ];
  labourDiagnostic
    .getRange(`J${observationStart}:J${observationEnd}`)
    .fillDown();
  labourDiagnostic.getRange(`N${observationStart}`).formulas = [
    [
      `=IF(K${observationStart}="",IF(J${observationStart}="","PASS","FAIL"),IF(ABS(J${observationStart}-K${observationStart})<0.01,"PASS","FAIL"))`,
    ],
  ];
  labourDiagnostic
    .getRange(`N${observationStart}:N${observationEnd}`)
    .fillDown();
  labourDiagnostic.getRange(
    `F${observationStart}:F${observationEnd}`,
  ).format.numberFormat = '#,##0';
  labourDiagnostic.getRange(
    `H${observationStart}:H${observationEnd}`,
  ).format.numberFormat = '#,##0';
  labourDiagnostic.getRange(
    `G${observationStart}:G${observationEnd}`,
  ).format.numberFormat = 'yyyy-mm-dd';
  labourDiagnostic.getRange(
    `I${observationStart}:I${observationEnd}`,
  ).format.numberFormat = 'yyyy-mm-dd';
  labourDiagnostic.getRange(
    `J${observationStart}:K${observationEnd}`,
  ).format.numberFormat = '0.00';
  labourDiagnostic
    .getRange(`N${observationStart}:N${observationEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'PASS',
      format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
    });
  labourDiagnostic
    .getRange(`N${observationStart}:N${observationEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'FAIL',
      format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
    });
  const observationsTable = labourDiagnostic.tables.add(
    `A${headerRow}:N${observationEnd}`,
    true,
    'LabourDiagnosticTable',
  );
  observationsTable.style = 'TableStyleMedium2';
  labourDiagnostic.freezePanes.freezeRows(headerRow);
  labourDiagnostic.freezePanes.freezeColumns(2);
  setWidths(
    labourDiagnostic,
    {
      A: 15,
      B: 28,
      C: 10,
      D: 47,
      E: 24,
      F: 18,
      G: 17,
      H: 18,
      I: 18,
      J: 18,
      K: 18,
      L: 25,
      M: 17,
      N: 15,
    },
    28,
  );
}

function buildMaterialScreen() {
  titleBand(
    materialScreen,
    'Alberta material-cost component screen',
    `Selected Calgary and Edmonton BCPI proxies · period ending ${release.material_cost_screen.period_end} · not AI-attributed effects`,
    'R',
  );
  const headers = [
    'Geography ID',
    'Building archetype',
    'Component',
    'Indicator ID',
    'Period end',
    'Index value',
    'Unit',
    'Points from 2023 base',
    'Prior-quarter end',
    'Prior-quarter index',
    'QoQ change',
    'Year-ago end',
    'Year-ago index',
    'YoY change',
    'Source ID',
    'Source status',
    'Change status',
    'Source URL',
  ];
  materialScreen.getRange('A4:R4').values = [headers];
  header(materialScreen.getRange('A4:R4'));
  const ordered = [...materialRows].sort((a, b) =>
    `${a.geography_id}|${a.archetype}|${a.component}`.localeCompare(
      `${b.geography_id}|${b.archetype}|${b.component}`,
    ),
  );
  const endRow = 4 + ordered.length;
  materialScreen.getRange(`A5:R${endRow}`).values = ordered.map((row) => [
    row.geography_id,
    labelize(row.archetype),
    labelize(row.component),
    row.indicator_id,
    new Date(`${row.period_end}T00:00:00Z`),
    Number(row.index_value),
    row.unit,
    Number(row.index_points_since_2023_base),
    new Date(`${row.previous_quarter_period_end}T00:00:00Z`),
    Number(row.previous_quarter_index),
    row.quarter_over_quarter_percent_change === ''
      ? null
      : Number(row.quarter_over_quarter_percent_change) / 100,
    new Date(`${row.year_ago_period_end}T00:00:00Z`),
    row.year_ago_index === '' ? null : Number(row.year_ago_index),
    row.year_over_year_percent_change === ''
      ? null
      : Number(row.year_over_year_percent_change) / 100,
    row.source_id,
    row.source_evidence_status,
    row.change_evidence_status,
    'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810028901',
  ]);
  materialScreen.getRange(`E5:E${endRow}`).format.numberFormat = 'yyyy-mm-dd';
  materialScreen.getRange(`F5:F${endRow}`).format.numberFormat = '0.0';
  materialScreen.getRange(`H5:H${endRow}`).format.numberFormat = '0.0';
  materialScreen.getRange(`I5:I${endRow}`).format.numberFormat = 'yyyy-mm-dd';
  materialScreen.getRange(`J5:J${endRow}`).format.numberFormat = '0.0';
  materialScreen.getRange(`K5:K${endRow}`).format.numberFormat = '0.0%';
  materialScreen.getRange(`L5:L${endRow}`).format.numberFormat = 'yyyy-mm-dd';
  materialScreen.getRange(`M5:M${endRow}`).format.numberFormat = '0.0';
  materialScreen.getRange(`N5:N${endRow}`).format.numberFormat = '0.0%';
  materialScreen
    .getRange(`N5:N${endRow}`)
    .conditionalFormats.add('colorScale', {
      colors: ['#B7DED3', '#F4E7B2', '#F6D5C2'],
      thresholds: ['min', '50%', 'max'],
    });
  const table = materialScreen.tables.add(
    `A4:R${endRow}`,
    true,
    'MaterialScreenTable',
  );
  table.style = 'TableStyleMedium2';
  materialScreen.freezePanes.freezeRows(4);
  materialScreen.freezePanes.freezeColumns(3);
  setWidths(
    materialScreen,
    {
      A: 15,
      B: 31,
      C: 27,
      D: 54,
      E: 14,
      F: 13,
      G: 18,
      H: 18,
      I: 16,
      J: 17,
      K: 14,
      L: 14,
      M: 15,
      N: 14,
      O: 28,
      P: 16,
      Q: 16,
      R: 45,
    },
    endRow,
  );
}

function buildProjectExposure() {
  titleBand(
    projectExposure,
    'Alberta public-delivery asset exposure',
    `Controlled classification + schedule-overlap screen · ${release.public_project_exposure.window.start_year}–${release.public_project_exposure.window.end_year} · not a delay finding`,
    'Y',
  );
  projectExposure.getRange('A4:J4').values = [
    [
      'Asset class',
      'Records',
      'Overlap',
      'Cost records',
      'Reported cost (CAD)',
      'Costed + dated overlap',
      'Cost allocated to window (CAD)',
      'Public sponsor signals',
      'Utility signals',
      'Unresolved sponsor signals',
    ],
  ];
  header(projectExposure.getRange('A4:J4'));
  const summaries = release.public_project_exposure.asset_class_summaries;
  const summaryEnd = 4 + summaries.length;
  projectExposure.getRange(`A5:J${summaryEnd}`).values = summaries.map(
    (item) => [
      labelize(item.asset_class),
      item.project_count,
      item.overlap_project_count,
      item.reported_cost_project_count,
      item.reported_cost_cad,
      item.overlap_with_cost_and_complete_schedule_count,
      item.indicative_cost_allocated_to_window_cad,
      item.government_or_public_institution_signal_count,
      item.municipal_or_public_utility_signal_count,
      item.unresolved_sponsor_signal_count,
    ],
  );
  projectExposure.getRange(`B5:D${summaryEnd}`).format.numberFormat = '#,##0';
  projectExposure.getRange(`E5:E${summaryEnd}`).format.numberFormat = '$#,##0';
  projectExposure.getRange(`F5:F${summaryEnd}`).format.numberFormat = '#,##0';
  projectExposure.getRange(`G5:G${summaryEnd}`).format.numberFormat = '$#,##0';
  projectExposure.getRange(`H5:J${summaryEnd}`).format.numberFormat = '#,##0';
  const summaryTable = projectExposure.tables.add(
    `A4:J${summaryEnd}`,
    true,
    'ProjectExposureSummaryTable',
  );
  summaryTable.style = 'TableStyleMedium2';

  projectExposure.getRange('A12:Y12').merge();
  projectExposure.getRange('A12').values = [
    [
      'Asset class, sponsor signal and uniform cost allocation are disclosed inferences. Incomplete schedules remain indeterminate. Reported-cost totals are not probability-weighted budgets or expenditure forecasts.',
    ],
  ];
  noteBlock(projectExposure.getRange('A12:Y12'));
  projectExposure.getRange('A12').format.rowHeight = 34;

  const headers = [
    'Project ID',
    'Name',
    'Asset class',
    'Asset class status',
    'Project type',
    'Sector',
    'Developer',
    'Sponsor signal',
    'Sponsor status',
    'Municipality',
    'Stage',
    'Reported cost (CAD)',
    'Start year',
    'End year',
    'Overlap status',
    'Overlap years',
    'Annualized cost if complete (CAD)',
    'Cost allocated to window (CAD)',
    'Longitude',
    'Latitude',
    'Location precision',
    'Source ID',
    'Source status',
    'As-of date',
    'Source URL',
  ];
  projectExposure.getRange('A14:Y14').values = [headers];
  header(projectExposure.getRange('A14:Y14'));
  const endRow = 14 + projectExposureRows.length;
  projectExposure.getRange(`A15:Y${endRow}`).values = projectExposureRows.map(
    (row) => [
      row.project_id,
      row.name,
      labelize(row.asset_class),
      row.asset_class_evidence_status,
      row.project_type,
      row.sector,
      row.developer,
      labelize(row.sponsor_signal),
      row.sponsor_signal_evidence_status,
      row.municipality,
      row.stage,
      numberOrNull(row.estimated_cost_cad),
      numberOrNull(row.start_year),
      numberOrNull(row.end_year),
      row.schedule_overlap_status,
      row.overlap_years,
      numberOrNull(row.annualized_cost_cad_if_complete),
      numberOrNull(row.indicative_cost_allocated_to_window_cad),
      numberOrNull(row.longitude),
      numberOrNull(row.latitude),
      row.location_precision,
      row.source_id,
      row.source_evidence_status,
      new Date(`${row.as_of_date}T00:00:00Z`),
      'https://www.majorprojects.alberta.ca/',
    ],
  );
  projectExposure.getRange(`L15:L${endRow}`).format.numberFormat = '$#,##0';
  projectExposure.getRange(`M15:N${endRow}`).format.numberFormat = '0';
  projectExposure.getRange(`Q15:R${endRow}`).format.numberFormat = '$#,##0';
  projectExposure.getRange(`S15:T${endRow}`).format.numberFormat = '0.0000';
  projectExposure.getRange(`X15:X${endRow}`).format.numberFormat = 'yyyy-mm-dd';
  const table = projectExposure.tables.add(
    `A14:Y${endRow}`,
    true,
    'ProjectExposureTable',
  );
  table.style = 'TableStyleMedium2';
  projectExposure.freezePanes.freezeRows(14);
  projectExposure.freezePanes.freezeColumns(3);
  setWidths(
    projectExposure,
    {
      A: 15,
      B: 44,
      C: 31,
      D: 17,
      E: 27,
      F: 18,
      G: 38,
      H: 36,
      I: 17,
      J: 24,
      K: 19,
      L: 20,
      M: 12,
      N: 12,
      O: 32,
      P: 19,
      Q: 27,
      R: 27,
      S: 13,
      T: 13,
      U: 18,
      V: 28,
      W: 15,
      X: 14,
      Y: 39,
    },
    endRow,
  );
}

function buildPowerEvidence() {
  titleBand(
    powerEvidence,
    'Observed AESO data-centre power boundary',
    'Requested load, Phase 1 allocation and executed contracts · separate from the AIIO MW scenario',
    'H',
  );
  powerEvidence.getRange('A5:A10').values = [
    ['Latest requested load (MW)'],
    ['Phase 1 interim limit (MW)'],
    ['Phase 1 allocated contracts (MW)'],
    ['Executed contract sum (MW)'],
    ['$50B additional transmission (MW)'],
    ['Phase 1 reconciliation'],
  ];
  powerEvidence.getRange('A5:A10').format.font = { bold: true, color: C.ink };
  powerEvidence.getRange('B5').formulas = [['=C19']];
  powerEvidence.getRange('B6').formulas = [['=C20']];
  powerEvidence.getRange('B7').formulas = [['=C21']];
  powerEvidence.getRange('B8').formulas = [['=SUM(C22:C23)']];
  powerEvidence.getRange('B9').values = [['UNKNOWN']];
  powerEvidence.getRange('B10').formulas = [
    ['=IF(AND(B6=B7,B7=B8),"PASS","FAIL")'],
  ];
  powerEvidence.getRange('B5:B10').format = {
    fill: C.soft,
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };
  powerEvidence.getRange('B5:B8').format.numberFormat = '#,##0.0';
  powerEvidence.getRange('B10').conditionalFormats.add('containsText', {
    text: 'PASS',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  powerEvidence.getRange('B10').conditionalFormats.add('containsText', {
    text: 'FAIL',
    format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
  });

  powerEvidence.getRange('D5:H10').merge();
  powerEvidence.getRange('D5').values = [
    [
      `${release.power_evidence.requested_load.warning} Requested load, allocated limits, executed contracts, connected load and forecasts are different quantities. AESO's no-reinforcement statement applies only to its scoped 1,200 MW interim approach through 2028 on the existing transmission system. Additional transmission for the separate $50B counterfactual remains unknown pending locations, connection studies and a system needs assessment.`,
    ],
  ];
  powerEvidence.getRange('D5:H10').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  powerEvidence.getRange('A13:H13').values = [
    [
      'Metric ID',
      'Period',
      'Value',
      'Unit',
      'Evidence status',
      'Source ID',
      'Source locator',
      'Source URL',
    ],
  ];
  header(powerEvidence.getRange('A13:H13'));
  const endRow = 13 + powerEvidenceRows.length;
  powerEvidence.getRange(`A14:H${endRow}`).values = powerEvidenceRows.map(
    (row) => [
      row.metric_id,
      row.period,
      Number(row.value),
      row.unit,
      row.evidence_status,
      row.source_id,
      row.source_locator,
      powerSourceUrl(row.source_id),
    ],
  );
  powerEvidence.getRange(`C14:C${endRow}`).format.numberFormat = '#,##0.000';
  const table = powerEvidence.tables.add(
    `A13:H${endRow}`,
    true,
    'PowerEvidenceTable',
  );
  table.style = 'TableStyleMedium2';
  powerEvidence.freezePanes.freezeRows(13);
  powerEvidence.freezePanes.freezeColumns(2);
  setWidths(
    powerEvidence,
    { A: 47, B: 17, C: 16, D: 13, E: 17, F: 47, G: 53, H: 54 },
    28,
  );
}

function buildCostBaseline() {
  titleBand(
    costBaselineSheet,
    'Validated market-reference cost baseline',
    `Internal model artifact · as of ${costBaseline.as_of_date} · public projections withheld`,
    'P',
  );

  costBaselineSheet.getRange('A5:B8').values = [
    ['Baseline model ID', costBaseline.model_id],
    [
      'Public projection authorized',
      costBaseline.publication_authorization.public_projection_authorized
        ? 'YES'
        : 'NO',
    ],
    [
      'Horizon checks passed',
      costBaseline.publication_summary.horizon_status_counts.gate_passed,
    ],
    [
      'Total horizon checks',
      costBaseline.publication_summary.horizon_result_count,
    ],
  ];
  costBaselineSheet.getRange('A5:A8').format.font = {
    bold: true,
    color: C.ink,
  };
  costBaselineSheet.getRange('B5:B8').format = {
    fill: C.soft,
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };
  costBaselineSheet.getRange('B6').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  costBaselineSheet.getRange('D5:P8').merge();
  costBaselineSheet.getRange('D5').values = [
    [
      'FAIL-CLOSED RESULT. Only one of 40 reference-class horizon checks passes. All Calgary and Edmonton four- and five-year health and school projections are null. The one passing horizon is not publishable until the independent modelling review gate authorizes it. These are shared-market BCPI reference classes, not AI effects and not realized project-cost forecasts.',
    ],
  ];
  costBaselineSheet.getRange('D5:P8').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  const baselineRows = costBaseline.reference_class_results.flatMap(
    (reference) =>
      reference.horizons.map((horizon) => [
        reference.asset_class,
        reference.asset_class_label,
        reference.geography_id,
        reference.geography_label,
        horizon.horizon_years,
        horizon.status,
        horizon.selected_method,
        horizon.validation_period?.selected_method_metrics
          ?.mean_absolute_percentage_error ?? null,
        horizon.validation_period?.selected_method_metrics
          ?.mean_percentage_error ?? null,
        horizon.validation_period?.empirical_interval_coverage_percent ?? null,
        horizon.projected_cumulative_change_percent,
        horizon.projected_index,
        horizon.reason,
        reference.latest_index,
        reference.reference_indicator_id,
        reference.mapping_status,
      ]),
  );
  costBaselineSheet.getRange('A10:P10').values = [
    [
      'Asset class',
      'Asset label',
      'Geography ID',
      'Geography',
      'Horizon (years)',
      'Gate status',
      'Selected method',
      'Validation MAPE (%)',
      'Validation bias (%)',
      'Interval coverage (%)',
      'Projected change (%)',
      'Projected index',
      'Failure reason',
      'Latest observed index',
      'Reference indicator ID',
      'Mapping status',
    ],
  ];
  header(costBaselineSheet.getRange('A10:P10'));
  const baselineEndRow = 10 + baselineRows.length;
  costBaselineSheet.getRange(`A11:P${baselineEndRow}`).values = baselineRows;
  costBaselineSheet.getRange(`E11:E${baselineEndRow}`).format.numberFormat =
    '0';
  costBaselineSheet.getRange(`H11:L${baselineEndRow}`).format.numberFormat =
    '0.000';
  costBaselineSheet.getRange(`N11:N${baselineEndRow}`).format.numberFormat =
    '0.0';
  costBaselineSheet
    .getRange(`F11:F${baselineEndRow}`)
    .conditionalFormats.add('containsText', {
      text: 'gate_passed',
      format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
    });
  costBaselineSheet
    .getRange(`F11:F${baselineEndRow}`)
    .conditionalFormats.add('containsText', {
      text: 'gate_failed',
      format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
    });
  const baselineTable = costBaselineSheet.tables.add(
    `A10:P${baselineEndRow}`,
    true,
    'CostBaselineGateTable',
  );
  baselineTable.style = 'TableStyleMedium2';
  costBaselineSheet
    .getRange(`A${baselineEndRow + 2}:P${baselineEndRow + 4}`)
    .merge();
  costBaselineSheet.getRange(`A${baselineEndRow + 2}`).values = [
    [costBaseline.publication_authorization.reason],
  ];
  noteBlock(
    costBaselineSheet.getRange(`A${baselineEndRow + 2}:P${baselineEndRow + 4}`),
  );
  costBaselineSheet.freezePanes.freezeRows(10);
  costBaselineSheet.freezePanes.freezeColumns(4);
  setWidths(
    costBaselineSheet,
    {
      A: 22,
      B: 22,
      C: 15,
      D: 18,
      E: 14,
      F: 16,
      G: 24,
      H: 18,
      I: 18,
      J: 19,
      K: 19,
      L: 17,
      M: 34,
      N: 19,
      O: 46,
      P: 16,
    },
    baselineEndRow + 4,
  );
}

function buildHistoricalCostEnvelope() {
  titleBand(
    historicalCostSheet,
    'Historical construction-cost envelope',
    `Observed BCPI history + inferred descriptive summaries · as of ${historicalCostEnvelope.as_of_date} · not a forecast`,
    'S',
  );
  const historicalRows = historicalCostEnvelope.reference_class_results.flatMap(
    (reference) => reference.horizons.map((horizon) => [
      reference.asset_class,
      reference.asset_class_label,
      reference.geography_id,
      reference.geography_label,
      horizon.horizon_years,
      horizon.interpretation_status,
      horizon.overlapping_window_count,
      horizon.non_overlapping_window_count,
      horizon.historical_cumulative_change_percent.minimum,
      horizon.historical_cumulative_change_percent.p10,
      horizon.historical_cumulative_change_percent.p25,
      horizon.historical_cumulative_change_percent.p50,
      horizon.historical_cumulative_change_percent.p75,
      horizon.historical_cumulative_change_percent.p90,
      horizon.historical_cumulative_change_percent.maximum,
      horizon.latest_realized_cumulative_change_percent,
      horizon.latest_realized_percentile_rank,
      null,
      currentSourceRegistry.sources.find(
        (item) => item.source_id === historicalCostEnvelope.source_id,
      )?.canonical_url ?? '',
    ]),
  );
  historicalCostSheet.getRange('A5:B9').values = [
    ['Envelope model ID', historicalCostEnvelope.model_id],
    ['Reference series', historicalCostEnvelope.reference_class_results.length],
    ['Horizon summaries', historicalRows.length],
    ['Latest observation', historicalCostEnvelope.as_of_date],
    ['Source ID', historicalCostEnvelope.source_id],
  ];
  historicalCostSheet.getRange('A5:A9').format.font = { bold: true, color: C.ink };
  historicalCostSheet.getRange('B5:B9').format = {
    fill: C.soft,
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };
  historicalCostSheet.getRange('D5:E8').values = [
    ['Historical summary authorized', historicalCostEnvelope.publication_authorization.historical_summary_authorized ? 'YES' : 'NO'],
    ['Future projection authorized', historicalCostEnvelope.publication_authorization.future_projection_authorized ? 'YES' : 'NO'],
    ['Project-cost translation authorized', historicalCostEnvelope.publication_authorization.project_cost_translation_authorized ? 'YES' : 'NO'],
    ['AI-attributable effect authorized', historicalCostEnvelope.publication_authorization.ai_attributable_effect_authorized ? 'YES' : 'NO'],
  ];
  historicalCostSheet.getRange('D5:D8').format.font = { bold: true, color: C.ink };
  historicalCostSheet.getRange('E5').format = { fill: C.tealLight, font: { bold: true, color: C.tealDark } };
  historicalCostSheet.getRange('E6:E8').format = { fill: C.amberLight, font: { bold: true, color: '#8A4826' } };
  historicalCostSheet.getRange('G5:S9').merge();
  historicalCostSheet.getRange('G5').values = [[
    'DESCRIPTIVE HISTORY ONLY. Quantiles summarize realized changes across overlapping historical windows. They are not probabilities, forecasts or project allowances. The existing held-out forecast gate remains unchanged, project-cost translation remains blank and no AI-attributable increment is estimated.',
  ]];
  historicalCostSheet.getRange('G5:S9').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  historicalCostSheet.getRange('A11:S11').values = [[
    'Asset class', 'Asset label', 'Geography ID', 'Geography', 'Horizon (years)',
    'History status', 'Overlapping windows', 'Non-overlapping windows',
    'Minimum change (%)', 'P10 change (%)', 'P25 change (%)', 'Median change (%)',
    'P75 change (%)', 'P90 change (%)', 'Maximum change (%)',
    'Latest realized change (%)', 'Latest percentile rank', 'Median annualized', 'Source URL',
  ]];
  header(historicalCostSheet.getRange('A11:S11'));
  const historicalEndRow = 11 + historicalRows.length;
  historicalCostSheet.getRange(`A12:S${historicalEndRow}`).values = historicalRows;
  for (let row = 12; row <= historicalEndRow; row += 1) {
    historicalCostSheet.getRange(`R${row}`).formulas = [[`=(1+L${row}/100)^(1/E${row})-1`]];
  }
  historicalCostSheet.getRange(`E12:E${historicalEndRow}`).format.numberFormat = '0';
  historicalCostSheet.getRange(`G12:H${historicalEndRow}`).format.numberFormat = '#,##0';
  historicalCostSheet.getRange(`I12:Q${historicalEndRow}`).format.numberFormat = '0.0';
  historicalCostSheet.getRange(`R12:R${historicalEndRow}`).format.numberFormat = '0.0%';
  historicalCostSheet.getRange(`F12:F${historicalEndRow}`).conditionalFormats.add('containsText', {
    text: 'historical_context_available',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  historicalCostSheet.getRange(`F12:F${historicalEndRow}`).conditionalFormats.add('containsText', {
    text: 'limited_history_only',
    format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } },
  });
  historicalCostSheet.getRange(`J12:N${historicalEndRow}`).conditionalFormats.add('dataBar', {
    color: C.teal,
    gradient: true,
  });
  const historicalTable = historicalCostSheet.tables.add(
    `A11:S${historicalEndRow}`,
    true,
    'HistoricalCostEnvelopeTable',
  );
  historicalTable.style = 'TableStyleMedium2';
  historicalCostSheet.getRange(`A${historicalEndRow + 2}:S${historicalEndRow + 4}`).merge();
  historicalCostSheet.getRange(`A${historicalEndRow + 2}`).values = [[
    'Interpretation: p10 and p90 mark the middle 80% of realized historical changes, not an 80% prediction interval. Overlapping windows are serially dependent. Roads, water/resilience and regulated utilities remain not assessed because the available BCPI model-building references are not fit-for-purpose cost indexes for those assets.',
  ]];
  noteBlock(historicalCostSheet.getRange(`A${historicalEndRow + 2}:S${historicalEndRow + 4}`));
  historicalCostSheet.freezePanes.freezeRows(11);
  historicalCostSheet.freezePanes.freezeColumns(4);
  setWidths(
    historicalCostSheet,
    {
      A: 30, B: 31, C: 15, D: 18, E: 14, F: 27, G: 20, H: 22,
      I: 18, J: 16, K: 16, L: 18, M: 16, N: 16, O: 18, P: 23,
      Q: 20, R: 18, S: 52,
    },
    historicalEndRow + 4,
  );
}

function buildHistoricalAnalog() {
  titleBand(
    historicalAnalogSheet,
    'Project historical-path stress test',
    `Coherent observed BCPI trajectories · as of ${historicalAnalogMatrix.as_of_date} · not a forecast or AI premium`,
    'U',
  );
  const sourceUrl = currentSourceRegistry.sources.find(
    (item) => item.source_id === historicalAnalogMatrix.source_id,
  )?.canonical_url ?? '';
  const analogRows = historicalAnalogMatrix.reference_class_results.flatMap(
    (reference) => reference.grid.map((item) => {
      const factors = item.schedule_weighted_factor;
      return [
        reference.asset_class,
        reference.asset_class_label,
        reference.geography_id,
        reference.geography_label,
        item.start_lag_years,
        item.duration_years,
        item.profile_id,
        item.status,
        item.overlapping_trajectory_count,
        item.non_overlapping_trajectory_count,
        factors?.minimum ?? null,
        factors?.p10 ?? null,
        factors?.p25 ?? null,
        factors?.p50 ?? null,
        factors?.p75 ?? null,
        factors?.p90 ?? null,
        factors?.maximum ?? null,
        sourceUrl,
        reference.mapping_status,
        item.expenditure_schedule
          .map((entry) => `${entry.horizon_years}y:${(entry.share * 100).toFixed(1)}%`)
          .join(' · '),
        `${reference.asset_class}|${reference.geography_id}|${item.start_lag_years}|${item.duration_years}|${item.profile_id}`,
      ];
    }),
  );
  const boundary = historicalAnalogMatrix.publication_authorization;
  historicalAnalogSheet.getRange('A5:B9').values = [
    ['Matrix model ID', historicalAnalogMatrix.model_id],
    ['Reference series', historicalAnalogMatrix.reference_class_results.length],
    ['Schedule combinations', analogRows.length],
    ['Latest observation', historicalAnalogMatrix.as_of_date],
    ['Source ID', historicalAnalogMatrix.source_id],
  ];
  historicalAnalogSheet.getRange('A5:A9').format.font = { bold: true, color: C.ink };
  historicalAnalogSheet.getRange('B5:B9').format = {
    fill: C.soft,
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };
  historicalAnalogSheet.getRange('D5:E10').values = [
    ['Historical stress test authorized', boundary.historical_analog_stress_test_authorized ? 'YES' : 'NO'],
    ['Historical budget translation authorized', boundary.historical_analog_budget_translation_authorized ? 'YES' : 'NO'],
    ['Future projection authorized', boundary.future_projection_authorized ? 'YES' : 'NO'],
    ['Probability interval authorized', boundary.probability_interval_authorized ? 'YES' : 'NO'],
    ['Recommended allowance authorized', boundary.recommended_escalation_allowance_authorized ? 'YES' : 'NO'],
    ['AI-attributable effect authorized', boundary.ai_attributable_effect_authorized ? 'YES' : 'NO'],
  ];
  historicalAnalogSheet.getRange('D5:D10').format.font = { bold: true, color: C.ink };
  historicalAnalogSheet.getRange('E5:E6').format = { fill: C.tealLight, font: { bold: true, color: C.tealDark } };
  historicalAnalogSheet.getRange('E7:E10').format = { fill: C.amberLight, font: { bold: true, color: '#8A4826' } };
  historicalAnalogSheet.getRange('G5:U10').merge();
  historicalAnalogSheet.getRange('G5').values = [[
    'HISTORICAL WHAT-IF ONLY. Each marker weights a complete observed price path through the declared expenditure schedule. The dollar equivalents are arithmetic translations of the illustrative June 2026 price-basis estimate. They are not probabilities, forecast bounds, recommended contingencies, realized project-cost estimates or an AI-attributable increment. Graph pressure scores are not added.',
  ]];
  historicalAnalogSheet.getRange('G5:U10').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  historicalAnalogSheet.getRange('A12:B12').merge();
  historicalAnalogSheet.getRange('A12').values = [['Illustrative project inputs']];
  sectionHeader(historicalAnalogSheet.getRange('A12:B12'));
  historicalAnalogSheet.getRange('A13:B20').values = [
    ['Price-basis estimate (CAD)', 1_200_000_000],
    ['June 2026 basis confirmed', 'YES'],
    ['Asset class', 'health_facilities'],
    ['Geography ID', 'CMA_835'],
    ['Start lag (years)', 3],
    ['Duration (years)', 5],
    ['Expenditure profile', 'even'],
    ['Lookup key', null],
  ];
  historicalAnalogSheet.getRange('A13:A20').format.font = { bold: true, color: C.ink };
  historicalAnalogSheet.getRange('B13:B19').format = {
    fill: '#EAF4FB',
    font: { color: C.blueInput },
    borders: { preset: 'outside', style: 'thin', color: '#AFCBDD' },
  };
  historicalAnalogSheet.getRange('B13').format.numberFormat = '$#,##0';
  historicalAnalogSheet.getRange('B20').formulas = [[
    '=B15&"|"&B16&"|"&B17&"|"&B18&"|"&B19',
  ]];
  historicalAnalogSheet.getRange('B20').format = {
    fill: C.soft,
    font: { name: 'Aptos Mono', size: 8, color: C.muted },
  };
  historicalAnalogSheet.getRange('B14').dataValidation = { rule: { type: 'list', values: ['YES', 'NO'] } };
  historicalAnalogSheet.getRange('B15').dataValidation = { rule: { type: 'list', values: historicalAnalogMatrix.reference_class_results.filter((item, index, list) => list.findIndex((candidate) => candidate.asset_class === item.asset_class) === index).map((item) => item.asset_class) } };
  historicalAnalogSheet.getRange('B16').dataValidation = { rule: { type: 'list', values: ['CMA_825', 'CMA_835'] } };
  historicalAnalogSheet.getRange('B17').dataValidation = { rule: { type: 'whole', operator: 'between', formula1: 0, formula2: 10 } };
  historicalAnalogSheet.getRange('B18').dataValidation = { rule: { type: 'whole', operator: 'between', formula1: 1, formula2: 10 } };
  historicalAnalogSheet.getRange('B19').dataValidation = { rule: { type: 'list', values: historicalAnalogMatrix.configuration.profile_ids } };

  historicalAnalogSheet.getRange('D12:G12').merge();
  historicalAnalogSheet.getRange('D12').values = [['Schedule-weighted historical markers']];
  sectionHeader(historicalAnalogSheet.getRange('D12:G12'));
  historicalAnalogSheet.getRange('D13:G17').values = [
    ['', 'Lower · p10', 'Median', 'Upper · p90'],
    ['Factor', null, null, null],
    ['Change from price basis', null, null, null],
    ['Budget equivalent', null, null, null],
    ['Increment vs estimate', null, null, null],
  ];
  header(historicalAnalogSheet.getRange('D13:G13'));
  historicalAnalogSheet.getRange('D14:D17').format.font = { bold: true, color: C.ink };
  const analogEndRow = 23 + analogRows.length;
  const analogCriteriaArgs = `$A$24:$A$${analogEndRow},$B$15,$C$24:$C$${analogEndRow},$B$16,$E$24:$E$${analogEndRow},$B$17,$F$24:$F$${analogEndRow},$B$18,$G$24:$G$${analogEndRow},$B$19`;
  const factorColumns = ['L', 'N', 'P'];
  factorColumns.forEach((sourceColumn, index) => {
    const outputColumn = ['E', 'F', 'G'][index];
    historicalAnalogSheet.getRange(`${outputColumn}14`).formulas = [[
      `=IF(COUNTIFS(${analogCriteriaArgs})=1,SUMIFS($${sourceColumn}$24:$${sourceColumn}$${analogEndRow},${analogCriteriaArgs}),"")`,
    ]];
    historicalAnalogSheet.getRange(`${outputColumn}15`).formulas = [[
      `=IF(ISNUMBER(${outputColumn}14),${outputColumn}14-1,"")`,
    ]];
    historicalAnalogSheet.getRange(`${outputColumn}16`).formulas = [[
      `=IF(AND($B$14="YES",ISNUMBER(${outputColumn}14)),$B$13*${outputColumn}14,"")`,
    ]];
    historicalAnalogSheet.getRange(`${outputColumn}17`).formulas = [[
      `=IF(ISNUMBER(${outputColumn}16),${outputColumn}16-$B$13,"")`,
    ]];
  });
  historicalAnalogSheet.getRange('E14:G14').format.numberFormat = '0.000';
  historicalAnalogSheet.getRange('E15:G15').format.numberFormat = '0.0%';
  historicalAnalogSheet.getRange('E16:G17').format.numberFormat = '$#,##0';
  historicalAnalogSheet.getRange('E14:G17').format = {
    fill: C.white,
    borders: { preset: 'all', style: 'thin', color: C.line },
  };

  historicalAnalogSheet.getRange('I12:J12').merge();
  historicalAnalogSheet.getRange('I12').values = [['Selected-path diagnostics']];
  sectionHeader(historicalAnalogSheet.getRange('I12:J12'));
  historicalAnalogSheet.getRange('I13:J18').values = [
    ['Status', null],
    ['Overlapping origins', null],
    ['Non-overlapping windows', null],
    ['Future projection', 'NO'],
    ['AI-attributable effect', 'NO'],
    ['Source ID', historicalAnalogMatrix.source_id],
  ];
  historicalAnalogSheet.getRange('I13:I18').format.font = { bold: true, color: C.ink };
  historicalAnalogSheet.getRange('J13').formulas = [[
    `=IF(COUNTIFS(${analogCriteriaArgs},$H$24:$H$${analogEndRow},"historical_context_available")=1,"historical_context_available",IF(COUNTIFS(${analogCriteriaArgs},$H$24:$H$${analogEndRow},"limited_history_only")=1,"limited_history_only","not_assessed"))`,
  ]];
  historicalAnalogSheet.getRange('J14').formulas = [[
    `=SUMIFS($I$24:$I$${analogEndRow},${analogCriteriaArgs})`,
  ]];
  historicalAnalogSheet.getRange('J15').formulas = [[
    `=SUMIFS($J$24:$J$${analogEndRow},${analogCriteriaArgs})`,
  ]];
  historicalAnalogSheet.getRange('J13:J18').format = {
    fill: C.soft,
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };
  historicalAnalogSheet.getRange('J13').conditionalFormats.add('containsText', {
    text: 'historical_context_available',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  historicalAnalogSheet.getRange('J13').conditionalFormats.add('containsText', {
    text: 'limited_history_only',
    format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } },
  });

  historicalAnalogSheet.getRange('L12:U20').merge();
  historicalAnalogSheet.getRange('L12').values = [[
    'Reading the result: the illustrative $1.2B Edmonton health-facility estimate uses an even five-year expenditure profile beginning three years after the June 2026 price basis. The three outputs show what that schedule would equal under the lower, median and upper descriptive markers across coherent past paths. Six non-overlapping schedule-length windows make this a limited-history stress test. Change the blue inputs to audit another supported building schedule; unsupported or out-of-grid combinations remain blank.',
  ]];
  noteBlock(historicalAnalogSheet.getRange('L12:U20'));

  historicalAnalogSheet.getRange('A23:U23').values = [[
    'Asset class', 'Asset label', 'Geography ID', 'Geography', 'Start lag (years)',
    'Duration (years)', 'Profile', 'Status', 'Overlapping origins',
    'Non-overlapping windows', 'Minimum factor', 'P10 factor', 'P25 factor',
    'Median factor', 'P75 factor', 'P90 factor', 'Maximum factor', 'Source URL',
    'Mapping status', 'Expenditure schedule', 'Lookup key',
  ]];
  header(historicalAnalogSheet.getRange('A23:U23'));
  historicalAnalogSheet.getRange(`A24:U${analogEndRow}`).values = analogRows;
  historicalAnalogSheet.getRange(`E24:F${analogEndRow}`).format.numberFormat = '0';
  historicalAnalogSheet.getRange(`I24:J${analogEndRow}`).format.numberFormat = '#,##0';
  historicalAnalogSheet.getRange(`K24:Q${analogEndRow}`).format.numberFormat = '0.000';
  historicalAnalogSheet.getRange(`H24:H${analogEndRow}`).conditionalFormats.add('containsText', {
    text: 'historical_context_available',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  historicalAnalogSheet.getRange(`H24:H${analogEndRow}`).conditionalFormats.add('containsText', {
    text: 'limited_history_only',
    format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } },
  });
  historicalAnalogSheet.getRange(`H24:H${analogEndRow}`).conditionalFormats.add('containsText', {
    text: 'not_assessed',
    format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
  });
  historicalAnalogSheet.getRange(`L24:P${analogEndRow}`).conditionalFormats.add('dataBar', {
    color: C.teal,
    gradient: true,
  });
  const analogTable = historicalAnalogSheet.tables.add(
    `A23:U${analogEndRow}`,
    true,
    'HistoricalAnalogMatrixTable',
  );
  analogTable.style = 'TableStyleMedium2';
  historicalAnalogSheet.freezePanes.freezeRows(23);
  historicalAnalogSheet.freezePanes.freezeColumns(4);
  setWidths(
    historicalAnalogSheet,
    {
      A: 30, B: 31, C: 15, D: 18, E: 16, F: 16, G: 18, H: 27,
      I: 19, J: 23, K: 16, L: 15, M: 15, N: 17, O: 15, P: 15,
      Q: 17, R: 52, S: 30, T: 58, U: 58,
    },
    analogEndRow,
  );
}

function buildReferenceReview() {
  titleBand(
    referenceReviewSheet,
    'Independent reference-cost review gate',
    'Hash-locked Alberta E1 review instrument · a prepared packet is not a verdict',
    'J',
  );
  const boundary = referenceCostReview.publication_boundary;
  const reviewerRows = Object.entries(programGates.independent_review).map(
    ([reviewer, state]) => [
      reviewer.toUpperCase(),
      state.status,
      state.reason,
      state.evidence,
    ],
  );
  const criteriaRows = referenceCostReview.required_criteria.map((criterion) => [
    criterion.criterion_id,
    criterion.required ? 'YES' : 'NO',
    'pending_independent_review',
    criterion.question,
  ]);
  const passingRows =
    referenceCostReview.facts_to_reconcile.gate_passing_horizons.map((item) => [
      item.asset_class,
      item.geography_id,
      item.horizon_years,
      item.selected_method,
      item.projected_cumulative_change_percent,
      'E1 baseline only; not a project-cost or AI-effect forecast',
    ]);

  referenceReviewSheet.getRange('A5:B10').values = [
    ['Package ID', referenceCostReview.package_id],
    ['Review status', referenceCostReview.review_status],
    ['Model ID', referenceCostReview.model_id],
    ['Locked input files', referenceCostReview.input_manifest.length],
    ['Required criteria', referenceCostReview.required_criteria.length],
    [
      'Gate-passing horizons',
      referenceCostReview.facts_to_reconcile.gate_passing_horizons.length,
    ],
  ];
  referenceReviewSheet.getRange('A5:A10').format.font = {
    bold: true,
    color: C.ink,
  };
  referenceReviewSheet.getRange('B5:B10').format = {
    fill: C.soft,
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };
  referenceReviewSheet.getRange('D5:E9').values = [
    [
      'Independent review complete',
      boundary.independent_review_complete ? 'YES' : 'NO',
    ],
    [
      'Public projection authorized',
      boundary.public_projection_authorized ? 'YES' : 'NO',
    ],
    [
      'AI-attributable effect authorized',
      boundary.ai_attributable_effect_authorized ? 'YES' : 'NO',
    ],
    [
      'Project-cost translation authorized',
      boundary.project_cost_translation_authorized ? 'YES' : 'NO',
    ],
    ['Validated reviewer verdicts', 0],
  ];
  referenceReviewSheet.getRange('D5:D9').format.font = {
    bold: true,
    color: C.ink,
  };
  referenceReviewSheet.getRange('E5:E8').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
  };
  referenceReviewSheet.getRange('G5:J10').merge();
  referenceReviewSheet.getRange('G5').values = [[
    'WITHHELD. The packet makes review reproducible but does not constitute independent review. A valid pass may recommend only the individually gate-passing E1 horizon. Failed horizons, AI-attributable effects, project-budget translations, province-wide claims and graph-score monetization remain prohibited.',
  ]];
  referenceReviewSheet.getRange('G5:J10').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  referenceReviewSheet.getRange('A13:D13').values = [[
    'Reviewer channel',
    'Status',
    'Reason',
    'Evidence record',
  ]];
  header(referenceReviewSheet.getRange('A13:D13'));
  referenceReviewSheet.getRange(`A14:D${13 + reviewerRows.length}`).values =
    reviewerRows;
  referenceReviewSheet
    .getRange(`B14:B${13 + reviewerRows.length}`)
    .conditionalFormats.add('containsText', {
      text: 'blocked',
      format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } },
    });

  referenceReviewSheet.getRange('A18:D18').values = [[
    'Criterion ID',
    'Required',
    'Current status',
    'Independent review question',
  ]];
  header(referenceReviewSheet.getRange('A18:D18'));
  const criteriaEndRow = 18 + criteriaRows.length;
  referenceReviewSheet.getRange(`A19:D${criteriaEndRow}`).values = criteriaRows;
  referenceReviewSheet
    .getRange(`C19:C${criteriaEndRow}`)
    .conditionalFormats.add('containsText', {
      text: 'pending_independent_review',
      format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } },
    });
  const criteriaTable = referenceReviewSheet.tables.add(
    `A18:D${criteriaEndRow}`,
    true,
    'ReferenceCostReviewCriteriaTable',
  );
  criteriaTable.style = 'TableStyleMedium2';

  referenceReviewSheet.getRange('A31:F31').values = [[
    'Asset class',
    'Geography ID',
    'Horizon (years)',
    'Selected method',
    'Projected cumulative change (%)',
    'Permitted claim if independently authorized',
  ]];
  header(referenceReviewSheet.getRange('A31:F31'));
  referenceReviewSheet.getRange(`A32:F${31 + passingRows.length}`).values =
    passingRows;
  referenceReviewSheet
    .getRange(`C32:C${31 + passingRows.length}`)
    .format.numberFormat = '0';
  referenceReviewSheet
    .getRange(`E32:E${31 + passingRows.length}`)
    .format.numberFormat = '0.0';

  referenceReviewSheet.getRange('A35:J38').merge();
  referenceReviewSheet.getRange('A35').values = [[boundary.reason]];
  noteBlock(referenceReviewSheet.getRange('A35:J38'));
  referenceReviewSheet.freezePanes.freezeRows(18);
  referenceReviewSheet.freezePanes.freezeColumns(1);
  setWidths(
    referenceReviewSheet,
    {
      A: 35,
      B: 27,
      C: 31,
      D: 75,
      E: 27,
      F: 56,
      G: 18,
      H: 18,
      I: 18,
      J: 18,
    },
    40,
  );
}

function buildSectorCapex() {
  titleBand(
    sectorCapexSheet,
    'Information-sector construction-capex screen',
    'Statistics Canada table 34-10-0035-01 · broad NAICS 51 context · not an AI-treatment measure',
    'T',
  );
  const boundary = informationSectorCapex.publication_boundary;
  const assessment = informationSectorCapex.treatment_requirement_assessment;
  const sourceUrl =
    'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410003501';

  sectorCapexSheet.getRange('A5:B10').values = [
    ['Model ID', informationSectorCapex.model_id],
    ['Observations', informationSectorCapex.observation_count],
    ['Geographies', informationSectorCapex.geography_count],
    ['Reference years', informationSectorCapex.reference_year_count],
    ['First year', informationSectorCapex.first_reference_year],
    ['Latest year', informationSectorCapex.latest_reference_year],
  ];
  sectorCapexSheet.getRange('A5:A10').format.font = {
    bold: true,
    color: C.ink,
  };
  sectorCapexSheet.getRange('B5:B10').format = {
    fill: C.soft,
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };
  sectorCapexSheet.getRange('D5:E9').values = [
    [
      'Descriptive context authorized',
      boundary.descriptive_broad_sector_capex_authorized ? 'YES' : 'NO',
    ],
    [
      'AI construction treatment authorized',
      boundary.ai_construction_treatment_authorized ? 'YES' : 'NO',
    ],
    [
      'AI-attributable effect authorized',
      boundary.ai_attributable_effect_authorized ? 'YES' : 'NO',
    ],
    [
      'Suppressed cells',
      informationSectorCapex.quality_flag_counts.suppressed_confidentiality,
    ],
    ['Finest relevant NAICS', assessment.finest_available_relevant_naics_code],
  ];
  sectorCapexSheet.getRange('D5:D9').format.font = {
    bold: true,
    color: C.ink,
  };
  sectorCapexSheet.getRange('E5').format = {
    fill: C.tealLight,
    font: { bold: true, color: C.tealDark },
  };
  sectorCapexSheet.getRange('E6:E7').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
  };
  sectorCapexSheet.getRange('G5:T10').merge();
  sectorCapexSheet.getRange('G5').values = [[
    `CONTEXT ONLY. The finest relevant provincial industry is broad NAICS ${assessment.finest_available_relevant_naics_code}, not 518210 or project-level data-centre construction. The source is ${assessment.published_frequency} at ${assessment.published_geography} resolution. Values through ${assessment.actual_or_revised_data_available_through} are actual/revised; 2025 is preliminary actual and 2026 is intentions. Suppressed cells remain blank. This evidence cannot authorize AI treatment, cost escalation or schedule-delay attribution.`,
  ]];
  sectorCapexSheet.getRange('G5:T10').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  sectorCapexSheet.getRange('A12:T12').values = [[
    'Observation ID',
    'Geography ID',
    'Geography',
    'Statistics Canada DGUID',
    'Reference year',
    'Release measure status',
    'Value ($ millions)',
    'Value (CAD, formula)',
    'Unit',
    'NAICS code',
    'NAICS label',
    'Expenditure category',
    'Statistics Canada symbol',
    'Quality flag',
    'Source evidence',
    'Classification evidence',
    'Treatment role',
    'AI treatment authorized',
    'Source ID',
    'Source URL',
  ]];
  header(sectorCapexSheet.getRange('A12:T12'));
  const dataStart = 13;
  const dataEnd = dataStart + informationSectorCapexRows.length - 1;
  const values = informationSectorCapexRows.map((row) => [
    row.observation_id,
    row.geography_id,
    row.geography_label,
    row.statcan_dguid,
    Number(row.reference_year),
    row.release_measure_status,
    numberOrNull(row.value_millions_cad),
    null,
    row.unit,
    row.naics_code,
    row.naics_label,
    row.expenditure_category,
    row.statcan_quality_symbol,
    row.quality_flag,
    row.source_evidence_status,
    row.classification_evidence_status,
    row.treatment_role,
    yesNo(row.ai_construction_treatment_authorized),
    row.source_id,
    sourceUrl,
  ]);
  sectorCapexSheet.getRange(`A${dataStart}:T${dataEnd}`).values = values;
  for (let row = dataStart; row <= dataEnd; row += 1) {
    sectorCapexSheet.getRange(`H${row}`).formulas = [
      [`=IF(G${row}="","",G${row}*1000000)`],
    ];
  }
  sectorCapexSheet.getRange(`E${dataStart}:E${dataEnd}`).format.numberFormat =
    '0';
  sectorCapexSheet.getRange(`G${dataStart}:G${dataEnd}`).format.numberFormat =
    '$#,##0.0';
  sectorCapexSheet.getRange(`H${dataStart}:H${dataEnd}`).format.numberFormat =
    '$#,##0';
  sectorCapexSheet
    .getRange(`F${dataStart}:F${dataEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'actual_or_revised',
      format: { fill: C.tealLight, font: { color: C.tealDark } },
    });
  sectorCapexSheet
    .getRange(`F${dataStart}:F${dataEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'preliminary_actual',
      format: { fill: '#FFF5D8', font: { color: '#7A5A00' } },
    });
  sectorCapexSheet
    .getRange(`F${dataStart}:F${dataEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'intentions',
      format: { fill: C.amberLight, font: { color: '#8A4826' } },
    });
  sectorCapexSheet
    .getRange(`N${dataStart}:N${dataEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'suppressed_confidentiality',
      format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
    });
  const table = sectorCapexSheet.tables.add(
    `A12:T${dataEnd}`,
    true,
    'SectorCapexTable',
  );
  table.style = 'TableStyleMedium2';

  const noteStart = dataEnd + 2;
  const noteEnd = noteStart + 2;
  sectorCapexSheet.getRange(`A${noteStart}:T${noteEnd}`).merge();
  sectorCapexSheet.getRange(`A${noteStart}`).values = [[
    `Permitted use: ${boundary.permitted_use}. Prohibited use: ${boundary.prohibited_use}. Source: Statistics Canada table 34-10-0035-01; source and transformation hashes are recorded in the model artifact.`,
  ]];
  noteBlock(sectorCapexSheet.getRange(`A${noteStart}:T${noteEnd}`));
  sectorCapexSheet.freezePanes.freezeRows(12);
  sectorCapexSheet.freezePanes.freezeColumns(4);
  setWidths(
    sectorCapexSheet,
    {
      A: 36,
      B: 13,
      C: 25,
      D: 20,
      E: 13,
      F: 22,
      G: 17,
      H: 19,
      I: 22,
      J: 12,
      K: 39,
      L: 25,
      M: 18,
      N: 27,
      O: 18,
      P: 23,
      Q: 36,
      R: 19,
      S: 45,
      T: 52,
    },
    noteEnd,
  );
}

function buildCmaReference() {
  titleBand(
    cmaReferenceSheet,
    'Vancouver, Toronto and Montréal reference-cost validation',
    'Unchanged held-out BCPI protocol · city-market evidence · all projections withheld pending review',
    'W',
  );
  const publicAuthorized =
    cmaReferenceBaseline.publication_authorization
      .public_projection_authorized;
  const cmaRows = cmaReferenceBaseline.reference_class_results.flatMap(
    (result) =>
      result.horizons.map((horizon) => {
        const failedGates = Object.entries(horizon.gates ?? {})
          .filter(([, passed]) => !passed)
          .map(([gate]) => gate)
          .join(' | ');
        return [
          result.geography_id,
          result.geography_label,
          labelize(result.asset_class),
          result.reference_class_label,
          result.observation_count,
          new Date(`${result.first_period_end}T00:00:00Z`),
          new Date(`${result.latest_period_end}T00:00:00Z`),
          result.latest_index,
          horizon.horizon_years,
          horizon.status,
          horizon.selected_method ?? '',
          horizon.projected_cumulative_change_percent,
          horizon.empirical_error_band_low_change_percent,
          horizon.empirical_error_band_high_change_percent,
          horizon.calibration_period?.origin_count ?? 0,
          horizon.validation_period?.origin_count ?? 0,
          horizon.validation_period?.selected_method_metrics
            ?.mean_absolute_percentage_error ?? null,
          horizon.validation_period?.selected_method_metrics
            ?.mean_percentage_error ?? null,
          horizon.validation_period?.empirical_interval_coverage_percent ?? null,
          failedGates || (horizon.status === 'gate_passed' ? 'none' : horizon.reason),
          publicAuthorized ? 'YES' : 'NO',
          cmaReferenceBaseline.source_id,
          'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810028901',
        ];
      }),
  );
  const dataStart = 13;
  const dataEnd = dataStart + cmaRows.length - 1;

  cmaReferenceSheet.getRange('A5:B10').values = [
    ['Model ID', cmaReferenceBaseline.model_id],
    ['Normalized observations', null],
    ['Reference series', null],
    ['Horizon results', null],
    ['Gate passed', null],
    ['Gate failed', null],
  ];
  cmaReferenceSheet.getRange('B6').formulas = [[`=SUM(E${dataStart}:E${dataEnd})/5`]];
  cmaReferenceSheet.getRange('B7').formulas = [[`=ROWS(A${dataStart}:A${dataEnd})/5`]];
  cmaReferenceSheet.getRange('B8').formulas = [[`=ROWS(A${dataStart}:A${dataEnd})`]];
  cmaReferenceSheet.getRange('B9').formulas = [[`=COUNTIF(J${dataStart}:J${dataEnd},"gate_passed")`]];
  cmaReferenceSheet.getRange('B10').formulas = [[`=COUNTIF(J${dataStart}:J${dataEnd},"gate_failed")`]];
  cmaReferenceSheet.getRange('A5:A10').format.font = {
    bold: true,
    color: C.ink,
  };
  cmaReferenceSheet.getRange('B5:B10').format = {
    fill: C.soft,
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };

  cmaReferenceSheet.getRange('D5:E10').values = [
    ['Not assessed', null],
    ['Public projection authorized', publicAuthorized ? 'YES' : 'NO'],
    ['Passing geography', 'Vancouver CMA only'],
    ['Latest quarter', new Date(`${cmaReferenceBaseline.as_of_date}T00:00:00Z`)],
    ['Release state', cmaReferenceBaseline.release_state],
    ['Independent review', 'pending'],
  ];
  cmaReferenceSheet.getRange('E5').formulas = [[`=COUNTIF(J${dataStart}:J${dataEnd},"not_assessed")`]];
  cmaReferenceSheet.getRange('E8').format.numberFormat = 'yyyy-mm-dd';
  cmaReferenceSheet.getRange('D5:D10').format.font = {
    bold: true,
    color: C.ink,
  };
  cmaReferenceSheet.getRange('E6:E10').format = {
    fill: C.amberLight,
    font: { color: '#8A4826', bold: true },
  };

  cmaReferenceSheet.getRange('G5:W10').merge();
  cmaReferenceSheet.getRange('G5').values = [[
    'WITHHELD. Nine Vancouver horizons pass the internal validation gates, but no CMA projection is authorized until independent modelling review. Toronto and Montréal have zero passing horizons. The three bus-depot histories are too short. CMA results are local model-building reference indexes, not province-wide forecasts, AI increments or project budget allowances.',
  ]];
  cmaReferenceSheet.getRange('G5:W10').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  cmaReferenceSheet.getRange('A12:W12').values = [[
    'Geography ID',
    'Geography',
    'Asset class',
    'Reference class',
    'Observations',
    'First quarter',
    'Latest quarter',
    'Latest index',
    'Horizon (years)',
    'Validation status',
    'Selected method',
    'Projected change (%)',
    'Band low (%)',
    'Band high (%)',
    'Calibration origins',
    'Validation origins',
    'Validation MAPE (%)',
    'Validation bias (%)',
    'Interval coverage (%)',
    'Failed gate(s)',
    'Public projection authorized',
    'Source ID',
    'Source URL',
  ]];
  header(cmaReferenceSheet.getRange('A12:W12'));
  cmaReferenceSheet.getRange(`A${dataStart}:W${dataEnd}`).values = cmaRows;
  cmaReferenceSheet.getRange(`E${dataStart}:E${dataEnd}`).format.numberFormat = '0';
  cmaReferenceSheet.getRange(`F${dataStart}:G${dataEnd}`).format.numberFormat =
    'yyyy-mm-dd';
  cmaReferenceSheet.getRange(`H${dataStart}:H${dataEnd}`).format.numberFormat =
    '0.0';
  cmaReferenceSheet.getRange(`I${dataStart}:I${dataEnd}`).format.numberFormat = '0';
  cmaReferenceSheet.getRange(`L${dataStart}:S${dataEnd}`).format.numberFormat =
    '0.0';
  cmaReferenceSheet
    .getRange(`J${dataStart}:J${dataEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'gate_passed',
      format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
    });
  cmaReferenceSheet
    .getRange(`J${dataStart}:J${dataEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'gate_failed',
      format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
    });
  cmaReferenceSheet
    .getRange(`J${dataStart}:J${dataEnd}`)
    .conditionalFormats.add('containsText', {
      text: 'not_assessed',
      format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } },
    });
  const table = cmaReferenceSheet.tables.add(
    `A12:W${dataEnd}`,
    true,
    'CmaReferenceValidationTable',
  );
  table.style = 'TableStyleMedium2';

  const noteStart = dataEnd + 2;
  const noteEnd = noteStart + 2;
  cmaReferenceSheet.getRange(`A${noteStart}:W${noteEnd}`).merge();
  cmaReferenceSheet.getRange(`A${noteStart}`).values = [[
    'The normalized 1,752-row CMA observation file remains the auditable input. Blank projection and interval cells are intentional when a horizon fails or is not assessed. A baseline-only model state does not authorize all rows; inspect every geography, asset class and horizon individually.',
  ]];
  noteBlock(cmaReferenceSheet.getRange(`A${noteStart}:W${noteEnd}`));
  cmaReferenceSheet.freezePanes.freezeRows(12);
  cmaReferenceSheet.freezePanes.freezeColumns(4);
  setWidths(
    cmaReferenceSheet,
    {
      A: 14,
      B: 22,
      C: 30,
      D: 39,
      E: 14,
      F: 14,
      G: 14,
      H: 14,
      I: 14,
      J: 18,
      K: 27,
      L: 18,
      M: 15,
      N: 15,
      O: 18,
      P: 18,
      Q: 19,
      R: 18,
      S: 19,
      T: 52,
      U: 22,
      V: 34,
      W: 52,
    },
    noteEnd,
  );
}

function buildProvinceBridge() {
  titleBand(
    provinceBridgeSheet,
    'British Columbia, Ontario and Quebec province-linked history',
    'Official province observations from 2017 · CMA-linked inferred history before 2017 · all projections withheld',
    'W',
  );
  const diagnostics = provinceLinkedBaseline.backcast_method.diagnostics;
  const horizonRows = provinceLinkedBaseline.reference_class_results.flatMap(
    (result) =>
      result.horizons.map((horizon) => {
        const failedGates = Object.entries(horizon.gates ?? {})
          .filter(([, passed]) => !passed)
          .map(([gate]) => gate)
          .join(' | ');
        return [
          result.geography_id,
          result.geography_label,
          labelize(result.asset_class),
          result.reference_class_label,
          result.observation_count,
          new Date(`${result.first_period_end}T00:00:00Z`),
          new Date(`${result.latest_period_end}T00:00:00Z`),
          result.latest_index,
          horizon.horizon_years,
          horizon.status,
          horizon.selected_method ?? '',
          horizon.projected_cumulative_change_percent,
          horizon.empirical_error_band_low_change_percent,
          horizon.empirical_error_band_high_change_percent,
          horizon.calibration_period?.origin_count ?? 0,
          horizon.validation_period?.origin_count ?? 0,
          horizon.validation_period?.selected_method_metrics
            ?.mean_absolute_percentage_error ?? null,
          horizon.validation_period?.selected_method_metrics
            ?.mean_percentage_error ?? null,
          horizon.validation_period?.empirical_interval_coverage_percent ?? null,
          failedGates || (horizon.status === 'gate_passed' ? 'none' : horizon.reason),
          provinceLinkedBaseline.publication_authorization
            .public_projection_authorized
            ? 'YES'
            : 'NO',
          provinceLinkedBaseline.source_id,
          'https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810028901',
        ];
      }),
  );
  const diagnosticsStart = 14;
  const diagnosticsEnd = diagnosticsStart + diagnostics.length - 1;
  const horizonHeaderRow = diagnosticsEnd + 3;
  const horizonStart = horizonHeaderRow + 1;
  const horizonEnd = horizonStart + horizonRows.length - 1;
  const totalObservations = provinceLinkedBaseline.reference_class_results.reduce(
    (total, result) => total + result.observation_count,
    0,
  );
  const inferredObservations = diagnostics.reduce(
    (total, item) => total + item.backcast_observation_count,
    0,
  );
  const officialObservations = totalObservations - inferredObservations;

  provinceBridgeSheet.getRange('A5:B10').values = [
    ['Model ID', provinceLinkedBaseline.model_id],
    ['Total linked observations', totalObservations],
    ['Inferred pre-2017 observations', inferredObservations],
    ['Official observations', officialObservations],
    ['Reference series', provinceLinkedBaseline.publication_summary.reference_series_count],
    ['Gate-passing horizons', provinceLinkedBaseline.publication_summary.horizon_status_counts.gate_passed],
  ];
  provinceBridgeSheet.getRange('A5:A10').format.font = { bold: true, color: C.ink };
  provinceBridgeSheet.getRange('B5:B10').format = {
    fill: C.soft,
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };
  provinceBridgeSheet.getRange('B6:B10').format.numberFormat = '#,##0';

  provinceBridgeSheet.getRange('D5:E10').values = [
    ['Overlap diagnostics', diagnostics.length],
    ['Maximum overlap MAPE', Math.max(...diagnostics.map((item) => item.overlap_mape_percent)) / 100],
    ['Public projection authorized', provinceLinkedBaseline.publication_authorization.public_projection_authorized ? 'YES' : 'NO'],
    ['Research display authorized', provinceLinkedBaseline.publication_authorization.province_linked_backcast_authorized_for_research_display ? 'YES' : 'NO'],
    ['Release state', provinceLinkedBaseline.release_state],
    ['Independent review', 'pending'],
  ];
  provinceBridgeSheet.getRange('D5:D10').format.font = { bold: true, color: C.ink };
  provinceBridgeSheet.getRange('E5:E10').format = {
    fill: C.amberLight,
    font: { color: '#8A4826', bold: true },
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  provinceBridgeSheet.getRange('E6').format.numberFormat = '0.00%';

  provinceBridgeSheet.getRange('G5:W10').merge();
  provinceBridgeSheet.getRange('G5').values = [[
    'RESEARCH DISPLAY ONLY. The pre-2017 bridge scales Montréal, Toronto or Vancouver to the first official provincial index level. Every inferred row is explicitly labelled and retains the reference CMA DGUID. The overlap screen confirms close tracking after the anchor, not historical province-wide representativeness. Nine British Columbia-linked horizons pass internally; Ontario and Quebec remain gate-failed, municipal-operations histories remain too short, and no project-cost or AI-effect result is authorized.',
  ]];
  provinceBridgeSheet.getRange('G5:W10').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  provinceBridgeSheet.getRange('A12:J12').merge();
  provinceBridgeSheet.getRange('A12').values = [['Backcast overlap diagnostics']];
  sectionHeader(provinceBridgeSheet.getRange('A12:J12'));
  provinceBridgeSheet.getRange('A13:J13').values = [[
    'Province ID',
    'Reference CMA ID',
    'Indicator ID',
    'Anchor quarter',
    'Scale factor',
    'Overlap count',
    'Overlap MAPE',
    'Max absolute overlap error',
    'Backcast observations',
    'Status',
  ]];
  header(provinceBridgeSheet.getRange('A13:J13'));
  provinceBridgeSheet.getRange(`A${diagnosticsStart}:J${diagnosticsEnd}`).values = diagnostics.map((item) => [
    item.province_id,
    item.reference_cma_id,
    item.indicator_id,
    new Date(`${item.anchor_period_end}T00:00:00Z`),
    item.anchor_scale_factor,
    item.overlap_observation_count,
    item.overlap_mape_percent / 100,
    item.overlap_max_absolute_error_percent / 100,
    item.backcast_observation_count,
    item.status.toUpperCase(),
  ]);
  provinceBridgeSheet.getRange(`D${diagnosticsStart}:D${diagnosticsEnd}`).format.numberFormat = 'yyyy-mm-dd';
  provinceBridgeSheet.getRange(`E${diagnosticsStart}:E${diagnosticsEnd}`).format.numberFormat = '0.000000';
  provinceBridgeSheet.getRange(`F${diagnosticsStart}:F${diagnosticsEnd}`).format.numberFormat = '0';
  provinceBridgeSheet.getRange(`G${diagnosticsStart}:H${diagnosticsEnd}`).format.numberFormat = '0.00%';
  provinceBridgeSheet.getRange(`I${diagnosticsStart}:I${diagnosticsEnd}`).format.numberFormat = '#,##0';
  provinceBridgeSheet.getRange(`J${diagnosticsStart}:J${diagnosticsEnd}`).conditionalFormats.add('containsText', {
    text: 'PASS',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  const diagnosticTable = provinceBridgeSheet.tables.add(
    `A13:J${diagnosticsEnd}`,
    true,
    'ProvinceBridgeDiagnosticTable',
  );
  diagnosticTable.style = 'TableStyleMedium2';

  provinceBridgeSheet.getRange(`A${horizonHeaderRow}:W${horizonHeaderRow}`).values = [[
    'Geography ID',
    'Geography',
    'Asset class',
    'Reference class',
    'Observations',
    'First quarter',
    'Latest quarter',
    'Latest index',
    'Horizon (years)',
    'Validation status',
    'Selected method',
    'Projected change (%)',
    'Band low (%)',
    'Band high (%)',
    'Calibration origins',
    'Validation origins',
    'Validation MAPE (%)',
    'Validation bias (%)',
    'Interval coverage (%)',
    'Failed gate(s)',
    'Public projection authorized',
    'Source ID',
    'Source URL',
  ]];
  header(provinceBridgeSheet.getRange(`A${horizonHeaderRow}:W${horizonHeaderRow}`));
  provinceBridgeSheet.getRange(`A${horizonStart}:W${horizonEnd}`).values = horizonRows;
  provinceBridgeSheet.getRange(`E${horizonStart}:E${horizonEnd}`).format.numberFormat = '0';
  provinceBridgeSheet.getRange(`F${horizonStart}:G${horizonEnd}`).format.numberFormat = 'yyyy-mm-dd';
  provinceBridgeSheet.getRange(`H${horizonStart}:H${horizonEnd}`).format.numberFormat = '0.0';
  provinceBridgeSheet.getRange(`I${horizonStart}:I${horizonEnd}`).format.numberFormat = '0';
  provinceBridgeSheet.getRange(`L${horizonStart}:S${horizonEnd}`).format.numberFormat = '0.0';
  provinceBridgeSheet.getRange(`J${horizonStart}:J${horizonEnd}`).conditionalFormats.add('containsText', {
    text: 'gate_passed',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  provinceBridgeSheet.getRange(`J${horizonStart}:J${horizonEnd}`).conditionalFormats.add('containsText', {
    text: 'gate_failed',
    format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
  });
  provinceBridgeSheet.getRange(`J${horizonStart}:J${horizonEnd}`).conditionalFormats.add('containsText', {
    text: 'not_assessed',
    format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } },
  });
  const horizonTable = provinceBridgeSheet.tables.add(
    `A${horizonHeaderRow}:W${horizonEnd}`,
    true,
    'ProvinceBridgeHorizonTable',
  );
  horizonTable.style = 'TableStyleMedium2';

  const noteStart = horizonEnd + 2;
  const noteEnd = noteStart + 2;
  provinceBridgeSheet.getRange(`A${noteStart}:W${noteEnd}`).merge();
  provinceBridgeSheet.getRange(`A${noteStart}`).values = [[
    'The 1,752-row combined observation file is the auditable model input: 1,296 pre-2017 inferred rows and 456 untouched official rows. Blank projection and interval cells are intentional when a horizon fails or is not assessed. The bridge improves validation history but cannot convert a CMA reference into an official historical provincial index.',
  ]];
  noteBlock(provinceBridgeSheet.getRange(`A${noteStart}:W${noteEnd}`));
  provinceBridgeSheet.freezePanes.freezeRows(horizonHeaderRow);
  provinceBridgeSheet.freezePanes.freezeColumns(4);
  setWidths(
    provinceBridgeSheet,
    {
      A: 14,
      B: 22,
      C: 39,
      D: 39,
      E: 14,
      F: 14,
      G: 16,
      H: 18,
      I: 18,
      J: 18,
      K: 27,
      L: 18,
      M: 15,
      N: 15,
      O: 18,
      P: 18,
      Q: 19,
      R: 18,
      S: 19,
      T: 52,
      U: 22,
      V: 34,
      W: 52,
    },
    noteEnd,
  );
}

function buildProjectCostCheck() {
  titleBand(
    projectCost,
    'Project cost decision check',
    'Editable blue cells · schedule-weighted market reference · AI increment remains separate',
    'L',
  );
  projectCost.getRange('A5:B9').values = [
    ['Project name', 'Demonstration Calgary health project'],
    ['Asset class', 'health_facilities'],
    ['Geography ID', 'CMA_825'],
    ['Current estimate (CAD)', 100000000],
    ['Estimate price basis', costBaseline.as_of_date],
  ];
  projectCost.getRange('A5:A9').format.font = { bold: true, color: C.ink };
  inputStyle(projectCost.getRange('B5:B9'));
  projectCost.getRange('B8').format.numberFormat = '$#,##0';
  projectCost.dataValidations.add({
    range: 'B8',
    rule: { type: 'decimal', operator: 'greaterThan', formula1: 0 },
  });

  projectCost.getRange('D5:L9').merge();
  projectCost.getRange('D5').values = [
    [
      'DEMONSTRATION INPUT, NOT AN OBSERVED PROJECT. Enter a project estimate only when its price basis is known. Version 0.1 requires that basis to equal the latest observed baseline quarter. Each expenditure year is evaluated separately; the full estimate is never escalated by only the end-year index.',
    ],
  ];
  noteBlock(projectCost.getRange('D5:L9'));

  projectCost.getRange('A12:C12').values = [
    ['Horizon year', 'Illustrative calendar year', 'Expenditure share'],
  ];
  header(projectCost.getRange('A12:C12'));
  projectCost.getRange('A13:C18').values = [
    [0, 2026, 0],
    [1, 2027, 0.2],
    [2, 2028, 0.2],
    [3, 2029, 0.2],
    [4, 2030, 0.2],
    [5, 2031, 0.2],
  ];
  inputStyle(projectCost.getRange('C13:C18'));
  projectCost.getRange('C13:C18').format.numberFormat = '0.0%';
  projectCost.dataValidations.add({
    range: 'C13:C18',
    rule: { type: 'decimal', operator: 'between', formula1: 0, formula2: 1 },
  });

  projectCost.getRange('E12:L12').values = [
    [
      'Horizon',
      'Share',
      'Gate status',
      'Reference index',
      'Index factor',
      'Weighted factor',
      'Failure boundary',
      'Evidence status',
    ],
  ];
  header(projectCost.getRange('E12:L12'));
  for (let index = 0; index < 6; index += 1) {
    const row = 13 + index;
    projectCost.getRange(`E${row}`).formulas = [[`=A${row}`]];
    projectCost.getRange(`F${row}`).formulas = [[`=C${row}`]];
    projectCost.getRange(`G${row}`).formulas = [
      [
        index === 0
          ? `=IF(F${row}=0,"NOT USED","observed_origin")`
          : `=IF(F${row}=0,"NOT USED",IF(COUNTIFS('Cost Baseline'!$A$11:$A$50,$B$6,'Cost Baseline'!$C$11:$C$50,$B$7,'Cost Baseline'!$E$11:$E$50,E${row},'Cost Baseline'!$F$11:$F$50,"gate_passed")=1,"gate_passed","WITHHELD"))`,
      ],
    ];
    projectCost.getRange(`H${row}`).formulas = [
      [
        index === 0
          ? `=IF(G${row}="observed_origin",SUMIFS('Cost Baseline'!$N$11:$N$50,'Cost Baseline'!$A$11:$A$50,$B$6,'Cost Baseline'!$C$11:$C$50,$B$7),"")`
          : `=IF(G${row}="gate_passed",SUMIFS('Cost Baseline'!$L$11:$L$50,'Cost Baseline'!$A$11:$A$50,$B$6,'Cost Baseline'!$C$11:$C$50,$B$7,'Cost Baseline'!$E$11:$E$50,E${row}),"")`,
      ],
    ];
    projectCost.getRange(`I${row}`).formulas = [
      [
        `=IF(H${row}="","",H${row}/SUMIFS('Cost Baseline'!$N$11:$N$50,'Cost Baseline'!$A$11:$A$50,$B$6,'Cost Baseline'!$C$11:$C$50,$B$7))`,
      ],
    ];
    projectCost.getRange(`J${row}`).formulas = [
      [`=IF(I${row}="","",F${row}*I${row})`],
    ];
    projectCost.getRange(`K${row}`).formulas = [
      [
        `=IF(G${row}="WITHHELD","Required horizon gate failed or is unavailable","")`,
      ],
    ];
    projectCost.getRange(`L${row}`).formulas = [
      [
        `=IF(F${row}=0,"not_used",IF(G${row}="WITHHELD","withheld","reference_baseline"))`,
      ],
    ];
  }
  projectCost.getRange('F13:F18').format.numberFormat = '0.0%';
  projectCost.getRange('H13:J18').format.numberFormat = '0.0000';
  projectCost.getRange('G13:G18').conditionalFormats.add('containsText', {
    text: 'WITHHELD',
    format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
  });

  projectCost.getRange('A21:B21').values = [
    ['Project calculation gate', 'Result'],
  ];
  header(projectCost.getRange('A21:B21'));
  projectCost.getRange('A22:A30').values = [
    ['Expenditure shares'],
    ['Active expenditure horizons'],
    ['Required horizon gates'],
    ['Independent modelling review'],
    ['Project result status'],
    ['Schedule-weighted factor'],
    ['Reference change'],
    ['Reference estimate'],
    ['Reference escalation'],
  ];
  projectCost.getRange('A22:A30').format.font = { bold: true, color: C.ink };
  projectCost.getRange('B22').formulas = [
    ['=IF(ABS(SUM(C13:C18)-1)<0.000001,"PASS","FAIL")'],
  ];
  projectCost.getRange('B23').formulas = [['=COUNTIF(C13:C18,">0")']];
  projectCost.getRange('B24').formulas = [
    ['=IF(COUNTIF(G13:G18,"WITHHELD")=0,"PASS","WITHHELD")'],
  ];
  projectCost.getRange('B25').values = [
    [
      costBaseline.publication_authorization.public_projection_authorized
        ? 'AUTHORIZED'
        : 'WITHHELD',
    ],
  ];
  projectCost.getRange('B26').formulas = [
    [
      '=IF(B22<>"PASS","NOT ASSESSED — PROFILE INVALID",IF(B24<>"PASS","WITHHELD — REQUIRED HORIZON GATE FAILED",IF(B25<>"AUTHORIZED","WITHHELD — INDEPENDENT REVIEW","BASELINE ONLY")))',
    ],
  ];
  projectCost.getRange('B27').formulas = [
    ['=IF(B26="BASELINE ONLY",SUM(J13:J18),"")'],
  ];
  projectCost.getRange('B28').formulas = [
    ['=IF(B26="BASELINE ONLY",B27-1,"")'],
  ];
  projectCost.getRange('B29').formulas = [
    ['=IF(B26="BASELINE ONLY",B8*B27,"")'],
  ];
  projectCost.getRange('B30').formulas = [
    ['=IF(B26="BASELINE ONLY",B29-B8,"")'],
  ];
  projectCost.getRange('B27').format.numberFormat = '0.0000';
  projectCost.getRange('B28').format.numberFormat = '0.0%';
  projectCost.getRange('B29:B30').format.numberFormat = '$#,##0';
  projectCost.getRange('B22:B26').conditionalFormats.add('containsText', {
    text: 'WITHHELD',
    format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
  });
  projectCost.getRange('B22:B26').conditionalFormats.add('containsText', {
    text: 'PASS',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });

  projectCost.getRange('D21:L26').merge();
  projectCost.getRange('D21').values = [
    [
      'EXPECTED DEFAULT RESULT: WITHHELD. The five-year Calgary health example requires horizons 1 through 5. Those horizons do not pass the predeclared validation gates, so the schedule-weighted project estimate remains blank. This protects decision makers from a precise-looking but unsupported escalation number.',
    ],
  ];
  projectCost.getRange('D21:L26').format = {
    fill: C.amberLight,
    font: { color: '#7B4529' },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  projectCost.getRange('D28:L34').merge();
  projectCost.getRange('D28').values = [
    [
      'AI-ATTRIBUTABLE INCREMENT: NOT CALIBRATED. Cost escalation %, escalation CAD and schedule delay remain blank. Graph pressure scores may explain mechanisms and bottlenecks, but they do not enter the market-reference calculation and cannot be converted into dollars or days without a separately validated attribution model.',
    ],
  ];
  noteBlock(projectCost.getRange('D28:L34'));
  projectCost.getRange('A33:B36').values = [
    ['AI-attributable cost escalation', null],
    ['AI-attributable escalation (CAD)', null],
    ['AI-attributable schedule delay', null],
    ['AI increment status', 'NOT CALIBRATED'],
  ];
  projectCost.getRange('A33:A36').format.font = { bold: true, color: C.ink };
  projectCost.getRange('B33').format.numberFormat = '0.0%';
  projectCost.getRange('B34').format.numberFormat = '$#,##0';
  projectCost.getRange('B35').format.numberFormat = '0 "days"';
  projectCost.getRange('B36').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  projectCost.freezePanes.freezeRows(4);
  setWidths(
    projectCost,
    {
      A: 26,
      B: 30,
      C: 19,
      D: 4,
      E: 12,
      F: 12,
      G: 20,
      H: 18,
      I: 15,
      J: 18,
      K: 34,
      L: 20,
    },
    38,
  );
}

function buildCanadaExpansion() {
  titleBand(
    canadaExpansion,
    'Canada expansion evidence gate',
    `Current research intake · excluded from public release basis ${release.manifest.version}`,
    'J',
  );

  canadaExpansion.getRange('A5:B5').values = [['Control', 'Value']];
  header(canadaExpansion.getRange('A5:B5'));
  canadaExpansion.getRange('A6:B20').values = [
    ['Public release basis', release.manifest.version],
    ['Project intake ID', provincialProjects.transformation_id],
    [
      'Project exposure authorized',
      provincialProjects.publication_boundary.public_project_exposure_authorized
        ? 'YES'
        : 'NO',
    ],
    ['Normalized project records', provincialProjects.record_count],
    ['Provincial BCPI model ID', provincialCostBaseline.model_id],
    [
      'Provincial BCPI horizon results',
      provincialCostBaseline.publication_summary.horizon_result_count,
    ],
    [
      'Provincial projections authorized',
      provincialCostBaseline.publication_authorization
        .public_projection_authorized
        ? 'YES'
        : 'NO',
    ],
    ['Power-planning contract ID', provincialPowerPlanning.model_id],
    ['Power-planning metrics', provincialPowerPlanning.metric_count],
    [
      'Named transmission actions',
      provincialPowerPlanning.transmission_action_count,
    ],
    [
      'Power profile authorized',
      provincialPowerPlanning.publication_boundary
        .provincial_power_profile_authorized
        ? 'YES'
        : 'NO',
    ],
    ['Digest ID', digestManifest.digest_id],
    ['Digest edition (UTC)', new Date(`${digestManifest.edition_date}T00:00:00Z`)],
    ['Digest items', digestManifest.item_count],
    ['Automatic model change', digestManifest.automatic_model_change ? 'YES' : 'NO'],
  ];
  canadaExpansion.getRange('A6:A20').format.font = {
    bold: true,
    color: C.ink,
  };
  canadaExpansion.getRange('B6:B20').format = {
    fill: C.white,
    font: { color: C.ink },
    borders: { preset: 'inside', style: 'thin', color: C.line },
  };
  canadaExpansion.getRange('B18').format.numberFormat = 'yyyy-mm-dd';
  for (const cell of ['B8', 'B12', 'B16', 'B20']) {
    canadaExpansion.getRange(cell).format = {
      fill: C.amberLight,
      font: { bold: true, color: '#8A4826' },
      borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
    };
  }

  canadaExpansion.getRange('D5:J5').merge();
  canadaExpansion.getRange('D5').values = [['Interpretation boundary']];
  sectionHeader(canadaExpansion.getRange('D5:J5'), C.amber);
  canadaExpansion.getRange('D6:J9').merge();
  canadaExpansion.getRange('D6').values = [
    [
      'PUBLIC PROJECTS — RESEARCH INTAKE ONLY. B.C., Ontario and Quebec source inventories differ in scope, vintage, threshold and schedule completeness. Counts support source audit; they do not authorize pooled exposure, cost totals, delay estimates or AI-attributable escalation.',
    ],
  ];
  noteBlock(canadaExpansion.getRange('D6:J9'));
  canadaExpansion.getRange('D11:J14').merge();
  canadaExpansion.getRange('D11').values = [
    [
      'PROVINCIAL COST REFERENCE — NOT ASSESSED. All 60 one- through five-year horizon checks remain null under the locked validation protocol. No Alberta coefficient, model choice or error band is transferred to another province.',
    ],
  ];
  noteBlock(canadaExpansion.getRange('D11:J14'));
  canadaExpansion.getRange('D16:J20').merge();
  canadaExpansion.getRange('D16').values = [
    [
      'POWER + DIGEST — SOURCE CONTRACT ONLY. Ontario energy, Quebec peak demand and B.C. plan actions remain separate quantities. The digest can flag review candidates but cannot change the graph, scenarios, baselines, workbook publication basis or Decision Mode.',
    ],
  ];
  noteBlock(canadaExpansion.getRange('D16:J20'));

  canadaExpansion.getRange('A23:G23').values = [
    [
      'Geography',
      'Source ID',
      'Raw records',
      'Normalized',
      'Reported cost',
      'Complete schedule',
      'Gate',
    ],
  ];
  header(canadaExpansion.getRange('A23:G23'));
  const projectRows = provincialProjects.source_diagnostics.map((item) => [
    provinceLabel(item.geography_id),
    item.source_id,
    item.raw_record_count,
    item.normalized_record_count,
    item.reported_cost_record_count,
    item.complete_schedule_record_count,
    'RESEARCH ONLY',
  ]);
  canadaExpansion.getRange('A24:G26').values = projectRows;
  canadaExpansion.getRange('C24:F26').format.numberFormat = '#,##0';
  canadaExpansion.getRange('G24:G26').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
  };

  const bcpiSummary = new Map();
  for (const item of provincialCostBaseline.reference_class_results) {
    const summary = bcpiSummary.get(item.geography_id) ?? {
      geography_id: item.geography_id,
      series: 0,
      horizons: 0,
      notAssessed: 0,
      latestPeriod: item.latest_period_end,
    };
    summary.series += 1;
    summary.horizons += item.horizons.length;
    summary.notAssessed += item.horizons.filter(
      (horizon) => horizon.status === 'not_assessed',
    ).length;
    bcpiSummary.set(item.geography_id, summary);
  }
  canadaExpansion.getRange('A29:G29').values = [
    [
      'Geography',
      'Reference series',
      'Horizon results',
      'Not assessed',
      'Latest quarter',
      'Unit',
      'Gate',
    ],
  ];
  header(canadaExpansion.getRange('A29:G29'));
  canadaExpansion.getRange('A30:G32').values = [...bcpiSummary.values()]
    .sort((a, b) => a.geography_id.localeCompare(b.geography_id))
    .map((item) => [
      provinceLabel(item.geography_id),
      item.series,
      item.horizons,
      item.notAssessed,
      new Date(`${item.latestPeriod}T00:00:00Z`),
      'Index, 2023=100',
      'WITHHELD',
    ]);
  canadaExpansion.getRange('B30:D32').format.numberFormat = '#,##0';
  canadaExpansion.getRange('E30:E32').format.numberFormat = 'yyyy-mm-dd';
  canadaExpansion.getRange('G30:G32').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
  };

  canadaExpansion.getRange('A35:G35').values = [
    [
      'Geography',
      'Metric count',
      'Quantity types',
      'Review status',
      'Comparison',
      'Scenario calibration',
      'Transmission requirement',
    ],
  ];
  header(canadaExpansion.getRange('A35:G35'));
  canadaExpansion.getRange('A36:G38').values = Object.entries(
    provincialPowerPlanning.coverage,
  )
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([geographyId, item]) => [
      provinceLabel(geographyId),
      item.metric_count,
      item.quantity_types.map(labelize).join('; '),
      provincialPowerPlanning.review_status,
      'SOURCE-SPECIFIC',
      'NO',
      'NO',
    ]);
  canadaExpansion.getRange('B36:B38').format.numberFormat = '#,##0';
  canadaExpansion.getRange('E36:G38').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
  };

  const sourceById = new Map(
    currentSourceRegistry.sources.map((item) => [item.source_id, item]),
  );
  const sourceRows = digestManifest.source_ids.map((sourceId) => {
    const item = sourceById.get(sourceId);
    return [sourceId, item?.geography ?? 'Unknown', item?.canonical_url ?? ''];
  });
  canadaExpansion.getRange('H23:J23').values = [
    ['Digest source ID', 'Publisher geography', 'Canonical URL'],
  ];
  header(canadaExpansion.getRange('H23:J23'));
  const digestSourceStartRow = 24;
  const digestSourceEndRow = digestSourceStartRow + sourceRows.length - 1;
  canadaExpansion.getRange(
    `H${digestSourceStartRow}:J${digestSourceEndRow}`,
  ).values = sourceRows;
  canadaExpansion.getRange(
    `H${digestSourceStartRow}:H${digestSourceEndRow}`,
  ).format.font = {
    name: 'Aptos Mono',
    size: 8,
    color: C.tealDark,
  };
  canadaExpansion.getRange(
    `J${digestSourceStartRow}:J${digestSourceEndRow}`,
  ).format.font = {
    size: 8,
    color: C.blueInput,
  };

  canadaExpansion.getRange('A41:J41').merge();
  canadaExpansion.getRange('A41').values = [['Publication boundary']];
  sectionHeader(canadaExpansion.getRange('A41:J41'), C.amber);
  canadaExpansion.getRange('A42:J46').merge();
  canadaExpansion.getRange('A42').values = [
    [
      'This sheet documents current research readiness, not provincial performance. It is deliberately outside the public release manifest. None of these intake artifacts can populate Decision Mode, create a provincial forecast, convert capital expenditure to transmission capacity, or change a model parameter until the relevant independent review and versioned release gates pass.',
    ],
  ];
  canadaExpansion.getRange('A42:J46').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  canadaExpansion.getRange('A48:J48').merge();
  canadaExpansion.getRange('A48').values = [
    [
      `Digest hash: ${digestManifest.markdown_sha256} · source registry hash: ${digestManifest.source_registry_sha256}`,
    ],
  ];
  canadaExpansion.getRange('A48').format = {
    font: { name: 'Aptos Mono', size: 8, color: C.muted },
  };
  canadaExpansion.freezePanes.freezeRows(4);
  setWidths(
    canadaExpansion,
    {
      A: 25,
      B: 34,
      C: 16,
      D: 18,
      E: 18,
      F: 20,
      G: 21,
      H: 32,
      I: 27,
      J: 48,
    },
    48,
  );
}

function buildAttributionGate() {
  titleBand(
    attributionGate,
    'AI-attributable effect identification gate',
    'Preregistered treatment, outcome, control and diagnostic requirements · research only',
    'J',
  );

  attributionGate.getRange('A5:B5').values = [['Control', 'Current value']];
  header(attributionGate.getRange('A5:B5'));
  attributionGate.getRange('A6:B13').values = [
    ['Contract ID', attributionReadiness.contract_id],
    ['Estimand ID', attributionReadiness.estimand_id],
    ['Analysis status', attributionReadiness.analysis_status],
    [
      'AI-attributable increment authorized',
      attributionReadiness.publication_authorization
        .ai_attributable_increment_authorized
        ? 'YES'
        : 'NO',
    ],
    [
      'Cost escalation (CAD)',
      attributionReadiness.publication_authorization.cost_escalation_cad,
    ],
    [
      'Cost escalation (%)',
      attributionReadiness.publication_authorization.cost_escalation_percent,
    ],
    [
      'Schedule delay (days)',
      attributionReadiness.publication_authorization.schedule_delay_days,
    ],
    [
      'Publication status',
      attributionReadiness.publication_authorization.status,
    ],
  ];
  attributionGate.getRange('A6:A13').format.font = {
    bold: true,
    color: C.ink,
  };
  attributionGate.getRange('B6:B13').format = {
    fill: C.white,
    font: { color: C.ink },
    borders: { preset: 'inside', style: 'thin', color: C.line },
  };
  attributionGate.getRange('B9:B13').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  attributionGate.getRange('B10').format.numberFormat = '$#,##0';
  attributionGate.getRange('B11').format.numberFormat = '0.0%';
  attributionGate.getRange('B12').format.numberFormat = '#,##0';

  attributionGate.getRange('D5:J5').merge();
  attributionGate.getRange('D5').values = [['Publication boundary']];
  sectionHeader(attributionGate.getRange('D5:J5'), C.amber);
  attributionGate.getRange('D6:J13').merge();
  attributionGate.getRange('D6').values = [
    [
      `${attributionReadiness.publication_authorization.reason} The Edmonton permit screen contributes ${permitProxyReport.data_centre_candidate_count} inferred data-centre candidates, but it contains ${permitProxyReport.explicit_ai_reference_count} explicit AI references and ${permitProxyReport.data_centre_candidate_occupancy_date_available_count} candidate occupancy dates. Its reported permit estimates are not realized spend. Announced capex, requested connection load, demand forecasts, scenario capex and graph pressure scores are prohibited as authorizing treatment measures. The graph remains a mechanism and bottleneck map; it does not supply the counterfactual or identify the treatment effect.`,
    ],
  ];
  attributionGate.getRange('D6:J13').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  attributionGate.getRange('A16:F16').values = [
    [
      'Domain',
      'Role',
      'Status',
      'Available variables',
      'Missing variables',
      'Registry-bound source IDs',
    ],
  ];
  header(attributionGate.getRange('A16:F16'));
  const domainRows = attributionReadiness.domain_status.map((domain) => [
    labelize(domain.domain_id),
    labelize(domain.role),
    domain.status,
    domain.available_variables.map(labelize).join('; '),
    domain.missing_variables.map(labelize).join('; '),
    domain.source_ids.join('; '),
  ]);
  attributionGate.getRange(`A17:F${16 + domainRows.length}`).values = domainRows;
  attributionGate.getRange(`A17:F${16 + domainRows.length}`).format = {
    font: { color: C.ink, size: 9 },
    wrapText: true,
    verticalAlignment: 'top',
    borders: {
      insideHorizontal: { style: 'thin', color: C.line },
      bottom: { style: 'thin', color: C.line },
    },
  };
  attributionGate.getRange(`A17:C${16 + domainRows.length}`).format.font = {
    bold: true,
    color: C.ink,
    size: 9,
  };
  attributionGate
    .getRange(`C17:C${16 + domainRows.length}`)
    .conditionalFormats.add('containsText', {
      text: 'available',
      format: {
        fill: C.tealLight,
        font: { color: C.tealDark, bold: true },
      },
    });
  attributionGate
    .getRange(`C17:C${16 + domainRows.length}`)
    .conditionalFormats.add('containsText', {
      text: 'missing',
      format: {
        fill: C.amberLight,
        font: { color: '#8A4826', bold: true },
      },
    });
  attributionGate.getRange(`A17:F${16 + domainRows.length}`).format.rowHeight = 58;

  attributionGate.getRange('A26:D26').values = [
    ['Design requirement', 'Value', 'Required before estimation', 'Status'],
  ];
  header(attributionGate.getRange('A26:D26'));
  attributionGate.getRange('A27:D34').values = [
    [
      'Primary estimator',
      labelize(attributionReadiness.design.primary_estimator),
      'Yes',
      'locked',
    ],
    [
      'Unit of analysis',
      attributionContract.unit_of_analysis,
      'Yes',
      'locked',
    ],
    ['Frequency', attributionContract.frequency, 'Yes', 'locked'],
    [
      'Anticipation periods',
      attributionReadiness.design.anticipation_periods,
      'Yes',
      'locked',
    ],
    [
      'Minimum pre-treatment quarters',
      attributionReadiness.design.minimum_pre_treatment_quarters,
      'Yes',
      'locked',
    ],
    [
      'Minimum post-treatment quarters',
      attributionReadiness.design.minimum_post_treatment_quarters,
      'Yes',
      'locked',
    ],
    [
      'Minimum treated regions',
      attributionReadiness.design.minimum_treated_regions,
      'Yes',
      'locked',
    ],
    [
      'Minimum controls per cohort',
      attributionReadiness.design.minimum_control_regions_per_cohort,
      'Yes',
      'locked',
    ],
  ];
  attributionGate.getRange('A27:A34').format.font = { bold: true, color: C.ink };
  attributionGate.getRange('B27:D34').format = {
    fill: C.white,
    font: { color: C.ink, size: 9 },
    wrapText: true,
    borders: { preset: 'inside', style: 'thin', color: C.line },
  };

  attributionGate.getRange('F26:H26').values = [
    ['Readiness check', 'Status', 'Summary'],
  ];
  header(attributionGate.getRange('F26:H26'));
  const readinessRows = attributionReadiness.readiness_checks.map((check) => [
    labelize(check.check_id),
    check.status,
    check.summary,
  ]);
  attributionGate.getRange(`F27:H${26 + readinessRows.length}`).values =
    readinessRows;
  attributionGate.getRange(`F27:H${26 + readinessRows.length}`).format = {
    font: { color: C.ink, size: 9 },
    wrapText: true,
    verticalAlignment: 'top',
    borders: {
      insideHorizontal: { style: 'thin', color: C.line },
      bottom: { style: 'thin', color: C.line },
    },
  };
  attributionGate.getRange(`F27:F${26 + readinessRows.length}`).format.font = {
    bold: true,
    color: C.ink,
    size: 9,
  };
  attributionGate
    .getRange(`G27:G${26 + readinessRows.length}`)
    .conditionalFormats.add('containsText', {
      text: 'pass',
      format: {
        fill: C.tealLight,
        font: { color: C.tealDark, bold: true },
      },
    });
  attributionGate
    .getRange(`G27:G${26 + readinessRows.length}`)
    .conditionalFormats.add('containsText', {
      text: 'pending',
      format: {
        fill: C.amberLight,
        font: { color: '#8A4826', bold: true },
      },
    });
  attributionGate.getRange(`F27:H${26 + readinessRows.length}`).format.rowHeight =
    44;

  attributionGate.getRange('A40:J40').merge();
  attributionGate.getRange('A40').values = [['Identification rule']];
  sectionHeader(attributionGate.getRange('A40:J40'), C.amber);
  attributionGate.getRange('A41:J46').merge();
  attributionGate.getRange('A41').values = [
    [
      `Authorizing measures: ${attributionContract.treatment.authorizing_measures.map(labelize).join('; ')}. Research-only proxies: ${attributionContract.treatment.proxy_measures_research_only.map(labelize).join('; ')}. Prohibited as treatment: ${attributionContract.treatment.prohibited_as_treatment.map(labelize).join('; ')}. Effect publication remains withheld until the identifying panel, common support, pre-trend equivalence, placebo and negative-control tests, leave-one-out sensitivity and independent review all pass.`,
    ],
  ];
  attributionGate.getRange('A41:J46').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  attributionGate.getRange('A48:J48').merge();
  attributionGate.getRange('A48').values = [
    [
      `Contract hash: ${attributionReadiness.contract_sha256} · investment-control output hash: ${investmentControlReport.output_sha256} · macro-control output hash: ${regionalMacroReport.output_sha256} · permit proxy output hash: ${permitProxyReport.output_sha256}`,
    ],
  ];
  attributionGate.getRange('A48').format = {
    font: { name: 'Aptos Mono', size: 8, color: C.muted },
  };
  attributionGate.freezePanes.freezeRows(4);
  setWidths(
    attributionGate,
    {
      A: 31,
      B: 26,
      C: 17,
      D: 40,
      E: 40,
      F: 34,
      G: 18,
      H: 58,
      I: 16,
      J: 16,
    },
    48,
  );
}

function buildPanelPreflight() {
  titleBand(
    panelPreflightSheet,
    'AI-attribution panel acquisition preflight',
    'Candidate scope, evidence receipts and field-complete acquisition queue · zero-row fail-closed boundary',
    'J',
  );

  const cards = [
    ['A5:B5', 'A6:B8', 'Candidate CMAs', '=COUNTA(A14:A18)'],
    ['C5:D5', 'C6:D8', 'Potential treated', '=COUNTIF(D14:D18,"potential_treated")'],
    ['E5:F5', 'E6:F8', 'Potential controls', '=COUNTIF(D14:D18,"potential_control")'],
    ['G5:H5', 'G6:H8', 'Fields queued', '=SUM(E22:E25)'],
    ['I5:J5', 'I6:J8', 'Assembled panel rows', `=${attributionPanelPreflight.current_eligibility.assembled_panel_row_count}`],
  ];
  for (const [labelRange, valueRange, label, formula] of cards) {
    card(panelPreflightSheet, labelRange, valueRange, label, formula);
  }
  panelPreflightSheet.getRange('A10:J10').merge();
  panelPreflightSheet.getRange('A10').values = [[
    `Eligibility now: ${attributionPanelPreflight.current_eligibility.authorizing_treated_region_count} authorizing treated regions · ${attributionPanelPreflight.current_eligibility.eligible_control_region_count} eligible controls · ${attributionPanelPreflight.current_eligibility.eligible_asset_class_count} eligible asset classes · effect estimation ${attributionPanelPreflight.publication_boundary.effect_estimation_authorized ? 'AUTHORIZED' : 'NOT AUTHORIZED'}. Candidate scope never confers eligibility.`,
  ]];
  panelPreflightSheet.getRange('A10:J10').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  panelPreflightSheet.getRange('A10').format.rowHeight = 38;

  panelPreflightSheet.getRange('A12:H12').merge();
  panelPreflightSheet.getRange('A12').values = [['Candidate geography frame']];
  sectionHeader(panelPreflightSheet.getRange('A12:H12'));
  panelPreflightSheet.getRange('A13:D13').values = [[
    'Geography ID',
    'Geography',
    'Province ID',
    'Cohort role',
  ]];
  header(panelPreflightSheet.getRange('A13:D13'));
  const candidateRegionRows = attributionPanelPreflight.candidate_scope.regions.map((region) => [
    region.geography_id,
    region.geography_label,
    region.province_id,
    region.cohort_role,
  ]);
  panelPreflightSheet.getRange('A14:D18').values = candidateRegionRows;
  panelPreflightSheet.getRange('A14:D18').format = {
    fill: C.white,
    font: { color: C.ink, size: 9 },
    borders: { insideHorizontal: { style: 'thin', color: C.line }, bottom: { style: 'thin', color: C.line } },
  };
  panelPreflightSheet.getRange('D14:D18').conditionalFormats.add('containsText', {
    text: 'potential_treated',
    format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } },
  });
  panelPreflightSheet.getRange('D14:D18').conditionalFormats.add('containsText', {
    text: 'potential_control',
    format: { fill: '#EAF1F4', font: { color: '#365D6D', bold: true } },
  });
  const candidateTable = panelPreflightSheet.tables.add('A13:D18', true, 'PanelCandidateRegions');
  candidateTable.style = 'TableStyleLight9';

  panelPreflightSheet.getRange('F12:J12').merge();
  panelPreflightSheet.getRange('F12').values = [['Candidate asset-class frame · not eligibility']];
  sectionHeader(panelPreflightSheet.getRange('F12:J12'), C.teal);
  panelPreflightSheet.getRange('F13:J18').merge();
  panelPreflightSheet.getRange('F13').values = [[
    `${attributionPanelPreflight.candidate_scope.asset_class_count} candidate classes: ${attributionPanelPreflight.candidate_scope.asset_classes.map(labelize).join('; ')}. The design minimum is ${attributionPanelPreflight.design_thresholds.minimum_asset_classes}; the current eligible count is ${attributionPanelPreflight.current_eligibility.eligible_asset_class_count}. ${attributionPanelPreflight.panel_assembly.reason}`,
  ]];
  noteBlock(panelPreflightSheet.getRange('F13:J18'));

  panelPreflightSheet.getRange('A20:J20').merge();
  panelPreflightSheet.getRange('A20').values = [['Operational acquisition queue']];
  sectionHeader(panelPreflightSheet.getRange('A20:J20'));
  panelPreflightSheet.getRange('A21:I21').values = [[
    'Task ID',
    'Priority',
    'Domain',
    'Required fields',
    'Field count',
    'Minimum geographies',
    'Frequency',
    'Current status',
    'Completion rule / candidate sources',
  ]];
  header(panelPreflightSheet.getRange('A21:I21'));
  const queueRows = attributionPanelPreflight.acquisition_queue.map((task) => [
    task.task_id,
    task.priority,
    task.domain_id,
    task.required_fields.join('; '),
    task.required_fields.length,
    task.minimum_geography_count,
    task.minimum_frequency,
    task.current_status,
    `${task.completion_rule} Sources: ${task.candidate_source_ids.join('; ')}.`,
  ]);
  panelPreflightSheet.getRange('A22:I25').values = queueRows;
  panelPreflightSheet.getRange('A22:I25').format = {
    fill: C.white,
    font: { color: C.ink, size: 8 },
    wrapText: true,
    verticalAlignment: 'top',
    borders: { insideHorizontal: { style: 'thin', color: C.line }, bottom: { style: 'thin', color: C.line } },
  };
  panelPreflightSheet.getRange('A22:C25').format.font = { bold: true, color: C.ink, size: 8 };
  panelPreflightSheet.getRange('H22:H25').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826', size: 8 },
    wrapText: true,
  };
  panelPreflightSheet.getRange('A22:I25').format.rowHeight = 72;
  const queueTable = panelPreflightSheet.tables.add('A21:I25', true, 'PanelAcquisitionQueue');
  queueTable.style = 'TableStyleLight9';

  panelPreflightSheet.getRange('A27:J27').merge();
  panelPreflightSheet.getRange('A27').values = [['Hash-locked evidence receipts · none authorizing']];
  sectionHeader(panelPreflightSheet.getRange('A27:J27'), C.teal);
  panelPreflightSheet.getRange('A28:J28').values = [[
    'Receipt ID',
    'Domain',
    'Geographies',
    'Evidence status',
    'Authorizing status',
    'Variables',
    'Source IDs',
    'Assertions',
    'Artifact path',
    'Artifact SHA-256',
  ]];
  header(panelPreflightSheet.getRange('A28:J28'));
  const receiptRows = attributionPanelPreflight.evidence_receipts.map((receipt) => [
    receipt.receipt_id,
    receipt.domain_id,
    receipt.geography_ids.join('; '),
    receipt.evidence_status,
    receipt.authorizing_status,
    receipt.available_variables.join('; '),
    receipt.source_ids.join('; '),
    `${receipt.assertion_count}/${receipt.assertion_count} ${receipt.assertions_passed ? 'PASS' : 'FAIL'}`,
    receipt.artifact_path,
    receipt.artifact_sha256,
  ]);
  panelPreflightSheet.getRange('A29:J39').values = receiptRows;
  panelPreflightSheet.getRange('A29:J39').format = {
    fill: C.white,
    font: { color: C.ink, size: 8 },
    wrapText: true,
    verticalAlignment: 'top',
    borders: { insideHorizontal: { style: 'thin', color: C.line }, bottom: { style: 'thin', color: C.line } },
  };
  panelPreflightSheet.getRange('A29:B39').format.font = { bold: true, color: C.ink, size: 8 };
  panelPreflightSheet.getRange('E29:E39').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826', size: 8 },
  };
  panelPreflightSheet.getRange('H29:H39').conditionalFormats.add('containsText', {
    text: 'PASS',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  panelPreflightSheet.getRange('A29:J39').format.rowHeight = 58;
  const receiptTable = panelPreflightSheet.tables.add('A28:J39', true, 'PanelEvidenceReceipts');
  receiptTable.style = 'TableStyleLight9';

  panelPreflightSheet.getRange('A41:J41').merge();
  panelPreflightSheet.getRange('A41').values = [['PSPE and publication boundary']];
  sectionHeader(panelPreflightSheet.getRange('A41:J41'), C.amber);
  panelPreflightSheet.getRange('A42:J45').merge();
  panelPreflightSheet.getRange('A42').values = [[
    `${attributionPanelPreflight.pspe_role} Every ${attributionPanelPreflight.field_gap_summary.required_field_instance_count} locked field instance is assigned to an acquisition task, but ${attributionPanelPreflight.field_gap_summary.complete_authorizing_scope_count} authorizing scopes are complete and ${attributionPanelPreflight.current_eligibility.assembled_panel_row_count} panel rows are assembled. Cost escalation and schedule-delay effects remain null.`,
  ]];
  panelPreflightSheet.getRange('A42:J45').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  panelPreflightSheet.getRange('A46:J46').merge();
  panelPreflightSheet.getRange('A46').values = [[
    `Preflight ${attributionPanelPreflight.preflight_id} · contract ${attributionPanelPreflight.contract_id} · evidence status ${attributionPanelPreflight.evidence_status}`,
  ]];
  panelPreflightSheet.getRange('A46').format = {
    font: { name: 'Aptos Mono', size: 8, color: C.muted },
  };
  panelPreflightSheet.freezePanes.freezeRows(4);
  setWidths(
    panelPreflightSheet,
    {
      A: 31,
      B: 16,
      C: 31,
      D: 46,
      E: 15,
      F: 18,
      G: 38,
      H: 28,
      I: 68,
      J: 66,
    },
    46,
  );
}

function buildTreatmentSources() {
  titleBand(
    treatmentSourcesSheet,
    'AI-construction treatment source qualification',
    'Eight public-source candidates · seven non-substitutable authorizing gates · zero eligible sources',
    'M',
  );

  card(treatmentSourcesSheet, 'A5:C5', 'A6:C8', 'Sources screened', `=${treatmentSourceFeasibility.candidate_count}`);
  card(treatmentSourcesSheet, 'D5:F5', 'D6:F8', 'Required gates', `=${treatmentSourceFeasibility.required_authorizing_gates.length}`);
  card(treatmentSourcesSheet, 'G5:I5', 'G6:I8', 'Qualifying sources', `=${treatmentSourceFeasibility.authorizing_candidate_count}`);
  card(treatmentSourcesSheet, 'J5:M5', 'J6:M8', 'Treatment authorized', treatmentSourceFeasibility.publication_boundary.treatment_authorized ? '="YES"' : '="NO"');
  treatmentSourcesSheet.getRange('J6:M8').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826', size: 21 },
    horizontalAlignment: 'center',
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  treatmentSourcesSheet.getRange('A10:M11').merge();
  treatmentSourcesSheet.getRange('A10').values = [[
    'ALL-GATES RULE. Passing several characteristics cannot be averaged into treatment eligibility. A failed gate changes what the measure means. Zero eligible sources means treatment is unidentified—not that AI-construction activity is zero.',
  ]];
  treatmentSourcesSheet.getRange('A10:M11').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  const gateLabels = {
    ai_or_data_centre_specific: 'AI / data centre',
    construction_activity_specific: 'Construction',
    realized_not_intended: 'Realized',
    region_or_project_linkable: 'Linked',
    quarterly_or_finer: 'Quarterly+',
    publicly_retrievable: 'Public',
    revision_provenance_available: 'Revisions',
  };
  const gates = treatmentSourceFeasibility.required_authorizing_gates;
  treatmentSourcesSheet.getRange('A13:M13').values = [[
    'Candidate ID',
    'Source',
    'Analytical role',
    ...gates.map((gate) => gateLabels[gate]),
    'Passed gates',
    'Result',
    'Exclusion reason',
  ]];
  header(treatmentSourcesSheet.getRange('A13:M13'));
  const rows = treatmentSourceFeasibility.candidates.map((candidate) => [
    candidate.candidate_id,
    candidate.source_title,
    labelize(candidate.analytical_role),
    ...gates.map((gate) => candidate.gate_assessment[gate] ? 'PASS' : 'FAIL'),
    candidate.passed_gate_count,
    'EXCLUDED',
    candidate.exclusion_reason,
  ]);
  treatmentSourcesSheet.getRange('A14:M21').values = rows;
  treatmentSourcesSheet.getRange('A14:M21').format = {
    fill: C.white,
    font: { color: C.ink, size: 8 },
    wrapText: true,
    verticalAlignment: 'top',
    borders: {
      insideHorizontal: { style: 'thin', color: C.line },
      bottom: { style: 'thin', color: C.line },
    },
  };
  treatmentSourcesSheet.getRange('A14:C21').format.font = { bold: true, color: C.ink, size: 8 };
  treatmentSourcesSheet.getRange('D14:J21').format.horizontalAlignment = 'center';
  treatmentSourcesSheet.getRange('K14:L21').format.horizontalAlignment = 'center';
  treatmentSourcesSheet.getRange('A14:M21').format.rowHeight = 58;
  treatmentSourcesSheet.getRange('D14:J21').conditionalFormats.add('containsText', {
    text: 'PASS',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  treatmentSourcesSheet.getRange('D14:J21').conditionalFormats.add('containsText', {
    text: 'FAIL',
    format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } },
  });
  treatmentSourcesSheet.getRange('L14:L21').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826', size: 8 },
    horizontalAlignment: 'center',
  };
  const table = treatmentSourcesSheet.tables.add('A13:M21', true, 'TreatmentSourceQualification');
  table.style = 'TableStyleLight9';

  treatmentSourcesSheet.getRange('A23:M23').merge();
  treatmentSourcesSheet.getRange('A23').values = [['Acquisition decision and publication boundary']];
  sectionHeader(treatmentSourcesSheet.getRange('A23:M23'), C.amber);
  treatmentSourcesSheet.getRange('A24:M27').merge();
  treatmentSourcesSheet.getRange('A24').values = [[
    `Status: ${labelize(treatmentSourceFeasibility.acquisition_decision.status)}. Next evidence required: ${treatmentSourceFeasibility.acquisition_decision.next_evidence_needed} Search boundary: ${treatmentSourceFeasibility.acquisition_decision.search_boundary}`,
  ]];
  treatmentSourcesSheet.getRange('A24:M27').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  treatmentSourcesSheet.getRange('A29:C33').values = [
    ['Publication field', 'Value', 'Interpretation'],
    ['Authorizing treatment measure', treatmentSourceFeasibility.publication_boundary.authorizing_treatment_measure, 'Must remain blank without an authorizing source'],
    ['AI-attributable cost effect', treatmentSourceFeasibility.publication_boundary.ai_attributable_cost_effect, 'Null—not zero'],
    ['AI-attributable schedule effect', treatmentSourceFeasibility.publication_boundary.ai_attributable_schedule_effect, 'Null—not zero'],
    ['Evidence status', treatmentSourceFeasibility.evidence_status, 'Observed source capability; inferred eligibility'],
  ];
  header(treatmentSourcesSheet.getRange('A29:C29'));
  treatmentSourcesSheet.getRange('A30:C33').format = {
    fill: C.white,
    font: { color: C.ink, size: 9 },
    wrapText: true,
    borders: { insideHorizontal: { style: 'thin', color: C.line }, bottom: { style: 'thin', color: C.line } },
  };
  treatmentSourcesSheet.getRange('A35:M35').merge();
  treatmentSourcesSheet.getRange('A35').values = [[
    `Feasibility ${treatmentSourceFeasibility.feasibility_id} · contract SHA-256 ${treatmentSourceFeasibility.input_manifest.contract_sha256} · registry SHA-256 ${treatmentSourceFeasibility.input_manifest.registry_sha256}`,
  ]];
  treatmentSourcesSheet.getRange('A35').format = { font: { name: 'Aptos Mono', size: 8, color: C.muted } };
  treatmentSourcesSheet.freezePanes.freezeRows(13);
  setWidths(treatmentSourcesSheet, {
    A: 34, B: 38, C: 22, D: 13, E: 13, F: 12, G: 12, H: 12, I: 12, J: 12, K: 12, L: 14, M: 70,
  }, 35);
}

function buildInvestmentControls() {
  titleBand(
    investmentControls,
    'Canada regional building-investment controls',
    `Statistics Canada ${investmentControlReport.source_id} · quarterly control panel through ${investmentControlReport.as_of_date}`,
    'R',
  );

  const summaryCards = [
    ['A5:C5', 'A6:C6', 'Observations', investmentControlReport.observation_count],
    ['D5:F5', 'D6:F6', 'Geographies', investmentControlReport.geography_count],
    ['G5:I5', 'G6:I6', 'Quarters', investmentControlReport.quarter_count],
    ['J5:L5', 'J6:L6', 'Latest period', investmentControlReport.as_of_date],
    ['M5:O5', 'M6:O6', 'Source evidence', 'observed monthly'],
    ['P5:R5', 'P6:R6', 'Panel evidence', 'inferred quarterly'],
  ];
  for (const [labelRange, valueRange, label, value] of summaryCards) {
    investmentControls.getRange(labelRange).merge();
    investmentControls.getRange(labelRange.split(':')[0]).values = [[label]];
    investmentControls.getRange(labelRange).format = {
      fill: C.tealLight,
      font: { bold: true, color: C.tealDark, size: 9 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
    };
    investmentControls.getRange(valueRange).merge();
    investmentControls.getRange(valueRange.split(':')[0]).values = [[value]];
    investmentControls.getRange(valueRange).format = {
      fill: C.white,
      font: { bold: true, color: C.ink, size: 14 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
    };
  }
  investmentControls.getRange('A6:I6').format.numberFormat = '#,##0';

  investmentControls.getRange('A8:R8').merge();
  investmentControls.getRange('A8').values = [
    [
      `REGIONAL CONTROL ONLY. ${investmentControlReport.publication_boundary.reason} Values are sums of three contiguous observed monthly values; incomplete quarters remain missing.`,
    ],
  ];
  investmentControls.getRange('A8:R8').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  investmentControls.getRange('A8').format.rowHeight = 42;

  const headers = [
    'observation_id',
    'indicator_id',
    'geography_label',
    'statcan_dguid',
    'type_of_structure',
    'investment_basis',
    'value',
    'unit',
    'geography_id',
    'period_start',
    'period_end',
    'source_id',
    'source_evidence_status',
    'evidence_status',
    'transformation_id',
    'source_month_count',
    'quality_flags',
    'source_url',
  ];
  investmentControls.getRange('A10:R10').values = [headers];
  header(investmentControls.getRange('A10:R10'));
  const sourceUrl = currentSourceRegistry.sources.find(
    (source) => source.source_id === investmentControlReport.source_id,
  )?.canonical_url;
  const rows = investmentControlRows.map((row) => [
    row.observation_id,
    row.indicator_id,
    row.geography_label,
    row.statcan_dguid,
    row.type_of_structure,
    row.investment_basis,
    numberOrNull(row.value),
    row.unit,
    row.geography_id,
    new Date(`${row.period_start}T00:00:00Z`),
    new Date(`${row.period_end}T00:00:00Z`),
    row.source_id,
    row.source_evidence_status,
    row.evidence_status,
    row.transformation_id,
    numberOrNull(row.source_month_count),
    row.quality_flags,
    sourceUrl ?? '',
  ]);
  const lastRow = 10 + rows.length;
  investmentControls.getRange(`A11:R${lastRow}`).values = rows;
  investmentControls.getRange(`G11:G${lastRow}`).format.numberFormat = '$#,##0';
  investmentControls.getRange(`J11:K${lastRow}`).format.numberFormat =
    'yyyy-mm-dd';
  investmentControls.getRange(`P11:P${lastRow}`).format.numberFormat = '#,##0';
  investmentControls.getRange(`A11:B${lastRow}`).format.font = {
    name: 'Aptos Mono',
    size: 8,
    color: C.ink,
  };
  investmentControls.getRange(`L11:O${lastRow}`).format.font = {
    name: 'Aptos Mono',
    size: 8,
    color: C.tealDark,
  };
  investmentControls.getRange(`R11:R${lastRow}`).format.font = {
    size: 8,
    color: C.blueInput,
  };
  const table = investmentControls.tables.add(
    `A10:R${lastRow}`,
    true,
    'InvestmentControlsTable',
  );
  table.style = 'TableStyleMedium2';
  investmentControls.freezePanes.freezeRows(10);
  investmentControls.freezePanes.freezeColumns(3);
  const widths = {
    A: 27,
    B: 48,
    C: 40,
    D: 17,
    E: 38,
    F: 36,
    G: 17,
    H: 20,
    I: 16,
    J: 15,
    K: 15,
    L: 24,
    M: 22,
    N: 18,
    O: 39,
    P: 18,
    Q: 30,
    R: 48,
  };
  for (const [column, width] of Object.entries(widths)) {
    investmentControls.getRange(`${column}1:${column}${lastRow}`).format.columnWidth =
      width;
  }
}

function buildRegionalMacro() {
  titleBand(
    regionalMacro,
    'Canada regional macro controls',
    `Seven separate quarterly controls · 2017 Q1 through ${regionalMacroReport.common_latest_period_end} · descriptive only`,
    'S',
  );

  const summaryCards = [
    ['A5:C5', 'A6:C6', 'Observations', regionalMacroReport.observation_count],
    ['D5:F5', 'D6:F6', 'Series', regionalMacroReport.series_count],
    ['G5:I5', 'G6:I6', 'Metrics', regionalMacroReport.metric_count],
    ['J5:L5', 'J6:L6', 'Jurisdictions', regionalMacroReport.province_and_territory_count],
    ['M5:O5', 'M6:O6', 'Quarters', regionalMacroReport.quarter_count],
    ['P5:S5', 'P6:S6', 'Latest common period', regionalMacroReport.common_latest_period_end],
  ];
  for (const [labelRange, valueRange, label, value] of summaryCards) {
    regionalMacro.getRange(labelRange).merge();
    regionalMacro.getRange(labelRange.split(':')[0]).values = [[label]];
    regionalMacro.getRange(labelRange).format = {
      fill: C.tealLight,
      font: { bold: true, color: C.tealDark, size: 9 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
    };
    regionalMacro.getRange(valueRange).merge();
    regionalMacro.getRange(valueRange.split(':')[0]).values = [[value]];
    regionalMacro.getRange(valueRange).format = {
      fill: C.white,
      font: { bold: true, color: C.ink, size: 14 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
    };
  }
  regionalMacro.getRange('A6:O6').format.numberFormat = '#,##0';

  regionalMacro.getRange('A8:S8').merge();
  regionalMacro.getRange('A8').values = [
    [
      `DESCRIPTIVE CONTROLS ONLY. ${regionalMacroReport.publication_boundary.reason} Quarterly averages, sums and year-over-year changes are inferred transformations of observed source values.`,
    ],
  ];
  regionalMacro.getRange('A8:S8').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  regionalMacro.getRange('A8').format.rowHeight = 42;

  regionalMacro.getRange('A10:N10').merge();
  regionalMacro.getRange('A10').values = [
    [`Latest Alberta context · year-over-year change through ${regionalMacroReport.common_latest_period_end}`],
  ];
  sectionHeader(regionalMacro.getRange('A10:N10'));
  const contextColumns = [
    ['A', 'B'],
    ['C', 'D'],
    ['E', 'F'],
    ['G', 'H'],
    ['I', 'J'],
    ['K', 'L'],
    ['M', 'N'],
  ];
  regionalMacroReport.latest_alberta_controls.forEach((item, index) => {
    const [startColumn, endColumn] = contextColumns[index];
    const labelRange = `${startColumn}11:${endColumn}11`;
    const valueRange = `${startColumn}12:${endColumn}12`;
    regionalMacro.getRange(labelRange).merge();
    regionalMacro.getRange(labelRange.split(':')[0]).values = [[item.indicator_label]];
    regionalMacro.getRange(labelRange).format = {
      fill: '#EDF3F5',
      font: { color: '#365D6D', bold: true, size: 8 },
      wrapText: true,
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#C5D4DA' },
    };
    regionalMacro.getRange(valueRange).merge();
    regionalMacro.getRange(valueRange.split(':')[0]).values = [[
      item.year_over_year_change_percent === null
        ? null
        : item.year_over_year_change_percent / 100,
    ]];
    regionalMacro.getRange(valueRange).format = {
      fill: C.white,
      font: { color: C.ink, bold: true, size: 12 },
      numberFormat: '0.0%;[Red]-0.0%',
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#C5D4DA' },
    };
  });
  regionalMacro.getRange('A11:N11').format.rowHeight = 34;

  regionalMacro.getRange('A14:S14').merge();
  regionalMacro.getRange('A14').values = [[
    'CPI and housing-start series cover ten provinces. Population and weekly earnings cover all 13 provinces and territories. Missing territorial values are not filled from national or capital-city proxies.',
  ]];
  noteBlock(regionalMacro.getRange('A14:S14'));

  const headers = [
    'observation_id',
    'indicator_id',
    'indicator_label',
    'geography_id',
    'geography_label',
    'statcan_dguid',
    'period_start',
    'period_end',
    'value',
    'unit',
    'year_over_year_change_percent',
    'source_id',
    'source_url',
    'source_evidence_status',
    'evidence_status',
    'transformation_id',
    'aggregation_method',
    'source_observation_count',
    'quality_flags',
  ];
  regionalMacro.getRange('A16:S16').values = [headers];
  header(regionalMacro.getRange('A16:S16'));
  const rows = regionalMacroRows.map((row) => [
    row.observation_id,
    row.indicator_id,
    row.indicator_label,
    row.geography_id,
    row.geography_label,
    row.statcan_dguid,
    new Date(`${row.period_start}T00:00:00Z`),
    new Date(`${row.period_end}T00:00:00Z`),
    numberOrNull(row.value),
    row.unit,
    row.year_over_year_change_percent === ''
      ? null
      : Number(row.year_over_year_change_percent) / 100,
    row.source_id,
    row.source_url,
    row.source_evidence_status,
    row.evidence_status,
    row.transformation_id,
    row.aggregation_method,
    numberOrNull(row.source_observation_count),
    row.quality_flags,
  ]);
  const lastRow = 16 + rows.length;
  regionalMacro.getRange(`A17:S${lastRow}`).values = rows;
  regionalMacro.getRange(`G17:H${lastRow}`).format.numberFormat = 'yyyy-mm-dd';
  regionalMacro.getRange(`I17:I${lastRow}`).format.numberFormat = '#,##0.00';
  regionalMacro.getRange(`K17:K${lastRow}`).format.numberFormat = '0.0%;[Red]-0.0%';
  regionalMacro.getRange(`R17:R${lastRow}`).format.numberFormat = '#,##0';
  regionalMacro.getRange(`A17:B${lastRow}`).format.font = {
    name: 'Aptos Mono',
    size: 8,
    color: C.ink,
  };
  regionalMacro.getRange(`L17:P${lastRow}`).format.font = {
    name: 'Aptos Mono',
    size: 8,
    color: C.tealDark,
  };
  regionalMacro.getRange(`M17:M${lastRow}`).format.font = {
    size: 8,
    color: C.blueInput,
  };
  const table = regionalMacro.tables.add(
    `A16:S${lastRow}`,
    true,
    'RegionalMacroControlsTable',
  );
  table.style = 'TableStyleMedium2';
  regionalMacro.freezePanes.freezeRows(16);
  regionalMacro.freezePanes.freezeColumns(3);
  setWidths(
    regionalMacro,
    {
      A: 27,
      B: 48,
      C: 44,
      D: 15,
      E: 28,
      F: 17,
      G: 14,
      H: 14,
      I: 18,
      J: 38,
      K: 22,
      L: 28,
      M: 48,
      N: 22,
      O: 18,
      P: 40,
      Q: 42,
      R: 18,
      S: 42,
    },
    lastRow,
  );
}

function buildProcurementIntake() {
  titleBand(
    procurementIntake,
    'CanadaBuys construction procurement outcome-feasibility intake',
    `Federal fiscal-year 2026-2027 files · as of ${procurementOutcomeReport.as_of_date} · research only`,
    'X',
  );

  const summaryCards = [
    ['A5:D5', 'A6:D6', 'Construction linkages', procurementOutcomeReport.construction_linkage_count],
    ['E5:H5', 'E6:H6', 'Tender + award', procurementOutcomeReport.linked_tender_award_count],
    ['I5:L5', 'I6:L6', 'Tender + contract', procurementOutcomeReport.linked_tender_contract_count],
    [
      'M5:P5',
      'M6:P6',
      'Positive award value',
      procurementOutcomeReport.field_availability.reported_award_value_cad,
    ],
    [
      'Q5:T5',
      'Q6:T6',
      'Single-province geography',
      procurementOutcomeReport.single_province_geography_count,
    ],
    ['U5:X5', 'U6:X6', 'CMA geography', procurementOutcomeReport.cma_geography_count],
  ];
  for (const [labelRange, valueRange, label, value] of summaryCards) {
    procurementIntake.getRange(labelRange).merge();
    procurementIntake.getRange(labelRange.split(':')[0]).values = [[label]];
    procurementIntake.getRange(labelRange).format = {
      fill: C.tealLight,
      font: { bold: true, color: C.tealDark, size: 9 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
    };
    procurementIntake.getRange(valueRange).merge();
    procurementIntake.getRange(valueRange.split(':')[0]).values = [[value]];
    procurementIntake.getRange(valueRange).format = {
      fill: C.white,
      font: { bold: true, color: C.ink, size: 14 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
    };
  }
  procurementIntake.getRange('A6:X6').format.numberFormat = '#,##0';

  procurementIntake.getRange('A8:X8').merge();
  procurementIntake.getRange('A8').values = [
    [
      `PROCUREMENT FEASIBILITY ONLY. ${procurementOutcomeReport.publication_boundary.reason} Procurement-instrument dates are not physical construction dates. Generated linkage IDs are not physical-project IDs, and null authorizing outcome fields are not zero effects.`,
    ],
  ];
  procurementIntake.getRange('A8:X8').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  procurementIntake.getRange('A8').format.rowHeight = 48;

  const headers = [
    'procurement_linkage_id',
    'solicitation_number',
    'title',
    'geography_id',
    'geography_label',
    'geography_evidence_status',
    'tender_publication_date',
    'tender_close_date',
    'tender_duration_days',
    'award_record_count',
    'award_date',
    'reported_award_value_cad',
    'contract_record_count',
    'contract_amendment_row_count',
    'reported_total_contract_value_cad',
    'reported_contract_start_date',
    'reported_contract_end_date',
    'cost_outcome_status',
    'schedule_outcome_status',
    'competition_outcome_status',
    'source_ids',
    'source_evidence_status',
    'evidence_status',
    'quality_flags',
  ];
  procurementIntake.getRange('A10:X10').values = [headers];
  header(procurementIntake.getRange('A10:X10'));
  const rows = procurementOutcomeRows.map((row) => [
    row.procurement_linkage_id,
    row.solicitation_number,
    row.title,
    row.geography_id,
    row.geography_label,
    row.geography_evidence_status,
    dateOrNull(row.tender_publication_date),
    dateOrNull(row.tender_close_date),
    numberOrNull(row.tender_duration_days),
    numberOrNull(row.award_record_count),
    dateOrNull(row.award_date),
    numberOrNull(row.reported_award_value_cad),
    numberOrNull(row.contract_record_count),
    numberOrNull(row.contract_amendment_row_count),
    numberOrNull(row.reported_total_contract_value_cad),
    dateOrNull(row.reported_contract_start_date),
    dateOrNull(row.reported_contract_end_date),
    row.cost_outcome_status,
    row.schedule_outcome_status,
    row.competition_outcome_status,
    row.source_ids,
    row.source_evidence_status,
    row.evidence_status,
    row.quality_flags,
  ]);
  const lastRow = 10 + rows.length;
  procurementIntake.getRange(`A11:X${lastRow}`).values = rows;
  procurementIntake.getRange(`G11:H${lastRow}`).format.numberFormat = 'yyyy-mm-dd';
  procurementIntake.getRange(`K11:K${lastRow}`).format.numberFormat = 'yyyy-mm-dd';
  procurementIntake.getRange(`P11:Q${lastRow}`).format.numberFormat = 'yyyy-mm-dd';
  procurementIntake.getRange(`L11:L${lastRow}`).format.numberFormat = '$#,##0';
  procurementIntake.getRange(`O11:O${lastRow}`).format.numberFormat = '$#,##0';
  procurementIntake.getRange(`A11:B${lastRow}`).format.font = {
    name: 'Aptos Mono',
    size: 8,
    color: C.ink,
  };
  procurementIntake.getRange(`U11:W${lastRow}`).format.font = {
    name: 'Aptos Mono',
    size: 8,
    color: C.tealDark,
  };
  procurementIntake.getRange(`R11:T${lastRow}`).format = {
    fill: C.amberLight,
    font: { color: '#8A4826', size: 8 },
  };
  const table = procurementIntake.tables.add(
    `A10:X${lastRow}`,
    true,
    'ProcurementIntakeTable',
  );
  table.style = 'TableStyleMedium2';
  procurementIntake.freezePanes.freezeRows(10);
  procurementIntake.freezePanes.freezeColumns(3);
  const widths = {
    A: 28,
    B: 24,
    C: 54,
    D: 15,
    E: 28,
    F: 25,
    G: 16,
    H: 16,
    I: 16,
    J: 15,
    K: 16,
    L: 20,
    M: 17,
    N: 19,
    O: 24,
    P: 17,
    Q: 17,
    R: 23,
    S: 23,
    T: 26,
    U: 48,
    V: 18,
    W: 23,
    X: 62,
  };
  for (const [column, width] of Object.entries(widths)) {
    procurementIntake.getRange(`${column}1:${column}${lastRow}`).format.columnWidth =
      width;
  }
}

function buildPermitProxy() {
  titleBand(
    permitProxy,
    'Edmonton data-centre permit activity proxy',
    `City of Edmonton issued-permit screen · ${permitProxyReport.period_start} to ${permitProxyReport.period_end} · research only`,
    'M',
  );

  const summaryCards = [
    ['A5:B5', 'A6:B6', 'Broad keyword screen', permitProxyReport.broad_screen_row_count],
    ['C5:D5', 'C6:D6', 'Data-centre candidates', permitProxyReport.data_centre_candidate_count],
    ['E5:F5', 'E6:F6', 'Candidates since 2018', permitProxyReport.data_centre_candidate_count_since_2018],
    ['G5:H5', 'G6:H6', 'Explicit AI references', permitProxyReport.explicit_ai_reference_count],
    ['I5:J5', 'I6:J6', 'Candidate occupancy dates', permitProxyReport.data_centre_candidate_occupancy_date_available_count],
    [
      'K5:M5',
      'K6:M6',
      'Reported permit estimate proxy',
      permitProxyReport.data_centre_candidate_reported_value_total_cad_proxy,
    ],
  ];
  for (const [labelRange, valueRange, label, value] of summaryCards) {
    permitProxy.getRange(labelRange).merge();
    permitProxy.getRange(labelRange.split(':')[0]).values = [[label]];
    permitProxy.getRange(labelRange).format = {
      fill: C.tealLight,
      font: { bold: true, color: C.tealDark, size: 9 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
    };
    permitProxy.getRange(valueRange).merge();
    permitProxy.getRange(valueRange.split(':')[0]).values = [[value]];
    permitProxy.getRange(valueRange).format = {
      fill: C.white,
      font: { bold: true, color: C.ink, size: 16 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
    };
  }
  permitProxy.getRange('A6:J6').format.numberFormat = '#,##0';
  permitProxy.getRange('K6:M6').format.numberFormat = '$#,##0';

  permitProxy.getRange('A8:M8').merge();
  permitProxy.getRange('A8').values = [
    [
      `NON-AUTHORIZING MUNICIPAL ACTIVITY PROXY. ${permitProxyReport.publication_boundary.reason} The CAD ${permitProxyReport.data_centre_candidate_reported_value_total_cad_proxy.toLocaleString('en-CA')} aggregate includes one demolition candidate; the non-demolition candidate aggregate is CAD ${permitProxyReport.data_centre_candidate_non_demolition_reported_value_total_cad_proxy.toLocaleString('en-CA')}. Neither is AI capex.`,
    ],
  ];
  permitProxy.getRange('A8:M8').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  permitProxy.getRange('A8').format.rowHeight = 62;

  const classificationCards = [
    [
      'A10:D10',
      'A11:D11',
      'Explicit data-centre reference',
      permitProxyReport.classification_counts.explicit_data_centre_reference,
    ],
    [
      'E10:H10',
      'E11:H11',
      'Server reference only',
      permitProxyReport.classification_counts.server_reference_only,
    ],
    [
      'I10:M10',
      'I11:M11',
      'Broad-query substring false positive',
      permitProxyReport.classification_counts.broad_query_substring_false_positive,
    ],
  ];
  for (const [labelRange, valueRange, label, value] of classificationCards) {
    permitProxy.getRange(labelRange).merge();
    permitProxy.getRange(labelRange.split(':')[0]).values = [[label]];
    permitProxy.getRange(labelRange).format = {
      fill: C.soft,
      font: { bold: true, color: C.muted, size: 9 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: C.line },
    };
    permitProxy.getRange(valueRange).merge();
    permitProxy.getRange(valueRange.split(':')[0]).values = [[value]];
    permitProxy.getRange(valueRange).format = {
      fill: C.white,
      font: { bold: true, color: C.ink, size: 13 },
      horizontalAlignment: 'center',
      verticalAlignment: 'center',
      borders: { preset: 'outside', style: 'thin', color: C.line },
    };
  }

  const headers = [
    'permit_proxy_id',
    'issue_date',
    'job_category',
    'building_type',
    'work_type',
    'matched_terms',
    'reported_estimated_value_cad_proxy',
    'floor_area_sq_ft',
    'occupancy_status',
    'ai_specificity_status',
    'classification_evidence_status',
    'description_sha256',
    'quality_flags',
  ];
  permitProxy.getRange('A13:M13').values = [headers];
  header(permitProxy.getRange('A13:M13'));
  const candidateRows = permitProxyRows
    .filter((row) => row.candidate_status === 'data_centre_candidate')
    .map((row) => [
      row.permit_proxy_id,
      dateOrNull(row.issue_date),
      row.job_category,
      row.building_type,
      row.work_type,
      row.matched_terms,
      numberOrNull(row.reported_estimated_construction_value_cad),
      numberOrNull(row.floor_area_sq_ft),
      row.occupancy_date_status,
      row.ai_specificity_status,
      row.classification_evidence_status,
      row.description_sha256,
      row.quality_flags,
    ]);
  const candidateLastRow = 13 + candidateRows.length;
  permitProxy.getRange(`A14:M${candidateLastRow}`).values = candidateRows;
  permitProxy.getRange(`B14:B${candidateLastRow}`).format.numberFormat = 'yyyy-mm-dd';
  permitProxy.getRange(`G14:G${candidateLastRow}`).format.numberFormat = '$#,##0';
  permitProxy.getRange(`H14:H${candidateLastRow}`).format.numberFormat = '#,##0';
  permitProxy.getRange(`A14:A${candidateLastRow}`).format.font = {
    name: 'Aptos Mono',
    size: 8,
    color: C.ink,
  };
  permitProxy.getRange(`L14:L${candidateLastRow}`).format.font = {
    name: 'Aptos Mono',
    size: 7,
    color: C.muted,
  };
  permitProxy.getRange(`I14:J${candidateLastRow}`).format = {
    fill: C.amberLight,
    font: { color: '#8A4826', size: 8 },
  };
  const table = permitProxy.tables.add(
    `A13:M${candidateLastRow}`,
    true,
    'EdmontonPermitProxyTable',
  );
  table.style = 'TableStyleMedium2';

  permitProxy.getRange('A33:M33').merge();
  permitProxy.getRange('A33').values = [['Audit and privacy controls']];
  sectionHeader(permitProxy.getRange('A33:M33'));
  const auditRows = [
    ['Source ID', permitProxyReport.source_ids.join('; ')],
    ['Evidence status', permitProxyReport.evidence_status],
    ['Input SHA-256', permitProxyReport.input_sha256],
    ['Output SHA-256', permitProxyReport.output_sha256],
    ['Retrieval manifest SHA-256', permitProxyReport.retrieval_manifest_sha256],
    ['Fields excluded', permitProxyReport.field_minimization.processed_output_excludes.join('; ')],
    ['Publication status', permitProxyReport.publication_boundary.status],
  ];
  auditRows.forEach(([label, value], index) => {
    const row = 34 + index;
    permitProxy.getRange(`A${row}:B${row}`).merge();
    permitProxy.getRange(`A${row}`).values = [[label]];
    permitProxy.getRange(`A${row}:B${row}`).format = {
      font: { bold: true, color: C.ink },
      borders: { preset: 'inside', style: 'thin', color: C.line },
    };
    permitProxy.getRange(`C${row}:G${row}`).merge();
    permitProxy.getRange(`C${row}`).values = [[value]];
    permitProxy.getRange(`C${row}:G${row}`).format = {
      font: { name: 'Aptos Mono', size: 8, color: C.muted },
      wrapText: true,
      borders: { preset: 'inside', style: 'thin', color: C.line },
    };
  });
  permitProxy.getRange('H34:M40').merge();
  permitProxy.getRange('H34').values = [
    [
      `Controlled classification is inferred and requires human review. Exact addresses, legal descriptions, coordinates, neighbourhoods and raw free-text job descriptions are absent from this processed sheet. Description lineage is retained only as a SHA-256 trace plus controlled matched-term labels. Official source: ${currentSourceRegistry.sources.find((item) => item.source_id === permitProxyReport.source_ids[0])?.canonical_url ?? ''}`,
    ],
  ];
  noteBlock(permitProxy.getRange('H34:M40'));
  permitProxy.freezePanes.freezeRows(13);
  permitProxy.freezePanes.freezeColumns(2);
  setWidths(
    permitProxy,
    {
      A: 27,
      B: 15,
      C: 24,
      D: 31,
      E: 27,
      F: 18,
      G: 23,
      H: 16,
      I: 18,
      J: 19,
      K: 21,
      L: 30,
      M: 60,
    },
    42,
  );
}

function buildAuditedOutcomes() {
  titleBand(
    auditedOutcomeSheet,
    'Audited public-project outcome references',
    'Hash-locked Ontario Auditor General cases · field discovery only · pending independent transcription review',
    'O',
  );

  const coverage = auditedOutcomes.coverage_summary;
  auditedOutcomeSheet.getRange('A5:B5').values = [['Coverage', 'Count / status']];
  header(auditedOutcomeSheet.getRange('A5:B5'));
  auditedOutcomeSheet.getRange('A6:B11').values = [
    ['Named completed projects', coverage.named_completed_project_count],
    ['Completed total-cost cases', coverage.completed_total_cost_case_count],
    [
      'Exact-day completion pairs',
      coverage.exact_day_substantial_completion_pair_count,
    ],
    ['Published price-basis dates', coverage.price_basis_date_case_count],
    [
      'Stable publisher project IDs',
      coverage.publisher_stable_project_id_case_count,
    ],
    [
      'Reference cases authorized',
      auditedOutcomes.publication_boundary.reference_case_publication_authorized
        ? 'YES'
        : 'NO',
    ],
  ];
  auditedOutcomeSheet.getRange('A6:A11').format.font = {
    bold: true,
    color: C.ink,
  };
  auditedOutcomeSheet.getRange('B6:B11').format = {
    fill: C.white,
    font: { color: C.ink },
    borders: { preset: 'inside', style: 'thin', color: C.line },
  };
  auditedOutcomeSheet.getRange('B11').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  auditedOutcomeSheet.getRange('D5:O5').merge();
  auditedOutcomeSheet.getRange('D5').values = [['Publication boundary']];
  sectionHeader(auditedOutcomeSheet.getRange('D5:O5'), C.amber);
  auditedOutcomeSheet.getRange('D6:O11').merge();
  auditedOutcomeSheet.getRange('D6').values = [
    [
      `${auditedOutcomes.publication_boundary.reason} These cases may inform schema design and graph-channel mapping, but they do not authorize an AI-attributable cost or schedule effect. Review status: ${labelize(auditedOutcomes.review.status)}.`,
    ],
  ];
  auditedOutcomeSheet.getRange('D6:O11').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  auditedOutcomeSheet.getRange('A13:O13').values = [
    [
      'Project',
      'Asset class',
      'Delivery model',
      'Baseline cost (CAD)',
      'Latest / final cost (CAD)',
      'Variance (CAD)',
      'Variance (%)',
      'Baseline substantial completion',
      'Actual substantial completion',
      'Delay (days)',
      'Latest cost status',
      'Price basis date',
      'Complete change history',
      'Cost panel authorized',
      'Schedule panel authorized',
    ],
  ];
  header(auditedOutcomeSheet.getRange('A13:O13'));
  const caseFirstRow = 14;
  const caseLastRow = caseFirstRow + auditedOutcomes.cases.length - 1;
  auditedOutcomeSheet.getRange(`A${caseFirstRow}:O${caseLastRow}`).values =
    auditedOutcomes.cases.map((item) => [
      item.project_name,
      labelize(item.asset_class),
      labelize(item.delivery_model),
      item.baseline_cost_cad,
      item.latest_or_final_cost_cad,
      item.cost_variance_cad,
      item.cost_variance_percent / 100,
      item.baseline_substantial_completion_date,
      item.actual_substantial_completion_date,
      item.schedule_delay_days,
      labelize(item.latest_or_final_cost_status),
      item.baseline_price_basis_date,
      item.approved_change_history_complete ? 'YES' : 'NO',
      item.cost_outcome_panel_authorized ? 'YES' : 'NO',
      item.schedule_outcome_panel_authorized ? 'YES' : 'NO',
    ]);
  auditedOutcomeSheet.getRange(`A${caseFirstRow}:O${caseLastRow}`).format = {
    font: { color: C.ink, size: 9 },
    wrapText: true,
    verticalAlignment: 'top',
    borders: {
      insideHorizontal: { style: 'thin', color: C.line },
      bottom: { style: 'thin', color: C.line },
    },
  };
  auditedOutcomeSheet.getRange(`A${caseFirstRow}:C${caseLastRow}`).format.font = {
    bold: true,
    color: C.ink,
    size: 9,
  };
  auditedOutcomeSheet.getRange(`D${caseFirstRow}:F${caseLastRow}`).format.numberFormat =
    '$#,##0';
  auditedOutcomeSheet.getRange(`G${caseFirstRow}:G${caseLastRow}`).format.numberFormat =
    '0.0%';
  auditedOutcomeSheet.getRange(`J${caseFirstRow}:J${caseLastRow}`).format.numberFormat =
    '#,##0';
  auditedOutcomeSheet.getRange(`M${caseFirstRow}:O${caseLastRow}`).format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826', size: 9 },
    borders: { preset: 'inside', style: 'thin', color: '#E1B48E' },
  };
  auditedOutcomeSheet.getRange(`A${caseFirstRow}:O${caseLastRow}`).format.rowHeight =
    58;

  const componentRows = auditedOutcomes.cases.flatMap((item) =>
    item.cost_components.map((component) => [
      item.project_name,
      component.source_category,
      labelize(component.graph_channel),
      component.value_cad,
      component.source_evidence_status,
      component.graph_channel_evidence_status,
    ]),
  );
  const componentFirstRow = 20;
  const componentLastRow = componentFirstRow + componentRows.length - 1;
  auditedOutcomeSheet.getRange('A19:F19').values = [
    [
      'Project',
      'Source cost category',
      'AIIO graph channel',
      'Value (CAD)',
      'Source evidence',
      'Channel evidence',
    ],
  ];
  header(auditedOutcomeSheet.getRange('A19:F19'));
  auditedOutcomeSheet.getRange(`A${componentFirstRow}:F${componentLastRow}`).values =
    componentRows;
  auditedOutcomeSheet.getRange(`A${componentFirstRow}:F${componentLastRow}`).format = {
    font: { color: C.ink, size: 9 },
    wrapText: true,
    verticalAlignment: 'top',
    borders: {
      insideHorizontal: { style: 'thin', color: C.line },
      bottom: { style: 'thin', color: C.line },
    },
  };
  auditedOutcomeSheet.getRange(`D${componentFirstRow}:D${componentLastRow}`).format.numberFormat =
    '$#,##0';

  auditedOutcomeSheet.getRange('H19:K19').values = [
    ['Project', 'Reported component total', 'Summed components', 'Check'],
  ];
  header(auditedOutcomeSheet.getRange('H19:K19'));
  const reconciliationFirstRow = 20;
  const reconciliationLastRow =
    reconciliationFirstRow + auditedOutcomes.cases.length - 1;
  auditedOutcomeSheet.getRange(
    `H${reconciliationFirstRow}:I${reconciliationLastRow}`,
  ).values = auditedOutcomes.cases.map((item) => [
    item.project_name,
    item.cost_component_total_cad,
  ]);
  for (let index = 0; index < auditedOutcomes.cases.length; index += 1) {
    const row = reconciliationFirstRow + index;
    auditedOutcomeSheet.getRange(`J${row}`).formulas = [
      [`=SUMIF($A$${componentFirstRow}:$A$${componentLastRow},H${row},$D$${componentFirstRow}:$D$${componentLastRow})`],
    ];
    auditedOutcomeSheet.getRange(`K${row}`).formulas = [
      [`=IF(ABS(I${row}-J${row})<1,"PASS","FAIL")`],
    ];
  }
  auditedOutcomeSheet.getRange(
    `H${reconciliationFirstRow}:K${reconciliationLastRow}`,
  ).format = {
    font: { color: C.ink, size: 9 },
    wrapText: true,
    borders: { preset: 'inside', style: 'thin', color: C.line },
  };
  auditedOutcomeSheet.getRange(
    `I${reconciliationFirstRow}:J${reconciliationLastRow}`,
  ).format.numberFormat = '$#,##0';
  auditedOutcomeSheet
    .getRange(`K${reconciliationFirstRow}:K${reconciliationLastRow}`)
    .conditionalFormats.add('containsText', {
      text: 'PASS',
      format: {
        fill: C.tealLight,
        font: { color: C.tealDark, bold: true },
      },
    });

  auditedOutcomeSheet.getRange('H24:O24').merge();
  auditedOutcomeSheet.getRange('H24').values = [['Evidence boundary']];
  sectionHeader(auditedOutcomeSheet.getRange('H24:O24'), C.amber);
  auditedOutcomeSheet.getRange('H25:O32').merge();
  auditedOutcomeSheet.getRange('H25').values = [
    [
      `Observed source categories are retained verbatim. AIIO graph channels are inferred classifications for mechanism mapping. Lakeridge Gardens has mixed month/day schedule precision, so no day-delay value is computed. Highway 427 has an exact ${auditedOutcomes.cases[1].schedule_delay_days}-day substantial-completion difference, but its latest cost was under dispute and not final at the audit date. Neither case has a published estimate price-basis date or complete approved-change history.`,
    ],
  ];
  auditedOutcomeSheet.getRange('H25:O32').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  const outcomeSource = currentSourceRegistry.sources.find(
    (item) => item.source_id === auditedOutcomes.source_id,
  );
  auditedOutcomeSheet.getRange('H34:O34').merge();
  auditedOutcomeSheet.getRange('H34').values = [['Source and reproducibility']];
  sectionHeader(auditedOutcomeSheet.getRange('H34:O34'));
  auditedOutcomeSheet.getRange('H35:O41').merge();
  auditedOutcomeSheet.getRange('H35').values = [
    [
      `Source: ${outcomeSource?.canonical_url ?? auditedOutcomes.source_id}\nArchive: ${auditedOutcomes.source_file.archive_file}\nContent hash: ${auditedOutcomes.source_file.content_hash}\nVerified text anchors: ${auditedOutcomes.source_file.verified_anchor_count}\nReview record: ${auditedOutcomes.review.review_record}`,
    ],
  ];
  auditedOutcomeSheet.getRange('H35:O41').format = {
    fill: C.soft,
    font: { name: 'Aptos Mono', color: C.muted, size: 8 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };

  const table = auditedOutcomeSheet.tables.add(
    `A19:F${componentLastRow}`,
    true,
    'AuditedOutcomeComponentsTable',
  );
  table.style = 'TableStyleMedium2';
  auditedOutcomeSheet.freezePanes.freezeRows(13);
  auditedOutcomeSheet.freezePanes.freezeColumns(1);
  setWidths(
    auditedOutcomeSheet,
    {
      A: 38,
      B: 28,
      C: 34,
      D: 20,
      E: 19,
      F: 19,
      G: 15,
      H: 36,
      I: 22,
      J: 22,
      K: 26,
      L: 18,
      M: 20,
      N: 20,
      O: 21,
    },
    46,
  );
}

function buildQuebecRevisions() {
  titleBand(
    quebecRevisionSheet,
    'Quebec authorized project revisions',
    'Official lifecycle histories · chain-reconciled research candidate · not final outturn or an AI effect',
    'R',
  );

  const coverage = quebecRevisions.coverage_summary;
  const boundary = quebecRevisions.publication_boundary;
  quebecRevisionSheet.getRange('A5:D5').values = [
    ['Coverage', 'Count / status', 'Chain quality', 'Count / status'],
  ];
  header(quebecRevisionSheet.getRange('A5:D5'));
  quebecRevisionSheet.getRange('A6:D10').values = [
    [
      'Source projects',
      coverage.source_project_count,
      'Stable lifecycle IDs',
      coverage.stable_lifecycle_project_id_count,
    ],
    [
      'Authorized cost events',
      coverage.authorized_cost_revision_event_count,
      'Reconciled cost chains',
      coverage.cost_revision_chain_reconciled_project_count,
    ],
    [
      'Authorized schedule events',
      coverage.authorized_schedule_revision_event_count,
      'Reconciled schedule chains',
      coverage.schedule_revision_chain_reconciled_project_count,
    ],
    [
      'Joint reconciled chains',
      coverage.joint_reconciled_revision_project_count,
      'Fiscal-year completion markers',
      coverage.actual_completion_fiscal_year_count,
    ],
    [
      'Reference panel authorized',
      boundary.authorized_revision_reference_panel_authorized ? 'YES' : 'NO',
      'AI effect authorized',
      boundary.ai_attributable_effect_authorized ? 'YES' : 'NO',
    ],
  ];
  quebecRevisionSheet.getRange('A6:A10').format.font = {
    bold: true,
    color: C.ink,
  };
  quebecRevisionSheet.getRange('C6:C10').format.font = {
    bold: true,
    color: C.ink,
  };
  quebecRevisionSheet.getRange('B6:D10').format.borders = {
    preset: 'inside',
    style: 'thin',
    color: C.line,
  };
  quebecRevisionSheet.getRange('B10:D10').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
    borders: { preset: 'inside', style: 'thin', color: '#E1B48E' },
  };

  quebecRevisionSheet.getRange('F5:R5').merge();
  quebecRevisionSheet.getRange('F5').values = [['Publication boundary']];
  sectionHeader(quebecRevisionSheet.getRange('F5:R5'), C.amber);
  quebecRevisionSheet.getRange('F6:R10').merge();
  quebecRevisionSheet.getRange('F6').values = [
    [
      `${boundary.reason} The descriptive medians below are research diagnostics only: they must not be transferred to Alberta, applied as project contingencies, or interpreted as causal AI effects.`,
    ],
  ];
  quebecRevisionSheet.getRange('F6:R10').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  quebecRevisionSheet.getRange('A13:G13').values = [
    [
      'Asset class',
      'Projects',
      'Cost chains',
      'Median authorized cost revision',
      'Schedule chains',
      'Median authorized schedule change (months)',
      'Use status',
    ],
  ];
  header(quebecRevisionSheet.getRange('A13:G13'));
  const byAsset = quebecRevisions.descriptive_statistics.by_asset_class;
  quebecRevisionSheet.getRange(`A14:G${13 + byAsset.length}`).values = byAsset.map(
    (item) => {
      const assetCoverage = quebecRevisions.asset_class_coverage.find(
        (coverageItem) => coverageItem.asset_class === item.asset_class,
      );
      return [
        labelize(item.asset_class),
        assetCoverage?.project_count ?? 0,
        assetCoverage?.cost_reconciled_count ?? 0,
        item.authorized_cost_variance_fraction.median,
        assetCoverage?.schedule_reconciled_count ?? 0,
        item.authorized_schedule_change_months.median,
        'RESEARCH CANDIDATE',
      ];
    },
  );
  const assetLastRow = 13 + byAsset.length;
  quebecRevisionSheet.getRange(`D14:D${assetLastRow}`).format.numberFormat =
    '0.0%';
  quebecRevisionSheet.getRange(`F14:F${assetLastRow}`).format.numberFormat =
    '0.0';
  quebecRevisionSheet.getRange(`G14:G${assetLastRow}`).format = {
    fill: C.soft,
    font: { bold: true, color: C.muted, size: 8 },
  };
  const assetTable = quebecRevisionSheet.tables.add(
    `A13:G${assetLastRow}`,
    true,
    'QuebecRevisionAssetSummaryTable',
  );
  assetTable.style = 'TableStyleMedium2';

  const dashboardSource = currentSourceRegistry.sources.find(
    (item) => item.source_id === 'QUEBEC_PQI_PROJECT_DASHBOARD',
  );
  const dictionarySource = currentSourceRegistry.sources.find(
    (item) => item.source_id === 'QUEBEC_PQI_DATA_DICTIONARY',
  );
  quebecRevisionSheet.getRange('I13:R13').merge();
  quebecRevisionSheet.getRange('I13').values = [['Source contract and reproducibility']];
  sectionHeader(quebecRevisionSheet.getRange('I13:R13'));
  quebecRevisionSheet.getRange('I14:R20').merge();
  quebecRevisionSheet.getRange('I14').values = [
    [
      `Dashboard: ${dashboardSource?.canonical_url ?? 'QUEBEC_PQI_PROJECT_DASHBOARD'}\nDashboard CSV: ${dashboardSource?.retrieval_url ?? ''}\nField dictionary: ${dictionarySource?.retrieval_url ?? dictionarySource?.canonical_url ?? 'QUEBEC_PQI_DATA_DICTIONARY'}\nDashboard hash: ${quebecRevisions.source_files.QUEBEC_PQI_PROJECT_DASHBOARD.content_hash}\nDictionary hash: ${quebecRevisions.source_files.QUEBEC_PQI_DATA_DICTIONARY.content_hash}\nContract: no_projet is stable through the lifecycle; cout_total is current authorized cost; suivi_modifications contains authorized lifecycle changes and effective dates. Parser evidence status: ${quebecRevisions.evidence_status}.`,
    ],
  ];
  quebecRevisionSheet.getRange('I14:R20').format = {
    fill: C.soft,
    font: { name: 'Aptos Mono', color: C.muted, size: 8 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };

  quebecRevisionSheet.getRange('A24:R24').values = [
    [
      'Project ID',
      'Project name',
      'Asset class',
      'Stage',
      'Region',
      'Municipality',
      'Cost events',
      'Cost chain',
      'Baseline authorized cost (CAD)',
      'Current authorized cost (CAD)',
      'Authorized variance (CAD)',
      'Authorized variance (%)',
      'Schedule events',
      'Schedule chain',
      'Baseline completion',
      'Current completion',
      'Schedule change (months)',
      'Quality flags',
    ],
  ];
  header(quebecRevisionSheet.getRange('A24:R24'));
  const firstProjectRow = 25;
  const lastProjectRow = firstProjectRow + quebecRevisionRows.length - 1;
  quebecRevisionSheet.getRange(`A${firstProjectRow}:R${lastProjectRow}`).values =
    quebecRevisionRows.map((row) => [
      row.project_id,
      row.project_name,
      labelize(row.asset_class),
      row.stage_source_text,
      row.region,
      row.municipality,
      numberOrNull(row.cost_revision_event_count),
      yesNo(row.cost_revision_chain_reconciles),
      numberOrNull(row.baseline_authorized_cost_cad),
      numberOrNull(row.current_authorized_cost_cad),
      numberOrNull(row.authorized_cost_variance_cad),
      numberOrNull(row.authorized_cost_variance_percent),
      numberOrNull(row.schedule_revision_event_count),
      yesNo(row.schedule_revision_chain_reconciles),
      monthOrNull(row.baseline_completion_month),
      monthOrNull(row.current_completion_month),
      numberOrNull(row.authorized_schedule_change_months),
      row.quality_flags,
    ]);
  quebecRevisionSheet.getRange(`I${firstProjectRow}:K${lastProjectRow}`).format.numberFormat =
    '$#,##0';
  quebecRevisionSheet.getRange(`L${firstProjectRow}:L${lastProjectRow}`).format.numberFormat =
    '0.0%';
  quebecRevisionSheet.getRange(`O${firstProjectRow}:P${lastProjectRow}`).format.numberFormat =
    'mmm yyyy';
  quebecRevisionSheet.getRange(`Q${firstProjectRow}:Q${lastProjectRow}`).format.numberFormat =
    '0';
  quebecRevisionSheet.getRange(`H${firstProjectRow}:H${lastProjectRow}`).conditionalFormats.add(
    'containsText',
    {
      text: 'NO',
      format: { fill: C.amberLight, font: { color: '#8A4826' } },
    },
  );
  quebecRevisionSheet.getRange(`N${firstProjectRow}:N${lastProjectRow}`).conditionalFormats.add(
    'containsText',
    {
      text: 'NO',
      format: { fill: C.amberLight, font: { color: '#8A4826' } },
    },
  );
  quebecRevisionSheet.getRange(`R${firstProjectRow}:R${lastProjectRow}`).format.font = {
    name: 'Aptos Mono',
    color: C.muted,
    size: 8,
  };
  const projectTable = quebecRevisionSheet.tables.add(
    `A24:R${lastProjectRow}`,
    true,
    'QuebecAuthorizedRevisionProjectsTable',
  );
  projectTable.style = 'TableStyleMedium2';
  quebecRevisionSheet.freezePanes.freezeRows(24);
  quebecRevisionSheet.freezePanes.freezeColumns(2);
  setWidths(
    quebecRevisionSheet,
    {
      A: 16,
      B: 50,
      C: 31,
      D: 24,
      E: 24,
      F: 24,
      G: 13,
      H: 13,
      I: 22,
      J: 22,
      K: 20,
      L: 18,
      M: 15,
      N: 15,
      O: 20,
      P: 20,
      Q: 18,
      R: 48,
    },
    lastProjectRow,
  );
}

function buildQuebecVintages() {
  titleBand(
    quebecVintageSheet,
    'Quebec complete archive and selection diagnostics',
    '69 official dates · 68 direct CSV snapshots · 1 official XLSX fallback · research-only',
    'V',
  );

  const boundary = quebecFullArchive.publication_boundary;
  quebecVintageSheet.getRange('A5:D5').values = [
    ['Archive coverage', 'Count / status', 'Panel diagnostic', 'Count / status'],
  ];
  header(quebecVintageSheet.getRange('A5:D5'));
  quebecVintageSheet.getRange('A6:D11').values = [
    [
      'Official snapshot dates',
      quebecFullArchive.snapshot_date_count,
      'Snapshot-project observations',
      quebecFullArchive.snapshot_observation_count,
    ],
    [
      'Unique stable project IDs',
      quebecFullArchive.unique_project_count,
      'Latest snapshot projects',
      quebecFullArchive.latest_snapshot_project_count,
    ],
    [
      'Disappearance events',
      quebecFullArchive.disappearance_event_count,
      'Publisher-declared retirements',
      quebecFullArchive.publisher_declared_retirement_disappearance_event_count,
    ],
    [
      'Unclassified disappearances',
      quebecFullArchive.unclassified_disappearance_event_count,
      'Projects with catalog reentry',
      quebecFullArchive.project_with_catalog_reentry_count,
    ],
    [
      'Direct CSV snapshots',
      quebecFullArchiveContract.direct_csv_snapshot_count,
      'Official XLSX fallback',
      quebecFullArchiveContract.paired_xlsx_fallback_count,
    ],
    [
      'Project-exit outcome authorized',
      boundary.project_exit_outcome_authorized ? 'YES' : 'NO',
      'AI-attributable effect authorized',
      boundary.ai_attributable_effect_authorized ? 'YES' : 'NO',
    ],
  ];
  quebecVintageSheet.getRange('A6:A11').format.font = {
    bold: true,
    color: C.ink,
  };
  quebecVintageSheet.getRange('C6:C11').format.font = {
    bold: true,
    color: C.ink,
  };
  quebecVintageSheet.getRange('B11:D11').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826' },
    borders: { preset: 'inside', style: 'thin', color: '#E1B48E' },
  };

  quebecVintageSheet.getRange('F5:V5').merge();
  quebecVintageSheet.getRange('F5').values = [['Interpretation boundary']];
  sectionHeader(quebecVintageSheet.getRange('F5:V5'), C.amber);
  quebecVintageSheet.getRange('F6:V11').merge();
  quebecVintageSheet.getRange('F6').values = [
    [
      `${boundary.reason} Publisher-declared complete-service and retirement markers are source statements, not audited final outcomes. One malformed December 2024 CSV is represented by its paired official XLSX. The ${quebecParserReview.sample_project_count}-project review packet is prepared, but reviewer fields remain blank and the parser is not authorized for decision use.`,
    ],
  ];
  quebecVintageSheet.getRange('F6:V11').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  quebecVintageSheet.getRange('A14:H14').values = [
    [
      'Snapshot date',
      'Threshold regime',
      'Projects',
      'Duplicates collapsed',
      'Schema profile',
      'Representation',
      'Resource ID',
      'Representation hash',
    ],
  ];
  header(quebecVintageSheet.getRange('A14:H14'));
  const vintageLastRow = 14 + quebecFullArchive.snapshot_summaries.length;
  quebecVintageSheet.getRange(`A15:H${vintageLastRow}`).values =
    quebecFullArchive.snapshot_summaries.map((vintage) => {
      return [
        vintage.snapshot_date,
        vintage.threshold_regime === 'cad_50m_and_over'
          ? 'CAD 50M+'
          : 'CAD 20M+',
        vintage.project_count,
        vintage.publisher_duplicate_rows_collapsed,
        vintage.schema_profile,
        vintage.representation_type,
        vintage.resource_id,
        vintage.representation_hash,
      ];
    });
  quebecVintageSheet.getRange(`G15:H${vintageLastRow}`).format.font = {
    name: 'Aptos Mono',
    color: C.muted,
    size: 8,
  };
  const vintageTable = quebecVintageSheet.tables.add(
    `A14:H${vintageLastRow}`,
    true,
    'QuebecCompleteArchiveSnapshotsTable',
  );
  vintageTable.style = 'TableStyleMedium2';

  quebecVintageSheet.getRange('J14:V14').values = [[
    'Previous snapshot',
    'Current snapshot',
    'Previous projects',
    'Current projects',
    'Continuing',
    'New',
    'Disappeared',
    'Reentered',
    'Declared retirement',
    'Unclassified',
    'Threshold transition',
    'Source ID',
    'Evidence status',
  ]];
  header(quebecVintageSheet.getRange('J14:V14'));
  const transitionLastRow = 14 + quebecFullTransitionRows.length;
  quebecVintageSheet.getRange(`J15:V${transitionLastRow}`).values =
    quebecFullTransitionRows.map((row) => [
      row.previous_snapshot_date,
      row.current_snapshot_date,
      numberOrNull(row.previous_project_count),
      numberOrNull(row.current_project_count),
      numberOrNull(row.continuing_project_count),
      numberOrNull(row.newly_observed_project_count),
      numberOrNull(row.disappeared_project_count),
      numberOrNull(row.reentered_project_count),
      numberOrNull(row.publisher_declared_retirement_disappearance_count),
      numberOrNull(row.unclassified_disappearance_count),
      yesNo(row.threshold_transition),
      row.source_id,
      row.evidence_status,
    ]);
  const transitionTable = quebecVintageSheet.tables.add(
    `J14:V${transitionLastRow}`,
    true,
    'QuebecCompleteArchiveTransitionsTable',
  );
  transitionTable.style = 'TableStyleMedium4';
  quebecVintageSheet.getRange(`U15:V${transitionLastRow}`).format.font = {
    name: 'Aptos Mono',
    color: C.muted,
    size: 8,
  };

  quebecVintageSheet.getRange('A86:V86').values = [
    [
      'Project ID',
      'Source record ID',
      'Latest project name',
      'Asset class',
      'First observed',
      'Last observed',
      'Snapshots',
      'In latest',
      'Pre-threshold',
      'Post-threshold',
      'Disappearances',
      'Reentries',
      'Declared retirements',
      'Unclassified exits',
      'Adjacent pairs',
      'Comparable cost pairs',
      'Cost pairs changed',
      'Comparable completion pairs',
      'Completion pairs changed',
      'Presence pattern',
      'Source ID',
      'Quality flags',
    ],
  ];
  header(quebecVintageSheet.getRange('A86:V86'));
  const firstLifecycleRow = 87;
  const lastLifecycleRow = firstLifecycleRow + quebecFullLifecycleRows.length - 1;
  quebecVintageSheet.getRange(`A${firstLifecycleRow}:V${lastLifecycleRow}`).values =
    quebecFullLifecycleRows.map((row) => [
      row.project_id,
      row.source_record_id,
      row.latest_project_name,
      labelize(row.latest_asset_class),
      row.first_observed_snapshot,
      row.last_observed_snapshot,
      numberOrNull(row.observed_snapshot_count),
      yesNo(row.present_in_latest_snapshot),
      yesNo(row.observed_pre_threshold),
      yesNo(row.observed_post_threshold),
      numberOrNull(row.interval_disappearance_count),
      numberOrNull(row.catalog_reentry_count),
      numberOrNull(row.publisher_declared_retirement_disappearance_count),
      numberOrNull(row.unclassified_disappearance_count),
      numberOrNull(row.consecutive_observation_pair_count),
      numberOrNull(row.comparable_cost_pair_count),
      numberOrNull(row.authorized_cost_change_pair_count),
      numberOrNull(row.comparable_completion_pair_count),
      numberOrNull(row.completion_month_change_pair_count),
      row.presence_pattern,
      row.source_id,
      row.quality_flags,
    ]);
  quebecVintageSheet.getRange(`H${firstLifecycleRow}:H${lastLifecycleRow}`).conditionalFormats.add(
    'containsText',
    {
      text: 'NO',
      format: { fill: C.amberLight, font: { color: '#8A4826' } },
    },
  );
  quebecVintageSheet.getRange(`T${firstLifecycleRow}:V${lastLifecycleRow}`).format.font = {
    name: 'Aptos Mono',
    color: C.muted,
    size: 8,
  };
  const lifecycleTable = quebecVintageSheet.tables.add(
    `A86:V${lastLifecycleRow}`,
    true,
    'QuebecCompleteArchiveProjectLifecyclesTable',
  );
  lifecycleTable.style = 'TableStyleMedium2';
  quebecVintageSheet.freezePanes.freezeRows(14);
  quebecVintageSheet.freezePanes.freezeColumns(2);
  setWidths(
    quebecVintageSheet,
    {
      A: 16,
      B: 17,
      C: 48,
      D: 31,
      E: 16,
      F: 16,
      G: 12,
      H: 12,
      I: 14,
      J: 15,
      K: 16,
      L: 12,
      M: 19,
      N: 17,
      O: 14,
      P: 18,
      Q: 17,
      R: 22,
      S: 22,
      T: 20,
      U: 31,
      V: 52,
    },
    lastLifecycleRow,
  );
}

function buildCanadaCoverage() {
  titleBand(
    canadaCoverageSheet,
    'Canada cross-domain evidence coverage',
    `All 13 provinces and territories · seven evidence domains · workbook ${workbookBuildVersion}`,
    'Q',
  );
  canadaCoverageSheet.getRange('A5:B10').values = [
    ['Model ID', canadaCrossDomainCoverage.model_id],
    ['Geographies', canadaCrossDomainCoverage.geography_count],
    ['Evidence domains', canadaCrossDomainCoverage.domain_count],
    ['Coverage cells', canadaCrossDomainCoverage.matrix_cell_count],
    ['Comparison authorized', canadaCrossDomainCoverage.publication_boundary.cross_province_comparison_authorized ? 'YES' : 'NO'],
    ['Missingness imputed', canadaCrossDomainCoverage.publication_boundary.missingness_imputed ? 'YES' : 'NO'],
  ];
  canadaCoverageSheet.getRange('A5:A10').format.font = { bold: true };
  canadaCoverageSheet.getRange('B9:B10').format = {
    fill: C.amberLight,
    font: { color: '#8A4826', bold: true },
  };
  canadaCoverageSheet.getRange('D5:Q5').merge();
  canadaCoverageSheet.getRange('D5').values = [['Interpretation boundary']];
  sectionHeader(canadaCoverageSheet.getRange('D5:Q5'), C.amber);
  canadaCoverageSheet.getRange('D6:Q10').merge();
  canadaCoverageSheet.getRange('D6').values = [[
    'Availability is not comparability. Public-project inventories, power quantities and broad-sector capex retain different scopes and meanings. Missing evidence is shown as not available and is never imputed. This sheet cannot authorize province rankings, province-specific calibration, an AI-attributable effect or a transmission requirement.',
  ]];
  noteBlock(canadaCoverageSheet.getRange('D6:Q10'));

  const domains = [
    ['labour', 'Labour'],
    ['materials', 'Materials'],
    ['building_investment', 'Investment'],
    ['regional_macro', 'Macro'],
    ['public_projects', 'Projects'],
    ['power_planning', 'Power'],
    ['information_sector_capex', 'Sector capex'],
  ];
  canadaCoverageSheet.getRange('A12:Q12').values = [[
    'Geography',
    'Geography ID',
    ...domains.map(([, label]) => label),
    ...domains.map(([, label]) => `${label} records`),
    'Publication role',
  ]];
  header(canadaCoverageSheet.getRange('A12:Q12'));
  const firstRow = 13;
  const lastRow = firstRow + canadaCrossDomainCoverage.geographies.length - 1;
  canadaCoverageSheet.getRange(`A${firstRow}:Q${lastRow}`).values =
    canadaCrossDomainCoverage.geographies.map((geography) => [
      geography.geography_label,
      geography.geography_id,
      ...domains.map(([domain]) => geography.domains[domain].status),
      ...domains.map(([domain]) => geography.domains[domain].record_count),
      geography.geography_id === 'PR_48' ? 'Alberta pilot + coverage inventory' : 'Coverage inventory only',
    ]);
  canadaCoverageSheet.getRange(`C${firstRow}:I${lastRow}`).conditionalFormats.add(
    'cellIs',
    { operator: 'equal', formula: '"available"', format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } } },
  );
  canadaCoverageSheet.getRange(`C${firstRow}:I${lastRow}`).conditionalFormats.add(
    'cellIs',
    { operator: 'equal', formula: '"available_with_missingness"', format: { fill: '#E9F0F2', font: { color: '#456574', bold: true } } },
  );
  canadaCoverageSheet.getRange(`C${firstRow}:I${lastRow}`).conditionalFormats.add(
    'cellIs',
    { operator: 'equal', formula: '"not_available"', format: { fill: C.amberLight, font: { color: '#8A4826', bold: true } } },
  );
  canadaCoverageSheet.getRange(`J${firstRow}:P${lastRow}`).format.numberFormat = '#,##0';
  const coverageTable = canadaCoverageSheet.tables.add(
    `A12:Q${lastRow}`,
    true,
    'CanadaCrossDomainCoverageTable',
  );
  coverageTable.style = 'TableStyleMedium2';

  canadaCoverageSheet.getRange('A28:C28').values = [['Input ID', 'Path', 'SHA-256']];
  header(canadaCoverageSheet.getRange('A28:C28'));
  const inputRows = Object.entries(canadaCrossDomainCoverage.input_manifest);
  canadaCoverageSheet.getRange(`A29:C${28 + inputRows.length}`).values = inputRows.map(
    ([inputId, item]) => [inputId, item.path, item.sha256],
  );
  canadaCoverageSheet.getRange(`C29:C${28 + inputRows.length}`).format.font = {
    name: 'Aptos Mono',
    size: 8,
    color: C.muted,
  };
  const inputTable = canadaCoverageSheet.tables.add(
    `A28:C${28 + inputRows.length}`,
    true,
    'CanadaCoverageInputManifestTable',
  );
  inputTable.style = 'TableStyleMedium2';
  canadaCoverageSheet.freezePanes.freezeRows(12);
  canadaCoverageSheet.freezePanes.freezeColumns(2);
  setWidths(
    canadaCoverageSheet,
    {
      A: 27, B: 15, C: 24, D: 24, E: 24, F: 24, G: 24, H: 24, I: 24,
      J: 14, K: 14, L: 14, M: 14, N: 14, O: 14, P: 14, Q: 31,
    },
    42,
  );
}

function buildSources() {
  titleBand(
    sources,
    'Current research source register',
    `All ${currentSourceRegistry.sources.length} registry sources · public release membership shown separately`,
    'J',
  );
  sources.getRange('A4:J4').values = [
    [
      'Source ID',
      'Title',
      'Publisher',
      'Domain',
      'Geography',
      'As-of date',
      'Registry status',
      'Evidence status',
      `In release ${release.manifest.version}`,
      'Canonical URL',
    ],
  ];
  header(sources.getRange('A4:J4'));
  const releaseSourceIds = new Set(
    release.sources.map((source) => source.source_id),
  );
  const sourceLastRow = 4 + currentSourceRegistry.sources.length;
  sources.getRange(`A5:J${sourceLastRow}`).values =
    currentSourceRegistry.sources.map((item) => [
      item.source_id,
      item.title,
      item.publisher,
      labelize(item.domain),
      item.geography,
      new Date(`${item.as_of_date}T00:00:00Z`),
      item.status,
      item.evidence_status,
      releaseSourceIds.has(item.source_id) ? 'YES' : 'NO',
      item.canonical_url,
    ]);
  sources.getRange(`F5:F${sourceLastRow}`).format.numberFormat = 'yyyy-mm-dd';
  sources.getRange(`I5:I${sourceLastRow}`).conditionalFormats.add(
    'containsText',
    {
      text: 'YES',
      format: {
        fill: C.tealLight,
        font: { color: C.tealDark, bold: true },
      },
    },
  );
  sources.getRange(`I5:I${sourceLastRow}`).conditionalFormats.add(
    'containsText',
    {
      text: 'NO',
      format: {
        fill: C.soft,
        font: { color: C.muted, bold: true },
      },
    },
  );
  const table = sources.tables.add(
    `A4:J${sourceLastRow}`,
    true,
    'SourceRegisterTable',
  );
  table.style = 'TableStyleMedium2';
  sources.freezePanes.freezeRows(4);
  sources.freezePanes.freezeColumns(1);
  setWidths(
    sources,
    {
      A: 31,
      B: 48,
      C: 26,
      D: 28,
      E: 42,
      F: 14,
      G: 16,
      H: 17,
      I: 18,
      J: 48,
    },
    sourceLastRow,
  );
}

function buildReleaseChecks() {
  titleBand(
    checks,
    'Workbook identity and reconciliation',
    `Workbook ${workbookBuildVersion} · public release basis ${release.manifest.version}`,
    'D',
  );
  checks.getRange('A5:B13').values = [
    ['Public release basis', release.manifest.version],
    ['Release ID', release.manifest.release_id],
    ['Schema version', release.manifest.schema_version],
    ['Model version', release.manifest.model_version],
    ['Engine version', release.manifest.engine_version],
    ['Parameter set ID', release.manifest.parameter_set_id],
    ['Code commit', release.manifest.code_commit],
    ['Input manifest hash', release.manifest.input_manifest_hash],
    ['Dirty worktree at build', release.manifest.dirty_worktree],
  ];
  checks.getRange('A5:A13').format.font = { bold: true };
  checks.getRange('B11:B12').format.font = {
    name: 'Aptos Mono',
    size: 9,
    color: C.muted,
  };
  checks.getRange('A15:C15').values = [['Check', 'Result', 'Expected']];
  header(checks.getRange('A15:C15'));
  const checkLabels = [
    ['Component shares sum to 100%', 'PASS'],
    ['Annual profile sums to 100%', 'PASS'],
    ['Timeline capex equals scenario total', 'PASS'],
    ['Dashboard core count matches project register', 'PASS'],
    ['Dashboard transfer proxy matches central case', 'PASS'],
    ['All pressure rows are scenario-labelled', 'PASS'],
    ['Release was built from a clean worktree', 'PASS'],
    ['Suppressed labour values remain flagged', 'PASS'],
    ['Canada labour coverage reconciles to release', 'PASS'],
    ['Workforce stock coverage reconciles to release', 'PASS'],
    ['Cross-vintage diagnostic formulas reconcile', 'PASS'],
    ['Material-screen rows reconcile to release', 'PASS'],
    ['Project-exposure rows reconcile to release', 'PASS'],
    ['Power evidence reconciles and transmission remains unknown', 'PASS'],
    ['Cost-baseline gate rows reconcile to the model artifact', 'PASS'],
    ['Public cost projection remains unauthorized', 'PASS'],
    ['Default project-cost result fails closed with blank outputs', 'PASS'],
    ['Provincial project exposure remains unauthorized', 'PASS'],
    ['Provincial BCPI projections remain unauthorized', 'PASS'],
    ['Provincial power profile remains unauthorized', 'PASS'],
    ['Weekly digest cannot change the model automatically', 'PASS'],
    ['AI-attributable effect remains unauthorized and null', 'PASS'],
    ['Regional investment-control panel reconciles to artifact', 'PASS'],
    ['CanadaBuys procurement intake reconciles and remains non-authorizing', 'PASS'],
    ['Edmonton permit proxy reconciles and remains non-authorizing', 'PASS'],
    ['Audited outcome references reconcile and remain non-authorizing', 'PASS'],
    ['Quebec authorized-revision chains reconcile and remain non-authorizing', 'PASS'],
    ['Quebec complete archive reconciles and remains non-authorizing', 'PASS'],
    ['Alberta scenario variants reconcile and remain non-authorizing', 'PASS'],
    ['Historical cost envelope reconciles and remains non-forecasting', 'PASS'],
    ['Reference-cost review packet reconciles and remains non-authorizing', 'PASS'],
    ['Information-sector capex screen reconciles and remains non-authorizing', 'PASS'],
    ['CMA reference-cost expansion reconciles and remains withheld', 'PASS'],
    ['Regional macro controls reconcile and remain descriptive only', 'PASS'],
    ['Province-linked BCPI bridge reconciles and remains non-authorizing', 'PASS'],
    ['Historical project analogs reconcile and remain non-forecasting', 'PASS'],
    ['AI-capex announcement ledger reconciles and remains non-authorizing', 'PASS'],
    ['Attribution panel preflight reconciles and assembles zero ineligible rows', 'PASS'],
    ['Treatment-source qualification reconciles and remains non-authorizing', 'PASS'],
    ['Canada cross-domain coverage reconciles without comparison or imputation', 'PASS'],
  ];
  checks.getRange('A16:C55').values = checkLabels.map(([label, expected]) => [
    label,
    null,
    expected,
  ]);
  checks.getRange('B16').formulas = [
    ['=IF(ABS(\'Assumptions\'!B19-1)<0.000001,"PASS","FAIL")'],
  ];
  checks.getRange('B17').formulas = [
    ['=IF(ABS(SUM(\'Scenario Timeline\'!B5:B14)-1)<0.000001,"PASS","FAIL")'],
  ];
  checks.getRange('B18').formulas = [
    ['=IF(ABS(\'Scenario Timeline\'!C15-\'Assumptions\'!B5)<1,"PASS","FAIL")'],
  ];
  checks.getRange('B19').formulas = [
    [
      `=IF(Dashboard!D6=COUNTIF('AI Projects'!$M$5:$M$${4 + release.baseline.projects.length},"core_data_centre"),"PASS","FAIL")`,
    ],
  ];
  checks.getRange('B20').formulas = [
    ['=IF(ABS(Dashboard!J6*1000-\'Assumptions\'!K24)<0.1,"PASS","FAIL")'],
  ];
  checks.getRange('B21').formulas = [
    [
      `=IF(COUNTIF('Pressure Results'!$J$5:$J$${4 + release.scenario.trade_pressure_order.length + release.scenario.public_delivery_pressure_order.length},"scenario")=ROWS('Pressure Results'!$J$5:$J$${4 + release.scenario.trade_pressure_order.length + release.scenario.public_delivery_pressure_order.length}),"PASS","FAIL")`,
    ],
  ];
  checks.getRange('B22').formulas = [['=IF(B13=FALSE,"PASS","FAIL")']];
  checks.getRange('B23').formulas = [
    [
      `=IF(COUNTIF('Labour Availability'!$O$5:$O$${4 + labourRows.length},"FAIL")=0,"PASS","FAIL")`,
    ],
  ];
  const canadaCoverageEnd =
    4 + release.baseline.labour_availability_canada.coverage.length;
  const canadaObservationStart = canadaCoverageEnd + 5;
  const canadaObservationEnd =
    canadaObservationStart +
    release.baseline.labour_availability_canada.observations.length -
    1;
  checks.getRange('B24').formulas = [
    [
      `=IF(AND(COUNTIF('Labour Canada'!$I$5:$I$${canadaCoverageEnd},"FAIL")=0,COUNTIF('Labour Canada'!$Q$${canadaObservationStart}:$Q$${canadaObservationEnd},"FAIL")=0),"PASS","FAIL")`,
    ],
  ];
  const workforceCoverageEnd =
    4 + release.baseline.labour_workforce_stock_canada.coverage.length;
  const workforceObservationStart = workforceCoverageEnd + 5;
  const workforceObservationEnd =
    workforceObservationStart +
    release.baseline.labour_workforce_stock_canada.observations.length -
    1;
  checks.getRange('B25').formulas = [
    [
      `=IF(AND(COUNTIF('Workforce Stock'!$J$5:$J$${workforceCoverageEnd},"FAIL")=0,COUNTIF('Workforce Stock'!$S$${workforceObservationStart}:$S$${workforceObservationEnd},"FAIL")=0),"PASS","FAIL")`,
    ],
  ];
  const diagnosticWarningRow =
    4 +
    labourPressure.trade_diagnostics.filter(
      (item) => item.geography_id === 'PR_48',
    ).length +
    2;
  const diagnosticObservationStart = diagnosticWarningRow + 3;
  const diagnosticObservationEnd =
    diagnosticObservationStart +
    labourPressure.occupation_diagnostics.length -
    1;
  checks.getRange('B26').formulas = [
    [
      `=IF(COUNTIF('Labour Diagnostic'!$N$${diagnosticObservationStart}:$N$${diagnosticObservationEnd},"FAIL")=0,"PASS","FAIL")`,
    ],
  ];
  checks.getRange('B27').formulas = [
    [
      `=IF(ROWS('Material Screen'!$A$5:$A$${4 + materialRows.length})=${release.material_cost_screen.observation_count},"PASS","FAIL")`,
    ],
  ];
  checks.getRange('B28').formulas = [
    [
      `=IF(AND(ROWS('Project Exposure'!$A$15:$A$${14 + projectExposureRows.length})=${release.public_project_exposure.screened_project_count},SUM('Project Exposure'!$B$5:$B$${4 + release.public_project_exposure.asset_class_summaries.length})=${release.public_project_exposure.screened_project_count}),"PASS","FAIL")`,
    ],
  ];
  checks.getRange('B29').formulas = [
    [
      `=IF(AND('Power Evidence'!B10="PASS",'Power Evidence'!B9="UNKNOWN"),"PASS","FAIL")`,
    ],
  ];
  checks.getRange('B30').formulas = [
    [
      '=IF(AND(ROWS(\'Cost Baseline\'!$A$11:$A$50)=40,COUNTIF(\'Cost Baseline\'!$F$11:$F$50,"gate_passed")=1),"PASS","FAIL")',
    ],
  ];
  checks.getRange('B31').formulas = [
    ['=IF(\'Cost Baseline\'!B6="NO","PASS","FAIL")'],
  ];
  checks.getRange('B32').formulas = [
    [
      '=IF(AND(LEFT(\'Project Cost Check\'!B26,8)="WITHHELD",\'Project Cost Check\'!B29="",\'Project Cost Check\'!B30=""),"PASS","FAIL")',
    ],
  ];
  checks.getRange('B33').formulas = [
    ['=IF(\'Canada Expansion\'!B8="NO","PASS","FAIL")'],
  ];
  checks.getRange('B34').formulas = [
    ['=IF(\'Canada Expansion\'!B12="NO","PASS","FAIL")'],
  ];
  checks.getRange('B35').formulas = [
    ['=IF(\'Canada Expansion\'!B16="NO","PASS","FAIL")'],
  ];
  checks.getRange('B36').formulas = [
    ['=IF(\'Canada Expansion\'!B20="NO","PASS","FAIL")'],
  ];
  checks.getRange('B37').formulas = [
    [
      '=IF(AND(\'Attribution Gate\'!B9="NO",\'Attribution Gate\'!B10="",\'Attribution Gate\'!B11="",\'Attribution Gate\'!B12=""),"PASS","FAIL")',
    ],
  ];
  const investmentControlLastRow = 10 + investmentControlRows.length;
  checks.getRange('B38').formulas = [
    [
      `=IF(AND(ROWS('Investment Controls'!$A$11:$A$${investmentControlLastRow})=${investmentControlReport.observation_count},COUNTIF('Investment Controls'!$M$11:$M$${investmentControlLastRow},"observed")=${investmentControlReport.observation_count},COUNTIF('Investment Controls'!$N$11:$N$${investmentControlLastRow},"inferred")=${investmentControlReport.observation_count}),"PASS","FAIL")`,
    ],
  ];
  const procurementIntakeLastRow = 10 + procurementOutcomeRows.length;
  checks.getRange('B39').formulas = [
    [
      `=IF(AND(ROWS('Procurement Intake'!$A$11:$A$${procurementIntakeLastRow})=${procurementOutcomeReport.construction_linkage_count},'Procurement Intake'!A6=${procurementOutcomeReport.construction_linkage_count},'Procurement Intake'!U6=0,COUNTIF('Procurement Intake'!$R$11:$R$${procurementIntakeLastRow},"missing_required_fields")=${procurementOutcomeReport.construction_linkage_count},COUNTIF('Procurement Intake'!$S$11:$S$${procurementIntakeLastRow},"missing_required_fields")=${procurementOutcomeReport.construction_linkage_count},COUNTIF('Procurement Intake'!$T$11:$T$${procurementIntakeLastRow},"missing_compliant_bidder_count")=${procurementOutcomeReport.construction_linkage_count}),"PASS","FAIL")`,
    ],
  ];
  const permitCandidateLastRow =
    13 +
    permitProxyRows.filter(
      (row) => row.candidate_status === 'data_centre_candidate',
    ).length;
  checks.getRange('B40').formulas = [
    [
      `=IF(AND('Permit Proxy'!A6=${permitProxyReport.broad_screen_row_count},'Permit Proxy'!C6=${permitProxyReport.data_centre_candidate_count},'Permit Proxy'!G6=${permitProxyReport.explicit_ai_reference_count},'Permit Proxy'!I6=${permitProxyReport.data_centre_candidate_occupancy_date_available_count},ROWS('Permit Proxy'!$A$14:$A$${permitCandidateLastRow})=${permitProxyReport.data_centre_candidate_count},COUNTIF('Permit Proxy'!$J$14:$J$${permitCandidateLastRow},"observed")=0),"PASS","FAIL")`,
    ],
  ];
  checks.getRange('B41').formulas = [
    [
      `=IF(AND('Audited Outcomes'!B6=${auditedOutcomes.coverage_summary.named_completed_project_count},'Audited Outcomes'!B9=0,'Audited Outcomes'!B11="NO",COUNTIF('Audited Outcomes'!$K$20:$K$${19 + auditedOutcomes.cases.length},"PASS")=${auditedOutcomes.cases.length},COUNTIF('Audited Outcomes'!$N$14:$O$${13 + auditedOutcomes.cases.length},"YES")=0),"PASS","FAIL")`,
    ],
  ];
  const quebecProjectLastRow = 24 + quebecRevisionRows.length;
  checks.getRange('B42').formulas = [
    [
      `=IF(AND('Quebec Revisions'!B6=${quebecRevisions.coverage_summary.source_project_count},'Quebec Revisions'!D6=${quebecRevisions.coverage_summary.stable_lifecycle_project_id_count},'Quebec Revisions'!D7=${quebecRevisions.coverage_summary.cost_revision_chain_reconciled_project_count},'Quebec Revisions'!D8=${quebecRevisions.coverage_summary.schedule_revision_chain_reconciled_project_count},'Quebec Revisions'!B10="NO",'Quebec Revisions'!D10="NO",ROWS('Quebec Revisions'!$A$25:$A$${quebecProjectLastRow})=${quebecRevisionRows.length},COUNTIF('Quebec Revisions'!$H$25:$H$${quebecProjectLastRow},"YES")=${quebecRevisions.coverage_summary.cost_revision_chain_reconciled_project_count},COUNTIF('Quebec Revisions'!$N$25:$N$${quebecProjectLastRow},"YES")=${quebecRevisions.coverage_summary.schedule_revision_chain_reconciled_project_count}),"PASS","FAIL")`,
    ],
  ];
  const quebecLifecycleLastRow = 86 + quebecFullLifecycleRows.length;
  const quebecSnapshotLastRow = 14 + quebecFullArchive.snapshot_summaries.length;
  const quebecTransitionLastRow = 14 + quebecFullTransitionRows.length;
  checks.getRange('B43').formulas = [
    [
      `=IF(AND('Quebec Vintages'!B6=${quebecFullArchive.snapshot_date_count},'Quebec Vintages'!D6=${quebecFullArchive.snapshot_observation_count},'Quebec Vintages'!B7=${quebecFullArchive.unique_project_count},'Quebec Vintages'!D7=${quebecFullArchive.latest_snapshot_project_count},'Quebec Vintages'!B8=${quebecFullArchive.disappearance_event_count},'Quebec Vintages'!D8=${quebecFullArchive.publisher_declared_retirement_disappearance_event_count},'Quebec Vintages'!B9=${quebecFullArchive.unclassified_disappearance_event_count},'Quebec Vintages'!D9=${quebecFullArchive.project_with_catalog_reentry_count},'Quebec Vintages'!B10=${quebecFullArchiveContract.direct_csv_snapshot_count},'Quebec Vintages'!D10=${quebecFullArchiveContract.paired_xlsx_fallback_count},'Quebec Vintages'!B11="NO",'Quebec Vintages'!D11="NO",ROWS('Quebec Vintages'!$A$15:$A$${quebecSnapshotLastRow})=${quebecFullArchive.snapshot_date_count},ROWS('Quebec Vintages'!$J$15:$J$${quebecTransitionLastRow})=${quebecFullTransitionRows.length},ROWS('Quebec Vintages'!$A$87:$A$${quebecLifecycleLastRow})=${quebecFullLifecycleRows.length},COUNTIF('Quebec Vintages'!$H$87:$H$${quebecLifecycleLastRow},"YES")=${quebecFullArchive.present_in_latest_project_count},SUM('Quebec Vintages'!$M$87:$M$${quebecLifecycleLastRow})=${quebecFullArchive.publisher_declared_retirement_disappearance_event_count}),"PASS","FAIL")`,
    ],
  ];
  checks.getRange('B44').formulas = [
    [
      '=IF(AND(COUNTA(\'Scenario Variants\'!$A$5:$A$8)=4,COUNTIF(\'Scenario Variants\'!$K$5:$K$8,"NO")=4,COUNTIF(\'Scenario Variants\'!$L$5:$L$8,"NO")=4,COUNTIF(\'Scenario Variants\'!$E$5:$E$8,10)=3,COUNTIF(\'Scenario Variants\'!$E$5:$E$8,15)=1,COUNTIF(\'Scenario Variants\'!$G$5:$G$8,72%)=3,COUNTIF(\'Scenario Variants\'!$G$5:$G$8,90%)=1,ABS(\'Scenario Variants\'!E12-\'Scenario Variants\'!D12/(1+ABS(\'Scenario Variants\'!D12)))<0.000001),"PASS","FAIL")',
    ],
  ];
  checks.getRange('B45').formulas = [
    [
      '=IF(AND(ROWS(\'Historical Envelope\'!$A$12:$A$51)=40,COUNTIF(\'Historical Envelope\'!$F$12:$F$51,"")=0,\'Historical Envelope\'!E5="YES",COUNTIF(\'Historical Envelope\'!$E$6:$E$8,"NO")=3,COUNTIF(\'Historical Envelope\'!$S$12:$S$51,"")=0,ABS(\'Historical Envelope\'!R12-((1+\'Historical Envelope\'!L12/100)^(1/\'Historical Envelope\'!E12)-1))<0.000001),"PASS","FAIL")',
    ],
  ];
  checks.getRange('B46').formulas = [
    [
      '=IF(AND(\'Reference Review\'!B6="pending_independent_review",\'Reference Review\'!E5="NO",\'Reference Review\'!E6="NO",\'Reference Review\'!E7="NO",\'Reference Review\'!E8="NO",\'Reference Review\'!E9=0,\'Reference Review\'!B8=10,\'Reference Review\'!B9=10,\'Reference Review\'!B10=1,COUNTA(\'Reference Review\'!$A$19:$A$28)=10,COUNTIF(\'Reference Review\'!$C$19:$C$28,"pending_independent_review")=10,COUNTA(\'Reference Review\'!$A$14:$A$15)=2,COUNTIF(\'Reference Review\'!$B$14:$B$15,"blocked")=2),"PASS","FAIL")',
    ],
  ];
  checks.getRange('B47').formulas = [
    [
      '=IF(AND(\'Sector Capex\'!B6=294,\'Sector Capex\'!B7=14,\'Sector Capex\'!B8=21,\'Sector Capex\'!E5="YES",\'Sector Capex\'!E6="NO",\'Sector Capex\'!E7="NO",\'Sector Capex\'!E8=99,\'Sector Capex\'!E9="51",ROWS(\'Sector Capex\'!$A$13:$A$306)=294,COUNTIF(\'Sector Capex\'!$R$13:$R$306,"NO")=294,COUNTIF(\'Sector Capex\'!$T$13:$T$306,"")=0,SUMIFS(\'Sector Capex\'!$H$13:$H$306,\'Sector Capex\'!$B$13:$B$306,"PR_48",\'Sector Capex\'!$E$13:$E$306,2024)=458600000),"PASS","FAIL")',
    ],
  ];
  checks.getRange('B48').formulas = [
    [
      '=IF(AND(\'CMA Reference\'!B6=1752,\'CMA Reference\'!B7=12,\'CMA Reference\'!B8=60,\'CMA Reference\'!B9=9,\'CMA Reference\'!B10=36,\'CMA Reference\'!E5=15,\'CMA Reference\'!E6="NO",\'CMA Reference\'!E7="Vancouver CMA only",\'CMA Reference\'!E9="baseline_only",\'CMA Reference\'!E10="pending",ROWS(\'CMA Reference\'!$A$13:$A$72)=60,COUNTIF(\'CMA Reference\'!$J$13:$J$72,"gate_passed")=9,COUNTIF(\'CMA Reference\'!$J$13:$J$72,"gate_failed")=36,COUNTIF(\'CMA Reference\'!$J$13:$J$72,"not_assessed")=15,COUNTIFS(\'CMA Reference\'!$A$13:$A$72,"CMA_933",\'CMA Reference\'!$J$13:$J$72,"gate_passed")=9,COUNTIFS(\'CMA Reference\'!$A$13:$A$72,"CMA_535",\'CMA Reference\'!$J$13:$J$72,"gate_passed")=0,COUNTIFS(\'CMA Reference\'!$A$13:$A$72,"CMA_462",\'CMA Reference\'!$J$13:$J$72,"gate_passed")=0,COUNT(\'CMA Reference\'!$L$13:$L$72)=9,COUNTIF(\'CMA Reference\'!$U$13:$U$72,"NO")=60,COUNTIF(\'CMA Reference\'!$W$13:$W$72,"")=0),"PASS","FAIL")',
    ],
  ];
  const regionalMacroLastRow = 16 + regionalMacroRows.length;
  checks.getRange('B49').formulas = [
    [
      `=IF(AND(ROWS('Regional Macro'!$A$17:$A$${regionalMacroLastRow})=${regionalMacroReport.observation_count},COUNTIF('Regional Macro'!$N$17:$N$${regionalMacroLastRow},"observed")=${regionalMacroReport.observation_count},COUNTIF('Regional Macro'!$O$17:$O$${regionalMacroLastRow},"observed")=494,COUNTIF('Regional Macro'!$O$17:$O$${regionalMacroLastRow},"inferred")=2622),"PASS","FAIL")`,
    ],
  ];
  checks.getRange('B50').formulas = [[
    '=IF(AND(\'Province Bridge\'!B6=1752,\'Province Bridge\'!B7=1296,\'Province Bridge\'!B8=456,\'Province Bridge\'!B9=12,\'Province Bridge\'!B10=9,\'Province Bridge\'!E5=12,\'Province Bridge\'!E6<3%,\'Province Bridge\'!E7="NO",\'Province Bridge\'!E8="YES",\'Province Bridge\'!E9="baseline_only",\'Province Bridge\'!E10="pending",ROWS(\'Province Bridge\'!$A$29:$A$88)=60,COUNTIF(\'Province Bridge\'!$J$29:$J$88,"gate_passed")=9,COUNTIF(\'Province Bridge\'!$J$29:$J$88,"gate_failed")=36,COUNTIF(\'Province Bridge\'!$J$29:$J$88,"not_assessed")=15,COUNTIF(\'Province Bridge\'!$J$14:$J$25,"PASS")=12,COUNTIF(\'Province Bridge\'!$U$29:$U$88,"NO")=60),"PASS","FAIL")',
  ]];
  checks.getRange('B51').formulas = [[
    '=IF(AND(\'Historical Analog\'!B6=8,\'Historical Analog\'!B7=1560,\'Historical Analog\'!E5="YES",\'Historical Analog\'!E6="YES",COUNTIF(\'Historical Analog\'!E7:E10,"NO")=4,ROWS(\'Historical Analog\'!$A$24:$A$1583)=1560,\'Historical Analog\'!J13="limited_history_only",\'Historical Analog\'!J14=154,\'Historical Analog\'!J15=6,ABS(\'Historical Analog\'!F14-1.136742)<0.000001,ABS(\'Historical Analog\'!F15-(\'Historical Analog\'!F14-1))<0.000001,ABS(\'Historical Analog\'!F16-\'Historical Analog\'!B13*\'Historical Analog\'!F14)<1,\'Historical Analog\'!J16="NO",\'Historical Analog\'!J17="NO",COUNTIF(\'Historical Analog\'!$R$24:$R$1583,"")=0),"PASS","FAIL")',
  ]];
  checks.getRange('B52').formulas = [[
    '=IF(AND(COUNTIF(\'AI Projects\'!$AC$6:$AC$16,"PASS")=11,\'AI Projects\'!AA16="NO"),"PASS","FAIL")',
  ]];
  checks.getRange('B53').formulas = [[
    '=IF(AND(\'Panel Preflight\'!A6=5,\'Panel Preflight\'!C6=2,\'Panel Preflight\'!E6=3,\'Panel Preflight\'!G6=27,\'Panel Preflight\'!I6=0,COUNTA(\'Panel Preflight\'!$A$22:$A$25)=4,COUNTA(\'Panel Preflight\'!$A$29:$A$39)=11,COUNTIF(\'Panel Preflight\'!$E$29:$E$39,"non_authorizing")=10,COUNTIF(\'Panel Preflight\'!$E$29:$E$39,"control_only")=1),"PASS","FAIL")',
  ]];
  checks.getRange('B54').formulas = [[
    '=IF(AND(\'Treatment Sources\'!A6=8,\'Treatment Sources\'!D6=7,\'Treatment Sources\'!G6=0,\'Treatment Sources\'!J6="NO",COUNTA(\'Treatment Sources\'!$A$14:$A$21)=8,COUNTIF(\'Treatment Sources\'!$L$14:$L$21,"EXCLUDED")=8,COUNTIF(\'Treatment Sources\'!$D$14:$J$21,"FAIL")>0,COUNTA(\'Treatment Sources\'!$B$30:$B$32)=0),"PASS","FAIL")',
  ]];
  checks.getRange('B55').formulas = [[
    '=IF(AND(\'Canada Coverage\'!B6=13,\'Canada Coverage\'!B7=7,\'Canada Coverage\'!B8=91,\'Canada Coverage\'!B9="NO",\'Canada Coverage\'!B10="NO",COUNTA(\'Canada Coverage\'!$A$13:$A$25)=13,COUNTA(\'Canada Coverage\'!$C$13:$I$25)=91,COUNTIF(\'Canada Coverage\'!$C$13:$I$25,"not_available")=22,COUNTIF(\'Canada Coverage\'!$C$13:$I$25,"available_with_missingness")=27,COUNTIF(\'Canada Coverage\'!$C$13:$I$25,"available")=42),"PASS","FAIL")',
  ]];
  checks.getRange('B16:B55').conditionalFormats.add('containsText', {
    text: 'PASS',
    format: { fill: C.tealLight, font: { color: C.tealDark, bold: true } },
  });
  checks.getRange('B16:B55').conditionalFormats.add('containsText', {
    text: 'FAIL',
    format: { fill: '#FDE8E5', font: { color: '#A33D32', bold: true } },
  });
  checks.getRange('A57:D59').merge();
  checks.getRange('A57').values = [
    [
      'A public release is blocked if any check returns FAIL, if the workbook and website manifests differ, if assumptions/scenarios are presented as observations, if an AI-attributable value appears before the identification gate passes, or if a cost output appears while a required validation or independent-review gate is withheld.',
    ],
  ];
  noteBlock(checks.getRange('A57:D59'));
  setWidths(checks, { A: 59, B: 61, C: 15, D: 18 }, 60);
}

function buildDashboard() {
  titleBand(
    dashboard,
    'Alberta pilot dashboard',
    `Observed pipeline + $50B counterfactual diagnostic · workbook ${workbookBuildVersion}`,
    'L',
  );
  card(
    dashboard,
    'A5:C5',
    'A6:C7',
    'Known reported core capex',
    `='AI Projects'!C${4 + release.baseline.projects.length + 1}`,
  );
  dashboard.getRange('A6').formulas = [
    [
      `=SUMIF('AI Projects'!$M$5:$M$${4 + release.baseline.projects.length},"core_data_centre",'AI Projects'!$C$5:$C$${4 + release.baseline.projects.length})/1000000000`,
    ],
  ];
  dashboard.getRange('A6').format.numberFormat = '$0.00"B"';
  card(dashboard, 'D5:F5', 'D6:F7', 'Core facility records', '');
  dashboard.getRange('D6').formulas = [
    [
      `=COUNTIF('AI Projects'!$M$5:$M$${4 + release.baseline.projects.length},"core_data_centre")`,
    ],
  ];
  dashboard.getRange('D6').format.numberFormat = '0';
  card(dashboard, 'G5:I5', 'G6:I7', 'Central trade pressure', '');
  dashboard.getRange('G6').formulas = [["=MAX('Pressure Results'!$F$5:$F$8)"]];
  dashboard.getRange('G6').format.numberFormat = '0.00';
  card(dashboard, 'J5:L5', 'J6:L7', 'Transfer planning proxy', '');
  dashboard.getRange('J6').formulas = [["='Assumptions'!K24/1000"]];
  dashboard.getRange('J6').format.numberFormat = '0.00" GW"';

  dashboard.getRange('A9:B9').values = [['Trade', 'Central pressure']];
  header(dashboard.getRange('A9:B9'));
  release.scenario.trade_pressure_order.forEach((_, index) => {
    const row = 10 + index;
    dashboard.getRange(`A${row}`).formulas = [
      [`='Pressure Results'!B${5 + index}`],
    ];
    dashboard.getRange(`B${row}`).formulas = [
      [`='Pressure Results'!F${5 + index}`],
    ];
  });
  dashboard.getRange(
    `B10:B${9 + release.scenario.trade_pressure_order.length}`,
  ).format.numberFormat = '0.00';
  const tradeChart = dashboard.charts.add(
    'bar',
    dashboard.getRange(
      `A9:B${9 + release.scenario.trade_pressure_order.length}`,
    ),
  );
  tradeChart.title =
    'Which trades are pinched first? (diagnostic pressure score)';
  tradeChart.hasLegend = false;
  tradeChart.xAxis = { axisType: 'textAxis', textStyle: { fontSize: 9 } };
  tradeChart.yAxis = { numberFormatCode: '0.00', min: 0 };
  tradeChart.setPosition('D9', 'L22');

  const albertaLabourRows = labourPressure.trade_diagnostics
    .filter(
      (item) =>
        item.geography_id === 'PR_48' &&
        item.vacancies_per_1_000_2021_employed !== null,
    )
    .sort(
      (a, b) =>
        b.vacancies_per_1_000_2021_employed -
        a.vacancies_per_1_000_2021_employed,
    );
  dashboard.getRange('A16:B16').values = [['Recruitment screen', 'Per 1,000']];
  header(dashboard.getRange('A16:B16'));
  albertaLabourRows.forEach((_, index) => {
    const dashboardRow = 17 + index;
    const diagnosticRow = 5 + index;
    dashboard.getRange(`A${dashboardRow}`).formulas = [
      [`='Labour Diagnostic'!A${diagnosticRow}`],
    ];
    dashboard.getRange(`B${dashboardRow}`).formulas = [
      [`='Labour Diagnostic'!D${diagnosticRow}`],
    ];
  });
  dashboard.getRange(
    `B17:B${16 + albertaLabourRows.length}`,
  ).format.numberFormat = '0.00';
  const recruitmentNoteStart = 18 + albertaLabourRows.length;
  const recruitmentNoteEnd = Math.min(23, recruitmentNoteStart + 2);
  dashboard.getRange(`A${recruitmentNoteStart}:B${recruitmentNoteEnd}`).merge();
  dashboard.getRange(`A${recruitmentNoteStart}`).values = [
    ['Cross-vintage screening metric only; incomplete trades are excluded.'],
  ];
  noteBlock(
    dashboard.getRange(`A${recruitmentNoteStart}:B${recruitmentNoteEnd}`),
  );

  dashboard.getRange('A25:B25').values = [['Year', 'Total capex (CAD bn)']];
  header(dashboard.getRange('A25:B25'));
  scenarioDefinition.annual_profile.forEach((_, index) => {
    const row = 26 + index;
    dashboard.getRange(`A${row}`).formulas = [
      [`='Scenario Timeline'!A${5 + index}`],
    ];
    dashboard.getRange(`B${row}`).formulas = [
      [`='Scenario Timeline'!C${5 + index}/1000000000`],
    ];
  });
  dashboard.getRange('B26:B35').format.numberFormat = '$0.0';
  const flowChart = dashboard.charts.add('line', dashboard.getRange('A25:B35'));
  flowChart.title = 'Counterfactual annual capex flow (CAD bn)';
  flowChart.hasLegend = false;
  flowChart.xAxis = { axisType: 'textAxis', textStyle: { fontSize: 9 } };
  flowChart.yAxis = { numberFormatCode: '$0.0', min: 0 };
  flowChart.setPosition('D25', 'L39');

  dashboard.getRange('A41:C42').merge();
  dashboard.getRange('A41').values = [
    ['Four- to five-year project cost outlook'],
  ];
  dashboard.getRange('A41:C42').format = {
    fill: C.amber,
    font: { bold: true, color: C.white, size: 11 },
    wrapText: true,
    verticalAlignment: 'center',
    horizontalAlignment: 'center',
  };
  dashboard.getRange('D41:L42').merge();
  dashboard.getRange('D41').formulas = [["='Project Cost Check'!B26"]];
  dashboard.getRange('D41:L42').format = {
    fill: C.amberLight,
    font: { bold: true, color: '#8A4826', size: 12 },
    wrapText: true,
    verticalAlignment: 'center',
    horizontalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };

  dashboard.getRange('A44:L47').merge();
  dashboard.getRange('A44').values = [
    [
      'WITHHELD COST OUTPUTS + UNCALIBRATED STRUCTURAL DIAGNOSTIC: only 1 of 40 reference-class horizon checks passes, and no public project-cost projection is authorized. Four- and five-year Alberta health and school results remain blank. Pressure scores are mechanisms, not percentages or delay estimates. Additional transmission for the $50B case and every AI-attributable cost or schedule increment remain unknown.',
    ],
  ];
  dashboard.getRange('A44:L47').format = {
    fill: C.amberLight,
    font: { color: '#7B4529', size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#E1B48E' },
  };
  dashboard.getRange('A48:L48').merge();
  dashboard.getRange('A48').values = [
    [`Release hash: ${release.manifest.input_manifest_hash}`],
  ];
  dashboard.getRange('A48').format = {
    font: { name: 'Aptos Mono', size: 8, color: C.muted },
    horizontalAlignment: 'left',
  };
  dashboard.freezePanes.freezeRows(4);
  setWidths(
    dashboard,
    {
      A: 18,
      B: 18,
      C: 4,
      D: 15,
      E: 15,
      F: 15,
      G: 15,
      H: 15,
      I: 15,
      J: 15,
      K: 15,
      L: 15,
    },
    48,
  );
}

function titleBand(sheet, title, subtitle, endColumn) {
  sheet.getRange(`A1:${endColumn}2`).merge();
  sheet.getRange('A1').values = [[title]];
  sheet.getRange(`A1:${endColumn}2`).format = {
    fill: C.navy,
    font: { name: 'Aptos Display', size: 22, bold: true, color: C.white },
    verticalAlignment: 'center',
    horizontalAlignment: 'left',
  };
  sheet.getRange(`A3:${endColumn}3`).merge();
  sheet.getRange('A3').values = [[subtitle]];
  sheet.getRange(`A3:${endColumn}3`).format = {
    fill: C.navy2,
    font: { size: 10, color: '#B7D9D2' },
    verticalAlignment: 'center',
  };
  sheet.getRange('A1').format.rowHeight = 28;
  sheet.getRange('A2').format.rowHeight = 28;
  sheet.getRange('A3').format.rowHeight = 21;
}

function header(range) {
  range.format = {
    fill: C.tealDark,
    font: { bold: true, color: C.white, size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'inside', style: 'thin', color: '#79A9A0' },
  };
  range.format.rowHeight = 28;
}

function sectionHeader(range, fill = C.tealDark) {
  range.format = {
    fill,
    font: { bold: true, color: C.white, size: 11 },
    verticalAlignment: 'center',
  };
}

function noteBlock(range) {
  range.format = {
    fill: C.soft,
    font: { color: C.muted, size: 10 },
    wrapText: true,
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: C.line },
  };
}

function inputStyle(range) {
  range.format = {
    fill: '#EAF3F8',
    font: { color: C.blueInput },
    borders: { preset: 'outside', style: 'thin', color: '#B7CDD9' },
  };
}

function card(sheet, labelRange, valueRange, label, formula) {
  sheet.getRange(labelRange).merge();
  sheet.getRange(labelRange.split(':')[0]).values = [[label]];
  sheet.getRange(labelRange).format = {
    fill: C.tealLight,
    font: { bold: true, color: C.tealDark, size: 9 },
    horizontalAlignment: 'center',
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
  };
  sheet.getRange(valueRange).merge();
  if (formula) sheet.getRange(valueRange.split(':')[0]).formulas = [[formula]];
  sheet.getRange(valueRange).format = {
    fill: C.white,
    font: { bold: true, color: C.ink, size: 21 },
    horizontalAlignment: 'center',
    verticalAlignment: 'center',
    borders: { preset: 'outside', style: 'thin', color: '#B9CEC7' },
  };
}

function setWidths(sheet, widths, maxRow) {
  for (const [column, width] of Object.entries(widths))
    sheet.getRange(`${column}1:${column}${maxRow}`).format.columnWidth = width;
  sheet.getRange(`A1:${Object.keys(widths).at(-1)}${maxRow}`).format.wrapText =
    true;
}

function labelize(value) {
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function provinceLabel(geographyId) {
  return (
    {
      PR_24: 'Quebec',
      PR_35: 'Ontario',
      PR_48: 'Alberta',
      PR_59: 'British Columbia',
    }[geographyId] ?? geographyId
  );
}

function tradeLabel(nodeId) {
  return (
    {
      trade_concrete: 'Concrete',
      trade_electricians: 'Electricians',
      trade_hvac: 'HVAC',
      trade_power_line: 'Power line',
    }[nodeId] ?? labelize(nodeId.replace('trade_', ''))
  );
}

function numberOrNull(value) {
  return value === '' ? null : Number(value);
}

function dateOrNull(value) {
  return value === '' ? null : new Date(`${value}T00:00:00Z`);
}

function monthOrNull(value) {
  return value === '' ? null : new Date(`${value}-01T00:00:00Z`);
}

function yesNo(value) {
  return String(value).toLowerCase() === 'true' ? 'YES' : 'NO';
}

function powerSourceUrl(sourceId) {
  if (sourceId.includes('AESO_DATA_CENTRE_UPDATE_2025_09')) {
    return 'https://www.aeso.ca/assets/Uploads/grid/Data-Centre/AESO-Data-Centre-Update-September-2025.pdf';
  }
  if (sourceId.includes('AESO_INTERIM_LARGE_LOAD_2025_06')) {
    return 'https://www.aeso.ca/aeso/newsroom/aeso-announces-interim-approach-to-large-load-connections/';
  }
  return 'https://www.aeso.ca/grid/connecting-to-the-grid/large-load-projects/';
}

function parseCsv(text) {
  const lines = text
    .replace(/^\uFEFF/, '')
    .trim()
    .split(/\r?\n/);
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    return Object.fromEntries(
      headers.map((headerName, index) => [headerName, values[index] ?? '']),
    );
  });
}

function parseCsvLine(line) {
  const output = [];
  let value = '';
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (character === '"') {
      if (quoted && line[index + 1] === '"') {
        value += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === ',' && !quoted) {
      output.push(value);
      value = '';
    } else {
      value += character;
    }
  }
  output.push(value);
  return output;
}
