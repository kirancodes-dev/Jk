<div align="center">

<sub>GOVERNMENT OF JHARKHAND · DEPARTMENT OF HIGHER & TECHNICAL EDUCATION · SMART INDIA HACKATHON 2026 · PS 26043</sub>

# SamadhanSetu<br/><sub>Jharkhand Societal Innovation & Collaboration Platform</sub>

### A village reports a broken hand pump. A university builds the fix. A CSR partner funds it. A field inspector proves it works.<br/>One platform runs that whole journey, across all 24 districts, with a human signing off every step.

[![CI/CD Pipeline](https://github.com/kirancodes-dev/Jk/actions/workflows/ci.yml/badge.svg)](https://github.com/kirancodes-dev/Jk/actions/workflows/ci.yml)
[![Backend tests](https://img.shields.io/badge/backend%20tests-214%20passing-brightgreen.svg)](tests/)
[![Flutter tests](https://img.shields.io/badge/flutter%20tests-79%20passing-brightgreen.svg)](frontend/test/)
[![AI accuracy](https://img.shields.io/badge/AI%20accuracy-89.9%25%20held--out-blueviolet.svg)](docs/AI_GOVERNANCE.md)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-Web%20%26%20Mobile-02569B.svg)](https://flutter.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org)

**[For judges](#-for-judges)** · **[Try it in 5 minutes](#-try-it-in-5-minutes)** · **[Team testing guide (PDF)](docs/JK_Portal_Team_Testing_Guide.pdf)** · **[Traceability matrix](TRACEABILITY_MATRIX.md)**

</div>

---

## 🧑‍⚖️ For judges

**What it is.** SamadhanSetu turns a citizen's report (a broken hand pump, a closed health centre) into a tracked project. A district officer validates it, a university builds the fix, a CSR partner funds it, and a field verifier proves it works. Every step is checked by role and district and written to a tamper-evident audit trail.

**Live demo.** *The public URL will be added here once the Render deployment is live.* Anyone can stand it up from this repository with the [one-click Render Blueprint](DEPLOYMENT.md#101-one-click-demo-on-render): [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/kirancodes-dev/Jk) (deploys the default branch). The demo accounts below sign in with `password123`.

**Three numbers, each with its evidence:**

| | | |
| :---: | :--- | :--- |
| **89.9%** | AI domain classification on 198 held-out reports (was 68.2%) | [AI governance](docs/AI_GOVERNANCE.md) · [`ai_accuracy_report.json`](ai_accuracy_report.json) |
| **0 failures** | in 43,364 requests at 241.8 req/s, with 200 simulated users on one laptop | [Load test report](docs/LOAD_TEST.md) |
| **214 + 79** | backend tests (on PostgreSQL 16, as in CI) and Flutter tests passing | [Tests](#-tests) |

**Run it locally in one command** (Docker):
```bash
git clone https://github.com/kirancodes-dev/Jk.git && cd Jk && docker compose -f docker-compose.dev.yml up --build
```
Then open http://localhost:8008. Migrations and every demo account are created on first start.

---

## The problem, and our answer

> *"Develop a digital platform to crowdsource societal challenges from citizens and rural communities, and facilitate collaborative, milestone-driven problem solving through Higher Educational Institutions (HEIs) and industry CSR partnerships."* (SIH 26043)

Grievance portals collect complaints, but they end at "forwarded to department". Nobody builds the solution, and nobody proves it worked.

This platform treats every citizen report as an **R&D project with a finish line**:

```mermaid
flowchart LR
    A["🧑‍🌾 Citizen / Panchayat<br/><b>reports</b> in Hindi or English,<br/>with photos, GPS, voice note"] --> B["🏛️ District Officer<br/><b>validates</b> with explainable<br/>AI triage"]
    B --> C["🎓 University<br/><b>builds</b> through faculty-approved<br/>milestones"]
    C --> D["🏭 Industry CSR<br/><b>funds</b> in tranches,<br/>signs IP agreement"]
    D --> E["🔍 Field Verifier<br/><b>proves</b> it with geotagged<br/>before/after evidence"]
    E --> F["📊 State Admin<br/><b>measures</b> impact across<br/>24 districts"]
```

---

## By the numbers

| 24 | 11 | 12 | 21 | 179 | 61 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| districts, each with GIS boundary checks | challenge domains in a fixed taxonomy | user roles with server-side access control | workflow states (15 on the main path) | REST API operations under `/api/v1` | database tables, 15 versioned migrations |

**The 12 roles** (`UserRole`): Citizen · Community organisation · Gram Panchayat (PRI) · Urban local body (ULB) · Government officer (district officers and field verifiers) · Government admin (state) · University · Faculty mentor · Student · Industry / CSR · Research lab · Innovation hub.

---

## ⚡ Try it in 5 minutes

**1. Open the live demo** (link in [For judges](#-for-judges)) or run it locally:

```bash
git clone https://github.com/kirancodes-dev/Jk.git && cd Jk
docker compose -f docker-compose.dev.yml up --build        # http://localhost:8008
```

**2. Log in.** These demo accounts exist **only when the server runs with `DEMO_MODE=true`** (the demo deployment and the dev compose file). Production refuses to start with `DEMO_MODE` on. Every demo account uses the password **`password123`**, and the login screen of the demo build lists them for one-tap sign-in:

| Persona | Email | What to look at |
| :--- | :--- | :--- |
| 🧑‍🌾 Citizen | `citizen@jharkhand.gov.in` | Report a challenge, see the AI analysis, track it to closure |
| 🏡 Gram Panchayat (PRI) | `pri.angara@jharkhand.gov.in` | Report on behalf of a village |
| 🏛️ District Officer, Ranchi | `officer.ranchi@jharkhand.gov.in` | Review and act on Ranchi challenges; override the AI |
| 🔍 Field Verifier | `verifier.ranchi@jharkhand.gov.in` | Geotagged inspections and lab test results |
| 🎓 University (BIT Mesra) | `university@bitmesra.ac.in` | Accept assignments, create projects |
| 👩‍🏫 Faculty Mentor | `faculty@bitmesra.ac.in` | Approve milestones or request revisions |
| 👨‍💻 Student | `student@bitmesra.ac.in` | Tasks and deliverable uploads |
| 🏭 Industry CSR (Tata Steel) | `industry@tatasteel.com` | Fund projects, sign IP consent |
| 📊 State Admin | `admin@jharkhand.gov.in` | Statewide analytics, district heatmap, impact dashboard |

**3. Follow one challenge end to end:**

1. As **Citizen**, report *"Hand pump broken in Angara village"* with a photo. The AI suggests a domain, a priority and possible duplicates, and shows its reasoning.
2. As **District Officer**, change the AI's category. The override and your written reason go into a tamper-evident ledger. Then validate the challenge.
3. As **University**, accept the assignment and create a project with a milestone. As **Student**, submit a deliverable.
4. As **Faculty**, approve the milestone. As **Industry**, pledge a funding tranche.
5. As **Citizen**, open *Track Solution* and see every step, with who did it and when.

**Then try to break it:** as the Ranchi officer, try to accept or validate a Dhanbad challenge; paste an admin URL as a citizen; or upload a disguised `.exe`. Each attempt is refused.

The full test plan (60+ checks across every role, device and language) is in the **[Team testing guide](docs/JK_Portal_Team_Testing_Guide.pdf)**.

---

## What makes it different

| | Differentiator | Proof in the repo |
| :---: | :--- | :--- |
| 🔒 | **A lifecycle that cannot be skipped.** 15 states on the main path from *Submitted* to *Closed*, 21 in all. Every transition is checked against role, jurisdiction and version, then written to a hash-chained audit trail. | [`workflow_service.py`](backend/app/services/workflow_service.py) · [state machine tests](tests/test_stage4_workflow_state_machine.py) |
| 🧠 | **AI that shows its work and never decides alone.** Transparent scoring, a published accuracy benchmark, and a mandatory human-override ledger. | [`services/ai/`](backend/app/services/ai/) · [benchmark](ai_accuracy_report.json) · [AI governance](docs/AI_GOVERNANCE.md) |
| 🗺️ | **District-level isolation.** A Ranchi officer cannot act on a Dhanbad challenge (accept, validate, assign, reject), and the server enforces this, not just the UI. | [negative security tests](tests/test_stage12_security_negative_properties.py) |
| 📶 | **Built for rural connectivity and tribal languages.** Offline drafts with client UUIDs and idempotency keys sync once, with no duplicates. Voice notes, text scaling, high contrast and screen readers are supported. Full Hindi and English; Santali (Ol Chiki) drafted for the whole citizen journey and Mundari, Ho, Kurukh and Khortha for its core, all awaiting native-speaker review. | [`offline_draft_service.dart`](frontend/lib/core/offline_draft_service.dart) · [translation review](docs/TRANSLATION_REVIEW.md) |
| ✅ | **Impact you can audit.** Closure needs geotagged field evidence, lab measurements with before/after deltas, and a citizen satisfaction rating. | [verification tests](tests/test_stage8_verification_and_closure.py) |
| 🛡️ | **Citizen data rights (DPDP), built in.** Citizens can export, correct and erase their data. Erasure pseudonymizes the person but keeps the audit trail intact. Logs scrub Aadhaar, phone numbers, OTPs and GPS. | [`privacy.py`](backend/app/routers/privacy.py) · [ops & security tests](tests/test_stage11_security_and_operations.py) |

---

## 🔄 The challenge lifecycle

A challenge only moves forward when the right role acts in the right jurisdiction. Illegal jumps (for example *Submitted → Resolved*) are rejected with a clear error.

```mermaid
stateDiagram-v2
    [*] --> SUBMITTED: Citizen / PRI reports
    SUBMITTED --> AI_ANALYSIS: automatic triage
    AI_ANALYSIS --> UNDER_REVIEW: officer picks up
    UNDER_REVIEW --> NEEDS_MORE_INFO: asks citizen
    NEEDS_MORE_INFO --> UNDER_REVIEW: citizen adds detail
    UNDER_REVIEW --> DUPLICATE
    UNDER_REVIEW --> REJECTED
    UNDER_REVIEW --> VALIDATED: officer approves
    VALIDATED --> UNIVERSITY_ASSIGNED: HEI accepts
    UNIVERSITY_ASSIGNED --> TEAM_FORMED
    TEAM_FORMED --> SOLUTION_PROPOSED
    SOLUTION_PROPOSED --> APPROVED
    APPROVED --> PROTOTYPE
    PROTOTYPE --> FIELD_TESTING
    FIELD_TESTING --> DEPLOYMENT
    DEPLOYMENT --> FIELD_VERIFICATION
    FIELD_VERIFICATION --> DEPLOYMENT: inspection failed, rework
    FIELD_VERIFICATION --> RESOLVED: inspector verifies
    RESOLVED --> IMPACT_AUDITED: citizen feedback
    IMPACT_AUDITED --> CLOSED: government sign-off
    CLOSED --> [*]
```

`ChallengeStatus` has **21 states**: the 15 on the main path above, the side states **NEEDS_MORE_INFO**, **DUPLICATE** and **REJECTED**, plus **PAUSED** (any active stage can be paused and resumed) and **REOPENED** (closed, rejected and duplicate challenges can return for re-review). **IN_PROGRESS** is a legacy status still counted by the analytics; the state machine does not move challenges into it. Every change records the actor, their role, the reason and the time.

---

## 🧠 Explainable, governable AI

The AI assists officers. It never approves, rejects or merges anything on its own.

**Priority score.** Five transparent factors, each scored 0–100, combined with versioned weights that administrators can tune:

$$\text{Priority} = 0.30\,\text{Severity} + 0.20\,\text{Urgency} + 0.20\,\text{Population} + 0.15\,\text{Health \& Safety} + 0.15\,\text{Regional Vulnerability}$$

Challenges from NITI Aayog **aspirational districts** (such as Khunti, Simdega and Gumla) score higher on regional vulnerability, so under-served areas are not buried in the queue.

**Duplicate detection.** Each candidate gets a composite score: text similarity 50%, same district or block 25%, same category 15%, recency within 180 days 10%. Text similarity is bag-of-words by default. It can switch to multilingual embeddings (`paraphrase-multilingual-MiniLM-L12-v2`) with `AI_EMBEDDINGS_ENABLED=true`. A match is only a suggestion: *"Requires human review (never auto-suppressed)."*

**Human override ledger.** When an officer changes an AI classification or priority, the platform records the original output, the new value, the officer and their mandatory justification.

**Published accuracy, measured on held-out data.** The domain classifier (`JHARKHAND_TAXONOMY_CLASSIFIER_V3`) matches a weighted English, Hinglish and Devanagari lexicon (`pani`, `nali`, `bijli`, `rojgar`, `aspatal`, `sadak`, `चापाकल`…) with word boundaries, title weighting and topic-negation handling. Every prediction returns its matched keywords, per-domain scores, runner-up and confidence. Anything below **0.70** confidence goes to an officer.

It was tuned only on a separate set of 440 reports (330 TRAIN, 110 DEV). The **198-report TEST set** (18 per domain; English, Hindi, Hinglish) is frozen by a SHA-256 check in CI:

| Model | TEST accuracy | Lowest domains |
| :--- | :---: | :--- |
| V2 (previous release) | 68.2% | Rural Livelihoods 50% · Healthcare, Environment, Public Admin 56% |
| **V3 (this release)** | **89.9% (178/198)** | Education 78% · Rural Livelihoods 78% · Accessibility 83% · all others ≥ 88.9% |

Predictions under the review threshold were right 52.9% of the time, against 93.4% for those accepted automatically, so the threshold catches the doubtful ones. One caveat: the developer saw the TEST set before tuning. Removing all 50 lexicon terms that match only TEST reports lowers accuracy to 89.4%, which bounds that effect. CI fails if TEST accuracy drops below 87.9%. Full method, ablation and limitations: [AI governance](docs/AI_GOVERNANCE.md) · [`ai_accuracy_report.json`](ai_accuracy_report.json).

### 🗣️ Languages

From [`scripts/translation_coverage.py`](scripts/translation_coverage.py). Every tribal-language string is a machine draft: **none is native-reviewed yet** ([review status and sheets](docs/TRANSLATION_REVIEW.md)). Missing strings fall back to Hindi, then English, and production builds can hide unreviewed drafts with `HIDE_UNREVIEWED_TRANSLATIONS=true`.

| Language | Script | Strings | Citizen flow (261 keys) | Core flow (73 keys) | Native-reviewed |
|---|---|---:|---:|---:|---:|
| English | Latin | 575 | 100% | 100% | source |
| Hindi | Devanagari | 575 | 100% | 100% | source |
| Santali | Ol Chiki (font bundled) | 264 | 100% | 100% | 0 |
| Mundari | Devanagari | 75 | 28.4% | 100% | 0 |
| Ho | Devanagari | 74 | 28.4% | 100% | 0 |
| Kurukh | Devanagari | 75 | 28.4% | 100% | 0 |
| Khortha | Devanagari | 75 | 28.4% | 100% | 0 |

### ⚡ Performance

[Load test](docs/LOAD_TEST.md) with Locust on one Apple M5 laptop (server, PostgreSQL and load generator together), 1,215 challenges across 24 districts:

| Users | Throughput | p50 | p95 | p99 | Failures |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 100, realistic think time | 48.9 req/s | 7 ms | 300 ms | 340 ms | 0 / 8,769 |
| 200, stress | 241.8 req/s | 100 ms | 770 ms | 1.4 s | 0 / 43,364 |

The test found and fixed an audit-chain race that failed 7–27% of submissions under load, and N+1 queries (102 → 2 per review-queue page). Raw results are in [`docs/load_test/`](docs/load_test/).

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Client["Flutter 3 · Web & Mobile"]
        UI["Role dashboards · Hindi/English + tribal-language drafts · offline drafts · voice notes · accessibility"]
    end
    subgraph API["FastAPI gateway"]
        SEC["JWT dual-token auth · RBAC + district tenancy · rate limiting · CSP/HSTS · 25 MB body cap"]
        FSM["Workflow state machine<br/>+ hash-chained audit"]
        AI["Explainable AI<br/>priority · dedup · matching"]
        PRIV["DPDP privacy rights"]
    end
    subgraph Data["Data & infrastructure"]
        PG[("PostgreSQL 16<br/>61 tables · Alembic")]
        S3[("Private S3 / MinIO<br/>SSE-S3 · presigned URLs")]
        WK["Background worker<br/>SKIP LOCKED queue · notification outbox"]
    end
    UI -->|HTTPS · REST · Bearer JWT| SEC
    SEC --> FSM & AI & PRIV
    FSM --> PG
    AI --> PG
    PRIV --> PG
    SEC --> S3
    WK --> PG
```

| Layer | Technology |
| :--- | :--- |
| Frontend | Flutter 3 (web + Android/iOS), Provider, custom Jharkhand government theme |
| Backend | Python 3.12+, FastAPI, SQLAlchemy, Pydantic, Alembic |
| Data | PostgreSQL 16, S3/MinIO object storage |
| AI | Explainable multilingual lexicon classifier (2.7 ms per report, no GPU), transparent priority and duplicate scoring, optional Sentence-Transformers embeddings |
| Ops | Docker Compose, GitHub Actions CI (bandit SAST, pip-audit), Prometheus `/metrics`, encrypted backups |

<details>
<summary><b>🔒 Security & privacy details</b></summary>

<br/>

- **Access control:** 12 role types with server-side RBAC. Vertical privilege escalation and horizontal BOLA are both tested, and district officers are confined to their own jurisdiction.
- **Transport & headers:** CSP tuned for Flutter CanvasKit/Wasm, HSTS behind HTTPS, `X-Frame-Options: DENY`, `nosniff`, a strict `Permissions-Policy`, and `no-store` on API responses.
- **Request limits:** 25 MB body cap, 60 s timeout. Rate limits key on the client IP, and `X-Forwarded-For` is honoured only when the request arrives through a private-network proxy (localhost, 10/8, 172.16/12, 192.168/16).
- **Uploads:** magic-byte type checks reject disguised executables and scripts. EICAR detection; photos are stored upright, without EXIF/GPS, at most 2,048 px (86.8% smaller on real photos); UUID-safe filenames; a quarantine prefix; and soft delete with a 30-day restore window, after which the file is purged.
- **Storage:** private buckets with AES-256 SSE and 15-minute presigned URLs. Production refuses to start without S3 or with default secrets (fail closed).
- **Logging:** structured JSON with request IDs. Passwords, JWTs, OTPs, Aadhaar numbers, mobile numbers and precise GPS are redacted automatically.
- **DPDP rights:** `GET /api/v1/privacy/notices` · `GET /api/v1/privacy/my-data` · `PUT /api/v1/privacy/correct-data` · `POST /api/v1/privacy/request-erasure`. These are technical controls, not a legal certification.
- **Demo safety:** `DEMO_MODE` endpoints (`/demo/reset`, `/demo/accounts`) are blocked in production, and production refuses to boot with `DEMO_MODE=true`. The public demo runs as `ENVIRONMENT=demo`, which keeps production's other fail-closed checks.

</details>

<details>
<summary><b>🔔 Notifications & background processing</b></summary>

<br/>

- Notifications are written to a **transactional outbox** first, so no alert is lost during network failures.
- Worker replicas claim jobs with `SELECT … FOR UPDATE SKIP LOCKED`, so no job is processed twice. Stuck jobs are recovered after 5 minutes. Shutdown is graceful on SIGTERM.
- Channel adapters: in-app, SMTP email, SMS, WhatsApp Business and push. SMS, WhatsApp and push are simulated in the demo. All channels retry with exponential backoff.

</details>

---

## 🧪 Tests

```bash
PYTHONPATH=. pytest tests/ -q        # backend: 214 passed (200 test functions) on PostgreSQL 16, as in CI
cd frontend && flutter test           # frontend: 79 passed (62 test cases; some generate several)
```

| Area | Suite |
| :--- | :--- |
| Five end-to-end journeys: citizen, officer, university, industry, executive | [`test_stage12_e2e_journeys.py`](tests/test_stage12_e2e_journeys.py) |
| Privilege escalation, BOLA, cross-district tampering, path traversal, fail-closed config | [`test_stage12_security_negative_properties.py`](tests/test_stage12_security_negative_properties.py) |
| Headers, PII masking, metrics, SSE-S3, EICAR, EXIF, worker locks, DPDP | [`test_stage11_security_and_operations.py`](tests/test_stage11_security_and_operations.py) |
| Lifecycle transitions and illegal-jump rejection | [`test_stage4_workflow_state_machine.py`](tests/test_stage4_workflow_state_machine.py) |
| AI triage, priority, duplicates, override ledger | [`test_stage5_ai_governance.py`](tests/test_stage5_ai_governance.py) |
| Classifier accuracy gate (held-out TEST ≥ 87.9%), frozen test set, explainability | [`test_ai_classifier_v3.py`](tests/test_ai_classifier_v3.py) |
| Audit-chain concurrency, list query budget, SPA path traversal, photo optimisation, attachment purge | [`tests/`](tests/) |
| HEI projects, CSR funding and IP, field verification, notifications, analytics | [`tests/`](tests/) (stages 6–10) |
| Offline sync, multi-role routing, dashboards, localization guard (no hard-coded English), tribal-language coverage and fonts | [`frontend/test/`](frontend/test/) |

Every requirement of PS 26043 is mapped to its models, APIs, screens and tests in the **[Traceability matrix](TRACEABILITY_MATRIX.md)**.

---

## 🚀 Local development

**Prerequisites:** Docker, or Python 3.12+, PostgreSQL 16 and the Flutter 3 SDK.

```bash
# Backend (also serves the compiled Flutter web app)
python3 -m venv backend/.venv && source backend/.venv/bin/activate
pip install -r backend/requirements.txt
export DATABASE_URL=postgresql://USER:PASS@localhost:5432/sih   # the app also reads a local .env
alembic upgrade head
DEMO_MODE=true PYTHONPATH=. python -m backend.app.services.demo_bootstrap   # every demo account
DEMO_MODE=true PYTHONPATH=. uvicorn backend.app.main:app --port 8008 --reload

# Frontend with hot reload (optional)
cd frontend && flutter pub get && flutter run -d chrome --web-port 3000
```

With `DEMO_MODE=true`, demo data is seeded on first start. Reset it with `POST /demo/reset`. Health probes: `/health`, `/live`, `/ready`. Metrics: `/metrics`.

---

## 📚 Documentation

| For | Read |
| :--- | :--- |
| Testers and evaluators | [Team testing guide](docs/JK_Portal_Team_Testing_Guide.pdf) · [Pilot acceptance pack](docs/PILOT_ACCEPTANCE_PACK.md) · [Load test](docs/LOAD_TEST.md) · [AI benchmark](docs/AI_GOVERNANCE.md) |
| Architects | [ARCHITECTURE.md](ARCHITECTURE.md) · [DATABASE.md](DATABASE.md) · [API.md](API.md) · [Full system report (PDF)](docs/SIH_26043_COMPLETE_ARCHITECTURE_AND_SYSTEM_REPORT.pdf) |
| Security reviewers | [SECURITY.md](docs/SECURITY.md) · [AI governance](docs/AI_GOVERNANCE.md) |
| Language reviewers | [Translation review](docs/TRANSLATION_REVIEW.md) · [review sheets](docs/translations/) |
| Decision makers | [Sustainability, cost and funding](docs/SUSTAINABILITY_AND_COST.md) |
| Operations | [DEPLOYMENT.md](DEPLOYMENT.md) · [Disaster recovery](docs/runbooks/disaster_recovery_runbook.md) · [Zero-downtime deploy & rollback](docs/runbooks/deployment_and_rollback.md) · [Secrets rotation](docs/runbooks/secrets_rotation.md) · [Incident response](docs/runbooks/incident_response.md) |

---

## 🏛️ Aligned with Jharkhand state initiatives

- **Jharkhand Higher Education Innovation Policy:** connects faculty and student researchers to real grassroots problems.
- **Jharkhand Industrial Policy 2021:** channels CSR investment into local university R&D.
- **Mukhyamantri Protsahan Yojana:** gives student innovators a verifiable record of their work.
- **Jal Jeevan Mission Jharkhand:** provides priority routing and lab verification for rural drinking-water challenges.

---

<div align="center">

Built by **Team Que Sera** (Team ID 141039) for **Smart India Hackathon 2026**, PS 26043, **Department of Higher & Technical Education, Government of Jharkhand**.<br/>
All rights reserved © 2026.

</div>
