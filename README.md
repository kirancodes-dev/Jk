# 🇮🇳 Societal Innovation Collaboration Portal — Jharkhand
### Smart India Hackathon (SIH) 2026 — Problem Statement 26043

> **"A digital platform to crowdsource societal challenges and facilitate collaborative problem solving through universities and industry partnerships."**
> 
> **Organization:** Government of Jharkhand  
> **Department:** Department of Higher & Technical Education  
> **Theme:** Smart Education  
> **Category:** Software / Mobile & Web Full-Stack  

---

## 🌟 Executive Summary

The **Societal Innovation Collaboration Portal** bridges the gap between grassroots citizens facing everyday civic and developmental challenges across all **24 districts of Jharkhand**, higher educational institutions (engineering colleges and universities), and industry CSR partners. 

By applying an automated **AI-powered problem analysis pipeline**, the platform classifies civic issues, detects duplicates, evaluates socio-economic severity, recommends top-fit universities, and orchestrates academic-industry student projects through a **10-stage transparent problem-solving lifecycle** with real-time verification and geotagged impact audits.

---

## 🏗️ Architecture & Technology Stack

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Flutter 3.x / Dart)                      │
│   Material 3 • Mobile-First Responsive • Jharkhand Forest Theme        │
│   6 Interactive Role Dashboards • Offline Drafts • Quick Role Switcher  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ REST APIs (JSON / JWT)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI / Python)                        │
│   Asynchronous Endpoints • JWT Security • RBAC Middleware               │
│   Storage Abstraction (Local / AWS S3) • In-App Notification System     │
└──────────────┬─────────────────────┬────────────────────┬───────────────┘
               │                     │                    │
               ▼                     ▼                    ▼
┌─────────────────────────┐ ┌──────────────────┐ ┌────────────────────────┐
│      DATABASE LAYER     │ │   AI PIPELINE    │ │     FILE STORAGE       │
│ SQLAlchemy 2.0 ORM      │ │ Domain NLP       │ │ AWS S3 API Compatible  │
│ Dual Engine Support:    │ │ Cosine Duplicates│ │ Local Disk Fallback    │
│  - SQLite (Zero-dep Dev)│ │ Priority Scoring │ │ `/uploads` Directory   │
│  - PostgreSQL (Prod)    │ │ University Rank  │ │ Geotagged Media        │
└─────────────────────────┘ └──────────────────┘ └────────────────────────┘
```

### Stack Components
- **Frontend**: Flutter (Dart), Material 3, Provider State Management, SharedPreferences Offline Cache, Mobile-First Android UX.
- **Backend**: FastAPI, Python 3.14, Pydantic v2 schemas, Passlib (Bcrypt), PyJWT.
- **Database**: SQLAlchemy ORM with dual-dialect abstraction (instant SQLite for local evaluation + PostgreSQL 16 for production), 28 interconnected relational tables.
- **AI Engine**: Python-based NLP Classifier, TF-IDF cosine duplicate matching, weighted multi-factor priority calculator, and university capability matrix matching (expandable to Gemini API).
- **Storage**: Pluggable storage service supporting AWS S3 and local static mounting.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ (tested with Python 3.14)
- Flutter SDK 3.x with Dart
- Git

---

### 1. Start the Backend API Server

The backend runs out of the box with zero external database configuration required using the pre-seeded SQLite database `sih_jharkhand.db` (or connects to PostgreSQL if `DATABASE_URL` is set).

```bash
# Navigate to project root
cd /Users/kiranbiradar/JK

# Activate virtual environment
source backend/.venv/bin/activate

# Install requirements (if not already installed)
pip install -r backend/requirements.txt

# Run the FastAPI server on port 8008
uvicorn backend.app.main:app --host 0.0.0.0 --port 8008 --reload
```

- **Swagger Interactive API Docs**: [http://localhost:8008/docs](http://localhost:8008/docs)
- **ReDoc API Documentation**: [http://localhost:8008/redoc](http://localhost:8008/redoc)
- **Health Check Endpoint**: [http://localhost:8008/health](http://localhost:8008/health)

---

### 2. Start the Flutter Frontend

The Flutter app connects to `http://localhost:8008/api/v1` and runs in Chrome or on an Android emulator/device.

```bash
cd /Users/kiranbiradar/JK/frontend

# Fetch dependencies
flutter pub get

# Run on Chrome for instant live preview
flutter run -d chrome --web-port 3000

# Or build static web distribution:
# flutter build web --release
```

---

## 👥 Pre-seeded Demo Accounts (SIH Jury Evaluation)

The system comes pre-loaded with sample accounts for all 6 stakeholder roles. **All accounts share the default password:** `password123`.

You can also use the **1-Click Demo Switcher chips** at the bottom of the Login Screen to instantly switch between these profiles without typing credentials!

| Role | Email | Password | Pre-seeded Persona |
|:---|:---|:---|:---|
| **Citizen** | `citizen@jharkhand.gov.in` | `password123` | Ramesh Kumar, Angara Village, Ranchi |
| **University Admin** | `university@bitmesra.ac.in` | `password123` | Dr. S. N. Sinha, BIT Mesra Dean |
| **Student Innovator** | `student@bitmesra.ac.in` | `password123` | Priya Kumari, B.Tech Env Engineering |
| **Faculty Mentor** | `faculty@bitmesra.ac.in` | `password123` | Prof. Arvind Sharma, HOD Water Resources |
| **Industry Partner** | `industry@tatasteel.com` | `password123` | Tata Steel CSR Foundation |
| **Govt Administrator** | `admin@jharkhand.gov.in` | `password123` | Rajesh Verma, Additional Secretary H&TE |

---

## 📋 End-to-End 20-Step SIH Demonstration Flow

Follow this exact walkthrough to showcase the complete problem-solving lifecycle to hackathon judges:

### Phase 1: Citizen Crowdsourcing & AI Classification
1. **Citizen Login**: Open portal and login as `citizen@jharkhand.gov.in`.
2. **Explore Challenges**: View citizen feed showing existing challenges in Ranchi, Dhanbad, and Jamshedpur with status badges.
3. **Report New Challenge**: Click `+ Report Challenge`. Enter:
   - *Title*: `Severe Ground Water Contamination in Angara Block`
   - *District*: `Ranchi`, *Block*: `Angara`
   - *Category*: `Water & Sanitation`
   - *Estimated Affected*: `5000`
4. **Offline Draft Test**: Toggle airplane mode or use "Save Draft" to see local persistent offline draft caching.
5. **AI Analysis Trigger**: Submit challenge. The real-time AI engine performs:
   - Automated NLP categorization into `Water & Sanitation`
   - Priority severity score calculation (`0.88 - High Priority`)
   - Duplicate similarity check against historical database
   - University matching recommendations (identifies BIT Mesra & NIT Jamshedpur)
6. **Confirmation & Tracking**: View the newly created challenge with its 10-stage lifecycle tracker (`SUBMITTED` -> `AI_ANALYZED` -> `VALIDATED`).

---

### Phase 2: Government Validation & University Assignment
7. **Govt Admin Login**: Use 1-click switcher to switch to `admin@jharkhand.gov.in`.
8. **Administrative Overview**: Inspect Jharkhand 24-district heatmap, pending approvals, and statewide impact KPIs.
9. **Validate & Assign**: Open Challenge Management, inspect the Angara Water challenge, review AI score (88/100), approve validation, and officially route it to BIT Mesra.

---

### Phase 3: University Adoption & Project Creation
10. **University Login**: Switch to `university@bitmesra.ac.in`.
11. **Challenge Discovery**: View incoming assigned challenges tailored to the institution's environmental research strengths.
12. **Create Project**: Click "Adopt Challenge" and create R&D project:
    - *Title*: `IoT Solar-Powered Reverse Osmosis & UV Filtration Unit`
    - *Budget*: `₹2,50,000`
    - *Lead Faculty*: Prof. Arvind Sharma
    - *Team Lead*: Priya Kumari (Student)
13. **Milestone Definition**: Create 3 developmental milestones:
    - *Milestone 1*: Water sample chemical analysis and sensor prototyping (30%)
    - *Milestone 2*: Pilot plant installation at Angara community center (40%)
    - *Milestone 3*: Water quality testing, verification, and community handover (30%)

---

### Phase 4: Student Execution & Faculty Mentorship
14. **Student Dashboard**: Switch to `student@bitmesra.ac.in`.
15. **Task Execution**: View assigned project tasks, milestone timelines, and skill badges.
16. **Submit Milestone Deliverable**: Click on Milestone 1, upload field test report, submit proof of work, and request faculty review.
17. **Faculty Approval**: Switch to `faculty@bitmesra.ac.in`, review student submission, provide qualitative mentorship feedback, and approve milestone progression.

---

### Phase 5: Industry CSR Sponsorship & Deployment Handover
18. **Industry Sponsor**: Switch to `industry@tatasteel.com`.
19. **Browse & Fund**: Navigate to "CSR Opportunities", filter by `Water & Sanitation`, discover the Angara project, and submit a **₹2,50,000 CSR Grant & Technical Mentorship Offer**.
20. **Impact & Citizen Closure**: 
    - Switch back to `citizen@jharkhand.gov.in` to observe the challenge transition to `RESOLVED`.
    - Switch to `admin@jharkhand.gov.in` to view updated statewide metrics: **5,000 citizens impacted**, water quality restored, and verified certificate of completion issued.

---

## 📊 Relational Database Architecture (28 Entities)

The database schema (`database/schema.sql` and `DATABASE.md`) implements clean third normal form (3NF) relational models:

1. `users` — Authentication, role-based access, district tagging
2. `citizens` — Community profile, identity, reported counts
3. `universities` — Accreditation, research specializations, NIRF rank
4. `students` — Enrollment, department, skill tags, project history
5. `faculty_mentors` — Designation, research domain, mentored projects
6. `industry_partners` — Corporate profile, CSR budget, sector preferences
7. `government_officials` — Department, jurisdiction, approval tier
8. `challenges` — Geotagged civic problems, severity, 10-stage status
9. `challenge_media` — Photos, videos, lab reports, attachments
10. `ai_challenge_analysis` — NLP domain, priority scores, duplicates
11. `duplicate_challenges` — Cosine similarity links between reports
12. `university_challenge_matches` — Ranked match scores and rationale
13. `projects` — Academic-industry collaborative problem-solving ventures
14. `project_members` — Student and faculty team composition
15. `project_milestones` — Weighted progress stages and deliverables
16. `project_tasks` — Kanban task board items, assignments, status
17. `task_submissions` — Student code, design schematics, test data
18. `industry_sponsorships` — CSR funding grants, equipment, mentors
19. `project_updates` — Public progress timeline entries with media
20. `challenge_votes` — Citizen community upvoting for urgency
21. `challenge_comments` — Public discussion and community input
22. `solution_verifications` — Official field audits and geotagged checks
23. `impact_metrics` — Citizens impacted, cost saved, carbon offset
24. `notifications` — Targeted role-based alerts and system messages
25. `districts` — 24 official administrative districts of Jharkhand
26. `offline_sync_queue` — Resilient sync journal for low-connectivity rural areas
27. `audit_logs` — Immutable compliance history of administrative actions
28. `badges_and_rewards` — Gamified student innovation credentials

---

## 🧪 Testing & Quality Assurance

### Backend Automated Test Suite
Run the full integration test suite covering auth, challenge ingestion, AI analysis, projects, and impact reporting:
```bash
pytest tests/test_backend.py -v
```
**Results:** `7 passed in 0.89s (100% pass rate)`

### Frontend Test Suite & Static Verification
```bash
cd frontend
flutter test
flutter analyze
flutter build web --release
```
**Results:** `0 issues found, successful production bundle compiled.`

---

## 🏛️ Aligned with Government of Jharkhand Initiatives
- **Smart Education Policy**: Engages engineering colleges directly in state development challenges.
- **Jharkhand Industrial Policy 2021**: Bridges corporate CSR funding directly to localized public university R&D.
- **Mukhyamantri Protsahan Yojana**: Recognizes and rewards students with verified state innovation certificates.

---

## 📄 License & Intellectual Property
Developed for **Smart India Hackathon 2026** under the auspices of the **Department of Higher & Technical Education, Government of Jharkhand**.
All rights reserved © 2026.
