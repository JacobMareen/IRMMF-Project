from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CaseContentFlagOut,
    CaseContentFlagUpdate,
    CaseNoteCreate,
    CaseNoteOut,
)
from app.modules.cases.services.base import CaseServiceBase

class CaseNoteMixin(CaseServiceBase):
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
