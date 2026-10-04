import Link from 'next/link';
import { ResearchShell } from '@/components/site-shell';

export default function NotFound() {
  return (
    <ResearchShell>
      <div className="grid min-h-[65dvh] place-items-center px-5 py-10">
        <section className="max-w-lg text-center">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-brand">
            404 · Page not found
          </p>
          <h1 className="mt-4 text-2xl font-medium">
            That route does not exist.
          </h1>
          <p className="mt-3 text-sm text-subtle">
            Return to the executive dashboard or open the public evidence
            record.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              className="rounded-md bg-brand px-5 py-2.5 text-sm font-medium text-white"
              href="/"
            >
              Dashboard
            </Link>
            <Link
              className="rounded-md border border-line px-5 py-2.5 text-sm"
              href="/evidence"
            >
              Evidence
            </Link>
          </div>
        </section>
      </div>
    </ResearchShell>
  );
}
