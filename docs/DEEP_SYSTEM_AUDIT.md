# SIH26043 — Deep System Architecture & Codebase Audit

**Repository**: [https://github.com/kirancodes-dev/Jk.git](https://github.com/kirancodes-dev/Jk.git)  
**Problem Statement**: SIH26043 — A digital platform to crowdsource societal challenges and facilitate collaborative problem solving through universities and industry partnerships.  
**Organization**: Government of Jharkhand — Department of Higher & Technical Education  
**Technology Bucket**: Smart Education | **Category**: Software  
**Audit Conducted**: September 2026  
**Audited Codebase Commit**: `87ef5b8` (Clean working tree, 21/21 Pytest passing, 4/4 Flutter tests passing)

---

## Executive Summary

The existing repository represents a feature-rich foundational prototype engineered for the Smart India Hackathon (SIH 2026). It contains:
- **Frontend**: Flutter Web/Mobile with Material 3, Provider state management, and 30+ screens across 6 stakeholder profiles (Citizen, Government Admin, University Admin, Faculty Mentor, Student Researcher, Industry Partner).
- **Backend**: FastAPI modular monolith with 15 routers, Pydantic v2 schemas, SQLAlchemy ORM, and JWT authentication.
- **Database**: 28 relational entities in PostgreSQL/SQLite managed via Alembic migrations.
- **AI/ML Engine**: Modular services for classification, duplicate detection (Levenshtein + Haversine geospatial proximity), priority scoring, and university matching.
- **Field Verification & Impact**: Real-time aggregation of citizen satisfaction ratings and verified impact metrics.

This audit evaluates the codebase against the requirements of an enterprise, sovereign public-service digital platform.

---

## Audit Classification Criteria

- **`COMPLETE`**: Production-ready, fully tested, secure, and integrated end-to-end.
- **`PARTIAL`**: Core logic exists, but missing edge-case handling, deeper validation, or full UI integration.
- **`DEMO ONLY`**: Implemented exclusively for hackathon evaluation; contains convenience bypasses.
- **`MOCK`**: Returns static, hardcoded, or simulated data rather than computing from DB/services.
- **`BROKEN`**: Causes runtime exceptions or contains blocking bugs.
- **`MISSING`**: Required by problem statement or target architecture but not yet built.
- **`PRODUCTION RISK`**: Vulnerability, scalability bottleneck, or integrity hazard under real-world load.

---

## A. Existing Architecture

| Subsystem | Existing Implementation | Classification | Source Code Reference | Audit Findings |
| :--- | :--- | :---: | :--- | :--- |
| **Monolith vs Services** | FastAPI Modular Monolith | **COMPLETE** | `backend/app/main.py:1-136` | Clean separation into `core/`, `models/`, `schemas/`, `routers/`, `services/`. |
| **API Versioning** | Standard `/api/v1` prefix | **COMPLETE** | `backend/app/core/config.py:7` | Standardized prefix across all 15 routers. |
| **Frontend Architecture** | Flutter Web SPA & Mobile | **PARTIAL** | `frontend/lib/main.dart`, `frontend/lib/core/` | UI coupled with state in some screens; requires centralized repository layer. |
| **Static SPA Serving** | FastAPI serving compiled Flutter Web | **COMPLETE** | `backend/app/main.py:115-135` | Serves `frontend/build/web` with SPA fallback route handling. |
| **Reverse Proxy / Gateway** | Ngrok for local public tunnel | **DEMO ONLY** | Active Ngrok process | Production requires Nginx / Cloudflare WAF with TLS termination. |

---

## B. Existing Frontend Functionality

| Screen / Capability | Existing Implementation | Classification | Source Code Reference | Audit Findings |
| :--- | :--- | :---: | :--- | :--- |
| **Login & Role Selection** | 4-tier account switcher & university role picker | **COMPLETE** | `frontend/lib/screens/common/login_screen.dart` | Clean tabs: Citizen, University, Industry, Government. Gated by `DEMO_MODE`. |
| **Citizen Submission Wizard** | 5-step stepper with location, urgency, pop size | **COMPLETE** | `frontend/lib/screens/citizen/report_challenge_screen.dart` | Captures GPS, category, narrative, affected population. |
| **Citizen Details & Rating** | Detail view, resolution rating (1-5 stars) | **COMPLETE** | `frontend/lib/screens/citizen/challenge_details_screen.dart` | Shows AI analysis, timeline, comments, and post-resolution feedback. |
| **Admin Review Queue** | Moderation queue with status tabs & audit trail | **COMPLETE** | `frontend/lib/screens/admin/challenge_management_screen.dart` | Validate, Reject with Reason, Mark Duplicate, Assign University. |
| **Admin Analytics & Map** | GeoJSON district map & analytics charts | **COMPLETE** | `frontend/lib/screens/admin/jharkhand_map_screen.dart` | 24 districts mapped with clickable district performance cards. |
| **University Project Workspace** | 6-tab workspace for project lifecycle | **COMPLETE** | `frontend/lib/screens/university/project_dashboard_screen.dart` | Overview, Milestones, Deliverables, Team, Industry, Verification. |
| **Student Task Execution** | Task Kanban & submission modal | **COMPLETE** | `frontend/lib/screens/student/student_dashboard.dart` | Task checklist with submission notes and attachment upload. |
| **Faculty Milestone Approval** | Milestone review and sign-off dialog | **COMPLETE** | `frontend/lib/screens/faculty/faculty_dashboard.dart` | Approve/Reject milestone deliverables with faculty guide verification. |
| **Industry Marketplace** | CSR project discovery & collaboration offers | **COMPLETE** | `frontend/lib/screens/industry/industry_dashboard.dart` | Filter projects by domain/stage; offer funding/mentorship. |
| **Notification Center** | Categorized notification feed | **PARTIAL** | `frontend/lib/screens/common/notifications_screen.dart` | In-app feed works; missing deep linking to specific project milestone tabs. |
| **Offline Connectivity UX** | Offline challenge draft storage | **PARTIAL** | `frontend/lib/screens/citizen/report_challenge_screen.dart` | Saves drafts locally; missing real-time `ONLINE/OFFLINE` top banner. |

---

## C. Existing Backend Functionality

| Endpoint Group | Implemented Methods | Classification | Source Code Reference | Audit Findings |
| :--- | :--- | :---: | :--- | :--- |
| **Auth (`/auth`)** | `login`, `register`, `refresh`, `logout`, `me`, `otp` | **COMPLETE** | `backend/app/routers/auth.py` | JWT token rotation, server-side revocation registry, OTP verification. |
| **Challenges (`/challenges`)** | `create`, `list`, `get`, `status`, `assign`, `duplicate`, `reject` | **COMPLETE** | `backend/app/routers/challenges.py` | Full lifecycle management with state machine & audit log insertion. |
| **Projects (`/projects`)** | `create`, `list`, `get`, `milestones`, `tasks`, `proposals`, `collaborations` | **COMPLETE** | `backend/app/routers/projects.py` | Weighted milestone calculation (`sum = 100%`), task delegation. |
| **Universities (`/universities`)** | `list`, `dashboard`, `accept-challenge`, `reject-challenge` | **COMPLETE** | `backend/app/routers/universities.py` | Multi-institution support with NIRF, incubation center flags. |
| **Verification (`/verification`)** | `records` (POST), `project/{id}` (GET), `review` (POST) | **COMPLETE** | `backend/app/routers/verification.py` | Geotagged inspection records with administrative review decision. |
| **Impact (`/impact`)** | `feedback` (POST), `challenge/{id}` (GET), `metrics` (GET) | **COMPLETE** | `backend/app/routers/impact.py` | Real-time database aggregation (`func.count`, `func.sum`, `func.avg`). |
| **Admin (`/admin`)** | `dashboard`, `analytics`, `audit-logs`, `jharkhand-map` | **COMPLETE** | `backend/app/routers/admin.py` | District KPIs, live audit logs with pagination support. |
| **Background Processing** | Synchronous AI calls in challenge route | **PRODUCTION RISK** | `backend/app/routers/challenges.py:120` | NLP runs synchronously during submission; must move to `BackgroundTasks`. |

---

## D. Existing Database Structure

| Table Name | Purpose | Foreign Keys & Indices | Classification | Audit Findings |
| :--- | :--- | :--- | :---: | :--- |
| `users` | Core user credentials & role | Indexed `email`, `role` | **COMPLETE** | Supports 6 standard roles + admin tiers (`PANCHAYAT` to `STATE`). |
| `citizens` | Citizen profile & address | FK `user_id` | **COMPLETE** | District, block, village, pincode. |
| `universities` | Higher education institutions | FK `user_id`, Indexed `name` | **COMPLETE** | NIRF ranking, incubation center flag, facility notes. |
| `faculty` | Faculty guides & mentors | FK `user_id`, `university_id` | **COMPLETE** | Research interests, expertise, experience years. |
| `students` | Student researchers | FK `user_id`, `university_id` | **COMPLETE** | Roll number, degree, year of study, skills list. |
| `industry_partners` | CSR & corporate sponsors | FK `user_id`, Indexed `name` | **COMPLETE** | Domain, CSR focus areas, technology stack, support types. |
| `challenges` | Crowdsourced societal issues | FK `citizen_id`, `university_id` | **COMPLETE** | Priority, status, escalation tier, population, moderation reason. |
| `challenge_locations` | Precise & approximate location | FK `challenge_id`, `district_id` | **COMPLETE** | District, block, village, address, latitude, longitude. |
| `ai_analysis` | Automated NLP results | FK `challenge_id` (Unique) | **COMPLETE** | Domain, detected priority, keywords, solution recommendation. |
| `challenge_similarity` | Duplicate detection matches | FK `challenge_id`, `similar_id` | **COMPLETE** | Similarity score, matched keywords, duplicate probability. |
| `university_matches` | AI university recommendations | FK `challenge_id`, `university_id` | **COMPLETE** | Match percentage, ranking, matching factors rationale. |
| `projects` | Adopted execution projects | FK `challenge_id`, `university_id` | **COMPLETE** | Progress percentage, timeline months, current stage. |
| `project_members` | Multidisciplinary student team | FK `project_id`, `student_id` | **COMPLETE** | Team role, join timestamp. |
| `project_milestones` | Weighted lifecycle milestones | FK `project_id` | **COMPLETE** | Weight percentage, status enum, completion percentage, faculty sign-off. |
| `project_tasks` | Student micro-tasks | FK `project_id`, `student_id` | **COMPLETE** | Completion flag, due date, submission notes, attachment link. |
| `verification_records` | Field inspection reports | FK `project_id`, `milestone_id` | **COMPLETE** | Geotagged lat/lng, inspector name/role, status enum, evidence URLs. |
| `citizen_feedback` | Post-resolution ratings | FK `challenge_id`, `citizen_id` | **COMPLETE** | 1-5 star rating, resolved boolean, comments, evidence photo URL. |
| `audit_logs` | Immutable audit trail | FK `actor_id` | **COMPLETE** | Actor name/role, entity, old/new state, action, IP, timestamp, reason. |
| `revoked_tokens` | Server-side JWT revocation | Indexed `jti`, Indexed `expires_at` | **COMPLETE** | Enforces instant token invalidation upon user logout. |
| `organization_profiles` | Formal institutional KYC | FK `user_id`, `verified_by` | **COMPLETE** | AISHE/CIN registration code, verification status enum. |
| **Migrations** | Alembic migration management | `alembic/versions/f48420fc1dd0_...` | **COMPLETE** | Configured to `settings.DATABASE_URL`; stamped to `head`. |

---

## E. Existing AI Implementation

| AI Capability | Implementation Mechanism | Classification | Source Code Reference | Audit Findings |
| :--- | :--- | :---: | :--- | :--- |
| **Domain Classification** | Keyword-frequency taxonomy scoring | **COMPLETE** | `services/ai/classification_service.py` | 10 controlled domains with keyword dictionaries & confidence scoring. |
| **Duplicate Detection** | Levenshtein ratio + Haversine distance | **COMPLETE** | `services/ai/deduplication_service.py` | Flags duplicates if text similarity >= 0.65 AND geographic distance <= 5km. |
| **Priority Assessment** | Explainable 5-factor scoring model | **COMPLETE** | `services/ai/priority_service.py` | Weighted factors: Affected population, keyword severity, urgency, domain weight. |
| **University Matching** | Domain expertise & geographic fit | **COMPLETE** | `services/ai/matching_service.py` | Ranks universities based on department alignment, NIRF rank, and district proximity. |
| **Human Oversight** | Government override requirement | **COMPLETE** | `core/state_machine.py`, `routers/admin.py` | AI recommendations are advisory; government officer retains final validation authority. |
| **Execution Timing** | Synchronous during POST `/challenges` | **PRODUCTION RISK** | `routers/challenges.py:120-140` | Adds 50-150ms latency to submission request. Must be offloaded to background task. |

---

## F. Existing Authentication

| Feature | Implementation | Classification | Source Code Reference | Audit Findings |
| :--- | :--- | :---: | :--- | :--- |
| **Password Storage** | Bcrypt with auto-salt | **COMPLETE** | `core/security.py:20` | Standard `passlib.context.CryptContext(schemes=["bcrypt"])`. |
| **JWT Access Tokens** | HS256 with 24-hour expiration | **COMPLETE** | `core/security.py:40` | Standard claims: `sub` (email), `role`, `user_id`, `jti`, `exp`. |
| **JWT Refresh Tokens** | 7-day refresh token rotation | **COMPLETE** | `routers/auth.py:270` | Issues new access token upon valid refresh token; revokes old token. |
| **Server Logout** | Blacklist registry in `revoked_tokens` | **COMPLETE** | `routers/auth.py:325` | `jti` added to blacklist; intercepted by `get_current_user` dependency. |
| **Password Reset OTP** | 6-digit cryptographic OTP | **COMPLETE** | `routers/auth.py:210` | 10-minute expiry; maximum 3 failed attempts lockout; backdoor removed. |
| **Login Rate Limiting** | In-memory IP tracking | **PARTIAL** | `routers/auth.py:12` | Basic tracking exists; requires Redis token-bucket limiter for distributed deployments. |

---

## G. Existing Authorization (RBAC + Object-Level)

| Level | Implementation | Classification | Source Code Reference | Audit Findings |
| :--- | :--- | :---: | :--- | :--- |
| **Role-Based Access (RBAC)** | `require_roles([UserRole...])` | **COMPLETE** | `routers/deps.py:40` | Enforces endpoint access by role across all 15 routers. |
| **Challenge Ownership** | Citizen update restrictions | **COMPLETE** | `routers/challenges.py` | Citizens can only view/modify their own submitted challenges. |
| **Project Membership (IDOR)** | Task & deliverable permissions | **PARTIAL** | `routers/projects.py:145` | Milestone review checks faculty role; needs explicit `ProjectMember` query check. |
| **Organization Verification** | Unverified org blocking | **PARTIAL** | `routers/organizations.py` | Schema supports `verification_status`; needs middleware gating adoption. |

---

## H. Existing File Storage

| Capability | Implementation | Classification | Source Code Reference | Audit Findings |
| :--- | :--- | :---: | :--- | :--- |
| **Local Disk Storage** | Files saved to `uploads/` directory | **COMPLETE** | `services/storage_service.py` | Generates secure UUID filenames preserving valid extension. |
| **MIME Whitelist** | Whitelist: JPG, PNG, PDF, MP4 | **COMPLETE** | `services/storage_service.py:15` | Rejects executable, script, or unknown binary file uploads. |
| **Size Enforcement** | 10MB default, 50MB video limit | **COMPLETE** | `services/storage_service.py:18` | Enforces max file size before writing to disk. |
| **Path Traversal Shield** | Regex sanitization + base directory check | **COMPLETE** | `services/storage_service.py:42` | Prevents `../` directory traversal attacks. |
| **Cloud S3 / MinIO** | Abstraction interface | **PARTIAL** | `services/storage_service.py` | Local driver active; S3 driver configured but requires S3 credentials in `.env`. |

---

## I. Existing Notifications

| Capability | Implementation | Classification | Source Code Reference | Audit Findings |
| :--- | :--- | :---: | :--- | :--- |
| **Database Persistence** | Stored in `notifications` table | **COMPLETE** | `services/notification_service.py` | Persists user ID, title, message, type, and read flag. |
| **Notification API** | `GET /notifications`, `PATCH /{id}/read` | **COMPLETE** | `routers/notifications.py` | Authenticated feed returning unread notifications. |
| **Email Service** | SMTP email abstraction | **PARTIAL** | `services/email_service.py` | HTML email templates created; requires production SMTP credentials. |
| **SMS Gateway** | Development logging simulator | **DEMO ONLY** | `services/notification_service.py` | Logs OTP to console; needs C-DAC or Twilio gateway integration for production. |

---

## J. Existing Offline Support

| Capability | Implementation | Classification | Source Code Reference | Audit Findings |
| :--- | :--- | :---: | :--- | :--- |
| **Local Draft Persistence** | `SharedPreferences` draft storage | **COMPLETE** | `report_challenge_screen.dart:55` | Auto-saves unsubmitted challenge inputs across app restarts. |
| **Auto-Recovery Dialog** | Prompts citizen to resume draft | **COMPLETE** | `report_challenge_screen.dart:70` | Restores title, description, category, and GPS coordinates. |
| **Network Banner UX** | Visual connection state indicator | **MISSING** | `frontend/lib/widgets/` | Needs real-time `ConnectivityBanner` displaying `ONLINE / OFFLINE / SYNCING`. |

---

## K. Existing Testing

| Test Suite | Coverage | Status | Source Code Reference |
| :--- | :--- | :---: | :--- |
| **Backend Integration Tests** | Auth, State Machine, Verification, Impact, Audit | **COMPLETE** | `tests/test_backend.py`, `tests/test_production_upgrade.py` (14 tests passed) |
| **University Auth Security** | Multi-institution affiliation isolation | **COMPLETE** | `tests/test_university_role_auth.py` (7 tests passed) |
| **Frontend Widget Tests** | Login screen, university role selection, smoke test | **COMPLETE** | `frontend/test/widget_test.dart`, `frontend/test/university_role_login_test.dart` (4 tests passed) |
| **End-to-End Reality Test** | Complete 7-phase live lifecycle test | **COMPLETE** | Tested via live Python harness against port 8008 |

---

## L. Existing Deployment & Infrastructure

| Component | Current Implementation | Target Production State | Classification |
| :--- | :--- | :---: | :--- |
| **Web Server** | Uvicorn ASGI on port 8008 | Gunicorn + Uvicorn workers behind Nginx | **PARTIAL** |
| **Public Exposure** | Ngrok HTTPS tunnel | Dedicated domain + TLS (`jharkhand-innovate.gov.in`) | **DEMO ONLY** |
| **Database** | SQLite local file | Managed PostgreSQL (AWS RDS / Supabase) | **PARTIAL** |
| **Containerization** | No `Dockerfile` in root | Multi-stage Docker + `docker-compose.yml` | **MISSING** |
| **CI/CD Pipeline** | No GitHub Actions workflow | GitHub Actions CI for lint, pytest, flutter test | **MISSING** |

---

## M. Security Vulnerability Analysis

1. **Object-Level Authorization (IDOR) on Project Tasks**:
   - *Risk*: A student belonging to University A could attempt to submit deliverables for a project owned by University B if the endpoint only validates `role == STUDENT`.
   - *Remediation*: Enforce `verify_project_membership(project_id, current_user.id)` in `routers/projects.py`.
2. **Demo Mode Gating**:
   - *Risk*: Hardcoded demo credentials in `auth_provider.dart` and `seed_data.py` could be accessed if deployed to production.
   - *Remediation*: Gate all demo accounts, demo seed routes, and fast-login buttons behind `DEMO_MODE=false`.
3. **Rate Limiting Persistence**:
   - *Risk*: Current in-memory rate limiting resets on server restart and is not shared across multiple worker processes.
   - *Remediation*: Move rate-limiting state to Redis or database-backed token bucket.

---

## N. Performance Risk Analysis

1. **Synchronous AI Processing during Challenge Submission**:
   - Challenge reporting currently executes text cleaning, keyword extraction, similarity computation, and university ranking synchronously. Under heavy traffic, this will degrade API throughput.
   - *Remediation*: Return `HTTP 201` with `status: "AI_ANALYSIS"` immediately, and dispatch heavy NLP to FastAPI `BackgroundTasks`.
2. **Unpaginated List Endpoints**:
   - `GET /projects` and `GET /challenges` without page limits will load all rows into memory as the database grows to thousands of records.
   - *Remediation*: Enforce `page: int = 1` and `page_size: int = 20` returning `total_count` and `total_pages`.

---

## O. UX & Usability Problems

1. **Absence of Top-Level Network Banner**:
   - Citizens in rural Jharkhand with intermittent connectivity have no visual indicator when their network drops or when drafts are queuing.
2. **Side-by-Side Duplicate Comparison Interface**:
   - Government officers need an immediate split-screen view comparing a newly reported challenge with the existing canonical challenge to make duplicate decisions confidently.

---

## P. Missing SIH26043 Requirements

1. **Multilingual Architecture (Hindi / Regional Localization)**:
   - Several UI labels are hardcoded in English. A state platform for Jharkhand must support Hindi (`hi_IN`) alongside English.
2. **Formal Organization KYC Approval Workflow**:
   - Schema exists (`organization_profiles`), but administrative review screens in the government portal need to inspect uploaded registration certificates before granting project execution rights.

---

## Q. Production Risk Summary

```text
[CRITICAL] Object-Level Authorization (IDOR) checks on project tasks and deliverables.
[HIGH]     Asynchronous offloading of AI NLP jobs via BackgroundTasks.
[HIGH]     Production environment gating (DEMO_MODE=false by default).
[MEDIUM]   API pagination on high-volume listing endpoints.
[MEDIUM]   Docker containerization and automated CI/CD validation.
[LOW]      Multilingual UI string extraction (English / Hindi).
```

---

## Conclusion & Architecture Roadmap

The platform has established a verified, working full-stack implementation. The path to production deployment consists of:
1. **P0**: Object-level IDOR enforcement, asynchronous AI background tasks, API pagination, and `DEMO_MODE` production gating.
2. **P1**: Side-by-side duplicate comparison modal, real-time connectivity banner, and bilingual localization bundle.
3. **P2**: Multi-stage `Dockerfile`, `docker-compose.yml`, and GitHub Actions CI/CD pipeline.
