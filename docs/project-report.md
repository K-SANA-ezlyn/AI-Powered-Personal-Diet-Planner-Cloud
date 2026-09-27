# Project Report — AI-Powered Personal Diet Planner with Cloud Storage

## Abstract

This project designs, implements, tests and (optionally) deploys a cloud-based
personal diet planning application whose core purpose is to demonstrate
cloud-computing architecture end-to-end: authentication, a managed cloud
database, object storage, an AI-style recommendation service with graceful
degradation, REST API design, security controls, observability, testing and
CI/CD. A provider-abstraction layer lets the identical codebase run in a
fully local simulation (SQLite + filesystem, zero cost) or on free-tier cloud
services (Supabase Postgres + Storage) by changing only environment
variables. All user data is synthetic and every generated plan is explicitly
labeled an educational wellness example, not medical advice.

## 1. Introduction

Diet planning apps illustrate nearly every cloud concept in one product:
multi-device access (SaaS), per-user data (cloud database), binary content
(object storage), third-party AI dependencies (resilience patterns), and
multi-tenant isolation (security). This project uses that domain to build a
small but complete cloud system with production-grade patterns — not a toy
CRUD demo.

## 2. Problem Statement

Individuals struggle to plan meals consistently and track approximate
nutrition toward a general wellness goal; they need their plans and progress
available across devices. From the course perspective, the deeper problem is
architectural: how should a multi-user application combine authentication, a
cloud database, object storage and an AI-style engine so that it remains
secure, available, scalable and testable at zero infrastructure cost for a
student?

## 3. Objectives

1. Demonstrate core cloud-computing concepts in working code (see
   `cloud-concepts-mapping.md` — 26 concepts, each mapped to a file).
2. Build a usable planner: profile → AI-generated plan → save → track → files.
3. Guarantee per-user data isolation server-side and prove it with tests.
4. Keep the system executable offline (local simulation) and deployable
   free of charge (cloud mode) with no code changes.
5. Engineer for failure: AI API fallback, storage/DB health probes, clean
   error contracts.
6. Ship with automated tests, CI, documentation and a deployment guide.

## 4. Existing System (survey)

Generic calorie-counting apps (manual entry, ad-heavy, closed data), static
diet PDFs (no personalization), and spreadsheet trackers (no sync, no access
control). None are designed to demonstrate cloud architecture; most require
paid tiers for API access or storage. None offer a local-only simulation
mode for learning.

## 5. Proposed System

A React SPA talking to a stateless FastAPI service. Authentication uses
bcrypt + JWT. Structured data (users, profiles, saved plans, file metadata)
lives in a relational cloud database; unstructured files live in object
storage behind a provider abstraction. Meal plans come from a strategy
interface: a deterministic rule-based engine over a curated food dataset
(primary, always available) with an optional external AI API adapter that
falls back automatically on any failure. Observability includes request
logging middleware and three health probes; protection includes CORS
allowlisting and per-IP rate limiting. 58 automated tests plus a 17-check
live smoke script verify behavior including isolation and fallback.

## 6. Cloud Computing Concepts Demonstrated

Summarized here; the full concept→file→proof table is
`cloud-concepts-mapping.md`. Headlines: SaaS delivery; PaaS hosting (Render/
Vercel/Supabase) with IaaS mapping; cloud database via a one-variable
provider swap; object storage with private-bucket + authorized-download
semantics; JWT authentication and server-side authorization; REST design
with precise status codes; stateless design enabling horizontal
scalability/elasticity; API-gateway responsibilities (CORS, rate limiting);
12-factor configuration and secrets management; logging and health-based
monitoring; graceful degradation; CI/CD with GitHub Actions.

## 7. Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 18 + Vite + React Router + axios | industry-standard SPA; dev proxy kills CORS friction |
| Backend | Python 3.11+, FastAPI, Pydantic v2 | typed contracts, auto Swagger docs, async-ready |
| ORM/DB | SQLAlchemy 2.0 → SQLite / Supabase Postgres | provider swap with zero code change |
| Storage | local folder ⇄ Supabase Storage (httpx) | same interface, env-selected |
| Auth | passlib bcrypt + PyJWT (HS256) | proven primitives, no vendor lock |
| AI | rule-based engine + OpenAI-compatible adapter | always-works primary, optional upgrade |
| Testing | pytest (58) + live smoke (17) | isolation via env-scoped fixtures |
| CI/CD | GitHub Actions | tests + build on every push |

## 8. System Architecture & Data Flow

Text diagrams and per-request flow traces: `architecture.md`. In one
sentence: browser → TLS → FastAPI (auth, validate, orchestrate) → AI engine
(with fallback) / cloud DB / object storage → JSON response → rendered SPA.

## 9. Database Design

Four tables (`users`, `profiles` 1:1, `diet_plans` 1:N, `user_files` 1:N)
with UUID PKs and indexed FKs; `nutrition_summary` stored as JSON for
engine flexibility; `engine_used` preserves plan provenance. Rationale and
sample SQL: `database-design.md`.

## 10. Cloud Storage Design

Object keys `meals/{user_id}/{uuid}_{safe_name}`; metadata rows in the DB,
bytes in the bucket; private bucket; owner-checked downloads; magic-byte
upload validation; compensating delete on metadata failure. `storage-design.md`.

## 11. AI Recommendation Logic

Rule-based pipeline: filter by meal slot → enforce dietary preference → hard
exclude allergens → score by goal (calorie direction, protein emphasis) →
activity bump → seeded variety pick per slot → aggregate approximate
nutrition + hydration note. Optional AI API path: structured prompt, strict
JSON response validation, 20 s timeout, any failure → rule-based fallback;
`engine_used` records the truth. `ai_engine/` and `test_diet_engine.py`.

## 12. Authentication & Authorization

Registration bcrypt-hashes; login issues a JWT (`sub`, `exp`, `jti`);
every protected route resolves the token to a user; every data query filters
by that user id; foreign ids return 404 (no existence leak); rate limiting
protects credential endpoints. Logout is stateless with production
upgrades documented. `security.md`.

## 13. API Design

15+ endpoints across auth, profile, diet generation, saved plans, files,
dashboard and health — with a published status-code contract (201/400/401/
404/413/415/422/429/503). `api-reference.md`.

## 14. Implementation Highlights

- **Cloud abstraction layer** (`backend/cloud/`): three services, each with
  local + cloud providers behind one interface — the design centerpiece.
- **Middleware stack**: request logging, rate limiting, exception → status
  mapping (413/415/503 contracts).
- **Backend-for-frontend dashboard**: one aggregate endpoint powers the
  whole dashboard screen.
- **Idempotent profile upsert**; storage-first upload with compensation.

## 15. Testing

**58 automated tests** across 6 files: auth (10), profile (7), engine rules
(12, including vegan/allergy exclusion and cross-day variety), fallback
(5), plans (11 including three isolation tests), files (10 including
renamed-.exe rejection and isolation), health/dashboard (4+). A 17-check
live smoke script walks register→generate→save→upload→isolation→logout over
real HTTP. A 34-case manual matrix (`test-plan.md`) covers the cloud-mode
and UI checks.

## 16. Cloud Deployment

Approach A: Render + Vercel + Supabase, ~35 minutes, free tier, exact env
vars. Approach B: AWS/Azure/GCP mapping table and topology. Monitoring via
health probes + UptimeRobot; CI green as the deploy gate. `cloud-deployment.md`.

## 17. Security

Controls table, authn vs authz, encryption in transit/at rest explained,
JWT lifecycle and logout upgrades, common student mistakes avoided, threat
snapshot (IDOR, XSS, CSRF, injection, malicious uploads). `security.md`.

## 18. Scalability

10 / 1,000 / 100,000-user walkthroughs with the exact bottleneck each hits
and the fix: replicas + pooling → Redis-backed limiting + caching + read
replicas → partitioning + queues + CDN. The stateless, 12-factor design is
the enabler throughout. `scalability.md`.

## 19. Results

- 58/58 automated tests green; 17/17 live smoke checks green; clean
  production frontend build.
- Complete workflow verified: register → profile → generate (fallback
  proven) → save → upload (round-trip bytes) → isolation denied (404s) →
  dashboard aggregate.
- Zero-cost execution proven in both local simulation and free-tier cloud.

## 20. Advantages

Runs offline or in the cloud with identical code · honest AI fallback with
provenance · strict user isolation tested, not claimed · professional error
contracts · excellent zero-cost learning surface for cloud concepts.

## 21. Limitations

Free-tier cold starts; in-memory rate limiting (single instance); stateless
logout; magic-byte-only malware screening; rule-based engine is a
recommendation simulation, not a clinical system; single-region demo.

## 22. Future Scope

Refresh tokens + revocation · Redis rate limiting · signed-URL direct
uploads · background workers for exports/notifications · nutrition tracking
over time (trend dashboard) · wearable import · ESP32/HX711 smart food-scale
integration · multi-language food datasets · Terraform for one-command infra.

## 23. Conclusion

The project delivers a working, tested, documented cloud application whose
architecture — not just its features — is the deliverable: provider
abstraction for portability, externalized state for scalability, defense in
depth for security, graceful degradation for resilience, and automation
(tests/CI) for maintainability. Every claim maps to a file, a test or a
probe.

## Disclaimer

This software is an educational demonstration. It does not provide medical,
clinical or nutritional advice. All data is synthetic. Consult qualified
professionals for personal health decisions.
