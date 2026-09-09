import { useTranslation } from 'react-i18next'
import { CheckCircle2, Info, TriangleAlert, XCircle } from 'lucide-react'
import type { RecommendationResult } from '../../types'
import Badge from '../common/Badge'

const STATUS_META = {
  eligible: { tone: 'green' as const, icon: CheckCircle2 },
  conditional: { tone: 'amber' as const, icon: Info },
  not_eligible: { tone: 'red' as const, icon: XCircle },
}

export default function RecommendationCard({
  result,
  rank,
  onSelect,
}: {
  result: RecommendationResult
  rank: number
  onSelect?: (id: number) => void
}) {
  const { t } = useTranslation()
  const meta = STATUS_META[result.eligibility_status]
  const Icon = meta.icon

  return (
    <article
      className={`card relative p-6 ${rank === 1 ? 'ring-2 ring-brand-600' : ''}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {rank === 1 && <Badge tone="blue">★ {t('recommendation.bestMatch')}</Badge>}
          <h3 className="text-lg font-bold text-slate-900">{result.scheme_name}</h3>
        </div>
        <Badge tone={meta.tone} dot>
          {t(`status.${result.eligibility_status}`)} · {result.match_score}%
        </Badge>
      </div>

      <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_auto]">
        <div className="space-y-4">
          {result.reasons.length > 0 && (
            <div>
              <p className="text-sm font-semibold text-slate-700">{t('recommendation.why')}</p>
              <ul className="mt-2 space-y-1.5">
                {result.reasons.slice(0, 4).map((r) => (
                  <li key={r} className="flex items-start gap-2 text-sm text-slate-600">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(result.warnings.length > 0 || result.unmatched.length > 0) && (
            <div className="space-y-2 rounded-xl bg-slate-50 p-3">
              {result.warnings.map((w) => (
                <p key={w} className="flex items-start gap-2 text-sm text-amber-700">
                  <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                  {w}
                </p>
              ))}
              {result.unmatched.map((u) => (
                <p key={u} className="flex items-start gap-2 text-sm text-red-600">
                  <XCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                  {u}
                </p>
              ))}
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-col gap-2 lg:w-40">
          <div>
            <p className="text-[11px] uppercase tracking-wide text-slate-400">
              {t('recommendation.maxLoan')}
            </p>
            <p className="tnum text-lg font-bold text-navy">
              ₹{result.max_loan.toLocaleString('en-IN')}
            </p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wide text-slate-400">
              {t('recommendation.interest')}
            </p>
            <p className="tnum font-semibold text-slate-800">{result.interest_rate}% p.a.</p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wide text-slate-400">
              {t('recommendation.tenure')}
            </p>
            <p className="tnum font-semibold text-slate-800">{result.tenure_months} months</p>
          </div>
        </div>
      </div>
    </article>
  )
}