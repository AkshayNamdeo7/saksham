import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import {
  Map as MapIcon,
  List,
  Navigation,
  ShieldCheck,
  Star,
} from 'lucide-react'
import { api } from '../services/api'
import type { Profile, ScoredPartner } from '../types'
import { useProfile } from '../context/ProfileContext'
import { Field, Select } from '../components/common/Inputs'
import PartnerCard from '../components/cards/PartnerCard'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import MapPanel from '../components/map/MapPanel'
import { cls } from '../utils/format'

const TYPES = ['SCA', 'PSB', 'RRB', 'NBFC-MFI']

export default function Partners() {
  const { t } = useTranslation()
  const [params] = useSearchParams()
  const { profile, selectedScheme, loanRequired } = useProfile()

  const [state, setState] = useState<string>((profile?.state as string) || 'Madhya Pradesh')
  const [partnerType, setPartnerType] = useState('')
  const [status, setStatus] = useState('')
  const [view, setView] = useState<'map' | 'list'>('map')
  const [userCoords, setUserCoords] = useState<[number, number] | null>(null)
  const [scored, setScored] = useState<ScoredPartner[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const schemeId = Number(params.get('scheme') || selectedScheme?.id || 0) || undefined

  async function recommend() {
    setLoading(true)
    setError(null)
    try {
      const res = await api.partnersRecommend.recommend({
        state,
        district: profile?.district,
        latitude: userCoords ? userCoords[0] : undefined,
        longitude: userCoords ? userCoords[1] : undefined,
        scheme_id: schemeId,
        purpose: profile?.purpose || selectedScheme?.purpose,
        loan_amount: loanRequired ?? undefined,
        limit: 10,
      })
      setScored(res.results)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Partner lookup failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setUserCoords([pos.coords.latitude, pos.coords.longitude]),
        () => {},
        { timeout: 5000 },
      )
    }
  }, [])

  useEffect(() => {
    recommend()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state, schemeId])

  const filtered = useMemo(() => {
    let list = scored
    if (partnerType) list = list.filter((p) => p.type === partnerType)
    if (status) list = list.filter((p) => p.status === status)
    return list
  }, [scored, partnerType, status])

  const recommended = filtered[0] || null

  const center = useMemo<[number, number] | null>(() => {
    return userCoords || (recommended ? [recommended.latitude, recommended.longitude] : null)
  }, [userCoords, recommended])

  function getDirections(p: ScoredPartner) {
    window.open(
      `https://www.google.com/maps/dir/?api=1&destination=${p.latitude},${p.longitude}`,
      '_blank',
      'noopener',
    )
  }

  return (
    <div className="container-app py-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('partners.title')}</h1>
          <p className="mt-2 text-slate-500">{t('partners.subtitle')}</p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 rounded-2xl bg-white p-4 shadow-card sm:grid-cols-3">
        <Field label="State" id="p-state">
          <Select
            id="p-state"
            value={state}
            onChange={(e) => setState(e.target.value)}
            options={['Madhya Pradesh', 'Maharashtra', 'Uttar Pradesh', 'Bihar', 'Rajasthan', 'Haryana'].map((s) => ({ value: s, label: s }))}
          />
        </Field>
        <Field label="Partner type" id="p-type">
          <Select
            id="p-type"
            value={partnerType}
            onChange={(e) => setPartnerType(e.target.value)}
            placeholder={t('partners.allTypes')}
            options={TYPES.map((x) => ({ value: x, label: x }))}
          />
        </Field>
        <Field label="Status" id="p-status">
          <Select
            id="p-status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            placeholder={t('partners.allStatus')}
            options={[
              { value: 'accepting', label: `🟢 ${t('partners.accepting')}` },
              { value: 'limited', label: `🟡 ${t('partners.limited')}` },
              { value: 'unavailable', label: `🔴 ${t('partners.unavailable')}` },
            ]}
          />
        </Field>
      </div>

      <div className="mt-6 flex gap-2">
        <button
          onClick={() => setView('map')}
          className={cls('btn', view === 'map' ? 'btn-primary' : 'btn-secondary')}
        >
          <MapIcon className="h-4 w-4" aria-hidden />
          {t('partners.mapToggle')}
        </button>
        <button
          onClick={() => setView('list')}
          className={cls('btn', view === 'list' ? 'btn-primary' : 'btn-secondary')}
        >
          <List className="h-4 w-4" aria-hidden />
          {t('partners.list')}
        </button>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[400px_1fr]">
        <div className={cls(view === 'map' ? 'order-2 lg:order-1' : 'order-1')}>
          {loading ? (
            <LoadingState message="Finding suitable partners…" rows={4} />
          ) : error ? (
            <ErrorState message={error} onRetry={recommend} />
          ) : (
            <div className="space-y-4">
              {recommended && (
                <div className="card border-brand-300 bg-brand-50/50 p-4">
                  <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-brand-800">
                    <Star className="h-3.5 w-3.5 fill-current" aria-hidden />
                    {t('partners.recommended')} · {recommended.total_score}/100
                  </p>
                  <PartnerCard partner={recommended} recommended onDirections={getDirections} onSelect={(p) => setSelectedId(p.id)} />
                </div>
              )}

              <p className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                {filtered.length} {filtered.length === 1 ? 'partner' : 'partners'}
              </p>

              {filtered.length === 0 ? (
                <p className="rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-400">
                  {t('partners.empty')}
                </p>
              ) : (
                <div className="max-h-[60vh] space-y-3 overflow-y-auto pr-1">
{filtered.map((p) => (
                            <PartnerCard
                              key={p.id}
                              partner={p}
                              onDirections={getDirections}
                              onSelect={(x) => setSelectedId(x.id)}
                            />
                          ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className={cls('min-h-[420px] rounded-2xl border border-slate-200 bg-slate-100', view === 'map' ? 'order-1 lg:order-2' : 'hidden')}>
          <MapPanel
            partners={filtered as any}
            selected={selectedId}
            userCoords={center}
            onSelect={(id) => setSelectedId(id)}
          />
        </div>
      </div>

      {recommended && (
        <div className="card mt-8 p-6">
          <h2 className="flex items-center gap-2 text-base font-bold text-slate-900">
            <ShieldCheck className="h-5 w-5 text-emerald-600" aria-hidden />
            {t('partners.why')}: {recommended.name}
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(recommended.breakdown).map(([k, v]) => (
              <div key={k} className="rounded-xl bg-slate-50 p-4">
                <p className="text-[11px] uppercase tracking-wide text-slate-400">{k}</p>
                <p className="tnum mt-0.5 text-lg font-bold text-slate-900">{v} pts</p>
              </div>
            ))}
          </div>
          <ul className="mt-4 space-y-1.5">
            {recommended.notes.map((n) => (
              <li key={n} className="flex items-start gap-2 text-sm text-slate-600">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                {n}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-amber-700">
            {t('common.demoNotice')}
          </p>
        </div>
      )}
    </div>
  )
}