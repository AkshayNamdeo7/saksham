import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Mail, ShieldCheck } from 'lucide-react'

const CONTACT_EMAIL = 'akshaynamdeo2006@gmail.com'

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
    [
      { to: '/help', label: t('footer.help') },
    ],
  ]

  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="container-app py-10">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <div className="flex items-center gap-2">
              <img src="/logo1.jpeg" alt="Saksham logo" className="h-8 w-8 rounded-lg object-contain" />
              <span className="text-lg font-extrabold text-navy">Saksham</span>
            </div>
            <p className="mt-3 max-w-xs text-sm text-slate-500">
              {t('brand.tagline')}
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

          <nav className="space-y-2">
            <p className="text-sm font-semibold text-slate-700">{t('footer.contact')}</p>
            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-brand-800"
            >
              <Mail className="h-4 w-4 shrink-0" aria-hidden />
              <span className="break-all">{CONTACT_EMAIL}</span>
            </a>
          </nav>
        </div>

        <div className="mt-10 space-y-3 border-t border-slate-100 pt-6 text-xs text-slate-400">
          <p className="flex items-start gap-2">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden />
            Scheme eligibility, interest rates, loan limits, partner availability and
            documentation requirements may change. Always verify against the latest official
            guidelines before applying.
          </p>
          <p>
            © {new Date().getFullYear()} Saksham. Built for Smart India Hackathon. No government
            affiliation is implied.
          </p>
        </div>
      </div>
    </footer>
  )
}