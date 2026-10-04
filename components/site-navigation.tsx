'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  Activity,
  BookOpen,
  Database,
  Download,
  FileText,
  FlaskConical,
  Gauge,
  LayoutDashboard,
  Layers3,
  Menu,
  ShieldCheck,
} from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

const navigation = [
  { href: '/', label: 'Alberta overview', icon: LayoutDashboard },
  {
    href: '/project-scenario?view=walkthrough',
    label: 'Guided story',
    icon: BookOpen,
  },
  { href: '/delivery', label: 'Delivery decisions', icon: Layers3 },
  { href: '/research', label: 'Research observatory', icon: FlaskConical },
  { href: '/evidence', label: 'Evidence register', icon: Database },
  { href: '/pressure', label: 'Market pressure', icon: Activity },
  { href: '/scenario', label: 'Scenario lab', icon: Gauge },
  { href: '/construction', label: 'Construction demand', icon: Layers3 },
  {
    href: '/historical-analog',
    label: 'Historical comparison',
    icon: BookOpen,
  },
  { href: '/methods', label: 'Methods', icon: BookOpen },
  { href: '/digest', label: 'Evidence digest', icon: FileText },
  { href: '/downloads', label: 'Downloads', icon: Download },
  { href: '/status', label: 'System status', icon: ShieldCheck },
];

export function ResearchNavigation() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Research navigation"
      className="flex gap-1 overflow-x-auto lg:flex-col"
    >
      {navigation.map(({ href, label, icon: Icon }) => (
        <Link
          aria-current={pathname === href.split('?')[0] ? 'page' : undefined}
          className={`flex shrink-0 items-center gap-3 rounded-md px-3 py-3 text-[13px] ${pathname === href.split('?')[0] ? 'bg-rail-active font-medium text-white' : 'text-white/75 hover:bg-rail-active hover:text-white'}`}
          href={href}
          key={href}
        >
          <Icon className="size-4 shrink-0" />
          {label}
        </Link>
      ))}
    </nav>
  );
}

export function DesktopNavigation() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Primary navigation"
      className="hidden gap-1 text-xs xl:flex"
    >
      {navigation.slice(1, 6).map(({ href, label }) => (
        <Link
          aria-current={pathname === href.split('?')[0] ? 'page' : undefined}
          className={`rounded-md px-3 py-2 ${pathname === href.split('?')[0] ? 'bg-brand-soft text-brand' : 'text-subtle hover:bg-workspace'}`}
          href={href}
          key={href}
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}

export function MobileNavigation() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        aria-label="Open site navigation"
        className="inline-flex size-10 items-center justify-center rounded-md border border-line bg-surface text-ink"
      >
        <Menu className="size-4" />
      </SheetTrigger>
      <SheetContent
        side="right"
        className="gap-0 border-line bg-surface text-ink"
      >
        <SheetHeader className="border-b border-line px-6 py-6 pr-12">
          <SheetTitle>AIIO Canada</SheetTitle>
          <SheetDescription>
            Decision tools and the public research record.
          </SheetDescription>
        </SheetHeader>
        <nav
          aria-label="Mobile primary navigation"
          className="min-h-0 flex-1 space-y-1 overflow-y-auto p-3"
        >
          {navigation.map(({ href, label, icon: Icon }) => (
            <Link
              aria-current={
                pathname === href.split('?')[0] ? 'page' : undefined
              }
              className={`flex items-center gap-3 rounded-md px-3 py-3 text-sm ${pathname === href.split('?')[0] ? 'bg-brand-soft font-medium text-brand' : 'text-subtle hover:bg-workspace'}`}
              href={href}
              key={href}
              onClick={() => setOpen(false)}
            >
              <Icon className="size-4 shrink-0" />
              {label}
            </Link>
          ))}
        </nav>
        <p className="border-t border-line p-5 text-xs leading-5 text-subtle">
          Observed ≠ inferred ≠ assumed ≠ scenario
        </p>
      </SheetContent>
    </Sheet>
  );
}
