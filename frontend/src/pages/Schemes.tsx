import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import type { Scheme } from '../types'
import SchemeCard from '../components/cards/SchemeCard'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'
import { Field, Input, Select } from '../components/common/Inputs'
import { formatINR } from '../utils/format'

const LOAN_BUCKETS = ['25000', '50000', '100000', '250000', '500000', '1000000']

const CATEGORY_LABELS: Record<string, (t: (k: string) => string) => string> = {
  business: () => 'Business',
  education: () => 'Education',
  support: () => 'Skill / Support',
  sanitation_enterprise: () => 'Sanitation Enterprise',
  micro_finance: (t) => t('home.catMicro'),
  term_loan: (t) => t('home.catTerm'),
}

export default function Schemes() {
  const { t } = useTranslation()
  const [search, setSearch] = useState('')
  const [purpose, setPurpose] = useState('')
  const [category, setCategory] = useState('')
  const [minLoan, setMinLoan] = useState('')
  const [maxLoan, setMaxLoan] = useState('')
  const [compareIds, setCompareIds] = useState<number[]>([])

  const { data, loading, error, reload } = useFetch(() => api.schemes.list(), [])

  const categoryOptions = useMemo(() => {
    const seen = new Set<string>()
    const opts: { value: string; label: string }[] = []
    for (const s of data || []) {
      if (!s.category || seen.has(s.category)) continue
      seen.add(s.category)
      const label = CATEGORY_LABELS[s.category]?.(t) ?? s.category.replace(/_/g, ' ')
      opts.push({ value: s.category, label })
    }
    return opts
  }, [data, t])

  const filtered = useMemo(() => {
    let list = data || []
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      list = list.filter((s) => s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q))
    }
    if (purpose) list = list.filter((s) => s.purpose === purpose)
    if (category) list = list.filter((s) => s.category === category)
    if (minLoan) {
      const v = Number(minLoan)
      list = list.filter((s) => Number(s.max_loan) >= v)
    }
    if (maxLoan) {
      const v = Number(maxLoan)
      list = list.filter((s) => Number(s.min_loan) <= v)
    }
    return list
  }, [data, search, purpose, category, minLoan, maxLoan])

  function toggleCompare(id: number) {
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (prev.length >= 3) return prev
      return [...prev, id]
    })
  }

  return (
    <div className="container-app py-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('schemes.title')}</h1>
        <p className="mt-2 text-slate-500">{t('schemes.subtitle')}</p>
      </div>

      <div className="mt-8 grid gap-4 rounded-2xl bg-white p-4 shadow-card sm:grid-cols-2 lg:grid-cols-3">
        <Field label={t('common.search')} id="sch_search">
          <Input
            id="sch_search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('schemes.search')}
          />
        </Field>
        <Field label="Purpose" id="sch_purpose">
          <Select
            id="sch_purpose"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            placeholder={t('schemes.allPurpose')}
            options={[
              { value: 'business', label: t('eligibility.purposeBusiness') },
              { value: 'self_employment', label: t('eligibility.purposeSelf') },
              { value: 'education', label: t('eligibility.purposeEducation') },
            ]}
          />
        </Field>
        <Field label="Category" id="sch_cat">
          <Select
            id="sch_cat"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder={t('schemes.allCategory')}
            options={categoryOptions}
          />
        </Field>
        <Field label={t('schemes.minLoan')} id="sch_minloan">
          <Select
            id="sch_minloan"
            value={minLoan}
            onChange={(e) => setMinLoan(e.target.value)}
            placeholder={t('schemes.anyLoan')}
            options={LOAN_BUCKETS.map((v) => ({ value: v, label: `${formatINR(Number(v))}+` }))}
          />
        </Field>
        <Field label={t('schemes.maxLoan')} id="sch_maxloan">
          <Select
            id="sch_maxloan"
            value={maxLoan}
            onChange={(e) => setMaxLoan(e.target.value)}
            placeholder={t('schemes.anyLoan')}
            options={LOAN_BUCKETS.map((v) => ({ value: v, label: `up to ${formatINR(Number(v))}` }))}
          />
        </Field>
        <div className="flex items-end">
          {compareIds.length >= 2 ? (
            <Link
              to={`/compare?ids=${compareIds.join(',')}`}
              className="btn-primary w-full"
            >
              {t('schemes.compareNow')} ({compareIds.length})
            </Link>
          ) : (
            <p className="w-full pb-1 text-center text-xs text-slate-400">
              {t('schemes.pickToCompare')}
            </p>
          )}
        </div>
      </div>

      {loading && <div className="mt-8"><LoadingState rows={4} /></div>}
      {error && !loading && (
        <div className="mt-8">
          <ErrorState message={error} onRetry={reload} />
        </div>
      )}
      {!loading && !error && filtered.length === 0 && (
        <div className="mt-8">
          <EmptyState message={t('schemes.empty')} />
        </div>
      )}
      {!loading && !error && filtered.length > 0 && (
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((s: Scheme) => (
            <SchemeCard
              key={s.id}
              scheme={s}
              compare={compareIds.includes(s.id)}
              onCompare={toggleCompare}
            />
          ))}
        </div>
      )}
    </div>
  )
}