"""Core case management API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from auth import get_principal, Principal
from app.db import get_db
from app.modules.cases.schemas import (
    CaseAdversarialForm,
    CaseAnonymizeRequest,
    CaseAcknowledgeMissed,
    CaseApplyPlaybook,
    CaseCreate,
    CaseContentFlagOut,
    CaseContentFlagUpdate,
    CaseEvidenceCreate,
    CaseEvidenceOut,
    CaseEvidenceSuggestionOut,
    CaseEvidenceSuggestionUpdate,
    CaseGateRecordOut,
    CaseImpactAnalysisForm,
    CaseLegalApprovalForm,
    CaseWorksCouncilForm,
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
    CaseLegalHoldCreate,
    CaseLegalHoldOut,
    CaseLegitimacyForm,
    CaseReporterMessageCreate,
    CaseReporterMessageOut,
    CaseNoteCreate,
    CaseNoteOut,
    CaseOut,
    CasePlaybookOut,
    CaseRecordDismissal,
    CaseRecordReasonsSent,
    CaseSeriousCauseOut,
    CaseSeriousCauseToggle,
    CaseSeriousCauseUpsert,
    CaseStageUpdate,
    CaseStatusUpdate,
    CaseSubjectCreate,
    CaseSubjectOut,
    CaseSubmitFindings,
    CaseTaskCreate,
    CaseTaskOut,
    CaseTaskUpdate,
    CaseCredentialingForm,
    CaseAuditEventOut,
    CaseDocumentOut,
    CaseDocumentCreate,
    CaseDecisionCreate,
    CaseOutcomeOut,
    CaseExportRedactionCreate,
    CaseRemediationExportCreate,
    CaseErasureApprove,
    CaseErasureExecute,
    CaseErasureJobOut,
    CaseUpdate,
    CaseNotificationOut,
    CaseTriageForm,
    CaseSanityCheckOut,
)
from app.modules.cases.errors import TransitionError
from app.modules.cases.service import CaseService
from app.security.rbac import require_roles


router = APIRouter()


def get_case_service(db: Session = Depends(get_db)) -> CaseService:
    return CaseService(db)


@router.post("/api/external/dropbox", response_model=CaseTriageTicketOut)
def submit_dropbox_ticket(
    payload: CaseTriageTicketCreate,
    tenant_key: str | None = Query(default=None),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.create_triage_ticket(payload, tenant_key or "default")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases", response_model=list[CaseOut])
def list_cases(
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    return service.list_cases(principal)


@router.get("/api/v1/cases/playbooks", response_model=list[CasePlaybookOut])
def list_playbooks(service: CaseService = Depends(get_case_service)):
    return service.list_playbooks()


@router.get("/api/v1/triage/inbox", response_model=list[CaseTriageTicketOut])
def list_triage_tickets(
    status: str | None = None,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR", "DPO_AUDITOR")),
    service: CaseService = Depends(get_case_service),
):
    return service.list_triage_tickets(principal, status=status)


@router.patch("/api/v1/triage/inbox/{ticket_id}", response_model=CaseTriageTicketOut)
def update_triage_ticket(
    ticket_id: str,
    payload: CaseTriageTicketUpdate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.update_triage_ticket(ticket_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/triage/inbox/{ticket_id}/convert", response_model=CaseOut)
def convert_triage_ticket(
    ticket_id: str,
    payload: CaseTriageTicketConvert,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.convert_triage_ticket(ticket_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/summary/draft", response_model=CaseSummaryDraftOut)
def draft_case_summary(
    case_id: str,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.draft_case_summary(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/redactions/suggest", response_model=list[CaseRedactionSuggestionOut])
def suggest_redactions(
    case_id: str,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR", "DPO_AUDITOR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.suggest_redactions(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/consistency", response_model=CaseConsistencyOut)
def get_consistency(
    case_id: str,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR", "DPO_AUDITOR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.get_consistency_insights(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/dashboard")
def get_dashboard(
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR", "DPO_AUDITOR")),
    service: CaseService = Depends(get_case_service),
):
    return service.get_dashboard(principal)


@router.get("/api/v1/notifications", response_model=list[CaseNotificationOut])
def list_notifications(
    case_id: str | None = None,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR", "DPO_AUDITOR")),
    service: CaseService = Depends(get_case_service),
):
    tenant_key = principal.tenant_key or "default"
    return service.list_notifications(tenant_key=tenant_key, case_id=case_id)


@router.post("/api/v1/notifications/{notification_id}/ack", response_model=CaseNotificationOut)
def acknowledge_notification(
    notification_id: int,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR", "DPO_AUDITOR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.acknowledge_notification(notification_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases", response_model=CaseOut)
def create_case(
    payload: CaseCreate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "HR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.create_case(payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}", response_model=CaseOut)
def get_case(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.get_case(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/api/v1/cases/{case_id}", response_model=CaseOut)
def update_case(
    case_id: str,
    payload: CaseUpdate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "HR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.update_case(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/status", response_model=CaseOut)
def update_case_status(
    case_id: str,
    payload: CaseStatusUpdate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.update_status(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/stage", response_model=CaseOut)
def update_case_stage(
    case_id: str,
    payload: CaseStageUpdate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.update_stage(case_id, payload, principal)
    except TransitionError as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code, "message": exc.message, "blockers": exc.blockers})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/subjects", response_model=CaseSubjectOut)
def add_subject(
    case_id: str,
    payload: CaseSubjectCreate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.add_subject(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/links", response_model=list[CaseLinkOut])
def list_links(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_links(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/links", response_model=CaseLinkOut)
def add_link(
    case_id: str,
    payload: CaseLinkCreate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "HR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.add_link(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/v1/cases/{case_id}/links/{link_id}", response_model=CaseLinkOut)
def remove_link(
    case_id: str,
    link_id: int,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "HR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.remove_link(case_id, link_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/legal-holds", response_model=list[CaseLegalHoldOut])
def list_legal_holds(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_legal_holds(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/legal-hold", response_model=CaseLegalHoldOut)
def create_legal_hold(
    case_id: str,
    payload: CaseLegalHoldCreate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.create_legal_hold(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/experts", response_model=list[CaseExpertAccessOut])
def list_expert_access(
    case_id: str,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_expert_access(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/experts", response_model=CaseExpertAccessOut)
def grant_expert_access(
    case_id: str,
    payload: CaseExpertAccessCreate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.grant_expert_access(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/experts/{access_id}/revoke", response_model=CaseExpertAccessOut)
def revoke_expert_access(
    case_id: str,
    access_id: str,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.revoke_expert_access(case_id, access_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/reporter-messages", response_model=list[CaseReporterMessageOut])
def list_reporter_messages(
    case_id: str,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_reporter_messages(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/reporter-messages", response_model=CaseReporterMessageOut)
def add_reporter_message(
    case_id: str,
    payload: CaseReporterMessageCreate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.add_reporter_message(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/whistleblow/portal/{reporter_key}")
def get_reporter_portal(
    reporter_key: str,
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.get_reporter_portal(reporter_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/whistleblow/portal/{reporter_key}/messages", response_model=CaseReporterMessageOut)
def post_reporter_portal_message(
    reporter_key: str,
    payload: CaseReporterMessageCreate,
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.post_reporter_portal_message(reporter_key, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/external/inbox")
def get_external_inbox(
    case_id: str,
    token: str,
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.get_reporter_portal_by_case(case_id, token)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/external/inbox", response_model=CaseReporterMessageOut)
def post_external_inbox_message(
    case_id: str,
    token: str,
    payload: CaseReporterMessageCreate,
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.post_reporter_portal_message_by_case(case_id, token, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/evidence", response_model=CaseEvidenceOut)
def add_evidence(
    case_id: str,
    payload: CaseEvidenceCreate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.add_evidence(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/tasks", response_model=CaseTaskOut)
def add_task(
    case_id: str,
    payload: CaseTaskCreate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.add_task(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/api/v1/cases/{case_id}/tasks/{task_id}", response_model=CaseTaskOut)
def update_task(
    case_id: str,
    task_id: str,
    payload: CaseTaskUpdate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.update_task(case_id, task_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/apply-playbook", response_model=CaseOut)
def apply_playbook(
    case_id: str,
    payload: CaseApplyPlaybook,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.apply_playbook(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/tasks", response_model=list[CaseTaskOut])
def list_tasks(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_tasks(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/sanity-check", response_model=CaseSanityCheckOut)
def get_sanity_check(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.sanity_check(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/suggestions", response_model=list[CaseEvidenceSuggestionOut])
def list_suggestions(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_suggestions(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.put("/api/v1/cases/{case_id}/suggestions/{suggestion_id}", response_model=CaseEvidenceSuggestionOut)
def update_suggestion(
    case_id: str,
    suggestion_id: str,
    payload: CaseEvidenceSuggestionUpdate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.update_suggestion(case_id, suggestion_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/suggestions/{suggestion_id}/convert", response_model=CaseEvidenceOut)
def convert_suggestion(
    case_id: str,
    suggestion_id: str,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.convert_suggestion(case_id, suggestion_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/documents", response_model=list[CaseDocumentOut])
def list_documents(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_documents(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/documents/{doc_type}", response_model=CaseDocumentOut)
def generate_document(
    case_id: str,
    doc_type: str,
    payload: CaseDocumentCreate,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL", "INVESTIGATOR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.create_document(case_id, doc_type, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/documents/{doc_id}/download")
def download_document(
    case_id: str,
    doc_id: int,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        filename, content, media_type = service.download_document(case_id, doc_id, principal)
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "Document not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail)


@router.get("/api/v1/cases/{case_id}/export")
def export_pack(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        payload = service.export_pack(case_id, principal)
        return Response(
            content=payload,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={case_id}_export.zip"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/export/redact")
def export_redacted_pack(
    case_id: str,
    payload: CaseExportRedactionCreate,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        data = service.export_redacted_pack(case_id, payload, principal)
        return Response(
            content=data,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={case_id}_export_redacted.zip"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/remediation-export")
def remediation_export(
    case_id: str,
    payload: CaseRemediationExportCreate,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        filename, media_type, content = service.export_remediation(case_id, payload, principal)
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/decision", response_model=CaseOutcomeOut)
def record_decision(
    case_id: str,
    payload: CaseDecisionCreate,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.set_decision(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/decision", response_model=CaseOutcomeOut | None)
def get_decision(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.get_decision(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/erasure/approve", response_model=CaseErasureJobOut)
def approve_erasure(
    case_id: str,
    payload: CaseErasureApprove,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.approve_erasure(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/erasure/execute", response_model=CaseErasureJobOut)
def execute_erasure(
    case_id: str,
    payload: CaseErasureExecute,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.execute_erasure(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/notes", response_model=CaseNoteOut)
def add_note(
    case_id: str,
    payload: CaseNoteCreate,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "HR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.add_note(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/notes", response_model=list[CaseNoteOut])
def list_notes(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_notes(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/flags", response_model=list[CaseContentFlagOut])
def list_flags(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_flags(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.put("/api/v1/cases/{case_id}/flags/{flag_id}", response_model=CaseContentFlagOut)
def update_flag(
    case_id: str,
    flag_id: int,
    payload: CaseContentFlagUpdate,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL", "DPO_AUDITOR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.update_flag(case_id, flag_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/gates/legitimacy", response_model=CaseGateRecordOut)
def save_legitimacy_gate(
    case_id: str,
    payload: CaseLegitimacyForm,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.save_gate(case_id, "legitimacy", payload.model_dump(), principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/gates/triage", response_model=CaseGateRecordOut)
def save_triage_gate(
    case_id: str,
    payload: CaseTriageForm,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.save_gate(case_id, "triage", payload.model_dump(), principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/gates/credentialing", response_model=CaseGateRecordOut)
def save_credentialing_gate(
    case_id: str,
    payload: CaseCredentialingForm,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.save_gate(case_id, "credentialing", payload.model_dump(), principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/gates/adversarial", response_model=CaseGateRecordOut)
def save_adversarial_gate(
    case_id: str,
    payload: CaseAdversarialForm,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.save_gate(case_id, "adversarial", payload.model_dump(), principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/gates/works-council", response_model=CaseGateRecordOut)
def save_works_council_gate(
    case_id: str,
    payload: CaseWorksCouncilForm,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.save_gate(case_id, "works_council", payload.model_dump(), principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/gates/impact-analysis", response_model=CaseGateRecordOut)
def save_impact_analysis_gate(
    case_id: str,
    payload: CaseImpactAnalysisForm,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL", "HR")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.save_gate(case_id, "impact_analysis", payload.model_dump(), principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/gates/legal", response_model=CaseGateRecordOut)
def save_legal_gate(
    case_id: str,
    payload: CaseLegalApprovalForm,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL", "LEGAL_COUNSEL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.save_gate(case_id, "legal", payload.model_dump(), principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/gates", response_model=list[CaseGateRecordOut])
def list_gates(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_gates(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/serious-cause", response_model=CaseSeriousCauseOut)
def upsert_serious_cause(
    case_id: str,
    payload: CaseSeriousCauseUpsert,
    principal: Principal = Depends(require_roles("ADMIN", "INVESTIGATOR", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.set_serious_cause(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/cases/{case_id}/serious-cause", response_model=CaseSeriousCauseOut | None)
def get_serious_cause(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.get_serious_cause(case_id, principal)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/serious-cause/enable", response_model=CaseOut)
def toggle_serious_cause(
    case_id: str,
    payload: CaseSeriousCauseToggle,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.toggle_serious_cause(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/actions/submit-findings", response_model=CaseSeriousCauseOut)
def submit_findings(
    case_id: str,
    payload: CaseSubmitFindings,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.submit_findings(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/serious-cause/record-dismissal", response_model=CaseSeriousCauseOut)
def record_dismissal(
    case_id: str,
    payload: CaseRecordDismissal,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.record_dismissal(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/serious-cause/record-reasons-sent", response_model=CaseSeriousCauseOut)
def record_reasons_sent(
    case_id: str,
    payload: CaseRecordReasonsSent,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.record_reasons_sent(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/serious-cause/acknowledge-missed", response_model=CaseSeriousCauseOut)
def acknowledge_missed_deadline(
    case_id: str,
    payload: CaseAcknowledgeMissed,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.acknowledge_missed_deadline(case_id, payload, principal)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/cases/{case_id}/anonymize", response_model=CaseOut)
def anonymize_case(
    case_id: str,
    payload: CaseAnonymizeRequest | None = None,
    principal: Principal = Depends(require_roles("ADMIN", "LEGAL")),
    service: CaseService = Depends(get_case_service),
):
    try:
        reason = payload.reason if payload else None
        return service.anonymize_case(case_id, principal, reason=reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/audit", response_model=list[CaseAuditEventOut])
def list_audit_events(
    case_id: str,
    actor: str | None = Query(default=None),
    principal: Principal = Depends(get_principal),
    service: CaseService = Depends(get_case_service),
):
    try:
        return service.list_audit_events(case_id, principal, actor=actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
