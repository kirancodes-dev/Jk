# SIH26043 — Comprehensive Production Gap Analysis & Architectural Audit
**Platform:** Societal Innovation Collaboration Portal — Government of Jharkhand  
**Date:** September 2026  
**Auditor:** Senior Government Platform & Security Architecture Team  

---

## 1. Executive Summary & Audit Methodology

This audit evaluates the codebase of the **Societal Innovation Collaboration Portal (Jharkhand)** against the rigorous standards required for a state-wide, multi-stakeholder e-governance deployment involving citizens across 24 districts, universities/colleges, faculty researchers, students, CSR/industry leaders, and multi-tier government officers (Panchayat, Block, District, and State levels).

Every capability claimed in project documentation was verified directly against backend Python/FastAPI code, SQLAlchemy models, database seed routines, and Flutter Dart screens/services.

### Summary Classification Matrix
| Area | Implemented | Partially Implemented | Demo/Mock Only | Missing | Production Risk Level |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Authentication & RBAC** | ⚠️ Partial | 6 roles, basic JWT | Hardcoded OTP backdoor (`123456`), no refresh tokens | Granular permissions, token revocation, account lockout, MFA | **CRITICAL** |
| **Organization Verification** | ❌ Missing | None | Auto-verified registrations | Approval workflow, document upload, verification statuses | **HIGH** |
| **Challenge Submission & Privacy** | ⚠️ Partial | Basic form, District dropdown | Exposes exact GPS to all users | Privacy obfuscation, MIME verification, virus scanning, chunked upload | **HIGH** |
| **Moderation & State Machine** | ❌ Missing | Free-form status updates | Any role can set any status | Strict transition state-machine, moderation queue, rejection reasons | **CRITICAL** |
| **AI Modules (Classify, Deduplicate, Priority, Match)** | ⚠️ Partial | Heuristic keyword counter & cosine sim | Opaque scoring, no human override logging | Modular services, confidence calibration, versioning, audit trail | **MEDIUM** |
| **Industry & CSR Marketplace** | ⚠️ Partial | Simple collaboration record | Single offer type, no budget workflow | Escrow/CSR vetting, milestone funding release, MoU tracking | **HIGH** |
| **Milestones & Project Lifecycle** | ⚠️ Partial | Milestones with % values | Arbitrary progress % (not weight-based) | Deliverable evidence submission, multi-party verification, field audits | **HIGH** |
| **Evidence & Impact Measurement** | ❌ Missing | Basic text field | Fixed counter table (`impact_metrics`) | Pre/post baseline metrics, field geotagged evidence, citizen validation | **HIGH** |
| **Audit Logging & Governance** | ⚠️ Partial | `status_history` table only | System text strings | Tamper-evident structured audit log for all mutating actions | **CRITICAL** |
| **Database & Migrations** | ⚠️ Partial | Dual SQLite/Postgres SQLAlchemy | `Base.metadata.create_all` only | Alembic migrations, database indexes, strict check constraints | **HIGH** |
| **Document Storage Security** | ❌ Insecure | Saves to `./uploads` or S3 | Unauthenticated upload endpoint | Private by default, presigned URLs, MIME validation, auth checks | **CRITICAL** |
| **Observability & Error Handling** | ⚠️ Partial | Basic logger / uvicorn | Exposes raw exception traces | Structured JSON logs, request IDs, sanitized production responses | **MEDIUM** |

---

## 2. Detailed Gap Analysis by Lifecycle & Component

### A. Authentication, Authorization & Identity (Phases 3 & 4)
- **Current State (`backend/app/routers/auth.py`, `backend/app/routers/deps.py`):**
  - Uses 6 roles: `CITIZEN`, `UNIVERSITY`, `STUDENT`, `FACULTY_MENTOR`, `INDUSTRY`, `GOVERNMENT_ADMIN`.
  - JWT tokens have a single 7-day expiration with no refresh token mechanism, no token revocation list, and no session invalidation on password change.
  - Hardcoded OTP backdoor in `email_service.py` line 30: `if clean_otp == "123456": return True`.
  - No rate limiting on `/auth/login`, `/auth/register`, `/auth/forgot-password`.
  - Role-checking in routes is coarse (`require_roles([UserRole.GOVERNMENT_ADMIN])`), with no granular permission system (e.g. `challenge.validate`, `project.approve`, `funding.release`).
- **Gaps & Risks:**
  - **Critical Security Flaw:** The hardcoded OTP code allows unauthorized password resets for any citizen, government officer, or university admin.
  - Lacks hierarchical government tiers (Panchayat Sevak, BDO, DC/DM, State Secretary).
  - Lacks organization lifecycle: Universities and Industry partners can self-register without government verification or legal document vetting.

### B. Challenge Lifecycle & State Machine (Phases 5, 6, 52, 53)
- **Current State (`backend/app/routers/challenges.py`):**
  - Challenges can be posted via `POST /challenges`.
  - `POST /challenges/{id}/status` allows any authenticated user (even a student or citizen) to arbitrarily change a challenge's status to `RESOLVED`, `REJECTED`, or `APPROVED`.
  - `GET /challenges/{id}` returns exact GPS coordinates (`latitude`, `longitude`) to any requester, exposing citizen home locations.
- **Gaps & Risks:**
  - **Broken Access Control:** Total lack of status transition validation; lifecycle stages can be skipped or abused.
  - **Citizen Privacy Violation:** Full GPS coordinates exposed to the public. Needs privacy-aware coordinate obfuscation for public queries (e.g. district/block centroid) and exact coordinates restricted to verified district officers.
  - Moderation queue (`SUBMITTED -> SCREENING -> NEEDS_REVIEW -> VALIDATED / REJECTED / DUPLICATE`) is completely missing.

### C. AI Pipeline Architecture (Phases 7, 8, 9, 10, 11, 33)
- **Current State (`backend/app/services/ai_service.py`):**
  - All AI logic lives in a single 237-line file using static dictionary keyword matching and in-memory cosine similarity.
  - Duplicate detection checks cosine similarity against loaded database challenges with a basic threshold.
  - Priority scoring sets priority based on keyword occurrences (`CRITICAL`, `HIGH`, etc.) without factoring in affected population numbers, geographic vulnerability, or multi-criteria weights.
  - No explanation breakdown, no confidence calibration, and no storage of AI model version, input snapshot, or government override log.
- **Gaps & Risks:**
  - Monolithic design makes pluggable LLM/embeddings integration fragile.
  - Lack of audit trail violates government AI governance principles: every AI recommendation must document input hash, model/version, confidence, and human override with justification.

### D. File Uploads & Document Security (Phases 26, 40)
- **Current State (`backend/app/services/storage_service.py`, `backend/app/routers/challenges.py`):**
  - `POST /challenges/upload` has NO authentication required.
  - No file size limits, MIME type validation, or extension whitelisting.
  - Static mounting of `/uploads` makes all uploaded documents publicly accessible via URL brute-forcing.
- **Gaps & Risks:**
  - **Remote Code Execution / Storage Denial of Service:** An unauthenticated attacker can upload malicious HTML, SVG, or executable scripts directly to the server.

### E. University Matching, Project & Team Management (Phases 11, 12, 13, 15, 16)
- **Current State (`backend/app/routers/projects.py`, `backend/app/routers/universities.py`):**
  - University matching matches keywords in university expertise strings.
  - Project creation arbitrarily defaults to student ID 1 if no students are selected (`# Add default student for seamless demo`).
  - Milestone progress is manually updated as arbitrary floats rather than weighted calculations from verified deliverables.
- **Gaps & Risks:**
  - Progress percentages are decoupled from deliverable completion and faculty/verifier sign-offs.
  - Student and multidisciplinary team assignment lacks invitation/acceptance workflow.

### F. Industry Collaboration & CSR Marketplace (Phase 14)
- **Current State (`backend/app/routers/industry.py`, `backend/app/models/models.py`):**
  - Industry partners can submit collaboration offers (`Mentorship`, `Funding`, etc.).
  - No formal budget breakdown, CSR eligibility verification, escrow tracking, or government approval gate for corporate sponsorships.
- **Gaps & Risks:**
  - Financial/equipment pledges cannot be legally audited or tracked against project milestone deliverables.

### G. Evidence, Verification, Impact Measurement & Citizen Closure (Phases 17, 18, 19)
- **Current State (`backend/app/models/models.py:ImpactMetrics`):**
  - A single static table `impact_metrics` stores generic name/value pairs.
  - No field verification records, no before-and-after photo comparisons, no GPS validation stamps, and no citizen feedback loops after solution deployment.
- **Gaps & Risks:**
  - Projects can claim "RESOLVED" status without field audits, violating government accountability.

### H. Database Hardening, Migrations & Performance (Phases 27, 28)
- **Current State:**
  - No Alembic configuration or migration history. Database changes require dropping the database or manual SQLite modifications.
  - Critical query filters (`challenges.status`, `challenges.category`, `challenge_locations.district_name`, `created_at`) lack compound indexes for high-volume querying.
  - Pagination is missing in `list_challenges`, `list_projects`, and `notifications`, risking high latency and OOM when records scale to thousands.

---

## 3. Recommended Implementation Roadmap & Phasing (P0 → P1 → P2 → P3)

### Phase P0: Critical Security & Integrity Foundation
1. **Security & Auth Overhaul:**
   - Remove OTP backdoor (`123456`) and enforce secure cryptographic OTP generation with rate limiting.
   - Implement JWT Access + Refresh token rotation with token revocation blacklist.
   - Expand roles and introduce granular permissions (`challenge:create`, `challenge:validate`, `challenge:assign`, `project:approve`, etc.).
2. **File Storage & Upload Security:**
   - Authenticate all upload endpoints.
   - Implement strict MIME-type detection (magic bytes), file-size enforcement (max 10MB images/PDFs), and sanitized filenames.
   - Secure media access: private documents with authenticated proxy/signed URLs.
3. **Formal State Machine & Audit Logging:**
   - Implement deterministic `ChallengeStateMachine` and `ProjectStateMachine`.
   - Deny illegal status transitions.
   - Create tamper-evident `AuditLog` table capturing actor, action, old/new states, IP, timestamp, and justification.

### Phase P1: Core Government Workflows
1. **Organization Verification Pipeline:**
   - University and Industry organization profiles with document submission and `PENDING`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED` states.
2. **Citizen Privacy & Submission Upgrades:**
   - Coordinate obfuscation for public API consumers; exact coordinates preserved for authorized district officers.
   - Draft saving, multi-file evidence attachment, and category taxonomy.
3. **Moderation Pipeline & Administrative Workflow:**
   - Dedicated moderation endpoints for Panchayat, Block, District, and State officers with structured rejection/action reasons.
4. **Weighted Milestone & Deliverable Verification:**
   - Weighted milestone calculation (weights summing to 100%).
   - Verification workflow (`SUBMITTED -> EVIDENCE_REVIEW -> FIELD_VERIFIED -> APPROVED`).

### Phase P2: Modular AI Services, Impact & Observability
1. **Modular AI Engine:**
   - Refactor into `AIClassificationService`, `AIDeduplicationService`, `AIPriorityService`, `AIUniversityMatchingService`.
   - Store model metadata, confidence scores, and government override audit records.
2. **Real Impact Metrics & Citizen Feedback:**
   - Pre/post metric tracking (`baseline_value`, `target_value`, `actual_value`).
   - Post-deployment citizen resolution rating & feedback.
3. **Database Migrations & Performance:**
   - Initialize Alembic migrations for PostgreSQL/SQLite dual support.
   - Add compound indexes and standard paginated responses (`data`, `page`, `page_size`, `total_count`).
4. **Structured Observability & Error Handling:**
   - Correlation IDs (`X-Request-ID`), standardized API envelope (`{success, data, message, request_id}`), and sanitized production error handling.

### Phase P3: Documentation, Disaster Recovery & Governance
1. Update `ARCHITECTURE.md`, `DATABASE.md`, `API.md`, `DEPLOYMENT.md`.
2. Produce `docs/PRODUCTION_CHECKLIST.md`, `docs/DISASTER_RECOVERY.md`, and `docs/AI_GOVERNANCE.md`.
3. Automated test coverage for security, RBAC, state transitions, uploads, and AI service overrides.
