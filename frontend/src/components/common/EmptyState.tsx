import type { ReactNode } from 'react'
import { Inbox } from 'lucide-react'

export default function EmptyState({
  message,
  icon,
  children,
}: {
  message: string
  icon?: ReactNode
  children?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-14 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
        {icon || <Inbox className="h-6 w-6" aria-hidden />}
      </span>
      <p className="max-w-sm text-sm text-slate-500">{message}</p>
      {children}
    </div>
  )
}