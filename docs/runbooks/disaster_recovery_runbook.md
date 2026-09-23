# Disaster Recovery & Business Continuity Runbook

**System**: SIH 26043 — Government of Jharkhand Societal Innovation Collaboration Portal  
**Department**: Higher & Technical Education, Government of Jharkhand  
**Classification**: Official / Sensitive  
**Target RPO (Recovery Point Objective)**: < 15 minutes  
**Target RTO (Recovery Time Objective)**: < 30 minutes  

---

## 1. Overview & Architecture

The portal disaster recovery strategy guarantees state business continuity through:
1. **Primary Database**: PostgreSQL (Supabase / Managed Cloud / On-Premise NIC datacenter) with automated WAL archiving and daily encrypted backups.
2. **Encrypted Cold Storage**: Automated AES-256 encrypted dumps stored in offsite multi-region object storage (`backups/postgres/`).
3. **Evidence Storage**: S3/MinIO compatible object store configured with SSE-S3 encryption (`AES256`), versioning, and cross-region bucket replication.
4. **Statutory Audit Integrity**: Complete tamper-evident audit logs (`audit_logs`) and hash chains preserved through all restore actions.

---

## 2. Emergency Escalation Hierarchy

| Role | Contact | Responsibility |
| :--- | :--- | :--- |
| **Incident Commander** | `dpo-innovation@jharkhand.gov.in` | Overall incident declaration, authority communication |
| **Database Lead** | `dba-alerts@jharkhand.gov.in` | Point-in-time recovery, WAL replay, schema integrity |
| **DevOps / Cloud Lead** | `infra-support@jharkhand.gov.in` | DNS switchover, S3 replication, container fleet redeployment |
| **Security Officer** | `secops@jharkhand.gov.in` | Checksum verification, decryption key custody, breach analysis |

---

## 3. Disaster Scenarios & Recovery Procedures

### Scenario A: Accidental Data Corruption or Malicious Deletion (PITR)

When data corruption is identified within the WAL retention window:
1. **Freeze Ingress**:
   ```bash
   # Enable maintenance mode via reverse proxy (NGINX/Cloudflare)
   # Sets 503 Service Temporarily Unavailable with maintenance page
   ```
2. **Identify Target Timestamp**:
   Determine the exact UTC timestamp `T_target` prior to the incident using `audit_logs` or application telemetry.
3. **Execute Point-in-Time Recovery**:
   In managed PostgreSQL / Supabase:
   - Navigate to **Backups** -> **Point in Time Recovery**.
   - Select timestamp `T_target`.
   - Provision recovery clone instance.
4. **Verify Schema & Record Counts**:
   Run schema health probe:
   ```bash
   python3 -c "from backend.app.core.database import check_database_connection; print(check_database_connection())"
   ```
5. **Switch Traffic**: Update `DATABASE_URL` in container environment and restart backend pods.

---

### Scenario B: Complete Datacenter / Host Outage (Cold Restore)

When the primary database instance is completely lost:
1. **Retrieve Latest Encrypted Backup & Manifest**:
   ```bash
   aws s3 cp s3://jharkhand-sih-backups/postgres/latest.sql.gz.enc ./backups/
   aws s3 cp s3://jharkhand-sih-backups/postgres/latest.manifest.json ./backups/
   ```
2. **Run Restore Verification Drill**:
   ```bash
   export BACKUP_PASSPHRASE="<STATE_OFFICIAL_ENCRYPTION_PASSPHRASE>"
   ./scripts/backup/verify_restore.sh ./backups/latest.sql.gz.enc ./backups/latest.manifest.json
   ```
3. **Provision Target PostgreSQL Instance**:
   Ensure PostgreSQL 15+ is running with database `sih_jharkhand`.
4. **Restore SQL Data**:
   ```bash
   openssl enc -d -aes-256-cbc -pbkdf2 \
       -in ./backups/latest.sql.gz.enc \
       -k "${BACKUP_PASSPHRASE}" | gzip -d | psql "${NEW_DATABASE_URL}"
   ```
5. **Verify Alembic Migration State**:
   ```bash
   alembic current
   # Expected head: 7a8e91d0f2a4 (or current release head)
   ```

---

### Scenario C: Object Storage / Evidence File Loss

1. **Verify Bucket Versioning**:
   ```bash
   aws s3api list-object-versions --bucket jharkhand-sih-challenges --prefix active/
   ```
2. **Restore Deleted Objects**:
   If objects were deleted via soft delete, restore retention state:
   ```bash
   # Call POST /api/v1/files/attachments/{object_id}/restore
   ```
3. **Cross-Region Secondary Sync**:
   Sync secondary replica bucket into active bucket:
   ```bash
   aws s3 sync s3://jharkhand-sih-challenges-replica s3://jharkhand-sih-challenges
   ```

---

## 4. Post-Recovery Validation Checklist

- [ ] Liveness probe returns `{"status":"alive"}` at `/live`.
- [ ] Readiness probe returns `{"status":"ready","database":"connected"}` at `/ready`.
- [ ] Aggregated health probe returns healthy at `/health`.
- [ ] Prometheus metrics endpoint active at `/metrics`.
- [ ] Background worker claims jobs without duplicate executions (`python -m backend.app.worker --run-once`).
- [ ] Incident report recorded in `docs/incidents/` within 24 hours.
