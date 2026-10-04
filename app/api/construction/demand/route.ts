import { loadConstructionSnapshot } from '@/lib/construction-snapshot';
import { modelProjectDemand } from '@/lib/project-demand-model.mjs';
import { buildDemandRisk } from '@/lib/demand-risk-analysis.mjs';
import evidence from '@/public/data/construction/adm-evidence.json';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export async function GET() {
  try {
    const { data, revision } = await loadConstructionSnapshot();
    return Response.json(
      {
        evidenceRevision: revision,
        risk: buildDemandRisk(data.projects, {
          asOf: data.manifest.asOf,
          exposure: evidence.exposure,
        }),
        ...modelProjectDemand(data.projects, { asOf: data.manifest.asOf }),
      },
      {
        headers: {
          'Cache-Control': 'no-store',
          'Content-Disposition':
            'attachment; filename="Alberta_Project_Demand_Model.json"',
        },
      },
    );
  } catch {
    return Response.json(
      { error: 'The published evidence could not support a model run.' },
      { status: 503 },
    );
  }
}
