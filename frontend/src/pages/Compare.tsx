import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import LoadingState from '../components/common/LoadingState'
import EmptyState from '../components/common/EmptyState'
import { formatLakh, formatPercent, tenureLabel, cls } from '../utils/format'

export default function Compare() {
  const { t } = useTranslation()
  const [params] = useSearchParams()
  const ids = useMemo(
    () => params.get('ids')?.split(',').map(Number).filter(Boolean) || [],
    [params],
  )

  const { data: all, loading, error } = useFetch(() => api.schemes.list(), [])

  const selected = (all || []).filter((s) => ids.includes(s.id)).slice(0, 3)

  const rows = useMemo(() => {
    const base = [
      { key: 'purpose', label: 'Purpose', get: (s: any) => s.purpose?.replace(/_/g, ' ') || '—' },
      { key: 'max_loan', label: t('schemes.maxLoan'), get: (s: any) => formatLakh(s.max_loan) },
      { key: 'interest_rate', label: t('schemes.interest'), get: (s: any) => formatPercent(s.interest_rate) },
      { key: 'tenure_months', label: t('schemes.tenure'), get: (s: any) => tenureLabel(s.tenure_months) },
      { key: 'moratorium_months', label: t('recommendation.moratorium'), get: (s: any) => tenureLabel(s.moratorium_months) },
      { key: 'income_threshold', label: 'Income threshold', get: (s: any) => (s.income_threshold ? formatLakh(s.income_threshold) : '—') },
      { key: 'partner_required', label: 'Partner required', get: (s: any) => (s.partner_required ? 'Yes' : 'No') },
    ]
    return base
  }, [t])

  return (
    <div className="container-app max-w-5xl py-12">
      <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('schemes.compare')}</h1>
      <p className="mt-2 text-slate-500">Compare 2–3 schemes side by side.</p>

      {loading && <div className="mt-8"><LoadingState rows={3} /></div>}
      {error && <p className="mt-8 text-red-600">{error}</p>}

      {!loading && !error && selected.length < 2 && (
        <div className="mt-8">
          <EmptyState message="Select at least two schemes to compare.">
            <Link to="/schemes" className="btn-primary mt-2">{t('schemes.title')}</Link>
          </EmptyState>
        </div>
      )}

      {!loading && !error && selected.length >= 2 && (
        <div className="card mt-8 overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="w-40 border-b border-slate-100 p-4 text-left font-semibold text-slate-400">Feature</th>
                {selected.map((s, i) => (
                  <th key={s.id} className={cls('border-b border-slate-100 p-4 text-left', i === 0 && 'bg-brand-50/50')}>
                    <div className="flex flex-col gap-1">
                      <span className="font-bold text-slate-900">{s.name}</span>
                      <Link to={`/schemes/${s.id}`} className="text-xs font-medium text-brand-700 hover:underline">
                        Details
                      </Link>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.key} className="border-b border-slate-50">
                  <td className="p-4 font-medium text-slate-500">{r.label}</td>
                  {selected.map((s, i) => (
                    <td key={s.id} className={cls('tnum p-4', i === 0 && 'bg-brand-50/40')}>
                      {r.get(s)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}