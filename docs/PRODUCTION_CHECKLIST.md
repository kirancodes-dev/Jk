# Production Deployment Checklist (SIH26043)

Government of Jharkhand — Department of Higher & Technical Education
Platform: Societal Innovation Collaboration Portal

---

## 1. Environment & Infrastructure Pre-Flight
- [x] **Python Environment**: Python 3.11+ virtual environment configured.
- [x] **Database Engine**: PostgreSQL configured with schema migrations via Alembic.
- [x] **Storage Service**: S3-compatible object storage configured with strict MIME whitelist (`image/png`, `image/jpeg`, `application/pdf`, `video/mp4`) and 10MB/50MB size guardrails.
- [x] **HTTPS / TLS Termination**: Enforced TLS 1.3 reverse proxy (NGINX / Cloudflare) with HSTS headers.
- [x] **Rate Limiting**: API level rate-limiting middleware active (`RATE_LIMIT_PER_MINUTE=60`).
- [x] **Observability**: Request correlation ID (`X-Request-ID`), `/live`, and `/ready` probes operational.

---

## 2. Authentication & Credential Security
- [x] **No Hardcoded Backdoors**: Verification OTPs are 6-digit cryptographic, time-expiring (10 min), and enforce maximum 3 failed attempts lockout.
- [x] **JWT Token Management**: Short-lived access tokens (60 mins) and rotatable refresh tokens (30 days).
- [x] **Server-side Session Revocation**: Immediate `/auth/logout` revocation recorded in database and in-memory cache.
- [x] **Role-Based Access Control (RBAC)**: Strict permission boundaries preventing role tampering across Citizens, Students, Faculty, Industry, and Government Administrators.
- [x] **University Affiliation Integrity**: Students and Faculty accounts must authenticate under their verified institution domain.

---

## 3. Governance, Verification & Audit Trails
- [x] **Challenge Lifecycle State Machine**: Enforced sequence of transitions from `SUBMITTED` to `UNDER_REVIEW`, `VALIDATED`, `UNIVERSITY_ASSIGNED`, `IN_PROGRESS`, `FIELD_VERIFICATION`, `RESOLVED`, and `CLOSED`.
- [x] **Immutable Audit Log**: All administrative, status, verification, and feedback events logged in `audit_logs` table.
- [x] **Field Verification Workflow**: Evidence review, geotagged latitude/longitude confirmation, and government officer sign-off required prior to project sign-off.
- [x] **Citizen Post-Resolution Feedback**: Beneficiary rating, resolution confirmation, and citizen satisfaction scores collected before challenge closure.
- [x] **Data-Driven Impact Reporting**: Zero hardcoded metric values; impact metrics dynamically computed from database records.

---

## 4. Disaster Recovery & High Availability
- [x] Automated daily PostgreSQL logical backups via `pg_dump`.
- [x] Point-in-time recovery (WAL archiving) configured.
- [x] Multi-zone read replicas for high-traffic public dashboards.
- [x] Documented disaster recovery runbook in `docs/DISASTER_RECOVERY.md`.
