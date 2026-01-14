# IRMMF Methodology Paper — Section 4: Intake & Profiling

> **Placement:** Insert this as **new Section 4** in IRMMF_Ultimate_v5_Methodology_Paper. Renumber current Section 4 (Assessment Design) to Section 5, and subsequent sections accordingly.

---

## 4. Intake & Profiling

Before deploying role-based assessment packs, IRMMF conducts a structured intake process to capture organizational context. This intake serves three purposes: (1) segmenting organizations into benchmark cohorts for future comparison, (2) determining appropriate assessment depth, and (3) configuring pack assignments based on respondent availability.

### 4.1 Intake Scope

The intake questionnaire comprises 55 questions across seven sections:

| Section | Focus | Primary Use |
|---------|-------|-------------|
| Organization Identity | Firmographics, industry, ownership, geography | Benchmark cohort assignment |
| Scale & Complexity | Employees, revenue, countries, business units, IT estate | Depth determination, benchmarking |
| Workforce Profile | Remote work, contractors, privileged users, high-risk roles, turnover | Risk indicators, benchmarking |
| Regulatory Context | NIS2, DORA, critical infrastructure, works councils, data protection | Depth determination, evidence policy overlay |
| Risk Profile | Crown jewels, incident history, threat exposure, upcoming events | Depth determination, priority weighting |
| Current Program State | Existing program maturity, tools, prior assessments | Baseline context, benchmarking |
| Assessment Configuration | Purpose, time, budget, role availability | Operational configuration |

The intake is completed once per assessment, typically by the engagement sponsor or project lead, before pack distribution.

### 4.2 Depth Determination

Assessment depth (Lightweight, Standard, or Deep) is computed from eight weighted factors derived from intake responses:

| Factor | Weight | Indicators |
|--------|--------|------------|
| Organizational Size | 20% | Employee count, revenue band |
| Risk Profile | 20% | Crown jewels present, incident history, active concerns, upcoming high-risk events |
| Operational Complexity | 15% | Geographic footprint, business unit count, IT system complexity |
| Regulatory Burden | 15% | NIS2 entity type, DORA scope, critical infrastructure designation |
| Technical Sophistication | 10% | Cloud adoption, UEBA/DLP deployment |
| Assessment Purpose | 10% | Baseline vs. periodic review vs. post-incident/audit |
| Time Availability | 5% | Calendar time for completion |
| Resource Constraints | 5% | Budget limitations |

Each factor is scored 0 (Lightweight threshold), 1 (Standard threshold), or 2 (Deep threshold) based on response matching. The weighted sum determines the recommendation:

- **Weighted Score < 0.7** → Lightweight mode (Tier 1 questions only)
- **Weighted Score 0.7–1.3** → Standard mode (Tiers 1–3)
- **Weighted Score > 1.3** → Deep mode (Tiers 1–4, including evidence sampling)

Two constraints apply regardless of computed score:

1. If fewer than three roles are available, assessment is capped at Standard mode
2. If fewer than two roles are available, assessment is capped at Lightweight mode

A manual override allows the sponsor to select a different depth with documented rationale.

### 4.3 Benchmark Cohort Assignment

Organizations are tagged for future benchmark comparison using a two-tier system:

**Primary Cohort** combines industry classification (NACE code groupings) with size band:

- Industry groups: Financial Services, Healthcare, Technology, Manufacturing, Energy/Utilities, Government/Public, Other
- Size bands: SME (<250 employees), Mid-Market (250–4,999), Enterprise (5,000+)

Example: *Financial Services × Mid-Market*

**Secondary Tags** enable refined comparison across:

- Geography (EU-Primary, UK-Primary, North America, Global)
- Regulatory status (NIS2-Essential, NIS2-Important, DORA-Inscope, Critical-Infrastructure, Public-Company)
- Risk profile (High-IP, High-PII, Incident-History, High-Turnover)
- Workforce characteristics (High-Remote, High-Contractor)
- Program maturity (No-Program, Early-Stage, Established)

Benchmark outputs become actionable once cohort populations reach statistical significance (target: 50+ assessments per primary cohort).

### 4.4 Regulatory Overlay

For organizations operating under stringent regulatory regimes, the intake triggers an **evidence policy overlay** that modifies scoring parameters:

| Trigger Condition | Overlay Applied | Effect |
|-------------------|-----------------|--------|
| NIS2 Essential Entity | EU_STRICT | LEG_STRICT evidence policy applied to all L-axis questions; Tier A evidence cap reduced to 1 |
| DORA In-Scope | EU_STRICT | Same as above |
| Works Council Present | EU_STRICT | Same as above; Legal pack flagged as mandatory |
| Critical Infrastructure | EU_STRICT | Same as above; R-axis evidence requirements elevated |

The overlay ensures that organizations subject to European employment and privacy law are assessed against appropriately rigorous evidence standards, reflecting the legal defensibility requirements for monitoring programs in these contexts.

### 4.5 Risk Priority Weighting

When intake responses indicate elevated risk conditions, the scoring engine applies a criticality weight multiplier:

**Risk Priority Flag** is set TRUE when any of the following conditions are present:
- Material insider incident in past 3 years (S5-Q02)
- Current insider threat concerns (S5-Q03)
- Upcoming high-risk events: layoffs, M&A, restructuring (S5-Q05)

When the flag is active:
- Criticality Weight (CW) for Visibility (V) axis questions is multiplied by 1.2
- Criticality Weight (CW) for Resilience (R) axis questions is multiplied by 1.2

This ensures that targeting and response capabilities receive elevated attention when the organization faces heightened insider risk exposure.

### 4.6 Pack Assignment

Role availability questions (S7-Q04 through S7-Q10) determine which assessment packs are deployed. Each pack maps to a target respondent role:

| Pack | Target Role | Minimum Viable |
|------|-------------|----------------|
| Executive | Board member, C-suite sponsor | Required |
| Security | CISO, Security Director, SOC Lead | Required (or HR) |
| HR | CHRO, HR Director, Employee Relations | Required (or Security) |
| Legal | General Counsel, DPO, Privacy Lead | Required |
| IT/IAM | CIO, IT Director, IAM Lead | Standard+ depth |
| Data/Business | Data Owner, Business Unit Lead | Standard+ depth |
| Risk/Audit | CRO, Head of Internal Audit | Deep depth only |

**Minimum viable assessment** requires: Executive + Legal + (Security OR HR) = 3 packs

When a target role is unavailable internally, proxy respondents may be designated per the role equivalency mapping (see Section 5.3). Proxy assignments adjust role weights and are reflected in Confidence Index calculations.

### 4.7 Integration with Assessment Engine

Intake outputs feed directly into the assessment configuration:

| Intake Output | Engine Input | Effect |
|---------------|--------------|--------|
| Depth Mode | Question tier filtering | Determines which questions are presented |
| Active Packs | Pack filtering | Determines which packs are deployed |
| Role Coverage | CI calculation | Contributes to Confidence Index (weight: 0.3) |
| Regulatory Overlay | Evidence policy selection | Modifies evidence caps and requirements |
| Risk Priority Flag | CW multiplier | Elevates criticality for V/R axis questions |
| Benchmark Tags | Assessment metadata | Stored for future cohort analysis |

The intake must be completed and validated before pack distribution. Validation confirms minimum required questions are answered and minimum viable pack assignment is achieved.

### 4.8 Intake Data Retention

Intake responses are retained as part of the assessment record and contribute to:

- Assessment configuration (immediate use)
- Organization profile (multi-assessment tracking)
- Benchmark database (anonymized, aggregated)
- Trend analysis (longitudinal comparison for repeat assessments)

For GDPR compliance, organization-identifiable intake data follows the same retention and deletion policies as assessment responses. Benchmark contributions are anonymized and aggregated, removing direct organizational identifiers while preserving cohort tags.

---

## Document Update Instructions

### Step 1: Insert Section 4

Copy the content above as new **Section 4: Intake & Profiling** in the methodology paper.

### Step 2: Renumber Subsequent Sections

| Current Section | New Section Number |
|-----------------|-------------------|
| 4. Assessment Design | 5. Assessment Design |
| 5. Evidence & Verification Model | 6. Evidence & Verification Model |
| 6. Scoring Engine and Algorithms | 7. Scoring Engine and Algorithms |
| 7. Outputs and Reporting | 8. Outputs and Reporting |
| 8. Moderation, Governance and Versioning | 9. Moderation, Governance and Versioning |
| Annex A | Annex A (unchanged) |
| Annex B | Annex B (unchanged) |
| Annex C | Annex C (unchanged) |
| Annex D | Annex D (unchanged) |

### Step 3: Update Table of Contents

Add entry for Section 4 and update all subsequent section numbers.

### Step 4: Update Cross-References

Search for references to "Section 4", "Section 5", etc. and increment by 1. Key locations:

- Executive Summary references to assessment design
- Section 2.2 references to headline metrics calculation
- Annex B references to scoring specification
- Annex D worked example references

### Step 5: Add to Annex C

Extend Annex C (Evidence Policy Matrix and Role Equivalency Tables) to include:

**C4. Depth Determination Thresholds**

| Factor | Lightweight (0) | Standard (1) | Deep (2) |
|--------|-----------------|--------------|----------|
| Size | SME (<250) | Mid-Market (250-4999) | Enterprise (5000+) |
| Complexity | Single country, <3 BUs | Multi-country or 3-10 BUs | >10 countries or >10 BUs |
| Risk | Low exposure, no incidents | Medium exposure or past incidents | High exposure, active concerns |
| Regulatory | No special regulations | Some sector regulation | NIS2 Essential, DORA, Critical Infrastructure |
| Tech | Basic IT, <50% cloud | Modern IT, cloud-first | Complex hybrid, UEBA/DLP deployed |
| Purpose | Baseline/awareness | Periodic review | Post-incident, audit, M&A |
| Time | <1 week | 1-4 weeks | >4 weeks |
| Resources | Minimal | Moderate | Significant+ |

**C5. Benchmark Cohort Definitions**

| Cohort Type | Values | Derivation |
|-------------|--------|------------|
| Industry | Financial Services, Healthcare, Technology, Manufacturing, Energy/Utilities, Government/Public, Other | NACE code grouping |
| Size | SME, Mid-Market, Enterprise | Employee band |
| Geography | EU-Primary, UK-Primary, North America, APAC, Global | Operating regions |
| Regulatory | NIS2-Essential, NIS2-Important, DORA-Inscope, Critical-Infrastructure | Regulatory context responses |

### Step 6: Update Document Control

In the Document Control table at the beginning:

| Field | Update |
|-------|--------|
| Version | Increment to 5.2 |
| Change summary | Add: "Adds Section 4 (Intake & Profiling) covering organization profiling, benchmark cohort assignment, depth determination logic, and assessment configuration." |
