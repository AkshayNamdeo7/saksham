import { cls } from '../../utils/format'

export default function LoadingScreen({ full = true }: { full?: boolean }) {
  return (
    <div
      className={cls(
        'flex items-center justify-center',
        full && 'min-h-[60vh]',
      )}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-3 text-slate-500">
        <span className="inline-block h-6 w-6 animate-spin rounded-full border-[3px] border-brand-200 border-t-brand-700" />
        <span className="text-sm">
          <img src="/logo1.jpeg" alt="Saksham logo" className="mr-2 inline h-6 w-6 rounded-md object-contain align-middle" />
          <span className="font-semibold text-brand-800">Saksham</span>
          <span className="ml-2">loading…</span>
        </span>
      </div>
    </div>
  )
}