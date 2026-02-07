from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import or_

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CaseEvidenceCreate,
    CaseEvidenceOut,
    CaseEvidenceSuggestionOut,
    CaseEvidenceSuggestionUpdate,
    CaseLinkCreate,
    CaseLinkOut,
)
from app.modules.cases.services.base import CaseServiceBase

class CaseEvidenceMixin(CaseServiceBase):
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

    def list_suggestions(self, case_id: str, principal: Principal) -> List[CaseEvidenceSuggestionOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        suggestions = (
            self.db.query(models.CaseEvidenceSuggestion)
            .filter(models.CaseEvidenceSuggestion.case_id == case.case_id)
            .order_by(models.CaseEvidenceSuggestion.created_at.desc())
            .all()
        )
        return [CaseEvidenceSuggestionOut.model_validate(item) for item in suggestions]

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

    def list_links(self, case_id: str, principal: Principal) -> List[CaseLinkOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        links = (
            self.db.query(models.CaseLink)
            .filter(models.CaseLink.case_id == case.case_id)
            .order_by(models.CaseLink.created_at.desc())
            .all()
        )
        return [CaseLinkOut.model_validate(link) for link in links]
