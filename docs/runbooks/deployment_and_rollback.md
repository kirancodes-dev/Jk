# Deployment & Zero-Downtime Rollback Runbook

**System**: SIH 26043 — Government of Jharkhand Societal Innovation Collaboration Portal  
**Department**: Higher & Technical Education, Government of Jharkhand  

---

## 1. Deployment Architecture

The portal is packaged and deployed using containerized microservices:
1. **API Service (`backend`)**: FastAPI running on Python 3.11/3.14 via Uvicorn workers behind NGINX reverse proxy.
2. **Worker Daemon (`worker`)**: Standalone `backend.app.worker` background process polling AI jobs and notification outbox.
3. **Database Migration**: Forward-only, backward-compatible Alembic migrations (`alembic upgrade head`).
4. **Web Frontend (`frontend`)**: Flutter Web CanvasKit SPA hosted statically.

---

## 2. Standard Production Deployment Procedure

1. **Pre-flight Health & Secret Verification**:
   - Ensure environment variables (`SECRET_KEY`, `DATABASE_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`) are set in Secrets Manager.
   - Verify non-root container configuration.
2. **Execute Database Migration**:
   ```bash
   # Run migration container prior to starting new application pods
   alembic upgrade head
   ```
3. **Deploy Backend Containers (Rolling Update)**:
   - Deploy new container revision with health probes configured:
     - Liveness: `GET /live` (timeout 5s, interval 10s)
     - Readiness: `GET /ready` (timeout 5s, interval 10s)
   - Ensure old pods are terminated only after new pods report `ready`.
4. **Deploy Background Worker Replicas**:
   - Rolling restart of worker pods. Worker concurrency locking (`FOR UPDATE SKIP LOCKED`) ensures zero collision during rolling restart.
5. **Post-Deployment Verification**:
   ```bash
   curl -f http://localhost:8008/health
   curl -f http://localhost:8008/live
   curl -f http://localhost:8008/ready
   curl -f http://localhost:8008/metrics
   ```

---

## 3. Rollback Procedure

If error rates spike (`5xx > 1%`) or health checks fail post-deployment:

1. **Immediate Traffic Rollback**:
   Revert reverse-proxy / Kubernetes deployment to previous immutable image tag:
   ```bash
   # Kubernetes / Docker Swarm rollback
   kubectl rollout undo deployment/jharkhand-portal-backend
   ```
2. **Database Rollback Policy**:
   - *Rule*: Never roll back database migrations if downstream schema changes contain newly committed production records.
   - If a rollback migration is strictly necessary and no destructive changes occurred:
     ```bash
     alembic downgrade -1
     ```
3. **Cache Invalidation**:
   Purge edge CDN cache for `/canvaskit/*`, `index.html`, and `main.dart.js`.
4. **Notify Engineering & Security Leads**:
   Broadcast notification to team and post incident log.
