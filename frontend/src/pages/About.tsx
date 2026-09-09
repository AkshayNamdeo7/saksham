import { useTranslation } from 'react-i18next'
import {
  BadgeCheck,
  Eye,
  FlaskConical,
  Languages,
  Library,
  ShieldCheck,
} from 'lucide-react'
import DemoBadge from '../components/common/DemoBadge'

export default function About() {
  const { t } = useTranslation()
  return (
    <div className="container-app max-w-4xl py-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('about.title')}</h1>
        <p className="mt-2 text-slate-500">{t('about.subtitle')}</p>
        <div className="mt-3 flex justify-center"><DemoBadge /></div>
      </div>

      <section className="card mt-10 p-6">
        <h2 className="text-base font-bold text-slate-900">What this platform does</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          Saksham helps eligible marginalized / SC beneficiaries discover suitable concessional
          financial assistance or educational loan schemes, understand eligibility, estimate
          repayment, locate suitable channel partners, and receive an intelligent
          application-routing recommendation.
        </p>
      </section>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {[
          { icon: Eye, title: 'Transparent matching', desc: 'Every recommendation shows which criteria matched and why, with a clear match score.' },
          { icon: ShieldCheck, title: 'Deterministic finance', desc: 'EMI, interest and repayment values come from exact calculation code — never AI guesses.' },
          { icon: Languages, title: 'Bilingual', desc: 'English and Hindi supported across the platform, including the assistant.' },
          { icon: FlaskConical, title: 'Prototype data', desc: 'All schemes, partners and statuses are demo data marked clearly as non-official.' },
        ].map((x) => (
          <div key={x.title} className="card p-5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
              <x.icon className="h-5 w-5" aria-hidden />
            </span>
            <h3 className="mt-3 text-sm font-bold text-slate-900">{x.title}</h3>
            <p className="mt-1 text-sm text-slate-500">{x.desc}</p>
          </div>
        ))}
      </div>

      <section className="card mt-6 p-6">
        <h2 className="text-base font-bold text-slate-900">Architecture</h2>
        <div className="mt-3 space-y-1.5 text-sm text-slate-600">
          <p>User input → Deterministic recommendation engine → Verified recommendation → AI explanation → User-friendly output.</p>
          <p>The AI explains results — it never changes the deterministic eligibility outcome.</p>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {[
            { label: 'Frontend', value: 'React · Vite · TypeScript · Tailwind' },
            { label: 'Backend', value: 'Python · FastAPI · SQLAlchemy' },
            { label: 'Data', value: 'SQLite (local) → PostgreSQL ready' },
          ].map((x) => (
            <div key={x.label} className="rounded-xl bg-slate-50 p-4">
              <p className="text-[11px] uppercase tracking-wide text-slate-400">{x.label}</p>
              <p className="mt-1 text-sm font-medium text-slate-800">{x.value}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="card mt-6 flex items-start gap-3 border-amber-200 bg-amber-50 p-5">
        <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" aria-hidden />
        <p className="text-sm text-amber-800">{t('common.demoNotice')} No government ownership or endorsement is implied.</p>
      </div>
    </div>
  )
}