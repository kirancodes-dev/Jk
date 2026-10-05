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
Confidence & Signals      Weighted 5-Factor Formula   Multi-Signal Distance   R&D Alignment Score
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

### 3.1 Domain Classification (`JHARKHAND_TAXONOMY_CLASSIFIER_V3`, v3.0.0)
Code: `backend/app/services/ai/classification_service.py`. Deterministic and rule-based; no data leaves the server.

**Domains (11):** Water Resources, Agriculture, Healthcare, Education, Sanitation, Environment, Energy, Urban Infrastructure, Rural Livelihoods, Accessibility, Public Administration.

**How a prediction is made**
1. Title and description are matched against a weighted lexicon of ~990 English, Hinglish (`pani`, `nali`, `bijli`, `rojgar`, `aspatal`, `sadak`) and Devanagari terms. Each term is an *anchor* (3.0), *strong* (2.0) or *supporting* (1.0) signal. Matching respects word boundaries (`lac` never fires inside `black`), and a matched phrase hides the shorter terms inside it (`septic tank` counts for Sanitation, not `tank` for Water).
2. Title matches count 1.5×; each term counts once per field. A citizen-selected category adds 4.0 to that domain.
3. **Topic negation** ("not a road problem", "bijli ki samasya nahi") zeroes the negated term. **Absences are not negation**: "no doctor", "not a single teacher" and "without electricity" keep their signal, because that is how citizens describe problems.
4. If the runner-up is within 0.5 points, title evidence, then anchor count, then the earliest mention decide.
5. **Confidence** = `0.30 + 0.66 × (0.5 × evidence + 0.5 × margin/top_score)`, where `evidence = 1 − e^(−top_score/4)`; capped at 0.96.
6. Optional: with `AI_EMBEDDINGS_ENABLED=true` and `sentence-transformers` installed, keyword scores are blended 0.6/0.4 with embedding similarity to a description of each domain. Without the model the classifier silently stays keywords-only (the default).

**Every prediction returns** the domain, confidence, `matched_keywords`, `matched_signals` (term, domain, weight, title/description, negated), per-domain scores, the runner-up domain and the margin. These are stored in `AIAnalysis.features_json` for audit.

**Human review.** `requires_human_review` is set for every `Unclassified` result and every prediction with confidence below **0.70**. The threshold is the smallest value at which auto-accepted DEV predictions were at least 98% accurate (`python scripts/ai_accuracy_benchmark.py --calibrate`). On the held-out TEST set, 17 of 198 reports (8.6%) were flagged; flagged predictions were right 52.9% of the time, against 93.4% for auto-accepted ones.

#### Evaluation protocol
| Split | Size | Source | Used for |
|---|---:|---|---|
| TRAIN | 330 | `scripts/ai_eval/train_dev.jsonl` | building and debugging the lexicon |
| DEV | 110 | same file, every 4th report per domain | keep/drop decisions, review threshold |
| TEST | 198 | `scripts/ai_accuracy_benchmark.py` (frozen since commit `cc2bbfc`) | the reported figure only |

TRAIN/DEV mix formal English (209), SMS-style English (66), Hindi in Devanagari (88) and Hinglish (77), and include cross-domain and topic-negation cases. CI checks the TEST set's SHA-256 (so it cannot be edited to raise the score) and checks that no report appears in two splits.

#### Results on the held-out TEST set
Reproduce with `PYTHONPATH=. python scripts/ai_accuracy_benchmark.py` (writes `ai_accuracy_report.json`).

| Domain | DEV (n=10) | TEST (n=18) | TEST, leakage-audited |
|---|---:|---:|---:|
| Accessibility | 9/10 (90%) | 15/18 (83.3%) | 77.8% |
| Agriculture | 10/10 (100%) | 18/18 (100.0%) | 100.0% |
| Education | 10/10 (100%) | 14/18 (77.8%) | 83.3% |
| Energy | 10/10 (100%) | 16/18 (88.9%) | 88.9% |
| Environment | 10/10 (100%) | 17/18 (94.4%) | 94.4% |
| Healthcare | 10/10 (100%) | 17/18 (94.4%) | 94.4% |
| Public Administration | 10/10 (100%) | 16/18 (88.9%) | 83.3% |
| Rural Livelihoods | 9/10 (90%) | 14/18 (77.8%) | 77.8% |
| Sanitation | 9/10 (90%) | 17/18 (94.4%) | 94.4% |
| Urban Infrastructure | 10/10 (100%) | 17/18 (94.4%) | 94.4% |
| Water Resources | 10/10 (100%) | 17/18 (94.4%) | 94.4% |
| **Overall** | **107/110 (97.3%)** | **178/198 (89.9%)** | **89.4%** |

Previous release (V2, commit `cc2bbfc`): 68.2% on the same TEST set.

**Ablation** (each row adds one step; decisions were taken on DEV):

| Variant | DEV | TEST |
|---|---:|---:|
| V2 keyword counter (commit `cc2bbfc`) | 63.6% | 68.2% |
| a. expanded multilingual lexicon, uniform weights | 93.6% | 89.9% |
| b. + weighted phrases and title boost | 96.4% | 89.9% |
| c. + topic-negation handling | 97.3% | 89.9% |
| d. + runner-up margin tie-break (**released**, keywords-only) | 97.3% | 89.9% |
| e. + 0.6/0.4 sentence-embedding blend (`paraphrase-multilingual-MiniLM-L12-v2`) | 97.3% | 88.4% |

The whole TEST gain comes from the lexicon and word-boundary matching (step a). Steps b and c helped on DEV but did not change TEST accuracy. The tie-break changes nothing on either split; it is kept so near-ties are resolved deterministically and explainably (margins above 1.0 lowered DEV accuracy). The embedding blend did not help on DEV and was slightly worse on TEST, so it stays off by default.

#### Honest caveats
- **The TEST set is not fully blind.** The developer read the 198 TEST reports before writing TRAIN/DEV and the lexicon. To bound the effect, the benchmark re-runs TEST with every lexicon term removed that fires only on TEST reports and was not in V2's taxonomy (50 terms, listed in `ai_accuracy_report.json` → `leakage_audit`). Accuracy drops from 89.9% to 89.4%, and every domain stays at or above 77.8%.
- **DEV is optimistic.** The same person wrote DEV and the lexicon, so DEV (97.3%) overstates real-world accuracy; TEST is the figure to quote.
- **All three sets are synthetic.** The next step is a blind evaluation on real, anonymised citizen submissions labelled by district officers.
- **Known gaps** (seen on TEST and deliberately *not* patched, to keep TEST held out): Hinglish spelling variants outside the lexicon (`kaarigaro` vs `karigar`) fall to `Unclassified`; reports that genuinely span two departments (blackouts during exams, a disability pension, livestock-based SHGs) split between the two. Fuzzy transliteration matching is the planned fix.

CI gate: `tests/test_ai_classifier_v3.py` fails if TEST accuracy drops below 87.9% (the 89.9% baseline minus 2 points), if any domain falls below 65%, or if DEV drops more than 2 points.

### 3.2 Multi-Factor Priority Formula
Code: `backend/app/services/ai/priority_service.py` (default weights `v2026.1-DEFAULT`; an administrator can activate a different weight set, which is versioned and audited).

$$\text{Priority} = 0.30\,S_{\text{severity}} + 0.20\,U_{\text{urgency}} + 0.20\,P_{\text{population}} + 0.15\,H_{\text{health\_safety}} + 0.15\,V_{\text{vulnerability}}$$

Each factor is scored 0–100:
- $S_{\text{severity}}$: keyword-derived; 95 for critical signals (e.g. death, outbreak, arsenic, collapse), 80 for high, 50 for medium, 35 otherwise.
- $U_{\text{urgency}}$: reporter's urgency: Critical 100, High 80, Medium 50, Low 25.
- $P_{\text{population}}$: affected people: ≥5,000 → 100; ≥1,000 → 80; ≥200 → 60; ≥50 → 40; otherwise 20.
- $H_{\text{health\_safety}}$: `min(100, 30 + 25 × health/safety signals)`.
- $V_{\text{vulnerability}}$: 85 for an aspirational district, otherwise 50.

The composite is clamped to 10–100. **CRITICAL** if ≥ 78 or severity ≥ 95; **HIGH** if ≥ 60 or severity ≥ 80; **MEDIUM** if ≥ 35; otherwise **LOW**.

### 3.3 Duplicate Detection Signals
Code: `backend/app/services/ai/deduplication_service.py`. Candidates are reports from the last 180 days.

$$\text{Duplicate score} = 0.50\,\text{text} + 0.25\,\text{geo} + 0.15\,\text{category} + 0.10\,\text{temporal}$$

- **Text**: bag-of-words cosine similarity of title + description (multilingual embedding similarity instead, only when the optional model is enabled).
- **Geo**: same block 1.0, same district 0.7, different district 0.3.
- **Category**: 1.0 if the categories match, else 0.
- **Temporal**: `1 − days_ago / 180`.
- A score ≥ **0.65** marks a likely duplicate. An officer then chooses `[Confirm Duplicate]` or `[Keep Separate]`; nothing is merged automatically.

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
- Classifier predictions below the 0.70 confidence threshold (and every `Unclassified` result) carry `requires_human_review = true` on the stored `AIAnalysis`.
