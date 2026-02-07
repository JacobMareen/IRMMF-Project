from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import List

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CaseErasureApprove,
    CaseErasureExecute,
    CaseErasureJobOut,
    CaseExpertAccessCreate,
    CaseExpertAccessOut,
    CaseLegalHoldCreate,
    CaseLegalHoldOut,
)
from app.modules.cases.documents import normalize_document_format, render_document
from app.modules.cases.services.base import CaseServiceBase

class CaseLegalMixin(CaseServiceBase):
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
