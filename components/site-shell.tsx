import { ChevronRight } from 'lucide-react';
import Link from 'next/link';

import { ModeToggle } from '@/components/mode-toggle';
import {
  ResearchNavigation,
  DesktopNavigation,
  MobileNavigation,
} from '@/components/site-navigation';

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface text-ink">
      <div className="mx-auto flex h-[72px] max-w-[1440px] items-center justify-between px-5 sm:px-8 lg:px-12">
        <Link
          className="flex items-center gap-3"
          href="/"
          aria-label="AIIO Canada home"
        >
          <span className="grid size-9 place-items-center rounded-full border border-[#bdd5ce] bg-white font-mono text-xs font-semibold text-[#17665f] shadow-[0_1px_2px_rgba(13,43,54,0.05)]">
            AI
          </span>
          <span>
            <span className="block text-sm font-semibold tracking-[-0.02em]">
              AIIO Canada
            </span>
            <span className="hidden text-[9px] uppercase tracking-[0.16em] text-[#536864] sm:block">
              Infrastructure impact observatory
            </span>
          </span>
        </Link>
        <DesktopNavigation />
        <div className="flex items-center gap-2">
          <div className="hidden sm:block">
            <ModeToggle compact />
          </div>
          <Link
            className="hidden h-8 items-center gap-1.5 rounded-full border border-[#d5d9d4] bg-white px-3 text-xs font-medium text-[#294a49] shadow-[0_1px_2px_rgba(13,43,54,0.04)] transition-colors hover:border-[#9ebeb6] hover:bg-[#f3f8f6] xl:inline-flex"
            href="/downloads"
          >
            Downloads <ChevronRight className="size-3.5" />
          </Link>
          <MobileNavigation />
        </div>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-surface text-subtle">
      <div className="mx-auto flex max-w-[1440px] flex-col justify-between gap-4 px-5 py-8 text-xs sm:px-8 md:flex-row md:items-center lg:px-12">
        <p>
          AI Infrastructure Impact Observatory Canada · Public research in
          development
        </p>
        <p className="font-mono">Observed ≠ inferred ≠ assumed ≠ scenario</p>
        <Link className="underline underline-offset-2" href="/status">
          System status
        </Link>
      </div>
    </footer>
  );
}

export function PageIntro({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <section className="border-b border-line bg-workspace">
      <div className="mx-auto max-w-[1440px] px-4 py-7 sm:px-8">
        <p className="text-xs font-medium text-brand">{eyebrow}</p>
        <h1 className="mt-2 max-w-4xl text-[26px] font-semibold tracking-tight text-ink">
          {title}
        </h1>
        <p className="mt-3 max-w-4xl text-sm leading-6 text-subtle">
          {description}
        </p>
      </div>
    </section>
  );
}

export function EvidencePill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    observed: 'border-brand/25 bg-brand-soft text-brand',
    inferred: 'border-line bg-workspace text-subtle',
    assumed: 'border-caution/25 bg-caution-soft text-caution',
    scenario: 'border-caution/25 bg-caution-soft text-caution',
  };
  return (
    <span
      className={`inline-flex shrink-0 whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-medium ${styles[status] ?? 'border-line bg-surface text-subtle'}`}
    >
      {status}
    </span>
  );
}

/** Shared frame for decision tools. Navigation is supplied by each workspace. */
export function WorkspaceShell({
  navigation,
  context,
  actions,
  children,
  research = false,
}: {
  research?: boolean;
  navigation: React.ReactNode;
  context: React.ReactNode;
  actions: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="workspace workspace-layout min-h-screen bg-workspace text-ink lg:grid lg:grid-cols-[208px_minmax(0,1fr)]">
      <a
        href="#workspace-content"
        className="sr-only z-50 rounded bg-surface p-3 text-ink focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
      >
        Skip to content
      </a>
      <aside className="workspace-rail flex flex-col bg-rail text-white lg:sticky lg:top-0 lg:h-dvh lg:overflow-y-auto">
        <Link
          href="/"
          className="flex h-[72px] shrink-0 items-center gap-3 border-b border-white/10 px-5"
          aria-label="AIIO Canada home"
        >
          <span className="grid size-8 place-items-center rounded-md border border-white/25 text-xs font-semibold">
            AI
          </span>
          <span className="font-semibold">
            AIIO <span className="font-normal text-white/70">Canada</span>
          </span>
        </Link>
        <div className="px-3 py-4">
          <p className="mb-3 hidden px-3 text-[11px] font-medium uppercase tracking-widest text-white/60 lg:block">
            {research ? 'Research workspace' : 'Decision workspace'}
          </p>
          {navigation}
        </div>
        {!research ? (
          <nav
            aria-label="Research and resources"
            className="mt-auto hidden space-y-1 border-t border-white/10 px-3 py-5 text-[13px] text-white/80 lg:block"
          >
            {[
              ['/research', 'Research observatory'],
              ['/evidence', 'Source registry'],
              ['/scenario', 'Scenario lab'],
              ['/pressure', 'Market pressure'],
              ['/methods', 'Methods'],
              ['/digest', 'Evidence digest'],
              ['/downloads', 'Downloads'],
              ['/status', 'System status'],
            ].map(([href, label]) => (
              <Link
                className="block rounded-md px-3 py-2 hover:bg-rail-active hover:text-white"
                key={href}
                href={href}
              >
                {label}
              </Link>
            ))}
          </nav>
        ) : (
          <p className="mt-auto hidden border-t border-white/10 px-6 py-5 text-xs leading-5 text-white/65 lg:block">
            Public research in development.
            <br />
            Evidence before estimates.
          </p>
        )}
      </aside>
      <div className="min-w-0">
        <header className="workspace-toolbar flex min-h-[72px] flex-wrap items-center justify-between gap-3 border-b border-line bg-surface px-4 py-3 sm:px-8">
          <div className="text-[13px] text-subtle">{context}</div>
          <div className="flex flex-wrap items-center gap-2">
            {actions}
            <div className="lg:hidden">
              <MobileNavigation />
            </div>
          </div>
        </header>
        <main
          id="workspace-content"
          tabIndex={-1}
          className={
            research
              ? 'research-content min-w-0 outline-none'
              : 'executive-screen min-w-0 p-4 outline-none sm:p-8'
          }
        >
          {children}
        </main>
      </div>
    </div>
  );
}

/** Consistent application navigation for every research route. */
export function ResearchShell({ children }: { children: React.ReactNode }) {
  return (
    <WorkspaceShell
      research
      navigation={<ResearchNavigation />}
      context={
        <>
          <span className="font-medium text-ink">AIIO Canada</span>
          <span className="mx-2">/</span>Research workspace
        </>
      }
      actions={
        <Link
          className="inline-flex h-10 items-center gap-2 rounded-md bg-brand px-4 text-sm font-medium text-white hover:bg-brand/90"
          href="/"
        >
          Open dashboard <ChevronRight className="size-4" />
        </Link>
      }
    >
      {children}
    </WorkspaceShell>
  );
}

export function SectionNavigation({
  items,
}: {
  items: Array<[string, string]>;
}) {
  return (
    <nav
      aria-label="On this page"
      className="flex flex-wrap gap-2 border-b border-line bg-surface px-4 py-3 sm:px-8"
    >
      {items.map(([id, label]) => (
        <a
          key={id}
          href={`#${id}`}
          className="rounded-md border border-line px-3 py-2 text-xs font-medium text-subtle hover:bg-brand-soft hover:text-brand"
        >
          {label}
        </a>
      ))}
    </nav>
  );
}
