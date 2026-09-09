export default function LoadingState({
  message = 'Loading…',
  rows = 3,
}: {
  message?: string
  rows?: number
}) {
  return (
    <div className="space-y-3 py-8" role="status" aria-live="polite">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-24 animate-pulse rounded-xl bg-slate-200/70"
          style={{ animationDelay: `${i * 120}ms` }}
        />
      ))}
      <div className="flex items-center justify-center gap-2 pt-2 text-sm text-slate-400">
        <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
        {message}
      </div>
    </div>
  )
}