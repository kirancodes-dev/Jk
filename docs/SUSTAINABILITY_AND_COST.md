# Sustainability and Cost

**Cost figures below are planning estimates, not vendor quotes.** Totals are the team's budget envelope; the line items show one way to allocate it, with every assumption stated so a department can replace it with real State Data Centre (SDC), SMS and audit quotes. Figures marked *measured* come from scripts in this repository.

## At a glance

| | Amount | Notes |
|---|---:|---|
| One-time cost | **₹9,00,000** | ≈ ₹37,500 per district across 24 districts |
| Infrastructure per year | **under ₹65,000** | runs on the existing Jharkhand SDC; no new hardware |
| Upkeep per year | **₹3–5 lakh** | maintenance, annual security audit, translation review |
| Running cost per reported challenge | **≈ ₹24** | (₹62,000 + ₹4.1 lakh) ÷ 20,000 challenges a year |

## 1. Planning assumptions

| Assumption | Value | Basis |
|---|---:|---|
| Districts | 24 | all of Jharkhand |
| Registered users | 50,000 citizens + 5,000 officials, PRI members, faculty and industry users | planning figure |
| Challenges reported per year | 20,000 | ≈ 2.3 per district per day |
| Photos per challenge | 3 | planning figure |
| Stored size per photo | **0.54 MB** *(measured)* | upload pipeline on 7 real 3,500–6,000 px photos of a Jharkhand village: 4.08 MB → 0.54 MB average (`scripts/image_storage_benchmark.py --photos …`) |
| Database growth per challenge | 10 KB budgeted (**1.9 KB measured**) | the challenge, location, AI analysis and status history took 2.34 MB for 1,215 seeded challenges; budget allows 5× for notifications, audit events and comments |
| API requests per challenge over its life | 200 | submitter, officer, university and industry views |
| Server capacity | **241.8 req/s, 0 failures** *(measured)* | 200 simulated users on one laptop (`docs/LOAD_TEST.md`) |

What follows from these:
- **Photo storage:** 20,000 × 3 × 0.54 MB ≈ **32 GB a year** (≈ 245 GB a year without the downscaling added in this release).
- **Database:** 20,000 × 10 KB ≈ **0.2 GB a year**.
- **Load:** 20,000 × 200 = 4 million requests a year ≈ 0.13 req/s on average, or about 2.5 req/s in a peak hour at 20× the average. The measured capacity leaves roughly 100× headroom, so one modest application VM and one database VM are enough.

## 2. One-time cost: ₹9,00,000

| Item | Basis | ₹ |
|---|---|---:|
| District onboarding and training (district officers, BDOs, PRI members) | 24 districts × ₹15,000 for a one-day workshop | 3,60,000 |
| Citizen awareness material in Hindi and the tribal languages | 24 districts × ₹5,000 (posters, QR standees, radio scripts) | 1,20,000 |
| Native-speaker review of the tribal translations | 5 languages × ₹30,000 (see `docs/TRANSLATION_REVIEW.md`) | 1,50,000 |
| Pre-launch security audit by a CERT-In empanelled auditor | one audit | 1,00,000 |
| SDC deployment, data migration and disaster-recovery set-up | about 15 person-days | 1,20,000 |
| Contingency | ≈ 5.5% | 50,000 |
| **Total** | **≈ ₹37,500 per district** | **9,00,000** |

## 3. Recurring cost

### Infrastructure: under ₹65,000 a year

| Item | Assumption | ₹ per year |
|---|---|---:|
| Compute: one application VM (4 vCPU, 8 GB) and one PostgreSQL VM (4 vCPU, 16 GB) on the SDC | taken from existing SDC capacity; this line covers a charge-back if the SDC applies one (assumed ₹2,500 a month) | 30,000 |
| Storage and backups | about 100 GB in year 1 (photos, database, three backup copies); assumed ₹2 per GB-month | 5,000 |
| SMS notifications (DLT-registered, transactional) | 20,000 challenges × 3 SMS × ₹0.25 | 15,000 |
| `gov.in` domain, TLS certificate, email relay | through NIC; no charge | 0 |
| Monitoring and logging | open-source tools on the same VMs; the app already exposes `/metrics` for Prometheus | 0 |
| Contingency | ≈ 20% | 12,000 |
| **Total** | | **62,000** |

### Upkeep: ₹3–5 lakh a year

| Item | Assumption | ₹ per year |
|---|---|---:|
| Maintenance (security patches, dependency updates, bug fixes) | half-time developer or AMC, ₹20,000–30,000 a month | 2,40,000–3,60,000 |
| Annual security audit | CERT-In empanelled auditor | 40,000–80,000 |
| Tribal-language review of new and changed strings | about ₹5,000 per language | 25,000 |
| Classifier re-check on a labelled sample of real reports | two days of a domain officer and a developer | 15,000–35,000 |
| **Total** | | **3,20,000–5,00,000** |

## 4. Funding model

| Source | Pays for | How |
|---|---|---|
| **Department of Higher & Technical Education (DHTE), Jharkhand** | The platform: the one-time cost, infrastructure and upkeep | As the nodal department for PS 26043, it budgets the platform as a state e-governance service hosted on the SDC. |
| **Corporate Social Responsibility (Companies Act 2013, Section 135)** | The solutions: prototypes, field trials and deployments of university projects | Companies that meet Section 135's thresholds must spend at least 2% of their average net profit of the previous three years on CSR. Schedule VII covers education, rural development, environmental sustainability and technology incubators in public institutions. Industry users already choose and track the projects they sponsor in the Industry dashboard; the money itself moves through each company's own CSR process. |
| **Reuse by other states** | Their own deployments | The district list, taxonomy, languages and branding are data, so another state can adopt the platform without rebuilding it. **This repository has no licence file yet.** Before offering it for reuse, the department should choose an open-source licence (the Government of India's Policy on Adoption of Open Source Software, 2015, favours open source in e-governance). |

## 5. Green practices

| Practice | Status | Evidence |
|---|---|---|
| **Paperless workflow** | in place | Reports, verification, approvals, status updates and the tamper-evident audit trail are digital; citizens are notified in the app, not by letter. |
| **Photos stored upright, without metadata, downscaled and compressed** | added in this release | `storage_service.strip_image_metadata` applies the EXIF orientation, removes all metadata (including GPS), caps the longest edge at 2,048 px and re-encodes at JPEG quality 82: **86.8% less storage** on real photos *(measured)*. |
| **Soft delete with a 30-day purge** | added in this release | Deleted attachments can be restored for 30 days; the worker then deletes the stored file hourly (`purge_expired_attachments`, migration `a1c5e9d27b40`). Before this release, soft-deleted files were never removed. |
| **Notification retention** | in place | Read notifications are archived after 90 days (`notification_service`, `retention_days=90`). |
| **No new hardware** | deployment plan | Runs on two VMs in the existing SDC; the measured capacity is about 100× the planned load. |
| **Lightweight, local AI** | in place | Domain classification takes **2.7 ms of CPU per report** on one core *(measured, 990 runs)*, with no GPU and no calls to external AI services. Sentence embeddings are optional and off by default. |
| **Efficient queries** | improved in this release | A 100-item review-queue page now takes 2 database queries instead of 102; the same machine served 70% more requests *(measured, `docs/LOAD_TEST.md`)*. |
| **Fonts bundled with the app** | added in this release | Ol Chiki and Warang Citi fonts ship with the app, so pages don't fetch fonts from third-party servers. |

## 6. What is not measured yet
- **Energy use and carbon footprint** have not been measured; the figures above (storage, CPU time per request) are proxies.
- **SDC charge-back, SMS and audit prices** are assumptions. Replace them with quotes before budgeting.
- **The free Render demo** (`DEPLOYMENT.md`) is for evaluation only; it is not the production hosting plan.
