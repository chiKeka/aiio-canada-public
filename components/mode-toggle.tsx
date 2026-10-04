'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function ModeToggle({ compact = false }: { compact?: boolean }) {
  const pathname = usePathname();
  const decisionMode = pathname === '/';
  const researchMode = pathname === '/research';

  return (
    <nav
      aria-label="View mode"
      className="inline-flex rounded-full border border-line bg-workspace p-0.5"
    >
      <Link
        aria-current={decisionMode ? 'page' : undefined}
        className={`rounded-full px-2.5 py-1.5 text-[11px] font-semibold transition-colors ${
          decisionMode ? 'bg-surface text-ink' : 'text-subtle hover:text-brand'
        }`}
        href="/"
      >
        {compact ? 'Decision' : 'Decision mode'}
      </Link>
      <Link
        aria-current={researchMode ? 'page' : undefined}
        className={`rounded-full px-2.5 py-1.5 text-[11px] font-semibold transition-colors ${
          researchMode ? 'bg-surface text-ink' : 'text-subtle hover:text-brand'
        }`}
        href="/research"
      >
        {compact ? 'Research' : 'Research mode'}
      </Link>
    </nav>
  );
}
