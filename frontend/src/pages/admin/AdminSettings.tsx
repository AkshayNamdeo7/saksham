import { useTranslation } from 'react-i18next'
import {
  Cpu,
  Database,
  FlaskConical,
  Globe,
  KeyRound,
  MapPin,
} from 'lucide-react'

export default function AdminSettings() {
  const { t } = useTranslation()
  const rows = [
    { key: 'VITE_API_URL', value: import.meta.env.VITE_API_URL || '(proxy → localhost:8000)' },
    { key: 'VITE_MAP_TILE_URL', value: import.meta.env.VITE_MAP_TILE_URL || '(OpenStreetMap default)' },
  ]

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-900">Settings</h1>
      <p className="mt-1 text-sm text-slate-500">Demo environment details. No secrets are stored on the client.</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="card p-5">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-amber-600" aria-hidden />
            <h2 className="text-sm font-bold text-slate-900">Demo mode</h2>
          </div>
          <p className="mt-2 text-sm text-slate-500">
            This is a prototype for the Smart India Hackathon. All schemes, partners and figures are sample data marked with the demo badge.
          </p>
          <span className="badge-amber mt-3">Prototype / Demo</span>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-slate-500" aria-hidden />
            <h2 className="text-sm font-bold text-slate-900">AI layer</h2>
          </div>
          <p className="mt-2 text-sm text-slate-500">
            AI explains deterministic results but never changes them. If no AI key is configured, a transparent template-based explanation is used.
          </p>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-slate-500" aria-hidden />
            <h2 className="text-sm font-bold text-slate-900">Data storage</h2>
          </div>
          <p className="mt-2 text-sm text-slate-500">
            FastAPI + SQLAlchemy. SQLite by default (backend/saksham.db), PostgreSQL-ready via DATABASE_URL.
          </p>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-slate-500" aria-hidden />
            <h2 className="text-sm font-bold text-slate-900">Administrator</h2>
          </div>
          <p className="mt-2 text-sm text-slate-500">Admin JWT session stored in localStorage. Log out in the sidebar when finished.</p>
        </div>
      </div>

      <div className="card mt-6 p-5">
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-slate-500" aria-hidden />
          <h2 className="text-sm font-bold text-slate-900">App configuration</h2>
        </div>
        <div className="mt-3 divide-y divide-slate-100">
          {rows.map((r) => (
            <div key={r.key} className="flex items-center justify-between gap-4 py-2.5">
              <span className="font-mono text-xs text-slate-500">{r.key}</span>
              <span className="truncate text-xs text-slate-400">{r.value}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card mt-6 p-5">
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-slate-500" aria-hidden />
          <h2 className="text-sm font-bold text-slate-900">Mapping</h2>
        </div>
        <p className="mt-2 text-sm text-slate-500">
          OpenStreetMap tiles via react-leaflet. Includes user geolocation (optional) and partner markers colored by status.
        </p>
      </div>

      <p className="mt-6 text-xs text-slate-400">
        Language for the public site: {t('nav.lang')} · {t('common.demoNotice')}
      </p>
    </div>
  )
}