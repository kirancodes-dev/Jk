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
The backend container runs as an unprivileged non-root user (`appuser`, UID 10001) for container security compliance.

```dockerfile
FROM python:3.12-slim AS runtime
# Installs libpq5 and minimal dependencies
# Copies application and creates unprivileged appuser (UID 10001)
# Exposes port 8008 and defines HEALTHCHECK on /live
```

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
