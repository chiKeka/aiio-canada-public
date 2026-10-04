'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { ResearchShell } from '@/components/site-shell';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('AIIO route failure', {
      digest: error.digest,
      message: error.message,
    });
  }, [error]);
  return (
    <ResearchShell>
      <div className="grid min-h-[65dvh] place-items-center px-5 py-10">
        <section className="max-w-lg rounded-lg border border-line bg-white p-8 text-center">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-brand">
            Temporary interruption
          </p>
          <h1 className="mt-4 text-2xl font-medium">
            This view could not be rendered.
          </h1>
          <p className="mt-3 text-sm leading-6 text-subtle">
            The evidence record has not been changed. Retry the view or check
            system status.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <button
              className="rounded-md bg-brand px-5 py-2.5 text-sm font-medium text-white"
              onClick={reset}
            >
              Try again
            </button>
            <Link
              className="rounded-md border border-line px-5 py-2.5 text-sm"
              href="/status"
            >
              System status
            </Link>
          </div>
        </section>
      </div>
    </ResearchShell>
  );
}
