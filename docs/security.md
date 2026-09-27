# Security

## Controls implemented (with locations)

| Control | Implementation | Where |
|---|---|---|
| Password hashing | bcrypt via passlib (never plaintext at rest) | `cloud/auth_service.py` |
| Authentication | JWT access tokens (HS256, `exp`, `jti`, `iss`) | `cloud/auth_service.py` |
| Token transport | `Authorization: Bearer` header over HTTPS (in prod) | `frontend/src/api/client.js` |
| Authorization | token-required dependency on every protected route | `utils/security.py` |
| User isolation | every query filters `user_id == JWT.sub`; foreign ids → 404 | all plan/file routes |
| No user enumeration | identical 401 for unknown email & wrong password | `routes/auth_routes.py` |
| Hashes never leak | response schemas exclude `password_hash` | `schemas/schemas.py` |
| Input validation | Pydantic schemas with ranges + literal enums at the boundary | `schemas/schemas.py` |
| Upload validation | extension whitelist → size limit → magic-byte sniffing | `utils/validators.py` |
| Path-traversal guard | sanitized object keys + local provider root check | `cloud/storage_service.py` |
| Private object storage | service-key uploads, owner-checked downloads | `storage-design.md` |
| CORS allowlist | only listed origins may call the API with credentials | `app.py` |
| Rate limiting | 10/min on login+register, 120/min elsewhere (per IP) | `middleware/rate_limit.py` |
| Brute-force resistance | bcrypt cost + login rate limit + generic errors | auth stack |
| Secrets management | all secrets via env vars; `.env` git-ignored; `.env.example` documents shape | `config.py` |
| Logging / audit | per-request method, path, status, latency to stdout | `middleware/logging_middleware.py` |
| Health observability | `/api/health`, `/health/db`, `/health/storage` | `routes/health_routes.py` |
| Backups | Supabase managed daily backups (cloud); copy the SQLite file (local) | deployment docs |

## Authentication vs Authorization (the interview classic)

* **Authentication — "who are you?"** Register hashes your password; login
  verifies it and issues a signed JWT containing `sub` (user id) and `exp`.
* **Authorization — "what may you do?"** Every protected route resolves the
  JWT to a `User`; every data query additionally filters by that user id.
  Result: even a *valid* token cannot read another user's plans or files —
  the API returns 404 as if the resource did not exist (no existence leak).

## Encryption, explained simply

* **In transit:** the browser↔API connection uses TLS (HTTPS) in deployment —
  Render and Vercel terminate TLS automatically; locally HTTP is fine because
  nothing leaves the machine.
* **At rest:** Supabase Postgres and Storage encrypt data at rest
  (AES-256, managed). Local SQLite relies on disk-level protection.
* Passwords are **never** recoverable — bcrypt is a one-way hash with a
  per-password salt, and verification re-hashes and compares.

## JWT lifecycle & logout

```text
login  -> server signs {sub, iat, exp, jti} with SECRET_KEY (HS256)
client -> stores token, attaches Bearer header on each request
server -> verifies signature + expiry on EVERY request
logout -> stateless: client discards the token
```

Stateless logout means an un-expired token technically still verifies — the
standard demo-grade answer, with the production-grade upgrades documented:
short expiries + refresh tokens, a revocation/denylist keyed by `jti`, or
rotating refresh tokens in httpOnly cookies.

## Common mistakes students make (avoided here — good talking points)

| Mistake | Why it's dangerous | This project |
|---|---|---|
| Plaintext or MD5/SHA passwords | trivially crackable | bcrypt |
| Secrets committed to git | permanent leak; bots scan for keys | `.env` ignored; examples only |
| `allow_origins=["*"]` with credentials | any site can act as the user | allowlist from env |
| Trusting client-side checks alone | anyone can call the API directly | server-side checks on every route |
| Returning 403 for other users' resources | confirms the resource exists | 404 instead |
| Storing blobs in the database | slow queries, huge backups | object storage |
| Accepting client-provided object keys | path traversal, overwriting others | server-built keys |
| No rate limiting on auth | credential stuffing | per-IP sliding window |
| Verbose error responses | leaks internals/stack traces | minimal `{"detail": …}` contract |
| Skipping upload content checks | malware renamed as images | magic-byte sniffing |

## Threat snapshot (educational)

| Threat | Mitigation |
|---|---|
| Credential stuffing / brute force | bcrypt + rate limiting + generic errors |
| Stolen token replay | TLS, expiry, (production: revocation list) |
| IDOR (guessing ids) | UUID ids + ownership filter + 404 semantics |
| Malicious uploads | whitelist + magic bytes + private bucket |
| SQL injection | SQLAlchemy parameterized ORM — no string SQL |
| XSS | React escapes by default; no `dangerouslySetInnerHTML` |
| CSRF | Bearer-token auth (no ambient cookies) + CORS allowlist |
