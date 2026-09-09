import { useTranslation } from 'react-i18next'
import { setAppLanguage } from '../../i18n'
import { cls } from '../../utils/format'

export default function LanguageSwitcher({ compact }: { compact?: boolean }) {
  const { i18n } = useTranslation()
  const current = i18n.language || 'en'

  return (
    <div
      role="group"
      aria-label="Language"
      className={cls(
        'flex rounded-lg border border-slate-200 bg-slate-50 p-0.5',
        compact ? '' : '',
      )}
    >
      {(['en', 'hi'] as const).map((lang) => (
        <button
          key={lang}
          onClick={() => setAppLanguage(lang)}
          aria-pressed={current.startsWith(lang)}
          className={cls(
            'focus-ring rounded-md px-2 py-1 text-xs font-semibold transition',
            current.startsWith(lang)
              ? 'bg-white text-brand-800 shadow-sm'
              : 'text-slate-500 hover:text-slate-800',
            compact ? 'px-2 py-1 text-[11px]' : 'px-2.5',
          )}
        >
          {lang === 'en' ? 'EN' : 'हिंदी'}
        </button>
      ))}
    </div>
  )
}