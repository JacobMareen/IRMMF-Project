from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone, timedelta, date
from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import Principal
from app.modules.cases import models
from app.modules.cases.errors import TransitionError
from app.modules.cases.schemas import (
    CASE_STATUSES,
    CASE_STAGES,
    CaseAcknowledgeMissed,
    CaseAdversarialForm,
    CaseBreakGlassRequest,
    CaseApplyPlaybook,
    CaseAuditEventOut,
    CaseContentFlagOut,
    CaseContentFlagUpdate,
    CaseCreate,
    CaseCredentialingForm,
    CaseEvidenceCreate,
    CaseEvidenceOut,
    CaseEvidenceSuggestionOut,
    CaseEvidenceSuggestionUpdate,
    CaseGateRecordOut,
    CaseImpactAnalysisForm,
    CaseLegalApprovalForm,
    CaseLinkCreate,
    CaseLinkOut,
    CaseExpertAccessCreate,
    CaseExpertAccessOut,
    CaseTriageTicketCreate,
    CaseTriageTicketUpdate,
    CaseTriageTicketConvert,
    CaseTriageTicketOut,
    CaseSummaryDraftOut,
    CaseRedactionSuggestionOut,
    CaseConsistencyOut,
    CaseOutcomeStat,
    CaseLegalHoldCreate,
    CaseLegalHoldOut,
    CaseLegitimacyForm,
    CaseReporterMessageCreate,
    CaseReporterMessageOut,
    CaseNoteCreate,
    CaseNoteOut,
    CaseOut,
    CasePlaybookOut,
    CaseDocumentOut,
    CaseDocumentCreate,
    CaseDecisionCreate,
    CaseOutcomeOut,
    CaseExportRedactionCreate,
    CaseRemediationExportCreate,
    CaseErasureApprove,
    CaseErasureExecute,
    CaseErasureJobOut,
    CaseRecordDismissal,
    CaseRecordReasonsSent,
    CaseSeriousCauseOut,
    CaseSeriousCauseToggle,
    CaseSeriousCauseUpsert,
    CaseStageUpdate,
    CaseStatusUpdate,
    CaseUpdate,
    CaseSubjectCreate,
    CaseSubjectOut,
    CaseSubmitFindings,
    CaseTaskCreate,
    CaseTriageForm,
    CaseTaskUpdate,
    CaseTaskOut,
    CaseWorksCouncilForm,
    CaseNotificationOut,
    CaseSanityCheckOut,
)
from app.modules.tenant import models as tenant_models
from app.modules.tenant.business_days import add_business_days
from app.modules.cases.playbooks import PLAYBOOKS, get_playbook
from app.modules.cases.documents import normalize_document_format, render_document, render_document_bytes
from app.security.audit import get_audit_context


STAGE_FLOW = {
    "INTAKE": {"LEGITIMACY_GATE"},
    "LEGITIMACY_GATE": {"CREDENTIALING"},
    "CREDENTIALING": {"INVESTIGATION"},
    "INVESTIGATION": {"ADVERSARIAL_DEBATE"},
    "ADVERSARIAL_DEBATE": {"DECISION"},
    "DECISION": {"CLOSURE"},
    "CLOSURE": set(),
}

STAGE_GATES = {
    ("INTAKE", "LEGITIMACY_GATE"): "triage",
    ("LEGITIMACY_GATE", "CREDENTIALING"): "legitimacy",
    ("CREDENTIALING", "INVESTIGATION"): "credentialing",
    ("ADVERSARIAL_DEBATE", "DECISION"): "adversarial",
    ("DECISION", "CLOSURE"): "legal",
}

GATE_VALIDATORS = {
    "triage": CaseTriageForm,
    "legitimacy": CaseLegitimacyForm,
    "credentialing": CaseCredentialingForm,
    "adversarial": CaseAdversarialForm,
    "impact_analysis": CaseImpactAnalysisForm,
    "works_council": CaseWorksCouncilForm,
    "legal": CaseLegalApprovalForm,
}


class CaseService:
    def __init__(self, db: Session):
        self.db = db

    def list_cases(self, principal: Principal) -> List[CaseOut]:
        tenant_key = principal.tenant_key or None
        query = self.db.query(models.Case)
        if tenant_key:
            query = query.filter(models.Case.tenant_key == tenant_key)
        cases = query.order_by(models.Case.created_at.desc()).all()
        visible = [case for case in cases if self._can_view_case(case, principal)]
        return [self._serialize_case(case) for case in visible]

    def list_playbooks(self) -> List[CasePlaybookOut]:
        return [CasePlaybookOut(key=pb.key, title=pb.title, description=pb.description) for pb in PLAYBOOKS]

    def get_dashboard(self, principal: Principal) -> dict:
        tenant_key = principal.tenant_key or None
        query = self.db.query(models.Case)
        if tenant_key:
            query = query.filter(models.Case.tenant_key == tenant_key)
        cases = query.all()
        cases = [case for case in cases if self._can_view_case(case, principal)]
        total_cases = len(cases)

        status_counts = {status: 0 for status in CASE_STATUSES}
        stage_counts = {stage: 0 for stage in CASE_STAGES}
        serious_cause_enabled = 0
        case_ids = []

        for case in cases:
            status_counts[case.status] = status_counts.get(case.status, 0) + 1
            stage_counts[case.stage] = stage_counts.get(case.stage, 0) + 1
            if case.serious_cause_enabled:
                serious_cause_enabled += 1
            case_ids.append(case.case_id)

        now = datetime.now(timezone.utc)
        age_days: list[float] = []
        stage_age_days: list[float] = []

        last_stage_change: dict[str, datetime] = {}
        if case_ids:
            events = (
                self.db.query(models.CaseAuditEvent)
                .filter(
                    models.CaseAuditEvent.case_id.in_(case_ids),
                    models.CaseAuditEvent.event_type == "stage_changed",
                )
                .order_by(models.CaseAuditEvent.created_at.desc())
                .all()
            )
            for event in events:
                if event.case_id not in last_stage_change:
                    last_stage_change[event.case_id] = event.created_at

        for case in cases:
            age_days.append((now - case.created_at).total_seconds() / 86400)
            last_change = last_stage_change.get(case.case_id, case.created_at)
            stage_age_days.append((now - last_change).total_seconds() / 86400)

        avg_days_open = round(sum(age_days) / len(age_days), 2) if age_days else 0.0
        avg_days_in_stage = round(sum(stage_age_days) / len(stage_age_days), 2) if stage_age_days else 0.0

        gate_keys = ["legitimacy", "credentialing", "adversarial"]
        gate_completed = {key: 0 for key in gate_keys}
        if case_ids:
            gate_records = (
                self.db.query(models.CaseGateRecord)
                .filter(models.CaseGateRecord.case_id.in_(case_ids))
                .all()
            )
            for record in gate_records:
                if record.gate_key in gate_keys and record.status == "completed":
                    gate_completed[record.gate_key] += 1

        gate_completion = {}
        for key in gate_keys:
            rate = round((gate_completed[key] / total_cases) * 100, 1) if total_cases else 0.0
            gate_completion[key] = {
                "completed": gate_completed[key],
                "total_cases": total_cases,
                "rate": rate,
            }

        window_days = 30
        threshold_cases = 5
        recent_case_count = 0
        if cases:
            since = now - timedelta(days=window_days)
            recent_case_count = sum(1 for case in cases if case.created_at >= since)

        alerts: list[dict] = []
        if recent_case_count >= threshold_cases:
            message = (
                f"{recent_case_count} cases opened in the last {window_days} days. "
                "HR exemption posture may be drifting toward systematic investigations."
            )
            alert_event = self._record_dashboard_alert(
                tenant_key=tenant_key or "default",
                alert_key="hr_exemption_drift",
                severity="warning",
                message=message,
            )
            alerts.append(
                {
                    "alert_key": alert_event.alert_key,
                    "severity": alert_event.severity,
                    "message": alert_event.message,
                    "created_at": alert_event.created_at.isoformat(),
                }
            )

        serious_cause_cases: list[dict] = []
        if case_ids:
            serious_cases = (
                self.db.query(models.Case, models.CaseSeriousCause)
                .join(models.CaseSeriousCause, models.CaseSeriousCause.case_id == models.Case.case_id)
                .filter(models.Case.case_id.in_(case_ids))
                .all()
            )
            for case, record in serious_cases:
                if not case.serious_cause_enabled:
                    continue
                decision_due = record.decision_due_at
                dismissal_due = record.dismissal_due_at
                title = case.title if self._can_view_case(case, principal) else "VIP case"
                serious_cause_cases.append(
                    {
                        "case_id": case.case_id,
                        "title": title,
                        "decision_due_at": decision_due.isoformat() if decision_due else None,
                        "dismissal_due_at": dismissal_due.isoformat() if dismissal_due else None,
                        "facts_confirmed_at": record.facts_confirmed_at.isoformat() if record.facts_confirmed_at else None,
                    }
                )
        serious_cause_cases = serious_cause_cases[:10]

        return {
            "total_cases": total_cases,
            "status_counts": status_counts,
            "stage_counts": stage_counts,
            "serious_cause_enabled": serious_cause_enabled,
            "avg_days_open": avg_days_open,
            "avg_days_in_stage": avg_days_in_stage,
            "gate_completion": gate_completion,
            "recent_case_count": recent_case_count,
            "recent_window_days": window_days,
            "alert_threshold_cases": threshold_cases,
            "alerts": alerts,
            "serious_cause_cases": serious_cause_cases,
        }

    def _record_dashboard_alert(
        self,
        tenant_key: str,
        alert_key: str,
        severity: str,
        message: str,
    ) -> models.DashboardAlertEvent:
        now = datetime.now(timezone.utc)
        recent = (
            self.db.query(models.DashboardAlertEvent)
            .filter(
                models.DashboardAlertEvent.tenant_key == tenant_key,
                models.DashboardAlertEvent.alert_key == alert_key,
            )
            .order_by(models.DashboardAlertEvent.created_at.desc())
            .first()
        )
        if recent and (now - recent.created_at) < timedelta(hours=24):
            return recent
        event = models.DashboardAlertEvent(
            tenant_key=tenant_key,
            alert_key=alert_key,
            severity=severity,
            message=message,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_case(self, case_id: str, principal: Principal) -> CaseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        return self._serialize_case(case)

    def create_case(self, payload: CaseCreate, principal: Principal) -> CaseOut:
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        tenant_key = principal.tenant_key or "default"
        company_id = None
        default_jurisdiction = "Belgium"
        tenant = (
            self.db.query(tenant_models.Tenant)
            .filter(tenant_models.Tenant.tenant_key == tenant_key)
            .first()
        )
        if tenant and tenant.settings:
            if tenant.settings.company_name:
                company_id = tenant.settings.company_name
            if tenant.settings.default_jurisdiction:
                default_jurisdiction = tenant.settings.default_jurisdiction
        if not company_id:
            # Integration pending: derive company from auth/tenant claims once login is enabled.
            company_id = "TBD-COMPANY"
        jurisdiction_value = payload.jurisdiction or default_jurisdiction
        self._ensure_jurisdiction_access(jurisdiction_value, principal)
        case = models.Case(
            case_id=case_id,
            tenant_key=tenant_key,
            created_by=principal.subject,
            company_id=company_id,
            title=payload.title.strip(),
            summary=payload.summary,
            jurisdiction=jurisdiction_value,
            vip_flag=bool(payload.vip_flag),
            external_report_id=payload.external_report_id,
            reporter_channel_id=payload.reporter_channel_id,
            reporter_key=payload.reporter_key,
            status="OPEN",
            stage="INTAKE",
            case_metadata={
                "reminders": [
                    "Integration pending: connect to PIA workflow engine.",
                    "Integration pending: link to assessment_id when assessment integration is enabled.",
                ],
                "urgent_dismissal": bool(payload.urgent_dismissal) if payload.urgent_dismissal is not None else None,
                "subject_suspended": bool(payload.subject_suspended) if payload.subject_suspended is not None else None,
            },
            serious_cause_enabled=False,
        )
        self.db.add(case)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="case_created",
            actor=principal.subject,
            message="Case created.",
            details={"jurisdiction": case.jurisdiction},
        )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def update_status(self, case_id: str, payload: CaseStatusUpdate, principal: Principal) -> CaseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        from_status = case.status
        case.status = payload.status
        if from_status != "CLOSED" and payload.status == "CLOSED":
            self._schedule_retaliation_task(case, principal)
        self.db.add(
            models.CaseStatusEvent(
                case_id=case.case_id,
                from_status=from_status,
                to_status=payload.status,
                reason=payload.reason,
                changed_by=principal.subject,
            )
        )
        self._log_audit_event(
            case_id=case.case_id,
            event_type="status_changed",
            actor=principal.subject,
            message=f"Status changed from {from_status} to {payload.status}.",
            details={"from": from_status, "to": payload.status, "reason": payload.reason},
        )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def update_case(self, case_id: str, payload: CaseUpdate, principal: Principal) -> CaseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return self._serialize_case(case)
        change_log: dict[str, dict[str, str | None]] = {}
        if "title" in updates:
            title_value = (updates.get("title") or "").strip()
            if not title_value:
                raise ValueError("Title cannot be empty.")
            if title_value != case.title:
                change_log["title"] = {"from": case.title, "to": title_value}
                case.title = title_value
        if "summary" in updates:
            summary_value = updates.get("summary")
            summary_value = summary_value.strip() if isinstance(summary_value, str) else None
            if summary_value != case.summary:
                change_log["summary"] = {"from": case.summary, "to": summary_value}
                case.summary = summary_value
        if "jurisdiction" in updates:
            jurisdiction_value = (updates.get("jurisdiction") or "").strip()
            if not jurisdiction_value:
                raise ValueError("Jurisdiction cannot be empty.")
            if jurisdiction_value != case.jurisdiction:
                self._ensure_jurisdiction_access(jurisdiction_value, principal)
                change_log["jurisdiction"] = {"from": case.jurisdiction, "to": jurisdiction_value}
                case.jurisdiction = jurisdiction_value
        if "vip_flag" in updates:
            vip_value = bool(updates.get("vip_flag"))
            if vip_value != case.vip_flag:
                change_log["vip_flag"] = {"from": case.vip_flag, "to": vip_value}
                case.vip_flag = vip_value
        if "external_report_id" in updates:
            report_value = (updates.get("external_report_id") or "").strip() or None
            if report_value != case.external_report_id:
                change_log["external_report_id"] = {"from": case.external_report_id, "to": report_value}
                case.external_report_id = report_value
        if "reporter_channel_id" in updates:
            channel_value = (updates.get("reporter_channel_id") or "").strip() or None
            if channel_value != case.reporter_channel_id:
                change_log["reporter_channel_id"] = {"from": case.reporter_channel_id, "to": channel_value}
                case.reporter_channel_id = channel_value
        if "reporter_key" in updates:
            key_value = (updates.get("reporter_key") or "").strip() or None
            if key_value != case.reporter_key:
                change_log["reporter_key"] = {"from": case.reporter_key, "to": key_value}
                case.reporter_key = key_value
        metadata = case.case_metadata or {}
        if "urgent_dismissal" in updates:
            urgent_value = updates.get("urgent_dismissal")
            if urgent_value is not None:
                urgent_value = bool(urgent_value)
            if metadata.get("urgent_dismissal") != urgent_value:
                change_log["urgent_dismissal"] = {
                    "from": metadata.get("urgent_dismissal"),
                    "to": urgent_value,
                }
                metadata["urgent_dismissal"] = urgent_value
        if "subject_suspended" in updates:
            suspended_value = updates.get("subject_suspended")
            if suspended_value is not None:
                suspended_value = bool(suspended_value)
            if metadata.get("subject_suspended") != suspended_value:
                change_log["subject_suspended"] = {
                    "from": metadata.get("subject_suspended"),
                    "to": suspended_value,
                }
                metadata["subject_suspended"] = suspended_value
        case.case_metadata = metadata
        if change_log:
            self._log_audit_event(
                case_id=case.case_id,
                event_type="case_updated",
                actor=principal.subject,
                message="Case metadata updated.",
                details=change_log,
            )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def update_stage(self, case_id: str, payload: CaseStageUpdate, principal: Principal) -> CaseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        self._validate_stage_transition(case, payload.stage)
        from_stage = case.stage
        case.stage = payload.stage
        self._log_audit_event(
            case_id=case.case_id,
            event_type="stage_changed",
            actor=principal.subject,
            message=f"Stage changed from {from_stage} to {payload.stage}.",
            details={"from": from_stage, "to": payload.stage},
        )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def add_subject(self, case_id: str, payload: CaseSubjectCreate, principal: Principal) -> CaseSubjectOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        subject = models.CaseSubject(
            case_id=case.case_id,
            subject_type=payload.subject_type,
            display_name=payload.display_name,
            reference=payload.reference,
            manager_name=payload.manager_name,
        )
        self.db.add(subject)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="subject_added",
            actor=principal.subject,
            message="Subject added.",
            details={"subject_type": payload.subject_type, "display_name": payload.display_name},
        )
        self.db.commit()
        self.db.refresh(subject)
        return CaseSubjectOut.model_validate(subject)

    def add_evidence(self, case_id: str, payload: CaseEvidenceCreate, principal: Principal) -> CaseEvidenceOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        self._ensure_evidence_unlocked(case)
        evidence = models.CaseEvidenceItem(
            case_id=case.case_id,
            evidence_id=f"EVD-{uuid.uuid4().hex[:6].upper()}",
            label=payload.label,
            source=payload.source,
            link=payload.link,
            notes=payload.notes,
            evidence_hash=payload.evidence_hash,
            status="registered",
        )
        self.db.add(evidence)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="evidence_added",
            actor=principal.subject,
            message="Evidence item added.",
            details={"evidence_id": evidence.evidence_id, "label": payload.label, "source": payload.source},
        )
        self.db.commit()
        self.db.refresh(evidence)
        return CaseEvidenceOut.model_validate(evidence)

    def add_task(self, case_id: str, payload: CaseTaskCreate, principal: Principal) -> CaseTaskOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        task = models.CaseTask(
            case_id=case.case_id,
            task_id=f"TASK-{uuid.uuid4().hex[:6].upper()}",
            title=payload.title,
            description=payload.description,
            task_type=payload.task_type,
            status=payload.status or "open",
            due_at=payload.due_at,
            assignee=payload.assignee,
        )
        self.db.add(task)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="task_added",
            actor=principal.subject,
            message="Task added.",
            details={"task_id": task.task_id, "title": payload.title},
        )
        self.db.commit()
        self.db.refresh(task)
        return CaseTaskOut.model_validate(task)

    def update_task(
        self,
        case_id: str,
        task_id: str,
        payload: CaseTaskUpdate,
        principal: Principal,
    ) -> CaseTaskOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        task = (
            self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .filter(models.CaseTask.task_id == task_id)
            .first()
        )
        if not task:
            raise ValueError("Task not found.")
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return CaseTaskOut.model_validate(task)
        change_log: dict[str, dict[str, str | None]] = {}
        if "status" in updates and updates["status"] is not None:
            status_value = updates["status"]
            if status_value != task.status:
                change_log["status"] = {"from": task.status, "to": status_value}
                task.status = status_value
        if "assignee" in updates:
            assignee_value = (updates.get("assignee") or "").strip() or None
            if assignee_value != task.assignee:
                change_log["assignee"] = {"from": task.assignee, "to": assignee_value}
                task.assignee = assignee_value
        if "due_at" in updates:
            due_value = updates.get("due_at")
            if due_value != task.due_at:
                change_log["due_at"] = {
                    "from": task.due_at.isoformat() if task.due_at else None,
                    "to": due_value.isoformat() if due_value else None,
                }
                task.due_at = due_value
        if change_log:
            self._log_audit_event(
                case_id=case.case_id,
                event_type="task_updated",
                actor=principal.subject,
                message="Task updated.",
                details={"task_id": task.task_id, "changes": change_log},
            )
        self.db.commit()
        self.db.refresh(task)
        return CaseTaskOut.model_validate(task)

    def apply_playbook(self, case_id: str, payload: CaseApplyPlaybook, principal: Principal) -> CaseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        playbook = get_playbook(payload.playbook_key)
        if not playbook:
            raise ValueError("Unknown playbook")
        existing_tasks = {
            task.title
            for task in self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .all()
        }
        existing_suggestions = {
            suggestion.suggestion_id
            for suggestion in self.db.query(models.CaseEvidenceSuggestion)
            .filter(models.CaseEvidenceSuggestion.case_id == case.case_id)
            .all()
        }
        for idx, task in enumerate(playbook.tasks, start=1):
            if task.title in existing_tasks:
                continue
            new_task = models.CaseTask(
                case_id=case.case_id,
                task_id=f"TASK-{uuid.uuid4().hex[:6].upper()}",
                title=task.title,
                description=task.description,
                status="open",
            )
            self.db.add(new_task)

        for idx, suggestion in enumerate(playbook.evidence, start=1):
            suggestion_id = f"SUG-{playbook.key}-{idx}"
            if suggestion_id in existing_suggestions:
                continue
            new_suggestion = models.CaseEvidenceSuggestion(
                case_id=case.case_id,
                suggestion_id=suggestion_id,
                playbook_key=playbook.key,
                label=suggestion.label,
                source=suggestion.source,
                description=suggestion.description,
                status="open",
            )
            self.db.add(new_suggestion)

        self._log_audit_event(
            case_id=case.case_id,
            event_type="playbook_applied",
            actor=principal.subject,
            message="Playbook applied to case.",
            details={"playbook_key": playbook.key},
        )
        self.db.commit()
        return self._serialize_case(case)

    def list_tasks(self, case_id: str, principal: Principal) -> List[CaseTaskOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        tasks = (
            self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .order_by(models.CaseTask.created_at.desc())
            .all()
        )
        return [CaseTaskOut.model_validate(task) for task in tasks]

    def list_links(self, case_id: str, principal: Principal) -> List[CaseLinkOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        links = (
            self.db.query(models.CaseLink)
            .filter(models.CaseLink.case_id == case.case_id)
            .order_by(models.CaseLink.created_at.desc())
            .all()
        )
        return [CaseLinkOut.model_validate(link) for link in links]

    def sanity_check(self, case_id: str, principal: Principal) -> CaseSanityCheckOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        missing: list[str] = []
        warnings: list[str] = []
        checks = [
            ("triage", bool(self._gate_data(case.case_id, "triage")), "Triage assessment missing"),
            ("impact", bool(self._gate_data(case.case_id, "impact_analysis")), "Impact analysis missing"),
            ("legitimacy", bool(self._gate_data(case.case_id, "legitimacy")), "Legitimacy gate not completed"),
            ("credentialing", bool(self._gate_data(case.case_id, "credentialing")), "Credentialing gate not completed"),
            ("adversarial", bool(self._gate_data(case.case_id, "adversarial")), "Adversarial gate not completed"),
            ("legal", bool(self._gate_data(case.case_id, "legal")), "Legal approval missing"),
        ]
        for _, ok, message in checks:
            if not ok:
                missing.append(message)

        subjects_count = self.db.query(models.CaseSubject).filter(models.CaseSubject.case_id == case.case_id).count()
        evidence_count = self.db.query(models.CaseEvidenceItem).filter(models.CaseEvidenceItem.case_id == case.case_id).count()
        tasks_count = self.db.query(models.CaseTask).filter(models.CaseTask.case_id == case.case_id).count()
        notes_count = self.db.query(models.CaseNote).filter(models.CaseNote.case_id == case.case_id).count()

        if subjects_count == 0:
            missing.append("No subjects recorded")
        if evidence_count == 0:
            missing.append("No evidence items registered")
        if tasks_count == 0:
            missing.append("No tasks recorded")
        if notes_count == 0:
            missing.append("No investigation notes")

        outcome = (
            self.db.query(models.CaseOutcome)
            .filter(models.CaseOutcome.case_id == case.case_id)
            .first()
        )
        if not outcome:
            missing.append("Decision/outcome not recorded")

        metadata = case.case_metadata or {}
        if metadata.get("works_council_monitoring") and metadata.get("works_council_approval_uri") is None:
            missing.append("Works Council approval missing")
        if metadata.get("evidence_locked"):
            warnings.append("Evidence folder locked pending Works Council approval")
        if case.is_anonymized:
            warnings.append("Case is anonymized; report completeness is limited")
        if case.status != "CLOSED":
            warnings.append(f"Case status is {case.status}, not CLOSED")

        total_checks = len(checks) + 5  # triage/impact/gates + subjects/evidence/tasks/notes/decision
        completed_checks = max(0, total_checks - len(missing))
        score = max(0, round((completed_checks / total_checks) * 100))
        return CaseSanityCheckOut(
            score=score,
            completed=completed_checks,
            total=total_checks,
            missing=missing,
            warnings=warnings,
        )

    def list_legal_holds(self, case_id: str, principal: Principal) -> List[CaseLegalHoldOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        holds = (
            self.db.query(models.CaseLegalHold)
            .filter(models.CaseLegalHold.case_id == case.case_id)
            .order_by(models.CaseLegalHold.created_at.desc())
            .all()
        )
        return [CaseLegalHoldOut.model_validate(hold) for hold in holds]

    def create_legal_hold(
        self,
        case_id: str,
        payload: CaseLegalHoldCreate,
        principal: Principal,
    ) -> CaseLegalHoldOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)

        contact_name = payload.contact_name.strip()
        if not contact_name:
            raise ValueError("Contact name is required.")

        contact_norm = self._normalize_person(contact_name)
        subjects = (
            self.db.query(models.CaseSubject)
            .filter(models.CaseSubject.case_id == case.case_id)
            .all()
        )
        conflicts = [
            subject.display_name
            for subject in subjects
            if contact_norm and contact_norm == self._normalize_person(subject.display_name)
        ]
        if conflicts and not payload.conflict_override_reason:
            raise ValueError("Contact matches a case subject. Provide an override reason.")

        hold_id = f"HOLD-{uuid.uuid4().hex[:8].upper()}"
        access_code = (payload.access_code or uuid.uuid4().hex[:10].upper()).strip()
        delivery_channel = (payload.delivery_channel or "SECURE_PORTAL").strip().upper()

        doc_type = "SILENT_LEGAL_HOLD"
        jurisdiction = (case.jurisdiction or "").strip().lower()
        if jurisdiction in {"us", "usa", "united states"} or "united states" in jurisdiction or "u.s." in jurisdiction:
            doc_type = "US_LEGAL_HOLD"

        title, content = render_document(
            doc_type,
            case,
            None,
            None,
            {
                "hold_id": hold_id,
                "contact_name": contact_name,
                "contact_role": payload.contact_role,
                "contact_email": payload.contact_email,
                "delivery_channel": delivery_channel,
                "preservation_scope": payload.preservation_scope,
            },
        )
        version = self._next_doc_version(case.case_id, doc_type)
        storage_uri = f"generated://{case.case_id}/{doc_type}/v{version}.txt"
        document = models.CaseDocument(
            case_id=case.case_id,
            doc_type=doc_type,
            version=version,
            format="txt",
            title=title,
            content=content,
            storage_uri=storage_uri,
            created_by=principal.subject,
        )
        self.db.add(document)
        self.db.flush()

        record = models.CaseLegalHold(
            case_id=case.case_id,
            hold_id=hold_id,
            contact_name=contact_name,
            contact_email=payload.contact_email,
            contact_role=payload.contact_role,
            preservation_scope=payload.preservation_scope,
            delivery_channel=delivery_channel,
            access_code=access_code,
            conflict_override_reason=payload.conflict_override_reason,
            conflict_override_by=principal.subject if payload.conflict_override_reason else None,
            document_id=document.id,
            created_by=principal.subject,
        )
        self.db.add(record)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="legal_hold_generated",
            actor=principal.subject,
            message="Legal hold instruction generated.",
            details={"hold_id": hold_id, "delivery_channel": delivery_channel, "doc_type": doc_type},
        )
        self.db.commit()
        self.db.refresh(record)
        return CaseLegalHoldOut.model_validate(record)

    def list_expert_access(self, case_id: str, principal: Principal) -> List[CaseExpertAccessOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        records = (
            self.db.query(models.CaseExpertAccess)
            .filter(models.CaseExpertAccess.case_id == case.case_id)
            .order_by(models.CaseExpertAccess.granted_at.desc())
            .all()
        )
        if records:
            now = datetime.now(timezone.utc)
            updated = False
            for record in records:
                if record.status == "active" and record.expires_at and record.expires_at <= now:
                    record.status = "expired"
                    record.revoked_at = now
                    record.revoked_by = "system"
                    updated = True
                    self._log_audit_event(
                        case_id=case.case_id,
                        event_type="expert_access_expired",
                        actor=principal.subject,
                        message="Expert access expired.",
                        details={"access_id": record.access_id, "expert_email": record.expert_email},
                    )
            if updated:
                self.db.commit()
        return [CaseExpertAccessOut.model_validate(record) for record in records]

    def grant_expert_access(
        self,
        case_id: str,
        payload: CaseExpertAccessCreate,
        principal: Principal,
    ) -> CaseExpertAccessOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        email = payload.expert_email.strip().lower()
        if not email:
            raise ValueError("Expert email is required.")
        existing = (
            self.db.query(models.CaseExpertAccess)
            .filter(
                models.CaseExpertAccess.case_id == case.case_id,
                models.CaseExpertAccess.expert_email == email,
                models.CaseExpertAccess.status == "active",
            )
            .first()
        )
        if existing:
            raise ValueError("An active expert access grant already exists for this email.")
        access_id = f"EXPERT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=48)
        record = models.CaseExpertAccess(
            case_id=case.case_id,
            access_id=access_id,
            expert_email=email,
            expert_name=payload.expert_name,
            organization=payload.organization,
            reason=payload.reason,
            status="active",
            granted_by=principal.subject,
            granted_at=now,
            expires_at=expires_at,
        )
        self.db.add(record)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="expert_access_granted",
            actor=principal.subject,
            message="Expert access granted.",
            details={
                "access_id": access_id,
                "expert_email": email,
                "expires_at": expires_at.isoformat(),
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return CaseExpertAccessOut.model_validate(record)

    def revoke_expert_access(self, case_id: str, access_id: str, principal: Principal) -> CaseExpertAccessOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        record = (
            self.db.query(models.CaseExpertAccess)
            .filter(
                models.CaseExpertAccess.case_id == case.case_id,
                models.CaseExpertAccess.access_id == access_id,
            )
            .first()
        )
        if not record:
            raise ValueError("Expert access record not found.")
        if record.status != "revoked":
            record.status = "revoked"
            record.revoked_at = datetime.now(timezone.utc)
            record.revoked_by = principal.subject
            self._log_audit_event(
                case_id=case.case_id,
                event_type="expert_access_revoked",
                actor=principal.subject,
                message="Expert access revoked.",
                details={"access_id": record.access_id, "expert_email": record.expert_email},
            )
            self.db.commit()
        self.db.refresh(record)
        return CaseExpertAccessOut.model_validate(record)

    def create_triage_ticket(self, payload: CaseTriageTicketCreate, tenant_key: str) -> CaseTriageTicketOut:
        subject = (payload.subject or "").strip() or "General inquiry"
        message = payload.message.strip()
        reporter_name = (payload.reporter_name or "").strip() or None
        reporter_email = (payload.reporter_email or "").strip() or None
        source = (payload.source or "dropbox").strip() or "dropbox"
        ticket_id = f"TRIAGE-{uuid.uuid4().hex[:8].upper()}"

        record = models.CaseTriageTicket(
            ticket_id=ticket_id,
            tenant_key=tenant_key or "default",
            subject=subject,
            message=message,
            reporter_name=reporter_name,
            reporter_email=reporter_email,
            source=source,
            status="new",
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return CaseTriageTicketOut.model_validate(record)

    def list_triage_tickets(
        self,
        principal: Principal,
        status: str | None = None,
    ) -> List[CaseTriageTicketOut]:
        tenant_key = principal.tenant_key or "default"
        query = self.db.query(models.CaseTriageTicket).filter(models.CaseTriageTicket.tenant_key == tenant_key)
        if status:
            query = query.filter(models.CaseTriageTicket.status == status.strip().lower())
        tickets = query.order_by(models.CaseTriageTicket.created_at.desc()).all()
        return [CaseTriageTicketOut.model_validate(ticket) for ticket in tickets]

    def update_triage_ticket(
        self,
        ticket_id: str,
        payload: CaseTriageTicketUpdate,
        principal: Principal,
    ) -> CaseTriageTicketOut:
        record = self._get_triage_ticket(ticket_id, principal)
        updates = payload.model_dump(exclude_unset=True)
        if "status" in updates and updates["status"]:
            record.status = updates["status"]
        if "triage_notes" in updates:
            record.triage_notes = updates.get("triage_notes")
        self.db.commit()
        self.db.refresh(record)
        return CaseTriageTicketOut.model_validate(record)

    def convert_triage_ticket(
        self,
        ticket_id: str,
        payload: CaseTriageTicketConvert,
        principal: Principal,
    ) -> CaseOut:
        record = self._get_triage_ticket(ticket_id, principal)
        if record.linked_case_id:
            case = self._get_case_or_raise(record.linked_case_id, principal=principal)
            return self._serialize_case(case)

        title = (payload.case_title or record.subject or "Triage case").strip()
        summary = (payload.case_summary or record.message or "").strip() or None
        create_payload = CaseCreate(
            title=title,
            summary=summary,
            jurisdiction=payload.jurisdiction,
            vip_flag=payload.vip_flag,
        )
        case = self.create_case(create_payload, principal)
        record.linked_case_id = case.case_id
        record.status = "triaged"
        self.db.commit()
        return case

    def draft_case_summary(self, case_id: str, principal: Principal) -> CaseSummaryDraftOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        notes = (
            self.db.query(models.CaseNote)
            .filter(models.CaseNote.case_id == case.case_id)
            .order_by(models.CaseNote.created_at.asc())
            .all()
        )
        now = datetime.now(timezone.utc)
        if not notes:
            summary = (
                "Draft summary (auto-generated).\n"
                "No investigation notes available yet. Add notes and retry."
            )
            return CaseSummaryDraftOut(summary=summary, note_count=0, generated_at=now)

        max_lines = int(os.getenv("IRMMF_SUMMARY_MAX_LINES", "12"))
        lines: list[str] = []
        for note in notes:
            snippet = (note.body or "").strip().replace("\n", " ")
            snippet = re.sub(r"\s+", " ", snippet)
            if len(snippet) > 160:
                snippet = snippet[:157].rsplit(" ", 1)[0] + "..."
            date_label = note.created_at.date().isoformat()
            lines.append(f"{date_label} · {note.note_type}: {snippet}")

        trimmed = lines[:max_lines]
        if len(lines) > max_lines:
            trimmed.append(f"...({len(lines) - max_lines} more notes)")

        header = (
            "Draft summary (auto-generated from case notes). Review for accuracy and legal tone.\n"
            f"Case: {case.case_id} · Generated {now.date().isoformat()}\n"
        )
        summary = header + "\n".join(trimmed)
        return CaseSummaryDraftOut(summary=summary, note_count=len(notes), generated_at=now)

    def suggest_redactions(self, case_id: str, principal: Principal) -> List[CaseRedactionSuggestionOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        sources: list[tuple[str, str]] = []

        if case.summary:
            sources.append(("case_summary", case.summary))

        subjects = (
            self.db.query(models.CaseSubject)
            .filter(models.CaseSubject.case_id == case.case_id)
            .all()
        )
        for subject in subjects:
            sources.append(("subject_name", subject.display_name))
            if subject.reference:
                sources.append(("subject_reference", subject.reference))
            if subject.manager_name:
                sources.append(("manager_name", subject.manager_name))

        notes = (
            self.db.query(models.CaseNote)
            .filter(models.CaseNote.case_id == case.case_id)
            .all()
        )
        for note in notes:
            sources.append((f"note:{note.note_type}", note.body))

        evidence = (
            self.db.query(models.CaseEvidenceItem)
            .filter(models.CaseEvidenceItem.case_id == case.case_id)
            .all()
        )
        for item in evidence:
            sources.append(("evidence_label", item.label))
            sources.append(("evidence_source", item.source))
            if item.link:
                sources.append(("evidence_link", item.link))

        tasks = (
            self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .all()
        )
        for task in tasks:
            sources.append(("task_title", task.title))
            if task.assignee:
                sources.append(("task_assignee", task.assignee))

        reporter_messages = (
            self.db.query(models.CaseReporterMessage)
            .filter(models.CaseReporterMessage.case_id == case.case_id)
            .all()
        )
        for msg in reporter_messages:
            sources.append(("reporter_message", msg.body))

        documents = (
            self.db.query(models.CaseDocument)
            .filter(models.CaseDocument.case_id == case.case_id)
            .all()
        )
        for doc in documents:
            content = doc.content or {}
            text = content.get("rendered_text")
            if text:
                sources.append((f"document:{doc.doc_type}", str(text)))

        patterns = [
            ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
            ("phone", re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b")),
            ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
            ("ip_address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
        ]
        suggestions: dict[str, CaseRedactionSuggestionOut] = {}

        def _add(value: str, match_type: str, source: str, reason: str) -> None:
            key = f"{match_type}:{value}"
            if key in suggestions:
                return
            suggestions[key] = CaseRedactionSuggestionOut(
                value=value,
                match_type=match_type,
                source=source,
                reason=reason,
            )

        for source, text in sources:
            if not text:
                continue
            for match_type, pattern in patterns:
                for match in pattern.findall(text):
                    value = match.strip()
                    if not value:
                        continue
                    reason = "PII detected"
                    if match_type == "email":
                        reason = "Email address"
                    elif match_type == "phone":
                        reason = "Phone number"
                    elif match_type == "ssn":
                        reason = "Government ID"
                    elif match_type == "ip_address":
                        reason = "IP address"
                    _add(value, match_type, source, reason)

        return list(suggestions.values())

    def get_consistency_insights(self, case_id: str, principal: Principal) -> CaseConsistencyOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        tenant_key = case.tenant_key or "default"
        playbook_key = None

        events = (
            self.db.query(models.CaseAuditEvent)
            .filter(
                models.CaseAuditEvent.case_id == case.case_id,
                models.CaseAuditEvent.event_type == "playbook_applied",
            )
            .order_by(models.CaseAuditEvent.created_at.desc())
            .all()
        )
        for event in events:
            detail_key = (event.details or {}).get("playbook_key")
            if detail_key:
                playbook_key = str(detail_key)
                break

        base_query = (
            self.db.query(models.CaseOutcome.outcome)
            .join(models.Case, models.Case.case_id == models.CaseOutcome.case_id)
            .filter(models.Case.tenant_key == tenant_key)
            .filter(models.Case.case_id != case.case_id)
            .filter(models.Case.jurisdiction == case.jurisdiction)
        )

        if playbook_key:
            related_case_ids: set[str] = set()
            all_events = (
                self.db.query(models.CaseAuditEvent.case_id, models.CaseAuditEvent.details)
                .filter(models.CaseAuditEvent.event_type == "playbook_applied")
                .all()
            )
            for case_id_value, details in all_events:
                if not details:
                    continue
                if details.get("playbook_key") == playbook_key:
                    related_case_ids.add(case_id_value)
            if related_case_ids:
                base_query = base_query.filter(models.CaseOutcome.case_id.in_(related_case_ids))

        outcomes = [row[0] for row in base_query.all()]
        total = len(outcomes)
        counts: dict[str, int] = {}
        for outcome in outcomes:
            normalized = (outcome or "UNKNOWN").upper()
            counts[normalized] = counts.get(normalized, 0) + 1

        stats: list[CaseOutcomeStat] = []
        for outcome, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
            percent = round((count / total) * 100, 1) if total else 0.0
            stats.append(CaseOutcomeStat(outcome=outcome, count=count, percent=percent))

        if total == 0:
            recommendation = "No historical outcomes available for similar cases yet."
        else:
            top = stats[0]
            recommendation = f"Most common outcome for similar cases is {top.outcome} ({top.percent}%)."

        warning = None
        if total < 3:
            warning = "Limited historical data; treat this as directional only."

        return CaseConsistencyOut(
            sample_size=total,
            jurisdiction=case.jurisdiction,
            playbook_key=playbook_key,
            outcomes=stats,
            recommendation=recommendation,
            warning=warning,
        )

    def list_reporter_messages(self, case_id: str, principal: Principal) -> List[CaseReporterMessageOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        messages = (
            self.db.query(models.CaseReporterMessage)
            .filter(models.CaseReporterMessage.case_id == case.case_id)
            .order_by(models.CaseReporterMessage.created_at.asc())
            .all()
        )
        return [CaseReporterMessageOut.model_validate(message) for message in messages]

    def add_reporter_message(
        self,
        case_id: str,
        payload: CaseReporterMessageCreate,
        principal: Principal,
    ) -> CaseReporterMessageOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        body = payload.body.strip()
        if not body:
            raise ValueError("Message body cannot be empty.")
        message = models.CaseReporterMessage(
            case_id=case.case_id,
            sender="investigator",
            body=body,
            created_by=principal.subject,
        )
        self.db.add(message)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="reporter_message_sent",
            actor=principal.subject,
            message="Reporter portal message sent.",
            details={"sender": "investigator"},
        )
        self.db.commit()
        self.db.refresh(message)
        return CaseReporterMessageOut.model_validate(message)

    def get_reporter_portal(self, reporter_key: str) -> dict:
        reporter_key = (reporter_key or "").strip()
        case = (
            self.db.query(models.Case)
            .filter(models.Case.reporter_key == reporter_key)
            .first()
        )
        if not case:
            raise ValueError("Reporter key not found.")
        messages = (
            self.db.query(models.CaseReporterMessage)
            .filter(models.CaseReporterMessage.case_id == case.case_id)
            .order_by(models.CaseReporterMessage.created_at.asc())
            .all()
        )
        return {
            "case_id": case.case_id,
            "external_report_id": case.external_report_id,
            "messages": [CaseReporterMessageOut.model_validate(message).model_dump() for message in messages],
        }

    def get_reporter_portal_by_case(self, case_id: str, reporter_key: str) -> dict:
        reporter_key = (reporter_key or "").strip()
        case_id = (case_id or "").strip()
        if not reporter_key or not case_id:
            raise ValueError("Case ID and token are required.")
        case = (
            self.db.query(models.Case)
            .filter(models.Case.case_id == case_id)
            .filter(models.Case.reporter_key == reporter_key)
            .first()
        )
        if not case:
            raise ValueError("Case token not found.")
        messages = (
            self.db.query(models.CaseReporterMessage)
            .filter(models.CaseReporterMessage.case_id == case.case_id)
            .order_by(models.CaseReporterMessage.created_at.asc())
            .all()
        )
        return {
            "case_id": case.case_id,
            "external_report_id": case.external_report_id,
            "messages": [CaseReporterMessageOut.model_validate(message).model_dump() for message in messages],
        }

    def post_reporter_portal_message(self, reporter_key: str, payload: CaseReporterMessageCreate) -> CaseReporterMessageOut:
        reporter_key = (reporter_key or "").strip()
        case = (
            self.db.query(models.Case)
            .filter(models.Case.reporter_key == reporter_key)
            .first()
        )
        if not case:
            raise ValueError("Reporter key not found.")
        body = payload.body.strip()
        if not body:
            raise ValueError("Message body cannot be empty.")
        message = models.CaseReporterMessage(
            case_id=case.case_id,
            sender="reporter",
            body=body,
            created_by=None,
        )
        self.db.add(message)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="reporter_message_received",
            actor="reporter",
            message="Reporter portal message received.",
            details={"sender": "reporter"},
        )
        self.db.commit()
        self.db.refresh(message)
        return CaseReporterMessageOut.model_validate(message)

    def post_reporter_portal_message_by_case(
        self,
        case_id: str,
        reporter_key: str,
        payload: CaseReporterMessageCreate,
    ) -> CaseReporterMessageOut:
        reporter_key = (reporter_key or "").strip()
        case_id = (case_id or "").strip()
        if not reporter_key or not case_id:
            raise ValueError("Case ID and token are required.")
        case = (
            self.db.query(models.Case)
            .filter(models.Case.case_id == case_id)
            .filter(models.Case.reporter_key == reporter_key)
            .first()
        )
        if not case:
            raise ValueError("Case token not found.")
        body = payload.body.strip()
        if not body:
            raise ValueError("Message body cannot be empty.")
        message = models.CaseReporterMessage(
            case_id=case.case_id,
            sender="reporter",
            body=body,
            created_by=None,
        )
        self.db.add(message)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="reporter_message_received",
            actor="reporter",
            message="Reporter portal message received.",
            details={"sender": "reporter"},
        )
        self.db.commit()
        self.db.refresh(message)
        return CaseReporterMessageOut.model_validate(message)

    def add_link(self, case_id: str, payload: CaseLinkCreate, principal: Principal) -> CaseLinkOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        if case.case_id == payload.linked_case_id:
            raise ValueError("Cannot link a case to itself.")

        linked_case = self._get_case_or_raise(payload.linked_case_id, principal=principal)
        self._ensure_not_anonymized(linked_case)
        relation = payload.relation_type
        reciprocal = self._relation_reciprocal(relation)

        existing = (
            self.db.query(models.CaseLink)
            .filter(models.CaseLink.case_id == case.case_id)
            .filter(models.CaseLink.linked_case_id == linked_case.case_id)
            .filter(models.CaseLink.relation_type == relation)
            .first()
        )
        if existing:
            return CaseLinkOut.model_validate(existing)

        link = models.CaseLink(
            case_id=case.case_id,
            linked_case_id=linked_case.case_id,
            relation_type=relation,
            created_by=principal.subject,
        )
        self.db.add(link)

        reciprocal_existing = (
            self.db.query(models.CaseLink)
            .filter(models.CaseLink.case_id == linked_case.case_id)
            .filter(models.CaseLink.linked_case_id == case.case_id)
            .filter(models.CaseLink.relation_type == reciprocal)
            .first()
        )
        if not reciprocal_existing:
            self.db.add(
                models.CaseLink(
                    case_id=linked_case.case_id,
                    linked_case_id=case.case_id,
                    relation_type=reciprocal,
                    created_by=principal.subject,
                )
            )

        self._log_audit_event(
            case_id=case.case_id,
            event_type="case_linked",
            actor=principal.subject,
            message="Case link created.",
            details={"linked_case_id": linked_case.case_id, "relation_type": relation},
        )
        self._log_audit_event(
            case_id=linked_case.case_id,
            event_type="case_linked",
            actor=principal.subject,
            message="Case link created.",
            details={"linked_case_id": case.case_id, "relation_type": reciprocal},
        )
        self.db.commit()
        self.db.refresh(link)
        return CaseLinkOut.model_validate(link)

    def remove_link(self, case_id: str, link_id: int, principal: Principal) -> CaseLinkOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        link = (
            self.db.query(models.CaseLink)
            .filter(models.CaseLink.id == link_id)
            .first()
        )
        if not link or link.case_id != case.case_id:
            raise ValueError("Case link not found.")

        reciprocal = self._relation_reciprocal(link.relation_type)
        self.db.query(models.CaseLink).filter(
            models.CaseLink.case_id == link.linked_case_id,
            models.CaseLink.linked_case_id == link.case_id,
            models.CaseLink.relation_type == reciprocal,
        ).delete(synchronize_session=False)
        self.db.delete(link)

        self._log_audit_event(
            case_id=case.case_id,
            event_type="case_unlinked",
            actor=principal.subject,
            message="Case link removed.",
            details={"linked_case_id": link.linked_case_id, "relation_type": link.relation_type},
        )
        self._log_audit_event(
            case_id=link.linked_case_id,
            event_type="case_unlinked",
            actor=principal.subject,
            message="Case link removed.",
            details={"linked_case_id": case.case_id, "relation_type": reciprocal},
        )
        self.db.commit()
        return CaseLinkOut.model_validate(link)

    def list_suggestions(self, case_id: str, principal: Principal) -> List[CaseEvidenceSuggestionOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        suggestions = (
            self.db.query(models.CaseEvidenceSuggestion)
            .filter(models.CaseEvidenceSuggestion.case_id == case.case_id)
            .order_by(models.CaseEvidenceSuggestion.created_at.desc())
            .all()
        )
        return [CaseEvidenceSuggestionOut.model_validate(item) for item in suggestions]

    def list_documents(self, case_id: str, principal: Principal) -> List[CaseDocumentOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        documents = (
            self.db.query(models.CaseDocument)
            .filter(models.CaseDocument.case_id == case.case_id)
            .order_by(models.CaseDocument.created_at.desc())
            .all()
        )
        self._log_audit_event(
            case_id=case.case_id,
            event_type="document_list_viewed",
            actor=principal.subject,
            message="Document list viewed.",
            details={"count": len(documents)},
        )
        self.db.commit()
        return [CaseDocumentOut.model_validate(doc) for doc in documents]

    def create_document(
        self,
        case_id: str,
        doc_type: str,
        payload: CaseDocumentCreate,
        principal: Principal,
    ) -> CaseDocumentOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        normalized = doc_type.strip().upper()
        format_value = normalize_document_format(payload.format)

        if normalized == "DISMISSAL_REASONS_LETTER" and not self._is_legal(principal):
            raise ValueError("Legal approval required to generate dismissal reasons letter.")

        gate_data = None
        if normalized == "INVESTIGATION_MANDATE":
            gate_data = self._gate_data(case.case_id, "legitimacy")
        if normalized == "INTERVIEW_INVITATION":
            gate_data = self._gate_data(case.case_id, "adversarial")

        extra_data = None
        proven_facts_note = None
        if normalized == "DISMISSAL_REASONS_LETTER":
            self._enforce_dismissal_window(case)
            proven_facts_note = self._latest_note_by_types(case.case_id, ["proven_facts", "proven facts"])
            if not proven_facts_note:
                raise ValueError("Proven facts note required before generating dismissal reasons letter.")

            last_doc = (
                self.db.query(models.CaseDocument)
                .filter(models.CaseDocument.case_id == case.case_id)
                .filter(models.CaseDocument.doc_type == normalized)
                .order_by(models.CaseDocument.version.desc())
                .first()
            )
            if last_doc and proven_facts_note.created_at > last_doc.created_at and not self._is_legal(principal):
                raise ValueError("Legal approval required to regenerate dismissal reasons letter.")

        if normalized == "INVESTIGATION_REPORT":
            extra_data = self._build_report_payload(case)

        title, content = render_document(normalized, case, gate_data, proven_facts_note, extra_data)
        version = self._next_doc_version(case.case_id, normalized)
        storage_uri = f"generated://{case.case_id}/{normalized}/v{version}.{format_value}"
        document = models.CaseDocument(
            case_id=case.case_id,
            doc_type=normalized,
            version=version,
            format=format_value,
            title=title,
            content=content,
            storage_uri=storage_uri,
            created_by=principal.subject,
        )
        self.db.add(document)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="document_generated",
            actor=principal.subject,
            message=f"Document generated: {normalized}.",
            details={"doc_type": normalized, "version": version, "format": format_value},
        )
        self.db.commit()
        self.db.refresh(document)
        return CaseDocumentOut.model_validate(document)

    def download_document(self, case_id: str, doc_id: int, principal: Principal) -> tuple[str, bytes, str]:
        case = self._get_case_or_raise(case_id, principal=principal)
        document = (
            self.db.query(models.CaseDocument)
            .filter(models.CaseDocument.case_id == case.case_id)
            .filter(models.CaseDocument.id == doc_id)
            .first()
        )
        if not document:
            raise ValueError("Document not found")
        content = document.content or {}
        rendered_text = content.get("rendered_text") or ""
        format_value = normalize_document_format(document.format)
        filename = f"{document.doc_type.lower()}_v{document.version}.{format_value}"
        payload, media_type = render_document_bytes(format_value, rendered_text)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="document_downloaded",
            actor=principal.subject,
            message="Document downloaded.",
            details={"doc_id": document.id, "doc_type": document.doc_type, "version": document.version},
        )
        self.db.commit()
        return filename, payload, media_type

    def export_pack(self, case_id: str, principal: Principal) -> bytes:
        import io
        import json
        import zipfile

        case = self._get_case_or_raise(case_id, principal=principal)
        evidence = self.db.query(models.CaseEvidenceItem).filter(models.CaseEvidenceItem.case_id == case.case_id).all()
        tasks = self.db.query(models.CaseTask).filter(models.CaseTask.case_id == case.case_id).all()
        notes = self.db.query(models.CaseNote).filter(models.CaseNote.case_id == case.case_id).all()
        gates = self.db.query(models.CaseGateRecord).filter(models.CaseGateRecord.case_id == case.case_id).all()
        documents = self.db.query(models.CaseDocument).filter(models.CaseDocument.case_id == case.case_id).all()
        legal_holds = self.db.query(models.CaseLegalHold).filter(models.CaseLegalHold.case_id == case.case_id).all()
        experts = self.db.query(models.CaseExpertAccess).filter(models.CaseExpertAccess.case_id == case.case_id).all()
        reporter_messages = (
            self.db.query(models.CaseReporterMessage)
            .filter(models.CaseReporterMessage.case_id == case.case_id)
            .all()
        )
        audits = self.db.query(models.CaseAuditEvent).filter(models.CaseAuditEvent.case_id == case.case_id).all()

        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)

        export_payload = {
            "case": self._serialize_case(case).model_dump(),
            "evidence": [CaseEvidenceOut.model_validate(item).model_dump() for item in evidence],
            "tasks": [CaseTaskOut.model_validate(item).model_dump() for item in tasks],
            "notes": [CaseNoteOut.model_validate(item).model_dump() for item in notes],
            "gates": [CaseGateRecordOut.model_validate(item).model_dump() for item in gates],
            "documents": [CaseDocumentOut.model_validate(item).model_dump() for item in documents],
            "legal_holds": [CaseLegalHoldOut.model_validate(item).model_dump() for item in legal_holds],
            "experts": [CaseExpertAccessOut.model_validate(item).model_dump() for item in experts],
            "reporter_messages": [CaseReporterMessageOut.model_validate(item).model_dump() for item in reporter_messages],
            "redaction_log": self._latest_redaction_log(case.case_id),
            "audit_events": [CaseAuditEventOut.model_validate(item).model_dump() for item in audits],
        }

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("case.json", json.dumps(export_payload, default=serialize, indent=2))
            for doc in documents:
                content = doc.content or {}
                rendered_text = content.get("rendered_text") or ""
                format_value = normalize_document_format(doc.format)
                payload, _ = render_document_bytes(format_value, rendered_text)
                filename = f"documents/{doc.doc_type.lower()}_v{doc.version}.{format_value}"
                zf.writestr(filename, payload)

        self._log_audit_event(
            case_id=case.case_id,
            event_type="export_generated",
            actor=principal.subject,
            message="Export pack generated.",
        )
        self.db.commit()
        buffer.seek(0)
        return buffer.read()

    def export_redacted_pack(
        self,
        case_id: str,
        payload: CaseExportRedactionCreate,
        principal: Principal,
    ) -> bytes:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        redaction_payload = {
            "note": payload.note,
            "redactions": payload.redactions,
            "created_by": principal.subject,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        version = self._next_doc_version(case.case_id, "EXPORT_REDACTION_LOG")
        document = models.CaseDocument(
            case_id=case.case_id,
            doc_type="EXPORT_REDACTION_LOG",
            version=version,
            format="json",
            title="Export Redaction Log",
            content={"redaction_log": redaction_payload},
            redaction_log=redaction_payload,
            storage_uri=f"generated://{case.case_id}/EXPORT_REDACTION_LOG/v{version}.json",
            created_by=principal.subject,
        )
        self.db.add(document)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="export_redaction_logged",
            actor=principal.subject,
            message="Export redaction log recorded.",
            details={"version": version},
        )
        self.db.commit()
        return self.export_pack(case.case_id, principal)

    def export_remediation(
        self,
        case_id: str,
        payload: CaseRemediationExportCreate,
        principal: Principal,
    ) -> tuple[str, str, bytes]:
        import csv
        import io
        import json

        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        outcome = (
            self.db.query(models.CaseOutcome)
            .filter(models.CaseOutcome.case_id == case.case_id)
            .first()
        )
        if not outcome:
            raise ValueError("Decision/outcome required before remediation export.")
        if outcome.outcome == "NO_SANCTION":
            raise ValueError("Remediation export requires a proven outcome (not NO_SANCTION).")

        statement = (payload.remediation_statement or "").strip()
        metadata = case.case_metadata or {}
        if not statement:
            statement = (metadata.get("remediation_statement") or "").strip()
        if not statement:
            raise ValueError("Remediation statement required for export.")

        export_format = (payload.format or "json").strip().lower()
        if export_format not in ("json", "csv"):
            raise ValueError("Unsupported remediation export format. Use json or csv.")

        exported_at = datetime.now(timezone.utc).isoformat()
        metadata.update(
            {
                "remediation_statement": statement,
                "remediation_exported_at": exported_at,
                "remediation_export_format": export_format,
            }
        )
        case.case_metadata = metadata
        self._log_audit_event(
            case_id=case.case_id,
            event_type="remediation_exported",
            actor=principal.subject,
            message="Remediation export generated.",
            details={"format": export_format},
        )
        self.db.commit()

        payload_dict = {
            "case_id": case.case_id,
            "case_uuid": str(case.case_uuid),
            "jurisdiction": case.jurisdiction,
            "case_title": case.title,
            "case_summary": case.summary,
            "outcome": outcome.outcome,
            "decision": outcome.decision,
            "decided_at": outcome.decided_at.isoformat() if outcome.decided_at else None,
            "remediation_statement": statement,
            "exported_at": exported_at,
        }

        if export_format == "csv":
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=list(payload_dict.keys()))
            writer.writeheader()
            writer.writerow(payload_dict)
            content = buffer.getvalue().encode("utf-8")
            filename = f"{case.case_id}_remediation.csv"
            return filename, "text/csv", content

        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        content = json.dumps(payload_dict, default=serialize, indent=2).encode("utf-8")
        filename = f"{case.case_id}_remediation.json"
        return filename, "application/json", content

    def set_decision(self, case_id: str, payload: CaseDecisionCreate, principal: Principal) -> CaseOutcomeOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        conflicts = self._role_separation_conflicts(case, principal)
        if conflicts:
            if not payload.role_separation_override_reason:
                raise ValueError(
                    "Role separation conflict detected. Provide an override reason with LEGAL approval."
                )
            if not self._is_legal(principal):
                raise ValueError("Role separation override requires LEGAL approval.")
        record = (
            self.db.query(models.CaseOutcome)
            .filter(models.CaseOutcome.case_id == case.case_id)
            .first()
        )
        if not record:
            record = models.CaseOutcome(case_id=case.case_id)
            self.db.add(record)
        record.outcome = payload.outcome.strip().upper()
        record.decision = payload.decision
        record.summary = payload.summary
        record.decided_by = principal.subject
        record.decided_at = payload.decided_at or datetime.now(timezone.utc)
        record.role_separation_override_reason = payload.role_separation_override_reason
        record.role_separation_override_by = principal.subject if payload.role_separation_override_reason else None
        self._apply_jurisdiction_decision_warning(case, record.decided_at)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="decision_recorded",
            actor=principal.subject,
            message="Decision recorded.",
            details={
                "outcome": record.outcome,
                "role_separation_override": bool(payload.role_separation_override_reason),
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return CaseOutcomeOut.model_validate(record)

    def get_decision(self, case_id: str, principal: Principal) -> CaseOutcomeOut | None:
        case = self._get_case_or_raise(case_id, principal=principal)
        record = (
            self.db.query(models.CaseOutcome)
            .filter(models.CaseOutcome.case_id == case.case_id)
            .first()
        )
        if not record:
            return None
        return CaseOutcomeOut.model_validate(record)

    def approve_erasure(self, case_id: str, payload: CaseErasureApprove, principal: Principal) -> CaseErasureJobOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        outcome = (
            self.db.query(models.CaseOutcome)
            .filter(models.CaseOutcome.case_id == case.case_id)
            .first()
        )
        if not outcome or outcome.outcome != "NO_SANCTION":
            raise ValueError("Erasure can only be approved for NO_SANCTION cases.")
        job = (
            self.db.query(models.CaseErasureJob)
            .filter(models.CaseErasureJob.case_id == case.case_id)
            .first()
        )
        now = datetime.now(timezone.utc)
        execute_after = payload.execute_after
        if not execute_after:
            settings = self._get_tenant_settings(case.tenant_key)
            retention_days = settings.retention_days if settings else 30
            execute_after = now + timedelta(days=retention_days)

        if not job:
            job = models.CaseErasureJob(case_id=case.case_id)
            self.db.add(job)
        job.status = "approved"
        job.approved_by = principal.subject
        job.approved_at = now
        job.execute_after = execute_after
        case.status = "ERASURE_PENDING"
        self._log_audit_event(
            case_id=case.case_id,
            event_type="erasure_approved",
            actor=principal.subject,
            message="Erasure approved.",
            details={"execute_after": execute_after.isoformat()},
        )
        self.db.commit()
        self.db.refresh(job)
        return CaseErasureJobOut.model_validate(job)

    def execute_erasure(self, case_id: str, payload: CaseErasureExecute, principal: Principal) -> CaseErasureJobOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        job = (
            self.db.query(models.CaseErasureJob)
            .filter(models.CaseErasureJob.case_id == case.case_id)
            .first()
        )
        if not job or job.status not in {"approved", "pending"}:
            raise ValueError("Erasure is not approved.")
        now = datetime.now(timezone.utc)
        case.status = "ERASED"
        case.is_anonymized = True
        case.anonymized_at = now
        self._erase_case_data(case, reason=payload.reason or "Erasure executed.")

        title, content = render_document("ERASURE_CERTIFICATE", case, None, None)
        cert = models.CaseDocument(
            case_id=case.case_id,
            doc_type="ERASURE_CERTIFICATE",
            version=self._next_doc_version(case.case_id, "ERASURE_CERTIFICATE"),
            format="txt",
            title=title,
            content=content,
            storage_uri=f"generated://{case.case_id}/ERASURE_CERTIFICATE/v1.txt",
            created_by=principal.subject,
        )
        self.db.add(cert)
        self.db.flush()

        job.status = "executed"
        job.executed_at = now
        job.certificate_doc_id = cert.id

        self._log_audit_event(
            case_id=case.case_id,
            event_type="erasure_executed",
            actor=principal.subject,
            message="Erasure executed.",
            details={"certificate_doc_id": cert.id},
        )
        self.db.commit()
        self.db.refresh(job)
        return CaseErasureJobOut.model_validate(job)

    def update_suggestion(
        self,
        case_id: str,
        suggestion_id: str,
        payload: CaseEvidenceSuggestionUpdate,
        principal: Principal,
    ) -> CaseEvidenceSuggestionOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        suggestion = (
            self.db.query(models.CaseEvidenceSuggestion)
            .filter(models.CaseEvidenceSuggestion.case_id == case.case_id)
            .filter(models.CaseEvidenceSuggestion.suggestion_id == suggestion_id)
            .first()
        )
        if not suggestion:
            raise ValueError("Suggestion not found")
        suggestion.status = payload.status
        self._log_audit_event(
            case_id=case.case_id,
            event_type="suggestion_updated",
            actor=principal.subject,
            message="Evidence suggestion updated.",
            details={"suggestion_id": suggestion_id, "status": payload.status},
        )
        self.db.commit()
        self.db.refresh(suggestion)
        return CaseEvidenceSuggestionOut.model_validate(suggestion)

    def convert_suggestion(self, case_id: str, suggestion_id: str, principal: Principal) -> CaseEvidenceOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        self._ensure_evidence_unlocked(case)
        suggestion = (
            self.db.query(models.CaseEvidenceSuggestion)
            .filter(models.CaseEvidenceSuggestion.case_id == case.case_id)
            .filter(models.CaseEvidenceSuggestion.suggestion_id == suggestion_id)
            .first()
        )
        if not suggestion:
            raise ValueError("Suggestion not found")
        evidence = models.CaseEvidenceItem(
            case_id=case.case_id,
            evidence_id=f"EVD-{uuid.uuid4().hex[:6].upper()}",
            label=suggestion.label,
            source=suggestion.source,
            link=None,
            notes=suggestion.description,
            status="registered",
        )
        suggestion.status = "converted"
        self.db.add(evidence)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="suggestion_converted",
            actor=principal.subject,
            message="Suggestion converted to evidence.",
            details={"suggestion_id": suggestion_id, "evidence_id": evidence.evidence_id},
        )
        self.db.commit()
        self.db.refresh(evidence)
        return CaseEvidenceOut.model_validate(evidence)

    def add_note(self, case_id: str, payload: CaseNoteCreate, principal: Principal) -> CaseNoteOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        settings = self._get_tenant_settings(case.tenant_key)
        matched_terms: list[str] = []
        if settings and settings.keyword_flagging_enabled:
            matched_terms = self._scan_for_keywords(payload.body, settings.keyword_list or [])
        note = models.CaseNote(
            case_id=case.case_id,
            note_type=(payload.note_type or "general").strip().lower(),
            body=payload.body.strip(),
            created_by=principal.subject,
            flags={"keyword_matches": matched_terms, "requires_review": bool(matched_terms)},
        )
        self.db.add(note)
        self.db.flush()
        if matched_terms:
            flag = models.CaseContentFlag(
                case_id=case.case_id,
                note_id=note.id,
                flag_type="keyword",
                terms=matched_terms,
                status="open",
            )
            self.db.add(flag)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="note_added",
            actor=principal.subject,
            message="Case note added.",
            details={"note_type": note.note_type, "keyword_matches": matched_terms},
        )
        self.db.commit()
        self.db.refresh(note)
        return CaseNoteOut.model_validate(note)

    def list_notes(self, case_id: str, principal: Principal) -> List[CaseNoteOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        notes = (
            self.db.query(models.CaseNote)
            .filter(models.CaseNote.case_id == case.case_id)
            .order_by(models.CaseNote.created_at.desc())
            .all()
        )
        return [CaseNoteOut.model_validate(note) for note in notes]

    def list_flags(self, case_id: str, principal: Principal) -> List[CaseContentFlagOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        flags = (
            self.db.query(models.CaseContentFlag)
            .filter(models.CaseContentFlag.case_id == case.case_id)
            .order_by(models.CaseContentFlag.created_at.desc())
            .all()
        )
        return [CaseContentFlagOut.model_validate(flag) for flag in flags]

    def update_flag(
        self,
        case_id: str,
        flag_id: int,
        payload: CaseContentFlagUpdate,
        principal: Principal,
    ) -> CaseContentFlagOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        flag = (
            self.db.query(models.CaseContentFlag)
            .filter(models.CaseContentFlag.case_id == case.case_id)
            .filter(models.CaseContentFlag.id == flag_id)
            .first()
        )
        if not flag:
            raise ValueError("Flag not found")
        flag.status = payload.status
        flag.resolved_by = principal.subject
        flag.resolved_at = datetime.now(timezone.utc)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="flag_updated",
            actor=principal.subject,
            message="Content flag updated.",
            details={"flag_id": flag_id, "status": payload.status},
        )
        self.db.commit()
        self.db.refresh(flag)
        return CaseContentFlagOut.model_validate(flag)

    def list_audit_events(
        self,
        case_id: str,
        principal: Principal,
        *,
        actor: str | None = None,
    ) -> List[CaseAuditEventOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        query = self.db.query(models.CaseAuditEvent).filter(models.CaseAuditEvent.case_id == case.case_id)
        if actor:
            query = query.filter(models.CaseAuditEvent.actor == actor)
        events = query.order_by(models.CaseAuditEvent.created_at.desc()).all()
        return [CaseAuditEventOut.model_validate(event) for event in events]

    def save_gate(self, case_id: str, gate_key: str, payload: dict, principal: Principal) -> CaseGateRecordOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        validated = self._validate_gate(gate_key, payload)
        if gate_key == "legal" and not self._is_legal(principal):
            raise ValueError("Legal approval required.")
        if gate_key == "credentialing":
            self._enforce_credentialing_rules(case, validated, principal)
        if gate_key == "legal":
            approved_at = (validated.get("approved_at") or "").strip()
            validated["approved_at"] = approved_at or datetime.now(timezone.utc).isoformat()
            note = (validated.get("approval_note") or "").strip()
            validated["approval_note"] = note or None
            validated["approved_by"] = principal.subject
        if gate_key == "works_council":
            monitoring = bool(validated.get("monitoring"))
            approval_uri = (validated.get("approval_document_uri") or "").strip() or None
            approved_at = (validated.get("approval_received_at") or "").strip()
            if approval_uri and not approved_at:
                validated["approval_received_at"] = datetime.now(timezone.utc).isoformat()
            metadata = case.case_metadata or {}
            if monitoring and not approval_uri:
                metadata["evidence_locked"] = True
            elif approval_uri:
                metadata["evidence_locked"] = False
            metadata["works_council_monitoring"] = monitoring
            metadata["works_council_approval_uri"] = approval_uri
            case.case_metadata = metadata
            if monitoring and not approval_uri:
                title, content = render_document(
                    "WORKS_COUNCIL_REQUEST",
                    case,
                    None,
                    None,
                    {
                        "monitoring": monitoring,
                        "summary": (case.summary or "").strip() or "Investigation monitoring requested.",
                        "requested_by": principal.subject,
                    },
                )
                version = self._next_doc_version(case.case_id, "WORKS_COUNCIL_REQUEST")
                storage_uri = f"generated://{case.case_id}/WORKS_COUNCIL_REQUEST/v{version}.txt"
                document = models.CaseDocument(
                    case_id=case.case_id,
                    doc_type="WORKS_COUNCIL_REQUEST",
                    version=version,
                    format="txt",
                    title=title,
                    content=content,
                    storage_uri=storage_uri,
                    created_by=principal.subject,
                )
                self.db.add(document)
        record = (
            self.db.query(models.CaseGateRecord)
            .filter(models.CaseGateRecord.case_id == case.case_id)
            .filter(models.CaseGateRecord.gate_key == gate_key)
            .first()
        )
        now = datetime.now(timezone.utc)
        if record:
            record.data = validated
            record.status = "completed"
            record.completed_by = principal.subject
            record.completed_at = now
        else:
            record = models.CaseGateRecord(
                case_id=case.case_id,
                gate_key=gate_key,
                status="completed",
                data=validated,
                completed_by=principal.subject,
                completed_at=now,
            )
            self.db.add(record)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="gate_saved",
            actor=principal.subject,
            message=f"Gate {gate_key} saved.",
            details={"gate_key": gate_key},
        )
        self.db.commit()
        self.db.refresh(record)
        return CaseGateRecordOut.model_validate(record)

    def list_gates(self, case_id: str, principal: Principal) -> List[CaseGateRecordOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        records = (
            self.db.query(models.CaseGateRecord)
            .filter(models.CaseGateRecord.case_id == case.case_id)
            .order_by(models.CaseGateRecord.updated_at.desc())
            .all()
        )
        return [CaseGateRecordOut.model_validate(record) for record in records]

    def set_serious_cause(self, case_id: str, payload: CaseSeriousCauseUpsert, principal: Principal) -> CaseSeriousCauseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        if not case.serious_cause_enabled:
            raise ValueError("Serious cause is not enabled for this case.")
        record = (
            self.db.query(models.CaseSeriousCause)
            .filter(models.CaseSeriousCause.case_id == case.case_id)
            .first()
        )
        now = datetime.now(timezone.utc)
        if not record:
            record = models.CaseSeriousCause(case_id=case.case_id)
            self.db.add(record)
        record.enabled = True
        record.enabled = payload.enabled
        record.override_reason = payload.override_reason
        if payload.override_reason:
            record.override_by = principal.subject

        jurisdiction_rule = self._get_jurisdiction_profile(case)

        clock_started = record.facts_confirmed_at is None
        facts_confirmed_at = payload.facts_confirmed_at or record.facts_confirmed_at
        if payload.enabled and not facts_confirmed_at:
            facts_confirmed_at = now
        record.facts_confirmed_at = facts_confirmed_at

        if payload.decision_due_at:
            record.decision_due_at = payload.decision_due_at
        elif facts_confirmed_at:
            record.decision_due_at = self._calculate_deadline(
                case,
                facts_confirmed_at,
                jurisdiction_rule,
                "decision_deadline_days",
                "decision_deadline_hours",
                fallback_days=3,
            )

        if payload.dismissal_due_at:
            record.dismissal_due_at = payload.dismissal_due_at
        elif record.decision_due_at:
            record.dismissal_due_at = self._calculate_deadline(
                case,
                record.decision_due_at,
                jurisdiction_rule,
                "dismissal_deadline_days",
                "dismissal_deadline_hours",
                fallback_days=3,
            )

        self._log_audit_event(
            case_id=case.case_id,
            event_type="serious_cause_updated",
            actor=principal.subject,
            message="Serious cause record updated.",
        )
        if payload.enabled and clock_started and record.facts_confirmed_at:
            self._log_audit_event(
                case_id=case.case_id,
                event_type="serious_cause_clock_started",
                actor=principal.subject,
                message="Serious-cause clock started.",
                details={"facts_confirmed_at": record.facts_confirmed_at.isoformat()},
            )

        self.db.commit()
        self.db.refresh(record)
        return CaseSeriousCauseOut.model_validate(record)

    def get_serious_cause(self, case_id: str, principal: Principal) -> CaseSeriousCauseOut | None:
        case = self._get_case_or_raise(case_id, principal=principal)
        if not case.serious_cause_enabled:
            return None
        record = (
            self.db.query(models.CaseSeriousCause)
            .filter(models.CaseSeriousCause.case_id == case.case_id)
            .first()
        )
        if not record:
            return None
        return CaseSeriousCauseOut.model_validate(record)

    def toggle_serious_cause(
        self,
        case_id: str,
        payload: CaseSeriousCauseToggle,
        principal: Principal,
    ) -> CaseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        case.serious_cause_enabled = payload.enabled
        case.date_incident_occurred = payload.date_incident_occurred
        case.date_investigation_started = payload.date_investigation_started
        case_metadata = case.case_metadata or {}
        if payload.decision_maker:
            if self._normalize_person(payload.decision_maker) == self._normalize_person(self._investigator_name(case)):
                raise ValueError("Decision maker cannot be the assigned investigator.")
            case_metadata["decision_maker"] = payload.decision_maker
        case.case_metadata = case_metadata
        if not payload.enabled:
            self.db.query(models.CaseSeriousCause).filter(models.CaseSeriousCause.case_id == case.case_id).delete()
        self._log_audit_event(
            case_id=case.case_id,
            event_type="serious_cause_toggle",
            actor=principal.subject,
            message="Serious cause toggle updated.",
            details={"enabled": payload.enabled},
        )
        if not payload.enabled:
            self._log_audit_event(
                case_id=case.case_id,
                event_type="serious_cause_clock_stopped",
                actor=principal.subject,
                message="Serious-cause clock stopped.",
            )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def submit_findings(self, case_id: str, payload: CaseSubmitFindings, principal: Principal) -> CaseSeriousCauseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        if not case.serious_cause_enabled:
            raise ValueError("Serious cause is not enabled for this case.")
        record = (
            self.db.query(models.CaseSeriousCause)
            .filter(models.CaseSeriousCause.case_id == case.case_id)
            .first()
        )
        if not record:
            record = models.CaseSeriousCause(case_id=case.case_id)
            self.db.add(record)
        clock_started = record.facts_confirmed_at is None
        confirmed_at = payload.confirmed_at or datetime.now(timezone.utc)
        record.facts_confirmed_at = confirmed_at
        jurisdiction_rule = self._get_jurisdiction_profile(case)
        record.decision_due_at = self._calculate_deadline(
            case,
            confirmed_at,
            jurisdiction_rule,
            "decision_deadline_days",
            "decision_deadline_hours",
            fallback_days=3,
        )
        record.dismissal_due_at = self._calculate_deadline(
            case,
            record.decision_due_at,
            jurisdiction_rule,
            "dismissal_deadline_days",
            "dismissal_deadline_hours",
            fallback_days=3,
        )
        case_metadata = case.case_metadata or {}
        if payload.decision_maker:
            if self._normalize_person(payload.decision_maker) == self._normalize_person(self._investigator_name(case)):
                raise ValueError("Decision maker cannot be the assigned investigator.")
            case_metadata["decision_maker"] = payload.decision_maker
            case.case_metadata = case_metadata
        self._log_audit_event(
            case_id=case.case_id,
            event_type="serious_cause_findings_submitted",
            actor=principal.subject,
            message="Findings submitted to decision maker.",
            details={"facts_confirmed_at": confirmed_at.isoformat()},
        )
        if clock_started:
            self._log_audit_event(
                case_id=case.case_id,
                event_type="serious_cause_clock_started",
                actor=principal.subject,
                message="Serious-cause clock started.",
                details={"facts_confirmed_at": confirmed_at.isoformat()},
            )
        self._create_serious_cause_notifications(case, record)
        self.db.commit()
        self.db.refresh(record)
        return CaseSeriousCauseOut.model_validate(record)

    def record_dismissal(
        self,
        case_id: str,
        payload: CaseRecordDismissal,
        principal: Principal,
    ) -> CaseSeriousCauseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        record = self._get_serious_cause_or_raise(case_id, principal)
        self._ensure_missed_deadline_ack(record)
        self._enforce_dismissal_window(case)
        record.dismissal_recorded_at = payload.dismissal_recorded_at or datetime.now(timezone.utc)
        self._log_audit_event(
            case_id=record.case_id,
            event_type="serious_cause_dismissal_recorded",
            actor=principal.subject,
            message="Dismissal recorded.",
            details={"dismissal_recorded_at": record.dismissal_recorded_at.isoformat()},
        )
        self.db.commit()
        self.db.refresh(record)
        return CaseSeriousCauseOut.model_validate(record)

    def record_reasons_sent(
        self,
        case_id: str,
        payload: CaseRecordReasonsSent,
        principal: Principal,
    ) -> CaseSeriousCauseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        record = self._get_serious_cause_or_raise(case_id, principal)
        self._ensure_missed_deadline_ack(record)
        record.reasons_sent_at = payload.sent_at or datetime.now(timezone.utc)
        record.reasons_delivery_method = payload.delivery_method or "STANDARD"
        record.reasons_delivery_proof_uri = payload.proof_uri
        jurisdiction_rule = self._get_jurisdiction_profile(case)
        if jurisdiction_rule.get("requires_registered_mail_receipt") and record.reasons_delivery_method != "REGISTERED_MAIL":
            raise ValueError("Registered mail is required for dismissal reasons in this jurisdiction.")
        if record.reasons_delivery_method == "REGISTERED_MAIL" and not record.reasons_delivery_proof_uri:
            raise ValueError("Registered mail requires proof of posting.")
        self._log_audit_event(
            case_id=record.case_id,
            event_type="serious_cause_reasons_sent",
            actor=principal.subject,
            message="Dismissal reasons sent.",
            details={"delivery_method": record.reasons_delivery_method},
        )
        self.db.commit()
        self.db.refresh(record)
        return CaseSeriousCauseOut.model_validate(record)

    def acknowledge_missed_deadline(
        self,
        case_id: str,
        payload: CaseAcknowledgeMissed,
        principal: Principal,
    ) -> CaseSeriousCauseOut:
        record = self._get_serious_cause_or_raise(case_id, principal)
        record.missed_acknowledged_at = datetime.now(timezone.utc)
        record.missed_acknowledged_by = principal.subject
        record.missed_acknowledged_reason = payload.reason
        self._log_audit_event(
            case_id=record.case_id,
            event_type="serious_cause_missed_ack",
            actor=principal.subject,
            message="Missed deadline acknowledged.",
            details={"reason": payload.reason},
        )
        self.db.commit()
        self.db.refresh(record)
        return CaseSeriousCauseOut.model_validate(record)

    def list_notifications(
        self,
        tenant_key: str,
        case_id: str | None = None,
    ) -> List[CaseNotificationOut]:
        query = self.db.query(models.CaseNotification).filter(models.CaseNotification.tenant_key == tenant_key)
        if case_id:
            query = query.filter(models.CaseNotification.case_id == case_id)
        notifications = query.order_by(models.CaseNotification.created_at.desc()).all()
        now = datetime.now(timezone.utc)
        updated = False
        for item in notifications:
            if item.status == "pending" and item.due_at and item.due_at <= now:
                item.status = "sent"
                item.sent_at = now
                updated = True
                self._log_audit_event(
                    case_id=item.case_id,
                    event_type="notification_sent",
                    actor="system",
                    message="Notification sent.",
                    details={"notification_type": item.notification_type, "severity": item.severity},
                )
        if updated:
            self.db.commit()
        return [CaseNotificationOut.model_validate(item) for item in notifications]

    def acknowledge_notification(
        self,
        notification_id: int,
        principal: Principal,
    ) -> CaseNotificationOut:
        notification = (
            self.db.query(models.CaseNotification)
            .filter(models.CaseNotification.id == notification_id)
            .first()
        )
        if not notification:
            raise ValueError("Notification not found.")
        if notification.tenant_key != (principal.tenant_key or "default"):
            raise ValueError("Notification not found.")
        notification.status = "acknowledged"
        notification.acknowledged_at = datetime.now(timezone.utc)
        notification.acknowledged_by = principal.subject
        self._log_audit_event(
            case_id=notification.case_id,
            event_type="notification_acknowledged",
            actor=principal.subject,
            message="Notification acknowledged.",
            details={"notification_type": notification.notification_type, "severity": notification.severity},
        )
        self.db.commit()
        self.db.refresh(notification)
        return CaseNotificationOut.model_validate(notification)

    def anonymize_case(
        self,
        case_id: str,
        principal: Principal,
        reason: str | None = None,
    ) -> CaseOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        case.title = "Anonymized case"
        case.summary = None
        case.created_by = None
        case.company_id = None
        case.external_report_id = None
        case.reporter_channel_id = None
        case.reporter_key = None
        case.vip_flag = False
        case.case_metadata = {"anonymized_reason": reason}
        case.status = "ERASED"
        case.is_anonymized = True
        case.anonymized_at = datetime.now(timezone.utc)
        case.serious_cause_enabled = False
        case.date_incident_occurred = None
        case.date_investigation_started = None

        self.db.query(models.CaseSubject).filter(models.CaseSubject.case_id == case.case_id).delete()
        self.db.query(models.CaseEvidenceItem).filter(models.CaseEvidenceItem.case_id == case.case_id).delete()
        self.db.query(models.CaseTask).filter(models.CaseTask.case_id == case.case_id).delete()
        self.db.query(models.CaseNote).filter(models.CaseNote.case_id == case.case_id).delete()
        self.db.query(models.CaseContentFlag).filter(models.CaseContentFlag.case_id == case.case_id).delete()
        self.db.query(models.CaseGateRecord).filter(models.CaseGateRecord.case_id == case.case_id).delete()
        self.db.query(models.CaseSeriousCause).filter(models.CaseSeriousCause.case_id == case.case_id).delete()
        self.db.query(models.CaseEvidenceSuggestion).filter(models.CaseEvidenceSuggestion.case_id == case.case_id).delete()
        self.db.query(models.CaseDocument).filter(models.CaseDocument.case_id == case.case_id).delete()
        self.db.query(models.CaseLegalHold).filter(models.CaseLegalHold.case_id == case.case_id).delete()
        self.db.query(models.CaseExpertAccess).filter(models.CaseExpertAccess.case_id == case.case_id).delete()
        self.db.query(models.CaseReporterMessage).filter(models.CaseReporterMessage.case_id == case.case_id).delete()
        self.db.query(models.CaseLink).filter(
            or_(
                models.CaseLink.case_id == case.case_id,
                models.CaseLink.linked_case_id == case.case_id,
            )
        ).delete(synchronize_session=False)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="case_anonymized",
            actor=principal.subject,
            message="Case anonymized.",
            details={"reason": reason},
        )

        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def break_glass(
        self,
        case_id: str,
        payload: CaseBreakGlassRequest,
        principal: Principal,
    ) -> dict:
        case = self._get_case_or_raise(case_id, principal=principal)
        duration = payload.duration_minutes or 60
        duration = min(480, max(15, duration))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=duration)
        details = {
            "reason": payload.reason,
            "scope": payload.scope,
            "duration_minutes": duration,
            "expires_at": expires_at.isoformat(),
        }
        self._log_audit_event(
            case_id=case.case_id,
            event_type="break_glass",
            actor=principal.subject,
            message="Break-glass access granted.",
            details=details,
        )
        self.db.commit()
        return {"status": "ok", "expires_at": expires_at}

    def _get_case_or_raise(
        self,
        case_id: str,
        tenant_key: str | None = None,
        principal: Principal | None = None,
    ) -> models.Case:
        effective_tenant = tenant_key or (principal.tenant_key if principal else None)
        case = (
            self.db.query(models.Case)
            .filter(models.Case.case_id == case_id)
            .first()
        )
        if not case:
            raise ValueError("Case not found")
        if effective_tenant and case.tenant_key != effective_tenant:
            raise ValueError("Case not found")
        if principal:
            self._ensure_jurisdiction_access(case.jurisdiction, principal)
            self._ensure_vip_access(case, principal)
        return case

    def _serialize_case(self, case: models.Case) -> CaseOut:
        subjects = (
            self.db.query(models.CaseSubject)
            .filter(models.CaseSubject.case_id == case.case_id)
            .order_by(models.CaseSubject.created_at.desc())
            .all()
        )
        evidence = (
            self.db.query(models.CaseEvidenceItem)
            .filter(models.CaseEvidenceItem.case_id == case.case_id)
            .order_by(models.CaseEvidenceItem.created_at.desc())
            .all()
        )
        tasks = (
            self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .order_by(models.CaseTask.created_at.desc())
            .all()
        )
        notes = (
            self.db.query(models.CaseNote)
            .filter(models.CaseNote.case_id == case.case_id)
            .order_by(models.CaseNote.created_at.desc())
            .all()
        )
        gates = (
            self.db.query(models.CaseGateRecord)
            .filter(models.CaseGateRecord.case_id == case.case_id)
            .order_by(models.CaseGateRecord.updated_at.desc())
            .all()
        )
        serious_cause = (
            self.db.query(models.CaseSeriousCause)
            .filter(models.CaseSeriousCause.case_id == case.case_id)
            .first()
        )
        outcome = (
            self.db.query(models.CaseOutcome)
            .filter(models.CaseOutcome.case_id == case.case_id)
            .first()
        )
        erasure_job = (
            self.db.query(models.CaseErasureJob)
            .filter(models.CaseErasureJob.case_id == case.case_id)
            .first()
        )
        metadata = case.case_metadata or {}
        return CaseOut(
            case_id=case.case_id,
            case_uuid=str(case.case_uuid),
            tenant_key=case.tenant_key,
            company_id=case.company_id,
            title=case.title,
            summary=case.summary,
            jurisdiction=case.jurisdiction,
            vip_flag=case.vip_flag,
            external_report_id=case.external_report_id,
            reporter_channel_id=case.reporter_channel_id,
            reporter_key=case.reporter_key,
            status=case.status,
            stage=case.stage,
            created_by=case.created_by,
            is_anonymized=case.is_anonymized,
            anonymized_at=case.anonymized_at,
            serious_cause_enabled=case.serious_cause_enabled,
            date_incident_occurred=case.date_incident_occurred,
            date_investigation_started=case.date_investigation_started,
            remediation_statement=metadata.get("remediation_statement"),
            remediation_exported_at=metadata.get("remediation_exported_at"),
            urgent_dismissal=metadata.get("urgent_dismissal"),
            subject_suspended=metadata.get("subject_suspended"),
            evidence_locked=metadata.get("evidence_locked"),
            created_at=case.created_at,
            updated_at=case.updated_at,
            subjects=[CaseSubjectOut.model_validate(subject) for subject in subjects],
            evidence=[CaseEvidenceOut.model_validate(item) for item in evidence],
            tasks=[CaseTaskOut.model_validate(task) for task in tasks],
            notes=[CaseNoteOut.model_validate(note) for note in notes],
            gates=[CaseGateRecordOut.model_validate(gate) for gate in gates],
            serious_cause=CaseSeriousCauseOut.model_validate(serious_cause) if serious_cause else None,
            outcome=CaseOutcomeOut.model_validate(outcome) if outcome else None,
            erasure_job=CaseErasureJobOut.model_validate(erasure_job) if erasure_job else None,
        )

    def _ensure_not_anonymized(self, case: models.Case) -> None:
        if case.is_anonymized:
            raise ValueError("Cannot modify an anonymized case.")

    def _validate_stage_transition(self, case: models.Case, target_stage: str) -> None:
        current = case.stage
        if target_stage == current:
            return
        allowed = STAGE_FLOW.get(current)
        if not allowed or target_stage not in allowed:
            raise TransitionError(
                code="INVALID_TRANSITION",
                message=f"Cannot move from {current} to {target_stage}.",
                blockers=[{"code": "invalid_transition", "from": current, "to": target_stage}],
            )
        blockers: list[dict] = []
        gate_key = STAGE_GATES.get((current, target_stage))
        if gate_key and not self._gate_completed(case.case_id, gate_key):
            blockers.append(
                {
                    "code": "missing_gate",
                    "gate": gate_key,
                    "message": f"Complete the {gate_key} gate before advancing.",
                }
            )
        if current == "INVESTIGATION" and target_stage == "ADVERSARIAL_DEBATE":
            evidence_count = (
                self.db.query(models.CaseEvidenceItem)
                .filter(models.CaseEvidenceItem.case_id == case.case_id)
                .count()
            )
            if evidence_count == 0:
                blockers.append(
                    {
                        "code": "missing_evidence",
                        "message": "At least one evidence item is required before adversarial debate.",
                    }
                )
            works_gate = self._gate_data(case.case_id, "works_council")
            if works_gate.get("monitoring") and not works_gate.get("approval_document_uri"):
                blockers.append(
                    {
                        "code": "works_council_pending",
                        "message": "Works Council approval required before advancing.",
                    }
                )
        if current == "DECISION" and target_stage == "CLOSURE":
            outcome = (
                self.db.query(models.CaseOutcome)
                .filter(models.CaseOutcome.case_id == case.case_id)
                .first()
            )
            if not outcome:
                blockers.append(
                    {
                        "code": "missing_decision",
                        "message": "Decision/outcome required before closure.",
                    }
                )
        if blockers:
            raise TransitionError(code="GATE_BLOCKED", message="Gate requirements not met.", blockers=blockers)

    def _gate_completed(self, case_id: str, gate_key: str) -> bool:
        record = (
            self.db.query(models.CaseGateRecord)
            .filter(models.CaseGateRecord.case_id == case_id)
            .filter(models.CaseGateRecord.gate_key == gate_key)
            .first()
        )
        return bool(record and record.status == "completed")

    def _validate_gate(self, gate_key: str, payload: dict) -> dict:
        validator = GATE_VALIDATORS.get(gate_key)
        if not validator:
            raise ValueError("Unknown gate.")
        return validator(**payload).model_dump()

    def _get_tenant_settings(self, tenant_key: str | None) -> tenant_models.TenantSettings | None:
        if not tenant_key:
            return None
        tenant = (
            self.db.query(tenant_models.Tenant)
            .filter(tenant_models.Tenant.tenant_key == tenant_key)
            .first()
        )
        return tenant.settings if tenant else None

    def _get_jurisdiction_rules(self, tenant_key: str | None) -> dict:
        settings = self._get_tenant_settings(tenant_key)
        if settings and settings.jurisdiction_rules is not None:
            return settings.jurisdiction_rules
        return tenant_models._default_jurisdiction_rules()

    def _resolve_jurisdiction_code(self, jurisdiction: str | None) -> str:
        if not jurisdiction:
            return "BE"
        value = jurisdiction.strip()
        if not value:
            return "BE"
        normalized = value.upper()
        mapping = {
            "BE": "BE",
            "BELGIUM": "BE",
            "BELGIQUE": "BE",
            "NL": "NL",
            "NETHERLANDS": "NL",
            "HOLLAND": "NL",
            "LU": "LU",
            "LUXEMBOURG": "LU",
            "IE": "IE",
            "IRELAND": "IE",
            "UK": "UK",
            "UNITED KINGDOM": "UK",
            "US": "US",
            "UNITED STATES": "US",
            "EU": "EU",
            "EU (NON-BELGIUM)": "EU",
        }
        if normalized in mapping:
            return mapping[normalized]
        if "BELGIUM" in normalized:
            return "BE"
        if "NETHERLANDS" in normalized or "HOLLAND" in normalized:
            return "NL"
        if "LUXEMBOURG" in normalized:
            return "LU"
        if "IRELAND" in normalized:
            return "IE"
        if "UNITED KINGDOM" in normalized:
            return "UK"
        if "UNITED STATES" in normalized:
            return "US"
        if "EU" in normalized:
            return "EU"
        return normalized

    def _get_jurisdiction_profile(self, case: models.Case) -> dict:
        rules = self._get_jurisdiction_rules(case.tenant_key)
        if not rules:
            return {}
        code = self._resolve_jurisdiction_code(case.jurisdiction)
        if code in rules:
            return rules.get(code) or {}
        if code.upper() in rules:
            return rules.get(code.upper()) or {}
        if code.lower() in rules:
            return rules.get(code.lower()) or {}
        return {}

    def _parse_gate_datetime(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _normalize_person(self, value: str | None) -> str:
        if not value:
            return ""
        cleaned = re.sub(r"\s+", " ", value.strip().lower())
        return cleaned

    def _dev_bypass_access(self) -> bool:
        return os.getenv("DEV_RBAC_DISABLED", "1").lower() in ("1", "true", "yes")

    def _requires_be_authorization(self, jurisdiction: str | None) -> bool:
        return self._resolve_jurisdiction_code(jurisdiction) == "BE"

    def _ensure_jurisdiction_access(self, jurisdiction: str | None, principal: Principal) -> None:
        if self._dev_bypass_access():
            return
        if not self._requires_be_authorization(jurisdiction):
            return
        roles = [role.upper() for role in (principal.roles or [])]
        if "BE_AUTHORIZED" in roles or "ADMIN" in roles:
            return
        raise ValueError("Case not found")

    def _ensure_vip_access(self, case: models.Case, principal: Principal) -> None:
        if self._dev_bypass_access():
            return
        if not getattr(case, "vip_flag", False):
            return
        if self._is_legal(principal):
            return
        if principal.subject and case.created_by and principal.subject == case.created_by:
            return
        raise ValueError("Case not found")

    def _can_view_case(self, case: models.Case, principal: Principal) -> bool:
        try:
            self._ensure_jurisdiction_access(case.jurisdiction, principal)
            self._ensure_vip_access(case, principal)
        except ValueError:
            return False
        return True

    def _schedule_retaliation_task(self, case: models.Case, principal: Principal) -> None:
        existing = (
            self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .filter(models.CaseTask.task_type == "retaliation_check")
            .first()
        )
        if existing:
            return
        due_at = datetime.now(timezone.utc) + timedelta(days=90)
        task = models.CaseTask(
            case_id=case.case_id,
            task_id=f"TASK-{uuid.uuid4().hex[:6].upper()}",
            title="Retaliation check-in (3 months)",
            description="Automated follow-up after case closure.",
            task_type="retaliation_check",
            status="open",
            due_at=due_at,
        )
        self.db.add(task)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="retaliation_task_scheduled",
            actor=principal.subject,
            message="Retaliation monitoring task scheduled.",
            details={"task_id": task.task_id, "due_at": due_at.isoformat()},
        )

    def _relation_reciprocal(self, relation: str) -> str:
        normalized = relation.strip().upper()
        if normalized == "PARENT":
            return "CHILD"
        if normalized == "CHILD":
            return "PARENT"
        return normalized

    def _investigator_name(self, case: models.Case) -> str:
        gate_data = self._gate_data(case.case_id, "credentialing")
        return (gate_data.get("investigator_name") or "").strip()

    def _enforce_credentialing_rules(
        self,
        case: models.Case,
        validated: dict,
        principal: Principal,
    ) -> None:
        investigator = self._normalize_person(validated.get("investigator_name"))
        if not investigator:
            return
        subjects = (
            self.db.query(models.CaseSubject)
            .filter(models.CaseSubject.case_id == case.case_id)
            .all()
        )
        conflicts = []
        for subject in subjects:
            if investigator and investigator == self._normalize_person(subject.display_name):
                conflicts.append(subject.display_name)
            if subject.manager_name and investigator == self._normalize_person(subject.manager_name):
                conflicts.append(f"{subject.manager_name} (manager)")
        if conflicts and not validated.get("conflict_override_reason"):
            raise ValueError(
                "Conflict detected: investigator matches a case subject or manager. "
                "Provide an override reason or assign a different investigator."
            )
        if not validated.get("conflict_check_passed") and not validated.get("conflict_override_reason"):
            raise ValueError("Conflict check failed. Provide an override reason or assign a different investigator.")

        settings = self._get_tenant_settings(case.tenant_key)
        if settings and settings.investigation_mode.lower() == "systematic":
            if not validated.get("licensed"):
                raise ValueError(
                    "Systematic investigations require a licensed investigator. "
                    "Update credentials or switch investigation mode in tenant settings."
                )
            if not validated.get("license_id"):
                raise ValueError("Licensed investigator requires a license ID for systematic investigations.")

        if conflicts:
            validated["conflict_detected"] = conflicts
        if validated.get("conflict_override_reason"):
            validated["conflict_override_by"] = principal.subject
            validated["conflict_override_at"] = datetime.now(timezone.utc).isoformat()

    def _enforce_role_separation(self, case: models.Case, principal: Principal) -> None:
        conflicts = self._role_separation_conflicts(case, principal)
        if "decision_maker_matches_investigator" in conflicts:
            raise ValueError("Decision maker cannot be the assigned investigator.")
        if "investigator_recording_decision" in conflicts:
            raise ValueError("Investigator cannot record the final decision.")

    def _role_separation_conflicts(self, case: models.Case, principal: Principal) -> list[str]:
        conflicts: list[str] = []
        investigator = self._normalize_person(self._investigator_name(case))
        if not investigator:
            return conflicts
        decision_maker = self._normalize_person((case.case_metadata or {}).get("decision_maker"))
        if decision_maker and decision_maker == investigator:
            conflicts.append("decision_maker_matches_investigator")
        if investigator == self._normalize_person(principal.subject):
            conflicts.append("investigator_recording_decision")
        return conflicts

    def _calculate_deadline(
        self,
        case: models.Case,
        start: datetime,
        rule: dict,
        days_key: str,
        hours_key: str,
        fallback_days: int = 3,
    ) -> datetime:
        deadline_type = (rule.get("deadline_type") or "working_days").lower()
        hours_value = rule.get(hours_key)
        if hours_value is None and deadline_type == "hours":
            days_value = rule.get(days_key) or rule.get("serious_cause_deadline_days") or fallback_days
            hours_value = int(days_value) * 24
        if hours_value is not None:
            return start + timedelta(hours=int(hours_value))

        days_value = rule.get(days_key) or rule.get("serious_cause_deadline_days") or fallback_days
        if deadline_type == "calendar_days":
            return start + timedelta(days=int(days_value))
        return self._add_business_days(case.tenant_key, start, int(days_value))

    def _enforce_dismissal_window(self, case: models.Case, now: datetime | None = None) -> None:
        rule = self._get_jurisdiction_profile(case)
        min_days = rule.get("min_cooling_off_days")
        max_days = rule.get("max_dismissal_window_days")
        if not min_days and not max_days:
            return
        gate_data = self._gate_data(case.case_id, "adversarial")
        trigger_date = self._parse_gate_datetime(gate_data.get("invitation_date"))
        if not trigger_date:
            raise ValueError("Cooling-off window requires an adversarial interview date.")
        now = now or datetime.now(timezone.utc)
        if min_days:
            earliest = trigger_date + timedelta(days=int(min_days))
            if now < earliest:
                raise ValueError(f"Cooling-off period active until {earliest.isoformat()}.")
        if max_days:
            latest = trigger_date + timedelta(days=int(max_days))
            if now > latest:
                raise ValueError(f"Dismissal window expired on {latest.isoformat()}.")

    def _apply_jurisdiction_decision_warning(self, case: models.Case, decided_at: datetime | None) -> None:
        rule = self._get_jurisdiction_profile(case)
        warn_hours = rule.get("warn_if_decision_under_hours")
        if not warn_hours or not decided_at:
            return
        if not self._notifications_enabled(case.tenant_key):
            return
        gate_data = self._gate_data(case.case_id, "adversarial")
        trigger_date = self._parse_gate_datetime(gate_data.get("invitation_date"))
        if not trigger_date:
            return
        hours_since = (decided_at - trigger_date).total_seconds() / 3600
        if hours_since < float(warn_hours):
            self._create_notification(
                case=case,
                notification_type="jurisdiction_warning",
                message=(
                    "Natural justice warning: decision recorded within the cooling-off window. "
                    "Ensure representations were considered."
                ),
                severity="warning",
                recipient_role="LEGAL",
                status="sent",
            )
        # Integration pending: enforce appeal checkbox once decision UI captures it.

    def _notifications_enabled(self, tenant_key: str | None) -> bool:
        settings = self._get_tenant_settings(tenant_key)
        if not settings:
            return True
        return settings.notifications_enabled

    def _serious_cause_notifications_enabled(self, tenant_key: str | None) -> bool:
        settings = self._get_tenant_settings(tenant_key)
        if not settings:
            return True
        return settings.notifications_enabled and settings.serious_cause_notifications_enabled

    def _create_notification(
        self,
        case: models.Case,
        notification_type: str,
        message: str,
        severity: str = "info",
        recipient_role: str | None = None,
        due_at: datetime | None = None,
        status: str = "pending",
    ) -> models.CaseNotification:
        notification = models.CaseNotification(
            case_id=case.case_id,
            tenant_key=case.tenant_key or "default",
            notification_type=notification_type,
            severity=severity,
            message=message,
            recipient_role=recipient_role,
            status=status,
            due_at=due_at,
            sent_at=datetime.now(timezone.utc) if status == "sent" else None,
        )
        self.db.add(notification)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="notification_created",
            actor="system",
            message="Notification created.",
            details={"notification_type": notification_type, "severity": severity},
        )
        return notification

    def _create_serious_cause_notifications(
        self,
        case: models.Case,
        record: models.CaseSeriousCause,
    ) -> None:
        if not self._serious_cause_notifications_enabled(case.tenant_key):
            return
        self._create_notification(
            case=case,
            notification_type="serious_cause_clock_started",
            message="Serious cause clock started. Confirm decision and dismissal deadlines.",
            severity="info",
            recipient_role="LEGAL",
            status="sent",
        )
        for label, due_at in [("decision", record.decision_due_at), ("dismissal", record.dismissal_due_at)]:
            if not due_at:
                continue
            for hours, severity in [(48, "info"), (24, "warning")]:
                reminder_at = due_at - timedelta(hours=hours)
                self._create_notification(
                    case=case,
                    notification_type=f"serious_cause_{label}_due_{hours}h",
                    message=f"{label.title()} deadline in {hours} hours for case {case.case_id}.",
                    severity=severity,
                    recipient_role="LEGAL",
                    due_at=reminder_at,
                    status="pending",
                )

    def _get_tenant_holidays(self, tenant_key: str | None) -> list[datetime.date]:
        if not tenant_key:
            return []
        tenant = (
            self.db.query(tenant_models.Tenant)
            .filter(tenant_models.Tenant.tenant_key == tenant_key)
            .first()
        )
        if not tenant:
            return []
        holidays = (
            self.db.query(tenant_models.TenantHoliday)
            .filter(tenant_models.TenantHoliday.tenant_id == tenant.id)
            .all()
        )
        return [holiday.holiday_date for holiday in holidays]

    def _next_doc_version(self, case_id: str, doc_type: str) -> int:
        latest = (
            self.db.query(models.CaseDocument)
            .filter(models.CaseDocument.case_id == case_id)
            .filter(models.CaseDocument.doc_type == doc_type)
            .order_by(models.CaseDocument.version.desc())
            .first()
        )
        if not latest:
            return 1
        return latest.version + 1

    def _latest_redaction_log(self, case_id: str) -> dict | None:
        latest = (
            self.db.query(models.CaseDocument)
            .filter(models.CaseDocument.case_id == case_id)
            .filter(models.CaseDocument.doc_type == "EXPORT_REDACTION_LOG")
            .order_by(models.CaseDocument.version.desc())
            .first()
        )
        if not latest:
            return None
        return latest.redaction_log or (latest.content or {}).get("redaction_log")

    def _latest_note(self, case_id: str, note_type: str) -> models.CaseNote | None:
        return (
            self.db.query(models.CaseNote)
            .filter(models.CaseNote.case_id == case_id)
            .filter(models.CaseNote.note_type == note_type)
            .order_by(models.CaseNote.created_at.desc())
            .first()
        )

    def _latest_note_by_types(self, case_id: str, note_types: list[str]) -> models.CaseNote | None:
        return (
            self.db.query(models.CaseNote)
            .filter(models.CaseNote.case_id == case_id)
            .filter(models.CaseNote.note_type.in_(note_types))
            .order_by(models.CaseNote.created_at.desc())
            .first()
        )

    def _ensure_evidence_unlocked(self, case: models.Case) -> None:
        metadata = case.case_metadata or {}
        if metadata.get("evidence_locked"):
            raise ValueError("Evidence folder is locked pending Works Council approval.")

    def _build_report_payload(self, case: models.Case) -> dict:
        impact = self._gate_data(case.case_id, "impact_analysis")
        triage = self._gate_data(case.case_id, "triage")
        gates = {
            record.gate_key: record.status
            for record in (
                self.db.query(models.CaseGateRecord)
                .filter(models.CaseGateRecord.case_id == case.case_id)
                .all()
            )
        }
        outcome = (
            self.db.query(models.CaseOutcome)
            .filter(models.CaseOutcome.case_id == case.case_id)
            .first()
        )
        evidence = (
            self.db.query(models.CaseEvidenceItem)
            .filter(models.CaseEvidenceItem.case_id == case.case_id)
            .order_by(models.CaseEvidenceItem.created_at.asc())
            .limit(25)
            .all()
        )
        tasks = (
            self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .order_by(models.CaseTask.created_at.asc())
            .limit(25)
            .all()
        )
        experts = (
            self.db.query(models.CaseExpertAccess)
            .filter(models.CaseExpertAccess.case_id == case.case_id)
            .order_by(models.CaseExpertAccess.granted_at.asc())
            .limit(10)
            .all()
        )
        notes = (
            self.db.query(models.CaseNote)
            .filter(models.CaseNote.case_id == case.case_id)
            .order_by(models.CaseNote.created_at.asc())
            .limit(15)
            .all()
        )
        lessons_note = self._latest_note_by_types(
            case.case_id,
            ["lessons_learned", "lessons learned", "root_cause", "root cause"],
        )
        timeline = [
            {
                "date": note.created_at.date().isoformat(),
                "type": note.note_type,
                "summary": (note.body or "")[:140],
            }
            for note in notes
        ]
        return {
            "impact_analysis": impact,
            "triage": triage,
            "gates": gates,
            "outcome": CaseOutcomeOut.model_validate(outcome).model_dump() if outcome else {},
            "evidence": [
                {"label": item.label, "source": item.source, "status": item.status}
                for item in evidence
            ],
            "tasks": [
                {"title": task.title, "status": task.status, "assignee": task.assignee}
                for task in tasks
            ],
            "experts": [
                {
                    "email": expert.expert_email,
                    "name": expert.expert_name,
                    "organization": expert.organization,
                    "status": expert.status,
                    "expires_at": expert.expires_at.isoformat() if expert.expires_at else None,
                }
                for expert in experts
            ],
            "timeline": timeline,
            "lessons_learned": lessons_note.body if lessons_note else "",
        }

    def _gate_data(self, case_id: str, gate_key: str) -> dict:
        record = (
            self.db.query(models.CaseGateRecord)
            .filter(models.CaseGateRecord.case_id == case_id)
            .filter(models.CaseGateRecord.gate_key == gate_key)
            .first()
        )
        return record.data if record else {}

    def _is_legal(self, principal: Principal) -> bool:
        if not principal.roles:
            return False
        return "LEGAL" in principal.roles or "LEGAL_COUNSEL" in principal.roles or "ADMIN" in principal.roles

    def _add_business_days(self, tenant_key: str | None, start: datetime, days: int) -> datetime:
        settings = self._get_tenant_settings(tenant_key)
        if not settings:
            return start + timedelta(days=days)
        holidays = self._get_tenant_holidays(tenant_key)
        return add_business_days(
            start=start,
            days=days,
            weekend_days=settings.weekend_days or [5, 6],
            holidays=holidays,
            saturday_is_business_day=settings.saturday_is_business_day,
            cutoff_hour=settings.deadline_cutoff_hour,
        )

    def _scan_for_keywords(self, text: str, keywords: list[str]) -> list[str]:
        if not text or not keywords:
            return []
        lowered = text.lower()
        matched = []
        for keyword in keywords:
            cleaned = keyword.strip()
            if not cleaned:
                continue
            if cleaned.lower() in lowered:
                matched.append(cleaned)
        return matched

    def _erase_case_data(self, case: models.Case, reason: str) -> None:
        case.title = "Erased case"
        case.summary = None
        case.created_by = None
        case.company_id = None
        case.case_metadata = {"erasure_reason": reason}
        case.serious_cause_enabled = False
        case.date_incident_occurred = None
        case.date_investigation_started = None

        self.db.query(models.CaseSubject).filter(models.CaseSubject.case_id == case.case_id).delete()
        self.db.query(models.CaseEvidenceItem).filter(models.CaseEvidenceItem.case_id == case.case_id).delete()
        self.db.query(models.CaseTask).filter(models.CaseTask.case_id == case.case_id).delete()
        self.db.query(models.CaseNote).filter(models.CaseNote.case_id == case.case_id).delete()
        self.db.query(models.CaseContentFlag).filter(models.CaseContentFlag.case_id == case.case_id).delete()
        self.db.query(models.CaseGateRecord).filter(models.CaseGateRecord.case_id == case.case_id).delete()
        self.db.query(models.CaseSeriousCause).filter(models.CaseSeriousCause.case_id == case.case_id).delete()
        self.db.query(models.CaseEvidenceSuggestion).filter(models.CaseEvidenceSuggestion.case_id == case.case_id).delete()

        outcome = (
            self.db.query(models.CaseOutcome)
            .filter(models.CaseOutcome.case_id == case.case_id)
            .first()
        )
        if outcome:
            outcome.summary = None
            outcome.decision = None
            outcome.decided_by = None


    def _log_audit_event(
        self,
        case_id: str,
        event_type: str,
        message: str,
        actor: str | None = None,
        details: dict | None = None,
    ) -> None:
        details_payload = dict(details or {})
        context = get_audit_context()
        if context:
            context_payload = dict(details_payload.get("_context") or {})
            if context.ip_address:
                context_payload.setdefault("ip_address", context.ip_address)
            if context.user_agent:
                context_payload.setdefault("user_agent", context.user_agent)
            if context_payload:
                details_payload["_context"] = context_payload
            if not actor and context.actor:
                actor = context.actor
        event = models.CaseAuditEvent(
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            message=message,
            details=details_payload,
        )
        self.db.add(event)

    def _get_triage_ticket(self, ticket_id: str, principal: Principal) -> models.CaseTriageTicket:
        tenant_key = principal.tenant_key or "default"
        record = (
            self.db.query(models.CaseTriageTicket)
            .filter(models.CaseTriageTicket.ticket_id == ticket_id)
            .first()
        )
        if not record or record.tenant_key != tenant_key:
            raise ValueError("Triage ticket not found.")
        return record

    def _get_serious_cause_or_raise(self, case_id: str, principal: Principal) -> models.CaseSeriousCause:
        case = self._get_case_or_raise(case_id, principal=principal)
        if not case.serious_cause_enabled:
            raise ValueError("Serious cause is not enabled for this case.")
        record = (
            self.db.query(models.CaseSeriousCause)
            .filter(models.CaseSeriousCause.case_id == case.case_id)
            .first()
        )
        if not record:
            raise ValueError("Serious cause record not found.")
        return record

    def _ensure_missed_deadline_ack(self, record: models.CaseSeriousCause) -> None:
        if record.dismissal_due_at and datetime.now(timezone.utc) > record.dismissal_due_at:
            if not record.missed_acknowledged_at:
                raise ValueError("Deadline missed. Legal acknowledgment required.")
