# AI-Powered Personal Diet Planner with Cloud Storage

> A cloud-native diet planning application: AI-generated personalized meal
> plans with automatic rule-based fallback, JWT authentication, a cloud
> database, private object storage, and a scalable REST architecture — built
> to demonstrate **cloud computing concepts** end-to-end. Runs entirely
> offline in local mode, or deploys to free-tier cloud with zero code changes.

![Architecture](docs/assets/architecture.png)

## Overview

Users register, fill a short demo wellness profile (age, height, weight,
activity, dietary preference, goal, allergies), and generate a personalized
one-day meal plan — breakfast, lunch, snack, dinner plus an approximate
nutrition summary. Plans are saved to a **cloud database** and files (meal
photos, food logs) to **object storage**; a dashboard aggregates everything,
available from any device. The recommendation layer has two interchangeable
engines behind one interface: a deterministic **rule-based engine** (always
available, offline, free) and an optional **external AI API** that the
system automatically falls back from — every plan records which engine
produced it.

| Mode | Database | Storage | AI | Cost |
|---|---|---|---|---|
| **LOCAL** (default) | SQLite | `uploads/` folder | rule-based (AI optional) | ₹0 / $0, works offline |
| **CLOUD** | Supabase Postgres (free) | Supabase private bucket | rule-based or AI API (free-tier keys) | free tier |

## Problem Statement

Meal planning is repetitive, easy to abandon, and hard to personalize; plans
scattered across notes and chats don't survive device switches. Existing apps
are closed, ad-heavy or paid. From a cloud-computing education perspective,
the real problem is architectural: how do you combine authentication, a
managed database, object storage, and an AI-style engine into one secure,
scalable, testable system — at zero infrastructure cost? This project
answers that with working code, not slides.

## Objectives

1. Demonstrate 26 cloud concepts mapped to exact files and proofs (`docs/cloud-concepts-mapping.md`).
2. Build a usable planner: profile → AI plan → save → retrieve → files → dashboard.
3. Prove server-side per-user isolation with tests, not claims.
4. Keep one codebase for local simulation and cloud deployment (env-var swap).
5. Engineer for failure: AI fallback, health probes, clean error contracts.
6. Ship tests, CI, deployment runbooks and recruiter-ready documentation.

## Features

- **Accounts** — register / login / logout; bcrypt-hashed passwords; JWT-protected SPA routes and APIs.
- **Profile** — validated demo health inputs with allergy-tag chips; idempotent upsert; powers personalization.
- **AI plan generation** — one-day plan (4 meals) + approximate nutrition + hydration note; per-request overrides; engine provenance on every plan.
- **Saved plans** — save/list/view/delete; export to `.txt`; every plan carries the educational disclaimer.
- **Cloud files** — upload/download/delete meal photos & logs; extension + size + magic-byte validation; private storage.
- **Dashboard** — one aggregated API call: goal, preference, latest plan, recent plans/files, totals, display-only BMI note.
- **Platform** — request logging, rate limiting, CORS allowlist, health probes, graceful AI fallback, 58 automated tests, CI.

## Cloud Computing Concepts (where each lives)

| Concept | In this project |
|---|---|
| SaaS | planner consumed via browser, nothing installed |
| PaaS | Render (API) · Vercel (SPA) · Supabase (DB/Storage) |
| IaaS (mapping) | docs map each managed piece to EC2/Blob equivalents |
| Cloud database | `DATABASE_URL` swap: SQLite ⇄ Supabase Postgres |
| Object storage | folder ⇄ private bucket — `cloud/storage_service.py` |
| Authentication | bcrypt + JWT (`cloud/auth_service.py`) |
| Authorization | token dependency + row-level ownership checks |
| REST API | 15+ endpoints, precise status contract (`docs/api-reference.md`) |
| Client–server | stateless React ⇄ stateless FastAPI, JSON/HTTP |
| Serverless readiness | stateless handlers map to Cloud Run/Lambda |
| Scalability & elasticity | externalized state; 10/1k/100k plans in `docs/scalability.md` |
| Availability | managed backups + replicas + health probes |
| Load balancing / CDN | platform edge; LB+ASG design documented |
| API gateway (role) | CORS allowlist + rate limiting + TLS proxy |
| Env vars & secrets | pydantic-settings; `.env.example`; zero secrets in git |
| Logging / monitoring | request-log middleware; `/api/health*` probes |
| Graceful degradation | AI API → rule-based fallback, proven by tests |
| CI/CD | GitHub Actions (pytest + build) → auto-deploy |

Full concept→file→evidence table: `docs/cloud-concepts-mapping.md`.

## Architecture

```text
USER (browser, any device)
        │ HTTPS + JWT Bearer
        ▼
React SPA (Vercel / localhost:5173)
        ▼
FastAPI REST API (Render / localhost:8000)
   CORS · rate limit · logging · JWT auth · validation
        ├──► AI ENGINE  AIApiEngine ──on any failure──► RuleBasedEngine
        │               (optional, env-keyed)          (food_data.json rules)
        ├──► CLOUD DATABASE   SQLite ⇄ Supabase Postgres
        └──► OBJECT STORAGE   uploads/ ⇄ Supabase private bucket
                     ▼
        Logs · health probes · GitHub Actions CI
```

Data flows and failure paths: `docs/architecture.md`.

## Technology Stack

- **Frontend** — React 18 + Vite + React Router + axios
- **Backend** — Python 3.11+ · FastAPI · SQLAlchemy 2.0 · Pydantic v2
- **Database** — SQLite (local) / Supabase Postgres (cloud)
- **Object storage** — local folder / Supabase Storage private bucket
- **Auth** — bcrypt + JWT (HS256)
- **AI** — rule-based engine (primary) + OpenAI-compatible adapter (optional)
- **Testing** — pytest (58) + live smoke script (17 checks)
- **CI/CD** — GitHub Actions; deploy targets Render + Vercel

## AI Recommendation Engine

Two engines, one interface (`backend/ai_engine/`):

- **RuleBasedEngine** — filters the curated food dataset by meal slot and
  dietary preference, hard-excludes allergens, scores foods against the goal
  (deficit-leaning for weight_loss, calorie-dense for weight_gain,
  protein-forward for fitness), adds an activity bump, then picks per-slot
  meals with seeded variety so plans change day to day. Sub-millisecond,
  offline, free.
- **AIApiEngine** (optional) — sends a structured prompt to any
  OpenAI-compatible endpoint, demands strict JSON, schema-validates the
  response with a 20-second timeout. **Any failure — missing key, timeout,
  5xx, malformed JSON — triggers automatic fallback to the rule-based
  engine.** The API key lives only in environment variables.
- Every generated plan records `engine_used`, making degradation auditable.

## Authentication

Register/login issue a signed JWT (`sub`, `exp`, `jti`); every protected
route resolves the token to a user; **every data query additionally filters
by that user id**, so one user cannot retrieve another's plans or files —
foreign ids return 404, never 403 (no existence leak). Passwords are
bcrypt-hashed; login errors are deliberately uniform (no user enumeration).
Stateless logout with production upgrades documented in `docs/security.md`.

## Database

Four tables — `users`, `profiles` (1:1), `diet_plans` (1:N), `user_files`
(1:N, metadata only) — UUID primary keys, indexed foreign keys, JSON
nutrition summaries, `engine_used` provenance column, `ON DELETE CASCADE`.
ERD, rationale and sample SQL: `docs/database-design.md`.

## Cloud Storage

Object keys `meals/{user_id}/{uuid}_{safe_name}`; bytes in object storage,
metadata in the database; private bucket; owner-checked downloads (300-second
signed URLs in cloud mode); path-traversal-proof key construction.
`docs/storage-design.md`.

## REST APIs

| Group | Endpoints |
|---|---|
| Auth | `POST /api/auth/register` · `login` · `logout` · `GET /api/auth/me` |
| Profile | `GET /api/profile` · `PUT /api/profile` |
| AI | `POST /api/diet/generate-plan` |
| Plans | `POST /api/plans` · `GET /api/plans` · `GET/DELETE /api/plans/{id}` |
| Files | `POST /api/files/upload` · `GET /api/files` · `GET /api/files/{id}/download` · `DELETE /api/files/{id}` |
| Aggregates | `GET /api/dashboard` · `GET /api/health` · `/health/db` · `/health/storage` |

Full request/response/status contract: `docs/api-reference.md`; live Swagger
at `/docs` when running.

## Folder Structure

```
AI-Powered-Personal-Diet-Planner-Cloud/
├── backend/
│   ├── app.py                 # FastAPI factory (CORS, logging, rate limit, routers)
│   ├── config.py              # env-driven settings (no hardcoded secrets)
│   ├── database.py            # engine/session from DATABASE_URL
│   ├── seed_demo.py           # synthetic demo users/profiles/plans
│   ├── models/                # User, Profile, DietPlan, UserFile
│   ├── schemas/               # Pydantic request/response contracts
│   ├── routes/                # auth, profile, diet, plans, files, dashboard, health
│   ├── services/              # dashboard aggregation (BFF)
│   ├── middleware/            # logging, rate limiting, error handlers
│   ├── cloud/                 # ★ provider abstractions: database, storage, auth
│   ├── ai_engine/             # diet_engine (factory+fallback), rule_based_engine,
│   │                          #   ai_api_engine, food_data.json
│   └── utils/                 # security (JWT dependency), validators (files/BMI)
├── frontend/                  # React SPA (Vite)
│   └── src/{api,context,services,components,pages,utils}
├── tests/                     # pytest suite (58 tests) + conftest
├── scripts/smoke_test.py      # 17-check live E2E
├── docs/                      # architecture, cloud-concepts-mapping, api-reference,
│                              #   database-design, storage-design, security,
│                              #   scalability, failure-handling, local-simulation-guide,
│                              #   cloud-deployment, test-plan, project-report,
│                              #   career-proof
├── sample_data/               # demo profile JSONs
├── screenshots/               # proof screenshots (README inside)
├── .github/workflows/ci.yml   # pytest + frontend build
├── .env.example / .env.cloud.example
├── requirements.txt / requirements-dev.txt / pytest.ini / .gitignore
└── README.md
```

## Installation & Local Setup

Prereqs: Python 3.11+, Node 18+, Git.

```bash
git clone https://github.com/<you>/AI-Powered-Personal-Diet-Planner-Cloud.git
cd AI-Powered-Personal-Diet-Planner-Cloud

python -m venv .venv
.venv\Scripts\activate                 # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

copy .env.example .env                 # macOS/Linux: cp .env.example .env

uvicorn backend.app:app --reload --port 8000      # Terminal 1
```

```bash
cd frontend
npm install
npm run dev                            # Terminal 2 → http://localhost:5173
```

Demo data (Terminal 3): `python -m backend.seed_demo` → log in with
`aasha@demo.com` / `Demo@12345` (vegetarian · weight-loss · nut allergy) or
`vikram@demo.com` / `Demo@12345` (non-vegetarian · weight-gain).

Full 16-step walkthrough with expected outputs: `docs/local-simulation-guide.md`.

## Environment Variables

See `.env.example` (local) and `.env.cloud.example` (cloud). Key variables:
`SECRET_KEY`, `DATABASE_URL`, `STORAGE_PROVIDER`, `SUPABASE_URL`,
`SUPABASE_SERVICE_KEY`, `SUPABASE_STORAGE_BUCKET`, `CORS_ORIGINS`,
`AI_PROVIDER`, `AI_API_URL`, `AI_API_KEY`. **Never commit `.env`** — the
`.gitignore` blocks it; cloud hosts keep secrets in their dashboards.

## Running the Application

| URL | What |
|---|---|
| http://localhost:5173 | the web app |
| http://localhost:8000/docs | interactive Swagger API docs |
| http://localhost:8000/api/health | liveness probe |

## Testing

```bash
pytest -v                         # 58 automated tests
python scripts/smoke_test.py      # 17 live end-to-end checks (server running)
```

34-case manual matrix with Test ID/Scenario/Expected/Actual/Pass-Fail:
`docs/test-plan.md`. CI runs pytest + the frontend build on every push
(`.github/workflows/ci.yml`).

## Cloud Deployment (free tier)

Render (API) + Vercel (SPA) + Supabase (Postgres + private Storage) —
step-by-step with exact env vars: `docs/cloud-deployment.md` (~35 min).
An AWS/Azure/GCP reference architecture table is included for reports and
interviews. Local vs cloud differences are documented in the same file.

## Security

bcrypt hashing · JWT expiry + token id · server-side user isolation (tested)
· no user enumeration · input validation at the boundary · extension+size+
magic-byte upload validation · path-traversal guards · private object storage
with authorized downloads · CORS allowlist · rate limiting · env-only secrets
· request logging · minimal error contracts. Details and the
common-mistakes table: `docs/security.md`.

## Scalability

Why the design scales (stateless API, externalized state, 12-factor config)
and concrete plans for 10 / 1,000 / 100,000 users — replicas, connection
pooling, Redis-backed limiting, caching, read replicas, queues, CDN,
partitioning: `docs/scalability.md`.

## Screenshots

`screenshots/` holds numbered proof screenshots with a per-shot "what this
proves" note — registration through deployment (see `screenshots/README.md`).

## Results

- 58/58 automated tests green · 17/17 live smoke checks green · clean
  production frontend build.
- Full workflow verified: register → profile → generate (fallback proven) →
  save → upload/download round-trip → cross-user access denied (404) →
  dashboard aggregation.
- Zero-cost execution demonstrated in both local simulation and free-tier
  cloud deployment.

## Limitations

- Free-tier hosts sleep after idle (cold start on the first request).
- In-memory rate limiting suits single-instance deployments (Redis at scale).
- Stateless JWT logout (client-side discard) — revocation strategy in docs.
- Malware screening is structural (magic bytes) — async AV pipeline documented.
- The rule-based engine is a recommendation *simulation* for education, not a
  clinical nutrition system. BMI is display-only.

## Future Improvements

Refresh tokens + revocation · Redis rate limiting · pre-signed direct uploads
· background workers for exports/notifications · nutrition trend tracking ·
wearable data import · ESP32 + HX711 smart food-scale integration ·
multi-region food datasets · Terraform-based one-command infrastructure.

## Learning Outcomes

- Designing a provider-abstraction layer so the cloud vendor is an
  environment variable.
- Correctly separating object storage from databases — and why it matters.
- Enforcing authn/authz and data isolation server-side, with tests as proof.
- Building for failure: fallbacks, health probes, compensating cleanup.
- Operational maturity: logging, monitoring, CI/CD, deployment runbooks.
- Communicating architecture through docs, diagrams and honest limitations.

## Disclaimer

This project is an **educational demonstration** for a cloud-computing
course. It does **not** provide medical, clinical or diagnostic advice, and
its outputs must not be treated as such. All user data shown is synthetic
demo data. For personal health decisions, consult a qualified professional.

## Author

**Khadeejath Sana** — Cloud Computing course project.
GitHub: [K-SANA-ezlyn](https://github.com/K-SANA-ezlyn)
