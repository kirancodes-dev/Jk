# Disaster Recovery Runbook (SIH26043)

Government of Jharkhand — Department of Higher & Technical Education

---

## 1. Objectives & Metrics
- **Recovery Point Objective (RPO)**: <= 1 Hour (Maximum acceptable data loss window).
- **Recovery Time Objective (RTO)**: <= 30 Minutes (Maximum acceptable service downtime window).

---

## 2. Backup Architecture

### 2.1 Database (PostgreSQL)
- **Continuous Archiving (WAL)**: Write-Ahead Logs streamed to encrypted object storage (`s3://jharkhand-portal-backups/wal/`).
- **Nightly Logical Dump**: Automated dump executed at 02:00 IST:
  ```bash
  pg_dump -Fc -v -h $DB_HOST -U $DB_USER -d $DB_NAME -f "/backups/db_$(date +%Y%m%d_%H%M%S).dump"
  ```
- **Retention Schedule**:
  - Hourly differential backups: 7 days
  - Daily full dumps: 30 days
  - Monthly snapshots: 12 months

### 2.2 Object Storage (Evidence & Deliverables)
- Cross-region replication enabled on the primary S3/MinIO bucket.
- Versioning enabled on all challenge media and verification evidence attachments.

---

## 3. Incident Restoration Procedure

### Scenario A: Primary Database Failure
1. **Promote Read Replica**:
   ```bash
   pg_ctl promote -D /var/lib/postgresql/data
   ```
2. **Update Application Connection String**:
   Update `DATABASE_URL` in container environment or secrets manager to point to the promoted standby.
3. **Restart API Service**:
   ```bash
   docker compose restart backend
   ```
4. **Run Readiness Probe**:
   ```bash
   curl -i http://localhost:8008/ready
   ```

### Scenario B: Complete Regional Failure (Cold Standby Recovery)
1. Provision target VM or managed database instance in alternate datacenter/zone.
2. Restore latest logical dump:
   ```bash
   pg_restore -v -h $NEW_DB_HOST -U $DB_USER -d $DB_NAME latest_production_backup.dump
   ```
3. Run schema migration check:
   ```bash
   PYTHONPATH=. alembic upgrade head
   ```
4. Update DNS records (CNAME) to alternate load balancer.
5. Verify health:
   ```bash
   curl https://portal.jharkhand.gov.in/health
   ```
