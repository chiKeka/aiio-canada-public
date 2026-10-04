'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export function ConstructionLiveUpdate({ revision }: { revision: string }) {
  const router = useRouter();
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    let active = true,
      pending = false;
    const controller = new AbortController();
    async function check() {
      if (document.visibilityState !== 'visible' || pending) return;
      pending = true;
      try {
        const response = await fetch('/api/construction/revision', {
          cache: 'no-store',
          signal: controller.signal,
        });
        if (!response.ok) throw new Error('Unavailable');
        const next = (await response.json()) as { revision?: unknown };
        if (typeof next.revision !== 'string')
          throw new Error('Invalid revision');
        if (active) {
          setUnavailable(false);
          if (next.revision !== revision) router.refresh();
        }
      } catch {
        if (active) setUnavailable(true);
      } finally {
        pending = false;
      }
    }
    const interval = setInterval(check, 60_000);
    window.addEventListener('focus', check);
    document.addEventListener('visibilitychange', check);
    void check();
    return () => {
      active = false;
      controller.abort();
      clearInterval(interval);
      window.removeEventListener('focus', check);
      document.removeEventListener('visibilitychange', check);
    };
  }, [revision, router]);
  return (
    <output className="block text-xs leading-5 text-subtle">
      {unavailable
        ? 'Update check unavailable. The displayed evidence remains the last loaded version; retrying automatically.'
        : 'This view checks for newly published evidence every minute while open and when you return to it.'}
    </output>
  );
}
