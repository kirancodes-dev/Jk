# Security Architecture & Threat Model (SIH26043)

Government of Jharkhand — Department of Higher & Technical Education

---

## 1. Authentication & Token Lifecycle
- **Tokens**: JWT signed using HS256 (or RS256 in clustered deployments) with distinct access and refresh lifecycles.
  - Access Token Expiration: 60 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`).
  - Refresh Token Expiration: 30 days (`REFRESH_TOKEN_EXPIRE_DAYS`).
- **Session Revocation**: When a user logs out, their JWT unique identifier (`jti`) is persisted in `revoked_tokens` table and cached in memory. Any subsequent request using a revoked token is rejected with HTTP 401.
- **Brute-Force Defense**: Password authentication locks an email for 10 minutes following 5 consecutive failed attempts.
- **OTP Verification**: Real 6-digit cryptographic OTPs with a 10-minute expiry and a 3-attempt limit. Demo backdoor codes (`123456`) are disabled.

---

## 2. Authorization & RBAC
- Explicit role hierarchies:
  - `GOVERNMENT_ADMIN`: Superuser operations, department assignment, challenge moderation, official field verification review, state-wide audit logs.
  - `UNIVERSITY`: Academic problem adoption, student and faculty team allocation, milestone progress tracking.
  - `FACULTY_MENTOR`: Research supervision, technical guidance, task reviews.
  - `STUDENT`: Task execution, milestone progress submission, deliverable file uploads.
  - `INDUSTRY`: CSR funding proposals, co-mentorship, internship offerings.
  - `CITIZEN`: Challenge submission, progress tracking, post-resolution feedback rating.

---

## 3. Data Protection & Privacy
- **GPS Privacy Centroid**: Exact GPS coordinates of citizen homes or sensitive infrastructure are redacted for unauthenticated users, providing village/block level centroids instead.
- **Secure File Storage**:
  - Whitelist of permitted MIME types: `image/jpeg`, `image/png`, `application/pdf`, `video/mp4`.
  - Content length validation: 10MB maximum for documents and images; 50MB for video evidence.
  - File extension and name sanitization to prevent path traversal attacks.
- **Audit Trails**: Every state change, inspection sign-off, and administrative moderation event records the actor's ID, role, client IP, before/after states, and timestamp in `audit_logs`.
