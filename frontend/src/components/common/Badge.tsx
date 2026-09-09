import type { ReactNode } from 'react'
import { cls } from '../../utils/format'

const tones = {
  green: 'badge-green',
  amber: 'badge-amber',
  red: 'badge-red',
  blue: 'badge-blue',
  slate: 'badge-slate',
} as const

export default function Badge({
  tone = 'slate',
  children,
  className,
  dot,
}: {
  tone?: keyof typeof tones
  children: ReactNode
  className?: string
  dot?: boolean
}) {
  return (
    <span className={cls(tones[tone], className)}>
      {dot && (
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />
      )}
      {children}
    </span>
  )
}