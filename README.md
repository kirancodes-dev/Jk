# 🇮🇳 Jharkhand Societal Innovation & Collaboration Platform
### Government of Jharkhand — Department of Higher & Technical Education
**Smart India Hackathon (SIH 2026) | Problem Statement 26043**

[![CI/CD Pipeline](https://github.com/kirancodes-dev/Jk/actions/workflows/ci.yml/badge.svg)](https://github.com/kirancodes-dev/Jk/actions/workflows/ci.yml)
[![Backend Tests](https://img.shields.io/badge/pytest-25%20passed-brightgreen.svg)](tests/)
[![Frontend Tests](https://img.shields.io/badge/flutter%20test-4%20passed-brightgreen.svg)](frontend/test/)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](backend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20Alpine-336791.svg)](https://www.postgresql.org)
[![Alembic](https://img.shields.io/badge/migrations-Alembic-red.svg)](alembic/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](Dockerfile)
[![License](https://img.shields.io/badge/license-Government%20of%20Jharkhand-green.svg)](#license)

> **"A digital platform to crowdsource societal challenges and facilitate collaborative problem solving through universities and industry partnerships."**

---

## 🏛️ Executive Summary

The **Jharkhand Societal Innovation & Collaboration Platform** is an enterprise-grade, secure, audit-governed public-service ecosystem connecting **Citizens / Gram Panchayats** across all **24 districts of Jharkhand**, **Higher Educational Institutions (HEIs)**, **Government Line Departments**, and **Industry CSR Partners**.

The platform automates grassroots civic problem ingestion, performs explainable AI-driven screening and duplicate detection, allocates challenges to accredited university research teams, enables structured student-faculty problem solving with milestone tracking, attracts corporate CSR co-funding, and enforces independent geotagged field verification before measuring verified community impact.

---

## 🏗️ Production Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│              FRONTEND CLIENTS (Flutter 3.x / Web & Mobile)              │
│  Sovereign Design System • Bilingual Localization (English & Hindi)     │
│  Role-Guarded Dashboards • Real-time Connectivity Status & Sync         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTPS / REST (JSON + JWT Bearer)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               API GATEWAY & SECURITY LAYER (FastAPI)                    │
│  Dual-Token Auth (Access + Refresh Rotation) • Revocation Blacklist      │
│  Fine-Grained Object-Level Authorization (IDOR Prevention)              │
│  Rate Limiting • Correlation IDs (X-Request-ID) • Security Headers       │
└──────────────┬─────────────────────┬────────────────────┬───────────────┘
               │                     │                    │
               ▼                     ▼                    ▼
┌─────────────────────────┐ ┌──────────────────┐ ┌────────────────────────┐
│   CORE DOMAIN LOGIC     │ │  EXPLAINABLE AI  │ │     FILE STORAGE       │
│ Strict 10-Stage State   │ │ NLP Categorizer  │ │ Private Cloud S3 /     │
│ Machine Engine          │ │ Multi-factor     │ │ Local Sanitized Mount  │
│ Event Notification Svc  │ │ Priority Scoring │ │ MIME & Size Validated  │
│ Immutable Audit Trail   │ │ University Match │ │ Geotagged Attachments  │
└──────────────┬──────────┘ └────────┬─────────┘ └────────────────────────┘
               │                     │
               ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 DATA PERSISTENCE LAYER (PostgreSQL 16)                  │
│  28 Relational 3NF Tables • Composite Performance Indexes              │
│  Alembic Migration Versioning • ACID Transaction Guarantees             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔒 Security & Authorization Architecture

### 1. Dual-Token Authentication & Session Management
- **Short-Lived Access Tokens**: 30-minute expiration with cryptographically signed HS256 JWTs.
- **Refresh Token Rotation**: Upon refresh, a new token pair is issued, and the previous refresh token is invalidated.
- **Token Blacklisting / Revocation**: Explicit `/auth/logout` revokes access tokens immediately in cache/database, blocking replay attacks.
- **Rate-Limiting Protection**: Anti-brute force middleware protecting login and OTP endpoints.

### 2. Fine-Grained Object-Level Authorization (IDOR Mitigation)
Unlike naive role-checking (`role == "student"`), every sensitive resource endpoint validates entity ownership and assignment:
- **Task Deliverable Submissions** (`/students/tasks/{id}/submit`): Asserts that the authenticated student is directly assigned to the task or is an active member of the project team.
- **Milestone Approvals** (`/faculty/milestones/{id}/approve`): Asserts that the authenticated faculty is the assigned project mentor or institutional dean.
- **Administrative Operations**: Restricted to verified government officials and university deans with immutable audit logging.

### 3. File Upload Security
- Strict whitelist of MIME types (`image/jpeg`, `image/png`, `application/pdf`).
- File size ceiling (maximum 10MB per file).
- Filename sanitization against directory traversal (`../`) and shell injection attacks.
- Private storage isolation with authenticated download endpoints.

---

## 🔄 Strict 10-Stage Challenge State Machine

Challenges advance strictly through authorized lifecycle transitions. Arbitrary jumps (e.g., `SUBMITTED` ➔ `RESOLVED`) are rejected with `HTTP 400 Bad Request`. Every transition requires an authenticated actor, timestamp, and audit justification:

```
[SUBMITTED] 
    │ (Automated Background Worker)
    ▼
[AI_ANALYSIS] 
    │ (Government Review & Triage)
    ├──────────────┬───────────────────┐
    ▼              ▼                   ▼
[UNDER_REVIEW] [REJECTED]        [DUPLICATE]
    │ 
    ▼
[VALIDATED] 
    │ (Lead University Assignment)
    ▼
[UNIVERSITY_ASSIGNED] 
    │ (Project Creation & Milestone Setup)
    ▼
[IN_PROGRESS] 
    │ (Deliverables Completed)
    ▼
[FIELD_VERIFICATION] 
    │ (Official On-Site Audit Passed)
    ▼
[RESOLVED] 
    │ (Social Impact Accounting)
    ▼
[IMPACT_AUDITED] 
    │ (Formal Closure)
    ▼
[CLOSED]
```

---

## 🧠 Explainable AI & Government Review Queue

The platform replaces black-box AI with transparent, explainable decision support for government administrators:

1. **Domain Classification & Confidence**:
   - Classifies civic reports into 8 domains (*Water & Sanitation*, *Roads & Infrastructure*, *Agriculture & Irrigation*, *Healthcare*, *Clean Energy*, *Education*, *Waste Management*, *Livelihood*).
   - Generates confidence ratings and extracted keyword rationale.
2. **Multi-Factor Priority Scoring**:
   - Weighted scoring formula: **Affected Population (35%)** + **Severity (30%)** + **Urgency (20%)** + **Health Impact (15%)**.
3. **Duplicate Detection & Human Triage**:
   - Multi-signal detection: Text similarity + Geographic coordinate proximity + Temporal proximity + Category overlap.
   - Government triage queue provides side-by-side comparison with explicit `[Confirm Duplicate]` or `[Keep Separate]` human controls.
4. **University Capability Matching**:
   - Recommends institutions based on accredited engineering departments, faculty research domains, available laboratory facilities, and past project track records.

---

## 📐 Field Verification & Real Impact Accounting

A challenge cannot transition to `RESOLVED` through a simple button click. The system requires evidence-based field auditing:

- **Official Field Verification Record**: Geotagged latitude/longitude coordinates, official inspecting officer name and designation, on-site photographs, and laboratory test reports.
- **Impact Metrics Structure**:
  - `Baseline Value`: Quantified pre-project severity (e.g., *Fluoride: 4.5 mg/L*).
  - `Target Value`: Target benchmark (e.g., *WHO Compliant: 1.0 mg/L*).
  - `Actual Value`: Lab-verified post-deployment measurement (e.g., *0.8 mg/L*).
  - `Verification Source`: Official department lab reference ID.
- **Citizen Community Feedback**: Post-resolution satisfaction survey (1–5 star rating + resolution confirmation).

---

## ⚙️ Configuration: Production vs Evaluation Mode

The system enforces strict operational separation between enterprise production deployment and evaluation demo modes via environment variables:

| Setting | Production Mode (`DEMO_MODE=false`) | Evaluation / Jury Mode (`DEMO_MODE=true`) |
| :--- | :--- | :--- |
| **Database** | PostgreSQL 16 with Alembic migrations | SQLite (`sih_jharkhand.db`) with auto-seeding |
| **Demo Endpoints** | Strictly blocked (`HTTP 403 Forbidden`) | `/api/v1/demo/reset` and `/accounts` enabled |
| **Passwords** | Unique, strong user-defined bcrypt passwords | Pre-configured persona credentials for juries |
| **File Storage** | AWS S3 / MinIO private bucket | Local filesystem `/uploads` mount |
| **AI Execution** | Asynchronous background workers | Inline synchronous or async execution |

### Setting Production Mode:
```bash
# In your production .env file:
DEMO_MODE=false
DATABASE_URL=postgresql://user:password@db-host:5432/sih_portal
JWT_SECRET=your-secure-production-random-secret-key-at-least-32-chars
MOCK_AI=false
```

---

## 🧪 Comprehensive Testing Suite

The repository contains **25 automated backend integration tests** and **4 Flutter widget tests**, including full unbroken end-to-end lifecycle verification:

```bash
# Run all backend integration tests:
PYTHONPATH=. backend/.venv/bin/pytest tests/ -v
```

### Test Suite Breakdown:
- **`tests/test_end_to_end_lifecycle.py`**: Complete 10-stage simulation: *Citizen submission ➔ AI screening ➔ Government triage & assignment ➔ University adoption ➔ Student task execution ➔ Faculty milestone approval ➔ Industry CSR grant ➔ Government field verification ➔ Citizen satisfaction feedback ➔ Audit trail verification*.
- **`tests/test_production_upgrade.py`**: Security hardening: *JWT refresh token flow, token logout revocation, object-level authorization (IDOR protection on student and faculty endpoints), demo mode 403 gating, query pagination headers, and async AI background task processing*.
- **`tests/test_backend.py`**: Core domain logic: *Authentication, challenge ingestion, AI analysis, project creation, and analytics aggregation*.
- **`tests/test_university_role_auth.py`**: 3-Tier university authentication, role selection, and token scoping.

### Frontend Widget Tests:
```bash
cd frontend
DEVELOPER_DIR=/Library/Developer/CommandLineTools flutter test
```
- Smoke tests, 4-tier top-level account selection, university context rendering, and multi-role selection modal tests (**4/4 passed**).

---

## 🚀 Deployment & DevOps

### 1. Docker Compose (Production Stack)
Deploy PostgreSQL 16 Alpine and the FastAPI application in a single command:

```bash
# Build and launch services in detached mode:
docker-compose up -d --build

# View application logs:
docker-compose logs -f web

# Health check validation:
curl -f http://localhost:8008/health
curl -f http://localhost:8008/ready
```

### 2. Database Migrations (Alembic)
```bash
# Apply migrations to the current database:
alembic upgrade head

# Generate a new migration revision:
alembic revision --autogenerate -m "describe_schema_change"
```

### 3. Monitoring & Health Probes
- **`/health`**: Basic service health and database connectivity status.
- **`/live`**: Kubernetes liveness probe asserting application responsiveness.
- **`/ready`**: Kubernetes readiness probe executing an active database ping (`SELECT 1`).

---

## 👥 Evaluation & Demonstration Personas (When `DEMO_MODE=true`)

For evaluators and jury testing in sandbox environments (`DEMO_MODE=true`), sample personas are provided:

| Stakeholder Role | Email | Purpose in Demonstration |
| :--- | :--- | :--- |
| **Citizen** | `citizen@jharkhand.gov.in` | Submits challenges with location and photos; provides post-resolution feedback |
| **Govt Administrator** | `admin@jharkhand.gov.in` | Triages incoming issues, reviews AI scores, and routes challenges to universities |
| **University Admin** | `university@bitmesra.ac.in` | Adopts assigned challenges and creates collaborative academic projects |
| **Faculty Mentor** | `faculty@bitmesra.ac.in` | Guides student teams and reviews milestone deliverables |
| **Student Innovator** | `student@bitmesra.ac.in` | Executes project tasks and uploads proof-of-work deliverables |
| **Industry Partner** | `industry@tatasteel.com` | Explores projects and sponsors CSR grants and technical mentorship |

*(Note: In production environments with `DEMO_MODE=false`, all user accounts must be registered individually with unique, secure credentials).*

---

## 📄 Key Documentation References

- **[DEEP_SYSTEM_AUDIT.md](docs/DEEP_SYSTEM_AUDIT.md)**: Full 17-section system audit (Sections A–Q) with source-level line references.
- **[UPGRADE_REPORT.md](docs/UPGRADE_REPORT.md)**: 16-section post-upgrade production report detailing all security, architectural, and database upgrades.
- **[DATABASE.md](docs/DATABASE.md)**: Complete database schema documentation covering all 28 relational entities.
- **[API.md](docs/API.md)**: REST API reference specifications.
- **[CI Pipeline](.github/workflows/ci.yml)**: Automated GitHub Actions CI workflow.

---

## 🏛️ Aligned State Initiatives
- **Jharkhand Higher Education Innovation Policy**: Bridges academic engineering faculties directly to grassroots civic challenges.
- **Jharkhand Industrial Policy 2021**: Directs corporate CSR investments into local university R&D.
- **Mukhyamantri Protsahan Yojana**: Recognizes student innovators with verifiable state digital credentials.

---

## 📜 License
Developed for **Smart India Hackathon 2026** under the auspices of the **Department of Higher & Technical Education, Government of Jharkhand**.  
All rights reserved © 2026.
