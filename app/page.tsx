import Link from 'next/link';
import { redirect } from 'next/navigation';
import { loadConstructionSnapshot } from '@/lib/construction-snapshot';
import { AdmDecisionBrief } from '@/components/adm-decision-brief';
import { AlbertaExecutive } from '@/components/alberta-executive';
import { AlbertaOverview } from '@/components/alberta-overview';
import { ResearchShell, PageIntro, SiteFooter } from '@/components/site-shell';
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';
export default async function Home({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const scenarioKeys = [
    'asset',
    'metro',
    'budget',
    'start',
    'years',
    'name',
    'basis',
    'stage',
    'profile',
    'contingency',
    'baseline',
    'peak',
    'capture',
    'lag',
    'uncertainty',
  ];
  if (scenarioKeys.some((key) => query[key] !== undefined)) {
    const values = new URLSearchParams();
    for (const [key, value] of Object.entries(query))
      if (typeof value === 'string') values.set(key, value);
    redirect(`/project-scenario?${values.toString()}`);
  }
  const { data, revision } = await loadConstructionSnapshot();
  return (
    <ResearchShell>
      <PageIntro
        eyebrow="Alberta infrastructure intelligence"
        title="Where could AI investment pressure Alberta’s public infrastructure?"
        description="AIIO is the AI Infrastructure Impact Observatory. Start with Alberta’s project pipeline and shared construction resources, then explore delivery decisions and project sensitivities."
      />
      <div className="mx-auto max-w-[1440px] space-y-8 px-4 py-6 sm:px-8">
        <nav aria-label="Start exploring" className="grid gap-3 sm:grid-cols-3">
          <Link
            className="rounded-lg bg-brand p-5 font-semibold text-white"
            href="/project-scenario?view=assessment"
          >
            Assess my project →
            <span className="mt-2 block text-sm font-normal">
              Your packages, shared resources and delivery options.
            </span>
          </Link>
          <Link
            className="rounded-lg border border-line bg-surface p-5 font-semibold"
            href="/delivery"
          >
            Review delivery exposure →
            <span className="mt-2 block text-sm font-normal">
              Projects, shared packages and decisions.
            </span>
          </Link>
          <Link
            className="rounded-lg border border-line bg-surface p-5 font-semibold"
            href="/historical-analog"
          >
            Explore Alberta’s previous boom →
            <span className="mt-2 block text-sm font-normal">
              Historical prices and workforce response.
            </span>
          </Link>
        </nav>
        <AlbertaExecutive data={data} />
        <AdmDecisionBrief data={data} revision={revision} />
        <AlbertaOverview
          data={data}
          revision={`${revision}:${new Date().toISOString().slice(0, 10)}`}
        />
      </div>
      <SiteFooter />
    </ResearchShell>
  );
}
