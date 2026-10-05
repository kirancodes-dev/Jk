# Load Test Report

**Measured 2026-10-05 on a single laptop.** These numbers describe this codebase on the hardware below; they are not a prediction for a cloud deployment. The earlier "94 req/s, 0 failures" figure in the submission deck has no test or raw results in the repository, so it is superseded by the measurements here.

## Results at a glance

| Run | Code | Users | req/s | p50 ms | p95 ms | p99 ms | max | failures |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `before_100u_realistic` | original | 100 | 48.9 | 11 | 290 | 340 | 0.4 s | 25 / 8,786 (0.28%) |
| `after_100u_realistic` | fixed | 100 | 48.9 | 7 | 300 | 340 | 0.4 s | 0 / 8,769 (0.00%) |
| `before_200u_stress` | original | 200 | 142.2 | 19 | 330 | 1400 | 118.6 s | 418 / 25,517 (1.64%) |
| `interim_200u_stress` | race + N+1 fixed | 200 | 182.5 | 49 | 2300 | 5700 | 48.4 s | 23 / 32,688 (0.07%) |
| `after_200u_stress` | fixed | 200 | **241.8** | 100 | 770 | 1400 | 5.4 s | **0 / 43,364** |

- **Realistic load** (100 users, 1–3 s think time): throughput is set by the think time (~49 req/s either way). The fixes removed every failure and halved list latency; p95 is dominated by sign-in, which costs ~340 ms of bcrypt by design.
- **Stress** (200 users, 0.2–1 s think time) saturates the laptop, which also runs the load generator and PostgreSQL. The fixed code serves 70% more requests with zero failures, and its worst response falls from 118.6 s to 5.4 s. Its median is higher than the original's because the original shed load: 384 requests waited 30 s for a database connection and then failed, which kept the remaining requests fast. Compare throughput, failures, p99 and max, not p50.

Raw Locust output for every run is in [`docs/load_test/`](load_test/): `<run>_stats.csv`, `<run>_stats_history.csv`, `<run>_failures.csv`, `<run>_exceptions.csv` and a self-contained `<run>.html` report.

## What was tested

**Dataset.** `scripts/seed_load_test_data.py` added 1,200 challenges to the demo seed: 1,215 challenges across all 24 districts and 11 domains, owned by 50 load-test citizens, with locations, AI analyses and status history. Report texts are the 440 labelled reports from the AI evaluation set (English, Hindi, Hinglish, SMS-style). The database was restored from the same snapshot before every run.

**Traffic mix** (`tests/load/locustfile.py`). Every non-2xx response counts as a failure.

| User type | Share | Behaviour (task weights) |
|---|---:|---|
| Citizen | 90% | signs in once per session, then: browse the public challenge list, 20 per page, random page (10); open a challenge (6); "My Challenges" (3); submit a new report with an idempotency key, AI analysis synchronous as in the app (1); sign in again (1) |
| Officer | 10% | signs in as `officer.ranchi@jharkhand.gov.in`, then: review queue, the 100-item list the admin Challenge Management screen loads, optionally filtered by tier (5); open a report (3) |

**Runs.** 100 users, spawn rate 10/s, 3 minutes, think time 1–3 s (realistic); 200 users, spawn rate 20/s, 3 minutes, think time 0.2–1 s (stress).

## Environment

| | |
|---|---|
| Machine | Apple M5, 10 cores (4 performance, 6 efficiency), 24 GB RAM, macOS 26.6.2 |
| App server | `uvicorn backend.app.main:app --workers 4`, the Dockerfile's command, Python 3.12.13, FastAPI 0.142.2, SQLAlchemy 2.1.3, default pool (5 + 5 overflow per worker) |
| Database | PostgreSQL 16.2, default configuration, `max_connections=200`, same machine |
| Load generator | Locust 2.46.7, same machine, so it competes with the server for CPU |
| App settings | `ENVIRONMENT=development`, `DEMO_MODE=true` (the demo-deployment profile) |

**Why not the docker-compose stack:** Docker is not installed on the test machine, so the same image command was run natively against a local PostgreSQL 16. The containers would add a little overhead and different CPU limits.

**Why `DEMO_MODE=true`:** in production mode, sign-in is limited to 20 attempts per minute per client IP, and a load generator on one machine is one IP. With `DEMO_MODE` that limit is 5,000 per minute. Logging, connection pooling and query behaviour are identical, so rate limiting is the only control not exercised here.

## Problems found and fixed

### 1. Audit hash-chain race (HTTP 500 on submit)
Concurrent requests read the same audit-chain head and computed the same next `sequence_number`; the unique constraint then rejected one of them with a 500. This affected 25 of 355 submissions (7%) at 100 users and 266 of 992 (27%) at 200 users. Without the constraint the chain would have forked.
**Fix:** `WorkflowService._record_domain_event` takes a transaction-scoped PostgreSQL advisory lock before reading the head (commit `ecb5aff`). `tests/test_audit_chain_concurrency.py` runs 12 concurrent writers; it fails 9 of 12 without the lock and passes with it.

### 2. N+1 queries on the challenge lists
The list endpoints lazily loaded each row's location and assigned university.
**Fix:** eager loading in `GET /challenges`, `/challenges/my` and `/challenges/nearby` (commit `056ece3`). `tests/test_list_query_budget.py` caps a 15-item page at 4 queries.

| Request (1,215 challenges in DB) | SQL queries before | after |
|---|---:|---:|
| `GET /challenges?page=3&page_size=20` | 22 | 2 |
| `GET /challenges?page=1&page_size=100` (review queue) | 102 | 2 |
| `GET /challenges/my` (citizen with 47 reports) | 56 | 5 |
| `GET /challenges/nearby?district=Ranchi` | 21 | 1 |

### 3. Audit lock held during AI matching
After fix 1, the synchronous AI step recorded its status transition *before* university matching and the duplicate search, so both ran while holding the chain lock. Submissions queued behind each other while holding database connections, and the pools ran out (the `interim_200u_stress` run: submit median 2.6 s, 23 failures).
**Fix:** the transition is recorded last in the same transaction (commit `aa22aa7`). Submit median under stress: 2,600 ms → 530 ms; failures 23 → 0.

### Per-endpoint before → after

**Realistic, 100 users**

| Endpoint | Requests | p50 ms | p95 ms | p99 ms | Failures |
|---|---:|---:|---:|---:|---:|
| `POST /auth/login` | 466 → 459 | 340 → 340 | 340 → 360 | 350 → 380 | 0 → 0 |
| `GET /challenges?page=[n]` | 3,710 → 3,694 | 11 → 7 | 16 → 11 | 30 → 20 | 0 → 0 |
| `GET /challenges/[id]` | 2,636 → 2,561 | 7 → 7 | 12 → 13 | 17 → 33 | 0 → 0 |
| `GET /challenges/my` | 1,087 → 1,124 | 13 → 6 | 19 → 13 | 28 → 33 | 0 → 0 |
| `POST /challenges` | 355 → 387 | 68 → 71 | 81 → 110 | 110 → 160 | 25 → 0 |
| `GET /challenges?page=1&page_size=100` (review queue) | 532 → 544 | 29 → 8 | 39 → 13 | 66 → 30 | 0 → 0 |

**Stress, 200 users**

| Endpoint | Requests | p50 ms | p95 ms | p99 ms | Failures |
|---|---:|---:|---:|---:|---:|
| `POST /auth/login` | 1,161 → 2,024 | 340 → 1000 | 1500 → 1900 | 30000 → 2900 | 12 → 0 |
| `GET /challenges?page=[n]` | 9,866 → 18,247 | 16 → 77 | 81 → 420 | 30000 → 730 | 74 → 0 |
| `GET /challenges/[id]` | 7,556 → 12,705 | 12 → 100 | 55 → 450 | 360 → 720 | 18 → 0 |
| `GET /challenges/my` | 2,977 → 5,555 | 24 → 88 | 110 → 460 | 30000 → 770 | 44 → 0 |
| `POST /challenges` | 992 → 1,870 | 97 → 530 | 250 → 1100 | 1700 → 1400 | 266 → 0 |
| `GET /challenges?page=1&page_size=100` (review queue) | 2,965 → 2,963 | 44 → 80 | 130 → 430 | 260 → 740 | 4 → 0 |

## Limits and open issues
- **One machine.** Load generator, four app workers and PostgreSQL shared 10 cores, and there is no network latency. A Render starter instance has far less CPU; measure a deployment before quoting numbers for it.
- **Sign-in is CPU-bound.** bcrypt (cost 12) takes ~340 ms of CPU per sign-in. That is intended for password security, but it caps sign-ins at roughly 3 per second per core.
- **Submissions are serialised at the audit chain.** Each submission holds the chain lock for its final insert and commit; at ~10 submissions/s this was not a bottleneck here, but sustained higher write rates need a shorter critical section.
- **Rate limiting, found while preparing this test, not fixed:** `RateLimiter.get_client_ip` trusts the first `X-Forwarded-For` entry, which any client can set, so the per-IP sign-in limit can be bypassed by spoofing the header; the limiter is also in-memory per worker, so 4 workers allow 4× the configured rate; and `RATE_LIMIT_PER_MINUTE` is defined in settings but not used anywhere. This test did not spoof the header.
- **Unpaginated `GET /challenges`** still returns every challenge. The Flutter app always passes `page`/`page_size`, but other clients can request the full table.

## Reproduce
```bash
# 1. Database and schema (PostgreSQL 16)
export DATABASE_URL=postgresql://USER:PASS@localhost:5432/sih_load
export ENVIRONMENT=development DEMO_MODE=true SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
alembic upgrade head

# 2. Seed demo accounts + 1,200 load-test challenges + 50 citizens
PYTHONPATH=. python scripts/seed_load_test_data.py --challenges 1200 --citizens 50

# 3. Start the API exactly as the Dockerfile does
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8008 --workers 4 &

# 4. Run (pip install locust)
LOAD_TEST_WAIT=1,3 locust -f tests/load/locustfile.py --host http://127.0.0.1:8008 \
  --headless -u 100 -r 10 -t 3m --csv docs/load_test/after_100u_realistic --html docs/load_test/after_100u_realistic.html
LOAD_TEST_WAIT=0.2,1 locust -f tests/load/locustfile.py --host http://127.0.0.1:8008 \
  --headless -u 200 -r 20 -t 3m --csv docs/load_test/after_200u_stress --html docs/load_test/after_200u_stress.html
```
With Docker available, the same test can target the compose stack: `docker compose up -d`, then run steps 2 and 4 against `http://localhost:8008` with the compose database URL. Set `ENVIRONMENT=development` and `DEMO_MODE=true` in `.env` first; production mode refuses to start with `DEMO_MODE` on. This compose path was not run for the results above.
