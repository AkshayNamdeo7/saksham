import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Calculator,
  Landmark,
  LayoutDashboard,
  MapPin,
  Menu,
  MessageSquareText,
  Search,
  ShieldCheck,
  X,
} from 'lucide-react'
import { cls } from '../../utils/format'
import LanguageSwitcher from './LanguageSwitcher'

const navItems = [
  { to: '/', labelKey: 'nav.home', end: true },
  { to: '/eligibility', labelKey: 'nav.findScheme', icon: Search },
  { to: '/schemes', labelKey: 'nav.schemes', icon: Landmark },
  { to: '/calculator', labelKey: 'nav.calculator', icon: Calculator },
  { to: '/partners', labelKey: 'nav.partners', icon: MapPin },
  { to: '/assistant', labelKey: 'nav.assistant', icon: MessageSquareText },
]

export default function Header() {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => setOpen(false), [location.pathname])

  return (
    <header
      className={cls(
        'sticky top-0 z-40 border-b transition',
        scrolled
          ? 'border-slate-200 bg-white/90 shadow-sm backdrop-blur'
          : 'border-transparent bg-white',
      )}
    >
      <div className="container-app flex h-16 items-center justify-between gap-3">
        <NavLink to="/" className="focus-ring flex items-center gap-2.5 rounded-lg" aria-label="Saksham home">
          <img src="/logo.jpeg" alt="Saksham logo" className="h-9 w-9 rounded-xl object-cover" />
          <span className="leading-tight">
            <span className="block text-lg font-extrabold tracking-tight text-navy">
              Saksham
            </span>
            <span className="hidden text-[10px] font-medium uppercase tracking-wider text-slate-400 sm:block">
              {t('brand.tagline')}
            </span>
          </span>
        </NavLink>

        <nav className="hidden items-center gap-0.5 lg:flex" aria-label="Primary">
          {navItems.map(({ to, labelKey, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cls(
                  'focus-ring rounded-lg px-3 py-2 text-sm font-medium transition',
                  isActive
                    ? 'bg-brand-50 text-brand-800'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
                )
              }
            >
              {t(labelKey)}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <LanguageSwitcher />
          <NavLink
            to="/admin"
            className="focus-ring inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            <LayoutDashboard className="h-4 w-4" aria-hidden />
            {t('nav.admin')}
          </NavLink>
        </div>

        <div className="flex items-center gap-2 lg:hidden">
          <LanguageSwitcher compact />
          <button
            onClick={() => setOpen(!open)}
            aria-label={open ? 'Close menu' : 'Open menu'}
            aria-expanded={open}
            className="focus-ring rounded-lg p-2 text-slate-600 hover:bg-slate-100"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {open && (
        <nav className="border-t border-slate-100 bg-white px-4 pb-4 pt-2 lg:hidden" aria-label="Mobile">
          <ul className="space-y-1">
            {navItems.map(({ to, labelKey, icon: Icon }) => {
              const active = location.pathname === to || (to !== '/' && location.pathname.startsWith(to))
              return (
                <li key={to}>
                  <NavLink
                    to={to}
                    className={cls(
                      'flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium',
                      active ? 'bg-brand-50 text-brand-800' : 'text-slate-700',
                    )}
                  >
                    {Icon && <Icon className="h-4 w-4" aria-hidden />}
                    {t(labelKey)}
                  </NavLink>
                </li>
              )
            })}
            <li className="pt-2">
              <NavLink
                to="/admin"
                className="flex items-center gap-3 rounded-xl border border-slate-200 px-3 py-3 text-sm font-medium text-slate-700"
              >
                <LayoutDashboard className="h-4 w-4" aria-hidden />
                {t('nav.admin')}
              </NavLink>
            </li>
          </ul>
          <p className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-400">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden />
            {t('brand.tagline')}
          </p>
        </nav>
      )}
    </header>
  )
}