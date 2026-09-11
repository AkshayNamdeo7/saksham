import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation } from 'react-router-dom'
import {
  ArrowRight,
  Calculator as CalcIcon,
  FileText,
  Landmark,
  MapPin,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react'
import { api } from '../services/api'
import { useProfile } from '../context/ProfileContext'
import type { Profile, RecommendationResult } from '../types'
import RecommendationCard from '../components/cards/RecommendationCard'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import Badge from '../components/common/Badge'
import { formatLakh, formatInterest } from '../utils/format'

export default function Recommendation() {
  const { t } = useTranslation()
  const location = useLocation()
  const { profile, recommendations, setRecommendationsData, setSelectedSchemeData, setLoanRequired } = useProfile()

  const incoming = (location.state as { profile?: Profile } | null)?.profile

  const [results, setResults] = useState<RecommendationResult[] | null>(
    recommendations ||
      (location.state as { results?: RecommendationResult[] } | null)?.results ||
      null,
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const profileData = incoming || profile

  async function run() {
    if (!profileData) {
      setError('No profile found. Please complete the eligibility check first.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await api.recommendations.get(profileData)
      setResults(res.results)
      setRecommendationsData(res.results)
      if (res.results?.[0]) {
        setSelectedSchemeData({
          id: res.results[0].scheme_id,
          name: res.results[0].scheme_name,
          slug: res.results[0].scheme_slug,
          description: '',
          category: res.results[0].category,
          purpose: res.results[0].purpose,
          max_loan: res.results[0].max_loan,
          min_loan: res.results[0].min_loan ?? 0,
          interest_rate: res.results[0].interest_rate,
          interest_rate_type: res.results[0].interest_rate_type,
          interest_tiers: res.results[0].interest_tiers,
          interest_display: res.results[0].interest_display,
          project_min: res.results[0].project_min ?? null,
          project_max: res.results[0].project_max ?? null,
          tenure_months: res.results[0].tenure_months,
          moratorium_months: res.results[0].moratorium_months,
          income_threshold: res.results[0].income_threshold,
          education_focus: res.results[0].purpose === 'education',
          eligibility_notes: '',
          required_documents: '',
          partner_required: true,
          active: true,
          is_demo: false,
          source_name: res.results[0].source_name,
          source_url: res.results[0].source_url,
          official_scheme_url: res.results[0].official_scheme_url,
          official_apply_url: res.results[0].official_apply_url,
          last_verified: res.results[0].last_verified,
          source_type: res.results[0].source_type,
          verification_status: res.results[0].verification_status,
          document_keys: [],
        } as any)
        setLoanRequired(
          profileData.requested_loan ??
            profileData.project_cost ??
            profileData.education_cost ??
            res.results[0].max_loan,
        )
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Recommendation failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // A fresh navigation from the eligibility form always recomputes
    // recommendations for the incoming profile, even when older results
    // are cached (e.g. in localStorage from a previous session).
    if (profileData && (incoming || !results)) run()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const best = results?.[0]
  const others = results?.slice(1) || []
  const hasAnyResults = results && results.length > 0

  const profilePurpose = profileData?.purpose === 'self_employment'
    ? t('eligibility.purposeSelf')
    : profileData?.purpose === 'education'
      ? t('eligibility.purposeEducation')
      : t('eligibility.purposeBusiness')
  const profileIncome = profileData?.annual_family_income
    ? `₹${profileData.annual_family_income.toLocaleString('en-IN')}`
    : '—'
  const profileLocation = [profileData?.district, profileData?.state].filter(Boolean).join(', ') || '—'

  return (
    <div className="container-app max-w-5xl py-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('recommendation.title')}</h1>
        <p className="mt-2 text-slate-500">{t('recommendation.subtitle')}</p>
      </div>

      {profileData && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 rounded-xl border border-slate-100 bg-slate-50 px-4 py-3 text-xs text-slate-500">
          <span className="font-medium text-slate-600">{t('recommendation.profileSummary')}:</span>
          <span>{t('recommendation.profilePurpose')}: <strong className="text-slate-800">{profilePurpose}</strong></span>
          <span>{t('recommendation.profileIncome')}: <strong className="text-slate-800">{profileIncome}</strong></span>
          <span>{t('recommendation.profileLocation')}: <strong className="text-slate-800">{profileLocation}</strong></span>
        </div>
      )}

      {loading && (
        <div className="mt-8">
          <LoadingState message="Finding suitable schemes…" rows={3} />
        </div>
      )}

      {error && !loading && (
        <div className="mt-8">
          <ErrorState
            message={error}
            onRetry={run}
          />
        </div>
      )}

      {!loading && !error && !profileData && (
        <div className="mt-16 flex flex-col items-center gap-4 text-center">
          <p className="text-slate-500">{t('eligibility.title')}</p>
          <Link to="/eligibility" className="btn-primary">{t('eligibility.start')}</Link>
        </div>
      )}

      {!loading && !error && profileData && results && results.length === 0 && (
        <div className="mt-16 flex flex-col items-center gap-4 text-center">
          <div className="rounded-xl bg-slate-50 p-6">
            <p className="text-sm font-semibold text-slate-700">{t('recommendation.noResults')}</p>
            <p className="mt-2 text-xs text-slate-500">No official schemes matched your profile. Try adjusting your purpose, project type, or location.</p>
          </div>
          <Link to="/eligibility" className="btn-secondary">{t('eligibility.start')}</Link>
        </div>
      )}

      {!loading && !error && hasAnyResults && (
        <div className="mt-8 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="green" dot>
                {results.length} {results.length === 1 ? 'match' : 'matches'}
              </Badge>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden />
                Official government schemes only
              </span>
              <button onClick={run} className="btn-ghost text-xs">
                <RefreshCw className="h-3.5 w-3.5" aria-hidden />
                Re-run
              </button>
            </div>
          </div>

          {best?.ai_explanation && (
            <div className="rounded-2xl border border-brand-100 bg-brand-50 p-5">
              <p className="text-sm font-semibold text-brand-900">AI explanation</p>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-700">{best.ai_explanation}</p>
            </div>
          )}

          {best && (
            <RecommendationCard result={best} rank={1} />
          )}

          {others.length > 0 && (
            <>
              <h2 className="pt-2 text-sm font-semibold uppercase tracking-wide text-slate-400">{t('recommendation.otherSchemes')}</h2>
              {others.map((r, i) => (
                <RecommendationCard key={r.scheme_id} result={r} rank={i + 2} />
              ))}
            </>
          )}

          {best && best.max_loan > 0 && (
            <section className="card p-6">
              <p className="text-sm font-semibold text-slate-700">{t('recommendation.snapshot')}</p>
              <p className="mt-1 text-xs text-amber-600">{t('recommendation.indicative')}</p>
              <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                {[
                  { label: t('recommendation.maxLoan'), value: formatLakh(best.max_loan) },
                  { label: t('recommendation.interest'), value: formatInterest(best.interest_rate, best.interest_display, best.interest_rate_type) },
                  best.tenure_months > 0 && { label: t('recommendation.tenure'), value: `${best.tenure_months} months` },
                  best.moratorium_months > 0 && { label: t('recommendation.moratorium'), value: `${best.moratorium_months} months` },
                ].filter(Boolean).map((x: any) => (
                  <div key={x.label} className="rounded-xl bg-slate-50 p-4">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400">{x.label}</p>
                    <p className="tnum mt-1 text-lg font-bold text-slate-900">{x.value}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          <div className="rounded-xl bg-amber-50 px-4 py-3 text-xs text-amber-800">
            ⚠️ {t('recommendation.officialVerifyNote')}
          </div>

          <section className="card p-6">
            <p className="text-sm font-semibold text-slate-700">{t('recommendation.nextSteps')}</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Link to="/compare" className="flex flex-col items-start gap-2 rounded-xl border border-slate-200 p-4 hover:border-brand-300 hover:bg-brand-50/40">
                <Landmark className="h-5 w-5 text-brand-700" aria-hidden />
                <span className="text-sm font-medium text-slate-700">{t('recommendation.compare')}</span>
                <ArrowRight className="h-4 w-4 text-slate-300" aria-hidden />
              </Link>
              <Link to="/calculator" className="flex flex-col items-start gap-2 rounded-xl border border-slate-200 p-4 hover:border-brand-300 hover:bg-brand-50/40">
                <CalcIcon className="h-5 w-5 text-brand-700" aria-hidden />
                <span className="text-sm font-medium text-slate-700">{t('recommendation.calcEmi')}</span>
                <ArrowRight className="h-4 w-4 text-slate-300" aria-hidden />
              </Link>
              <Link to={`/partners?scheme=${best?.scheme_id}`} className="flex flex-col items-start gap-2 rounded-xl border border-slate-200 p-4 hover:border-brand-300 hover:bg-brand-50/40">
                <MapPin className="h-5 w-5 text-brand-700" aria-hidden />
                <span className="text-sm font-medium text-slate-700">{t('recommendation.findPartner')}</span>
                <ArrowRight className="h-4 w-4 text-slate-300" aria-hidden />
              </Link>
              <Link to="/application" className="flex flex-col items-start gap-2 rounded-xl border border-slate-200 p-4 hover:border-brand-300 hover:bg-brand-50/40">
                <FileText className="h-5 w-5 text-brand-700" aria-hidden />
                <span className="text-sm font-medium text-slate-700">{t('recommendation.appGuide')}</span>
                <ArrowRight className="h-4 w-4 text-slate-300" aria-hidden />
              </Link>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}
