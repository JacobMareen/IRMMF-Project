# IRMMF Project Handbook

This document consolidates all technical, operational, and user documentation for the IRMMF Project (v10 Streamlined Intake / Investigation Module MVP).

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Investigation Module](#investigation-module)
3. [Dynamic Workforce Module](#dynamic-workforce-dwf-module)
4. [PIA Module](#pia-privacy-impact-assessment-module)
5. [Insider Risk Program Module](#insider-risk-program-module)
6. [Assessment Module](#assessment-module)
7. [Technical Implementation](#technical-implementation)
8. [UX & Architecture Improvement Plan](#ux--architecture-improvement-plan)
9. [Deployment & Operations](#deployment--operations)
10. [User Guides](#user-guides)

---

## Project Overview

The IRMMF (Insider Risk Maturity Model Framework) Project is a platform for assessing and managing insider risk. It consists of two primary pillars:
1.  **Assessment Module:** Evaluates organizational maturity against the IRMMF framework.
2.  **Investigation Module:** Manages insider risk cases, inquiries, and investigations with jurisdiction-aware workflows.

---

## Investigation Module

The Investigation Module is a jurisdiction-aware case workflow for insider risk investigations.

### Key Features
*   **Case Lifecycle:** `INTAKE → LEGITIMACY_GATE → CREDENTIALING → INVESTIGATION → ADVERSARIAL_DEBATE → DECISION → CLOSURE`.
*   **Jurisdiction Engine:** Centralized rules (e.g., Belgium/Netherlands specific deadlines) configured in Tenant Settings.
*   **Gates:** Hard blocks for Legitimacy (Legal Basis), Credentialing (Conflict of Interest), and Adversarial Debate.
*   **Serious Cause:** dedicated "Serious Cause Clock" key for managing dismissal deadlines (e.g., 3-day rule in Belgium).
*   **Reporter Portal:** Anonymous two-way messaging for whistleblowers.
*   **Secure Access:** "Expert Access" grants for external counsel (48h windows).

### API Summary
*   **Cases:** `/api/v1/cases`, `/api/v1/cases/{id}`
*   **Evidence:** `/api/v1/cases/{id}/evidence` (Supports hashing)
*   **Tasks:** `/api/v1/cases/{id}/tasks` (Playbook integration)
*   **Gates:** `/api/v1/cases/{id}/gates/{type}` (legitimacy, credentialing, adversarial)
*   **Audit:** `/api/v1/audit` (Immutable logs)

See `app/modules/cases/` for implementation details.

---

## Dynamic Workforce (DWF) Module

The DWF module measures security culture and behavior across the dynamic workforce (contractors, gig workers, etc.).

### Key Features
*   **Culture Assessment:** Dedicated questions for evaluating workforce security culture.
*   **Tenant Isolation:** Supports separate assessments per tenant.

### API Summary
*   **Questions:** `/api/v1/dwf/questions/all`
*   **Assessment:** `/api/v1/dwf/assessment/register`
*   **Submission:** `/api/v1/dwf/submit`
*   **Analysis:** `/api/v1/dwf/assessment/{id}/analysis`

---

## PIA (Private Investigations Act) Module

Manages compliance with the Private Investigations Act through a structured 8-step workflow.

### Key Features
*   **8-Step Workflow:** `INTAKE → THRESHOLD → PREPARATION → ASSESSMENT → VALIDATION → REVIEW → SIGNOFF → CLOSURE`.
*   **Evidence Collection:** Upload evidence supporting compliance checks.
*   **Anonymization:** Feature to anonymize PIA cases for GDPR compliance (Right to Erasure).

### API Summary
*   **Cases:** `/api/v1/pia/cases`
*   **Workflow:** `/api/v1/pia/workflow` (List steps)
*   **Evidence:** `/api/v1/pia/cases/{id}/evidence`
*   **Anonymize:** `/api/v1/pia/cases/{id}/anonymize`

---

## Insider Risk Program Module

Manages the governance and strategy of the Insider Risk Program itself.

### Key Features
*   **Policy Management:** Edit and version the Insider Risk Policy.
*   **Control Register:** Track controls and link them to assessment recommendations.
*   **Roadmap:** Plan and track program improvements.

### API Summary
*   **Policy:** `/api/v1/insider-program/policy`
*   **Controls:** `/api/v1/insider-program/controls`
*   **Roadmap:** `/api/v1/insider-program/roadmap`

---

## Tenant & User Management Modules

Core infrastructure for multi-tenancy and RBAC.

### Tenant Module
*   **Settings:** Manage holidays, jurisdiction rules, and global configurations.
*   **Holidays:** Custom business-day calendars for deadline logic.
*   **API:** `/api/v1/tenant/settings`, `/api/v1/tenant/holidays`.

### Users Module
*   **RBAC:** Role-based access control (`ADMIN`, `HR`, `LEGAL`, `INVESTIGATOR`, etc.).
*   **Invites:** Invite new users to the tenant.
*   **API:** `/api/v1/users`, `/api/v1/users/invite`, `/api/v1/auth/login`.

---

## Assessment Module

The Assessment Module (v10) focuses on a streamlined intake process and maturity scoring.

### Intake Streamlining (v10)
*   **Reduced Friction:** Intake questions reduced from 57 to **25**.
*   **Zero Text Fields:** All inputs are now dropdowns for standardized benchmarking.
*   **Sections:**
    1.  Organization Profile
    2.  Regulatory & Compliance
    3.  Workforce Characteristics
    4.  Technology Environment
    5.  Current Program State
    6.  Assessment Context

### Multi-Select Questions
*   **Overview:** 11 questions now allow multiple selections to better reflect capability maturity.
*   **Scoring:** 0 selections = Maturity 0; 7+ = Maturity 4.
*   **Domains Covered:** Fraud Detection, Whistleblowing, Regulatory Frameworks, etc.
*   **Technical:** Stored as comma-separated strings (e.g., `"OPT1,OPT2"`) in `fact_responses`.

### Website Scraper
*   **Purpose:** Pre-fills intake data from public website analysis.
*   **Coverage:** Infers Industry, Size, Footprint, Revenue, and IT Environment (approx. 28% of intake).
*   **Logic:** Maps keywords to v10 dropdown options (e.g., "100,000 employees" -> Revenue "$50B+").

---

## Technical Implementation

### Backend Architecture
*   **Framework:** FastAPI + SQLAlchemy (Async/Sync mix) + Pydantic.
*   **Database:** PostgreSQL with `pgcrypto` extension.
*   **Structure:** Modular design (`app/modules/{module_name}`).
*   **Authentication:** RBAC with tenant isolation (`X-IRMMF-KEY`, `X-IRMMF-ROLES`).

### Frontend Architecture
*   **Framework:** React + Vite + TypeScript.
*   **Styling:** Vanilla CSS variables (Gold/Dark theme).
*   **State:** React Context + Hooks.

### Database & Configuration
*   **Settings (`app/core/settings.py`):** Centralized configuration using `pydantic-settings`. Loads from `.env`.
*   **Database (`app/db.py`):** SQLAlchemy engine and session factory.
*   **Models:**
    *   `app/modules/assessment/models.py`: Assessment domain (Question, Answer, Assessment, Response).
    *   `app/models.py`: Base class and Insider Risk Program domain (Policy, Controls).
    *   `alembic/env.py`: Migration environment (imports all modules to register metadata).
*   **Maintenance:**
    *   `ingest_excel.py`: CLI tool to load Question Bank from JSON (`app/core/irmmf_bank.json`).

### Risk Engine (`app/core/risk_engine.py`)
*   **Scoring Logic:**
    *   **Mitigation Score:** Weighted average of axis scores, curved by scenario configuration (Sigmoid, Logarithmic).
    *   **Risk Score:** `Likelihood (inverted mitigation) * Impact`.
    *   **Archetypes:**
        *   **Paper Dragon:** High friction, low trust (Controls declared but not effective).
        *   **Cyber Sovereign:** High trust, managed friction.
        *   **Resilient Optimiser:** Balanced approach.
*   **Configuration:** Scenarios loaded from `config/risk_scenarios_simple.yaml`.

### Security Architecture
*   **RBAC:** Lightweight role checks (`require_roles` dependency).
    *   Roles: `ADMIN`, `HR`, `LEGAL`, `INVESTIGATOR`, `AUDITOR`.
*   **Tenant Isolation:**
    *   `X-IRMMF-KEY` header context.
    *   `ensure_tenant_match`: Gatekeeper to prevent cross-tenant data access.
    *   `DEV_RBAC_DISABLED`: Environment flag to bypass checks in local dev.

### CLI Tools (`scripts/`)
*   `verify_investigation_module.py`: Comprehensive smoke test for case lifecycle.
*   `ingest_excel.py`: Loads question bank mechanics.
*   `dev_reset_db.py`: Destructive database reset for local dev.

### Frontend Architecture (`frontend/src/pages/`)
*   **Networking (`api/client.ts`):** Centralized `ApiClient` handles auth injection (`Authorization`, `X-IRMMF-KEY`, `X-IRMMF-ROLES`) and error parsing. Replaces global `window.fetch` patching.
*   **CaseFlow.tsx:** Monolithic controller for the investigation workflow (Evidence, Tasks, Gates).
*   **AssessmentFlow.tsx:** Maturity assessment runner with neuro-adaptive branching.
*   **CommandCenter.tsx:** Operational dashboard.
*   **Settings.tsx:** Tenant configuration (Jurisdiction rules, Holidays).

---

## UX & Architecture Improvement Plan

### Goal Description
Enhance the user friendliness and professional feel of the application while robustifying the backend architecture. This plan covers the work done to fix scoring bias and the ongoing refactoring.

### Phase 1: Core Scoring & Risk Model (Completed)
**Problem:** "0" scores for low maturity (Harmonic Mean bias).
**Solution:** Implemented Hybrid Scoring (75% Arithmetic + 25% Harmonic) in `app/core/engines.py`.
**Validation:** Verified via unit tests and UI checks.

### Phase 2: Refactoring & Stability (Completed)
**Risk Heatmap:** Extracted to `frontend/src/components/RiskHeatmap.tsx` and fixed sizing/alignment.
**Config:** Moved hardcoded paths to `app/core/settings.py`.
**Hooks:** Created `frontend/src/hooks/useAssessmentData.ts` to clean up `frontend/src/pages/AssessmentHub.tsx`.
**DevOps:** Created `dev.sh` for unified startup.

### Phase 3: Visual Dashboard (Completed)
*   `frontend/src/components/charts/CaseStatusChart.tsx`: Doughnut chart showing Open vs. Closed vs. On-Hold cases.
*   `frontend/src/components/charts/GateThroughputChart.tsx`: Bar chart showing completion rates for key gates.
*   `frontend/src/components/charts/ChartConfig.ts`: Centralized Chart.js registration.

### Phase 4: Interactive Feedback (Completed)
**Toast System:** Global toast provider for better error/success messaging.
**Integration:** Integrated `useToast` into `frontend/src/pages/AssessmentHub.tsx` for user actions.
**Theming:** Updated toast CSS to use global variables (light/dark mode support).

### Phase 5: Robustness (Completed)
**Schemas:** Verified field validators (min/max scores 0-4) in `ResponseCreate`.
**Ingestion:** Added validation for Excel column headers to prevent runtime errors.

### Phase 6: Framework Visualization (Completed)
**Goal:** Replace standard progress cards with an interactive "Risk Radar" or "Framework Shield".
**Component:** `frontend/src/components/visuals/FrameworkRadar.tsx` using SVG for radial progress segments.
**Interaction:** Hover for summary, click for detailed `frontend/src/components/visuals/DomainDetailOverlay.tsx` with capabilities.
**Education:** Added `frontend/src/components/FrameworkGuide.tsx` modal to explain the methodology (Domains + Axes).

### Phase 7: Advanced Intelligence (Executive Reporting)
**Executive Summary Generation:** Implement an AI-driven report generator (using `app/modules/ai`) that consumes assessment results (`ResultsPayload`) and produces a C-level narrative.
**Content:** Auto-generate High-Level Recommendations, Key Findings, and Business Impact Analysis based on maturity scores and gaps.
**Format:** Exportable PDF/HTML format designed for board presentation.
**Risk Treatment:** Interactive treatment planning module (current placeholder in Risks view).
**AI Analysis:** Free-text intake analysis (requires new `app/modules/ai` backend service).

### Phase 8: Content & Depth (Planned)
**Methodology Guide:** Expand `frontend/src/components/FrameworkGuide.tsx` into a comprehensive, readable manual.
**Capabilities Integration:** Integrate domain capability tags into Assessment Results and scoring views to provide granular context.

### Phase 9: Strategic Enhancements (Based on Industry Analysis)
**Third-Party Risk Module:** Add assessment criteria for Trusted Partners and Supply Chain (Ref: DTEX, Leidos).
**Maturity Mapper:** Map IRMMF Archetypes to industry-standard 1-5 Maturity Levels (Ad-hoc -> Optimized) for CISO reporting (Ref: CMMI, Cyberhaven).
**Socio-Technical Profiling:** Distinguish between Malicious vs Negligent risk indicators in the dashboard (Ref: Orange Cyberdefense STS Theory).
**Global Benchmarking:** Create a Scenario Benchmark view to compare scores against simulated Industry/Sector averages (Ref: Gurucul, Ponemon).
**Board-Ready Reporting:** Generate PDF Executive Summaries focusing on Business Value and ROI rather than just technical scores.

### Phase 10: Case Management Maturity (Refining Evidence & Workflow)
**Privacy-First Workflow:** Implement Anonymized by Default views for analysts, revealing PII only with Break Glass justification (Ref: DTEX, Proofpoint).
**Update:** Break-glass endpoint + UI added in Case Flow and Case list overlays; PII masking applied to subjects, evidence labels, reporter messages, legal holds, expert access, case titles/summaries, and notes. PII entry fields (subjects, evidence, legal holds, experts, notes, reporter replies) now require break-glass unlock. Audit event logged for break-glass actions.
**Investigator Audit Trail:** Log every action taken by the investigator (viewing evidence, unmasking users) to ensure watching-the-watcher compliance.
**Integrated Feedback Loop:** Right-sized response workflow (send micro-learning or nudge emails for low-risk negligence) (Ref: Code42 Instructor).
**Legal-Ready Packaging:** One-click Case Export that bundles timeline, evidence, and audit logs into a tamper-evident ZIP for HR/Legal handoff.

### Phase 11: Adaptive Methodology (The Triage Pivot)
**Rapid Benchmark (Tier 1):** Promote the 25-question Intake module to be the default starting experience.
**Unified Schema (Refactor):** Merge `IntakeQuestion` and `Question` tables. Treat Intake as Tier 0 questions to simplify DB and remove redundant tables.
**Smart Extension:** Use Gatekeeper Logic to dynamically unlock Deep Dive tiers based on Tier 0 answers.
**Score Integrity:** Tag assessment results as `CONFIDENCE_LEVEL: LOW` (Rapid) vs `CONFIDENCE_LEVEL: HIGH` (Full) to prevent apples-to-oranges benchmarking.
**Gatekeeper Logic:** Ensure Rapid answers automatically close/open downstream Deep Dive sections.
**Engagement Mechanics:** Ghost Bars (show potential score on Radar chart), incentive teasers (Unlock Domain Analysis), and extension workflow UI to invite users to unlock domains after Rapid Benchmark.

### Phase 12: UX Polish & Content Enrichment
**Info Overlays:** Standardized clickable info icons that trigger a click-outside-to-close overlay for definitions (replacing simple browser tooltips).
**Rich Archetypes:** Expand archetype definitions from bullet points to full prose with peer comparison context.
**Registration Portal:** Self-service registration flow that creates a dedicated tenant/user (removing manual SQL provisioning).

### Phase 13: Strategic Enablers (Based on Global/Belgian Analysis)
**Structural Integrity Floor:** Implement a multiplicative penalty in scoring for organizations that have policies (BaseScore) but fail execution (Axis E), preventing paper maturity.
**Evidence-Aware Assessment:** Add confidence adjusters based on micro-questions (e.g., specific MFA type, RMM tool usage) to refine scores.
**Shadow Worker Detection:** Add risk scenarios for Remote Management Tools (AnyDesk/RustDesk) and Timezone Anomalies to detect proxy workers (Ref: North Korean checks).
**Belgian Compliance Module:** CBA No. 81 alignment with tiered visibility (PII hidden by default until Break Glass procedure is logged).
**Works Council Logic:** `EvidencePolicyID: LEG_STRICT` requires DPIA/Works Council approval for high maturity scores in Domain 4.
**Signal Fusion:** Backend logic to correlate disparate signals (Auth Event + Geolocation + HID presence) into a single high-fidelity risk score.

### Verification Plan
**Rapid Mode:** Start new assessment and verify only 25 questions load.
**Engagement:** Verify Ghost Bars appear on the Radar when hovering locked domains.
**Logic Check:** Answer No to a gatekeeper and verify related deep dive questions are skipped/closed.
**Benchmarking:** Verify Rapid results do not overwrite Full benchmarks in the dashboard.
**Dashboard:** Load Command Center and verify charts render with correct data.
**Toasts:** Trigger a save/submit action and verify the animated toast appears.

---

## Deployment & Operations

### Ingestion
The `ingest_excel.py` script loads the static question bank.
```bash
# Full reset of question bank from JSON source
TRUNCATE_BANK=1 python ingest_excel.py
```

### Deployment Checklist
1.  **Backup:** `pg_dump -h localhost -U postgres -d irmmf_db > backup.sql`
2.  **Ingest:** Run `ingest_excel.py` (loads `app/core/irmmf_bank.json`).
3.  **Build Frontend:** `cd frontend && npm run build`.
4.  **Restart Backend:** `python main.py`.

### Troubleshooting
*   **"Assessment data unavailable":** DB empty. Run ingestion.
*   **Multi-select checkboxes missing:** Frontend build outdated. Rebuild.
*   **Selections not saving:** Check network tab for 500 errors (usually DB schema mismatch).

---

## User Guides

### Multi-Select Questions
*   **Identify:** Look for blue "Select all that apply" banner.
*   **Select:** Click unlimited checkboxes.
*   **Confirm:** Click "Confirm Selection" to save.
*   **Defer:** Use "Defer / Skip" to convert current selection to draft state.

> **Tip:** Select ALL capabilities that are truly implemented. Partial or planned capabilities should not be selected to ensure accurate maturity scoring.
