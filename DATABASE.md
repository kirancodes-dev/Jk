# Database Architecture & Relational Schema — SIH 2026

## 1. Overview
The database layer is engineered with SQLAlchemy ORM and managed version-by-version using **Alembic**.

- **Production & CI**: Strictly requires **PostgreSQL 16+** with connection pooling (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`). SQLite is strictly prohibited when `ENVIRONMENT=production`.
- **Local Development / Test Fallback**: Explicitly supports local SQLite (`sqlite:///./sih_jharkhand.db`) for zero-friction setup.
- **Total Entities**: 33 Relational Tables with 3NF normalization.
- **Alembic Single Source of Truth**: Schema creation and migrations in production are exclusively driven by `alembic upgrade head`. Runtime startup reliance on `Base.metadata.create_all` has been completely eliminated for production.
- **Foreign Key Constraints & Cascade Rules**: Enforced across all relationships.
- **Indexes & Unique Constraints**: Applied on lookup and filtering columns (`users.email`, `challenges.category`, `challenges.status`, `districts.name`, `revoked_tokens.jti`, etc.).

---

## 2. Entity Relationship Summary

```
[districts] ──< [challenge_locations] >── [challenges] ──< [challenge_media]
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
             [ai_analysis]         [challenge_similarity]     [university_matches]
                                                                        │
                                                                        ▼
                                                                  [universities]
                                                                        │
                                                                        ▼
                                                                   [projects]
                                                                        │
                    ┌─────────────────────────┬─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼                         ▼
            [project_members]        [project_milestones]        [project_tasks]       [solution_proposals]
                    │                         │                         │
                    ▼                         ▼                         ▼
                [students]          [verification_records]    [industry_collaborations]
```

---

## 3. Database Tables (Complete 33 Entities)

| Table Name | Primary Key | Key Foreign Keys | Purpose |
| :--- | :--- | :--- | :--- |
| `districts` | `id` | - | All 24 administrative districts of Jharkhand with GPS & population |
| `government_departments` | `id` | - | Nodal departments (Higher & Technical Education) |
| `challenge_categories` | `id` | - | Domain taxonomy classifications and icons |
| `impact_metrics` | `id` | - | Statewide cumulative metrics (patents, startups, beneficiaries) |
| `revoked_tokens` | `id` | - | JWT revocation blacklist with expiration indexing |
| `users` | `id` | - | Platform user credentials, bcrypt password hash, role enum |
| `audit_logs` | `id` | - | Immutable compliance audit log of security and administrative events |
| `citizens` | `id` | `user_id -> users.id` | Profile details for citizen problem reporters |
| `industry_partners`| `id` | `user_id -> users.id` | Corporate CSR partners (Tata Steel, Bokaro Steel, etc.) |
| `organization_profiles`| `id` | - | Organization verification records, legal registrations, and compliance |
| `universities` | `id` | `user_id -> users.id` | University institutions, incubation & innovation labs, NIRF rank |
| `departments` | `id` | `university_id -> universities.id` | Academic departments (Civil, CSE, ECE, Environmental, etc.) |
| `university_expertise` | `id` | `university_id` | Departmental research domains and matching weights |
| `faculty` | `id` | `user_id`, `university_id`, `department_id` | Faculty mentors supervising multidisciplinary student teams |
| `students` | `id` | `user_id`, `university_id`, `department_id` | Student innovators with registered technical skillsets |
| `challenges` | `id` | `citizen_id`, `assigned_university_id` | Core societal problem records with 10-stage lifecycle status |
| `challenge_locations` | `id` | `challenge_id`, `district_id` | District, block, village, and GPS latitude/longitude |
| `challenge_media` | `id` | `challenge_id` | File attachments (photos, videos, documents) |
| `ai_analysis` | `id` | `challenge_id` | AI classified domain, priority, keywords, recommended solution |
| `challenge_similarity` | `id` | `challenge_id`, `similar_challenge_id` | Duplicate challenge detection score and matched terms |
| `university_matches` | `id` | `challenge_id`, `university_id` | Ranked compatibility percentage (e.g. 94.5%) |
| `status_history` | `id` | `challenge_id` | Immutable audit trail of challenge status transitions |
| `citizen_feedback` | `id` | `challenge_id`, `citizen_id` | Citizen satisfaction, resolution ratings, and feedback |
| `projects` | `id` | `challenge_id`, `university_id`, `faculty_mentor_id` | Multidisciplinary projects working on challenge solutions |
| `project_members` | `id` | `project_id`, `student_id` | Student roster with team roles (Software, Hardware, Hydraulics) |
| `project_milestones` | `id` | `project_id` | Milestone progress (0% - 100%) and faculty sign-offs |
| `project_tasks` | `id` | `project_id`, `assigned_to_student_id` | Engineering tasks, completion flags, and submission notes |
| `project_documents` | `id` | `project_id` | Technical design docs, CAD models, lab reports |
| `solution_proposals` | `id` | `project_id` | Formal technical proposals with budgets and timelines |
| `industry_collaborations` | `id` | `project_id`, `industry_id` | CSR support (Mentorship, grants, prototype funding, pilots) |
| `verification_records` | `id` | `project_id`, `milestone_id` | Independent geotagged field inspections and officer sign-offs |
| `comments` | `id` | `challenge_id`, `user_id` | Stakeholder discussions between citizen, university, and govt |
| `notifications` | `id` | `user_id` | In-app alerts for status transitions, team invites, and offers |

---

## 4. Database Setup & Alembic Migrations

Alembic is the single authoritative schema change mechanism:
- **Baseline Migration**: `alembic/versions/f48420fc1dd0_initial_production_schema.py` contains explicit DDL for all 33 tables, composite indexes, foreign keys, and PostgreSQL enums.
- **Upgrade**:
  ```bash
  alembic upgrade head
  ```
- **Downgrade**:
  ```bash
  alembic downgrade base
  ```
- **Programmatic Runner**: `backend.app.core.db_migrate.run_migrations()` provides an observable, transaction-safe migration runner that re-raises any database exceptions without swallowing errors.

