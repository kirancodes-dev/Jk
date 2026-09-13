# REST API Documentation — SIH 2026 Problem Statement 26043

FastAPI auto-generates interactive OpenAPI documentation available at:
`http://localhost:8008/docs` (Swagger UI) and `http://localhost:8008/redoc` (ReDoc).

---

## 1. Authentication Endpoints (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | Email & password login, returns JWT token & role | No |
| `POST` | `/auth/register` | User signup with role-specific profile creation | No |
| `POST` | `/auth/verify-otp` | 6-digit OTP verification | No |
| `POST` | `/auth/forgot-password` | Requests password reset code | No |
| `POST` | `/auth/reset-password` | Resets password with verified OTP | No |
| `GET` | `/auth/me` | Fetches authenticated user profile | Yes (Bearer) |

---

## 2. Challenge Endpoints (`/api/v1/challenges`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/challenges` | List challenges with filters (`category`, `district`, `status`, `search`) | No |
| `POST` | `/challenges` | Citizen reports challenge; triggers automatic AI classification & university matching | Yes (CITIZEN) |
| `GET` | `/challenges/my` | Challenges reported by the authenticated citizen | Yes (CITIZEN) |
| `GET` | `/challenges/nearby` | Challenges in/around selected district (`?district=Ranchi`) | No |
| `GET` | `/challenges/{id}` | Complete challenge details, AI analysis, matches, audit history, comments | No |
| `POST` | `/challenges/{id}/status` | Advances challenge status with audit remarks | Yes (ADMIN/UNIV) |
| `POST` | `/challenges/{id}/assign` | Government admin assigns nodal university | Yes (ADMIN) |
| `POST` | `/challenges/{id}/comments`| Adds stakeholder comment / inquiry | Yes (Bearer) |
| `POST` | `/challenges/upload` | Uploads photo/video/document attachment | Yes (Bearer) |

---

## 3. AI Service Endpoints (`/api/v1/ai`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/ai/analyze-text` | Real-time text analysis: extracts domain, priority, keywords, recommended solution, and ranks top 3 universities | No |

---

## 4. University & Project Endpoints (`/api/v1/universities`, `/api/v1/projects`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/universities` | Lists all registered universities with NIRF & incubation centers | No |
| `GET` | `/universities/dashboard`| University statistics (assigned, active projects, student teams) | Yes (UNIVERSITY) |
| `POST` | `/universities/accept-challenge/{id}` | Formally accepts challenge for mobilization | Yes (UNIVERSITY) |
| `POST` | `/universities/reject-challenge/{id}` | Declines challenge with capacity remarks | Yes (UNIVERSITY) |
| `GET` | `/projects` | Lists all active societal innovation projects | No |
| `POST` | `/projects` | Initializes project, assigns mentor and multidisciplinary team | Yes (UNIVERSITY) |
| `GET` | `/projects/{id}` | Detailed project view: milestones, team roster, tasks, collaborations | No |
| `POST` | `/projects/{id}/milestones` | Adds project milestone | Yes (UNIVERSITY/MENTOR) |
| `PATCH`| `/projects/{id}/milestones/{m_id}` | Updates completion percentage (0-100%) | Yes (MENTOR/STUDENT) |
| `POST` | `/projects/{id}/tasks` | Adds student development task | Yes (MENTOR/UNIV) |
| `POST` | `/projects/{id}/proposals` | Submits formal solution proposal to Government Admin | Yes (UNIV/MENTOR) |
| `POST` | `/projects/{id}/collaborations` | Industry partner submits collaboration offer | Yes (INDUSTRY) |

---

## 5. Student & Faculty Endpoints (`/api/v1/students`, `/api/v1/faculty`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/students/dashboard` | Student tasks, project assignments, skills | Yes (STUDENT) |
| `POST` | `/students/submit-task/{id}` | Submits progress updates, notes, attachments | Yes (STUDENT) |
| `GET` | `/faculty/dashboard` | Mentored projects, pending student reviews, pending milestones | Yes (FACULTY) |
| `POST` | `/faculty/approve-milestone/{id}` | Faculty mentor formal sign-off on milestone | Yes (FACULTY) |

---

## 6. Industry & Government Admin Endpoints (`/api/v1/industry`, `/api/v1/admin`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/industry/dashboard` | Active CSR collaborations & focus areas | Yes (INDUSTRY) |
| `GET` | `/industry/browse-projects` | Filter projects by domain, technology, stage | No |
| `GET` | `/admin/dashboard` | Statewide totals (Submitted, Assigned, In Progress, Resolved) | Yes (ADMIN) |
| `GET` | `/admin/jharkhand-map` | 24-district data with population, coordinates, and challenge counts | Yes (ADMIN) |
| `GET` | `/admin/analytics` | Distributions by Category, Priority, and District | Yes (ADMIN) |
| `GET` | `/admin/impact` | Statewide tangible outcomes (patents, startups, beneficiaries) | Yes (ADMIN) |
| `POST` | `/admin/challenges/{id}/validate` | Officially validates challenge for assignment | Yes (ADMIN) |
| `GET` | `/admin/reports/csv` | Streams CSV report of all statewide challenges | Yes (ADMIN) |

---

## 7. Notifications & Demo Seeding (`/api/v1/notifications`, `/api/v1/demo`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/notifications` | List user in-app notifications | Yes (Bearer) |
| `PATCH`| `/notifications/{id}/read` | Marks notification as read | Yes (Bearer) |
| `GET` | `/demo/accounts` | Quick listing of credentials for all 6 demo roles | No |
| `POST` | `/demo/reset` | Resets and re-seeds database with realistic Jharkhand demo data | No |
