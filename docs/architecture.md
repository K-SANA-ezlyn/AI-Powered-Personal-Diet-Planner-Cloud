# Architecture

## System overview

```text
                    USER (browser — any device)
                            │  HTTPS + JWT Bearer
                            ▼
        ┌───────────────────────────────────────────┐
        │  FRONTEND — React SPA (Vercel / :5173)    │
        │  Landing · Register · Login · Profile ·   │
        │  Generate · Result · Saved Plans ·        │
        │  Cloud Files · Dashboard                  │
        └───────────────────┬───────────────────────┘
                            │  JSON over HTTP (axios)
                            ▼
        ┌───────────────────────────────────────────┐
        │  API LAYER — FastAPI (Render / :8000)     │
        │  CORS allowlist · rate limiting · request │
        │  logging · JWT auth · validation · error  │
        │  contracts (4xx/5xx)                      │
        └──────┬──────────────┬──────────────┬──────┘
               │              │              │
               ▼              ▼              ▼
        ┌───────────┐  ┌───────────┐  ┌───────────────┐
        │ AI LAYER  │  │ DATA      │  │ STORAGE LAYER │
        │ diet      │  │ LAYER     │  │ object store  │
        │ engine:   │  │ cloud DB  │  │ uploads/ ⇄    │
        │ AI API -> │  │ SQLite ⇄  │  │ Supabase      │
        │ fallback  │  │ Supabase  │  │ private       │
        │ rule-based│  │ Postgres  │  │ bucket        │
        └───────────┘  └───────────┘  └───────────────┘
               │              │              │
               └──────────────┴──────────────┘
                              ▼
                 logs · health probes · CI/CD
```

## Layer responsibilities

| Layer | Component | Responsibility |
|---|---|---|
| Client | React SPA | rendering, form validation UX, JWT storage, routing guards |
| Application | FastAPI | authn/authz, request validation, orchestration, rate limiting, logging |
| AI | `backend/ai_engine/` | meal-plan generation; AI-API adapter with automatic rule-based fallback |
| Data | `backend/database.py` + models | structured persistence (users, profiles, plans, file metadata) |
| Storage | `backend/cloud/storage_service.py` | unstructured blobs (meal photos, exports) via provider abstraction |

## Request flow: generate & save a plan

```text
1. Browser: POST /api/diet/generate-plan  (Authorization: Bearer <JWT>)
2. FastAPI: JWT verified -> User resolved; Pydantic validates overrides
3. diet_routes: load Profile row -> build UserPreferences (merged overrides)
4. diet_engine.get_diet_engine():
     AI_PROVIDER=auto + key configured? -> try AIApiEngine
     any failure (timeout, 5xx, bad JSON, wrong schema)?
        -> log & fall back to RuleBasedEngine        <- resilience point
5. Engine returns DietPlanResult (meals + nutrition + engine_used)
6. Response 200  (nothing persisted yet — explicit save follows)
7. Browser: POST /api/plans  -> row INSERTed into diet_plans (cloud DB)
8. Dashboard GET /api/dashboard now aggregates the new plan
```

## Request flow: upload a file

```text
1. POST /api/files/upload (multipart)  -> JWT checked
2. validators.validate_file: extension whitelist -> size limit -> magic bytes
3. storage_provider.upload(bytes, meals/{user_id}/{uuid}_{name})
     local mode: writes under uploads/   (path-traversal guarded)
     cloud mode: POSTs to private Supabase bucket with service key
4. Metadata INSERT into user_files
     if the DB insert fails -> provider.delete() removes the orphaned object
5. Response 201 with metadata (never the bytes)
```

## Failure paths (summary)

| Failure | Behaviour | HTTP |
|---|---|---|
| AI API down / slow / malformed | automatic rule-based fallback, plan still delivered | 200 |
| Storage outage | `StorageError` -> handler | 503 |
| DB down | health probe reports; requests fail fast | 503 |
| Expired/garbage token | 401 with clear message | 401 |
| Other user's plan/file id | 404 — existence never confirmed | 404 |
| Disallowed/oversized upload | 415 / 413 | 415/413 |

## Cloud reference topology (deployment)

See `cloud-deployment.md` for the free-tier walkthrough and the
AWS/Azure/GCP mapping (managed DB, object storage, container hosting,
API gateway, monitoring). The application is stateless — every piece of
state is externalized to the database/storage layer — so horizontal
scaling is a matter of running more replicas behind a load balancer.
