import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { ArrowRight, CheckSquare, Square } from 'lucide-react'
import type { Scheme } from '../../types'
import { formatLakh, formatPercent, tenureLabel, cls } from '../../utils/format'
import Badge from '../common/Badge'

export default function SchemeCard({
  scheme,
  compare,
  onCompare,
}: {
  scheme: Scheme
  compare?: boolean
  onCompare?: (id: number) => void
}) {
  const { t } = useTranslation()

  const categoryLabel = {
    micro_finance: t('home.catMicro'),
    term_loan: t('home.catTerm'),
    education: t('home.catEdu'),
  }[scheme.category]

  const purposeLabel = {
    business: t('eligibility.purposeBusiness'),
    self_employment: t('eligibility.purposeSelf'),
    education: t('eligibility.purposeEducation'),
  }[scheme.purpose]

  return (
    <div className="card flex flex-col p-5 transition hover:border-brand-300 hover:shadow-elevated">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-base font-bold leading-snug text-slate-900">
          {scheme.name}
        </h3>
        {compare !== undefined && (
          <button
            onClick={() => onCompare?.(scheme.id)}
            aria-pressed={compare}
            aria-label={`${compare ? 'Remove from' : 'Add to'} comparison: ${scheme.name}`}
            className={cls(
              'focus-ring shrink-0 rounded-lg p-1.5',
              compare ? 'bg-brand-100 text-brand-800' : 'text-slate-400 hover:text-slate-700',
            )}
          >
            {compare ? <CheckSquare className="h-5 w-5" /> : <Square className="h-5 w-5" />}
          </button>
        )}
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5">
        <Badge tone="blue">{categoryLabel}</Badge>
        <Badge tone="slate">{purposeLabel}</Badge>
        {scheme.is_demo && <Badge tone="amber">{t('common.demo')}</Badge>}
      </div>
      <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-slate-500">
        {scheme.description}
      </p>

      <dl className="mt-4 grid grid-cols-3 gap-2 border-t border-slate-100 pt-4 text-sm">
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-slate-400">
            {t('schemes.maxLoan')}
          </dt>
          <dd className="tnum mt-0.5 font-bold text-navy">{formatLakh(scheme.max_loan)}</dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-slate-400">
            {t('schemes.interest')}
          </dt>
          <dd className="mt-0.5 font-bold text-slate-800">
            {formatPercent(scheme.interest_rate)}
          </dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-slate-400">
            {t('schemes.tenure')}
          </dt>
          <dd className="mt-0.5 font-bold text-slate-800">
            {tenureLabel(scheme.tenure_months)}
          </dd>
        </div>
      </dl>

      <div className="mt-auto flex items-center justify-between gap-2 pt-4">
        <Link
          to={`/schemes/${scheme.id}`}
          className="focus-ring inline-flex items-center gap-1 rounded-lg text-sm font-semibold text-brand-700 hover:text-brand-900"
        >
          {t('schemes.viewDetails')}
          <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
      </div>
    </div>
  )
}