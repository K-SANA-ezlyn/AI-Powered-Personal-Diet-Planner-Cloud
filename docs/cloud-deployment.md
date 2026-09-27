# Cloud Deployment (Free Tier)

Two approaches: **A** — actually deployable at zero cost (~35 minutes), and
**B** — the AWS/Azure/GCP reference architecture for reports/interviews.

## Local vs Cloud (what actually changes)

| Aspect | Local mode | Cloud mode |
|---|---|---|
| Database | SQLite file | Supabase Postgres (managed, backed up) |
| Object storage | `uploads/` folder | Supabase private bucket |
| API host | `uvicorn` on :8000 | Render container, TLS + autoscale |
| Frontend | Vite dev server :5173 | Vercel build, CDN, TLS |
| CORS | localhost origins | your Vercel origin |
| Secrets | `.env` file | hosting dashboard env vars |
| Cost | ₹0 / $0 | free tier |

**No code changes** — only `DATABASE_URL`, `STORAGE_PROVIDER`, `SUPABASE_*`
and `CORS_ORIGINS` environment variables move. That portability *is* the
cloud-architecture lesson.

---

## Approach A — Render + Vercel + Supabase (free tier, recommended)

### A1. Supabase — managed Postgres + Storage (~10 min)

1. supabase.com → **New project** (no credit card). Save the DB password.
2. **Database → Connection string → URI** (use the *Connection pooling* 6543
   URI for serverless-friendly pooling). It looks like:
   `postgresql+psycopg2://postgres.<ref>:<PASSWORD>@aws-0-<region>.pooler.supabase.com:6543/postgres`
   *(prepend `postgresql+psycopg2://` — SQLAlchemy needs the driver name.)*
3. **Storage → New bucket**: name `diet-planner-files`, **keep it PRIVATE**.
4. **Project Settings → API**: copy `Project URL` and `service_role` key
   (secret!). Leave the anon key for reference only.

### A2. Render — API (~10 min)

1. Push the repo to GitHub (see README §GitHub).
2. render.com → **New → Web Service** → connect the repo.
3. Settings:
   - **Root directory:** (blank — repo root)
   - **Runtime:** Python 3 · **Build:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
   - **Instance type:** Free
4. **Environment** (from `.env.cloud.example`; set these, not a .env file):
   ```
   ENVIRONMENT=cloud
   SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(48))">
   DATABASE_URL=<A1.2 pooled URI>
   STORAGE_PROVIDER=supabase
   SUPABASE_URL=<A1.4 project URL>
   SUPABASE_SERVICE_KEY=<A1.4 service_role key>
   SUPABASE_STORAGE_BUCKET=diet-planner-files
   CORS_ORIGINS=https://<you>.vercel.app,http://localhost:5173
   AI_PROVIDER=rule_based        # or auto + AI_API_URL/KEY if you have one
   ```
5. **Deploy** — first boot creates all tables via the startup hook.
6. Verify: `https://<service>.onrender.com/api/health` → `{"status":"ok"…}`.

### A3. Vercel — SPA (~5 min)

1. vercel.com → **Add New → Project** → import the repo.
2. **Root directory:** `frontend` (framework auto-detected: Vite).
3. **Environment variable:** `VITE_API_BASE=https://<service>.onrender.com/api`
4. **Deploy** → open `https://<you>.vercel.app`.

### A4. Post-deploy verification (checklist)

```text
□ /api/health returns ok            (app alive)
□ /api/health/db returns ok         (managed Postgres reachable)
□ /api/health/storage returns ok    (bucket writable/readable)
□ Register + login on the Vercel URL (JWT round-trip over TLS)
□ Generate + save a plan            (row in Supabase → Table Editor)
□ Upload a file                     (object visible in Supabase → Storage)
□ CORS: no browser console errors on the Vercel origin
```

> Free-tier notes: Render sleeps after ~15 idle minutes (first request then
> takes ~30 s — mention as a known limitation); Supabase pauses after a week
> of inactivity (restore from the dashboard).

---

## Approach B — AWS / Azure / GCP reference architecture

| Layer | AWS | Azure | GCP | In this repo |
|---|---|---|---|---|
| SPA hosting + CDN | S3 + CloudFront | Static Web Apps | Cloud Storage + Cloud CDN | `frontend/` build |
| API hosting | App Runner / ECS Fargate | Container Apps | Cloud Run | `backend/app.py` (stateless) |
| Managed DB | RDS PostgreSQL / Aurora Serverless | Azure Database for PostgreSQL | Cloud SQL | `DATABASE_URL` swap |
| Object storage | S3 (private + presigned URLs) | Blob Storage (SAS tokens) | Cloud Storage (signed URLs) | `storage_service.py` provider |
| Secrets | Secrets Manager | Key Vault | Secret Manager | env vars today; drop-in swap |
| API gateway | API Gateway | API Management | API Gateway | CORS+rate-limit middleware play this role |
| Autoscaling | App Runner auto / ASG | Container Apps scale rules | Cloud Run concurrency | stateless ⇒ add replicas |
| Logs/monitoring | CloudWatch | Azure Monitor | Cloud Logging | logging middleware → stdout |
| CI/CD | CodePipeline / GitHub Actions | GitHub Actions | Cloud Build | `.github/workflows/ci.yml` |

```text
User ─► CDN (SPA) ─► API Gateway ─► N × API containers (autoscaled)
                                        ├──► Managed Postgres (+replicas)
                                        ├──► Private object storage
                                        └──► Secrets manager / logs / alarms
```

Steps (AWS example, for the report): create RDS Postgres → S3 private bucket →
ECR image or App Runner direct-from-GitHub → inject the same env vars →
health check path `/api/health` → CloudWatch alarms on 5xx/latency. The
application code is identical; only the managed-service endpoints change.

## Monitoring after deployment

- **UptimeRobot** (free) → monitor `/api/health` every 5 min.
- **Render logs** = the request-log middleware output (method, path, status, latency).
- **Supabase dashboard** = DB storage/CPU and storage usage at a glance.
- **GitHub Actions** = green checks on every push; hosts auto-deploy `main`.
