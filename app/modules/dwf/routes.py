"""Dynamic Workforce module API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.modules.dwf.services import DwfService
from app.modules.dwf import schemas as dwf_schemas
from auth import get_principal, Principal
from app.security.access import tenant_principal_required


router = APIRouter(dependencies=[Depends(tenant_principal_required)])


def get_dwf_service(db: Session = Depends(get_db)) -> DwfService:
    return DwfService(db)


@router.get("/api/v1/dwf/questions/all", response_model=list[dwf_schemas.DwfQuestionOut])
def get_dwf_questions(dwf_service: DwfService = Depends(get_dwf_service)):
    return dwf_service.get_questions()


@router.post("/api/v1/dwf/assessment/register")
def register_dwf_assessment(
    payload: dwf_schemas.DwfAssessmentRegister,
    principal: Principal = Depends(get_principal),
    dwf_service: DwfService = Depends(get_dwf_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        return {"assessment_id": dwf_service.register_assessment(payload.assessment_id, tenant_key=tenant_key)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/v1/dwf/submit")
def submit_dwf_answer(
    payload: dwf_schemas.DwfResponseCreate,
    principal: Principal = Depends(get_principal),
    dwf_service: DwfService = Depends(get_dwf_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        return dwf_service.submit_answer(payload, tenant_key=tenant_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/v1/dwf/assessment/{assessment_id}/analysis")
def get_dwf_analysis(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    dwf_service: DwfService = Depends(get_dwf_service),
):
    try:
        tenant_key = principal.tenant_key or "default"
        return dwf_service.get_analysis(assessment_id, tenant_key=tenant_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
