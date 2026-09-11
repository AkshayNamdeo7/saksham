import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  ArrowRight,
  Calculator,
  CheckCircle2,
  Compass,
  GraduationCap,
  Handshake,
  Languages,
  MapPin,
  MessagesSquare,
  Scale,
  ShieldCheck,
  Store,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import { formatLakh, formatPercent, tenureLabel } from '../utils/format'
import SchemeCard from '../components/cards/SchemeCard'

export default function Home() {
  const { t } = useTranslation()
  const { data: schemes, loading, error, reload } = useFetch(() => api.schemes.list(), [])

  const journey = [
    { icon: <Wallet className="h-5 w-5" />, title: t('home.step1'), desc: 'Share basic details in a short guided check.' },
    { icon: <CheckCircle2 className="h-5 w-5" />, title: t('home.step2'), desc: 'A transparent engine matches suitable schemes.' },
    { icon: <Calculator className="h-5 w-5" />, title: t('home.step3'), desc: 'Estimate EMI, tenure and total repayment.' },
    { icon: <MapPin className="h-5 w-5" />, title: t('home.step4'), desc: 'Find an eligible nearby channel partner.' },
    { icon: <MessagesSquare className="h-5 w-5" />, title: t('home.step5'), desc: 'Know which documents to carry and what to do next.' },
  ]

  const features = [
    { icon: <Scale className="h-5 w-5" />, title: t('home.feat1'), desc: t('home.feat1Desc') },
    { icon: <Calculator className="h-5 w-5" />, title: t('home.feat2'), desc: t('home.feat2Desc') },
    { icon: <Handshake className="h-5 w-5" />, title: t('home.feat3'), desc: t('home.feat3Desc') },
    { icon: <Compass className="h-5 w-5" />, title: t('home.feat4'), desc: t('home.feat4Desc') },
    { icon: <Languages className="h-5 w-5" />, title: t('home.feat5'), desc: t('home.feat5Desc') },
  ]

  const categories = [
    { icon: <Store className="h-5 w-5" />, label: t('home.catMicro'), desc: 'Small projects, typically up to a ₹1.4 lakh band' },
    { icon: <TrendingUp className="h-5 w-5" />, label: t('home.catTerm'), desc: 'Larger expansion, up to ₹50 lakh' },
    { icon: <GraduationCap className="h-5 w-5" />, label: t('home.catEdu'), desc: 'Education loans for courses and colleges' },
    { icon: <ShieldCheck className="h-5 w-5" />, label: t('home.catSelf'), desc: 'Self-employment and skill-to-enterprise' },
  ]

  const faqs = [
    { q: 'Do I need to login to check eligibility?', a: 'No. The public eligibility flow works without any login.' },
    { q: 'Are these figures official?', a: 'Saksham shows sourced scheme information and links every scheme to its official source. Always verify figures against the latest official guidelines before applying.' },
    { q: 'What makes a recommendation?', a: 'A deterministic rule engine scoring purpose, income, project size and loan limits, then a plain-language explanation.' },
  ]

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-navy text-white">
        <div className="pointer-events-none absolute inset-0 opacity-20" style={{ background: 'radial-gradient(600px 300px at 20% 10%, #3b82f6 0%, transparent 60%), radial-gradient(500px 280px at 85% 20%, #10b981 0%, transparent 60%)' }} />
        <div className="container-app relative grid items-center gap-12 py-16 lg:grid-cols-[1.05fr_1fr] lg:py-24">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-300" aria-hidden />
              {t('brand.tagline')}
            </span>
            <h1 className="mt-5 text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl">
              {t('home.heroTitle')}
            </h1>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-slate-300 sm:text-lg">
              {t('home.heroSubtitle')}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/eligibility" className="btn bg-white text-navy hover:bg-slate-100">
                {t('home.ctaCheck')}
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
              <Link to="/schemes" className="btn border border-white/25 bg-transparent text-white hover:bg-white/10">
                {t('home.ctaExplore')}
              </Link>
            </div>
            <div className="mt-6 flex items-center gap-2 text-xs text-slate-400">
              <ShieldCheck className="h-4 w-4 text-emerald-300" aria-hidden />
              <span>Verified source data — always confirm against official guidelines.</span>
            </div>
          </div>

          {/* Preview */}
          <div className="relative">
            <div className="rounded-2xl border border-white/10 bg-white/95 p-5 shadow-2xl backdrop-blur">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <p className="text-sm font-semibold text-slate-900">Your match, at a glance</p>
                <span className="badge-green">Eligible</span>
              </div>
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3.5 py-3">
                  <span className="text-xs text-slate-500">Best scheme</span>
                  <span className="text-sm font-bold text-navy">Micro Finance Scheme</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3.5 py-3">
                  <span className="text-xs text-slate-500">Match score</span>
                  <span className="text-sm font-bold text-emerald-700">92%</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3.5 py-3">
                  <span className="text-xs text-slate-500">Estimated EMI</span>
                  <span className="tnum text-sm font-bold text-slate-900">₹4,024 / mo</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3.5 py-3">
                  <span className="text-xs text-slate-500">Channel partner</span>
                  <span className="text-sm font-bold text-slate-900">Eligible nearby partner</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Journey */}
      <section className="container-app py-16">
        <div className="text-center">
          <h2 className="section-title">{t('home.journeyTitle')}</h2>
          <p className="section-sub">{t('home.journeySubtitle')}</p>
        </div>
        <ol className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {journey.map((s, i) => (
            <li key={s.title} className="card card-hover relative p-5">
              <span className="absolute right-4 top-4 text-3xl font-extrabold text-slate-100">{i + 1}</span>
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                {s.icon}
              </span>
              <h3 className="mt-3 text-sm font-bold text-slate-900">{s.title}</h3>
              <p className="mt-1 text-xs leading-relaxed text-slate-500">{s.desc}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Why Saksham */}
      <section className="bg-white py-16">
        <div className="container-app">
          <div className="grid gap-6 lg:grid-cols-5">
            <div className="lg:col-span-2">
              <h2 className="section-title">{t('home.whyTitle')}</h2>
              <p className="section-sub">{t('home.whySubtitle')}</p>
              <div className="mt-6 rounded-2xl bg-navy p-5 text-white">
                <h3 className="text-lg font-bold">{t('home.impactTitle')}</h3>
                <p className="mt-1 text-sm text-slate-300">{t('home.impactDesc')}</p>
                <ul className="mt-4 space-y-2 text-xs">
                  {['Better awareness', 'Less confusion', 'Better routing', 'Faster next steps'].map((x) => (
                    <li key={x} className="flex items-center gap-2">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" aria-hidden />
                      {x}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:col-span-3">
              {features.map((f) => (
                <div key={f.title} className="card card-hover p-5">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">{f.icon}</span>
                  <h3 className="mt-3 text-sm font-bold text-slate-900">{f.title}</h3>
                  <p className="mt-1 text-sm text-slate-500">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Scheme categories */}
      <section className="container-app py-16">
        <div className="text-center">
          <h2 className="section-title">{t('home.categoriesTitle')}</h2>
          <p className="section-sub">{t('home.categoriesSubtitle')}</p>
        </div>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {categories.map((c) => (
            <div key={c.label} className="card card-hover p-5 text-center">
              <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">{c.icon}</span>
              <h3 className="mt-3 text-sm font-bold text-slate-900">{c.label}</h3>
              <p className="mt-1 text-xs text-slate-500">{c.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Featured schemes */}
      <section className="bg-white py-16">
        <div className="container-app">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="section-title">Popular schemes</h2>
              <p className="section-sub">A look at the schemes available on Saksham.</p>
            </div>
            <Link to="/schemes" className="btn-secondary">
              {t('home.ctaExplore')}
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          </div>
          {loading && <p className="py-10 text-center text-slate-400">Loading schemes…</p>}
          {error && (
            <div className="py-10 text-center text-red-600">
              Unable to load schemes.{' '}
              <button onClick={reload} className="underline">Retry</button>
            </div>
          )}
          {!loading && !error && (
            <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {(schemes || []).slice(0, 4).map((s) => (
                <SchemeCard key={s.id} scheme={s} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Financial literacy */}
      <section className="container-app py-16">
        <div className="text-center">
          <h2 className="section-title">{t('home.literacyTitle')}</h2>
          <p className="section-sub">{t('home.literacySubtitle')}</p>
        </div>
        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {[
            { term: 'EMI', def: 'Equal Monthly Installment — the fixed amount you repay every month, including a part of the principal and interest.' },
            { term: 'Moratorium', def: 'A period when repayment may be paused (e.g., during a course). Interest treatment varies by scheme.' },
            { term: 'Channel Partner', def: 'An agency such as a state corporation or bank that processes applications and disburses the loan.' },
          ].map((x) => (
            <div key={x.term} className="card p-6">
              <h3 className="text-base font-bold text-brand-800">{x.term}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{x.def}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="bg-white py-16">
        <div className="container-app max-w-3xl">
          <h2 className="section-title text-center">{t('home.faqTitle')}</h2>
          <div className="mt-8 space-y-3">
            {faqs.map((f) => (
              <details key={f.q} className="card group p-5">
                <summary className="cursor-pointer list-none text-sm font-semibold text-slate-900">
                  <span className="inline-block w-2 transition group-open:rotate-90">›</span> {f.q}
                </summary>
                <p className="mt-2 pl-5 text-sm text-slate-500">{f.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="container-app py-16">
        <div className="rounded-3xl bg-gradient-to-br from-navy to-brand-900 px-6 py-14 text-center text-white">
          <h2 className="text-2xl font-bold sm:text-3xl">{t('home.finalCta')}</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-slate-300">{t('home.finalCtaDesc')}</p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link to="/eligibility" className="btn bg-white text-navy hover:bg-slate-100">{t('home.ctaCheck')}</Link>
            <Link to="/assistant" className="btn border border-white/25 bg-transparent text-white hover:bg-white/10">{t('assistant.title')}</Link>
          </div>
        </div>
      </section>
    </div>
  )
}