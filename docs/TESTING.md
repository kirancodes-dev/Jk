# 🧪 Automated Testing Strategy & Test Execution Guide
**Jharkhand Societal Innovation & Collaboration Platform**  
*Government of Jharkhand — Department of Higher & Technical Education*  
*SIH 2026 — Problem Statement 26043*

---

## 1. Test Architecture Overview

The platform maintains a two-tiered automated testing strategy:
1. **Backend Integration & Security Suite (pytest)**:
   - 25 automated tests covering authentication, authorization, IDOR protection, state machine enforcement, pagination, async AI tasks, and complete end-to-end lifecycle simulation.
2. **Frontend Widget & Smoke Test Suite (flutter test)**:
   - 4 tests validating the sovereign design system, role guards, account picker, and university sub-role dispatching.

---

## 2. Test Execution Commands

### 2.1 Backend Tests
```bash
# Navigate to repository root
cd /Users/kiranbiradar/JK

# Run complete pytest suite
PYTHONPATH=. backend/.venv/bin/pytest tests/ -v

# Run only the end-to-end integration test
PYTHONPATH=. backend/.venv/bin/pytest tests/test_end_to_end_lifecycle.py -v

# Run with code coverage
PYTHONPATH=. backend/.venv/bin/pytest --cov=backend/app tests/
```

### 2.2 Frontend Widget Tests
```bash
cd /Users/kiranbiradar/JK/frontend
DEVELOPER_DIR=/Library/Developer/CommandLineTools flutter test
```

---

## 3. Backend Test Suite Breakdown

| Test File | Test Count | Key Areas Covered |
| :--- | :--- | :--- |
| **`tests/test_end_to_end_lifecycle.py`** | 1 | Complete 10-stage simulation: Citizen submit ➔ AI analyze ➔ Govt triage & allocate ➔ University adopt ➔ Student submit ➔ Faculty approve ➔ Industry sponsor ➔ Govt field verify ➔ Citizen feedback ➔ Audit check |
| **`tests/test_production_upgrade.py`** | 10 | Refresh token rotation, logout revocation, IDOR mitigation on student/faculty routes, unauthenticated upload blocking, pagination headers, async AI background tasks, demo mode 403 gating |
| **`tests/test_backend.py`** | 7 | Demo accounts listing, citizen login, admin dashboard analytics, Jharkhand 24-district heatmap data, AI text screening, challenge reporting flow |
| **`tests/test_university_role_auth.py`** | 7 | University 3-tier sub-role login (Student, Faculty, Dean), token scoping, role permission asserts |
| **Total** | **25 Passed** | **100% Pass Rate in ~70 seconds** |

---

## 4. Continuous Integration (CI/CD)
The entire test suite is automatically executed on every pull request and push to `main` via GitHub Actions (`.github/workflows/ci.yml`). Merges are blocked if any test fails.
