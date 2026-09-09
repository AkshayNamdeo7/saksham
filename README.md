# Saksham — Scheme Matching Platform for Marginalized Entrepreneurs

A full-stack prototype platform (Smart India Hackathon demo) that helps marginalized / SC beneficiaries discover suitable concessional financial-assistance and education-loan schemes, understand eligibility, estimate repayment, locate eligible channel partners, and get transparent application-routing guidance.

> **Prototype / Demo only.** All schemes, partners, statuses and figures are sample data. Verify everything against official scheme guidelines before applying.

## SIH Problem Statement

Many marginalized and SC/ST entrepreneurs and students are unaware of the concessional loan, subsidy, and education-loan schemes they are eligible for, and even when they are aware, they struggle to understand eligibility, compare options, estimate repayment, locate the right channel partner, and prepare the correct documents. Information is fragmented across agencies, criteria are complex, and guidance is rarely available in an accessible, bilingual, and transparent way.

**Saksham** addresses this gap with a guided, explainable digital assistant that:
1. Collects a simple profile (category, income, purpose, project/course, location).
2. Deterministically shortlists eligible schemes with a transparent match score and reasons.
3. Provides an EMi/repayment estimator with warning when a requested amount exceeds a scheme limit.
4. Routes the user to the most suitable eligible channel partner using weighted, explainable scoring.
5. Lists per-scheme document checklists and an end-to-end application path.
6. Offers English + हिंदी support with an AI assistant that never alters the deterministic outcomes.

---

## Features

- **Guided eligibility flow** — short multi-step form (age, family income, purpose, project/course, location) with demo-scenario autofill.
- **Transparent recommendation engine** — every scheme result shows a match score plus the exact matched/unmatched criteria and next steps.
- **Deterministic EMI calculator** — interest, EMI, total repayment and timeline buckets are computed by calculation code only (AI never guesses financial figures). Moratorium option included.
- **Partner locator** — weighted routing (eligibility 40, scheme 30, distance 20, capacity/status 10), OpenStreetMap markers colored by status, distance + Google-Maps directions, per-partner score breakdown.
- **Document checklists** — per-scheme required/optional documents (demo).
- **Application guidance** — recommended end-to-end path (scheme → requirement → partner → documents → next step) plus a downloadable summary.
- **AI assistant** — intent-based chat in English and Hindi with deterministic fallback; AI explains but never changes results.
- **Admin console** — JWT-protected dashboard with demo analytics, scheme CRUD, partner CRUD, and applications/recommendations tables.
- **Bilingual (EN / हिंदी)** — persisted language choice across the platform.

## Tech stack

- **Frontend:** React 18 · Vite · TypeScript · Tailwind CSS · React Router · react-leaflet (OSM) · recharts · i18next · lucide-react
- **Backend:** Python 3 · FastAPI · SQLAlchemy · SQLite (PostgreSQL-ready) · python-jose + bcrypt (JWT admin auth)
- **Testing:** pytest (HTTP + business-logic tests)

## Repository layout

```
saksham/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, routes, startup seed
│   │   ├── api/
│   │   │   ├── deps.py          # get_current_admin (JWT)
│   │   │   └── routes/          # schemes, partners, eligibility, recommendations,
│   │   │                        # calculator, partner_routing, assistant, admin_*
│   │   ├── core/                # config, security
│   │   ├── db/                  # session, seed (demo data + admin user)
│   │   ├── models/              # SQLAlchemy models
│   │   ├── repositories/        # query helpers
│   │   ├── schemas/             # Pydantic contracts
│   │   └── services/            # recommendation_engine, calculator, partner_routing,
│   │                            # ai_service, assistant_handler
│   ├── tests/                   # pytest suite
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # public pages + pages/admin/*
│   │   ├── components/          # layout, cards, map, assistant, common
│   │   ├── context/ProfileContext.tsx   # persisted journey state
│   │   ├── services/api.ts      # typed API client
│   │   ├── services/adminApi.ts # admin API client
│   │   ├── hooks/, utils/, i18n/, types/
│   │   └── App.tsx              # lazy route registry
│   ├── vite.config.ts           # port 5173, /api → localhost:8000 proxy
│   └── package.json
└── README.md
```

## Getting started

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env          # then adjust values if needed
uvicorn app.main:app --reload --port 8000
```

The API runs at `http://localhost:8000`. With `SEED_ON_STARTUP=1` (default), the SQLite DB is created and seeded idempotently on startup: **8 schemes, 10 documents, 24 partners**, and the admin user.

> On first seed, `JWT_SECRET` from `.env` is used to store the admin password hash. If you change `JWT_SECRET` after seeding, reset the DB or update the seed (demo only — see `backend/app/db/seed.py`).

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. In dev, `/api/*` is proxied to `localhost:8000` by `vite.config.ts`.

### Optional env

| Variable | Where | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | backend `.env` | `sqlite:///./saksham.db` (default) or a PostgreSQL DSN |
| `JWT_SECRET` | backend `.env` | Sign admin tokens. Use a strong random secret in production |
| `CORS_ORIGINS` | backend `.env` | Comma-separated allowed origins |
| `AI_API_KEY` / `AI_BASE_URL` / `AI_MODEL` | backend `.env` | Optional LLM; empty → deterministic template explanations |
| `MAP_TILE_URL` | backend `.env` / `VITE_MAP_TILE_URL` | Custom tile source; falls back to OpenStreetMap demo tiles |
| `VITE_API_URL` | frontend `.env` | Full API base when not using the dev proxy |

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
| GET | `/api/schemes`, `/api/schemes/{id}`, `/api/schemes/{id}/documents` | Scheme catalog + document checklists |
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

## Testing

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

The suite covers the deterministic business logic (recommendation engine, calculator, partner routing) and the HTTP API surface.

## Design principles

- **Deterministic core** — eligibility, scoring, EMI and routing are rule-based; identical input always yields identical output.
- **Explainable AI** — the optional LLM explains *why* a scheme/partner matched; it never alters the deterministic outcome. With no API key, a transparent template-based explanation is used.
- **Verified finance** — no financial value is generated by AI; all figures come from calculation code.
- **Demo honesty** — every data-driven surface carries a "Prototype / Demo Data" badge and official-verification notices.

## Disclaimers

- This platform is a prototype for demonstration purposes. Scheme eligibility, interest rates, loan limits, partner availability and documentation requirements should be verified against the latest official guidelines before applying.
- This is a prototype for demonstration; it has **no** government ownership or endorsement.
- Scheme names, partner details, availability, interest rates and thresholds are sample data.
- Always confirm current eligibility criteria, documents and rates with the official issuing agency before acting.

## Roadmap (beyond the demo)

- PostgreSQL + Alembic migrations, rate limiting, refresh tokens.
- Live scheme/partner data via official open APIs plus verification status.
- Application document upload + status tracking.
- Admin user management and audit log viewer.
- PWA/offline support for low-bandwidth field use.