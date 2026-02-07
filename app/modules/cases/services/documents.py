from __future__ import annotations

import csv
import io
import json
import zipfile
import re
from datetime import datetime, timezone
from typing import List

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CaseAuditEventOut,
    CaseDocumentCreate,
    CaseDocumentOut,
    CaseEvidenceOut,
    CaseExpertAccessOut,
    CaseExportRedactionCreate,
    CaseGateRecordOut,
    CaseLegalHoldOut,
    CaseNoteOut,
    CaseRedactionSuggestionOut,
    CaseRemediationExportCreate,
    CaseReporterMessageOut,
    CaseTaskOut,
)
from app.modules.cases.documents import normalize_document_format, render_document, render_document_bytes
from app.modules.cases.services.base import CaseServiceBase

class CaseDocumentMixin(CaseServiceBase):
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
