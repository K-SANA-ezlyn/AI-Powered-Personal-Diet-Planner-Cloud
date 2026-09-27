# Scalability — 10, 1,000 and 100,000 Users

## Why this design scales at all (the fundamentals)

1. **Stateless application tier.** No sessions, no local files for state —
   the JWT carries identity, all state lives in the DB/object storage.
   Any replica can serve any request ⇒ scale horizontally.
2. **Externalized state.** Managed Postgres + object storage.
3. **12-factor config.** Scaling = launching more containers with the same
   image and env, nothing else.
4. **Cheap AI by construction.** The heavy lifting (meal planning) is a
   deterministic local engine; the optional remote AI is behind a fallback,
   so scaling the AI path is optional, not existential.

## Scenario walkthroughs

### 10 users — a classroom demo
- **Architecture:** one API instance (Render free tier), Supabase free tier.
- **Bottleneck:** free-tier cold starts (~30 s after idle), not capacity.
- **What breaks first:** nothing, realistically. SQLite local mode would also
  happily serve this.
- **Interview line:** "At this scale the cloud value is availability and
  anywhere-access, not raw throughput."

### 1,000 users — a small college
- **Architecture:** 2+ API replicas behind the platform load balancer;
  Postgres with connection pooling (Supabase pooler, port 6543); CDN in
  front of the SPA (Vercel does this by default).
- **Bottleneck:** DB connections — each replica × each worker holds a pool;
  pooling/`pool_pre_ping` (already configured) keeps this sane.
- **Changes needed:** none to the code. Add replicas in the dashboard.
- **Interview line:** "The rate limiter moves from in-memory to Redis when
  there is more than one instance — that's the only stateful component."

### 100,000 users — a public app
- **Architecture (cloud-native):**
  ```text
                        DNS + CDN  (SPA assets, images)
                             │
                       Load Balancer / API Gateway
                       (TLS, WAF, global rate limits)
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
        API container    API container    API container     (autoscaled on CPU/RPS)
            └───────┬────────┴───────┬─────────┘
                    ▼                ▼
        Cache (Redis: hot dashboards,   Queue (SQS/Cloud Tasks:
        engine results, rate buckets)   export/notify jobs)
                    │
        Postgres primary ──► read replicas (plans/files reads)
                    │
        Object storage (meal photos; near-infinite)
  ```
- **Key moves:**
  - **Autoscaling** containers on CPU/RPS; scale-to-zero for spiky nights.
  - **Read replicas** — the workload is read-heavy (dashboards, lists).
  - **Caching** — dashboard payloads are per-user and idempotent for seconds:
    `dashboard:{user_id}` in Redis with ~30 s TTL absorbs thundering refreshes.
  - **Queues** — plan-export emails, file post-processing → background
    workers instead of request-path work.
  - **Sharding/partitioning** — `diet_plans` partitions by `user_id` hash when
    a single Postgres stops fitting.
  - **CDN** — static SPA + downloadable exports off the API entirely.
- **Bottlenecks in order:** DB write throughput → DB connections → rate
  limiter state → (rarely) CPU.
- **Interview line:** "Every change is configuration or infrastructure — the
  application contract doesn't move, because identity is in the token and
  state is already externalized."

## Load-balancing & elasticity notes

| Concern | Answer |
|---|---|
| LB algorithm | round-robin/least-connections at the platform edge; stateless makes any algorithm safe |
| Session affinity needed? | **No** — that's the point of the JWT design |
| Autoscaling trigger | CPU > 60% or RPS per replica > threshold; min 2, max N |
| Cold starts | keep min replicas ≥ 1 in production hours (free tier sleeps — demo limitation) |
| Multi-region | read replicas + storage replication; the SPA is already global via CDN |

## Queues: where they'd slot in

Async work here is intentionally small (plan generation is <10 ms locally),
but the natural queue candidates are: plan-export PDF rendering, email
notifications, AI-batch analytics, thumbnail generation for meal photos. The
architecture note: enqueue from the API, process in workers, never do
unpredictable-latency work inside the HTTP request.

## Elasticity in one sentence

Because the container is stateless and config-driven, "scaling up" is a
replica-count slider — the same image runs at 10 users and 100,000 users;
only the infrastructure around it changes.
