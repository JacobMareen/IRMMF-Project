# Investigation Module MVP Notes

Date: January 27, 2026
Owner: IRMMF Platform

## Scope & Backlog Alignment

This file tracks implementation notes for the `Investigation_Module_MVP_Backlog.xlsx`.

## Module Overview (What’s Built)

The Investigation Module is a jurisdiction-aware case workflow for insider risk investigations. It provides:
- **Case lifecycle**: create, stage transitions, status changes, audit trail.
- **Core records**: subjects, evidence register, tasks/checklists, append-only notes.
- **PIA workflow gates**: legitimacy, credentialing, adversarial debate.
- **Serious-cause clock (BE)**: deadlines, business-day calculator, escalation flags.
- **Playbooks + suggestions**: apply standard playbooks to generate tasks and evidence suggestions.
- **Reporter portal Q&A**: anonymous two-way messages tied to reporter key.
- **Document generation**: investigation mandate, interview invitation, dismissal reasons letter, silent legal hold instruction, erasure certificate.
- **Export + erasure**: export pack, erasure approval/execution, anonymization.
- **Dashboards + alerts**: operational dashboard, HR exemption drift alerts, serious-cause countdowns.
- **Notifications**: in-app notifications for serious-cause milestones (acknowledge flow).
- **Settings**: tenant settings, business-day rules, keyword flagging, notifications toggles.

## How to Use (Quick Start)

1. **Create a case**
   - Go to `Cases` and create a new case (title, summary, jurisdiction).
2. **Open the flow**
   - Click **Open Flow** to access the multi-step investigation workflow.
3. **Intake**
   - Update case context, add subjects, optionally enable serious-cause early.
4. **Legitimacy Gate**
   - Select legal basis (dropdown), document proportionality and mandate.
5. **Credentialing Gate**
   - Confirm investigator details, licensing, conflict check.
6. **Investigation**
   - Add tasks, evidence, notes, meetings; apply playbooks and convert evidence suggestions.
7. **Adversarial Debate**
   - Record invitation + interview summary; generate invitation letter if needed.
8. **Decision**
   - Record outcome; for serious-cause cases, manage deadlines and dismissal steps.
9. **Closure**
   - Export documents, generate certificate, anonymize when appropriate.

Additional tools:
- **Command Center**: operational dashboard + alerts.
- **Notifications**: view and acknowledge serious-cause reminders.
- **Settings**: configure tenant, business-day rules, keyword flagging, notification toggles.

## Test Script (Smoke Test)

Use this script to validate the module end-to-end (case creation, gates, notifications, documents):

```
API_BASE=http://127.0.0.1:8000/api/v1 \\
TENANT_KEY=default \\
scripts/verify_investigation_module.py
```

Optional cleanup:
```
CLEANUP=1 scripts/verify_investigation_module.py
```

The script creates a test case, exercises gates and stage transitions, generates a mandate, triggers serious-cause notifications, and optionally anonymizes the case.

### Implemented (so far)
- **US1.1 Tenant setup + org configuration**
  - `GET/PUT /api/v1/tenant/settings`
  - `tenants`, `tenant_settings` tables
  - Settings UI wired in `Platform Settings`
- **US1.2 Authentication + user management (scaffolded)**
  - `POST /api/v1/auth/login` (dev mode only)
  - `GET /api/v1/users`, `POST /api/v1/users/invite`
  - `users`, `user_roles` tables
  - UI for invite + list + role update
  - UI login now calls `/api/v1/auth/login` and stores roles/token for RBAC headers.
- **US1.3 RBAC (guardrails scaffolded)**
  - `require_roles()` helper
  - RBAC enforcement disabled by default via `DEV_RBAC_DISABLED=1`
  - Role catalog expanded: `LEGAL_COUNSEL`, `EXTERNAL_EXPERT`, `AUDITOR`
- **T1.1a Tenant settings schema + migration**
  - Alembic baseline + `0002_tenant_settings_assessments` revision
  - `tenant_settings` fields for investigation mode, retention, keyword flagging, etc.
- **T1.1b Settings API + validation**
  - Tenant settings routes, validation, and model wiring
- **T1.1c Settings UI**
  - Platform Settings form with save and JSON rules editor
- **T1.4a Business-day calculator + tests**
  - `add_business_days()` service and unit tests for weekends, holidays, and cutoff hours

### Implemented (this pass)
- **US2.1 Case object + lifecycle state**
  - Tables: `cases`, `case_status_events`, `case_subjects`
  - Status values: `OPEN, ON_HOLD, CLOSED, ERASURE_PENDING, ERASED`
  - Stages: `INTAKE → LEGITIMACY_GATE → CREDENTIALING → INVESTIGATION → ADVERSARIAL_DEBATE → DECISION → CLOSURE`
  - Intake metadata updates supported via `PATCH /api/v1/cases/{case_id}`
- **US2.2 Evidence register (metadata + links)**
  - Table: `case_evidence_items`
  - API: `POST /api/v1/cases/{case_id}/evidence`
  - Evidence hash supported (`case_evidence_items.evidence_hash`) for integrity tracking
- **US2.3 Case tasks/checklists**
  - Table: `case_tasks`
  - API: `POST /api/v1/cases/{case_id}/tasks` and `GET /api/v1/cases/{case_id}/tasks`
  - UI: `Cases` page (create + list + inline subject/evidence/task capture)
- **US2.4 Notes + interview log (append-only)**
  - Table: `case_notes`
  - API: `POST/GET /api/v1/cases/{case_id}/notes`
  - UI: Notes entry + read-only list
- **US2.9 Immutable evidence hashing**
  - Field: `case_evidence_items.evidence_hash`
  - UI: Evidence register hash input (optional)
- **US2.10 External report metadata linkage**
  - Fields: `cases.external_report_id`, `cases.reporter_channel_id`, `cases.reporter_key`
  - UI: Intake fields to link external portal metadata
- **US2.7 Case linking (duplicate/related)**
  - Table: `case_links`
  - API: `GET/POST/DELETE /api/v1/cases/{case_id}/links`
  - UI: Intake step related cases panel
- **US2.8 Silent legal hold generator**
  - Table: `case_legal_holds`
  - API: `POST /api/v1/cases/{case_id}/legal-hold`, `GET /api/v1/cases/{case_id}/legal-holds`
  - UI: Investigation step legal hold card + download
- **US2.1 Secure Key Portal (public)**
  - Public endpoint: `/api/external/inbox?case_id=...&token=...`
  - UI: `/external/inbox` lightweight portal for anonymous two-way messages.
- **US2.2 Investigator chat console**
  - Reporter Q&A panel in Investigation step now includes response templates for quick replies.
- **US2.6 Serious cause clock record**
  - Table: `case_serious_cause`
  - API: `POST/GET /api/v1/cases/{case_id}/serious-cause`
  - UI: Serious cause clock inputs (business-day aware)
- **US3.1 Workflow transitions / hard gates**
  - Transition validation enforced on `/cases/{id}/stage`
  - Blocked transitions return `409` with reason codes
- **US3.1 Stage 1: Initial assessment (triage)**
  - Gate: `triage` with impact/probability matrix, risk_score (1–5), and outcome (Dismiss/Route to HR/Open Full Investigation).
  - Required before moving from `INTAKE → LEGITIMACY_GATE`.
- **US3.2 Stage 2: Impact analysis (PIA)**
  - Gate: `impact_analysis` capturing estimated loss, regulation breached, operational/financial/reputational/people impacts.
  - UI card in Investigation step; data included in export pack and audit trail.
- **US3.2 Legitimacy gate wizard (mandate record)**
  - Table: `case_gate_records`
  - API: `POST /api/v1/cases/{case_id}/gates/legitimacy`
  - UI: Legitimacy gate form
- **US3.3 Credentialing constraints**
  - API: `POST /api/v1/cases/{case_id}/gates/credentialing`
  - UI: Credentialing gate form
  - Systematic investigation mode now requires a licensed investigator + license ID (enforced server-side)
- **US3.3 Investigation checklist progress**
  - Tasks track status (`open`, `in_progress`, `completed`).
  - Investigation step shows completion progress bar.
- **US3.7 Conflict of Interest check (investigator vs subject/manager)**
  - Subject capture includes optional manager name
  - Credentialing gate blocks assignment when investigator matches subject or manager (override required)
- **US6.1 Immutable audit log**
  - Audit events are append-only (DB trigger guardrails in dev).
  - `GET /api/v1/audit?case_id=...&actor=...` supports filtering by actor.
  - Audit log lives in the Case Flow `Audit` step with actor + date filters.
  - Serious-cause clock events are now explicitly logged (clock started/stopped, findings submitted, dismissal recorded).
- **US6.3 Serious-cause audit event types**
  - Clock start/stop and key deadline actions emit dedicated audit events.
- **SOS: Escalate to Expert (External access grant)**
  - Table: `case_expert_access`
  - API: `GET/POST /api/v1/cases/{case_id}/experts`, `POST /api/v1/cases/{case_id}/experts/{access_id}/revoke`
  - UI: Investigation step card to grant 48h external expert access with revoke tracking.
- **Secure Inbox: Unlinked Dropbox (triage inbox)**
  - Table: `case_triage_tickets`
  - API: `POST /api/external/dropbox`, `GET/PATCH /api/v1/triage/inbox`, `POST /api/v1/triage/inbox/{ticket_id}/convert`
  - UI: Case Management → Inbox with create-case actions; public `/external/dropbox` intake page.
- **AI: Draft Summary (MVP heuristic)**
  - API: `GET /api/v1/cases/{case_id}/summary/draft`
  - Generates a draft decision summary from investigation notes (timeline format). Intended as a placeholder for future LLM integration.
- **AI: PII Auto-Redaction (MVP heuristic)**
  - API: `GET /api/v1/cases/{case_id}/redactions/suggest`
  - Uses regex heuristics to suggest PII candidates (email, phone, SSN, IP) for DSAR redaction logs.
- **AI: Consistency Recommender (MVP heuristic)**
  - API: `GET /api/v1/cases/{case_id}/consistency`
  - Shows outcome distribution for similar cases (same jurisdiction, optional playbook) with a caution when sample size is small.
- **US10.1 Security baseline**
  - Lightweight rate limiting middleware (per-IP) with optional max body size guard.
  - Guardrails are configurable via env (`IRMMF_RATE_LIMIT_*`, `IRMMF_MAX_BODY_MB`).
- **US5.1 Document template engine (PDF/DOCX)**
  - Document generation supports `txt`, `pdf`, and `docx` formats.
  - PDF export uses `reportlab`; DOCX export uses `python-docx`.
- **US3.4 Adversarial debate workflow**
  - API: `POST /api/v1/cases/{case_id}/gates/adversarial`
  - UI: Adversarial debate (interview) form
- **Case anonymization (data minimization)**
  - API: `POST /api/v1/cases/{case_id}/anonymize`
  - Clears subjects, notes, evidence, tasks, gates, serious-cause record
- **US1.4 Business-day calendar settings (Belgium)**
  - Tenant settings extended with weekend days, Saturday rule, cutoff hour
  - Holiday API: `GET/POST/DELETE /api/v1/tenant/holidays`
- **Infrastructure: Alembic migrations scaffold**
  - Added `alembic.ini`, `alembic/env.py`, and a baseline revision (`0001_baseline`)
  - DB URL pulls from `DATABASE_URL` (falls back to dev default)
  - Added revision `0002_tenant_settings_assessments` for tenant_settings columns + assessment tenant defaults
  - Runtime schema patching was removed; apply migration `0002_tenant_settings_assessments` (or run its SQL manually if Alembic isn't available)
  - Manual stamp helper: `./venv/bin/python scripts/stamp_alembic_version.py --revision 0002_tenant_settings_assessments`
  - Serious-cause deadlines now use the tenant business-day calculator
- **US2.5 Serious cause toggle + base fields**
  - Case fields: `serious_cause_enabled`, incident/investigation dates
  - API: `POST /api/v1/cases/{case_id}/serious-cause/enable`
- **US3.5 Submit findings action**
  - API: `POST /api/v1/cases/{case_id}/actions/submit-findings`
  - Sets `facts_confirmed_at` and computes deadlines
- **US3.6 Missed deadline acknowledgements**
  - API: `POST /api/v1/cases/{case_id}/serious-cause/acknowledge-missed`
- **US6.1 Immutable audit log (MVP)**
  - Table: `case_audit_events`
  - API: `GET /api/v1/audit?case_id=...`
- **US6.2 Sanity Check Wizard**
  - API: `GET /api/v1/cases/{case_id}/sanity-check`
  - Checks missing gates, evidence, tasks, notes, and decision outcome.
  - Returns score + missing items and warnings; surfaced in Closure step UI.
- **US6.2 Prohibited data keyword flagging (MVP)**
  - Table: `case_content_flags`
  - Notes scanned when tenant keyword flagging is enabled
- **US8.1 Jurisdiction banner**
  - Belgium banner added to case header UI
- **US8.2 BE authorized access restriction**
  - Belgium cases require `BE_AUTHORIZED` role (ADMIN bypass) for list/detail access.
  - UI role selector includes BE Authorized option.
- **US8.3 Jurisdiction rules config (JSON)**
  - Tenant settings store JSON rules in `tenant_settings.jurisdiction_rules`
  - Settings UI includes a JSON editor for jurisdiction rules
- **US8.4 Jurisdiction validator service**
  - Stage transitions return structured blockers when jurisdiction rules prevent progress
  - Case Flow shows a banner + modal listing unmet jurisdiction requirements
- **US4.1 Playbook library + apply to case**
  - Playbooks: DATA_EXFIL, FRAUD, SABOTAGE
  - API: `GET /api/v1/cases/playbooks`, `POST /api/v1/cases/{case_id}/apply-playbook`
  - Applying playbook adds tasks + evidence suggestions (deduped)
- **UI: Case management overlays**
  - Cases and PIA Compliance now open creation/workspace flows in overlays (scroll-locked), with list views simplified for faster scanning.
  - Case creation overlay now walks through intake → triage → subjects before handing off to the full flow.
  - Triage capture uses business-friendly labels and richer context fields (trigger source, sensitivity, stakeholders, confidence).
  - Triage labels and outcomes aligned with the Insider Risk Program policy rubric.
  - Single source of truth: cases are created and managed in `Case Management → Cases`; Compliance is now policy + workflow guidance only.
- **US4.2 NL: Suspension Enforcer**
  - Intake captures urgent dismissal + subject suspended flags.
  - NL urgent dismissal without suspension triggers a warning modal before saving.
- **US4.2 Evidence checklist suggestions UX**
  - Table: `case_evidence_suggestions`
  - API: `GET /api/v1/cases/{case_id}/suggestions`
  - Convert: `POST /api/v1/cases/{case_id}/suggestions/{suggestion_id}/convert`
  - Dismiss: `PUT /api/v1/cases/{case_id}/suggestions/{suggestion_id}`
- **US4.3 DE/FR: Works Council Airlock**
  - Works Council gate captures monitoring, approval URI, approval timestamp, and notes.
  - Evidence folder locks when monitoring is required and approval missing; unlocks once approval URI is saved.
  - Request document generated as `WORKS_COUNCIL_REQUEST` when monitoring is enabled.
- **US4.4 US: Legal Hold Notification**
  - US cases generate `US_LEGAL_HOLD` instruction (Preserve Mailbox X) with no subject notification.
  - Logged via `case_legal_holds` + audit event `legal_hold_generated`.
- **US5.1 Document template engine (PDF/DOCX)**
  - Table: `case_documents`
  - API: `POST /api/v1/cases/{case_id}/documents/{doc_type}`, `GET /api/v1/cases/{case_id}/documents`
  - Download: `GET /api/v1/cases/{case_id}/documents/{doc_id}/download`
- **US5.1 Investigation report generator**
  - Document type: `INVESTIGATION_REPORT`
  - Pulls triage, impact analysis, evidence register, task checklist, decision/outcome, gate status, and lessons learned.
- **US5.2 One-click case export pack**
  - API: `GET /api/v1/cases/{case_id}/export` (ZIP with case JSON + docs)
- **US5.2 Root cause & recommendations**
  - Notes captured via `note_type=lessons_learned` with root cause + action items.
  - Surfaced in Closure UI and the Investigation Report.
- **US5.3 Dismissal reasons letter from proven facts**
  - Document type: `DISMISSAL_REASONS_LETTER` (requires note_type `proven_facts`)
  - Legal approval required for generation/regeneration
- **US5.4 Proof-of-posting enforcement**
  - `record-reasons-sent` requires proof URI if delivery method is REGISTERED_MAIL
- **US5.5 DSAR redaction tool**
  - API: `POST /api/v1/cases/{case_id}/export/redact`
  - Stores redaction log on `case_documents` and produces redacted export pack
- **US7.1 Decision & outcome model**
  - Table: `case_outcomes`
  - API: `POST/GET /api/v1/cases/{case_id}/decision`
  - Decision required before closing a case
- **US7.2 Erasure trigger + certificate**
  - Table: `case_erasure_jobs`
  - API: `POST /api/v1/cases/{case_id}/erasure/approve`, `POST /api/v1/cases/{case_id}/erasure/execute`
- **US7.4 Remediation export (assessment handshake)**
  - API: `POST /api/v1/cases/{case_id}/remediation-export`
  - Stores `case_metadata.remediation_statement` and exports JSON/CSV for assessment intake.
  - Generates `ERASURE_CERTIFICATE` document
- **US3.4 Legal/compliance gate (closure blocker)**
  - Added gate `legal` required for `DECISION → CLOSURE` stage transition.
  - API: `POST /api/v1/cases/{case_id}/gates/legal` (Legal/Admin only)
  - UI: Legal approval card added to the Decision step.
- **US1.2 Detailed audit logging (enhanced)**
  - Audit events now capture request context (`ip_address`, `user_agent`) in `details._context`.
  - Document list/download actions logged (`document_list_viewed`, `document_downloaded`).
- **US2.1 Secure Key Portal (public alias)**
  - Added `/api/external/inbox?case_id=...&token=...` for external portal access.
  - Mirrors existing reporter portal flow; still uses case reporter token.
- **US7.3 Retaliation monitoring task**
  - Auto-create task on case close (`task_type=retaliation_check`, due +90 days)
  - UI: Task badge shows in Investigation step list
- **US3.8 Role separation (investigator ≠ decision maker)**
  - Decision blocked when decision maker == investigator; override requires LEGAL reason
  - API: `POST /api/v1/cases/{case_id}/decision` supports `role_separation_override_reason`
- **US1.6 VIP / highly sensitive case lockdown**
  - Field: `cases.vip_flag`
  - Access: only ADMIN/LEGAL or case creator; dashboards redact VIP titles
  - UI: VIP toggle in case creation + intake
- **US1.5 Secure reporter portal (anonymous 2-way)**
  - Table: `case_reporter_messages`
  - API: `GET/POST /api/v1/whistleblow/portal/{reporter_key}/messages`, `GET/POST /api/v1/cases/{case_id}/reporter-messages`
  - UI: Investigation step reporter Q&A card
- **US9.1 Basic operational dashboard**
  - API: `GET /api/v1/dashboard`
  - Metrics: case counts by status/stage, avg days open/stage, gate completion rates
  - UI: Command Center summary card
- **US9.2 Systematic drift monitoring (HR exemption)**
  - Dashboard alert banner when case volume exceeds threshold
  - Alerts stored in `dashboard_alert_events` (per tenant, daily throttle)
- **US9.3 Serious-cause countdown widget**
  - Dashboard lists serious-cause cases and deadlines
  - Case list shows badges for decision/dismissal due
- **US9.4 Notification center (serious-cause milestones)**
  - API: `GET /api/v1/notifications`, `POST /api/v1/notifications/{id}/ack`
  - Notifications stored in `case_notifications`
  - Toggle controls in tenant settings (notifications + serious-cause milestones)
- **US10.1 Security baseline**
  - Security headers middleware (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy)
- **US10.2 Automated tests**
  - Business-day calculator tests
  - Case status/stage validation tests
  - Triage validator tests (scores + outcomes)

## API Summary (Core Case Module)

- `GET /api/v1/cases`
- `POST /api/v1/cases`
- `GET /api/v1/cases/{case_id}`
- `PATCH /api/v1/cases/{case_id}`
- `POST /api/v1/cases/{case_id}/status`
- `POST /api/v1/cases/{case_id}/stage`
- `POST /api/v1/cases/{case_id}/subjects`
- `GET /api/v1/cases/{case_id}/links`
- `POST /api/v1/cases/{case_id}/links`
- `DELETE /api/v1/cases/{case_id}/links/{link_id}`
- `GET /api/v1/cases/{case_id}/legal-holds`
- `POST /api/v1/cases/{case_id}/legal-hold`
- `POST /api/v1/cases/{case_id}/evidence`
- `GET /api/v1/cases/{case_id}/reporter-messages`
- `POST /api/v1/cases/{case_id}/reporter-messages`
- `GET /api/v1/cases/{case_id}/experts`
- `POST /api/v1/cases/{case_id}/experts`
- `POST /api/v1/cases/{case_id}/experts/{access_id}/revoke`
- `POST /api/external/dropbox`
- `GET /api/v1/triage/inbox`
- `PATCH /api/v1/triage/inbox/{ticket_id}`
- `POST /api/v1/triage/inbox/{ticket_id}/convert`
- `POST /api/v1/cases/{case_id}/tasks`
- `GET /api/v1/cases/{case_id}/tasks`
- `POST /api/v1/cases/{case_id}/notes`
- `GET /api/v1/cases/{case_id}/notes`
- `POST /api/v1/cases/{case_id}/gates/legitimacy`
- `POST /api/v1/cases/{case_id}/gates/credentialing`
- `POST /api/v1/cases/{case_id}/gates/adversarial`
- `GET /api/v1/cases/{case_id}/gates`
- `POST /api/v1/cases/{case_id}/serious-cause`
- `GET /api/v1/cases/{case_id}/serious-cause`
- `POST /api/v1/cases/{case_id}/anonymize`
- `POST /api/v1/cases/{case_id}/serious-cause/enable`
- `POST /api/v1/cases/{case_id}/actions/submit-findings`
- `POST /api/v1/cases/{case_id}/serious-cause/record-dismissal`
- `POST /api/v1/cases/{case_id}/serious-cause/record-reasons-sent`
- `POST /api/v1/cases/{case_id}/serious-cause/acknowledge-missed`
- `GET /api/v1/cases/{case_id}/flags`
- `PUT /api/v1/cases/{case_id}/flags/{flag_id}`
- `GET /api/v1/audit?case_id=...`
- `GET /api/v1/cases/playbooks`
- `POST /api/v1/cases/{case_id}/apply-playbook`
- `GET /api/v1/cases/{case_id}/suggestions`
- `POST /api/v1/cases/{case_id}/suggestions/{suggestion_id}/convert`
- `PUT /api/v1/cases/{case_id}/suggestions/{suggestion_id}`
- `GET /api/v1/cases/{case_id}/documents`
- `POST /api/v1/cases/{case_id}/documents/{doc_type}`
- `GET /api/v1/cases/{case_id}/documents/{doc_id}/download`
- `GET /api/v1/cases/{case_id}/summary/draft`
- `GET /api/v1/cases/{case_id}/redactions/suggest`
- `GET /api/v1/cases/{case_id}/consistency`
- `GET /api/v1/cases/{case_id}/export`
- `POST /api/v1/cases/{case_id}/export/redact`
- `POST /api/v1/cases/{case_id}/remediation-export`
- `POST /api/v1/cases/{case_id}/decision`
- `GET /api/v1/cases/{case_id}/decision`
- `POST /api/v1/cases/{case_id}/erasure/approve`
- `POST /api/v1/cases/{case_id}/erasure/execute`
- `GET /api/v1/dashboard`
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{notification_id}/ack`
- `GET /api/v1/whistleblow/portal/{reporter_key}`
- `POST /api/v1/whistleblow/portal/{reporter_key}/messages`

## UI Notes

- `Cases` page is now a lightweight launcher:
  - Create case form
  - Case list with summary + open flow action
  - Minimize/expand cards and quick close button
  - Close/re-open confirmation (blocked when anonymized)
- `Case Flow` contains all case work (subjects, evidence, tasks, notes, gates, serious cause, documents, erasure):
  - Multi-step navigation mirrors the PIA workflow
  - Inline guidance and helper copy added per step
  - Guidance is collapsible via the info button
  - Dropdown suggestions for legal basis, jurisdiction, and other structured fields
  - Recommended tasks and meeting minutes capture added in Investigation step
  - Serious cause enabled early in Intake (timeline actions remain in Decision)
  - Credentialing gate enforces conflict-of-interest + role separation guardrails
  - Closure step includes audit timeline (refreshable)
- Location: `frontend/src/pages/Cases.tsx` and `frontend/src/pages/CaseFlow.tsx`
- Cases and Compliance pages include cross-links for quick navigation.
- Shared workspace layout: `frontend/src/components/CaseWorkspace.tsx` keeps Cases + PIA case panels aligned.
- Case Management UI groups Compliance, Cases, Inbox, and Notifications under `/case-management/*`.

## Multi-Tenant & User Linking Notes

- `tenant_key` is recorded on cases and PIA cases.
- In dev, tenant is derived from the `X-IRMMF-KEY` header or defaults to `default`.
- Case creation uses the principal subject as `created_by`.
- **TODO**: Replace with real login/JWT claims once auth is enabled.

## Outstanding Reminders

- Auth integration pending: replace dev identity fallbacks with login/JWT claims (see multi-tenant notes).

## Developer Notes

- New tables in this pass:
  - `cases`, `case_subjects`, `case_evidence_items`, `case_tasks`, `case_status_events`
  - `case_notes`, `case_gate_records`, `case_serious_cause`
  - `case_content_flags`, `case_audit_events`, `tenant_holidays`
  - `case_evidence_suggestions`
  - `case_documents`
  - `case_links`
  - `case_legal_holds`
- `case_reporter_messages`
- `case_expert_access`
- `case_triage_tickets`
- `case_outcomes`, `case_erasure_jobs`
- `dashboard_alert_events`
- `case_notifications`
- `cases.case_uuid` is immutable and should be treated as the legal audit identifier.
- `cases.external_report_id`, `cases.reporter_channel_id`, `cases.reporter_key` store external portal linkage metadata.
- `cases.vip_flag` marks VIP/highly sensitive cases for access restriction.
- `case_evidence_items.evidence_hash` stores optional integrity hashes for evidence records.
- Case status transitions are logged in `case_status_events`.
- `case_tasks.task_type` supports system task labels (e.g., retaliation_check).
- `case_outcomes.role_separation_override_reason` + `role_separation_override_by` track LEGAL overrides.
- `case_subjects.manager_name` captures optional manager for COI checks.
- `case_documents.redaction_log` stores DSAR export redaction notes.
- `case_metadata.remediation_statement` + `case_metadata.remediation_exported_at` capture remediation export context.
- Frontend attaches `Authorization`, `X-IRMMF-ROLES`, and `X-IRMMF-KEY` headers on `/api/v1/*` requests.
- Frontend API helpers live in `frontend/src/lib/api.ts` (API_BASE/API_ROOT + apiFetch/apiJson/apiBlob).
- Belgium cases require `BE_AUTHORIZED` or `ADMIN` in `X-IRMMF-ROLES` for access.
- In dev, `DEV_RBAC_DISABLED=1` bypasses VIP/BE access checks to avoid blocking test flows.
- Security context: `PrincipalContextMiddleware` caches header-derived principals; tenant/role checks live in `app/security/access.py`.
- PIA/DWF routers enforce tenant context via router-level dependency (`tenant_principal_required`).
- Assessment endpoints enforce tenant matching (ADMIN override); dev bypass applies when `DEV_RBAC_DISABLED=1`.
- Recommendation library endpoints require tenant context (ADMIN override) when RBAC is enabled.
- Dev DB reset helper (destructive): `python scripts/dev_reset_db.py`
- Dev reset stamps `alembic_version` (override with `ALEMBIC_HEAD` if needed).
- One-command checks: `python scripts/run_quality_checks.py` (pytest + smoke test).
- Smoke test CLI overrides: `python scripts/verify_investigation_module.py --api-base ... --tenant-key ... --roles ... --cleanup`
- Smoke test exits non-zero if any step fails (after case creation succeeds).
- Pytest filters suppress Python 3.14 asyncio deprecation warnings from FastAPI/Starlette; remove after upgrading deps.
- If startup errors mention `jurisdiction_rules`, reset the dev DB to add the column.
- `tenant_settings.jurisdiction_rules` stores per-country guardrail logic.
- Alembic scaffolding lives in `alembic/` with a baseline revision in `alembic/versions`.

## Jurisdiction Engine (Implemented)

Goal: Centralize country-specific rules in a configurable profile and drive deadlines/guardrails from tenant settings.

Implemented components:
- **Tenant setting: `jurisdiction_rules` (JSON)**
  - Editable in Platform Settings under "Jurisdiction rules engine".
  - Example:
    ```
    {
      "BE": {
        "decision_deadline_days": 3,
        "dismissal_deadline_days": 3,
        "deadline_type": "working_days",
        "requires_registered_mail_receipt": true
      },
      "NL": {
        "decision_deadline_hours": 48,
        "deadline_type": "hours"
      },
      "LU": {
        "min_cooling_off_days": 1,
        "max_dismissal_window_days": 8,
        "trigger_event": "pre_dismissal_interview"
      },
      "IE": {
        "warn_if_decision_under_hours": 24
      }
    }
    ```
- **Validator hooks**
  - Serious-cause deadlines derived from `jurisdiction_rules`.
  - Registered-mail proof enforced when configured.
  - Cooling-off windows enforced for dismissal actions.
  - Natural-justice warning created on decision when configured.
- **UI**
  - Jurisdiction selection expanded (BE/NL/LU/IE + others).
  - Serious-cause copy updated to reflect jurisdiction rules.

## Recent UI Updates

- **Insider Risk Program**
  - Renamed the Recommendations navigation/page to Insider Risk Program (navigation + page copy).
  - Added insider risk policy framework section and a control register UI for tracking program controls.
  - Persisted policy + controls via new API endpoints and tables:
    - `GET/PUT /api/v1/insider-program/policy`
    - `GET/POST/PUT /api/v1/insider-program/controls`
    - Tables: `insider_risk_policies`, `insider_risk_controls`
  - Control register supports linking to assessment recommendations via `linked_rec_ids` and `linked_categories`.
  - Alembic revision: `0003_insider_program` (policy + control tables).
  - New subpages under Insider Risk Program: Policy, Controls, Risks, Roadmap, Actions.
  - Assessment risk view moved to `Insider Risk Program → Risks` (assessment route redirects).
  - Roadmap is now persisted via `GET/POST/PUT/DELETE /api/v1/insider-program/roadmap`
    with table `insider_risk_roadmap_items` (Alembic `0004_insider_program_roadmap`).
  - Alembic revision: `0005_case_expert_access` (external expert access grants).
  - Alembic revision: `0006_triage_inbox` (triage inbox tickets).

## Backlog Extensions (NAVEX Gap + Process Edge)

Additions proposed for future sprints:
- **Jurisdiction Guardrail Expansion (Epic 8)**: NL/LU/IE rules and warnings implemented via Jurisdiction Engine.

## Whistleblowing Integration Notes

- External whistleblowing portal remains separate, but will link into Cases via metadata:
  - `external_report_id`, `reporter_channel_id`, `reporter_key`.
- Reporter portal supports anonymous two-way messages tied to `reporter_key`.
- Case UI surfaces reporter Q&A inside the Investigation step.

## Environment

- Postgres runs on port `5432` in dev (single source of truth is `.env`).
- Keep DBeaver and the API pointing at the same port/database.
- `.env` includes:
  - `DATABASE_URL=postgresql+psycopg://irmmf_app:secure_password@127.0.0.1:5432/irmmf_db`
- Assessment UI now auto-resets stale assessment IDs (404) and re-creates a fresh assessment to avoid DB mismatch issues.

---
If this file is moved, update the location in project docs.
