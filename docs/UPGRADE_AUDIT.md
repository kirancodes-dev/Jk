# Full System Upgrade Audit (SIH26043)

**Platform**: Jharkhand Societal Innovation Collaboration Portal  
**Problem Statement**: SIH26043 — Department of Higher & Technical Education, Government of Jharkhand  
**Date**: September 2026  

---

## 1. Capability Classification Matrix

Every system capability has been audited and classified into one of six standard maturity tiers:
- **COMPLETE**: Production-ready, fully tested, secure, and integrated.
- **PARTIAL**: Implemented but missing edge-case handling, deeper validation, or connected UI.
- **DEMO ONLY**: Mocked or implemented only for visual demonstration.
- **BROKEN**: Fails during runtime execution or contains blocking bugs.
- **MISSING**: Required by the problem statement/architecture but not yet implemented.
- **PRODUCTION RISK**: Security, performance, or integrity hazard under real-world load.

---

| System Domain | Specific Capability | Classification | Current State & Upgrade Path |
| :--- | :--- | :--- | :--- |
| **Authentication** | JWT Access & Refresh Token Rotation | **COMPLETE** | Implemented with `/auth/refresh` and `/auth/logout`. |
| **Authentication** | Server-Side Session Revocation | **COMPLETE** | In-memory blacklist and database persistence in `revoked_tokens`. |
| **Authentication** | Multi-Role Affiliation Security | **COMPLETE** | Enforces institution checks preventing students from logging into other universities. |
| **Authentication** | Password Reset & Cryptographic OTP | **COMPLETE** | 6-digit expiring OTP with attempt limit; backdoor removed. |
| **Authentication** | One-Click Demo Role Switcher | **DEMO ONLY** | Fast switcher exists on login screen. Must be gated behind `DEMO_MODE=false`. |
| **Access Control** | Role-Based Access Control (RBAC) | **COMPLETE** | Strict role permissions mapped in `deps.py`. |
| **Access Control** | Object-Level Authorization (IDOR) | **PRODUCTION RISK** | Endpoints need project membership verification before updating tasks or milestones. |
| **Challenge Engine** | Challenge Submission & Centroid | **COMPLETE** | Validates payload, uploads evidence, records centroid location. |
| **Challenge Engine** | Lifecycle State Machine Enforcement | **COMPLETE** | Enforced through `state_machine.py` with `audit_logs` tracking. |
| **Challenge Engine** | Moderation & Clarification Workflow | **PARTIAL** | Government can validate/escalate, but needs dedicated Reject/Clarify/Duplicate UI. |
| **Challenge Engine** | Duplicate Review Interface | **MISSING** | Needs side-by-side comparison UI for government reviewers. |
| **Challenge Engine** | Community Engagement & Comments | **COMPLETE** | Authenticated comments and upvoting support active. |
| **AI Processing** | Modular Multi-Engine Architecture | **COMPLETE** | Classification, deduplication, priority, and university matching modularized. |
| **AI Processing** | Geospatial Proximity Deduplication | **COMPLETE** | Haversine distance threshold (<= 5km) + text similarity. |
| **AI Processing** | Asynchronous Background AI Execution | **PRODUCTION RISK** | Currently runs synchronously during challenge submission. Must use `BackgroundTasks`. |
| **AI Processing** | Explainability & Decision Auditability | **PARTIAL** | Metadata stored in DB, but needs human-readable rationale in Flutter UI. |
| **University & Project** | Challenge Adoption & Project Creation | **COMPLETE** | University adopts challenge and initializes project workspace. |
| **University & Project** | Weighted Milestone Progress | **COMPLETE** | Project progress calculated from approved milestone weights (`sum = 100%`). |
| **University & Project** | Deliverable File Upload & Review | **PARTIAL** | Schema supports deliverables, but needs dedicated file viewer in project tabs. |
| **University & Project** | Multi-Disciplinary Team Builder | **PARTIAL** | Team allocation works, but lacks cross-department faculty invitation UI. |
| **Industry Marketplace** | CSR Sponsorship & Mentorship Offers | **COMPLETE** | Industry partners can discover projects and submit collaboration offers. |
| **Industry Marketplace** | Formal Funding Agreement Tracking | **PARTIAL** | Backend records offers, but needs agreement milestone disbursement tracking. |
| **Verification & Impact** | Field Inspection Evidence Submission | **COMPLETE** | Submissions with geotags and multi-format evidence files. |
| **Verification & Impact** | Official Government Sign-Off | **COMPLETE** | Government reviews evidence and verifies milestone/challenge resolution. |
| **Verification & Impact** | Citizen Post-Resolution Feedback | **COMPLETE** | Beneficiary rating and resolution confirmation in `citizen_feedback`. |
| **Verification & Impact** | Real-Time Dynamic Impact Metrics | **COMPLETE** | Dynamically calculated from database without hardcoded statistics. |
| **Storage & Media** | Secure File Upload & MIME Validation | **COMPLETE** | Validates MIME types, sanitizes filenames, and limits file sizes. |
| **Storage & Media** | Resilient Upload Progress & Previews | **PARTIAL** | Media upload exists, but lacks progress percentage indicators and document previewers. |
| **Offline Sync** | Offline Challenge Drafts | **PARTIAL** | Local draft storage exists, but lacks connectivity banner (ONLINE / OFFLINE / SYNCING). |
| **Observability** | Request Correlation & Health Probes | **COMPLETE** | `X-Request-ID`, `/live`, `/ready`, and `/health` active and verified. |
| **Observability** | Structured Logging | **PARTIAL** | Standard console output; needs JSON structured formatter. |
| **Database** | PostgreSQL Migrations | **COMPLETE** | Alembic initialized, configured, and stamped to `head`. |
| **UI Design System** | Material 3 Government Tokens | **PARTIAL** | Themes defined, but needs unified reusable widgets (`AppButton`, `AppTextField`, `AppCard`). |
| **Accessibility** | Semantic Labels & Screen Readers | **PARTIAL** | Visual layouts clean, but needs accessible ARIA/semantics and color-contrast verification. |
| **Localization** | Multilingual Architecture (EN/HI) | **MISSING** | UI strings are hardcoded in widget classes; needs localization bundle. |

---

## 2. Recommended Implementation Roadmap

### Phase 1: Frontend Architecture & Design System (P0)
- Build unified design tokens and reusable widgets: `AppButton`, `AppTextField`, `AppCard`, `LoadingView`, `ErrorView`, `EmptyView`, `ConfirmDialog`, `MediaPreview`, `RoleGuard`.
- Replace demo shortcuts with robust authenticated role navigation.

### Phase 2: Core Workflows & UI Integration (P0)
- **Citizen Experience**: Multi-step submission wizard with progress indicator; side-by-side duplicate view; post-resolution feedback rating modal.
- **Government Workflow**: Comprehensive moderation workspace (Validate, Reject with Reason, Request More Info, Mark Duplicate, Assign Institution, Field Verification Review).
- **University & Project Workspace**: Unified 6-tab workspace (Overview, Milestones, Deliverables & Evidence, Team, Funding, and Verification Audit).
- **Notification Center**: Categorized tabs with deep-linking navigation.

### Phase 3: Backend Hardening & Background Execution (P0)
- Enforce object-level authorization (IDOR checks) across project deliverables and student task submissions.
- Offload AI text processing, duplicate detection, and notification dispatches to FastAPI `BackgroundTasks`.
- Add standard pagination query parameters (`page`, `page_size`, `total_pages`) to challenge and project lists.

### Phase 4: Offline Connectivity UX & Localization (P1)
- Connectivity status banner (`ONLINE`, `OFFLINE`, `SYNCING`) with reliable auto-retry.
- Centralized string localization structure for English and Hindi.
