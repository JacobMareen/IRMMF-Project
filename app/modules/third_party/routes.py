"""Third-party risk assessment endpoints (MVP scaffold)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import Principal, get_principal
from app.db import get_db
from app.modules.third_party.schemas import (
    ThirdPartyAssessmentIn,
    ThirdPartyAssessmentOut,
    ThirdPartyAssessmentUpdate,
    ThirdPartyQuestionOut,
    ThirdPartyResponseIn,
    ThirdPartyAnalysisOut,
)
from app.modules.third_party.service import ThirdPartyService
from app.security.access import tenant_principal_required


router = APIRouter(dependencies=[Depends(tenant_principal_required)])


def get_service(db: Session = Depends(get_db)) -> ThirdPartyService:
    return ThirdPartyService(db)


@router.get("/api/v1/third-party/assessments", response_model=list[ThirdPartyAssessmentOut])
def list_assessments(
    principal: Principal = Depends(get_principal),
    service: ThirdPartyService = Depends(get_service),
):
    tenant_key = principal.tenant_key or "default"
    return service.list_assessments(tenant_key)


@router.get("/api/v1/third-party/questions/all", response_model=list[ThirdPartyQuestionOut])
def list_questions(
    service: ThirdPartyService = Depends(get_service),
):
    return service.get_questions()


@router.post("/api/v1/third-party/assessments", response_model=ThirdPartyAssessmentOut, status_code=201)
def create_assessment(
    payload: ThirdPartyAssessmentIn,
    assessment_id: str = Query(...),
    principal: Principal = Depends(get_principal),
    service: ThirdPartyService = Depends(get_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        return service.create_assessment(tenant_key, assessment_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/v1/third-party/assessments/{third_party_id}", response_model=ThirdPartyAssessmentOut)
def get_assessment(
    third_party_id: str,
    principal: Principal = Depends(get_principal),
    service: ThirdPartyService = Depends(get_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        return service.get_assessment(third_party_id, tenant_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/api/v1/third-party/assessments/{third_party_id}", response_model=ThirdPartyAssessmentOut)
def update_assessment(
    third_party_id: str,
    payload: ThirdPartyAssessmentUpdate,
    principal: Principal = Depends(get_principal),
    service: ThirdPartyService = Depends(get_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        return service.update_assessment(third_party_id, payload, tenant_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/api/v1/third-party/assessments/{third_party_id}/responses",
    response_model=ThirdPartyAssessmentOut,
)
def submit_assessment_responses(
    third_party_id: str,
    payload: ThirdPartyResponseIn,
    principal: Principal = Depends(get_principal),
    service: ThirdPartyService = Depends(get_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        return service.submit_responses(third_party_id, payload, tenant_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/api/v1/third-party/assessments/{third_party_id}/analysis",
    response_model=ThirdPartyAnalysisOut,
)
def get_assessment_analysis(
    third_party_id: str,
    principal: Principal = Depends(get_principal),
    service: ThirdPartyService = Depends(get_service),
):
    tenant_key = principal.tenant_key or "default"
    try:
        return service.get_analysis(third_party_id, tenant_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
