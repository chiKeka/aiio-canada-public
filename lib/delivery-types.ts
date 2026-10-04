export type Citation = { source: string; verifiedOn: string };
export type Milestone = Citation & { status: string };
export type DeliveryRegister = {
  version: number;
  asOf: string;
  projects: {
    id: string;
    campusId: string | null;
    recordEvidence: Citation | null;
    recordKind: string;
    constructionCost: (Citation & { value: number }) | null;
    milestones: Record<string, Milestone | null>;
  }[];
  packages: (Citation & {
    projectId: string;
    projectName: string;
    projectKind: 'data_centre' | 'infrastructure';
    region: string;
    trade: string;
    start: string;
    end: string;
    basis: 'reported' | 'inferred';
  })[];
  capacity: (Citation & {
    contractor: string;
    region: string;
    trade: string;
    quarter: string;
    paidHours: number;
    committedHours: number;
  })[];
  suppliers: (Citation & {
    supplier: string;
    equipment: string;
    specification: string;
    region: string;
    slotStatus: string;
    requiredOnSite: string;
    leadWeeks: number;
    freightWeeks: number;
    testingWeeks: number;
  })[];
  actions: {
    id: string;
    title: string;
    projectId: string | null;
    owner: string | null;
    due: string | null;
    status: string;
    evidence: string | null;
    benefit: { value: number; basis: string } | null;
  }[];
};
