# Incident Response & Security Operations Runbook

**System**: SIH 26043 — Government of Jharkhand Societal Innovation Collaboration Portal  
**Department**: Higher & Technical Education, Government of Jharkhand  

---

## 1. Incident Severity Levels

| Severity | Definition | Target Response Time | Actions |
| :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Data breach, unauthorized privilege escalation, full portal outage | < 15 minutes | Freeze ingress, convene emergency call, notify CERT-In / State DPO within 6 hours |
| **SEV-2 (Major)** | Core workflow outage (submissions or evaluations down), DB failover degraded | < 30 minutes | Incident commander assigned, failover to secondary or rolling rollback |
| **SEV-3 (Moderate)** | Non-blocking service failure (e.g. email delivery delayed, AI analysis falling back) | < 2 hours | Fallback worker diagnostics, inspect dead-letter queue, provider retry |
| **SEV-4 (Minor)** | Minor UI cosmetic glitch, single non-critical log alert | Next business day | Regular ticket backlog |

---

## 2. Security Breach / Credential Compromise Response

1. **Containment**:
   - Isolate affected user accounts:
     ```sql
     UPDATE users SET is_active = FALSE WHERE id = :compromised_id;
     ```
   - Invalidate active JWT sessions via token revocation table.
   - If admin account compromised, rotate `SECRET_KEY` immediately.
2. **Evidence Preservation**:
   - Query `audit_logs` for all actions performed by `actor_id`:
     ```sql
     SELECT * FROM audit_logs WHERE actor_id = :compromised_id ORDER BY timestamp DESC;
     ```
   - Export immutable JSON dump of log evidence.
3. **Malware / Quarantined Upload Incident**:
   - If an infected file triggers EICAR or malware detection:
     - Check `storage_key` and confirm attachment remains in `quarantine/` with `scan_status = 'INFECTED'`.
     - Confirm physical object is barred from `active/` and downloads.
     - Review uploader IP via `TrustedProxyHelper` logs.
4. **Post-Mortem**:
   - Complete Post-Incident Analysis (Root Cause Analysis, Timeline, Corrective Actions) within 48 hours.
