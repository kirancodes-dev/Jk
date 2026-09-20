# 🧠 AI Governance, Explainability & Decision Support
**Jharkhand Societal Innovation & Collaboration Platform**  
*Government of Jharkhand — Department of Higher & Technical Education*  
*SIH 2026 — Problem Statement 26043*

---

## 1. Principles of AI Governance
The platform adheres to the **National Strategy for Artificial Intelligence (NITI Aayog)** principles:
1. **Explainability**: Every classification, priority score, and match percentage includes human-readable factor rationales.
2. **Human-in-the-Loop**: AI outputs are recommendations. Official triage, duplicate confirmation, and assignment decisions require explicit human approval.
3. **Auditability**: All model predictions, input signals, confidence scores, and subsequent human overrides are persisted with timestamps.
4. **Fairness across Districts**: Algorithmic weighting ensures tribal and remote blocks receive equitable priority scoring based on health severity and affected population.

---

## 2. Model Pipeline Architecture

```
[Citizen Submission]
       │
       ▼ (Asynchronous Background Task)
[Text Normalization & NLP Screening]
       │
       ├─────────────────────────┬─────────────────────────┬─────────────────────────┐
       ▼                         ▼                         ▼                         ▼
[Domain Classification]  [Priority Calculation]   [Duplicate Detection]   [University Capability Match]
Confidence & Keywords     Weighted 4-Factor Formula   Multi-Signal Distance   R&D Alignment Score
       │                         │                         │                         │
       └─────────────────────────┼─────────────────────────┴─────────────────────────┘
                                 ▼
                    [AI Analysis Record Stored]
                                 │
                                 ▼ (Notification Dispatched)
                [Government Review Queue Triage]
                   - Side-by-side Duplicate Compare
                   - Human Override Controls
```

---

## 3. Explainability Specifications

### 3.1 Domain Classification
- **Supported Domains**: Water & Sanitation, Infrastructure, Agriculture, Healthcare, Energy, Education, Waste Management, Livelihood.
- **Explainability Output**:
  - `Confidence`: Percentage (e.g., `92%`).
  - `Rationale`: Extracted keyword clusters (e.g., `["fluoride contamination", "borehole pump", "turbidity"]`).

### 3.2 Multi-Factor Priority Formula
Priority is calculated using a transparent weighted multi-factor formula:
$$\text{Priority Score} = 0.35 \times P_{\text{pop}} + 0.30 \times S_{\text{sev}} + 0.20 \times U_{\text{urg}} + 0.15 \times H_{\text{health}}$$

Where:
- $P_{\text{pop}}$: Normalized affected citizen count ($\le 500 \to 0.2$, $500\text{--}2000 \to 0.5$, $>2000 \to 1.0$).
- $S_{\text{sev}}$: Keyword-derived socio-economic severity.
- $U_{\text{urg}}$: Reporter indicated urgency level.
- $H_{\text{health}}$: Public health impact multiplier.

### 3.3 Duplicate Detection Signals
Rather than a binary boolean flag, duplicate analysis outputs multi-dimensional similarity vectors:
- **Text Cosine Similarity**: TF-IDF similarity on title and description.
- **Geographic Proximity**: Haversine distance between geotagged coordinates ($< 5\text{ km}$ elevates score).
- **Temporal Proximity**: Time delta between submissions.
- **Category Overlap**: Domain agreement.
- **Human Decision**: Government administrators select `[Confirm Duplicate]` or `[Keep Separate]`.

### 3.4 University Capability Matching
Institutions are ranked based on:
1. **Department Specialization**: Direct faculty alignment (e.g., Environmental Engineering for Water challenges).
2. **Laboratory Accreditation**: NABL or central testing lab availability.
3. **Faculty Track Record**: Published patents or past state projects in the domain.
4. **Geographic Proximity**: Distance from the challenge district.

---

## 4. Human Override & Auditability
When a government official modifies an AI recommendation (e.g., changing domain, adjusting priority score, or re-routing university):
- `human_override` flag is set to `true`.
- `override_reason` is mandatory.
- An immutable `AuditLog` entry is generated.
- These override signals are saved for periodic model fine-tuning.
