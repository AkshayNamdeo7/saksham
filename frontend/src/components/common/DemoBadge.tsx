import { ShieldAlert } from 'lucide-react'

export default function DemoBadge({ subtle }: { subtle?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full text-xs font-medium ${
        subtle
          ? 'bg-amber-50 px-2.5 py-1 text-amber-700'
          : 'bg-amber-100 px-3 py-1.5 text-amber-800'
      }`}
    >
      <ShieldAlert className="h-3.5 w-3.5" aria-hidden />
      Prototype / Demo Data
    </span>
  )
}