import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import {
  CheckCircle2,
  FileText,
  Navigation,
  Download,
} from 'lucide-react'
import { api } from '../services/api'
import type { ScoredPartner, Scheme } from '../types'
import { useProfile } from '../context/ProfileContext'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import Badge from '../components/common/Badge'
import DemoBadge from '../components/common/DemoBadge'
import { formatINR } from '../utils/format'
import { formatInterest } from '../utils/format'

export default function Application() {
  const { t } = useTranslation()
  const { profile, selectedScheme, loanRequired, setSelectedSchemeData, setLoanRequired } = useProfile()

  const [scheme, setScheme] = useState<Scheme | null>(selectedScheme)
  const [top, setTop] = useState<ScoredPartner | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!scheme) return
    setLoading(true)
    setError(null)
    api.partnersRecommend
      .recommend({
        state: profile?.state,
        district: profile?.district,
        latitude: undefined,
        longitude: undefined,
        scheme_id: scheme.id,
        purpose: scheme.purpose,
        loan_amount: loanRequired ?? undefined,
        limit: 1,
      })
      .then((res) => setTop(res.results[0] || null))
      .catch((e) => setError(e instanceof Error ? e.message : 'Routing failed'))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scheme?.id])

  function downloadSummary() {
    if (!scheme) return
    const lines = [
      'SAKSHAM — Recommendation Summary (Prototype/Demo)',
      '-----------------------------------------------',
      `Scheme: ${scheme.name}`,
      `Category: ${scheme.category} | Purpose: ${scheme.purpose}`,
      `Max loan: ${formatINR(scheme.max_loan)}`,
      `Interest: ${formatInterest(scheme.interest_rate, scheme.interest_display, scheme.interest_rate_type)}`,
      `Tenure: ${scheme.tenure_months} months`,
      `Loan required: ${loanRequired ? formatINR(loanRequired) : '—'}`,
      '',
      'Recommended channel partner:',
      top ? `- ${top.name} (${top.type}, ${top.city}, ${top.state})` : '- pending',
      top ? `- Routing score: ${top.total_score}/100` : '',
      '',
      'Official Verification Required:',
      'This is prototype data for demonstration. Verify all figures against official scheme guidelines before applying.',
    ]
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'saksham-recommendation-summary.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="container-app max-w-4xl py-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('application.title')}</h1>
        <p className="mt-2 text-slate-500">{t('application.subtitle')}</p>
      </div>
      <div className="mt-2 flex justify-center"><DemoBadge subtle /></div>

      {!scheme && (
        <div className="card mt-10 flex flex-col items-center gap-4 p-10 text-center">
          <p className="text-slate-500">First get a recommendation to build your application path.</p>
          <Link to="/eligibility" className="btn-primary">{t('eligibility.start')}</Link>
        </div>
      )}

      {scheme && (
        <div className="mt-10 space-y-5">
          {loading && <LoadingState rows={3} />}
          {error && !loading && <ErrorState message={error} />}

          {/* Step 1: scheme */}
          <div className="card p-6">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">1</span>
              <h2 className="text-base font-bold text-slate-900">{t('application.selectedScheme')}</h2>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 p-4">
              <div>
                <p className="text-lg font-bold text-navy">{scheme.name}</p>
                <p className="text-xs text-slate-500">{scheme.category} · {scheme.purpose}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Link to={`/schemes/${scheme.id}`} className="btn-secondary text-xs">Details</Link>
                <Link to={`/calculator?scheme=${scheme.id}`} className="btn-secondary text-xs">EMI</Link>
                {scheme.official_scheme_url || scheme.source_url ? (
                  <a
                    href={scheme.official_scheme_url || scheme.source_url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary text-xs"
                  >
                    Official source
                  </a>
                ) : null}
              </div>
            </div>
            {!scheme.official_apply_url && !scheme.application_mode && (
              <p className="mt-3 text-xs text-amber-700">
                Application route should be verified with the official source/channelizing agency.
              </p>
            )}
          </div>

          {/* Step 2: requirement */}
          <div className="card p-6">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">2</span>
              <h2 className="text-base font-bold text-slate-900">{t('application.requirement')}</h2>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-[11px] uppercase tracking-wide text-slate-400">Loan required</p>
                <p className="tnum mt-1 text-lg font-bold text-slate-900">
                  {loanRequired ? formatINR(loanRequired) : formatINR(scheme.max_loan)}
                </p>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-[11px] uppercase tracking-wide text-slate-400">Interest</p>
                <p className="tnum mt-1 text-sm font-bold leading-snug text-slate-900">
                  {formatInterest(scheme.interest_rate, scheme.interest_display, scheme.interest_rate_type)}
                </p>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-[11px] uppercase tracking-wide text-slate-400">Purpose</p>
                <p className="tnum mt-1 text-lg font-bold text-slate-900 capitalize">{scheme.purpose}</p>
              </div>
            </div>
          </div>

          {/* Step 3: partner */}
          <div className="card p-6">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">3</span>
              <h2 className="text-base font-bold text-slate-900">{t('application.partner')}</h2>
            </div>
            {top ? (
              <div className="mt-4 rounded-xl border border-brand-200 bg-brand-50/50 p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-bold text-slate-900">★ {top.name}</p>
                    <p className="mt-0.5 text-sm text-slate-500">
                      {top.type} · {top.city}, {top.district}, {top.state}
                    </p>
                    <p className="mt-1 text-sm text-slate-500">{top.address}</p>
                    <p className="mt-1 text-sm text-slate-500">📞 {top.phone}</p>
                  </div>
                  <Badge tone="green" dot>{top.total_score}/100 {t('partners.score')}</Badge>
                </div>
                <ul className="mt-3 space-y-1">
                  {top.notes.map((n) => (
                    <li key={n} className="flex items-start gap-2 text-sm text-slate-600">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden />
                      {n}
                    </li>
                  ))}
                </ul>
                <div className="mt-4 flex flex-wrap gap-2">
                  <a
                    href={`https://www.google.com/maps/dir/?api=1&destination=${top.latitude},${top.longitude}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary text-xs"
                  >
                    <Navigation className="h-4 w-4" aria-hidden />
                    {t('application.getDirections')}
                  </a>
                  <a href={`tel:${top.phone}`} className="btn-secondary text-xs">
                    Call
                  </a>
                </div>
              </div>
            ) : (
              !loading && <p className="mt-4 text-sm text-slate-400">No partner determined for this demo scenario.</p>
            )}
          </div>

          {/* Step 4: docs */}
          <div className="card p-6">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">4</span>
              <h2 className="text-base font-bold text-slate-900">{t('application.docs')}</h2>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {(scheme as any).document_keys?.length ? (
                (scheme as any).document_keys.map((k: string) => (
                  <span key={k} className="badge-slate">{k.replace(/_/g, ' ')}</span>
                ))
              ) : (
                <p className="text-sm text-slate-500">Aadhaar, caste certificate, income certificate, bank details, project report (demo).</p>
              )}
            </div>
            <div className="mt-3">
              <Link to="/documents" className="btn-ghost text-xs">
                <FileText className="h-3.5 w-3.5" aria-hidden />
                View document checklist
              </Link>
            </div>
          </div>

          {/* Step 5: next */}
          <div className="card p-6">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">5</span>
              <h2 className="text-base font-bold text-slate-900">{t('application.nextStep')}</h2>
            </div>
            <div className="mt-4 space-y-2">
              {[
                'Confirm the details with the recommended partner.',
                'Carry the scheme document checklist.',
                'Submit the application and track processing.',
              ].map((s) => (
                <p key={s} className="flex items-start gap-2 text-sm text-slate-600">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden />
                  {s}
                </p>
              ))}
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <button onClick={downloadSummary} className="btn-primary text-xs">
                <Download className="h-4 w-4" aria-hidden />
                {t('application.downloadSummary')}
              </button>
            </div>
            <p className="mt-4 text-xs text-amber-700">{t('common.demoNotice')}</p>
          </div>

          {/* Timeline */}
          <div className="card p-6">
            <h2 className="text-sm font-semibold text-slate-700">Journey timeline</h2>
            <div className="mt-4 flex items-center gap-1 overflow-x-auto">
              {['Profile', 'Scheme', 'Finance', 'Partner'].map((s, i) => (
                <div key={s} className="flex items-center gap-1">
                  <span className="flex items-center gap-1.5 whitespace-nowrap rounded-full bg-emerald-100 px-3 py-1.5 text-xs font-medium text-emerald-800">
                    <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
                    {s}
                  </span>
                  {i < 3 && <span className="h-0.5 w-5 bg-slate-300" />}
                </div>
              ))}
              <span className="flex items-center gap-1.5 whitespace-nowrap rounded-full bg-amber-100 px-3 py-1.5 text-xs font-medium text-amber-800">
                Next step
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}