import { loadConstructionSnapshot } from '@/lib/construction-snapshot';
import { ConstructionWorkspace } from '@/components/construction-workspace';
import { AlbertaOverview } from '@/components/alberta-overview';
import { ResearchShell, PageIntro, SiteFooter } from '@/components/site-shell';
import Link from 'next/link';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export default async function ConstructionPage() {
  const { data, revision } = await loadConstructionSnapshot();
  return (
    <ResearchShell>
      <PageIntro
        eyebrow="Alberta construction intelligence"
        title="Construction demand & capacity"
        description="Explore the Alberta pipeline, workforce, construction prices and procurement procurement signals. Review delivery implications and mitigations, then explore conditional demand in the scenario model."
      />
      <div className="mx-auto max-w-[1440px] px-4 py-4 sm:px-8">
        <Link
          href="/construction/pilot"
          className="text-sm text-brand underline"
        >
          Focused Alberta pilot: CAL-3 Phase 1 and South Windsong School
        </Link>
      </div>
      <ConstructionWorkspace
        evidenceAsOf={data.manifest.asOf}
        overview={
          <AlbertaOverview
            data={data}
            revision={`${revision}:${new Date().toISOString().slice(0, 10)}`}
          />
        }
      />
      <SiteFooter />
    </ResearchShell>
  );
}
