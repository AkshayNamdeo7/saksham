# Saksham — Scheme Matching Platform for Marginalized Entrepreneurs

A full-stack platform that helps marginalized / SC beneficiaries discover suitable concessional financial-assistance and education-loan schemes, understand eligibility, estimate repayment, locate eligible channel partners, and get transparent application-routing guidance.

> **Prototype.** Scheme figures, partner availability, document lists and demo scenarios are partial/sample data. The official scheme catalog is imported from curated government sources (NSFDC, NSKFDC, NBCFDC, PM-DAKSH, PM-AJAY) at first bootstrap. Forecasted loan amounts, interest rates and eligibility thresholds should always be verified against the latest official guidelines before applying.

## SIH Problem Statement

Many marginalized and SC/ST entrepreneurs and students are unaware of the concessional loan, subsidy, and education-loan schemes they are eligible for, and even when they are aware, they struggle to understand eligibility, compare options, estimate repayment, locate the right channel partner, and prepare the correct documents. Information is fragmented across agencies, criteria are complex, and guidance is rarely available in an accessible, bilingual, and transparent way.

**Saksham** addresses this gap with a guided, explainable digital assistant that:
1. Collects a simple profile (category, income, purpose, project/course, location).
2. Deterministically shortlists eligible schemes with a transparent match score and reasons.
3. Provides an EMI/repayment estimator with a warning when a requested amount exceeds a scheme limit.
4. Routes the user to the most suitable eligible channel partner using weighted, explainable scoring.
5. Lists per-scheme document checklists and an end-to-end application path.
6. Offers English + हिंदी support with an AI assistant that never alters the deterministic outcomes.

---

## Features

- **Guided eligibility flow** — short multi-step form (age, family income, purpose, project/course, location) with demo-scenario autofill.
- **Transparent recommendation engine** — every scheme result shows a match score plus the exact matched/unmatched criteria and next steps.
- **Deterministic EMI calculator** — interest, EMI, total repayment and timeline buckets are computed by calculation code only (AI never guesses financial figures). Moratorium option included.
- **Partner locator** — weighted routing (eligibility 40, scheme 30, distance 20, capacity/status 10), OpenStreetMap markers colored by status, distance + Google-Maps directions, per-partner score breakdown.
- **Document checklists** — per-scheme required/optional documents.
- **Application guidance** — recommended end-to-end path (scheme → requirement → partner → documents → next step) plus a downloadable summary.
- **AI assistant** — intent-based chat in English and Hindi with deterministic fallback; AI explains but never changes results.
- **Admin console** — JWT-protected dashboard with demo analytics, scheme CRUD, partner CRUD, and applications/recommendations tables.
- **Bilingual (EN / हिंदी)** — persisted language choice across the platform.

## Tech stack

- **Frontend:** React 18 · Vite · TypeScript · Tailwind CSS · React Router · react-leaflet (OSM) · recharts · i18next · lucide-react
- **Backend:** Python 3 · FastAPI · SQLAlchemy · PostgreSQL (Neon) via `psycopg2` · python-jose + bcrypt (JWT admin auth)
- **Hosting:** Vercel — static React app + a FastAPI service; SPA rewrites keep deep links served by the frontend while `/api/*` is routed to the API service
- **Database:** Neon PostgreSQL (serverless, connection-pooled, `sslmode=require`)
- **Testing:** pytest (HTTP + business-logic tests)

## Architecture

```
Browser
  │
  ├── /            → Vercel Service "web"   (frontend/ — React SPA, framework: vite)
  └── /api/*       → Vercel Service "api"   (backend/ — FastAPI, entrypoint: app.main:app)
                        │
                        └── DATABASE_URL  → Neon PostgreSQL (serverless)
```

`vercel.json` defines two Vercel Services and a catch-all rewrite that sends `/api/:path*` to the API service and everything else to the SPA, so a refresh of `/assistant`, `/schemes` etc. never returns 404.

## Repository layout

```
saksham/
├── vercel.json             # Vercel services (web + api) and rewrites
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, routes, non-fatal startup provisioning
│   │   ├── api/
│   │   │   ├── deps.py          # get_current_admin (JWT)
│   │   │   └── routes/          # schemes, partners, eligibility, recommendations,
│   │   │                        # calculator, partner_routing, assistant, admin_*
│   │   ├── core/                # config, security
│   │   ├── db/
│   │   │   ├── init_db.py       # idempotent bootstrap: schema + official data import
│   │   │   ├── session.py       # engine + get_db (lazy provisioning + connect timeout)
│   │   │   └── seed.py          # demo seed data + admin user
│   │   ├── models/              # SQLAlchemy models
│   │   ├── repositories/        # query helpers
│   │   ├── schemas/             # Pydantic contracts
│   │   └── services/            # recommendation_engine, calculator, partner_routing,
│   │                            # ai_service, assistant_handler, scheme_import
│   ├── tests/                   # pytest suite
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # public pages + pages/admin/*
│   │   ├── components/          # layout, cards, map, assistant, common
│   │   ├── context/ProfileContext.tsx   # persisted journey state
│   │   ├── services/api.ts      # typed API client (relative /api/*, env-overridable)
│   │   ├── services/adminApi.ts # admin API client
│   │   ├── hooks/, utils/, i18n/, types/
│   │   └── App.tsx              # lazy route registry
│   ├── vite.config.ts           # port 5173, /api → localhost:8000 proxy
│   └── package.json
└── README.md
```

## Getting started (local development)

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

`DATABASE_URL` in `backend/.env` is **required**. Locally you can point it at any PostgreSQL instance, or use SQLite for a quick prototype:

```ini
DATABASE_URL=sqlite:///./saksham.db        # local prototype only
# DATABASE_URL=postgresql://user:pass@host:5432/saksham?sslmode=require   # PostgreSQL / Neon
```

The API runs at `http://localhost:8000`. On first start the schema is created and the database is provisioned idempotently: if no official scheme exists, the curated official catalog (NSFDC, NSKFDC, NBCFDC, PM-DAKSH, PM-AJAY — ~20 records) is imported, then the demo seed (extra schemes, documents, partners, admin user) fills the remaining backstop data. Once official records exist, re-imports are skipped on subsequent cold starts.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. In dev, `/api/*` is proxied to `localhost:8000` by `vite.config.ts`. Set `VITE_API_URL` only when the API is not served from the same origin (e.g. a standalone deployment).

### 3. Frontend build + checks

```powershell
cd frontend
npm run build      # TypeScript + Vite production build
npm run lint       # tsc --noEmit type-check
```

### Backend env variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | **Required.** PostgreSQL/Neon DSN (or `sqlite:///./saksham.db` for a local prototype). In production the DSN carries `?sslmode=require` for Neon. No default — the app refuses to start without it. |
| `JWT_SECRET` | Signs admin tokens. Use a strong random secret in production. |
| `CORS_ORIGINS` | Comma-separated allowed origins. In production include the deployed frontend origin (Vercel serves `/api` on the same origin, so this is often already satisfied). |
| `SEED_ON_STARTUP` | `1` (default) provisions schema + data on startup; `0` creates the schema only and skips the data bootstrap. |
| `AI_API_KEY` / `AI_BASE_URL` / `AI_MODEL` | Optional LLM; empty → deterministic template explanations. |
| `MAP_TILE_URL` | Custom tile source; falls back to OpenStreetMap demo tiles. |

## Deployment (Vercel + Neon)

1. **Database** — create a Neon project and a `saksham` database. Copy the pooled connection string.
2. **Vercel project** — link the repo. In *Settings → Environment Variables* for the API service set:
   - `DATABASE_URL` → the Neon DSN with `?sslmode=require`
   - `JWT_SECRET` → a strong random secret
   - `CORS_ORIGINS` → the production frontend origin (same-origin normally suffices)
   - `SEED_ON_STARTUP=1` (default) for first-time provisioning
3. **Deploy** — Vercel builds the `web` (vite) and `api` (fastapi) services from `vercel.json`. Deep links and `/api/*` are routed per the rewrites. On first cold start the schema + official scheme catalog are bootstrapped into Neon automatically.

> **Why the API no longer 500s when Neon wakes slowly:** the startup hook provisions the database best-effort and **never takes the app down**. If the database is unreachable at cold start (e.g. a suspended Neon compute waking up), `/health` still returns `200` immediately, a warning is logged, and the first real request retries provisioning automatically. A `connect_timeout=10` ensures a broken/held endpoint fails fast instead of hanging a serverless invocation.

## Demo access

- **Admin console:** http://localhost:5173/admin/login — username `admin`, password `saksham@2026` *(prototype only)*.

### Suggested walkthrough

1. **Eligibility** — use "Load demo scenario" (SC beneficiary, ₹2.4L income, small manufacturing, ₹1.2L cost, Bhopal) → continue.
2. **Recommendation** — review match scores and explanations; pick a scheme → "Proceed to EMI".
3. **Calculator** — EMI, interest, timeline; then "Find partners".
4. **Partner Locator** — see the recommended partner with the scoring breakdown and map; try List/Map toggle and state filters.
5. **Application** — recommended end-to-end path + downloadable summary.
6. **Admin** — sign in, view dashboard charts, edit schemes/partners.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/schemes`, `/api/schemes/{id}`, `/api/schemes/{id}/documents` | Scheme catalog (official + demo) + document checklists |
| GET | `/api/partners`, `/api/partners/{id}` | Partner catalog |
| POST | `/api/eligibility/check` | Records an eligibility check (accepts profile) |
| POST | `/api/recommendations` | Deterministic scheme recommendations with reasons |
| POST | `/api/calculator/emi` | EMI / interest / repayment / timeline |
| POST | `/api/partners/recommend` | Weighted partner routing with score breakdown |
| POST | `/api/partners/application-route` | Persist application guidance + best partner |
| POST | `/api/assistant/chat` | Intent-based assistant (en/hi) |
| POST | `/api/admin/auth/login` | Admin login (OAuth2 password form) → JWT |
| GET | `/api/admin/dashboard` | Demo analytics |
| CRUD | `/api/admin/schemes`, `/api/admin/partners` | Admin scheme/partner management (JWT) |
| GET | `/api/admin/applications`, `/api/admin/recommendations` | Recorded activity (JWT) |

Interactive docs are available at `/docs` on the API service.

## Testing

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

The suite covers the deterministic business logic (recommendation engine, calculator, partner routing), the official scheme-data integrity (`>= 20` active official records), and the HTTP API surface.

## Design principles

- **Deterministic core** — eligibility, scoring, EMI and routing are rule-based; identical input always yields identical output.
- **Explainable AI** — the optional LLM explains *why* a scheme/partner matched; it never alters the deterministic outcome. With no API key, a transparent template-based explanation is used.
- **Verified finance** — no financial value is generated by AI; all figures come from calculation code.
- **Resilient serverless** — database provisioning never blocks or kills app startup; on failure it retries lazily on the first request.
- **Demo honesty** — demo and sample surfaces carry verification notices; the official catalog is curated from government sources but must still be confirmed against live guidelines.

## Disclaimers

- This platform is a prototype for demonstration purposes. Scheme eligibility, interest rates, loan limits, partner availability and documentation requirements should be verified against the latest official guidelines before applying.
- This is a prototype for demonstration; it has **no** government ownership or endorsement.
- The official scheme catalog is imported from curated public government sources, but availability, interest rates and thresholds shown are indicative only.
- Always confirm current eligibility criteria, documents and rates with the official issuing agency before acting.

## Roadmap (beyond the demo)

- Alembic migrations, rate limiting, refresh tokens.
- Live scheme/partner data via official open APIs plus verification status.
- Application document upload + status tracking.
- Admin user management and audit log viewer.
- PWA/offline support for low-bandwidth field use.