import Link from 'next/link';
import {
  Download,
  FileJson2,
  FileSpreadsheet,
  Fingerprint,
} from 'lucide-react';

import { PageIntro, SiteFooter, ResearchShell } from '@/components/site-shell';
import releaseData from '@/public/data/latest.json';
import researchSurface from '@/public/data/research-surface.json';

const downloads = [
  {
    icon: FileJson2,
    title: 'Alberta historical boom comparison',
    detail:
      '2005–2008 institutional construction-price observations, index repricing formula, source vintages and interpretation limits.',
    href: '/data/alberta-boom-analog.json',
    format: 'JSON',
  },
  {
    icon: FileSpreadsheet,
    title: 'Alberta delivery briefing',
    detail:
      'Generate an editable PowerPoint from published evidence: pipeline, workforce, construction prices, procurement and mitigation priorities. Source dates and references included.',
    href: '/api/briefing',
    format: 'PPTX',
  },
  {
    icon: FileJson2,
    title: 'Complete public data bundle',
    detail:
      'Baseline, diagnostic scenario, independent power overlay, sources, digest and release manifest',
    href: '/data/latest.json',
    format: 'JSON',
  },
  {
    icon: Fingerprint,
    title: 'Release manifest',
    detail: 'Input and output hashes, model version and code state',
    href: '/data/manifest.json',
    format: 'JSON',
  },
  {
    icon: Fingerprint,
    title: 'Research workspace manifest',
    detail:
      'Hashes the supplemental research artifacts used by the evolving website without promoting them into the frozen release',
    href: '/data/research-surface.json',
    format: 'JSON',
  },
  {
    icon: FileSpreadsheet,
    title: 'Alberta AI project register',
    detail: 'Observed project fields with inferred AI classification',
    href: '/downloads/alberta_ai_projects.csv',
    format: 'CSV',
  },
  {
    icon: FileSpreadsheet,
    title: 'Alberta BCPI observations',
    detail: 'Calgary and Edmonton normalized construction-price rows',
    href: '/downloads/bcpi_alberta.csv',
    format: 'CSV',
  },
  {
    icon: FileSpreadsheet,
    title: 'Alberta labour availability',
    detail:
      'Graph-relevant NOC vacancy and offered-wage observations with suppression and quality flags',
    href: '/downloads/labour_availability_alberta.csv',
    format: 'CSV',
  },
  {
    icon: FileSpreadsheet,
    title: 'Canada provincial labour availability',
    detail:
      'The same trade indicators for all 13 provinces and territories with geography lineage and no national-average substitution',
    href: '/downloads/labour_availability_canada.csv',
    format: 'CSV',
  },
  {
    icon: FileSpreadsheet,
    title: 'Canada detailed-trade workforce stock',
    detail:
      '2021 Census employed-person counts for six NOC unit groups across all provinces and territories, with selected-coordinate lineage and rounding flags',
    href: '/downloads/labour_workforce_stock_canada.csv',
    format: 'CSV',
  },
  {
    icon: FileSpreadsheet,
    title: 'Alberta material-cost screen',
    detail:
      'Selected Calgary and Edmonton BCPI component proxies with quarterly and annual changes',
    href: '/downloads/bcpi_material_cost_screen_alberta.csv',
    format: 'CSV',
  },
  {
    icon: FileSpreadsheet,
    title: 'Alberta public-project exposure',
    detail:
      'Delivery-relevant project records with inferred asset and sponsor signals, schedule overlap and missingness preserved',
    href: '/downloads/public_project_exposure_alberta.csv',
    format: 'CSV',
  },
  {
    icon: FileSpreadsheet,
    title: 'Alberta power evidence screen',
    detail:
      'AESO requested-load, Phase 1 allocation and executed-contract observations with source locators',
    href: '/downloads/power_evidence_alberta.csv',
    format: 'CSV',
  },
  {
    icon: FileSpreadsheet,
    title: 'Auditable Alberta pilot workbook',
    detail:
      'Formula-driven assumptions, diagnostic outputs, evidence registers and release checks',
    href: `/downloads/AIIO_Alberta_Pilot_${releaseData.manifest.version}.xlsx`,
    format: 'XLSX',
  },
];

export default function DownloadsPage() {
  return (
    <ResearchShell>
      <div className="border-b border-line bg-brand-soft px-8 py-3 text-sm">
        <Link href="/construction" className="font-medium text-brand underline">
          Construction demand workspace: quarterly scenarios, benchmarks,
          formulas and presentation downloads
        </Link>
      </div>
      <PageIntro
        eyebrow="Downloads and reproducibility"
        title="Downloads & releases"
        description="The frozen release remains reproducible while the research workspace evolves above it. Separate manifests make mixed vintages, silent changes and accidental promotion detectable."
      />
      <section className="mx-auto max-w-5xl px-5 py-8 sm:px-8 lg:py-8">
        <div className="mb-8 grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-line bg-workspace p-5">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-brand">
              Frozen publication basis
            </p>
            <p className="mt-2 text-lg font-medium">
              Release {releaseData.manifest.version}
            </p>
            <div className="mt-4 grid gap-2 text-xs text-subtle">
              <p>Model: {releaseData.manifest.model_version}</p>
              <p>Schema: {releaseData.manifest.schema_version}</p>
              <p>
                Input manifest:{' '}
                <span className="font-mono">
                  {releaseData.manifest.input_manifest_hash.slice(0, 28)}…
                </span>
              </p>
              <p>Status: {releaseData.manifest.status}</p>
            </div>
          </div>
          <div className="rounded-lg border border-caution/30 bg-workspace p-5">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-caution">
              Evolving research workspace
            </p>
            <p className="mt-2 text-lg font-medium">
              {researchSurface.artifact_count} hash-locked artifacts
            </p>
            <div className="mt-4 grid gap-2 text-xs text-caution">
              <p>Surface: {researchSurface.surface_id}</p>
              <p>Base release: {researchSurface.frozen_release_version}</p>
              <p>
                Artifact manifest:{' '}
                <span className="font-mono">
                  {researchSurface.artifact_manifest_sha256.slice(0, 28)}…
                </span>
              </p>
              <p>Status: workspace research preview · not a public release</p>
            </div>
          </div>
        </div>
        <p className="mb-8 rounded-lg border border-caution/30 bg-workspace p-4 text-xs leading-5 text-caution">
          Supplemental research artifacts support current Research Mode and
          fail-closed executive diagnostics. They are not members of release{' '}
          {releaseData.manifest.version}, do not authorize AI-attributable cost
          or schedule estimates, and will not enter a public bundle until the
          release workflow passes.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          {downloads.map((item) => (
            <a
              className="group rounded-lg border border-line bg-surface p-5 transition-transform hover:-translate-y-0.5 hover:border-line"
              download
              href={item.href}
              key={item.title}
            >
              <div className="flex items-start justify-between">
                <span className="grid size-10 place-items-center rounded-full bg-workspace text-brand">
                  <item.icon className="size-4" />
                </span>
                <span className="font-mono text-[10px] text-subtle">
                  {item.format}
                </span>
              </div>
              <h2 className="mt-6 font-medium">{item.title}</h2>
              <p className="mt-2 text-sm leading-5 text-subtle">
                {item.detail}
              </p>
              <span className="mt-5 inline-flex items-center gap-1 text-xs font-medium text-brand">
                Download <Download className="size-3" />
              </span>
            </a>
          ))}
        </div>
      </section>
      <SiteFooter />
    </ResearchShell>
  );
}
