# SIH 26043 — Traceability Matrix & Requirements Verification

**Problem Statement ID**: 26043  
**Title**: A digital platform to crowdsource societal challenges and facilitate collaborative problem solving through universities and industry partnerships.  
**Organization**: Government of Jharkhand — Department of Higher & Technical Education  
**Document Version**: 1.0 (Production Acceptance Release)  

---

## 1. Bidirectional Requirements Traceability Matrix

| Req ID | SIH 26043 Requirement Description | Architecture & Code Implementation | Frontend Screen / Component | Automated Verification Test |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | **Multilingual Citizen Crowdsourcing**: Low-bandwidth, mobile-responsive challenge submission with voice notes, image geotagging, tribal language fallback. | `backend/app/routers/challenges.py`<br>`backend/app/services/storage_service.py` | `SubmitChallengeScreen`<br>`app_strings.dart` (EN/HI/Tribal)<br>`OfflineDraftService` | `tests/test_stage12_e2e_journeys.py::test_citizen_journey_end_to_end`<br>`tests/test_stage3_challenges_and_media.py` |
| **REQ-02** | **AI-Powered Deduplication & Taxonomy Tagging**: Auto-categorization into state SDG domains, duplicate similarity clustering, priority scoring. | `backend/app/services/ai/taxonomy_engine.py`<br>`backend/app/services/ai/duplicate_detector.py`<br>`backend/app/services/ai/queue_service.py` | `ChallengeDetailScreen`<br>`AIDeduplicationBadge`<br>`AIExplanationDialog` | `tests/test_stage4_ai_taxonomy_and_clustering.py`<br>`tests/test_stage12_e2e_journeys.py` |
| **REQ-03** | **Human-in-the-Loop Governance**: Government officers can review, override, validate, or reject AI categorizations without destroying AI audit lineage. | `backend/app/models/models.py` (`AIHumanOverride`)<br>`backend/app/routers/challenges.py` | `GovernmentReviewDialog`<br>`AIHumanOverridePanel` | `tests/test_stage4_ai_taxonomy_and_clustering.py::test_human_override` |
| **REQ-04** | **Multi-Tier Jurisdiction RBAC**: Enforce 4 tiers (STATE, DISTRICT, SUBDIVISION, BLOCK/PANCHAYAT) so officers only review their geographic jurisdiction. | `backend/app/routers/deps.py` (`enforce_jurisdiction_access`)<br>`backend/app/models/models.py` | `OfficerDashboardScreen`<br>`JurisdictionPicker` | `tests/test_stage12_security_negative_properties.py::test_cross_district_tampering_blocked`<br>`tests/test_stage2_auth_and_rbac.py` |
| **REQ-05** | **Academic HEI Collaboration & Mentorship**: Universities, faculty mentors, and student innovator teams bid on validated challenges and submit milestone deliverables. | `backend/app/routers/projects.py`<br>`backend/app/routers/universities.py`<br>`backend/app/services/matching_service.py` | `UniversityHubScreen`<br>`ProjectWorkspaceScreen`<br>`MilestoneTracker` | `tests/test_stage6_projects_and_collaboration.py`<br>`tests/test_stage12_e2e_journeys.py::test_university_hei_collaboration_journey` |
| **REQ-06** | **CSR Funding & Industry Escrow Support**: Corporate partners offer financial grants, equipment, and pilot implementation with immutable ledger records. | `backend/app/routers/industry.py`<br>`backend/app/models/models.py` (`FundingRecord`, `EscrowLedger`) | `IndustryPortalScreen`<br>`CSRGrantDialog`<br>`FundingLedgerCard` | `tests/test_stage7_industry_and_partnerships.py`<br>`tests/test_stage12_e2e_journeys.py::test_industry_partner_sponsorship_journey` |
| **REQ-07** | **Tamper-Evident Audit Chains**: Cryptographic SHA-256 state transaction hashing (`previous_hash` -> `current_hash`) for public finance accountability. | `backend/app/services/audit_service.py`<br>`backend/app/models/models.py` (`AuditLog`, `DomainAuditEvent`) | `AuditLogViewerScreen`<br>`HashVerificationChip` | `tests/test_stage5_status_workflow_and_audit.py`<br>`tests/test_stage12_security_negative_properties.py` |
| **REQ-08** | **Multi-Channel Notification Outbox**: Observable event-driven notifications (In-App, SMS, Email) with retries, failure reasons, and citizen preference consent. | `backend/app/services/notification_service.py`<br>`backend/app/models/models.py` (`NotificationOutbox`) | `NotificationBellWidget`<br>`NotificationSettingsScreen` | `tests/test_stage9_notifications_and_outbox.py`<br>`tests/test_stage11_security_and_operations.py` |
| **REQ-09** | **Verifiable Executive Analytics & "Why this number"**: District drill-downs, exportable CSVs (bounded 5k rows), coarse GPS (~1.1km) PII redaction. | `backend/app/services/analytics_service.py`<br>`backend/app/services/privacy_redaction_service.py` | `AdminDashboardScreen`<br>`KPIMetadataBottomSheet`<br>`ExportAuditNotice` | `tests/test_stage10_analytics_and_dashboards.py`<br>`tests/test_stage12_e2e_journeys.py::test_executive_analytics_journey` |
| **REQ-10** | **Production Security & DevSecOps**: Strict CSP, HSTS, frame protection, 25MB body limit, trusted proxy IP verification, SSE-S3 encrypted object storage, quarantine, and malware scanning. | `backend/app/core/security_headers.py`<br>`backend/app/services/storage_service.py`<br>`backend/app/core/telemetry.py` | Web `index.html` headers<br>Flutter Web CanvasKit | `tests/test_stage11_security_and_operations.py`<br>`tests/test_stage12_security_negative_properties.py` |
| **REQ-11** | **Digital Personal Data Protection (DPDP)**: Technical citizen rights for data export (`/my-data`), correction (`/correct-data`), and anonymization (`/request-erasure`). | `backend/app/services/dpdp_service.py`<br>`backend/app/routers/privacy.py` | `PrivacySettingsScreen`<br>`DataRightsModal` | `tests/test_stage11_security_and_operations.py::test_dpdp_citizen_rights` |
| **REQ-12** | **Disaster Recovery & Operational Runbooks**: Encrypted cold backups, automated restore verification drills, zero-downtime deployment, secrets rotation, incident response. | `scripts/backup/backup_postgres.sh`<br>`scripts/backup/verify_restore.sh`<br>`docs/runbooks/` | DevOps CI/CD workflow | `tests/test_stage11_security_and_operations.py::test_backup_script_execution` |

---

## 2. Security & Verification Assurance Summary

- **Total Functional Stages**: 12 / 12 Complete
- **Database Engine**: PostgreSQL 16 (Supabase cloud production / Alembic migrations `7a8e91d0f2a4`)
- **Storage Substrate**: Private S3/MinIO compatible object store with SSE-S3 (`AES256`) encryption and quarantine scanning
- **Application Metrics**: Real-time Prometheus endpoint at `/metrics`
- **Mobile Compatibility**: WCAG AA 48x48 tap targets, offline drafts, typed localization (EN/HI + Santhali/Ho/Kharia tribal fallback)
