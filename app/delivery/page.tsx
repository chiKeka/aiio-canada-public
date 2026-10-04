import { loadConstructionSnapshot } from '@/lib/construction-snapshot';
import { ResearchShell, PageIntro, SiteFooter } from '@/components/site-shell';
import { DeliveryWorkspace } from '@/components/delivery-workspace';
import register from '@/data/governance/alberta-delivery-register.json';
import { validateDeliveryRegister } from '@/lib/alberta-delivery.mjs';
import type { DeliveryRegister } from '@/lib/delivery-types';
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';
export default async function DeliveryPage() {
  const { data } = await loadConstructionSnapshot();
  validateDeliveryRegister(register);
  return (
    <ResearchShell>
      <PageIntro
        eyebrow="Alberta delivery decisions"
        title="From evidence to delivery action"
        description="Verify project milestones, locate package overlap, confirm capacity and assign delivery actions."
      />
      <div className="mx-auto max-w-[1440px] px-4 py-6 sm:px-8">
        <DeliveryWorkspace
          projects={data.projects}
          register={register as DeliveryRegister}
        />
      </div>
      <SiteFooter />
    </ResearchShell>
  );
}
