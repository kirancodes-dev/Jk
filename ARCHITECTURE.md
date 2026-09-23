# Architectural Design Document — SIH 2026 Problem Statement 26043

## 1. Executive Summary
**Platform**: Societal Innovation & Multidisciplinary Collaboration Portal  
**Organization**: Government of Jharkhand, Department of Higher & Technical Education  
**Theme**: Smart Education & Societal Problem Solving  

The platform crowdsources societal challenges directly from citizens across all 24 districts of Jharkhand, utilizes a deterministic & pluggable AI engine to classify domains, score urgency, detect duplicate submissions, and match challenges to top universities (e.g. BIT Mesra, NIT Jamshedpur, IIT-ISM Dhanbad). Multidisciplinary student teams and faculty mentors build functional prototypes with industry CSR sponsorship, tracked by state government administrators on live geospatial dashboards.

---

## 2. High-Level System Architecture

```
                                  ┌────────────────────────────────┐
                                  │      CLIENT APPLICATIONS       │
                                  │  (Flutter Material 3 Mobile/Web│
                                  └───────────────┬────────────────┘
                                                  │ HTTPS / REST JSON
                                                  ▼
                                  ┌────────────────────────────────┐
                                  │         API GATEWAY            │
                                  │    (FastAPI Async Server)      │
                                  └───────┬───────────────┬────────┘
                                          │               │
                     ┌────────────────────┴──────┐        └──────────────────────┐
                     ▼                           ▼                               ▼
       ┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
       │     AI ANALYSIS ENGINE    │ │   RELATIONAL DATA LAYER   │ │   MEDIA STORAGE ENGINE    │
       │ • Domain Classification   │ │ • PostgreSQL (Production) │ │ • AWS S3 Bucket           │
       │ • Priority Evaluation     │ │ • SQLite (Local dev only) │ │ • Local Media Directory   │
       │ • TF-IDF Duplicate Engine │ │ • 33 Relational Entities  │ │ • Image/Video/Doc Uploads │
       │ • University Matchmaker   │ │ • Alembic Version Control │ └───────────────────────────┘
       └───────────────────────────┘ └───────────────────────────┘
```

---

## 3. Core Subsystems

### 3.1 Role-Based Access Control (RBAC) Subsystem
The platform enforces strict role boundaries across 6 stakeholder profiles:
1. **CITIZEN**: Ground reporting, GPS capture, offline draft caching, 10-stage solution lifecycle tracking.
2. **UNIVERSITY**: Institutional dashboard, challenge discovery, project mobilization, multidisciplinary team assembly.
3. **STUDENT**: Task boards, laboratory work submission, prototype telemetry notes, cross-department team collaboration.
4. **FACULTY MENTOR**: Academic supervision, student submission verification, formal milestone approvals, technical guidance.
5. **INDUSTRY PARTNER**: CSR exploration, technical support, prototype grants, field pilot implementation.
6. **GOVERNMENT ADMIN**: Statewide district heatmaps, challenge validation, university assignment, impact dashboards.

### 3.2 AI & NLP Pipeline
When a societal challenge is submitted:
1. **Text Normalization**: Strips punctuation, filters stopwords, normalizes vocabulary.
2. **Domain Classification**: Scores challenge content against 10 domain dictionaries (Water Management, Agriculture, Healthcare, Education, Sanitation, Environment, Energy, Urban Infrastructure, Rural Livelihoods, Accessibility).
3. **Priority & Urgency Matrix**: Evaluates health hazard keywords (`shortage`, `poison`, `outbreak`, `crisis`, `fatal`) to assign `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` priority.
4. **Duplicate Detection Engine**: Vectorizes challenge title and description to compute token cosine similarity against all registered challenges in the state database. Returns similarity scores and flags potential duplicates.
5. **University Matching Engine**: Computes compatibility scores based on:
   - District proximity (15% weight)
   - Specialized departmental research centers (18% weight)
   - Incubation and innovation labs (7% weight)
   - Ranking formula generates realistic percentages (e.g. 94.5%, 82.0%, 76.5%).

### 3.3 Offline / Rural Connectivity Layer
For remote rural areas in Jharkhand with intermittent cellular coverage:
- **Local Storage Drafts**: Automatically saves form inputs into `SharedPreferences`.
- **Restoration Hook**: On opening the app, unsaved drafts are restored with a 1-tap confirmation.
- **Graceful Network Fallback**: Media uploads and text submissions queue locally until connection returns.

---

## 4. Security & Compliance
- **JWT Authentication**: Signed with HMAC-SHA256, 7-day token expiration.
- **Password Hashing**: Salted bcrypt password hashes.
- **Data Isolation**: Multi-tenant role checks on every API endpoint.
- **Environment Driven**: Zero hardcoded secrets; loaded via `.env`.
