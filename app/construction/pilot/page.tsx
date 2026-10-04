import { AlbertaPilot } from '@/components/alberta-pilot';
import { ResearchShell, PageIntro, SiteFooter } from '@/components/site-shell';

export default function AlbertaPilotPage() {
  return (
    <ResearchShell>
      <PageIntro
        eyebrow="Focused Alberta pilot · review pending"
        title="CAL-3 Phase 1 and South Windsong School"
        description="Source-backed project accounting and a conditional electrical-work scheduling demonstration. Actual shared contractor capacity and attributable public costs remain unknown."
      />
      <AlbertaPilot />
      <SiteFooter />
    </ResearchShell>
  );
}
