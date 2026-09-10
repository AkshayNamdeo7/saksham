import { useEffect } from 'react'
import { Link, NavLink, Navigate, Outlet, useNavigate } from 'react-router-dom'
import {
  BarChart3,
  FileText,
  Handshake,
  Landmark,
  LayoutDashboard,
  LogOut,
  Settings,
} from 'lucide-react'
import { isAdminAuthed } from '../../services/adminApi'
import { cls } from '../../utils/format'

const items = [
  { to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/admin/schemes', label: 'Schemes', icon: Landmark },
  { to: '/admin/partners', label: 'Partners', icon: Handshake },
  { to: '/admin/applications', label: 'Applications', icon: FileText },
  { to: '/admin/settings', label: 'Settings', icon: Settings },
]

export default function AdminLayout() {
  const navigate = useNavigate()

  useEffect(() => {
    if (!isAdminAuthed()) navigate('/admin/login')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!isAdminAuthed()) return <Navigate to="/admin/login" replace />

  return (
    <div className="flex min-h-screen bg-slate-100">
      <aside className="hidden w-60 shrink-0 flex-col bg-navy text-white md:flex">
        <div className="flex items-center gap-2 px-5 py-5">
          <img src="/logo.jpeg" alt="Saksham logo" className="h-9 w-9 rounded-xl object-cover" />
          <div>
            <p className="font-bold leading-none">Saksham Admin</p>
            <p className="mt-1 text-[10px] uppercase tracking-wider text-slate-400">Prototype console</p>
          </div>
        </div>
        <nav className="mt-2 flex-1 space-y-0.5 px-3">
          {items.map((x) => (
            <NavLink
              key={x.to}
              to={x.to}
              className={({ isActive }) =>
                cls(
                  'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition',
                  isActive ? 'bg-white/10 text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white',
                )
              }
            >
              <x.icon className="h-4 w-4" aria-hidden />
              {x.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-white/10 p-3">
          <Link
            to="/"
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-300 hover:bg-white/5 hover:text-white"
          >
            ← Back to site
          </Link>
          <button
            onClick={() => {
              localStorage.removeItem('saksham-admin-token')
              navigate('/admin/login')
            }}
            className="mt-1 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-red-200 hover:bg-white/10"
          >
            <LogOut className="h-4 w-4" aria-hidden />
            Logout
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-3.5 md:hidden">
          <span className="font-bold text-navy">Saksham Admin</span>
          <div className="flex items-center gap-2">
            {items.slice(0, 4).map((x) => (
              <NavLink key={x.to} to={x.to} className="p-2 text-slate-500" aria-label={x.label}>
                <x.icon className="h-5 w-5" />
              </NavLink>
            ))}
            <button
              onClick={() => {
                localStorage.removeItem('saksham-admin-token')
                navigate('/admin/login')
              }}
              className="p-2 text-slate-500"
              aria-label="Logout"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </header>
        <main className="flex-1 p-5 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}