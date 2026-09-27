# REST API Reference

Base URL (local): `http://localhost:8000` · Interactive docs: `/docs` (Swagger UI)

All responses are JSON. Authentication is `Authorization: Bearer <JWT>` on
every route except register/login and health probes.

## Status-code contract

| Code | Meaning here |
|---|---|
| 200 | success |
| 201 | resource created (register, save plan, upload) |
| 400 | invalid value (e.g. unknown allergy tag) |
| 401 | missing/expired/garbage token, or bad credentials |
| 404 | resource not found **or owned by someone else** (deliberate — no existence leak) |
| 413 | upload too large |
| 415 | upload type rejected (extension or magic bytes) |
| 422 | request body fails schema validation (Pydantic) |
| 429 | rate limit exceeded (auth endpoints, 10/min/IP) |
| 503 | storage or database unavailable |

---

## Auth — `/api/auth`

### POST `/api/auth/register` → 201
```json
{ "name": "Aasha Kumar", "email": "aasha@example.com", "password": "8+ chars" }
```
**201** → `{"id","name","email","created_at"}` · duplicate email → **409** ·
weak password → **422**

### POST `/api/auth/login` → 200
```json
{ "email": "aasha@example.com", "password": "…" }
```
**200** → `{"access_token","token_type":"bearer","user":{…}}` ·
unknown email **or** wrong password → **401** with the *same* message
(no user enumeration)

### POST `/api/auth/logout` → 200 (auth)
Stateless: the client discards the token. Server validates the caller.

### GET `/api/auth/me` → 200 (auth)
Returns the authenticated user. Used by the SPA on boot.

---

## Profile — `/api/profile`

### GET `/api/profile` → 200 (auth)
The caller's profile. **404** if not created yet.

### PUT `/api/profile` → 200 (auth) — create-or-update (idempotent)
```json
{
  "age": 28, "height_cm": 165, "weight_kg": 68,
  "activity_level": "moderate",
  "dietary_preference": "vegetarian",
  "goal": "weight_loss",
  "allergies": "nuts",
  "meals_per_day": 3
}
```
Validated ranges: age 10–100, height 100–250, weight 25–300.
`allergies` accepts comma-separated tags from:
`nuts, dairy, gluten, eggs, soy, fish, shellfish` — anything else → **400**.
Activity: `sedentary|light|moderate|active|athlete` ·
Preference: `vegetarian|vegan|non_vegetarian|eggetarian` ·
Goal: `weight_loss|weight_gain|maintenance|fitness` · anything else → **422**.

---

## AI plan — `/api/diet`

### POST `/api/diet/generate-plan` → 200 (auth)
Body optional — overrides default to the saved profile:
```json
{ "goal": "weight_gain", "dietary_preference": "non_vegetarian", "allergies": "soy" }
```
**200** →
```json
{
  "title": "Weight Gain · Non Vegetarian Plan",
  "breakfast": "…(~520 kcal)", "lunch": "…", "snack": "…", "dinner": "…",
  "nutrition_summary": {
    "calories_kcal": 1930, "protein_g": 96, "carbs_g": 268, "fat_g": 61,
    "hydration_reminder": "…", "goal_calorie_hint": "…",
    "estimated_bmi_display_only": 22.2
  },
  "engine_used": "rule_based",
  "goal": "weight_gain", "dietary_preference": "non_vegetarian",
  "disclaimer": "Educational/general wellness example — not medical or clinical nutrition advice."
}
```
`engine_used` records whether the AI API or the rule-based fallback produced
the plan. **Nothing is persisted** — saving is explicit.

---

## Saved plans — `/api/plans`

| Endpoint | Auth | Notes |
|---|---|---|
| POST `/api/plans` | ✓ | body `{"plan": <generated plan>, "title": "optional"}` → **201** |
| GET `/api/plans` | ✓ | caller's plans, newest first |
| GET `/api/plans/{id}` | ✓ | one plan; another user's id → **404** |
| DELETE `/api/plans/{id}` | ✓ | delete own plan; another user's id → **404** |

---

## Cloud files — `/api/files`

| Endpoint | Auth | Notes |
|---|---|---|
| POST `/api/files/upload` | ✓ | multipart `file`; images/PDF/TXT/CSV; ≤ `MAX_FILE_SIZE_MB`; magic-byte checked → **201** metadata |
| GET `/api/files` | ✓ | caller's file metadata, newest first |
| GET `/api/files/{id}/download` | ✓ | owner-only; streams bytes (cloud mode could return a 300 s signed URL instead) |
| DELETE `/api/files/{id}` | ✓ | removes object + metadata row; owner-only |

Metadata shape: `{"id","filename","storage_path","content_type","size_bytes","uploaded_at"}`

---

## Dashboard & health

### GET `/api/dashboard` → 200 (auth)
One aggregate payload: `user`, `profile` (+ `bmi_display`, informational only),
`latest_plan`, `recent_plans[5]`, `recent_files[5]`, `total_plans`, `total_files`.

### GET `/api/health` → 200 (public)
Liveness: `{"status":"ok","app":…,"environment":…,"storage_provider":…,"auth_provider":…}`

### GET `/api/health/db` · `/api/health/storage` → 200 / 503
Readiness probes for the two backing services — used by Render/monitoring.

---

## Error shape

Every error is `{"detail": "<human-readable message>"}` (FastAPI validation
errors additionally include the field path). No stack traces, no internal
identifiers — ever.
