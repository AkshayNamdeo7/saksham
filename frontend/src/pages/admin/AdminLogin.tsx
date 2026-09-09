import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock, ShieldCheck } from 'lucide-react'
import Button from '../../components/common/Button'
import { Field, Input } from '../../components/common/Inputs'
import { adminApi } from '../../services/adminApi'
import { useTranslation } from 'react-i18next'

export default function AdminLogin() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function login() {
    setBusy(true)
    setError(null)
    try {
      const res = await adminApi.login(username, password)
      localStorage.setItem('saksham-admin-token', res.access_token)
      localStorage.setItem('saksham-admin-name', res.display_name)
      navigate('/admin/dashboard', { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 text-3xl font-extrabold text-white">स</div>
          <h1 className="mt-4 text-2xl font-bold text-white">Saksham Admin</h1>
          <p className="mt-1 text-sm text-slate-400">{t('nav.admin')}</p>
        </div>
        <div className="rounded-2xl bg-white p-6 shadow-elevated">
          <div className="space-y-4">
            <Field label="Username">
              <Input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
            </Field>
            <Field label="Password">
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && login()}
                autoComplete="current-password"
              />
            </Field>
            {error && <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
            <Button onClick={login} loading={busy} fullWidth>
              <Lock className="h-4 w-4" aria-hidden />
              Sign in
            </Button>
          </div>
          <div className="mt-4 rounded-lg bg-slate-50 px-3 py-2.5 text-xs text-slate-500">
            Demo credentials:
            <br />
            username <span className="font-mono font-semibold">admin</span>
            <br />
            password <span className="font-mono font-semibold">saksham@2026</span>
          </div>
        </div>
        <p className="mt-4 flex items-center justify-center gap-1.5 text-xs text-slate-400">
          <ShieldCheck className="h-3.5 w-3.5" aria-hidden />
          Prototype · For demonstration only.
        </p>
      </div>
    </div>
  )
}