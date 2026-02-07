from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import List

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CaseAcknowledgeMissed,
    CaseOut,
    CaseRecordDismissal,
    CaseRecordReasonsSent,
    CaseSeriousCauseOut,
    CaseSeriousCauseToggle,
    CaseSeriousCauseUpsert,
    CaseSubmitFindings,
)
from app.modules.cases.services.base import CaseServiceBase

class CaseSeriousCauseMixin(CaseServiceBase):
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

    def set_serious_cause(
        self,
        case_id: str,
        payload: CaseSeriousCauseUpsert,
        principal: Principal,
    ) -> CaseSeriousCauseOut:
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
        
        record.enabled = True # Implicitly true if upserting
        record.override_reason = payload.override_reason
        if payload.override_reason:
            record.override_by = principal.subject

        jurisdiction_rule = self._get_jurisdiction_profile(case)
        clock_started = record.facts_confirmed_at is None
        facts_confirmed_at = payload.facts_confirmed_at or record.facts_confirmed_at
        
        # If toggling on via this route (though toggle_serious_cause is preferred), ensure dates
        if not facts_confirmed_at and payload.enabled: 
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
        # If this call started the clock
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
            investigator = self._investigator_name(case)
            if self._normalize_person(payload.decision_maker) == self._normalize_person(investigator):
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
