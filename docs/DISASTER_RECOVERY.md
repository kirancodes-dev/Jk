# 🚨 Disaster Recovery & High Availability Runbook
**Jharkhand Societal Innovation & Collaboration Platform**  
*Government of Jharkhand — Department of Higher & Technical Education*  
*SIH 2026 — Problem Statement 26043*

---

## 1. Objectives & Metrics
- **Recovery Point Objective (RPO)**: $\le 15 \text{ minutes}$ (maximum allowable data loss).
- **Recovery Time Objective (RTO)**: $\le 60 \text{ minutes}$ (maximum allowable downtime).

---

## 2. Backup Strategy

### 2.1 Database (PostgreSQL 16)
- **Automated Daily Logical Backups**:
  ```bash
  # Daily compressed pg_dump snapshot
  pg_dump -h $DB_HOST -U $DB_USER -d sih_portal -F c -b -v -f /backups/sih_portal_$(date +%Y%m%d_%H%M%S).dump
  ```
- **Continuous Archiving (WAL-G / pgBackRest)**:
  - Write-Ahead Logs (WAL) are streamed continuously to secondary cloud object storage for Point-In-Time Recovery (PITR).
- **Retention Schedule**:
  - Daily backups kept for 30 days.
  - Weekly backups kept for 12 weeks.
  - Monthly compliance archives kept for 7 years (under state digital archiving norms).

### 2.2 Evidence & File Attachments (S3 / MinIO)
- Bucket versioning enabled on all evidence buckets.
- Cross-region replication (CRR) between state primary data center (Ranchi SDC) and disaster recovery cloud (NIC Cloud / AWS Mumbai).

---

## 3. Database Restoration Procedure

### Restoring from a Logical Snapshot:
```bash
# 1. Stop web application services
docker-compose stop web

# 2. Drop existing database connections and recreate database
psql -h $DB_HOST -U $DB_USER -c "DROP DATABASE IF EXISTS sih_portal_recovery;"
psql -h $DB_HOST -U $DB_USER -c "CREATE DATABASE sih_portal_recovery OWNER sih_user;"

# 3. Restore from compressed dump
pg_restore -h $DB_HOST -U $DB_USER -d sih_portal_recovery -v /backups/sih_portal_latest.dump

# 4. Apply latest Alembic migrations to ensure schema alignment
DATABASE_URL=postgresql://sih_user:password@$DB_HOST:5432/sih_portal_recovery alembic upgrade head

# 5. Swap database and restart services
psql -h $DB_HOST -U $DB_USER -c "ALTER DATABASE sih_portal RENAME TO sih_portal_old;"
psql -h $DB_HOST -U $DB_USER -c "ALTER DATABASE sih_portal_recovery RENAME TO sih_portal;"
docker-compose start web
```

---

## 4. Disaster Failover Checklist
1. **Primary DC Failure Detection**: Automated health check alerts via Prometheus / Alertmanager triggering after 3 failed consecutive probe checks.
2. **DNS Failover**: Update Anycast DNS or Cloudflare load balancer routing from Primary SDC to DR replica.
3. **Promote Read Replica**: Execute `pg_ctl promote` on the standby database node.
4. **Service Health Assertion**: Verify `/health`, `/live`, and `/ready` probes return HTTP 200 before opening public traffic.
