# Failure Handling

A cloud-native app is defined by what happens when dependencies fail. This
document catalogs every modeled failure, the exact behavior, and where the
code enforces it.

## Failure catalogue

| # | Failure | Detected by | Behaviour | HTTP | Code |
|---|---|---|---|---|---|
| 1 | AI API unreachable / timeout | httpx exception in adapter (20 s hard cap) | **automatic rule-based fallback**; plan still delivered; `engine_used=rule_based` | 200 | `ai_engine/diet_engine.py::_FallbackEngine` |
| 2 | AI API returns malformed JSON / wrong schema | schema validation in adapter | adapter raises → fallback (same as #1) | 200 | `ai_api_engine.py::_validate` |
| 3 | AI API misconfigured (no key) | factory readiness probe | rule-based engine selected at startup | 200 | `diet_engine.py::get_diet_engine` |
| 4 | Object storage down | `StorageError` from provider | upload/download fail with clear message; **client may retry safely** | 503 | `storage_service.py` + error handler |
| 5 | DB down | `database_health()` / engine errors | health probe flips to 503; requests fail fast; `pool_pre_ping` recovers after transient drops | 503/500 | `cloud/database_service.py` |
| 6 | Metadata insert fails *after* object upload | try/except around DB write | **compensating delete** removes the orphaned object | 500 (rollback clean) | `routes/file_routes.py` |
| 7 | Expired token | JWT `exp` check | 401 "Token has expired — please log in again"; SPA auto-redirects to login | 401 | `utils/security.py` |
| 8 | Garbage/forged token | signature check | 401 + warning log | 401 | `utils/security.py` |
| 9 | Duplicate registration race | unique constraint on email | 409 | 409 | `users.email` unique |
| 10 | Disallowed/oversized upload | validators | 415 / 413 before touching storage | 415/413 | `utils/validators.py` |
| 11 | Path traversal attempt in object key | `build_storage_path` sanitization + `_full()` root check | rejected/mapped to safe key; no escape from storage root | 503/404 | `cloud/storage_service.py` |
| 12 | Rate-limit breach | sliding-window middleware | 429 + `Retry-After` header | 429 | `middleware/rate_limit.py` |
| 13 | Unexpected server error | global handler | clean 500 JSON, full traceback only in **logs** | 500 | `middleware/error_handlers.py` |

## The resilience star: AI fallback

```text
request -> get_diet_engine()
             ├── AI_PROVIDER=rule_based ────────────► RuleBasedEngine
             └── AI_PROVIDER=auto|ai_api
                    ├── key configured? ──► AIApiEngine (timeout 20 s)
                    │        │
                    │        ├─ success ──► plan (engine_used=ai_api)
                    │        └─ ANY failure ─┐
                    └── no key ──────────────┤
                                             ▼
                                    RuleBasedEngine (engine_used=rule_based)

              -> the user ALWAYS receives a plan; the truth of which
                 engine answered is recorded on the plan itself
```

Why this matters architecturally: the dependency that can fail (third-party
AI) is **never on the critical path**. Degradation is graceful, observable
(logs + `engine_used`), and honest.

## Transactional pattern for file uploads (storage ↔ DB)

```text
1. validate (ext, size, magic bytes)          fail -> 415/413, nothing stored
2. storage.upload(bytes)                      fail -> 503, nothing stored
3. db.insert(metadata)                        fail -> storage.delete(object)  [compensation]
4. commit -> 201
```

There is no point where the system holds "an object without metadata" or
"metadata without an object" after the request completes — the classic
two-resource consistency demo, done with a compensating action because
cross-service transactions aren't available.

## Retry guidance for clients

- **503 (storage/DB):** retry with backoff (idempotent GETs are safe; uploads
  are safe because keys are unique per attempt).
- **429:** honor `Retry-After`.
- **5xx from AI path:** never happens — fallback already absorbed it.
- **4xx:** do not retry; fix the request.

## What the demo explicitly does NOT model (honest limitations)

- Multi-instance rate limiting (needs Redis) — single-instance only.
- Circuit-breaker around the AI API (the fallback already caps blast radius;
  a breaker would additionally save the failed-call latency).
- Dead-letter queues for background jobs (no background jobs in MVP).
- Automated DB failover (managed by Supabase in cloud mode).
