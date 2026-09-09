import type {
  ChatMessage,
  DocumentItem,
  LoanResult,
  Partner,
  PartnerRecommendResponse,
  Profile,
  RecommendationResult,
  ScoredPartner,
  Scheme,
} from '../types'

const BASE = import.meta.env.VITE_API_URL || ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  })
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

interface RawScoredPartner {
  partner: number
  partner_name: string
  partner_type: string
  state: string
  district: string
  city: string
  address: string
  latitude: number
  longitude: number
  status: string
  capacity_pct: number
  fund_utilization_pct: number
  npa_indicator: string
  phone: string
  email: string | null
  accepting_applications: boolean
  is_demo: boolean
  supported_schemes?: { id: number; name: string }[]
  breakdown: { scheme: number; distance: number; capacity: number; eligibility: number }
  total_score: number
  distance_km: number | null
  notes: string[]
}

interface RawPartnerRecommendResponse {
  weights: { eligibility: number; scheme: number; distance: number; capacity: number }
  results: RawScoredPartner[]
}

// ------- Public API -------
export const api = {
  schemes: {
    list: (params?: { purpose?: string; category?: string; search?: string }) => {
      const q = new URLSearchParams()
      if (params?.purpose) q.set('purpose', params.purpose)
      if (params?.category) q.set('category', params.category)
      if (params?.search) q.set('search', params.search)
      const qs = q.toString()
      return request<Scheme[]>(`/api/schemes${qs ? `?${qs}` : ''}`)
    },
    get: (id: number) => request<Scheme>(`/api/schemes/${id}`),
    documents: (id: number) => request<DocumentItem[]>(`/api/schemes/${id}/documents`),
  },
  partners: {
    list: (params?: Record<string, string | number | undefined>) => {
      const q = new URLSearchParams()
      for (const [k, v] of Object.entries(params || {})) {
        if (v !== undefined && v !== '' && v !== null) q.set(k, String(v))
      }
      const qs = q.toString()
      return request<Partner[]>(`/api/partners${qs ? `?${qs}` : ''}`)
    },
    get: (id: number) => request<Partner>(`/api/partners/${id}`),
  },
  eligibility: {
    check: (profile: Profile) =>
      request<{ check_id: number; accepted: boolean }>('/api/eligibility/check', {
        method: 'POST',
        body: JSON.stringify(profile),
      }),
  },
  recommendations: {
    get: (profile: Profile, schemeIds?: number[]) =>
      request<{ profile: Profile; results: RecommendationResult[] }>(
        '/api/recommendations',
        {
          method: 'POST',
          body: JSON.stringify({ profile, scheme_ids: schemeIds }),
        },
      ),
  },
  calculator: {
    emi: (payload: {
      principal: number
      annual_rate: number
      tenure: number
      tenure_unit: 'months' | 'years'
      moratorium_months?: number
      scheme_max_loan?: number
    }) =>
      request<LoanResult>('/api/calculator/emi', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
  partnersRecommend: {
    recommend: async (payload: {
      state?: string
      district?: string
      latitude?: number
      longitude?: number
      scheme_id?: number
      purpose?: string
      loan_amount?: number
      limit?: number
    }) => {
      const res = await request<RawPartnerRecommendResponse>('/api/partners/recommend', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      return {
        weights: res.weights,
        results: res.results.map((r): ScoredPartner => ({
          id: r.partner,
          name: r.partner_name,
          type: r.partner_type as ScoredPartner['type'],
          state: r.state,
          district: r.district,
          city: r.city,
          address: r.address,
          latitude: r.latitude,
          longitude: r.longitude,
          status: r.status as ScoredPartner['status'],
          capacity_pct: r.capacity_pct,
          fund_utilization_pct: r.fund_utilization_pct,
          npa_indicator: r.npa_indicator,
          phone: r.phone,
          email: r.email,
          accepting_applications: r.accepting_applications,
          is_demo: r.is_demo,
          scheme_slugs: [],
          supported_schemes: (r.supported_schemes || []).map((s) => ({ id: s.id, name: s.name, slug: '' })),
          breakdown: r.breakdown,
          total_score: r.total_score,
          distance_km: r.distance_km,
          notes: r.notes,
        })),
      }
    },
  },
  assistant: {
    chat: (payload: { message: string; language: string; history: ChatMessage[] }) =>
      request<{
        message: string
        language: string
        suggestions: { key: string; en: string; hi: string }[]
      }>('/api/assistant/chat', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
}

export type { Profile, RecommendationResult, ScoredPartner, Partner, Scheme, LoanResult }