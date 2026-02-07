from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CaseGateRecordOut,
)
from app.modules.cases.documents import render_document 
from app.modules.cases.services.base import CaseServiceBase

class CaseGateMixin(CaseServiceBase):
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
