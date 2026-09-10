import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { CheckCircle2, ChevronLeft, ChevronRight, Wand2 } from 'lucide-react'
import { api } from '../services/api'
import { useProfile } from '../context/ProfileContext'
import type { Profile, Purpose } from '../types'
import ProgressStepper from '../components/common/ProgressStepper'
import { Field, Input, Select } from '../components/common/Inputs'
import Button from '../components/common/Button'
import { parseCurrencyInput, formatINR } from '../utils/format'

const STATES = [
  'Madhya Pradesh', 'Maharashtra', 'Uttar Pradesh', 'Bihar', 'Rajasthan', 'Haryana', 'Gujarat', 'Odisha', 'Chhattisgarh', 'West Bengal',
]

const DISTRICTS: Record<string, string[]> = {
  'Madhya Pradesh': ['Bhopal', 'Indore', 'Jabalpur', 'Gwalior', 'Ujjain', 'Sagar'],
  Maharashtra: ['Mumbai', 'Nagpur', 'Pune', 'Thane', 'Aurangabad'],
  'Uttar Pradesh': ['Lucknow', 'Kanpur', 'Varanasi', 'Agra', 'Prayagraj'],
  Bihar: ['Patna', 'Gaya', 'Muzaffarpur', 'Bhagalpur'],
  Rajasthan: ['Jaipur', 'Jodhpur', 'Udaipur', 'Kota'],
  Haryana: ['Chandigarh', 'Gurugram', 'Faridabad', 'Hisar'],
  Gujarat: ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot'],
  Odisha: ['Bhubaneswar', 'Cuttack', 'Rourkela'],
  Chhattisgarh: ['Raipur', 'Bilaspur', 'Durg'],
  'West Bengal': ['Kolkata', 'Howrah', 'Bardhaman'],
}

const PROJECT_TYPES = ['dairy', 'small_manufacturing', 'retail_shop', 'sewing/tailoring', 'auto/transport', 'food_processing', 'other']
const COURSE_TYPES = ['undergraduate', 'postgraduate', 'professional', 'vocational', 'diploma']
const EDUCATION_LEVELS = ['below_10th', '10th', '12th', 'graduate', 'post_graduate']

const STEPS = 6

interface LocalForm {
  age: number | ''
  annual_family_income: string
  requested_loan: string
  purpose: Purpose
  project_type: string
  project_cost: string
  education_level: string
  course_type: string
  education_cost: string
  state: string
  district: string
  city: string
}

const INITIAL_FORM: LocalForm = {
  age: '',
  annual_family_income: '',
  purpose: 'business',
  project_type: '',
  project_cost: '',
  education_level: '',
  course_type: '',
  education_cost: '',
  requested_loan: '',
  state: '',
  district: '',
  city: '',
}

export default function Eligibility() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { setProfileData } = useProfile()

  const [step, setStep] = useState(0)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<LocalForm>(INITIAL_FORM)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const purposes: { value: Purpose; label: string }[] = [
    { value: 'business', label: t('eligibility.purposeBusiness') },
    { value: 'self_employment', label: t('eligibility.purposeSelf') },
    { value: 'education', label: t('eligibility.purposeEducation') },
  ]

  const isEducation = form.purpose === 'education'

  function set<K extends keyof LocalForm>(key: K, value: LocalForm[K]) {
    setForm((f) => ({ ...f, [key]: value }))
    setErrors((e) => ({ ...e, [key]: '' }))
  }

  function validate(stepIndex: number): boolean {
    const nextErrors: Record<string, string> = {}
    if (stepIndex === 0) {
      const age = form.age
      if (age === '' || Number(age) < 18 || Number(age) > 100) nextErrors.age = 'Enter a valid age between 18 and 100.'
    }
    if (stepIndex === 1) {
      const income = parseCurrencyInput(form.annual_family_income)
      if (income === undefined || income < 0) nextErrors.annual_family_income = 'Enter a valid annual income in INR.'
    }
    if (stepIndex === 3) {
      if (isEducation) {
        if (!form.education_level) nextErrors.education_level = 'Select your education level.'
        if (!form.course_type) nextErrors.course_type = 'Select a course type.'
        const cost = parseCurrencyInput(form.education_cost)
        if (cost === undefined || cost <= 0) nextErrors.education_cost = 'Enter the estimated education cost.'
      } else {
        if (!form.project_type) nextErrors.project_type = 'Select a project type.'
        const cost = parseCurrencyInput(form.project_cost)
        if (cost === undefined || cost <= 0) nextErrors.project_cost = 'Enter the estimated project cost.'
      }
    }
    if (stepIndex === 4) {
      if (!form.state) nextErrors.state = 'Select a state.'
      if (!form.district) nextErrors.district = 'Select a district.'
      if (!form.city) nextErrors.city = 'Enter your city or village.'
    }
    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  function next() {
    if (!validate(step)) return
    setStep((s) => Math.min(s + 1, STEPS - 1))
  }

  function back() {
    setStep((s) => Math.max(s - 1, 0))
  }

  async function submit() {
    if (!validate(step)) return
    setSaving(true)
    try {
      const profile: Profile = {
        age: form.age === '' ? undefined : Number(form.age),
        state: form.state || undefined,
        district: form.district || undefined,
        city: form.city || undefined,
        annual_family_income: parseCurrencyInput(form.annual_family_income),
        purpose: form.purpose,
        project_type: isEducation ? undefined : form.project_type || undefined,
        project_cost: isEducation ? undefined : parseCurrencyInput(form.project_cost),
        education_level: isEducation ? form.education_level || undefined : undefined,
        course_type: isEducation ? form.course_type || undefined : undefined,
        education_cost: isEducation ? parseCurrencyInput(form.education_cost) : undefined,
        requested_loan:
          parseCurrencyInput(form.requested_loan) ||
          (isEducation ? parseCurrencyInput(form.education_cost) : parseCurrencyInput(form.project_cost)),
        language: (localStorage.getItem('saksham-lang') || 'en') as 'en' | 'hi',
      }
      await api.eligibility.check(profile)
      setProfileData(profile)
      expectsubmit(profile)
    } catch {
      /* handled by caller */
    } finally {
      setSaving(false)
    }
  }

  function expectsubmit(profile: Profile) {
    navigate('/recommendation', { state: { profile } })
  }

  function loadDemo() {
    setForm({
      age: 32,
      annual_family_income: '240000',
      purpose: 'business',
      project_type: 'small_manufacturing',
      project_cost: '120000',
      education_level: '',
      course_type: '',
      education_cost: '',
      requested_loan: '120000',
      state: 'Madhya Pradesh',
      district: 'Bhopal',
      city: 'Bhopal',
    })
    setErrors({})
  }

  const stepContent = useMemo(() => {
    switch (step) {
      case 0:
        return (
          <div className="space-y-4">
            <Field label={t('eligibility.age')} required id="age">
              <Input
                id="age"
                type="number"
                min={18}
                max={100}
                value={form.age}
                onChange={(e) => set('age', e.target.value === '' ? '' : Number(e.target.value))}
                placeholder="e.g. 32"
                error={!!errors.age}
              />
              {errors.age ? <p className="mt-1 text-xs text-red-600">{errors.age}</p> : null}
            </Field>
            <button onClick={loadDemo} className="inline-flex items-center gap-2 rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-xs font-medium text-brand-800 hover:bg-brand-100">
              <Wand2 className="h-3.5 w-3.5" aria-hidden />
              {t('eligibility.demoScenario')}
            </button>
            <p className="text-xs text-slate-400">{t('eligibility.demoScenarioDesc')}</p>
          </div>
        )
      case 1:
        return (
          <div className="space-y-4">
            <Field label={`${t('eligibility.annualIncome')} (INR)`} required id="income" hint="e.g. 240000 = ₹2,40,000">
              <Input
                id="income"
                value={form.annual_family_income}
                onChange={(e) => set('annual_family_income', e.target.value)}
                placeholder="240000"
                inputMode="numeric"
                error={!!errors.annual_family_income}
              />
            </Field>
            <Field label={t('eligibility.requestedLoan')} id="loan" hint="Optional">
              <Input
                id="loan"
                value={form.requested_loan}
                onChange={(e) => set('requested_loan', e.target.value)}
                placeholder="120000"
                inputMode="numeric"
              />
            </Field>
          </div>
        )
      case 2:
        return (
          <div role="radiogroup" aria-label={t('eligibility.purpose')}>
            <p className="label">{t('eligibility.purpose')}</p>
            <div className="grid gap-3 sm:grid-cols-3">
              {purposes.map((p) => (
                <button
                  key={p.value}
                  onClick={() => set('purpose', p.value)}
                  aria-checked={form.purpose === p.value}
                  role="radio"
                  className={`rounded-xl border-2 p-4 text-left transition ${
                    form.purpose === p.value
                      ? 'border-brand-600 bg-brand-50'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <span className="block text-sm font-bold text-slate-900">{p.label}</span>
                  <span className="mt-0.5 block text-xs text-slate-500">
                    {p.value === 'education' ? 'Courses & college fees' : 'Income-generating activity'}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )
      case 3:
        return isEducation ? (
          <div className="space-y-4">
            <Field label={t('eligibility.educationLevel')} required id="edu_level">
              <Select
                id="edu_level"
                value={form.education_level}
                onChange={(e) => set('education_level', e.target.value)}
                placeholder="Select…"
                options={EDUCATION_LEVELS.map((v) => ({ value: v, label: v.replace(/_/g, ' ') }))}
                error={!!errors.education_level}
              />
            </Field>
            <Field label={t('eligibility.courseType')} required id="course">
              <Select
                id="course"
                value={form.course_type}
                onChange={(e) => set('course_type', e.target.value)}
                placeholder="Select…"
                options={COURSE_TYPES.map((v) => ({ value: v, label: v.replace(/_/g, ' ') }))}
                error={!!errors.course_type}
              />
            </Field>
            <Field label={`${t('eligibility.educationCost')} (INR)`} required id="edu_cost">
              <Input
                id="edu_cost"
                value={form.education_cost}
                onChange={(e) => set('education_cost', e.target.value)}
                placeholder="400000"
                inputMode="numeric"
                error={!!errors.education_cost}
              />
            </Field>
          </div>
        ) : (
          <div className="space-y-4">
            <Field label={t('eligibility.projectType')} required id="ptype">
              <Select
                id="ptype"
                value={form.project_type}
                onChange={(e) => set('project_type', e.target.value)}
                placeholder="Select…"
                options={PROJECT_TYPES.map((v) => ({ value: v, label: v.replace(/_/g, ' ') }))}
                error={!!errors.project_type}
              />
            </Field>
            <Field label={`${t('eligibility.projectCost')} (INR)`} required id="pcost">
              <Input
                id="pcost"
                value={form.project_cost}
                onChange={(e) => set('project_cost', e.target.value)}
                placeholder="120000"
                inputMode="numeric"
                error={!!errors.project_cost}
              />
            </Field>
          </div>
        )
      case 4:
        return (
          <div className="space-y-4">
            <Field label={t('eligibility.state')} required id="state">
              <Select
                id="state"
                value={form.state}
                onChange={(e) => {
                  set('state', e.target.value)
                  set('district', '')
                }}
                placeholder="Select state…"
                options={STATES.map((v) => ({ value: v, label: v }))}
                error={!!errors.state}
              />
            </Field>
            <Field label={t('eligibility.district')} required id="district">
              <Select
                id="district"
                value={form.district}
                onChange={(e) => set('district', e.target.value)}
                placeholder="Select district…"
                options={(DISTRICTS[form.state || ''] || []).map((v) => ({ value: v, label: v }))}
                disabled={!form.state}
                error={!!errors.district}
              />
            </Field>
            <Field label={t('eligibility.city')} required id="city">
              <Input
                id="city"
                value={form.city}
                onChange={(e) => set('city', e.target.value)}
                placeholder="e.g. Bhopal"
                error={!!errors.city}
              />
            </Field>
          </div>
        )
      case 5:
        return (
          <div className="space-y-1">
            <p className="flex items-start gap-2 text-sm text-slate-500">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden />
              {t('eligibility.reviewDesc')}
            </p>
            <div className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-200">
              {[
                { label: t('eligibility.age'), value: form.age === '' ? '—' : `${form.age} years` },
                { label: t('eligibility.annualIncome'), value: formatINR(parseCurrencyInput(form.annual_family_income) || 0) },
                { label: t('eligibility.requestedLoan'), value: parseCurrencyInput(form.requested_loan) ? formatINR(parseCurrencyInput(form.requested_loan)) : `${t('common.notProvided')} (optional)` },
                { label: t('eligibility.purpose'), value: t(`eligibility.purpose${String(form.purpose).charAt(0).toUpperCase()}${String(form.purpose).slice(1)}`) },
                ...(isEducation
                  ? [
                      { label: t('eligibility.educationLevel'), value: form.education_level || '—' },
                      { label: t('eligibility.courseType'), value: form.course_type || '—' },
                      { label: t('eligibility.educationCost'), value: formatINR(parseCurrencyInput(form.education_cost) || 0) },
                    ]
                  : [
                      { label: t('eligibility.projectType'), value: form.project_type || '—' },
                      { label: t('eligibility.projectCost'), value: formatINR(parseCurrencyInput(form.project_cost) || 0) },
                    ]),
                { label: `${t('eligibility.state')} / ${t('eligibility.district')} / ${t('eligibility.city')}`, value: [form.state, form.district, form.city].filter(Boolean).join(' · ') || '—' },
              ].map((row) => (
                <div key={row.label} className="flex items-start justify-between gap-4 px-4 py-3">
                  <span className="text-sm text-slate-500">{row.label}</span>
                  <span className="tnum text-right text-sm font-semibold capitalize text-slate-900">{row.value}</span>
                </div>
              ))}
            </div>
            <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
              {t('common.officialVerify')} · {t('common.demoNotice')}
            </p>
          </div>
        )
      default:
        return null
    }
  }, [step, form, errors, isEducation, t]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="container-app max-w-3xl py-12">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{t('eligibility.title')}</h1>
        <p className="mt-2 text-slate-500">{t('eligibility.subtitle')}</p>
      </div>

      <div className="mt-8">
        <ProgressStepper
          steps={[t('eligibility.step1'), t('eligibility.step2'), t('eligibility.step3'), t('eligibility.step4'), t('eligibility.step5'), t('eligibility.step6')]}
          current={step}
        />
      </div>

      <div className="card mt-8 p-6 sm:p-8">
        {stepContent}

        <div className="mt-8 flex items-center justify-between border-t border-slate-100 pt-5">
          <Button variant="ghost" onClick={back} disabled={step === 0}>
            <ChevronLeft className="h-4 w-4" aria-hidden />
            {t('common.back')}
          </Button>
          {step < STEPS - 1 ? (
            <Button onClick={next}>
              {t('common.next')}
              <ChevronRight className="h-4 w-4" aria-hidden />
            </Button>
          ) : (
            <Button onClick={submit} loading={saving}>
              {t('eligibility.start')}
              <ChevronRight className="h-4 w-4" aria-hidden />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}