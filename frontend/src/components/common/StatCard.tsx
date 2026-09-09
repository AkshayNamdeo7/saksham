import type { LucideIcon } from 'lucide-react'
import { cls } from '../../utils/format'

export default function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  tone = 'blue',
}: {
  icon: LucideIcon
  label: string
  value: string | number
  sub?: string
  tone?: 'blue' | 'green' | 'amber' | 'red'
}) {
  const tones = {
    blue: 'bg-brand-50 text-brand-700',
    green: 'bg-emerald-50 text-emerald-700',
    amber: 'bg-amber-50 text-amber-700',
    red: 'bg-red-50 text-red-600',
  }
  return (
    <div className="card flex items-start gap-4 p-5">
      <span className={cls('flex h-11 w-11 shrink-0 items-center justify-center rounded-xl', tones[tone])}>
        <Icon className="h-5 w-5" aria-hidden />
      </span>
      <div className="min-w-0">
        <p className="text-sm text-slate-500">{label}</p>
        <p className="tnum mt-0.5 truncate text-xl font-bold text-slate-900">{value}</p>
        {sub && <p className="mt-0.5 text-xs text-slate-400">{sub}</p>}
      </div>
    </div>
  )
}