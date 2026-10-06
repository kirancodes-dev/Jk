# Production Deployment Guide — SIH 2026 Portal
**Government of Jharkhand — Department of Higher & Technical Education**
**Societal Innovation Collaboration Platform (Problem Statement 26043)**

---

## 1. Cloud Architecture Overview

The production system is deployed on AWS (Mumbai Region `ap-south-1`) with high availability, secure VPC isolation, and compliance with Indian digital data governance norms.

```
                  [ Internet Users / Citizens / Mobile App ]
                                      │
                                      ▼
                   [ AWS Route 53 DNS + AWS CloudFront CDN ]
                                      │
                                      ▼
                        [ Application Load Balancer ]
                               (Port 443 SSL)
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
   [ ECS Fargate / EC2 Instance 1 ]          [ ECS Fargate / EC2 Instance 2 ]
   FastAPI (Python 3.14) + Gunicorn          FastAPI (Python 3.14) + Gunicorn
   (Port 8008)                               (Port 8008)
                 │                                         │
                 ├────────────────────┬────────────────────┤
                 ▼                    ▼                    ▼
     [ AWS RDS PostgreSQL ]    [ AWS S3 Bucket ]     [ Amazon CloudWatch ]
      Multi-AZ (Port 5432)     (Encrypted AES-256)   (Logs & Alarms)
```

---

## 2. Infrastructure Prerequisites

| Component | Recommended Specification |
|:---|:---|
| **VPC** | 2 Public Subnets, 2 Private Subnets, NAT Gateway, Internet Gateway |
| **Compute** | AWS ECS Fargate or 2x `t3.medium` EC2 instances (Ubuntu 24.04 LTS) |
| **Database** | AWS RDS PostgreSQL 16 (Multi-AZ, `db.t3.medium`, 50GB gp3 storage) |
| **Storage** | AWS S3 Bucket (`sih-jharkhand-portal-media-prod`) with private ACL & CORS |
| **Security** | AWS WAF, Security Groups, IAM Roles with least-privilege policies |
| **DNS / SSL** | AWS Route 53 + AWS Certificate Manager (ACM) SSL Certificate |

---

## 3. Database Setup (AWS RDS PostgreSQL)

### 3.1 Create RDS Instance
```bash
# Generate secure password via AWS CLI or KMS
DB_PASSWORD=$(openssl rand -base64 24)

aws rds create-db-instance \
    --db-instance-identifier sih-jharkhand-pg-prod \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 16.2 \
    --master-username sih_admin \
    --master-user-password "${DB_PASSWORD}" \
    --allocated-storage 50 \
    --storage-type gp3 \
    --vpc-security-group-ids sg-xxxxxx \
    --db-subnet-group-name sih-private-db-subnets \
    --backup-retention-period 14 \
    --multi-az \
    --storage-encrypted \
    --no-publicly-accessible
```

### 3.2 Initialize Database Schema via Alembic
Database schema migrations must be applied using Alembic. Never use raw DDL scripts or `create_all` in production:
```bash
# Run migration runner from bastion, CI/CD pipeline, or ECS task:
export DATABASE_URL="postgresql://sih_admin:${DB_PASSWORD}@sih-jharkhand-pg-prod.xxxxxx.ap-south-1.rds.amazonaws.com:5432/sih_jharkhand"
alembic upgrade head
```

---

## 4. AWS S3 Media Storage Configuration

### 4.1 Create S3 Bucket
```bash
aws s3api create-bucket \
    --bucket sih-jharkhand-portal-media-prod \
    --region ap-south-1 \
    --create-bucket-configuration LocationConstraint=ap-south-1

# Enable Server-Side Encryption
aws s3api put-bucket-encryption \
    --bucket sih-jharkhand-portal-media-prod \
    --server-side-encryption-configuration '{
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
    }'

# Block Public Access (Files served via Pre-signed URLs or CloudFront)
aws s3api put-public-access-block \
    --bucket sih-jharkhand-portal-media-prod \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 4.2 S3 CORS Configuration
```json
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
      "AllowedOrigins": ["https://sih.jharkhand.gov.in"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}
```
Apply CORS:
```bash
aws s3api put-bucket-cors --bucket sih-jharkhand-portal-media-prod --cors-configuration file://cors.json
```

---

## 5. Dockerized Backend Deployment

### 5.1 Dockerfile (`Dockerfile`)
A two-stage build: stage 1 builds the Flutter web app with the pinned `ghcr.io/cirruslabs/flutter:3.41.9` image; stage 2 is the Python 3.12 API runtime, which serves that web app at `/` and the API at `/api/v1`. The container runs as an unprivileged user (`appuser`, UID 10001).

`docker-entrypoint.sh` starts the container:

| Variable | Default | Effect |
|---|---|---|
| `RUN_MIGRATIONS_ON_START` | `false` | `true` runs `alembic upgrade head` before the server starts. Use it for single-instance deployments; with several replicas, run migrations as a separate release step. |
| `DEMO_MODE` | `false` | With `ENVIRONMENT` other than `production`, seeds the demo data and every demo account once, before the workers start. |
| `WEB_CONCURRENCY` | `4` | Uvicorn worker processes. |
| `PORT` | `8008` | Listen port (Render sets its own). |
| `EVALUATOR_MODE` (build arg) | `false` | `true` adds the one-tap demo persona picker to the login screen. |

Build and push to AWS ECR:
```bash
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com
docker build -t sih-backend:latest .
docker tag sih-backend:latest <AWS_ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/sih-backend:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/sih-backend:latest
```

### 5.2 Container Orchestration & Health Probes

The application provides distinct probes:
- **Liveness Probe**: `GET /live` (HTTP 200 without requiring database connectivity).
- **Readiness Probe**: `GET /ready` (Verifies database connectivity and storage readiness, returning 503 if unavailable without leaking internal errors).
- **Aggregated Health Probe**: `GET /health` (Status summary).

Configure ALB target group:
- **Health Check Path**: `/ready` or `/live`
- **Port**: `8008`
- **Healthy Threshold**: `2`
- **Interval**: `30` seconds
- **Timeout**: `5` seconds


---

## 6. Nginx Reverse Proxy with SSL (EC2 Option)

If hosting on an AWS EC2 instance behind an Elastic IP:

```nginx
server {
    listen 80;
    server_name sih.jharkhand.gov.in api.sih.jharkhand.gov.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.sih.jharkhand.gov.in;

    ssl_certificate /etc/letsencrypt/live/api.sih.jharkhand.gov.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.sih.jharkhand.gov.in/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8008;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Issue SSL with Certbot:
```bash
sudo certbot --nginx -d api.sih.jharkhand.gov.in
```

---

## 7. Frontend Deployment (Web & Mobile APK)

### 7.1 Flutter Web Build & S3 / CloudFront Hosting
```bash
cd frontend
flutter clean
flutter pub get
flutter build web --release --dart-define=API_URL=https://api.sih.jharkhand.gov.in

# Deploy to S3 Static Hosting Bucket
aws s3 sync build/web/ s3://sih-jharkhand-frontend-prod/ --delete

# Invalidate CloudFront CDN Distribution Cache
aws cloudfront create-invalidation --distribution-id E1XXXXXXXXXXXX --paths "/*"
```

### 7.2 Flutter Android APK / App Bundle Build
```bash
cd frontend
flutter build apk --release --dart-define=API_URL=https://api.sih.jharkhand.gov.in
# Output: frontend/build/app/outputs/flutter-apk/app-release.apk

flutter build appbundle --release --dart-define=API_URL=https://api.sih.jharkhand.gov.in
# Output: frontend/build/app/outputs/bundle/release/app-release.aab
```

---

## 8. Monitoring, Backups & Incident Response

### 8.1 Amazon CloudWatch Alarms
- **API High Error Rate**: Alarm when 5XX error responses > 1% over 5 minutes.
- **CPU / Memory Threshold**: Trigger autoscaling scale-out when CPU > 75% or RAM > 80%.
- **Database Connection Spikes**: Alarm when RDS connections exceed 80% of max capacity.

### 8.2 Database Backup Policy
- **Automated Snapshots**: Daily automated RDS snapshot with 14-day retention.
- **Point-in-Time Recovery (PITR)**: 5-minute RPO window across the last 14 days.
- **Pre-deployment Dump**:
  ```bash
  pg_dump -h <HOST> -U sih_admin -d sih_jharkhand > backup_$(date +%F_%T).sql
  ```

---

## 9. Deployment Verification Runbook

After deployment, perform the 5-point sanity check:
1. **Health Check**: `curl -f https://api.sih.jharkhand.gov.in/health` returns `{"status":"healthy","database":"connected"}`.
2. **Auth Verification**: Post credentials to `/api/v1/auth/login` and verify signed JWT response.
3. **Seed Check**: Verify 24 districts and initial challenges via `/api/v1/challenges`.
4. **Media Upload Check**: Test uploading a sample image to `/api/v1/challenges/upload-media`.
5. **AI Pipeline Test**: Call `/api/v1/ai/analyze-challenge` with test description and confirm domain, priority, and similarity results.

---

## 10. Render Deployment (Blueprint)

### 10.1 One-click demo on Render
`render.yaml` at the repository root is a [Render Blueprint](https://render.com/docs/blueprint-spec) for the public evaluation demo. It needs no input.

**Deploy**
1. Push this repository to GitHub (or GitLab) and sign in to [Render](https://render.com).
2. **New → Blueprint**, pick the repository, and click **Apply**. Render creates:
   - `samadhansetu-demo-db`: PostgreSQL 16, free plan, Singapore;
   - `samadhansetu-demo`: a Docker web service, free plan, built from the root `Dockerfile` with `EVALUATOR_MODE=true`.
3. The first build takes several minutes (Flutter web app, then Python dependencies). On start the container applies Alembic migrations and seeds the demo data.
4. Copy the service URL (`https://<service-name>.onrender.com`) into the "Live demo" line of `README.md`.

**What the Blueprint sets:** `ENVIRONMENT=demo`, `DEMO_MODE=true`, `RUN_MIGRATIONS_ON_START=true`, `WEB_CONCURRENCY=1` (fits 512 MB), a generated `SECRET_KEY`, `DATABASE_URL` from the managed database, `STORAGE_TYPE=local`.

`ENVIRONMENT=demo` applies the same fail-closed checks as production (`backend/app/core/config.py`): a strong `SECRET_KEY`, PostgreSQL only, no wildcard CORS, and S3 credentials whenever `STORAGE_TYPE=s3`. It differs from production in only two ways: demo accounts (`DEMO_MODE`) are allowed, and so is local file storage. **Production still rejects both.**

**Verify** (replace the host):
```bash
curl https://<service>.onrender.com/health   # "status":"healthy","environment":"demo","demo_mode":true,"storage":"local-ephemeral"
curl https://<service>.onrender.com/live     # {"status":"alive"}
open https://<service>.onrender.com/docs     # Swagger UI
open https://<service>.onrender.com/         # web app; the login screen lists one-tap demo accounts
```
The demo accounts (`GET /api/v1/demo/accounts`) share the password `password123` and exist only when `DEMO_MODE=true`.

**Free-plan behaviour**
- **Cold start.** The web service sleeps after 15 minutes without traffic, and the next request waits up to about a minute while it wakes. The page then shows a loading message, which after 6 seconds explains the wait. To keep the demo warm during judging, point an uptime monitor at `/live` every 10 minutes; one always-on free service uses about 720 of Render's 750 free instance-hours a month.
- **Uploads are not persistent.** `STORAGE_TYPE=local` writes to the container disk, which is wiped on every restart and redeploy; `/health` reports `"storage":"local-ephemeral"`.
- **Free PostgreSQL expires 30 days after creation.** For a longer-lived demo, switch the database to a paid plan. A new database is migrated and re-seeded automatically on the next start.

**Optional: persistent uploads in a free S3-compatible bucket** (e.g. Cloudflare R2, 10 GB free). In the service's **Environment** settings, set:
```
STORAGE_TYPE=s3
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AWS_REGION=auto
AWS_ACCESS_KEY_ID=<R2 access key>
AWS_SECRET_ACCESS_KEY=<R2 secret key>
S3_BUCKET_NAME=<bucket>
```
`storage_service.py` passes `S3_ENDPOINT_URL` to boto3, so any S3-compatible store works. This path has not been tested against R2 for this release.

**If the build fails** with out-of-memory errors on the free build machine, build the image elsewhere (`docker build --build-arg EVALUATOR_MODE=true -t samadhansetu .`), push it to a registry, and create the Render service from that image with the same environment variables.

**Verified locally** (2026-10-06): the web build (`flutter build web --release --dart-define=EVALUATOR_MODE=true`) and `docker-entrypoint.sh` were run, with the Blueprint's environment, against an empty PostgreSQL 16 database. Migrations and seeding completed; `/health`, `/live`, `/docs` and the web app responded; and all 10 demo accounts signed in. The Docker image itself and a live Render deployment have not been tested from this repository.

### 10.2 Production pilot on Render
`deploy/render.production.yaml` describes a production configuration (`ENVIRONMENT=production`, `DEMO_MODE=false`, S3 storage). Point a Blueprint at that file. Before the first deploy, fill in every `sync: false` variable in the dashboard; the app refuses to start without them:
- `ALLOWED_CORS_ORIGINS`: explicit origins, no wildcard (e.g. `https://your-app.onrender.com`).
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_NAME`: production requires S3 and rejects local storage.
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`: a departmental address, not a personal inbox.
- `CLAMAV_HOST`, `FINANCE_INTEGRATION_PROVIDER`: leave unset unless you are wiring up those integrations.

Run migrations as a release step (`alembic upgrade head` from a Render Shell, with `DATABASE_URL` set), or set `RUN_MIGRATIONS_ON_START=true` while the service has a single instance. The web app is built into the same image and served at `/`; it calls the API on its own origin, so it needs no API URL setting.
