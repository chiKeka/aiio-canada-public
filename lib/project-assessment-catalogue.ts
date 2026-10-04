import publishedProjects from '../public/data/construction/projects.json' with { type: 'json' };
import pilot from '../data/pilots/alberta-cal3-windsong-v0.1.json' with { type: 'json' };
import constructionManifest from '../public/data/construction/manifest.json' with { type: 'json' };

export const assessmentAssetTypes = [
  'school',
  'hospital',
  'government',
  'other',
] as const;
export type AssessmentAssetType = (typeof assessmentAssetTypes)[number];
export type AssessmentTrade = 'Civil' | 'Electrical' | 'Mechanical' | 'Other';
export type AssessmentCatchment = 'Calgary' | 'Edmonton' | 'manual' | 'unknown';
export type CatalogueSourceRef = {
  id: string;
  href: string;
  status: 'observed' | 'assumption' | 'unknown';
  reviewStatus: 'published_release' | 'candidate_only' | 'owner_input_required';
  note: string;
  sha256?: string;
};
export const catchmentOptions: {
  id: AssessmentCatchment;
  label: string;
  note: string;
}[] = [
  {
    id: 'unknown',
    label: 'Unknown resource pool',
    note: 'Location does not establish shared crews or capacity. Keep resource competition unknown.',
  },
  {
    id: 'Calgary',
    label: 'Calgary resource pool — owner assumption',
    note: 'Use only with an explicit assumption that selected packages compete for the same trade capacity; geographic proximity alone is insufficient.',
  },
  {
    id: 'Edmonton',
    label: 'Edmonton resource pool — owner assumption',
    note: 'Use only with an explicit assumption that selected packages compete for the same trade capacity; geographic proximity alone is insufficient.',
  },
  {
    id: 'manual',
    label: 'Define another resource pool',
    note: 'Owner must name and affirm a common resource pool. This does not establish empirical competition.',
  },
];
const templateSource: CatalogueSourceRef = {
  id: 'OWNER_PHASE_TEMPLATE_V1',
  href: '/project-scenario?view=assessment',
  status: 'assumption',
  reviewStatus: 'owner_input_required',
  note: 'Editable package headings only. No empirical budget shares, costs, paid hours, workforce conversion, dates or precedence are assigned. Source: AIIO owner assessment template v1.',
};
export type OwnerPhaseTemplate = {
  id: string;
  title: string;
  trade: AssessmentTrade;
  budgetShare: number | null;
  paidHours: number | null;
  remainingExposureCAD: number | null;
  releaseMonth: number | null;
  plannedFinishMonth: number | null;
  basis: 'assumption';
  sourceRefs: CatalogueSourceRef[];
};
export function buildOwnerPhaseTemplates(
  assetType: AssessmentAssetType,
): OwnerPhaseTemplate[] {
  const prefix =
    assetType === 'school'
      ? 'School'
      : assetType === 'hospital'
        ? 'Hospital'
        : assetType === 'government'
          ? 'Government building'
          : 'Project';
  return (['Civil', 'Electrical', 'Mechanical', 'Other'] as const).map(
    (trade) => ({
      id: `owner-${trade.toLowerCase()}`,
      title: `${prefix} ${trade.toLowerCase()} package`,
      trade,
      budgetShare: null,
      paidHours: null,
      remainingExposureCAD: null,
      releaseMonth: null,
      plannedFinishMonth: null,
      basis: 'assumption',
      sourceRefs: [{ ...templateSource }],
    }),
  );
}
export const assessmentSupportBoundary = {
  quantitativeRegion: 'Alberta',
  quantitativeUse:
    'Conditional owner-input scenarios only; no empirical regional calibration, causal attribution or measured capacity is established.',
  institutionalAssetTypes: ['school', 'hospital', 'government'],
  otherLocationsAndTypes:
    'Qualitative diligence only; no region or asset calibration is established by this catalogue.',
  costBoundary:
    'An owner budget or a published whole-project estimate never automatically supplies a trade cost, paid hours, uncommitted exposure or an AI-attributable increment.',
  competitionBoundary:
    'Dates, trade, geographic location and resource-pool assumptions must be supplied separately. A nearby DC is not evidence of contractor or workforce overlap.',
};
type PublishedDCProject = {
  id: string;
  name: string;
  region: string;
  stage: string;
  cost: number | null;
  start: number | null;
  end: number | null;
  source: string;
  asOf: string;
};
type PilotField = {
  value: unknown;
  status: string;
  sourceIds: string[];
  note: string;
};
export type EnablingAssetLink = {
  id: string;
  aiPhaseIds: string[];
  siteId: string | null;
  scope: PilotField;
  incrementality: PilotField;
  costCad: PilotField;
  payer: PilotField;
  funding: PilotField;
  aiCapexMembership: PilotField;
  inServiceMilestone: PilotField;
  payerObligations: PilotField | null;
  sourceRefs: CatalogueSourceRef[];
  publicationStatus: 'candidate_only';
};
const pilotSources = pilot.sources as Record<
  string,
  { url: string; sha256: string }
>;
const copyField = (field: PilotField): PilotField => ({
  ...field,
  value: structuredClone(field.value),
  sourceIds: [...field.sourceIds],
});
export function buildCAL3EnablingLinks(): EnablingAssetLink[] {
  return pilot.enablingAssets.map((asset) => {
    const fields = [
      asset.scope,
      asset.incrementality,
      asset.costCad,
      asset.payer,
      asset.funding,
      asset.aiCapexMembership,
      asset.inServiceMilestone,
    ];
    const extra =
      'payerObligations' in asset
        ? (asset.payerObligations as PilotField)
        : null;
    const sourceIds = [
      ...new Set(
        [...fields, ...(extra ? [extra] : [])].flatMap(
          (field) => field.sourceIds,
        ),
      ),
    ];
    return {
      id: asset.id,
      aiPhaseIds: [...asset.aiPhaseIds],
      siteId: 'siteId' in asset ? (asset.siteId as string) : 'CAL3_SITE',
      scope: copyField(asset.scope),
      incrementality: copyField(asset.incrementality),
      costCad: copyField(asset.costCad),
      payer: copyField(asset.payer),
      funding: copyField(asset.funding),
      aiCapexMembership: copyField(asset.aiCapexMembership),
      inServiceMilestone: copyField(asset.inServiceMilestone),
      payerObligations: extra ? copyField(extra) : null,
      sourceRefs: sourceIds.map((id) => ({
        id,
        href: pilotSources[id]?.url ?? '/construction/pilot',
        sha256: pilotSources[id]?.sha256,
        status: 'observed',
        reviewStatus: 'candidate_only',
        note: 'Source-backed review candidate. Design/permit scope does not establish executed cost, full ultimate payer shares, commissioned service or phase attribution.',
      })),
      publicationStatus: 'candidate_only',
    };
  });
}
export type DCPhaseCatalogueEntry = {
  id: string;
  projectId: string;
  name: string;
  location: string;
  stage: string;
  registryAsOf: string;
  reportedStartYear: number | null;
  reportedEndYear: number | null;
  reportedWindowQualification: string;
  serviceTarget: string | null;
  phaseConstructionCostCAD: null;
  wholeProjectEstimateCAD: number | null;
  costQualification: string;
  defaultCatchment: 'unknown';
  paidHours: null;
  sourceRefs: CatalogueSourceRef[];
  enablingAssetLinks: EnablingAssetLink[];
};
export function buildDCPhaseCatalogue(
  projects: PublishedDCProject[] = publishedProjects,
  projectArtifactSha256?: string,
): DCPhaseCatalogueEntry[] {
  const published = projects === publishedProjects;
  const projectHash =
    projectArtifactSha256 ??
    (published ? constructionManifest.sha256['projects.json'] : undefined);
  return projects.map((project) => {
    const cal3 = project.id === 'ABMP_11416';
    const phaseSource: CatalogueSourceRef[] = cal3
      ? ['CAL3_OPERATOR_TENANT', 'CAL3_OPERATOR_DESIGN'].map((id) => ({
          id,
          href: pilotSources[id].url,
          sha256: pilotSources[id].sha256,
          status: 'observed',
          reviewStatus: 'candidate_only',
          note: 'Phase1 anchor-tenant/design disclosure; no phase-specific construction budget, paid hours, resource pool or precise package chronology.',
        }))
      : [];
    return {
      id: cal3 ? 'CAL3_PHASE1' : `${project.id}_SCOPE_UNRESOLVED`,
      projectId: project.id,
      name: cal3
        ? 'CAL-3 Phase 1 — construction scope unknown'
        : `${project.name} — package scope unknown`,
      location: project.region,
      stage: project.stage,
      registryAsOf: project.asOf,
      reportedStartYear: project.start,
      reportedEndYear: project.end,
      reportedWindowQualification:
        'Registry project-level reported years, where present; not observed trade-package start/completion or proof of delivery. Missing dates remain unknown.',
      serviceTarget: cal3 ? String(pilot.facts.aiServiceTarget.value) : null,
      phaseConstructionCostCAD: null,
      wholeProjectEstimateCAD: project.cost,
      costQualification: cal3
        ? '$750m is the whole-facility register estimate, not a Phase1 construction budget. Regional $1b investment statements are not phase budgets. No conversion to work hours is authorized.'
        : 'Published register estimate applies to its project record (which may name a phase), not reconciled local construction/trade scope, realized spend or exposed commitment. Keep selected package cost unknown.',
      defaultCatchment: 'unknown',
      paidHours: null,
      sourceRefs: [
        {
          id: published
            ? 'ALBERTA_CONSTRUCTION_RELEASE'
            : 'SUPPLIED_DC_PROJECT_RECORDS',
          href: project.source || '/construction',
          sha256: projectHash,
          status: published ? 'observed' : 'assumption',
          reviewStatus: published
            ? 'published_release'
            : 'owner_input_required',
          note: `Project selection record, as of ${project.asOf}; publisher stage and estimate are not realized work. Supplied revisions require their own review and provenance; the original release hash is not reused.`,
        },
        ...phaseSource,
      ],
      enablingAssetLinks: cal3 ? buildCAL3EnablingLinks() : [],
    };
  });
}
export const dcPhaseCatalogue = buildDCPhaseCatalogue();

/** Engine-ready owner packages; headings do not initialize numerical demand. */
export function buildOwnerPackageTemplates(assetType: AssessmentAssetType) {
  return buildOwnerPhaseTemplates(assetType).map((template) => ({
    id: template.id,
    name: template.title,
    scope: template.trade,
    trade: template.trade,
    catchment: null as string | null,
    hours: null as number | null,
    releaseMonth: null as number | null,
    finishMonth: null as number | null,
    predecessors: [] as string[],
    budgetCAD: null as number | null,
    uncommittedCAD: null as number | null,
    commitment: 'unknown' as const,
    cashMonth: null as number | null,
  }));
}
