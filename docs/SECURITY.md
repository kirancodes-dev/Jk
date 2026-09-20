# 🛡️ Security Architecture & Compliance Specification
**Jharkhand Societal Innovation & Collaboration Platform**  
*Government of Jharkhand — Department of Higher & Technical Education*  
*SIH 2026 — Problem Statement 26043*

---

## 1. Threat Model & Security Posture
The platform is designed under a **Zero-Trust Architecture** for sensitive public-sector innovation, student intellectual property, and government fund allocation.

### Protected Assets:
1. **Citizen PII**: Phone numbers, residential addresses, and exact geotagged coordinates.
2. **Student & Faculty Intellectual Property**: Research proposals, source code, schematics, and milestone deliverables.
3. **Government Verification & Triage Records**: Departmental approvals, internal notes, inspector credentials, and fund sanction decisions.
4. **Corporate CSR Financial Commitments**: Grant offers, transaction IDs, and partnership agreements.

---

## 2. Authentication Architecture

### 2.1 Dual-Token Lifecycle (OAuth2 + JWT)
- **Access Tokens**: Short-lived (30 minutes), signed with HMAC-SHA256 (`HS256`), containing standard claims (`sub`, `role`, `jti`, `iat`, `exp`).
- **Refresh Tokens**: Long-lived (7 days), stored securely, with **Refresh Token Rotation (RTR)**. Every refresh generates a new refresh token and revokes the old one.
- **Revocation / Blacklist**:
  - In-memory fast cache (`backend/app/core/security.py`) and persistent table (`revoked_tokens`) store revoked JTIs.
  - Logging out immediately invalidates both access and refresh tokens.

### 2.2 Production vs Demo Separation
- **`DEMO_MODE=false` (Production)**:
  - Demo endpoints (`/api/v1/demo/reset`, `/api/v1/demo/accounts`) return `HTTP 403 Forbidden`.
  - All users must register with unique bcrypt passwords (minimum 8 characters, complex character rules).
  - Hardcoded credentials (`password123`) are strictly prohibited and non-existent.
- **`DEMO_MODE=true` (Evaluation Sandbox Only)**:
  - Enables pre-seeded evaluation personas for jury review.

### 2.3 Rate Limiting & Anti-Brute-Force
- Authentication routes (`/auth/login`, `/auth/verify-otp`) are throttled to 5 failed attempts per IP address per 15-minute window.

---

## 3. Object-Level Authorization (IDOR Mitigation)

Every resource endpoint enforces fine-grained authorization checks beyond role validation:

| Resource | Protected Action | Object-Level Verification Helper |
| :--- | :--- | :--- |
| **Project** | `GET /api/v1/projects/{id}` | `verify_project_membership`: Asserts caller is student member, faculty mentor, lead university, or government admin |
| **Task Deliverable** | `POST /api/v1/students/tasks/{id}/submit` | Asserts caller is the assigned student or member of project team |
| **Milestone** | `POST /api/v1/faculty/milestones/{id}/approve` | Asserts caller is assigned faculty mentor or institutional dean |
| **Challenge** | `POST /api/v1/impact/feedback` | `verify_challenge_ownership`: Asserts caller is original reporting citizen |
| **Verification** | `POST /api/v1/verification/records` | Asserts caller is authorized inspecting officer or government admin |

---

## 4. Secure File & Document Management

Public static mounting of private documents is strictly prohibited.

1. **Authentication & Authorization**: File access requires a valid JWT.
2. **MIME Type Whitelisting**:
   - Permitted: `image/jpeg`, `image/png`, `application/pdf`.
   - Executable extensions (`.exe`, `.sh`, `.php`, `.py`, `.js`) are rejected with `HTTP 400`.
3. **File Size Enforcement**: Maximum file size is capped at **10 MB**.
4. **Filename Sanitization**: Strip path traversal characters (`..`, `/`, `\`) and non-alphanumeric symbols; store files under UUIDv4 keys.
5. **Private Storage & Presigned URLs**: Files are stored in private cloud buckets (AWS S3 or MinIO) and served via short-lived (15-minute) presigned URLs.

---

## 5. Audit Logging & Compliance (DPDP & RTI Ready)

Every security-sensitive event writes an immutable entry into the `audit_logs` table:
- `actor_id`, `actor_name`, `actor_role`
- `action` (e.g., `CHALLENGE_STATUS_TRANSITION`, `MILESTONE_APPROVE`, `USER_LOGOUT`)
- `entity_name` and `entity_id`
- `old_state` and `new_state`
- `client_ip` and `request_id`
- `created_at` (UTC ISO-8601 timestamp)

Audit logs are append-only; database update and delete permissions on `audit_logs` are revoked for application workers.

---

## 6. HTTP Security Headers
All responses inject the following security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (in production HTTPS)
- `X-Request-ID: <uuidv4>` for cross-service request correlation
