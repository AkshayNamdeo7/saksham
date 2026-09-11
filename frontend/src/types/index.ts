export type Purpose = 'business' | 'self_employment' | 'education'

export type SchemeCategory =
  | 'micro_finance'
  | 'term_loan'
  | 'business'
  | 'education'
  | 'support'
  | 'sanitation_enterprise'

export type EligibilityStatus = 'eligible' | 'conditional' | 'not_eligible'

export interface SchemeInterestTier {
  loan_up_to?: number
  interest_rate: number
  channel?: string
  course_location?: string
}

export interface Scheme {
  id: number
  name: string
  slug: string
  description: string
  category: SchemeCategory
  purpose: Purpose
  max_loan: number
  min_loan: number
  interest_rate: number | null
  interest_rate_type?: string | null
  interest_tiers?: SchemeInterestTier[] | null
  interest_display?: string | null
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
  source_name: string | null
  source_url: string | null
  official_scheme_url: string | null
  official_apply_url: string | null
  last_verified: string | null
  source_type: string
  verification_status: string
  document_keys: string[]
  application_mode?: string | null
  finance_percentage?: number | null
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
  sub_category?: string
  purpose: Purpose
  match_score: number
  eligibility_status: EligibilityStatus
  max_loan: number
  min_loan?: number
  interest_rate: number | null
  interest_rate_type?: string | null
  interest_tiers?: SchemeInterestTier[] | null
  interest_display?: string | null
  tenure_months: number
  moratorium_months: number
  income_threshold: number | null
  project_min?: number | null
  project_max?: number | null
  finance_percentage?: number | null
  reasons: string[]
  matched: string[]
  unmatched: string[]
  warnings: string[]
  verification_items?: string[]
  next_steps?: string[]
  financing_summary?: string[]
  repayment_financing?: string[]
  recommendation_note?: string
  data_confidence?: string
  is_demo: boolean
  source_name?: string | null
  source_url?: string | null
  official_scheme_url?: string | null
  official_apply_url?: string | null
  last_verified?: string | null
  source_type?: string
  verification_status?: string
  application_mode?: string
  ai_explanation?: string
  hard_block?: boolean
  score_breakdown?: Record<string, number>
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
  structured?: AssistantSchemeCard[]
  step?: number
  totalSteps?: number
}

export interface AssistantSchemeCard {
  scheme_slug: string
  scheme_name: string
  match_score: number
  eligibility_status: string
  data_confidence: string
  max_loan: number | null
  interest_display: string | null
  official_scheme_url: string | null
  last_verified: string | null
  reasons: string[]
  is_loan: boolean
}

export interface AssistantResponse {
  message: string
  language: string
  suggestions: { key: string; en: string; hi: string }[]
  structured: AssistantSchemeCard[] | null
  step?: number | null
  total_steps?: number | null
}

export interface PartnerRecommendResponse {
  weights: { eligibility: number; scheme: number; distance: number; status: number }
  results: ScoredPartner[]
}