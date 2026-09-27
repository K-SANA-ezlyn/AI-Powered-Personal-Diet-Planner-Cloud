# Career Proof Pack — Resume, LinkedIn, GitHub Strategy

Everything below is worded to be **honest**: an educational cloud project
with synthetic data — which is exactly what recruiters respect.

## A. Resume bullet points (pick 3)

- Built a cloud-hosted AI diet-planner (React + FastAPI) demonstrating
  cloud-database/object-storage abstraction with provider swap via
  environment variables, JWT auth, and server-side per-user isolation; 58
  automated tests + CI pipeline kept it green.
- Designed a graceful-degradation AI layer: deterministic rule-based
  recommendation engine as primary path with automatic fallback from an
  external AI API on timeout/malformed responses, recording engine
  provenance on every plan.
- Deployed the full stack on free-tier cloud (Render, Vercel, Supabase
  Postgres + private Storage) with health probes, rate limiting, CORS
  allowlisting and request logging; zero secrets committed to source.

## B. Two-line project description (resume)

> Cloud-based diet planner (React, FastAPI, PostgreSQL) with JWT auth, AI
> meal-plan generation and automatic rule-based fallback, object storage and
> a provider-abstraction layer enabling local-to-cloud deployment via
> environment variables only. 58 automated tests, CI/CD, free-tier deployment.

## C. LinkedIn project description

> 🥗 AI-Powered Personal Diet Planner with Cloud Storage — my cloud-computing
> course project, built to demonstrate real cloud architecture end-to-end:
>
> • React SPA + FastAPI REST API (JWT auth, rate limiting, CORS allowlist)
> • Cloud database & object storage behind a provider-abstraction layer —
>   SQLite→Supabase Postgres / local-disk→private bucket by changing ONE env var
> • AI meal-plan engine with a resilience twist: an external AI API that
>   automatically falls back to a deterministic local engine on any failure,
>   with the engine provenance stored on every plan
> • Server-side per-user data isolation, 58 automated tests, 17-check live
>   E2E smoke, GitHub Actions CI, and a free-tier deployment (Render+Vercel+Supabase)
>
> Fully runnable offline for learning, deployable for free. Synthetic demo
> data only; clearly labeled educational output. Repo in the comments. 🚀

## D. Technical skills demonstrated

Cloud: SaaS/PaaS/IaaS concepts, managed databases, object storage, env-based
secrets, health probes, monitoring, CI/CD, autoscaling design.
Backend: FastAPI, REST design, SQLAlchemy ORM, JWT/bcrypt, middleware,
rate limiting, provider/strategy patterns, graceful degradation.
Frontend: React, React Router, axios interceptors, protected routing.
Quality: pytest isolation fixtures, E2E smoke tests, test-plan matrices.
Docs: architecture diagrams, ADR-style rationale, deployment runbooks.

## E. GitHub repository setup

**Name:** `AI-Powered-Personal-Diet-Planner-Cloud`
**Description:**
> Cloud-based AI-powered personal diet planning application with
> authentication, personalized recommendation generation, cloud database
> integration, object storage, and scalable deployment architecture.

**Topics (add all):**
`cloud-computing` `artificial-intelligence` `python` `fastapi` `react`
`cloud-storage` `database` `rest-api` `full-stack` `jwt-authentication`
`supabase` `pytest` `ci-cd` `software-architecture`

## F. Commit strategy — day-wise, genuine-looking history

Push in this order (one logical day per batch). Each batch is already
modular, so this reads like real incremental development:

| Day | Files | Commit message | Screenshot to capture |
|---|---|---|---|
| 1 | `.gitignore`, `requirements*.txt`, `pytest.ini`, `.env.example`, `docs/architecture.md` | `Create cloud application architecture and project scaffolding` | folder tree + architecture diagram |
| 2 | `frontend/` scaffolding, landing/register/login pages, styles | `Set up React frontend with landing and auth pages` | login page |
| 3 | `backend/app.py`, `config.py`, `database.py`, middleware, health routes | `Add FastAPI application with logging, rate limiting and health probes` | `/api/health` response + Swagger |
| 4 | `cloud/auth_service.py`, `utils/security.py`, `routes/auth_routes.py` | `Add user authentication with bcrypt and JWT` | register → token response |
| 5 | `routes/profile_routes.py`, models | `Implement user profile management with validation` | profile saved |
| 6 | `ai_engine/*` (data, rule-based, adapter, factory) | `Add AI diet recommendation engine with rule-based core` | generated plan |
| 7 | `routes/diet_routes.py`, `plan_routes.py` | `Implement diet plan generation and REST API` | plan saved to cloud |
| 8 | `cloud/database_service.py`, `storage_service.py`, `routes/file_routes.py` | `Integrate cloud database and object storage providers` | Supabase bucket / uploads folder |
| 9 | `dashboard_routes.py`, `services/dashboard_service.py`, dashboard page | `Build user dashboard with aggregated cloud data` | dashboard |
| 10 | `tests/*`, `scripts/smoke_test.py`, `docs/test-plan.md` | `Add automated tests and end-to-end smoke checks` | green pytest output |
| 11 | `.github/workflows/ci.yml`, `.env.cloud.example`, `docs/cloud-deployment.md` | `Deploy application to cloud with CI pipeline` | Render + Vercel dashboards |
| 12 | `README.md`, remaining `docs/`, `screenshots/` | `Complete README and project documentation` | GitHub repo home |

## G. Proof checklist — 23 screenshots (professional filenames)

Store in `screenshots/`, name exactly:

1. `01-project-folder-structure.png` — IDE/tree view
2. `02-cloud-architecture-diagram.png` — docs diagram
3. `03-registration-page.png` — empty register form
4. `04-registration-success.png` — welcome profile redirect
5. `05-login-page.png` — login form
6. `06-user-profile-form.png` — filled profile
7. `07-profile-saved-success.png` — success box
8. `08-diet-preference-selection.png` — choice chips selected
9. `09-plan-generation-page.png` — before generate
10. `10-generated-diet-plan.png` — full plan card (disclaimer visible!)
11. `11-plan-saved-success.png` — save confirmation
12. `12-saved-plans-list.png` — grid of plans
13. `13-cloud-database-record.png` — Supabase Table Editor row
14. `14-cloud-storage-object.png` — Supabase Storage object
15. `15-file-upload-page.png` — upload + list
16. `16-file-upload-success.png` — success + row
17. `17-file-download-roundtrip.png` — downloaded bytes match
18. `18-user-dashboard.png` — full dashboard
19. `19-api-swagger-docs.png` — /docs
20. `20-health-probes-response.png` — three probes
21. `21-automated-tests-passing.png` — `pytest -v` green tail
22. `22-ci-pipeline-green.png` — GitHub Actions check
23. `23-deployed-app-live.png` — Vercel URL dashboard

(`screenshots/README.md` repeats this list with "what it proves" notes.)
