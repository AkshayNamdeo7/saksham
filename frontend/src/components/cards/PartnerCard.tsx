import { useTranslation } from 'react-i18next'
import { CheckCircle2, Navigation, Phone } from 'lucide-react'
import type { ScoredPartner } from '../../types'
import Badge from '../common/Badge'
import { cls } from '../../utils/format'

const STATUS_LABEL: Record<string, string> = {
  accepting: 'Accepting',
  limited: 'Limited',
  unavailable: 'Unavailable',
}

export default function PartnerCard({
  partner,
  recommended,
  onDirections,
  onSelect,
}: {
  partner: ScoredPartner
  recommended?: boolean
  onDirections?: (p: ScoredPartner) => void
  onSelect?: (p: ScoredPartner) => void
}) {
  const { t } = useTranslation()

  const tone =
    partner.status === 'accepting'
      ? 'green'
      : partner.status === 'limited'
        ? 'amber'
        : 'red'

  return (
    <article
      className={cls(
        'card cursor-pointer p-4 transition hover:border-brand-300 hover:shadow-elevated',
        recommended && 'border-brand-400 ring-1 ring-brand-400 bg-brand-50/40',
      )}
      onClick={() => onSelect?.(partner)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-bold text-slate-900">
            {recommended && '★ '}
            {partner.name}
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">
            {partner.type} · {partner.city}, {partner.state}
          </p>
        </div>
        <Badge tone={tone} dot>
          {STATUS_LABEL[partner.status]}
        </Badge>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
        {partner.distance_km !== null && (
          <span>📍 {partner.distance_km.toFixed(1)} km</span>
        )}
        <span className="inline-flex items-center gap-1 font-semibold text-brand-800">
          <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
          {partner.total_score}/100 {t('partners.score')}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {(partner.supported_schemes || []).slice(0, 2).map((s) => (
          <span key={s.id} className="badge-slate max-w-full truncate">
            {s.name}
          </span>
        ))}
      </div>

      <div className="mt-3 flex gap-2">
        {partner.phone && (
          <a
            href={`tel:${partner.phone}`}
            onClick={(e) => e.stopPropagation()}
            className="focus-ring inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            <Phone className="h-3.5 w-3.5" aria-hidden />
            Call
          </a>
        )}
        {onDirections && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDirections(partner)
            }}
            className="focus-ring inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-brand-200 px-3 py-1.5 text-xs font-medium text-brand-700 hover:bg-brand-50"
          >
            <Navigation className="h-3.5 w-3.5" aria-hidden />
            {t('partners.directions')}
          </button>
        )}
      </div>
    </article>
  )
}