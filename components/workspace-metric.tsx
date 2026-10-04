/** A shared readout for comparable figures in decision tools. */
export function WorkspaceMetric({
  label,
  value,
  emphasized = false,
}: {
  label: string;
  value: string;
  emphasized?: boolean;
}) {
  return (
    <dl
      className={`min-w-0 rounded-lg border p-4 ${emphasized ? 'border-brand/25 bg-brand-soft' : 'border-line bg-surface'}`}
    >
      <dt className="text-xs leading-5 text-subtle">{label}</dt>
      <dd
        className={`mt-2 break-words text-[26px] font-semibold tracking-tight tabular-nums ${emphasized ? 'text-brand' : 'text-ink'}`}
      >
        {value}
      </dd>
    </dl>
  );
}
