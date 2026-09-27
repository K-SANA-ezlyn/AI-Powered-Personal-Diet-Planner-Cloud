# Test Plan & Manual Test Matrix

**Automated suite:** `pytest -v` → **58 tests** (auth, profile, engine rules,
fallback, plans, files, isolation, health, dashboard).
**Live E2E:** `python scripts/smoke_test.py` → **17 checks**.
**Below:** the manual matrix for the report — run it against your deployment
and record Actual Result + Pass/Fail.

**Environments:** Local mode (SQLite + uploads/) and Cloud mode (Supabase).

| Test ID | Scenario | Input / Steps | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|---|---|
| TC-01 | New user registration | Register with fresh email, name, 8+ char password | 201; user row created; password stored as bcrypt hash only | | |
| TC-02 | Duplicate email registration | Register again with the same email | 409 "Email already registered"; no second row | | |
| TC-03 | Weak password rejected | Register with password `short` | 422 validation error naming min length | | |
| TC-04 | Valid login | Correct email + password | 200; JWT + user object returned | | |
| TC-05 | Invalid login — wrong password | Correct email, wrong password | 401 "Invalid email or password" | | |
| TC-06 | Invalid login — unknown email | Unregistered email | 401 with the *same* message as TC-05 (no enumeration) | | |
| TC-07 | Unauthorized dashboard access | Call `/api/dashboard` with no token | 401; SPA redirects to /login | | |
| TC-08 | Expired/garbage token | Send `Authorization: Bearer not.a.jwt` | 401 | | |
| TC-09 | Profile creation | PUT /api/profile with valid values | 200; GET returns saved values | | |
| TC-10 | Profile range validation | age = 5 | 422 | | |
| TC-11 | Unknown allergy tag | allergies = "pineapple" | 422 with allowed-tags hint | | |
| TC-12 | Diet plan generation | POST /api/diet/generate-plan | 200; 4 meals + nutrition + disclaimer; engine_used set | | |
| TC-13 | Vegetarian preference | Profile diet=vegetarian; generate | No meat items in any meal | | |
| TC-14 | Vegan preference | diet=vegan; generate | No dairy/egg/meat items in any meal | | |
| TC-15 | Non-vegetarian + goal override | Override goal=weight_gain, diet=non_vegetarian | Plan reflects overrides; denser calorie hint | | |
| TC-16 | Allergy exclusion (hard) | Profile allergies=nuts; generate repeatedly | No nut items in any meal, ever | | |
| TC-17 | AI API failure → fallback | Set AI_API_URL to an unreachable URL; generate | 200; plan still delivered; engine_used=rule_based | | |
| TC-18 | Rule-based determinism+variety | Generate on consecutive days | Valid plans; meals differ across days | | |
| TC-19 | Save diet plan | POST /api/plans with generated plan | 201; appears in GET /api/plans and dashboard | | |
| TC-20 | Retrieve plan by id | GET /api/plans/{saved_id} | 200 with the same plan | | |
| TC-21 | Delete plan | DELETE own plan | 200; subsequent GET 404 | | |
| TC-22 | File upload — valid PNG | Upload small real PNG | 201 metadata; object stored; listed | | |
| TC-23 | File download round-trip | Download uploaded file | Bytes identical to upload | | |
| TC-24 | Invalid file — renamed exe | Upload `virus.exe` → then rename to `.jpg` and retry | Both 415 (extension; magic bytes) | | |
| TC-25 | Oversized file | Upload > MAX_FILE_SIZE_MB | 413 | | |
| TC-26 | User A cannot retrieve User B's plan | B's plan id in A's session | 404 (no existence leak); B's data unchanged | | |
| TC-27 | User A cannot retrieve User B's file | B's file id download as A | 404 | | |
| TC-28 | User A cannot delete User B's data | DELETE B's plan/file as A | 404; owner still sees both intact | | |
| TC-29 | Logout | POST /api/auth/logout; discard token client-side | 200; protected pages inaccessible afterwards | | |
| TC-30 | Health probes | GET /api/health, /health/db, /health/storage | All 200 in local; all 200 in cloud | | |
| TC-31 | Cloud DB persistence | Save plan in cloud mode; inspect Supabase Table Editor | Row visible in diet_plans | | |
| TC-32 | Cloud object storage | Upload in cloud mode; inspect Supabase Storage | Object visible under meals/{user_id}/ | | |
| TC-33 | Rate limiting | Hammer /api/auth/login >10×/min from one IP | 429 with Retry-After | | |
| TC-34 | Dashboard aggregate | After 1 plan + 1 file | latest_plan set; totals = 1/1; BMI display note | | |

**Recording results:** copy this table into `reports/manual-test-results.md`,
fill the last two columns, and screenshot the interesting rows (see
`screenshots/README.md`).
