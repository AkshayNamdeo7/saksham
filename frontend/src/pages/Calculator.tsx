import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'
import { AlertTriangle, Calculator as CalcIcon } from 'lucide-react'
import { Field, Input, Select } from '../components/common/Inputs'
import Button from '../components/common/Button'
import { api } from '../services/api'
import { useFetch } from '../hooks/useFetch'
import type { LoanResult } from '../types'
import DemoBadge from '../components/common/DemoBadge'

export default function Calculator() {
  const { t } = useTranslation()
  const [params] = useSearchParams()
  const schemeId = params.get('scheme')

  const { data: schemes } = useFetch(() => api.schemes.list(), [])
  const scheme = schemes?.find((s) => s.id === Number(schemeId)) || null

  const [principal, setPrincipal] = useState(scheme ? Math.min(scheme.max_loan, 140000) : 120000)
  const [rate, setRate] = useState(scheme ? scheme.interest_rate : 4.0)
  const [tenure, setTenure] = useState(scheme ? scheme.tenure_months : 36)
  const [tenureUnit, setTenureUnit] = useState<'months' | 'years'>('months')
  const [moratorium, setMoratorium] = useState(scheme ? scheme.moratorium_months : 0)
  const [result, setResult] = useState<LoanResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (scheme) {
      setRate(scheme.interest_rate)
      setMoratorium(scheme.moratorium_months)
      setTenure(scheme.tenure_months)
    }
  }, [scheme])

  async function calc() {
    if (!principal || principal <= 0 || rate < 0 || !tenure || tenure <= 0) {
      setError('Enter valid positive values first.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await api.calculator.emi({
        principal,
        annual_rate: rate,
        tenure,
        tenure_unit: tenureUnit,
        moratorium_months: moratorium,
        scheme_max_loan: scheme ? scheme.max_loan : undefined,
      })
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Calculation failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    calc()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const pieData = useMemo(() => {
    if (!result) return []
    return [
      { name: 'Principal', value: result.principal },
      { name: 'Interest', value: Math.max(0, result.total_interest) },
    ]
  }, [result])

  const overLimit = result?.warnings?.some((w) => w.includes('exceeds')) || false

  return (
    <div className="container-app max-w-6xl py-12">
      {scheme && (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-brand-50 px-4 py-3">
          <p className="text-sm text-brand-900">
            {t('calculator.calcFromScheme', { name: scheme.name })} · {t('recommendation.indicative')}
          </p>
          <DemoBadge subtle />
        </div>
      )}

      <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('calculator.title')}</h1>
      <p className="mt-2 text-slate-500">{t('calculator.subtitle')}</p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[380px_1fr]">
        <div className="card h-fit p-6">
          <div className="space-y-4">
            <Field label={`${t('calculator.loanAmount')} (INR)`} required>
              <Input
                type="number"
                min={0}
                value={principal}
                onChange={(e) => setPrincipal(Number(e.target.value))}
                placeholder="120000"
              />
            </Field>
            <Field label={`${t('calculator.annualRate')}`} required>
              <Input
                type="number"
                min={0}
                max={50}
                step={0.25}
                value={rate}
                onChange={(e) => setRate(Number(e.target.value))}
                placeholder="4.0"
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label={t('calculator.tenure')} required>
                <Input
                  type="number"
                  min={1}
                  value={tenure}
                  onChange={(e) => setTenure(Number(e.target.value))}
                />
              </Field>
              <Field label={t('calculator.tenureUnit')} required>
                <Select
                  value={tenureUnit}
                  onChange={(e) => setTenureUnit(e.target.value as 'months' | 'years')}
                  options={[
                    { value: 'years', label: t('calculator.years') },
                    { value: 'months', label: t('calculator.months') },
                  ]}
                />
              </Field>
            </div>
            <Field label={t('calculator.moratorium')} hint={t('calculator.moratoriumNote')}>
              <Input
                type="number"
                min={0}
                max={60}
                value={moratorium}
                onChange={(e) => setMoratorium(Number(e.target.value))}
              />
            </Field>
            <Button onClick={calc} loading={loading} fullWidth>
              <CalcIcon className="h-4 w-4" aria-hidden />
              Calculate
            </Button>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        </div>

        <div className="space-y-6">
          {overLimit && result && (
            <div className="flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden />
              <div>
                <p className="font-semibold">{t('calculator.warningOverLimit')}</p>
                <p className="mt-0.5 text-amber-700">{result.warnings[0]}</p>
              </div>
            </div>
          )}

          {!result && !loading && (
            <div className="card flex items-center justify-center p-16 text-slate-400">—</div>
          )}

          {result && (
            <>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  { label: t('calculator.emi'), value: `₹${result.emi.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`, sub: '/ month' },
                  { label: t('calculator.totalInterest'), value: `₹${result.total_interest.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
                  { label: t('calculator.totalRepayment'), value: `₹${result.total_repayment.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
                  { label: 'Tenure', value: `${result.tenure_months} months` },
                ].map((x) => (
                  <div key={x.label} className="card p-5">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400">{x.label}</p>
                    <p className="tnum mt-1 text-lg font-bold text-slate-900">{x.value}</p>
                    {x.sub && <p className="text-xs text-slate-400">{x.sub}</p>}
                  </div>
                ))}
              </div>

              <div className="card p-6">
                <h2 className="text-base font-bold text-slate-900">{t('calculator.breakdown')}</h2>
                <div className="mt-4 flex flex-col items-center gap-6 sm:flex-row">
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3}>
                        <Cell fill="#0b2545" />
                        <Cell fill="#60a5fa" />
                      </Pie>
                      <Tooltip formatter={(v: any) => `₹${Number(v).toLocaleString('en-IN')}`} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full bg-navy" />
                      <span>{t('calculator.principal')}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full bg-[#60a5fa]" />
                      <span>{t('calculator.totalInterest')}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <h2 className="text-base font-bold text-slate-900">{t('calculator.timeline')}</h2>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={result.timeline} margin={{ top: 16 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v: any) => `₹${Number(v).toLocaleString('en-IN')}`} />
                    <Bar dataKey="principal" stackId="a" fill="#0b2545" name="Principal" />
                    <Bar dataKey="interest" stackId="a" fill="#60a5fa" name="Interest" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}