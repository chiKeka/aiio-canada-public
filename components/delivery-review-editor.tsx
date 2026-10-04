'use client';
import { useState } from 'react';
import type { DeliveryRegister } from '@/lib/delivery-types';
import { validateDeliveryRegister } from '@/lib/alberta-delivery.mjs';
export function DeliveryReviewEditor({
  register,
}: {
  register: DeliveryRegister;
}) {
  const [draft, setDraft] = useState(register);
  const [message, setMessage] = useState(
    'Draft changes are not published or saved on this page. Export a review file to retain them.',
  );
  const [raw, setRaw] = useState(JSON.stringify(register, null, 2));
  function updateAction(
    index: number,
    key: 'owner' | 'due' | 'status' | 'evidence',
    value: string,
  ) {
    const next = {
      ...draft,
      actions: draft.actions.map((a, i) =>
        i === index ? { ...a, [key]: value || null } : a,
      ),
    };
    setDraft(next);
    setRaw(JSON.stringify(next, null, 2));
    setMessage('Unsaved review draft. Export to retain these changes.');
  }
  function exportDraft() {
    try {
      validateDeliveryRegister(draft);
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(draft, null, 2)], {
          type: 'application/json',
        }),
      );
      const a = document.createElement('a');
      a.href = url;
      a.download = 'alberta-delivery-review-draft.json';
      a.click();
      URL.revokeObjectURL(url);
      setMessage(
        'Validated review draft exported. Published records have not changed.',
      );
    } catch (e) {
      setMessage(e instanceof Error ? e.message : 'Invalid register');
    }
  }
  return (
    <details className="rounded-lg border border-line bg-surface p-5">
      <summary className="cursor-pointer text-lg font-semibold">
        Prepare a review update
      </summary>
      <p className="my-3 text-sm text-subtle">
        Assign owners and dates, attach evidence, or add sourced milestone,
        package, contractor and supplier records in the structured editor.
        Export the validated file for the existing review process.
      </p>
      <div className="space-y-4">
        {draft.actions.map((a, i) => (
          <fieldset key={a.id} className="rounded border border-line p-3">
            <legend className="px-1 text-sm font-semibold">
              {a.id} · {a.title}
            </legend>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-sm">
                Owner
                <input
                  className="mt-1 w-full rounded border border-line bg-surface p-2"
                  value={a.owner ?? ''}
                  onChange={(e) => updateAction(i, 'owner', e.target.value)}
                />
              </label>
              <label className="text-sm">
                Due date
                <input
                  type="date"
                  className="mt-1 w-full rounded border border-line bg-surface p-2"
                  value={a.due ?? ''}
                  onChange={(e) => updateAction(i, 'due', e.target.value)}
                />
              </label>
              <label className="text-sm">
                Status
                <select
                  className="mt-1 w-full rounded border border-line bg-surface p-2"
                  value={a.status}
                  onChange={(e) => updateAction(i, 'status', e.target.value)}
                >
                  {['open', 'in_progress', 'blocked', 'complete'].map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </label>
              <label className="text-sm">
                Supporting evidence
                <input
                  className="mt-1 w-full rounded border border-line bg-surface p-2"
                  value={a.evidence ?? ''}
                  onChange={(e) => updateAction(i, 'evidence', e.target.value)}
                />
              </label>
            </div>
          </fieldset>
        ))}
      </div>
      <details className="my-4">
        <summary className="cursor-pointer text-sm text-brand">
          Structured evidence editor
        </summary>
        <label className="text-sm">
          Delivery register JSON
          <textarea
            rows={14}
            className="mt-2 w-full rounded border border-line bg-surface p-3 font-mono text-xs"
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
          />
        </label>
        <button
          className="mt-2 rounded border border-line px-3 py-2 text-sm"
          onClick={() => {
            try {
              const parsed = JSON.parse(raw);
              validateDeliveryRegister(parsed);
              setDraft(parsed);
              setMessage(
                'Structured draft validated and applied to the editor. Export to retain it.',
              );
            } catch (e) {
              setMessage(e instanceof Error ? e.message : 'Invalid register');
            }
          }}
        >
          Validate and apply draft
        </button>
      </details>
      <button
        className="rounded bg-brand px-4 py-2 text-sm text-white"
        onClick={exportDraft}
      >
        Export validated review draft
      </button>
      <output aria-live="polite" className="mt-3 text-sm">
        {message}
      </output>
    </details>
  );
}
