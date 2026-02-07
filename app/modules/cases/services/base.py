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


class CaseServiceBase:
    def __init__(self, db: Session):
        self.db = db

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
        case.external_report_id = None
        case.reporter_channel_id = None
        case.reporter_key = None
        case.vip_flag = False
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
