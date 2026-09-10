import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ShieldCheck } from 'lucide-react'

export default function Footer() {
  const { t } = useTranslation()

  const linkRows: { to: string; label: string }[][] = [
    [
      { to: '/about', label: t('footer.about') },
      { to: '/eligibility', label: t('home.step1') },
      { to: '/schemes', label: 'Schemes' },
    ],
    [
      { to: '/calculator', label: 'EMI Calculator' },
      { to: '/partners', label: 'Partners' },
      { to: '/assistant', label: 'AI Assistant' },
    ],
  ]

  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="container-app py-10">
        <div className="grid gap-8 md:grid-cols-3">
          <div>
            <div className="flex items-center gap-2">
              <img src="/logo.jpeg" alt="Saksham logo" className="h-8 w-8 rounded-lg object-cover" />
              <span className="text-lg font-extrabold text-navy">Saksham</span>
            </div>
            <p className="mt-3 max-w-xs text-sm text-slate-500">
              {t('brand.tagline')}. {t('common.demoNotice')}
            </p>
          </div>

          {linkRows.map((rows, i) => (
            <nav key={i} className="space-y-2">
              {rows.map((l) => (
                <Link
                  key={l.to + l.label}
                  to={l.to}
                  className="block text-sm text-slate-600 hover:text-brand-800"
                >
                  {l.label}
                </Link>
              ))}
            </nav>
          ))}
        </div>

        <div className="mt-10 space-y-3 border-t border-slate-100 pt-6 text-xs text-slate-400">
          <p className="flex items-start gap-2">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" aria-hidden />
            {t('common.demoNotice')} Scheme eligibility, interest rates, loan limits, partner
            availability and documentation requirements should be verified against the latest
            official guidelines before applying.
          </p>
          <p>
            © {new Date().getFullYear()} Saksham (prototype). Built for Smart India Hackathon
            demonstration. No government affiliation is implied.
          </p>
        </div>
      </div>
    </footer>
  )
}