from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import List

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CASE_STATUSES,
    CASE_STAGES,
    CaseBreakGlassRequest,
    CaseCreate,
    CaseOut,
    CaseStatusUpdate,
    CaseSummaryDraftOut,
    CaseUpdate,
    CaseStageUpdate,
    CaseAuditEventOut,
)
from app.modules.tenant import models as tenant_models
from app.modules.cases.services.base import CaseServiceBase

class CaseCoreMixin(CaseServiceBase):
    def list_cases(self, principal: Principal) -> List[CaseOut]:
        tenant_key = principal.tenant_key or None
        query = self.db.query(models.Case)
        if tenant_key:
            query = query.filter(models.Case.tenant_key == tenant_key)
        cases = query.order_by(models.Case.created_at.desc()).all()
        visible = [case for case in cases if self._can_view_case(case, principal)]
        return [self._serialize_case(case) for case in visible]

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
            # self._schedule_retaliation_task is in CaseTaskMixin, assumed available via composition
            if hasattr(self, "_schedule_retaliation_task"):
                 self._schedule_retaliation_task(case, principal) # type: ignore
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

        self._erase_case_data(case, reason=reason or "Manual anonymization")
        
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
