# Backend Comprehensive Audit (SIH26043)

**Platform**: Jharkhand Societal Innovation Collaboration Portal  
**Framework**: FastAPI / Python / SQLAlchemy / PostgreSQL  
**Date**: September 2026  
**Auditor**: Senior Full-Stack & Government Digital Platform Architect  

---

## Executive Summary
The backend architecture is structured around FastAPI routers, SQLAlchemy ORM models (33 tables), Pydantic schemas, and modular AI engines. All 21 core unit, integration, and security tests pass. However, several production hardening areas require attention: object-level authorization (IDOR protection), background async processing for AI and notifications, standardized API pagination envelopes, and database query optimization.

---

## Detailed Router-by-Router Audit

### 1. Authentication & Identity (`backend/app/routers/auth.py`)

| Feature | Status | Findings & Risks |
| :--- | :--- | :--- |
| JWT Access Tokens | **COMPLETE** | 60-minute expiry with HS256 signature and `jti` tracking. |
| Refresh Token Rotation | **COMPLETE** | Rotates refresh tokens via `/auth/refresh` and revokes old tokens. |
| Logout & Revocation | **COMPLETE** | In-memory blacklist and database persistence in `revoked_tokens`. |
| OTP Verification | **COMPLETE** | Cryptographic 6-digit expiring code; demo backdoor eliminated. |
| Brute-Force Lockout | **COMPLETE** | 10-minute lockout after 5 failed password attempts. |
| User Profile (`/auth/me`) | **COMPLETE** | Returns active user role, permissions, and institution ID. |

---

### 2. Challenges & Moderation (`backend/app/routers/challenges.py`)

| Feature | Status | Findings & Risks |
| :--- | :--- | :--- |
| Challenge Creation | **COMPLETE** | Validates payload, stores centroid GPS, links media, triggers AI. |
| Status Transition | **COMPLETE** | Enforced through `state_machine.py` with `audit_logs` persistence. |
| Moderation Endpoints | **PARTIAL** | Missing explicit `/challenges/{id}/moderate` endpoint allowing reviewers to flag spam, request clarification, or confirm duplicates. |
| GPS Privacy Redaction | **PARTIAL** | Centroid returned for public, but needs explicit object-level policy to restrict exact coordinates to government officers and the reporting citizen. |
| Challenge History | **COMPLETE** | Returns immutable audit trail and historical status transitions. |
| Pagination & Filtering | **PARTIAL** | Filters by district, category, and status exist, but endpoint returns unbounded lists instead of standard paginated results (`page`, `page_size`, `total_pages`). |

---

### 3. AI Services & Explainability (`backend/app/services/ai/`)

| Engine | Status | Findings & Risks |
| :--- | :--- | :--- |
| Classification | **COMPLETE** | Modular `AIClassificationService` tagging domain with confidence. |
| Deduplication | **COMPLETE** | Multi-factor text similarity + Haversine geospatial proximity (<= 5km). |
| Priority Scoring | **COMPLETE** | Multi-criteria calculation (severity + urgency + population impact). |
| University Matching | **COMPLETE** | Scores academic departments, research labs, and geographic distance. |
| Async Processing | **PRODUCTION RISK** | AI processing currently runs synchronously inside the `POST /challenges` request loop. If payload is large or AI service encounters high load, request response times spike. Must be moved to `BackgroundTasks` or Celery. |
| Explainability Metadata | **COMPLETE** | Records `model_name`, `confidence`, and human override flags in `ai_analysis`. |

---

### 4. Universities & Projects (`backend/app/routers/universities.py` & `projects.py`)

| Feature | Status | Findings & Risks |
| :--- | :--- | :--- |
| Challenge Adoption | **COMPLETE** | Verified universities can adopt validated challenges. |
| Project Creation | **COMPLETE** | Generates project workspace, milestones, and team members. |
| Milestone Progress | **PARTIAL** | Weighted milestone calculation exists, but milestone progress can still be updated without attached deliverable evidence. |
| Object-Level Authorization | **PRODUCTION RISK** | Must verify that the updating student or faculty mentor actually belongs to the project (`ProjectMember.user_id == current_user.id`) to prevent Insecure Direct Object References (IDOR). |

---

### 5. Verification & Impact (`backend/app/routers/verification.py` & `impact.py`)

| Feature | Status | Findings & Risks |
| :--- | :--- | :--- |
| Field Inspection Submissions | **COMPLETE** | Accepts inspector details, geotags, notes, and evidence files. |
| Administrative Review | **COMPLETE** | Allows Government Admins to approve/verify records and sign off milestones. |
| Citizen Feedback | **COMPLETE** | Collects post-resolution rating, confirmation, and satisfaction score. |
| Dynamic Impact Metrics | **COMPLETE** | Computes real-time metrics dynamically from SQL aggregations with zero hardcoded numbers. |

---

### 6. Observability, Security & Infrastructure (`backend/app/main.py`)

| Feature | Status | Findings & Risks |
| :--- | :--- | :--- |
| Correlation ID | **COMPLETE** | `X-Request-ID` attached to all incoming and outgoing requests. |
| Security Headers | **COMPLETE** | `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY` active. |
| Kubernetes Health Probes | **COMPLETE** | `/live`, `/ready`, and `/health` probes operational. |
| Structured Logging | **PARTIAL** | Basic console logging via uvicorn. Needs JSON structured logger for ELK/CloudWatch integration. |
| Database Migrations | **COMPLETE** | Alembic initialized with `alembic/env.py` and stamped initial migration. |
