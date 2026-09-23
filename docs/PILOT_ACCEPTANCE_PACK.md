# Pilot Acceptance Pack & Evaluator Guide

**Problem Statement**: SIH 2026 — PS 26043  
**Title**: Crowdsourcing Societal Challenges and Collaborative Problem Solving  
**Beneficiary**: Department of Higher & Technical Education, Government of Jharkhand  
**Environment**: Production Pilot & Evaluator Demo Quarantined Build  
**Release Version**: 1.0.0 (Production Hardened)  

---

## 1. Executive Summary & Purpose

This Pilot Acceptance Pack provides the evaluation committee and state nodal officers with a structured, step-by-step verification methodology to evaluate the Jharkhand Societal Innovation Collaboration Portal.

The platform establishes an end-to-end bridge between:
1. **Citizens, PRIs, and Urban Local Bodies**: Who crowdsource real civic, environmental, rural, and educational challenges across all 24 districts of Jharkhand.
2. **State & District Administration**: Who validate, prioritize, and monitor resolution progress under strict jurisdiction-based SLA governance.
3. **Universities & Research Institutions (HEIs)**: Whose multidisciplinary student and faculty teams tackle verified societal problems through capstone projects, prototypes, and field deployments.
4. **Corporate & Industry Partners**: Who provide CSR funding, technical mentorship, and pilot commercialization pathways.

---

## 2. Pre-Seeded Evaluator Persona Test Accounts

| Persona / Stakeholder | Demo Email | Role in Platform | Jurisdiction / Affiliation |
| :--- | :--- | :--- | :--- |
| **State Government Admin** | `admin.state@jharkhand.gov.in` | Statewide Governance, System Admin, KPI Audit | State Tier (All 24 Districts) |
| **District Officer (Ranchi)** | `officer.ranchi@jharkhand.gov.in` | Challenge Validation, District Review, SLA Monitor | Ranchi District |
| **Panchayati Raj Rep (PRI)** | `pri.ormanjhi@jharkhand.gov.in` | Local Citizen Problem Crowdsourcing & Ground Check | Ormanjhi Block, Ranchi |
| **University Dean / Nodal** | `nodal.bit@bitmesra.ac.in` | Institution Portfolio, Department Collaboration | BIT Mesra |
| **Faculty Mentor** | `mentor.cs@bitmesra.ac.in` | Student Team Guidance, Deliverable Verification | Dept of CSE, BIT Mesra |
| **Student Innovator Lead** | `student.lead@bitmesra.ac.in` | Proposal Submission, Deliverable Uploads, Workspace | B.Tech Innovation Cell |
| **Industry Partner Lead** | `csr.tata@tatasteel.com` | CSR Grants, Technical Mentorship, IP Agreements | Tata Steel CSR Division |
| **Citizen (Rural / Urban)** | `citizen.ranchi@jharkhand.gov.in` | Challenge Crowdsourcing, Status Tracking | Bero Block, Ranchi |

*Default Evaluator Passphrase for Demo Persona Accounts*: `Demo@123456` (Configured solely in quarantined `DEMO_MODE=true` builds).

---

## 3. Evaluator Step-by-Step Acceptance Test Scenarios

### Test Scenario 1: Citizen Challenge Crowdsourcing & Multilingual Usability
1. Open Portal at root URL (`http://localhost:8008` or deployed pilot URL).
2. Switch language to **Hindi (हिन्दी)** via top-bar locale selector; observe typed localization without layout distortion.
3. Login as Citizen (`citizen.ranchi@jharkhand.gov.in`).
4. Navigate to **Post a Challenge** (`/challenges/submit`):
   - Enter title: *"Solar Micro-Grid Failure in Bero Tribal Hamlet"*.
   - Select District: **Ranchi**, Block: **Bero**.
   - Attach supporting field evidence (JPG/PNG or PDF).
   - Click **Submit**.
5. **Expected Result**:
   - Immediate challenge creation with unique tracking code.
   - AI taxonomy engine auto-classifies domain as **Renewable Energy & Rural Infrastructure**.
   - Citizen receives in-app confirmation and SMS outbox record generated.

---

### Test Scenario 2: District Officer Review & Jurisdiction RBAC
1. Login as District Officer (`officer.ranchi@jharkhand.gov.in`).
2. Open **Officer Dashboard**:
   - Filter challenges by status: `SUBMITTED`.
   - Verify only challenges within **Ranchi District** appear in the actionable queue.
3. Open the newly submitted Bero challenge:
   - Review AI classification, confidence score, and deduplication cluster.
   - Approve / Validate challenge with priority **HIGH**.
4. **Expected Result**:
   - Challenge transitions to `VALIDATED`.
   - Immutable audit log entry recorded with SHA-256 state transaction hash.
   - Notification dispatched to universities matching the domain taxonomy.

---

### Test Scenario 3: University Proposal Submission & Faculty Verification
1. Login as Student Lead (`student.lead@bitmesra.ac.in`).
2. Browse **Validated Challenges**; select the Bero Solar Micro-Grid challenge.
3. Click **Submit Solution Proposal**:
   - Detail proposed technical solution (IoT-based inverter monitoring).
   - Nominate Faculty Mentor (`mentor.cs@bitmesra.ac.in`).
   - Submit proposal.
4. Login as Faculty Mentor (`mentor.cs@bitmesra.ac.in`):
   - Review proposal and endorse student project team.
5. **Expected Result**:
   - Proposal transitions to `APPROVED` project workspace.
   - Milestone schedule initialized with typed evidence requirements.

---

### Test Scenario 4: Industry CSR Grant & Escrow Ledger
1. Login as Industry Partner (`csr.tata@tatasteel.com`).
2. Navigate to **Industry Hub** -> browse active innovation projects.
3. Select Bero Solar project workspace:
   - Click **Offer CSR Grant**: Enter INR `2,50,000`, equipment support, and mentorship agreement.
4. **Expected Result**:
   - Formal bilateral agreement record created.
   - Escrow funding milestone tracked with transparent public accountability.

---

### Test Scenario 5: Statewide Executive Governance & Verifiable Analytics
1. Login as State Government Admin (`admin.state@jharkhand.gov.in`).
2. Navigate to **Executive Analytics Dashboard**:
   - Inspect State KPIs: Total Crowdsourced, Validated, Active HEI Projects, Resolved.
   - Click on any KPI card; click **"Why this number"**:
     - Inspect underlying source record list with pagination and audit IDs.
   - Click **Export Audit CSV**:
     - Observe bounded export (max 5,000 rows) with coarse GPS (~1.1km) and masked citizen PII.
3. **Expected Result**:
   - Complete executive visibility without violating citizen privacy or crashing DB pools.

---

## 4. Evaluator Acceptance Sign-off Matrix

| Acceptance Criteria | Technical Implementation Verification | Evaluator Status |
| :--- | :--- | :--- |
| **1. Functional Completeness** | Crowdsourcing, AI deduplication, RBAC, HEI bidding, CSR funding, notifications | [ ] PASS / [ ] FAIL |
| **2. Security & Privacy** | Strict CSP, HSTS, 25MB body limit, SSE-S3 encrypted storage, DPDP data rights | [ ] PASS / [ ] FAIL |
| **3. Reliability & Scaling** | Background worker with concurrency locks (`SKIP LOCKED`), Prometheus telemetry | [ ] PASS / [ ] FAIL |
| **4. Disaster Recovery** | OpenSSL AES-256 automated backups, verified restore drills, runbooks | [ ] PASS / [ ] FAIL |
| **5. Mobile & Usability** | WCAG AA tap targets (48x48), offline drafts, Hindi/Tribal localization | [ ] PASS / [ ] FAIL |

**Evaluator Signature**: _____________________________  
**Date**: _____________________________  
**Designation**: Evaluator / State Nodal Officer, Government of Jharkhand  
