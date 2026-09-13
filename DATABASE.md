# Database Architecture & Relational Schema — SIH 2026

## 1. Overview
The database layer is engineered with SQLAlchemy ORM supporting both **PostgreSQL** (production target) and **SQLite** (instant zero-friction local development fallback).

- Total Entities: 28 Tables
- Foreign Key Constraints & Cascade Rules: Enforced on all parent-child relationships
- Indexes: Applied on lookup columns (`users.email`, `challenges.category`, `challenges.status`, `districts.name`, etc.)

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
                    │                                                   │
                    ▼                                                   ▼
                [students]                                      [industry_collaborations]
```

---

## 3. Core Database Tables (Minimum Specification)

| Table Name | Primary Key | Key Foreign Keys | Purpose |
| :--- | :--- | :--- | :--- |
| `districts` | `id` | - | All 24 administrative districts of Jharkhand with GPS & population |
| `users` | `id` | - | Platform user credentials, bcrypt password hash, role enum |
| `citizens` | `id` | `user_id -> users.id` | Profile details for rural citizen problem reporters |
| `universities` | `id` | `user_id -> users.id` | University institutions, incubation & innovation labs, NIRF rank |
| `departments` | `id` | `university_id -> universities.id` | Academic departments (Civil, CSE, ECE, Environmental, etc.) |
| `faculty` | `id` | `user_id`, `university_id`, `department_id` | Faculty mentors supervising multidisciplinary student teams |
| `students` | `id` | `user_id`, `university_id`, `department_id` | Student innovators with registered technical skillsets |
| `industry_partners`| `id` | `user_id -> users.id` | Corporate CSR partners (Tata Steel, Bokaro Steel, etc.) |
| `government_departments` | `id` | - | Nodal departments (Higher & Technical Education) |
| `challenges` | `id` | `citizen_id`, `assigned_university_id` | Core societal problem records with 10-stage lifecycle status |
| `challenge_locations` | `id` | `challenge_id`, `district_id` | District, block, village, and GPS latitude/longitude |
| `challenge_media` | `id` | `challenge_id` | File attachments (photos of dried wells, crop blights, documents) |
| `ai_analysis` | `id` | `challenge_id` | AI classified domain, priority, keywords, recommended solution |
| `challenge_similarity` | `id` | `challenge_id`, `similar_challenge_id` | Duplicate challenge detection score and matched terms |
| `university_expertise` | `id` | `university_id` | Departmental research domains and matching weights |
| `university_matches` | `id` | `challenge_id`, `university_id` | Ranked compatibility percentage (e.g. 94.5%) |
| `projects` | `id` | `challenge_id`, `university_id`, `faculty_mentor_id` | Multidisciplinary projects working on challenge solutions |
| `project_members` | `id` | `project_id`, `student_id` | Student roster with team roles (Software, Hardware, Hydraulics) |
| `project_milestones` | `id` | `project_id` | Milestone progress (0% - 100%) and faculty sign-offs |
| `project_tasks` | `id` | `project_id`, `assigned_to_student_id` | Engineering tasks, completion flags, and submission notes |
| `solution_proposals` | `id` | `project_id` | Formal technical proposals with budgets and timelines |
| `industry_collaborations` | `id` | `project_id`, `industry_id` | CSR support (Mentorship, grants, prototype funding, pilots) |
| `status_history` | `id` | `challenge_id` | Immutable audit trail of every status change and remarks |
| `comments` | `id` | `challenge_id`, `user_id` | Stakeholder discussions between citizen, university, and govt |
| `notifications` | `id` | `user_id` | In-app alerts for status transitions, team invites, and offers |
| `impact_metrics` | `id` | - | Statewide cumulative metrics (patents, startups, beneficiaries) |

---

## 4. Database Setup & Migrations
The database schema DDL is maintained in:
- SQL DDL: `database/schema.sql`
- SQLAlchemy Models: `backend/app/models/models.py`
- Automatic Migration: On server startup, `Base.metadata.create_all(bind=engine)` creates all missing tables automatically.
