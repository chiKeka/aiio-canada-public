'use client';

import { useState } from 'react';

export function BriefingDownload() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function download() {
    setBusy(true);
    setError('');
    try {
      const response = await fetch('/api/briefing');
      if (!response.ok)
        throw new Error(
          'The briefing could not be generated. Please try again or review the published evidence.',
        );
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `Alberta_Delivery_Briefing_${response.headers.get('X-Evidence-As-Of') || 'evidence'}.pptx`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : 'Download failed. Please try again.',
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="space-y-2">
      <button
        type="button"
        disabled={busy}
        onClick={download}
        className="rounded-md bg-brand px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {busy ? 'Preparing PowerPoint…' : 'Download Alberta briefing (.pptx)'}
      </button>
      <output className="block text-xs text-subtle">
        {busy
          ? 'Building slides from published evidence…'
          : 'Published evidence, source notes and delivery priorities. Scenario inputs are exported separately.'}
      </output>
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}
