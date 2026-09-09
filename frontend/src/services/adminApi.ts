const BASE = import.meta.env.VITE_API_URL || ''

function getToken(): string | null {
  return localStorage.getItem('saksham-admin-token')
}

async function adminRequest<T>(
  path: string,
  options?: RequestInit,
  auth = true,
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }
  const res = await fetch(`${BASE}${path}`, { headers, ...options })
  if (res.status === 401 || res.status === 403) {
    localStorage.removeItem('saksham-admin-token')
  }
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
  return res.json() as Promise<T>
}

export interface AdminLoginResponse {
  access_token: string
  token_type: string
  username: string
  display_name: string
  role: string
}

export const adminApi = {
  login: (username: string, password: string) => {
    const body = new URLSearchParams()
    body.set('username', username)
    body.set('password', password)
    return adminRequest<AdminLoginResponse>('/api/admin/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    }, false)
  },
  dashboard: () => adminRequest<AdminDashboard>('/api/admin/dashboard'),
  schemes: {
    list: () => adminRequest<any[]>('/api/admin/schemes'),
    create: (data: any) => adminRequest<any>('/api/admin/schemes', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: any) => adminRequest<any>(`/api/admin/schemes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => adminRequest<any>(`/api/admin/schemes/${id}`, { method: 'DELETE' }),
  },
  partners: {
    list: () => adminRequest<any[]>('/api/admin/partners'),
    create: (data: any) => adminRequest<any>('/api/admin/partners', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: number, data: any) => adminRequest<any>(`/api/admin/partners/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: number) => adminRequest<any>(`/api/admin/partners/${id}`, { method: 'DELETE' }),
  },
  applications: () => adminRequest<any[]>('/api/admin/applications'),
  recommendations: () => adminRequest<any[]>('/api/admin/recommendations'),
}

export interface AdminDashboard {
  totals: {
    schemes: number
    active_schemes: number
    partners: number
    accepting_partners: number
    limited_partners: number
    unavailable_partners: number
    applications: number
    recommendations: number
    eligibility_checks: number
    events: number
  }
  by_type: { name: string; count: number }[]
  by_state: { state: string; count: number }[]
  by_partner_status: { status: string; count: number }[]
  by_application_state: { state: string; count: number }[]
  by_purpose: { purpose: string; count: number }[]
  by_scheme: { scheme: string; count: number }[]
  demo_mode: boolean
}

export function isAdminAuthed(): boolean {
  return !!getToken()
}