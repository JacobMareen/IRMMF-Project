"""PIA compliance module API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_principal, Principal
from app.db import get_db
from app.modules.pia.schemas import (
    PiaAnonymizeRequest,
    PiaCaseAdvance,
    PiaCaseCreate,
    PiaCaseOut,
    PiaCaseSummary,
    PiaAuditEventOut,
    PiaEvidenceCreate,
    PiaOverview,
    PiaWorkflowStep,
)
from app.modules.pia.service import PiaService
from app.security.access import tenant_principal_required


router = APIRouter(dependencies=[Depends(tenant_principal_required)])


def get_pia_service(db: Session = Depends(get_db)) -> PiaService:
    return PiaService(db)


@router.get("/api/v1/pia/overview", response_model=PiaOverview)
def get_pia_overview(service: PiaService = Depends(get_pia_service)):
    return service.get_overview()


@router.get("/api/v1/pia/workflow", response_model=list[PiaWorkflowStep])
def get_pia_workflow(service: PiaService = Depends(get_pia_service)):
    return service.get_workflow()


@router.get("/api/v1/pia/cases", response_model=list[PiaCaseOut])
def list_pia_cases(
    principal: Principal = Depends(get_principal),
    service: PiaService = Depends(get_pia_service),
):
    tenant_key = principal.tenant_key or "default"
    return service.list_cases(tenant_key=tenant_key)


@router.post("/api/v1/pia/cases", response_model=PiaCaseOut)
def create_pia_case(
    payload: PiaCaseCreate,
    principal: Principal = Depends(get_principal),
    service: PiaService = Depends(get_pia_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        payload.user_id = payload.user_id or principal.subject
        return service.create_case(payload, tenant_key=tenant_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/pia/cases/{case_id}", response_model=PiaCaseOut)
def get_pia_case(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: PiaService = Depends(get_pia_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        return service.get_case(case_id, tenant_key=tenant_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/pia/cases/{case_id}/advance", response_model=PiaCaseOut)
def advance_pia_case(
    case_id: str,
    payload: PiaCaseAdvance,
    principal: Principal = Depends(get_principal),
    service: PiaService = Depends(get_pia_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        return service.advance_case(case_id, payload, tenant_key=tenant_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/pia/cases/{case_id}/evidence", response_model=PiaCaseOut)
def add_pia_evidence(
    case_id: str,
    payload: PiaEvidenceCreate,
    principal: Principal = Depends(get_principal),
    service: PiaService = Depends(get_pia_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        return service.add_evidence(case_id, payload, tenant_key=tenant_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/pia/cases/{case_id}/anonymize", response_model=PiaCaseOut)
def anonymize_pia_case(
    case_id: str,
    payload: PiaAnonymizeRequest | None = None,
    principal: Principal = Depends(get_principal),
    service: PiaService = Depends(get_pia_service),
):
    try:
        actor = payload.actor if payload else None
        reason = payload.reason if payload else None
        tenant_key = principal.tenant_key or "default"
        return service.anonymize_case(case_id, actor=actor, reason=reason, tenant_key=tenant_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/v1/pia/cases/{case_id}/steps/{step_key}", response_model=PiaCaseOut)
def save_pia_step(
    case_id: str,
    step_key: str,
    payload: dict,
    principal: Principal = Depends(get_principal),
    service: PiaService = Depends(get_pia_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        return service.save_step(case_id, step_key, payload, tenant_key=tenant_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/pia/cases/{case_id}/audit", response_model=list[PiaAuditEventOut])
def get_pia_audit(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: PiaService = Depends(get_pia_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        return service.get_audit_log(case_id, tenant_key=tenant_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/pia/cases/{case_id}/summary", response_model=PiaCaseSummary)
def get_pia_summary(
    case_id: str,
    principal: Principal = Depends(get_principal),
    service: PiaService = Depends(get_pia_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        return service.get_summary(case_id, tenant_key=tenant_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
