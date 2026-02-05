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
8. [Deployment & Operations](#deployment--operations)
9. [User Guides](#user-guides)

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
    *   `ingest_excel.py`: CLI tool to load Questions/Answers from Excel (v6.1 structure).

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

## Deployment & Operations

### Ingestion
The `ingest_excel.py` script loads the static question bank.
```bash
# Full reset of question bank
TRUNCATE_BANK=1 python ingest_excel.py
```

### Deployment Checklist
1.  **Backup:** `pg_dump -h localhost -U postgres -d irmmf_db > backup.sql`
2.  **Ingest:** Run `ingest_excel.py` with `v10` Consolidated Excel.
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
