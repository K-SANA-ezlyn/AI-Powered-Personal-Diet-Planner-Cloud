# Cloud Computing Concepts — Where Each One Lives

Every concept below is **actually implemented** (not just discussed). Use this
table during demos/vivas to jump straight to the code or output that proves it.

| # | Concept | Where it appears in this project | Proof / demo |
|---|---|---|---|
| 1 | **Cloud Computing** | Whole system: browser client + centrally hosted API/DB/storage | run locally or deployed; same UX from any device |
| 2 | **SaaS** | The planner consumed as a service via browser; nothing installed | open the deployed URL, log in, use it |
| 3 | **PaaS** | Render hosts the FastAPI container; Vercel hosts the SPA; Supabase hosts Postgres+Storage | `docs/cloud-deployment.md` |
| 4 | **IaaS (mapping)** | docs map every managed piece to EC2/VM + EBS/Blob equivalents | this table + `cloud-deployment.md` appendix |
| 5 | **Cloud Database** | `DATABASE_URL` swap: SQLite (local) ⇄ Supabase Postgres (cloud); same ORM | start app twice with two `.env` files |
| 6 | **Cloud Object Storage** | `cloud/storage_service.py`: `LocalStorageProvider` ⇄ `SupabaseStorageProvider` | upload a meal photo in both modes |
| 7 | **Object vs structured data** | bytes in the bucket, metadata rows in `user_files` table | schema in `database-design.md` |
| 8 | **Authentication** | register/login issue bcrypt-hashed accounts + JWTs (`cloud/auth_service.py`) | `POST /api/auth/login` response |
| 9 | **Authorization** | `utils/security.py` dependency on every protected route + row-level ownership checks | isolation tests in `tests/test_plans.py` |
| 10 | **REST API** | 15+ endpoints, JSON, correct verbs/status codes | `docs/api-reference.md`, Swagger at `/docs` |
| 11 | **Client–Server architecture** | stateless React SPA ⇄ stateless FastAPI, JSON/HTTP only | network tab of the browser devtools |
| 12 | **Serverless readiness** | app factory + stateless handlers map 1:1 to Cloud Run/Lambda containers | `cloud-deployment.md` § AWS mapping |
| 13 | **Scalability & elasticity** | stateless app; state externalized; replicas behind LB | `scalability.md` (10 / 1k / 100k users) |
| 14 | **Availability** | managed Postgres backups, stateless replicas, `/api/health*` probes | UptimeRobot hitting the deployed probe |
| 15 | **Load balancing** | platform edge routing in free tier; LB+ASG design documented | `scalability.md` architecture diagram |
| 16 | **API Gateway (role)** | CORS allowlist + rate limiting middleware + TLS termination at proxy | `backend/middleware/rate_limit.py` |
| 17 | **Environment variables** | pydantic-settings; ALL config from env; `.env.example` shipped | `config.py`, `.env.example` |
| 18 | **Secrets management** | no secret in git; hosting dashboards hold prod secrets; `.gitignore` blocks `.env` | repo search finds zero keys |
| 19 | **Logging** | request logging middleware (method, path, status, latency) | terminal/Render logs output |
| 20 | **Monitoring** | `/api/health`, `/api/health/db`, `/api/health/storage` probes | curl each endpoint |
| 21 | **Graceful degradation** | AI API failure → rule-based fallback; `engine_used` records truth | `tests/test_diet_engine.py::test_fallback_on_api_crash` |
| 22 | **Deployment** | Render + Vercel + Supabase, step-by-step | `cloud-deployment.md` |
| 23 | **CI/CD** | GitHub Actions: pytest + vite build on every push; hosts auto-deploy `main` | `.github/workflows/ci.yml` green check |
| 24 | **Input validation** | Pydantic schemas at the boundary; file ext+size+magic-bytes | `tests/test_files.py` |
| 25 | **Cloud security basics** | bcrypt, JWT expiry, CORS allowlist, path-traversal guards, no enumeration | `security.md` |
| 26 | **Backup** | Supabase daily managed backups (cloud); SQLite file copy (local) | Supabase dashboard → Backups |

## Two-level explanation (for the report/viva)

**A. Simple explanation.**
The app you open in a browser is just the storefront. A computer in the cloud
(the API) does the thinking: it checks who you are, asks a recipe engine to
build your meal plan, and keeps your plans and photos in big central storage.
Because everything lives centrally, you can log in from your laptop or phone
and see the same data — and if the fancy AI is unreachable, a built-in backup
brain still gives you a plan.

**B. Technical explanation.**
A React SPA communicates over HTTPS/JSON with a stateless FastAPI service.
Authentication is delegated to a token system (JWT) with bcrypt-hashed
credentials. Business state is externalized: structured entities live in a
managed relational database (Postgres in the cloud, SQLite locally — the same
ORM), while unstructured blobs go to object storage through a provider
abstraction chosen by environment variables. Meal-plan generation is behind a
strategy interface with a deterministic local engine and an optional remote AI
adapter; a wrapper enforces fallback on any failure, so the dependency that
can fail is never on the critical path. The service is 12-factor: config comes
from the environment, logs go to stdout, and health endpoints make it
orchestrator-friendly — the same container image promotes from laptop to
cloud without code changes.
