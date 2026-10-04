/* oxlint-disable jsx-a11y/no-noninteractive-tabindex -- This component is a keyboard-scrollable region (WCAG 2.1.1). */
import { cn } from '@/lib/utils';

/** Allows keyboard users to pan a wide table without widening the page. */
export function WorkspaceScrollRegion({
  label,
  children,
  className,
  live,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
  live?: 'polite';
}) {
  return (
    <section
      aria-label={label}
      aria-live={live}
      tabIndex={0}
      className={cn('relative overflow-x-auto', className)}
    >
      {children}
    </section>
  );
}
