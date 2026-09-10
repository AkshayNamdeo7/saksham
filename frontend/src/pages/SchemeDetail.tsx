import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  ArrowLeft,
  Calculator as CalcIcon,
  CheckCircle2,
  ExternalLink,
  FileText,
  HelpCircle,
  Landmark,
  MapPin,
  ShieldCheck,
  Wallet,
} from 'lucide-react'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import Badge from '../components/common/Badge'
import DemoBadge from '../components/common/DemoBadge'
import { formatLakh, formatPercent, tenureLabel } from '../utils/format'

export default function SchemeDetail() {
  const { id } = useParams()
  const { t } = useTranslation()
  const { data, loading, error, reload } = useFetch(
    () => api.schemes.get(Number(id)),
    [id],
  )
  const { data: docs } = useFetch(
    () => (id ? api.schemes.documents(Number(id)) : Promise.resolve([])),
    [id],
  )

  if (loading) return <div className="container-app py-12"><LoadingState rows={4} /></div>
  if (error) return (
    <div className="container-app py-12">
      <ErrorState message={error} onRetry={reload} />
    </div>
  )
  if (!data) return null

  const scheme = data

  const steps = [
    'Complete the eligibility check',
    'Prepare the scheme-specific documents',
    'Visit the recommended channel partner',
    'Submit the application with supporting documents',
    'Track processing and verification with the partner',
  ]

  return (
    <div className="container-app max-w-4xl py-12">
      <Link to="/schemes" className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-700 hover:text-brand-900">
        <ArrowLeft className="h-4 w-4" aria-hidden />
        {t('schemeDetail.back')}
      </Link>

      <div className="mt-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap gap-2">
            <Badge tone="blue">{scheme.category.replace(/_/g, ' ')}</Badge>
            <Badge tone="slate">{scheme.purpose.replace(/_/g, ' ')}</Badge>
            {scheme.verification_status === 'verified' && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden />
                {scheme.source_name || 'Verified source'}
                {scheme.last_verified && <span className="text-emerald-500"> · {scheme.last_verified}</span>}
              </span>
            )}
            {scheme.is_demo && <DemoBadge subtle />}
          </div>
          <h1 className="mt-3 text-2xl font-bold text-slate-900 sm:text-3xl">{scheme.name}</h1>
          <p className="mt-2 max-w-2xl text-slate-500">{scheme.description}</p>
        </div>
        <div className="flex flex-col gap-2">
          {(scheme.official_scheme_url || scheme.source_url) && (
            <a
              href={scheme.official_scheme_url || scheme.source_url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary flex items-center gap-1.5 text-sm"
            >
              <ExternalLink className="h-4 w-4" aria-hidden />
              View Official Scheme
            </a>
          )}
          {scheme.official_apply_url ? (
            <a
              href={scheme.official_apply_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700"
            >
              <ExternalLink className="h-4 w-4" aria-hidden />
              Apply on Official Portal
            </a>
          ) : null}
          <Link to={`/calculator?scheme=${scheme.id}`} className="btn-secondary text-sm">
            <CalcIcon className="h-4 w-4" aria-hidden />
            {t('schemeDetail.calcEmi')}
          </Link>
          <Link to={`/partners?scheme=${scheme.id}`} className="btn-primary text-sm">
            <MapPin className="h-4 w-4" aria-hidden />
            {t('schemeDetail.findPartner')}
          </Link>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
        ⚠️ {t('common.officialVerify')} — {t('common.demoNotice')}
      </div>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { icon: Wallet, label: t('schemeDetail.financing'), value: formatLakh(scheme.max_loan) },
          { icon: Landmark, label: t('schemeDetail.interest'), value: `${formatPercent(scheme.interest_rate)} p.a.` },
          { icon: CheckCircle2, label: t('schemeDetail.tenure'), value: tenureLabel(scheme.tenure_months) },
          { icon: HelpCircle, label: t('schemeDetail.moratorium'), value: tenureLabel(scheme.moratorium_months) },
        ].map((x) => (
          <div key={x.label} className="card p-5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
              <x.icon className="h-4.5 w-4.5" aria-hidden />
            </span>
            <p className="mt-3 text-[11px] uppercase tracking-wide text-slate-400">{x.label}</p>
            <p className="tnum mt-0.5 text-lg font-bold text-slate-900">{x.value}</p>
          </div>
        ))}
      </section>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="card p-6">
          <h2 className="text-base font-bold text-slate-900">{t('schemeDetail.overview')}</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{scheme.description}</p>

          <h2 className="mt-6 text-base font-bold text-slate-900">{t('schemeDetail.eligibility')}</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{scheme.eligibility_notes}</p>

          {scheme.income_threshold && (
            <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
              Demo income threshold: <span className="tnum font-semibold text-slate-800">₹{scheme.income_threshold.toLocaleString('en-IN')}</span>
            </p>
          )}

          {scheme.project_min !== null && scheme.project_max !== null && (
            <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
              Demo project band: <span className="tnum font-semibold text-slate-800">{formatLakh(scheme.project_min)} – {formatLakh(scheme.project_max)}</span>
            </p>
          )}

          <h2 className="mt-6 text-base font-bold text-slate-900">{t('schemeDetail.partnerReq')}</h2>
          <p className="mt-2 text-sm text-slate-600">
            {scheme.partner_required
              ? 'A channel partner is normally required to process this loan (demo).'
              : 'No channel partner required for this demo scheme.'}
          </p>
        </section>

        <section className="card p-6">
          <h2 className="text-base font-bold text-slate-900">{t('schemeDetail.documents')}</h2>
          <ul className="mt-3 space-y-2">
            {(docs || []).map((d) => (
              <li key={d.key} className="flex items-start gap-2.5 text-sm">
                <span className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${d.is_required ? 'bg-brand-100 text-brand-800' : 'bg-slate-100 text-slate-500'}`}>
                  {d.is_required ? <CheckCircle2 className="h-3.5 w-3.5" /> : <FileText className="h-3.5 w-3.5" />}
                </span>
                <div>
                  <p className="font-medium text-slate-800">{d.name}</p>
                  {!d.is_required && <span className="text-xs text-slate-400">{t('documents.optional')}</span>}
                </div>
              </li>
            ))}
          </ul>

          <h2 className="mt-6 text-base font-bold text-slate-900">{t('schemeDetail.steps')}</h2>
          <ol className="mt-3 space-y-2">
            {steps.map((s, i) => (
              <li key={s} className="flex items-start gap-2.5 text-sm text-slate-600">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-[11px] font-bold text-emerald-800">{i + 1}</span>
                {s}
              </li>
            ))}
          </ol>
        </section>
      </div>

      {scheme.supported_partners && scheme.supported_partners.length > 0 && (
        <section className="card mt-6 p-6">
          <h2 className="text-base font-bold text-slate-900">Demo channel partners</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {scheme.supported_partners.slice(0, 6).map((p) => (
              <span key={p.id} className="badge-slate">{p.name}</span>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}