# Secrets Rotation Runbook

**System**: SIH 26043 — Government of Jharkhand Societal Innovation Collaboration Portal  
**Department**: Higher & Technical Education, Government of Jharkhand  

---

## 1. Secrets Inventory & Frequency

| Secret Name | Usage | Rotation Frequency | Zero-Downtime Support |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | JWT access & refresh tokens | 90 days | Dual-key verification or grace period |
| `DATABASE_URL` (password) | PostgreSQL connection pool | 60 days | Dual user roles (`app_user_v1`, `app_user_v2`) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 evidence storage & SSE-S3 | 90 days | Dual IAM access keys on service account |
| `SMTP_PASSWORD` | State Gov email notification relay | 90 days | Immediate config update |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | Pluggable AI service credentials | 180 days | Instant swap via environment reload |
| `BACKUP_PASSPHRASE` | OpenSSL AES-256 cold backup encryption | 180 days | Update script env; old dumps keep old key |

---

## 2. JWT `SECRET_KEY` Rotation Procedure

1. **Generate Cryptographically Secure Key**:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
2. **Deploy Dual-Key Support / Grace Period**:
   - Update `SECRET_KEY` in environment variables.
   - Users with existing unexpired access tokens will seamlessly refresh via `/api/v1/auth/refresh` using their long-lived refresh tokens or re-authenticate via OTP/password.
3. **Restart API Service Fleet**:
   Perform rolling restart of backend containers.
4. **Invalidate Stale Sessions**:
   If rotation is due to a suspected key leak:
   ```sql
   INSERT INTO revoked_tokens (jti, revoked_at, reason)
   SELECT 'ALL_PRIOR', NOW(), 'EMERGENCY_SECRET_KEY_ROTATION';
   ```

---

## 3. Database Password Rotation Procedure

1. **Create Alternate DB Role in PostgreSQL**:
   ```sql
   CREATE USER jharkhand_app_v2 WITH PASSWORD '<NEW_SECURE_PASSWORD>';
   GRANT jharkhand_app_role TO jharkhand_app_v2;
   ```
2. **Update Application Secret**:
   Update `DATABASE_URL` in cloud secrets manager to use `jharkhand_app_v2`.
3. **Deploy Rolling Restart**:
   Restart backend pods. Active connections drain gracefully.
4. **Revoke Old Role**:
   After 24 hours of zero connections to `jharkhand_app_v1`:
   ```sql
   DROP USER jharkhand_app_v1;
   ```
