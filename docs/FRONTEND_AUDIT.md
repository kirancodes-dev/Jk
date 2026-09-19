# Frontend Comprehensive Audit (SIH26043)

**Platform**: Jharkhand Societal Innovation Collaboration Portal  
**Framework**: Flutter / Dart (Material 3)  
**Date**: September 2026  
**Auditor**: Senior Full-Stack & Government Digital Platform Architect  

---

## Executive Summary
The Flutter application contains a rich collection of 28+ screens covering Citizen, Government Admin, University, Faculty, Student, and Industry roles. However, it was built primarily as a demonstration prototype with several UI-level hardcodings, demo-only shortcuts, inconsistent widget hierarchies, and missing feedback states.

---

## Detailed Screen-by-Screen Audit

### 1. Authentication & Common Screens (`frontend/lib/screens/common/`)

| Screen | Classification | Identified Issues & Gaps |
| :--- | :--- | :--- |
| `login_screen.dart` | **PARTIAL / DEMO ONLY** | Contains a grid of 6 one-click demo login buttons at the bottom. While helpful for hackathon demos, it bypasses standard authenticated credential flows. Missing "Remember Me", session expiration warning, and explicit password visibility toggle. |
| `register_screen.dart` | **PARTIAL** | Hardcoded district list in dropdown. No dynamic validation for official government domain emails or university roll numbers. |
| `otp_screen.dart` | **PARTIAL** | Fixed 6-digit input without paste support, auto-focus progression across digits, or countdown timer for resend OTP. |
| `forgot_password_screen.dart` | **COMPLETE** | Functional with backend `/auth/forgot-password` and `/auth/reset-password`. Needs clearer inline password policy feedback. |
| `university_selection_screen.dart` | **COMPLETE** | Fetches universities from API. Needs search filter debouncing for larger institutional directories. |
| `university_role_selection_screen.dart` | **COMPLETE** | Accurately branches between Student, Faculty Mentor, and University Dean roles. |
| `profile_screen.dart` | **PARTIAL** | Static user details view. Lacks profile editing, KYC document upload, and notification preference controls. |
| `notifications_screen.dart` | **PARTIAL** | Flat list without categorization tabs (All, Projects, Challenges, Approvals). Lacks deep-linking navigation on tap. |
| `onboarding_screen.dart` | **COMPLETE** | Explains the portal value proposition across 3 slides. |

---

### 2. Citizen Experience (`frontend/lib/screens/citizen/`)

| Screen | Classification | Identified Issues & Gaps |
| :--- | :--- | :--- |
| `citizen_dashboard.dart` | **PARTIAL** | Computes status counts client-side by filtering `getMyChallenges()`. Needs backend-provided KPI summary. Quick action buttons need offline draft indicator. |
| `report_challenge_screen.dart` | **PARTIAL** | Stepper-like layout, but lacks true multi-step validation wizard (Problem ➔ Location ➔ Evidence ➔ Beneficiaries ➔ Review). Media picker lacks progress bar and upload cancellation. |
| `my_challenges_screen.dart` | **COMPLETE** | Lists user challenges with StatusBadge. Lacks search and status chip filters. |
| `nearby_challenges_screen.dart` | **PARTIAL** | Queries challenges by district, but lacks interactive map clustering or geolocation distance calculation. |
| `challenge_details_screen.dart` | **PARTIAL** | Excellent visual display of status, tier, and AI recommendations. Missing: side-by-side duplicate comparison view and citizen resolution feedback submission modal. |
| `track_solution_screen.dart` | **PARTIAL** | Step indicator for 10-stage lifecycle, but stages are hardcoded UI elements rather than dynamically fetched milestone progress. |
| `ai_analysis_screen.dart` | **PARTIAL** | Displays AI domain, priority, and similarity score, but lacks explainability breakdown ("Why did AI assign High Priority?"). |
| `challenge_submitted_screen.dart` | **COMPLETE** | Confirms submission and provides reference ID. |

---

### 3. Government Administration (`frontend/lib/screens/admin/`)

| Screen | Classification | Identified Issues & Gaps |
| :--- | :--- | :--- |
| `admin_dashboard.dart` | **PARTIAL** | Displays state-wide KPIs and tier breakdown. Lacks pending review queue badge count and direct links to audit logs and verification records. |
| `challenge_management_screen.dart` | **PARTIAL** | Allows "Validate" and "Assign University". Missing: "Reject with Reason", "Request More Info", "Mark Duplicate", and Tab filters (Pending, Under Review, Validated, Assigned). |
| `analytics_screen.dart` | **COMPLETE** | Visual breakdown by category, district, and priority using custom bar and progress indicators. |
| `impact_dashboard_screen.dart` | **PARTIAL** | Fetches `/admin/impact` metrics, but lacks baseline vs actual comparison charts and field verification evidence viewer. |
| `jharkhand_map_screen.dart` | **COMPLETE** | Interactive map of 24 Jharkhand districts with color-coded challenge density. |

---

### 4. University & Project Management (`frontend/lib/screens/university/`)

| Screen | Classification | Identified Issues & Gaps |
| :--- | :--- | :--- |
| `university_dashboard.dart` | **PARTIAL** | Shows active projects and assigned challenges. Missing: research laboratory capabilities and department workload indicators. |
| `challenge_discovery_screen.dart` | **PARTIAL** | Shows available challenges. "Adopt" button creates an initial project, but lacks multi-disciplinary team builder before adoption. |
| `create_project_screen.dart` | **COMPLETE** | Form for student leads, faculty guide, and budget. Needs milestone weighting constraint (`sum = 100%`). |
| `project_dashboard_screen.dart` | **PARTIAL** | 4 tabs (Overview, Milestones, Team, Industry). Needs 6 tabs: Overview, Milestones, Deliverables & Evidence, Team, Funding, and Verification Audit. |

---

### 5. Faculty & Student Screens (`frontend/lib/screens/faculty/` & `student/`)

| Screen | Classification | Identified Issues & Gaps |
| :--- | :--- | :--- |
| `faculty_dashboard.dart` | **PARTIAL** | Review queue for milestones. Clicking "Approve" triggers API call, but lacks deliverable file preview and revision request dialog. |
| `student_dashboard.dart` | **PARTIAL** | Kanban task board. Missing: task creation, file attachment uploader, and field testing evidence submission. |

---

### 6. Industry Screens (`frontend/lib/screens/industry/`)

| Screen | Classification | Identified Issues & Gaps |
| :--- | :--- | :--- |
| `industry_dashboard.dart` | **PARTIAL** | Displays CSR statistics and collaboration requests. Needs formal sponsorship agreement and disbursement tracking. |
| `browse_projects_screen.dart` | **COMPLETE** | Filterable project list with "Offer Funding / Mentorship" dialog. |

---

## Cross-Cutting Frontend Deficiencies
1. **Design System**: Colors and typography are defined in `theme.dart`, but lack standard design tokens for spacing, elevation, semantic input states, and accessible contrast ratios.
2. **Missing Core Widgets**: Missing `AppButton`, `AppTextField`, `ConfirmDialog`, `MediaPreview`, `FileUploader`, `PaginationControls`, and `RoleGuard`.
3. **Hardcoded Strings**: Strings are directly in widget code without `l10n` localization keys (English/Hindi).
4. **Error & Empty States**: Many screens show generic `Center(child: Text('Error'))` or silent `catch (_)` blocks on network failure.
5. **Responsive Layouts**: Screens are optimized for mobile viewports; larger tablet and desktop web layouts show stretched cards without max-width constraints.
