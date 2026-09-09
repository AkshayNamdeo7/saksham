import { useFetch } from '../../hooks/useFetch'
import { adminApi } from '../../services/adminApi'
import StatCard from '../../components/common/StatCard'
import LoadingState from '../../components/common/LoadingState'
import ErrorState from '../../components/common/ErrorState'
import {
  Landmark,
  Handshake,
  FileText,
  BadgeCheck,
  AlertTriangle,
  BarChart3,
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const PIE_COLORS = ['#0b2545', '#4f46e5', '#10b981', '#f59e0b', '#ef4444']

export default function AdminDashboard() {
  const { data, loading, error, reload } = useFetch(() => adminApi.dashboard(), [])

  if (loading) return <LoadingState rows={4} />
  if (error) return <ErrorState message={error} onRetry={reload} />
  if (!data) return null

  const { totals } = data

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500">Live demo analytics (prototype data).</p>
        </div>
        <span className="badge-amber">Prototype / Demo</span>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Landmark} label="Total Schemes" value={totals.schemes} sub={`${totals.active_schemes} active`} />
        <StatCard icon={Handshake} label="Active Partners" value={totals.partners} sub={`${totals.accepting_partners} accepting`} tone="green" />
        <StatCard icon={FileText} label="Demo Applications" value={totals.applications} sub={`${totals.eligibility_checks} checks`} />
        <StatCard icon={BarChart3} label="Recommendations" value={totals.recommendations} sub={`${totals.events} events`} tone="amber" />
      </div>

      <div className="mt-6 grid gap-4 rounded-2xl bg-white p-4 sm:grid-cols-3">
        <div className="rounded-xl bg-slate-50 p-4 text-center">
          <p className="flex items-center justify-center gap-1 text-xs text-slate-400">
            <BadgeCheck className="h-3.5 w-3.5 text-emerald-500" aria-hidden /> Accepting
          </p>
          <p className="tnum mt-1 text-2xl font-bold text-emerald-700">{totals.accepting_partners}</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-4 text-center">
          <p className="text-xs text-slate-400">Limited capacity</p>
          <p className="tnum mt-1 text-2xl font-bold text-amber-600">{totals.limited_partners}</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-4 text-center">
          <p className="flex items-center justify-center gap-1 text-xs text-slate-400">
            <AlertTriangle className="h-3.5 w-3.5 text-red-500" aria-hidden /> Unavailable
          </p>
          <p className="tnum mt-1 text-2xl font-bold text-red-600">{totals.unavailable_partners}</p>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h2 className="text-base font-bold text-slate-900">Recommendations by scheme (demo)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.by_scheme.map((x) => ({ name: x.scheme, count: x.count }))} margin={{ top: 16 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#4f46e5" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6">
          <h2 className="text-base font-bold text-slate-900">Purpose distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={data.by_purpose.map((x) => ({ name: x.purpose, value: x.count }))} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={3}>
                {(data.by_purpose || []).map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 flex flex-wrap justify-center gap-3 text-xs">
            {(data.by_purpose || []).map((x, i) => (
              <span key={x.purpose} className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                {x.purpose}
              </span>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-base font-bold text-slate-900">Partner status (demo)</h2>
          <div className="mt-4 space-y-3">
            {[
              { key: 'accepting', label: 'Accepting', color: '#059669' },
              { key: 'limited', label: 'Limited capacity', color: '#d97706' },
              { key: 'unavailable', label: 'Unavailable', color: '#dc2626' },
            ].map((s) => {
              const row = (data.by_partner_status || []).find((x) => x.status === s.key)
              const count = row?.count || 0
              const max = Math.max(...(data.by_partner_status || []).map((x) => x.count), 1)
              return (
                <div key={s.key}>
                  <div className="flex justify-between text-sm">
                    <span className="flex items-center gap-1.5 text-slate-600">
                      <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                      {s.label}
                    </span>
                    <span className="tnum font-bold text-slate-900">{count}</span>
                  </div>
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full" style={{ width: `${(count / max) * 100}%`, background: s.color }} />
                  </div>
                </div>
              )
            })}
          </div>
          <p className="mt-3 text-xs text-slate-400">Prototype availability — not real bank data.</p>
        </div>

        <div className="card p-6">
          <h2 className="text-base font-bold text-slate-900">Route applications by state</h2>
          {data.by_application_state.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.by_application_state.map((x) => ({ name: x.state, count: x.count }))} margin={{ top: 16 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#0b2545" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-16 text-center text-sm text-slate-400">
              No route applications recorded yet. Run the Application flow on the site.
            </p>
          )}
        </div>

        <div className="card p-6">
          <h2 className="text-base font-bold text-slate-900">Partners by state</h2>
          <div className="mt-4 space-y-3">
            {data.by_state.map((x) => (
              <div key={x.state}>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">{x.state}</span>
                  <span className="tnum font-bold text-slate-900">{x.count}</span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-brand-600"
                    style={{ width: `${(x.count / Math.max(...data.by_state.map((s) => s.count), 1)) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-base font-bold text-slate-900">Partners by type</h2>
          <div className="mt-4 space-y-3">
            {data.by_type.map((x) => (
              <div key={x.name} className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3">
                <span className="text-sm font-medium text-slate-700">{x.name}</span>
                <span className="tnum text-sm font-bold text-slate-900">{x.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}