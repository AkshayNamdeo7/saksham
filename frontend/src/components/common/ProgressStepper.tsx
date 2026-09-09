import { Check } from 'lucide-react'
import { cls } from '../../utils/format'

export default function ProgressStepper({
  steps,
  current,
}: {
  steps: string[]
  current: number
}) {
  return (
    <ol className="flex items-center" aria-label="Progress">
      {steps.map((label, i) => {
        const done = i < current
        const active = i === current
        return (
          <li
            key={label}
            className={cls('flex items-center', i < steps.length - 1 && 'flex-1')}
          >
            <div className="flex flex-col items-center gap-1.5">
              <span
                className={cls(
                  'flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-bold transition',
                  done && 'border-emerald-500 bg-emerald-500 text-white',
                  active && 'border-brand-700 bg-white text-brand-700 ring-4 ring-brand-100',
                  !done && !active && 'border-slate-300 bg-white text-slate-400',
                )}
                aria-current={active ? 'step' : undefined}
              >
                {done ? <Check className="h-4 w-4" /> : i + 1}
              </span>
              <span
                className={cls(
                  'hidden max-w-[72px] text-center text-[10px] font-medium leading-tight sm:block',
                  active ? 'text-brand-800' : 'text-slate-400',
                )}
              >
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <span
                className={cls(
                  'mx-1 h-0.5 flex-1 rounded sm:mx-2',
                  i < current ? 'bg-emerald-500' : 'bg-slate-200',
                )}
                style={{ minWidth: 8 }}
              />
            )}
          </li>
        )
      })}
    </ol>
  )
}