# AI Governance, Explainability & Auditability (SIH26043)

Government of Jharkhand — Department of Higher & Technical Education

---

## 1. Governance Principles
In compliance with Government of India and Jharkhand State AI Ethics guidelines, automated decision-making on societal challenges must remain:
1. **Explainable**: Every priority score, category classification, and university recommendation must produce an inspectable rationale.
2. **Auditable**: Model name, version, timestamp, and confidence scores are stored in `ai_analysis` alongside the challenge record.
3. **Overridable**: AI suggestions are advisory. Government administrators and academic coordinators retain full authority to override classifications or priority levels, with overrides logged in `audit_logs`.

---

## 2. Modular Architecture
The AI engine is organized into four independent, decoupled micro-services:

| Service | Responsibility | Algorithmic Basis | Fallback |
| :--- | :--- | :--- | :--- |
| `AIClassificationService` | Domain & Category tagging | Keyword semantic matching across 8 official domains | Default domain with low confidence score |
| `AIDeduplicationService` | Duplicate challenge identification | Multi-factor: text Jaccard similarity + Haversine geographic proximity | Distance <= 5km and similarity >= 0.45 flagged as candidate duplicate |
| `AIPriorityService` | Emergency & severity scoring | Multi-criteria formula: severity + urgency + affected population size | Base priority MEDIUM |
| `AIUniversityMatchingService` | Academic matching & routing | Department alignment + research lab capabilities + geographic proximity | All accredited state universities listed |

---

## 3. Human Override Protocol
When an administrator modifies an AI-assigned category or priority:
1. The original AI output remains immutable in `ai_analysis`.
2. The manual update is applied to `challenges` with `moderated_by`, `moderation_reason`, and `moderated_at` populated.
3. An immutable entry is written to `audit_logs` capturing the previous vs new value and reason.
