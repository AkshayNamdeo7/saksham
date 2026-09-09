import { useState } from 'react'
import { useFetch } from '../../hooks/useFetch'
import { adminApi } from '../../services/adminApi'
import LoadingState from '../../components/common/LoadingState'
import ErrorState from '../../components/common/ErrorState'
import Badge from '../../components/common/Badge'
import { formatINR } from '../../utils/format'

export default function AdminApplications() {
  const { data: applications, loading: la, error: ea, reload: ra } = useFetch<any[]>(
    () => adminApi.applications(),
    [],
  )
  const { data: recommendations, loading: lr, error: er, reload: rr } = useFetch<any[]>(
    () => adminApi.recommendations(),
    [],
  )
  const [tab, setTab] = useState<'applications' | 'recommendations'>('applications')

  if (la || lr) return <LoadingState rows={5} />
  if ((tab === 'applications' && ea) || (tab === 'recommendations' && er)) {
    return <ErrorState message={(tab === 'applications' ? ea : er)!} onRetry={tab === 'applications' ? ra : rr} />
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Applications</h1>
          <p className="text-sm text-slate-500">Application-routing guidance and recommendations recorded during the demo.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setTab('applications')} className={tab === 'applications' ? 'btn-primary text-xs' : 'btn-secondary text-xs'}>
            Routing ({applications?.length || 0})
          </button>
          <button onClick={() => setTab('recommendations')} className={tab === 'recommendations' ? 'btn-primary text-xs' : 'btn-secondary text-xs'}>
            Recommendations ({recommendations?.length || 0})
          </button>
        </div>
      </div>

      {tab === 'applications' ? (
        <div className="card mt-6 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-[11px] uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3">Scheme</th>
                <th className="px-4 py-3">Partner</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Loan</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {(applications || []).map((a) => (
                <tr key={a.id} className="border-b border-slate-50 align-top hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-medium text-slate-800">{a.scheme_name || '—'}</td>
                  <td className="px-4 py-3 text-slate-500">{a.partner_name || '—'}</td>
                  <td className="px-4 py-3">
                    <Badge tone="blue">{a.partner_score ?? '—'}</Badge>
                  </td>
                  <td className="tnum px-4 py-3 text-slate-700">{a.loan_required ? formatINR(a.loan_required) : '—'}</td>
                  <td className="px-4 py-3 text-xs text-slate-400">{a.created_at ? new Date(a.created_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
              {(applications || []).length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-slate-400">
                    No routing guidance recorded yet. Run the Application flow on the site.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card mt-6 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-[11px] uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3">Scheme</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {(recommendations || []).map((r) => (
                <tr key={r.id} className="border-b border-slate-50 hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-medium text-slate-800">{r.scheme_name || '—'}</td>
                  <td className="tnum px-4 py-3 text-slate-700">{r.match_score}%</td>
                  <td className="px-4 py-3">
                    <Badge tone={r.eligibility_status === 'eligible' ? 'green' : r.eligibility_status === 'conditional' ? 'amber' : 'red'}>
                      {r.eligibility_status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">{r.created_at ? new Date(r.created_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
              {(recommendations || []).length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-10 text-center text-slate-400">
                    No recommendations recorded yet. Run the Eligibility flow on the site.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}