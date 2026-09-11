import { useMemo, useState } from 'react'
import { useFetch } from '../../hooks/useFetch'
import { adminApi } from '../../services/adminApi'
import LoadingState from '../../components/common/LoadingState'
import ErrorState from '../../components/common/ErrorState'
import Modal from '../../components/common/Modal'
import Button from '../../components/common/Button'
import { Field, Input, Select } from '../../components/common/Inputs'
import Badge from '../../components/common/Badge'
import { useToast } from '../../context/ToastContext'
import { formatINR } from '../../utils/format'
import { Plus, Pencil, Trash2 } from 'lucide-react'

const CATEGORIES = ['micro_finance', 'term_loan', 'education']
const PURPOSES = ['business', 'self_employment', 'education']

const BASE: Record<string, any> = {
  name: '',
  slug: '',
  description: '',
  category: 'micro_finance',
  purpose: 'business',
  max_loan: 1000000,
  min_loan: 10000,
  interest_rate: 7,
  tenure_months: 36,
  moratorium_months: 0,
  income_threshold: 300000,
  project_min: null,
  project_max: null,
  education_focus: false,
  eligibility_notes: '',
  required_documents: '',
  partner_required: true,
  active: true,
  is_demo: true,
}

export default function AdminSchemes() {
  const { data, loading, error, reload } = useFetch<any[]>(() => adminApi.schemes.list(), [])
  const toast = useToast()
  const [query, setQuery] = useState('')
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<any | null>(null)
  const [form, setForm] = useState<Record<string, any>>(BASE)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const q = query.toLowerCase()
    return (data || []).filter(
      (s) => s.name.toLowerCase().includes(q) || s.category.includes(q) || s.purpose.includes(q),
    )
  }, [data, query])

  function openCreate() {
    setEditing(null)
    setForm({ ...BASE })
    setErr(null)
    setModal(true)
  }

  function openEdit(s: any) {
    setEditing(s)
    setForm({
      ...BASE,
      ...s,
      min_loan: s.min_loan ?? null,
      project_min: s.project_min ?? null,
      project_max: s.project_max ?? null,
      income_threshold: s.income_threshold ?? null,
    })
    setErr(null)
    setModal(true)
  }

  async function save() {
    setBusy(true)
    setErr(null)
    try {
      const payload = {
        ...form,
        min_loan: form.min_loan === '' || form.min_loan == null ? null : Number(form.min_loan),
        max_loan: Number(form.max_loan),
        interest_rate: Number(form.interest_rate),
        tenure_months: Number(form.tenure_months),
        moratorium_months: Number(form.moratorium_months),
        income_threshold: form.income_threshold === '' || form.income_threshold == null ? null : Number(form.income_threshold),
        project_min: form.project_min === '' || form.project_min == null ? null : Number(form.project_min),
        project_max: form.project_max === '' || form.project_max == null ? null : Number(form.project_max),
        education_focus: Boolean(form.education_focus),
        active: Boolean(form.active),
        partner_required: Boolean(form.partner_required),
      }
      if (editing) await adminApi.schemes.update(editing.id, payload)
      else await adminApi.schemes.create(payload)
      setModal(false)
      reload()
      toast.success(editing ? 'Scheme updated.' : 'Scheme created.')
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed')
      toast.error(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setBusy(false)
    }
  }

  async function remove(s: any) {
    if (!window.confirm(`Delete "${s.name}"? This is a destructive demo action.`)) return
    try {
      await adminApi.schemes.delete(s.id)
      reload()
      toast.info(`Scheme "${s.name}" deleted (demo).`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  if (loading) return <LoadingState rows={5} />
  if (error) return <ErrorState message={error} onRetry={reload} />

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Schemes</h1>
          <p className="text-sm text-slate-500">{filtered.length} schemes · demo data</p>
        </div>
        <div className="flex gap-2">
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search…" />
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4" aria-hidden />
            New
          </Button>
        </div>
      </div>

      <div className="card mt-6 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-100 text-[11px] uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Purpose</th>
              <th className="px-4 py-3">Max loan</th>
              <th className="px-4 py-3">Rate</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr key={s.id} className="border-b border-slate-50 hover:bg-slate-50/60">
                <td className="px-4 py-3 font-medium text-slate-800">{s.name}</td>
                <td className="px-4 py-3 text-slate-500">{s.category}</td>
                <td className="px-4 py-3 text-slate-500">{s.purpose}</td>
                <td className="tnum px-4 py-3 text-slate-700">{formatINR(s.max_loan)}</td>
                <td className="tnum px-4 py-3 text-slate-700">{s.interest_rate != null ? `${s.interest_rate}%` : '—'}</td>
                <td className="px-4 py-3">
                  <Badge tone={s.active ? 'green' : 'red'} dot>{s.active ? 'Active' : 'Inactive'}</Badge>
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-1">
                    <button onClick={() => openEdit(s)} className="rounded-lg p-2 text-slate-500 hover:bg-white hover:text-brand-700" aria-label="Edit">
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button onClick={() => remove(s)} className="rounded-lg p-2 text-slate-500 hover:bg-red-50 hover:text-red-600" aria-label="Delete">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-slate-400">No schemes match.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Modal open={modal} onClose={() => setModal(false)} title={editing ? 'Edit scheme' : 'New scheme'}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Field label="Name" required>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </Field>
          </div>
          <Field label="Slug" required>
            <Input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
          </Field>
          <Field label="Category">
            <Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} options={CATEGORIES.map((c) => ({ value: c, label: c }))} />
          </Field>
          <Field label="Purpose">
            <Select value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })} options={PURPOSES.map((c) => ({ value: c, label: c }))} />
          </Field>
          <Field label="Max loan (₹)">
            <Input type="number" value={form.max_loan} onChange={(e) => setForm({ ...form, max_loan: e.target.value })} />
          </Field>
          <Field label="Min loan (₹)">
            <Input type="number" value={form.min_loan ?? ''} onChange={(e) => setForm({ ...form, min_loan: e.target.value })} />
          </Field>
          <Field label="Interest rate (% p.a.)">
            <Input type="number" step="0.01" value={form.interest_rate} onChange={(e) => setForm({ ...form, interest_rate: e.target.value })} />
          </Field>
          <Field label="Tenure (months)">
            <Input type="number" value={form.tenure_months} onChange={(e) => setForm({ ...form, tenure_months: e.target.value })} />
          </Field>
          <Field label="Moratorium (months)">
            <Input type="number" value={form.moratorium_months} onChange={(e) => setForm({ ...form, moratorium_months: e.target.value })} />
          </Field>
          <Field label="Income threshold (₹)">
            <Input type="number" value={form.income_threshold ?? ''} onChange={(e) => setForm({ ...form, income_threshold: e.target.value })} />
          </Field>
          <Field label="Project cost min (₹)">
            <Input type="number" value={form.project_min ?? ''} onChange={(e) => setForm({ ...form, project_min: e.target.value })} />
          </Field>
          <Field label="Project cost max (₹)">
            <Input type="number" value={form.project_max ?? ''} onChange={(e) => setForm({ ...form, project_max: e.target.value })} />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Eligibility notes">
              <textarea
                className="input min-h-[70px]"
                value={form.eligibility_notes}
                onChange={(e) => setForm({ ...form, eligibility_notes: e.target.value })}
              />
            </Field>
          </div>
          <div className="sm:col-span-2 flex flex-wrap gap-3">
            {(['active', 'education_focus', 'partner_required'] as const).map((k) => (
              <label key={k} className="flex items-center gap-2 text-sm text-slate-600">
                <input type="checkbox" checked={Boolean(form[k])} onChange={(e) => setForm({ ...form, [k]: e.target.checked })} />
                {k}
              </label>
            ))}
          </div>
        </div>
        {err && <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{err}</p>}
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setModal(false)}>Cancel</Button>
          <Button onClick={save} loading={busy}>{editing ? 'Save changes' : 'Create'}</Button>
        </div>
      </Modal>
    </div>
  )
}