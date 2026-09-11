import { useTranslation } from 'react-i18next'
import { Languages } from 'lucide-react'
import { setAppLanguage } from '../../i18n'
import { cls } from '../../utils/format'

export default function LanguageSwitcher({ compact }: { compact?: boolean }) {
  const { i18n } = useTranslation()
  const current = i18n.language || 'en'

  const options = [
    { lang: 'en' as const, label: compact ? 'EN' : 'English' },
    { lang: 'hi' as const, label: compact ? 'हिंदी' : 'हिन्दी' },
  ]

  return (
    <div
      role="group"
      aria-label="Language"
      className="inline-flex h-9 items-center gap-1 rounded-lg border border-slate-200 bg-white p-1"
    >
      <Languages
        className={cls('ml-0.5 shrink-0 text-slate-400', compact ? 'h-3.5 w-3.5' : 'h-4 w-4')}
        aria-hidden
      />
      {options.map(({ lang, label }) => (
        <button
          key={lang}
          onClick={() => setAppLanguage(lang)}
          aria-pressed={current.startsWith(lang)}
          aria-label={`${label} language`}
          className={cls(
            'focus-ring inline-flex h-full items-center rounded-md font-semibold transition',
            current.startsWith(lang)
              ? 'bg-brand-700 text-white'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
            compact ? 'px-1.5 text-[11px]' : 'px-2.5 text-xs',
          )}
        >
          {label}
        </button>
      ))}
    </div>
  )
}