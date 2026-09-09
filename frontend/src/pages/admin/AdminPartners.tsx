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
import { Plus, Pencil, Trash2 } from 'lucide-react'

const TYPES = ['SCA', 'PSB', 'RRB', 'NBFC-MFI']
const STATUS = ['accepting', 'limited', 'unavailable']

const BASE: Record<string, any> = {
  name: '',
  type: 'SCA',
  state: 'Madhya Pradesh',
  district: '',
  city: '',
  address: '',
  latitude: 23.2599,
  longitude: 77.4126,
  status: 'accepting',
  capacity_pct: 100,
  fund_utilization_pct: 55,
  npa_indicator: 'low',
  phone: '1800-000-000',
  email: null,
  accepting_applications: true,
  scheme_slugs: [],
}

export default function AdminPartners() {
  const { data, loading, error, reload } = useFetch<any[]>(() => adminApi.partners.list(), [])
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
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.type.toLowerCase().includes(q) ||
        (p.city || '').toLowerCase().includes(q) ||
        (p.state || '').toLowerCase().includes(q),
    )
  }, [data, query])

  function openCreate() {
    setEditing(null)
    setForm({ ...BASE })
    setErr(null)
    setModal(true)
  }

  function openEdit(p: any) {
    setEditing(p)
    setForm({ ...BASE, ...p, email: p.email ?? null })
    setErr(null)
    setModal(true)
  }

  async function save() {
    setBusy(true)
    setErr(null)
    try {
      const payload = {
        ...form,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        capacity_pct: Number(form.capacity_pct),
        fund_utilization_pct: Number(form.fund_utilization_pct),
        accepting_applications: Boolean(form.accepting_applications),
        email: form.email || null,
        scheme_slugs: Array.isArray(form.scheme_slugs) ? form.scheme_slugs : [],
      }
      if (editing) await adminApi.partners.update(editing.id, payload)
      else await adminApi.partners.create(payload)
      setModal(false)
      reload()
      toast.success(editing ? 'Partner updated.' : 'Partner created.')
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Save failed')
      toast.error(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setBusy(false)
    }
  }

  async function remove(p: any) {
    if (!window.confirm(`Delete "${p.name}"?`)) return
    try {
      await adminApi.partners.delete(p.id)
      reload()
      toast.info(`Partner "${p.name}" deleted (demo).`)
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
          <h1 className="text-xl font-bold text-slate-900">Partners</h1>
          <p className="text-sm text-slate-500">{filtered.length} partners · demo data</p>
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
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">City</th>
              <th className="px-4 py-3">State</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Utilization</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50/60">
                <td className="px-4 py-3 font-medium text-slate-800">{p.name}</td>
                <td className="px-4 py-3 text-slate-500">{p.type}</td>
                <td className="px-4 py-3 text-slate-500">{p.city}</td>
                <td className="px-4 py-3 text-slate-500">{p.state}</td>
                <td className="px-4 py-3">
                  <Badge tone={p.status === 'accepting' ? 'green' : p.status === 'limited' ? 'amber' : 'red'} dot>
                    {p.status}
                  </Badge>
                </td>
                <td className="tnum px-4 py-3 text-slate-700">{p.fund_utilization_pct}%</td>
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-1">
                    <button onClick={() => openEdit(p)} className="rounded-lg p-2 text-slate-500 hover:bg-white hover:text-brand-700" aria-label="Edit">
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button onClick={() => remove(p)} className="rounded-lg p-2 text-slate-500 hover:bg-red-50 hover:text-red-600" aria-label="Delete">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-slate-400">No partners match.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Modal open={modal} onClose={() => setModal(false)} title={editing ? 'Edit partner' : 'New partner'}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Field label="Name" required>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </Field>
          </div>
          <Field label="Type">
            <Select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} options={TYPES.map((t) => ({ value: t, label: t }))} />
          </Field>
          <Field label="Status">
            <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} options={STATUS.map((t) => ({ value: t, label: t }))} />
          </Field>
          <Field label="City">
            <Input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          </Field>
          <Field label="State">
            <Input value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} />
          </Field>
          <Field label="District">
            <Input value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} />
          </Field>
          <Field label="Phone">
            <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>
          <Field label="Latitude">
            <Input type="number" step="0.0001" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} />
          </Field>
          <Field label="Longitude">
            <Input type="number" step="0.0001" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} />
          </Field>
          <Field label="Capacity %">
            <Input type="number" value={form.capacity_pct} onChange={(e) => setForm({ ...form, capacity_pct: e.target.value })} />
          </Field>
          <Field label="Utilization %">
            <Input type="number" value={form.fund_utilization_pct} onChange={(e) => setForm({ ...form, fund_utilization_pct: e.target.value })} />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Address">
              <textarea className="input min-h-[60px]" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            </Field>
          </div>
          <div className="sm:col-span-2 flex flex-wrap gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" checked={Boolean(form.accepting_applications)} onChange={(e) => setForm({ ...form, accepting_applications: e.target.checked })} />
              accepting_applications
            </label>
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