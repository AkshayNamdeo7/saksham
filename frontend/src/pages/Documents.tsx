import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import { CheckCircle2, HelpCircle } from 'lucide-react'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import { Field, Select } from '../components/common/Inputs'

export default function Documents() {
  const { t, i18n } = useTranslation()
  const [schemeId, setSchemeId] = useState<number | ''>('')

  const { data: schemes } = useFetch(() => api.schemes.list(), [])
  const { data: docs, loading, error, reload } = useFetch(
    () => (schemeId ? api.schemes.documents(Number(schemeId)) : Promise.resolve([])),
    [schemeId],
  )

  const scheme = schemes?.find((s) => s.id === Number(schemeId))

  const hi = (i18n.language || 'en').startsWith('hi')

  return (
    <div className="container-app max-w-3xl py-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('documents.title')}</h1>
        <p className="mt-2 text-slate-500">{t('documents.subtitle')}</p>
      </div>

      <div className="card mt-8 p-6">
        <Field label="Scheme" id="doc-scheme" required>
          <Select
            id="doc-scheme"
            value={schemeId}
            onChange={(e) => setSchemeId(e.target.value ? Number(e.target.value) : '')}
            placeholder="Select a scheme…"
            options={(schemes || []).map((s) => ({ value: String(s.id), label: s.name }))}
          />
        </Field>

        {scheme && (
          <p className="mt-3 text-sm text-amber-700">
            ⚠️ {t('common.officialVerify')}: No document is universally mandatory — requirements depend on the scheme and official guidelines.
          </p>
        )}
      </div>

      <div className="mt-6">
        {!schemeId && (
          <div className="card p-8 text-center text-sm text-slate-400">
            Select a scheme to see its document checklist.
          </div>
        )}
        {loading && <LoadingState rows={4} />}
        {error && !loading && <ErrorState message={error} onRetry={reload} />}
        {!loading && !error && (docs || []).length > 0 && (
          <div className="space-y-3">
            {(docs || []).map((d) => (
              <div key={d.key} className="card flex items-start gap-4 p-5">
                <span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${d.is_required ? 'bg-brand-100 text-brand-800' : 'bg-slate-100 text-slate-500'}`}>
                  {d.is_required ? <CheckCircle2 className="h-5 w-5" /> : <HelpCircle className="h-5 w-5" />}
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-slate-900">{hi && d.name_hi ? d.name_hi : d.name}</p>
                  <p className="mt-1 text-sm text-slate-500">{d.description}</p>
                  <p className="mt-1.5 text-xs">
                    <span className={`badge ${d.is_required ? 'badge-blue' : 'badge-slate'}`}>
                      {d.is_required ? t('documents.required') : t('documents.optional')}
                    </span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {scheme && (docs || []).length > 0 && (
        <div className="mt-8 flex justify-center">
          <Link to={`/schemes/${scheme.id}`} className="btn-secondary">
            {t('schemeDetail.back')}
          </Link>
        </div>
      )}
    </div>
  )
}