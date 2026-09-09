export type Purpose = 'business' | 'self_employment' | 'education'

export type SchemeCategory = 'micro_finance' | 'term_loan' | 'education'

export type EligibilityStatus = 'eligible' | 'conditional' | 'not_eligible'

export interface Scheme {
  id: number
  name: string
  slug: string
  description: string
  category: SchemeCategory
  purpose: Purpose
  max_loan: number
  min_loan: number
  interest_rate: number
  tenure_months: number
  moratorium_months: number
  income_threshold: number | null
  project_min: number | null
  project_max: number | null
  education_focus: boolean
  eligibility_notes: string
  required_documents: string
  partner_required: boolean
  active: boolean
  is_demo: boolean
  document_keys: string[]
  rules?: { key: string; value: string; description: string }[]
  supported_partners?: {
    id: number
    name: string
    type: string
    state: string
    district: string
    city: string
    status: string
  }[]
}

export interface DocumentItem {
  id: number
  key: string
  name: string
  name_hi: string | null
  description: string
  is_required: boolean
  applies_to: string
}

export type PartnerStatus = 'accepting' | 'limited' | 'unavailable'

export interface Partner {
  id: number
  name: string
  type: 'SCA' | 'PSB' | 'RRB' | 'NBFC-MFI'
  state: string
  district: string
  city: string
  address: string
  latitude: number
  longitude: number
  status: PartnerStatus
  capacity_pct: number
  fund_utilization_pct: number
  npa_indicator: string
  phone: string
  email: string | null
  accepting_applications: boolean
  is_demo: boolean
  scheme_slugs: string[]
  supported_schemes?: { id: number; name: string; slug: string }[]
}

export interface RecommendationResult {
  scheme_id: number
  scheme_name: string
  scheme_slug: string
  category: SchemeCategory
  purpose: Purpose
  match_score: number
  eligibility_status: EligibilityStatus
  max_loan: number
  interest_rate: number
  tenure_months: number
  moratorium_months: number
  income_threshold: number | null
  reasons: string[]
  matched: string[]
  unmatched: string[]
  warnings: string[]
  next_steps: string[]
  is_demo: boolean
  ai_explanation?: string
  hard_block?: boolean
}

export interface Profile {
  age?: number
  state?: string
  district?: string
  city?: string
  annual_family_income?: number
  purpose: Purpose
  project_type?: string
  project_cost?: number
  education_level?: string
  course_type?: string
  institution_type?: string
  education_cost?: number
  requested_loan?: number
  language?: string
}

export interface LoanResult {
  principal: number
  annual_rate: number
  tenure_months: number
  tenure_unit: string
  moratorium_months: number
  emi: number
  total_interest: number
  total_repayment: number
  total_payments: number
  effective_annual_rate: number
  warnings: string[]
  timeline: { period: string; principal: number; interest: number; balance: number }[]
}

export interface ScoredPartner extends Partner {
  breakdown: { scheme: number; distance: number; capacity: number; eligibility: number }
  total_score: number
  distance_km: number | null
  notes: string[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface PartnerRecommendResponse {
  weights: { eligibility: number; scheme: number; distance: number; status: number }
  results: ScoredPartner[]
}