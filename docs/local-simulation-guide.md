# Local Simulation Guide — Run Everything on Your Machine

Zero cloud accounts, zero credit cards, zero internet needed after installing
dependencies. This is the "virtual simulation" of the cloud deployment.

## Step 1 — Install required software (once)

| Tool | Version | Check |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Git | any | `git --version` |

## Step 2 — Get the project

```bash
git clone https://github.com/<you>/AI-Powered-Personal-Diet-Planner-Cloud.git
cd AI-Powered-Personal-Diet-Planner-Cloud
# (or create the folder and copy the files if you are building from scratch)
```

## Step 3 — Create a Python virtual environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

## Step 4 — Install dependencies

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

## Step 5 — Configure environment variables

```bash
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env
```
Defaults are correct for local mode. Optional (recommended): give yourself a
real secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
# paste into SECRET_KEY inside .env
```

## Step 6 — Start the backend (Terminal 1)

```bash
uvicorn backend.app:app --reload --port 8000
```
Expected log line:
`Diet planner API started | env=local | storage=local | auth=local | db=sqlite | ai=rule_based`

Verify probes:
- http://localhost:8000/api/health → `{"status": "ok", ...}`
- http://localhost:8000/docs → Swagger UI for all endpoints

## Step 7 — Start the frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```
Open **http://localhost:5173**.

## Step 8 — (Optional) seed demo users (Terminal 3)

```bash
python -m backend.seed_demo
```
Creates: `aasha@demo.com` / `Demo@12345` (vegetarian, weight-loss, allergic to
nuts) and `vikram@demo.com` / `Demo@12345` (non-vegetarian, weight-gain) —
each with a saved plan.

## Step 9 — Register your own user

Landing → **Create free account** → name/email/password (8+ chars).
You land on the Profile page. (A duplicate email returns a friendly 409.)

## Step 10 — Complete your profile

Fill age/height/weight, pick activity level, dietary preference, goal, tap
any allergy tags → **Save profile**. Re-open the page later — values persist
(cloud database at work).

## Step 11 — Generate a diet plan

**Generate Plan** → optionally override goal/diet/exclusions → **✨ Generate
plan**. The card shows 4 meals, approximate nutrition, a hydration reminder,
which engine produced it (rule-based by default) and the educational
disclaimer.

## Step 12 — Save the plan

**💾 Save to cloud** on the plan card → success message → it now appears in
**Saved Plans** and as "Latest plan" on the **Dashboard**.

## Step 13 — Upload a sample file

**Cloud Files** → choose a small PNG/JPG (or PDF/TXT/CSV) → **☁️ Upload to
cloud**. It appears in the table; **⬇️ Download** round-trips the exact bytes.
Try a renamed `.exe` or a >5 MB file — both are rejected with clear errors.

## Step 14 — Retrieve & delete

Dashboard shows latest plan + recent files. Open **Saved Plans → View** for
any plan's detail page; delete plans/files you don't want.

## Step 15 — Test logout / login and isolation

- **Logout** → you're bounced to login; **back-button** returns to login too
  (protected routes guard).
- Log in as the other demo user → their dashboard shows *their* data only.
- Deep-link another user's plan id (`/plans/<id>` from another account) →
  "Plan not found" — user isolation proven.

## Step 16 — Run the automated proof

```bash
# Terminal 3 (with venv active), from the project root:
pytest -v                       # 58 automated tests

# with backend + frontend running (backend on :8000):
python scripts/smoke_test.py    # 17 live end-to-end checks
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: backend` | run commands from the project root, venv active |
| Frontend shows network errors | backend not running on :8000; check Terminal 1 |
| `npm run dev` port busy | `npm run dev -- --port 5174` |
| Port 8000 busy | `uvicorn backend.app:app --reload --port 8001` (update vite proxy target if you do) |
| DB seems stale/corrupt | stop server, delete `diet_planner.db`, restart (recreates schema) |
| bcrypt install error on Windows | keep pinned `bcrypt==4.0.1` from requirements.txt |
