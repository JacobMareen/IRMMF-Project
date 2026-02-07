from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CaseOut,
    CaseReporterMessageCreate,
    CaseReporterMessageOut,
    CaseTriageTicketConvert,
    CaseTriageTicketCreate,
    CaseTriageTicketOut,
    CaseTriageTicketUpdate,
    CaseCreate,
)
from app.modules.cases.services.base import CaseServiceBase

class CaseTriageMixin(CaseServiceBase):
    def list_triage_tickets(self, principal: Principal) -> List[CaseTriageTicketOut]:
        tenant_key = principal.tenant_key or "default"
        tickets = (
            self.db.query(models.CaseTriageTicket)
            .filter(models.CaseTriageTicket.tenant_key == tenant_key)
            .order_by(models.CaseTriageTicket.created_at.desc())
            .all()
        )
        return [CaseTriageTicketOut.model_validate(ticket) for ticket in tickets]

    def get_triage_ticket(self, ticket_id: str, principal: Principal) -> CaseTriageTicketOut:
        ticket = self._get_triage_ticket(ticket_id, principal)
        return CaseTriageTicketOut.model_validate(ticket)

    def create_triage_ticket(
        self,
        payload: CaseTriageTicketCreate,
        tenant_key: str,
    ) -> CaseTriageTicketOut:
        # Note: This method is used by external webhooks, so it does not take a Principal.
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
            source_ref=payload.source_ref,
            status="new",
            priority=payload.priority or "medium",
        )
        self.db.add(record)
        self._log_audit_event(
            case_id="system", 
            event_type="triage_ticket_created",
            actor="system",
            message="Triage ticket created via webhook.",
            details={"ticket_id": ticket_id, "subject": subject, "source": source},
        )
        self.db.commit()
        self.db.refresh(record)
        return CaseTriageTicketOut.model_validate(record)

    def update_triage_ticket(
        self,
        ticket_id: str,
        payload: CaseTriageTicketUpdate,
        principal: Principal,
    ) -> CaseTriageTicketOut:
        ticket = self._get_triage_ticket(ticket_id, principal)
        updates = payload.model_dump(exclude_unset=True)
        if updates:
            for key, value in updates.items():
                if hasattr(ticket, key):
                    setattr(ticket, key, value)
            ticket.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(ticket)
        return CaseTriageTicketOut.model_validate(ticket)

    def convert_triage_ticket(
        self,
        ticket_id: str,
        payload: CaseTriageTicketConvert,
        principal: Principal,
    ) -> CaseOut:
        ticket = self._get_triage_ticket(ticket_id, principal)
        if ticket.status == "converted":
            if ticket.linked_case_id:
                case = self._get_case_or_raise(ticket.linked_case_id, principal=principal)
                return self._serialize_case(case)
            raise ValueError("Ticket already marked converted but no case link found.")

        # Logic similar to create_case but adapted to use ticket data
        # We need to access create_case which is in CoreMixin.
        # Since this is a Mixin, we assume self.create_case exists if the class composes correctly.
        # However, purely relying on assumed method existence in type checking is tricky.
        # We can duplicate the logic or trust the composition.
        # Given this is "Refactoring", duplication is bad.
        # But `create_case` in CoreMixin takes a payload.
        
        title = (payload.case_title or ticket.subject or "Triage case").strip()
        summary = (payload.case_summary or ticket.description or ticket.message or "").strip() or None
        
        create_payload = CaseCreate(
            title=title,
            summary=summary,
            jurisdiction=payload.jurisdiction,
            vip_flag=payload.vip_flag,
            urgent_dismissal=payload.urgent_dismissal,
        )
        
        # We call the public create_case method which we assume is available on self
        # casting self to Any to avoid static check issues if run in strict mode
        case = self.create_case(create_payload, principal) # type: ignore

        ticket.status = "converted"
        ticket.linked_case_id = case.case_id
        ticket.updated_at = datetime.now(timezone.utc)
        
        self._log_audit_event(
            case_id=case.case_id,
            event_type="case_created_from_ticket",
            actor=principal.subject,
            message="Case created from triage ticket.",
            details={"ticket_id": ticket.ticket_id},
        )
        
        # We also need to add case metadata to link back
        metadata = case.case_metadata or {}
        metadata["converted_from_ticket"] = ticket.ticket_id
        case.case_metadata = metadata
        self.db.commit()
        
        return case

    def list_reporter_messages(
        self,
        case_id: str,
        principal: Principal,
    ) -> List[CaseReporterMessageOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        messages = (
            self.db.query(models.CaseReporterMessage)
            .filter(models.CaseReporterMessage.case_id == case.case_id)
            .order_by(models.CaseReporterMessage.created_at.asc())
            .all()
        )
        return [CaseReporterMessageOut.model_validate(msg) for msg in messages]

    def add_reporter_message(
        self,
        case_id: str,
        payload: CaseReporterMessageCreate,
        principal: Principal,
    ) -> CaseReporterMessageOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        msg_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
        message = models.CaseReporterMessage(
            case_id=case.case_id,
            message_id=msg_id,
            sender_role="investigator",
            sender_name=principal.subject,
            body=payload.body,
            is_internal=False,
        )
        self.db.add(message)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="reporter_message_sent",
            actor=principal.subject,
            message="Message sent to reporter.",
            details={"message_id": msg_id},
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
