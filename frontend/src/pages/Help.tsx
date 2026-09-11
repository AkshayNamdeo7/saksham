import { useTranslation } from 'react-i18next'
import { Mail } from 'lucide-react'

const CONTACT_EMAIL = 'akshaynamdeo2006@gmail.com'

export default function Help() {
  const { t } = useTranslation()

  const faqs = [
    { q: t('help.q1'), a: t('help.q1a') },
    { q: t('help.q2'), a: t('help.q2a') },
    { q: t('help.q3'), a: t('help.q3a') },
  ]

  return (
    <div className="container-app max-w-3xl py-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('help.title')}</h1>
        <p className="mt-2 text-slate-500">{t('help.subtitle')}</p>
      </div>

      <section className="mt-10">
        <h2 className="text-base font-bold text-slate-900">{t('help.faqTitle')}</h2>
        <div className="mt-4 space-y-3">
          {faqs.map((f) => (
            <details key={f.q} className="card group p-5">
              <summary className="cursor-pointer list-none text-sm font-semibold text-slate-900">
                <span className="inline-block w-2 transition group-open:rotate-90">›</span> {f.q}
              </summary>
              <p className="mt-2 pl-5 text-sm text-slate-500">{f.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="card mt-10 flex items-start gap-3 p-6">
        <Mail className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" aria-hidden />
        <div>
          <h2 className="text-base font-bold text-slate-900">{t('help.contactTitle')}</h2>
          <p className="mt-1 text-sm text-slate-500">{t('help.contactDesc')}</p>
          <a
            href={`mailto:${CONTACT_EMAIL}`}
            className="mt-2 inline-block text-sm font-medium text-brand-800 underline decoration-brand-300 underline-offset-2 hover:text-brand-900"
          >
            {CONTACT_EMAIL}
          </a>
        </div>
      </section>
    </div>
  )
}