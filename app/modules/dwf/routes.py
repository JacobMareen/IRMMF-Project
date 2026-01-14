"""Dynamic Workforce module API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.modules.dwf.services import DwfService
from app.modules.dwf import schemas as dwf_schemas


router = APIRouter()


def get_dwf_service(db: Session = Depends(get_db)) -> DwfService:
    return DwfService(db)


@router.get("/api/v1/dwf/questions/all", response_model=list[dwf_schemas.DwfQuestionOut])
def get_dwf_questions(dwf_service: DwfService = Depends(get_dwf_service)):
    return dwf_service.get_questions()


@router.post("/api/v1/dwf/assessment/register")
def register_dwf_assessment(
    payload: dwf_schemas.DwfAssessmentRegister,
    dwf_service: DwfService = Depends(get_dwf_service),
):
    return {"assessment_id": dwf_service.register_assessment(payload.assessment_id)}


@router.post("/api/v1/dwf/submit")
def submit_dwf_answer(
    payload: dwf_schemas.DwfResponseCreate,
    dwf_service: DwfService = Depends(get_dwf_service),
):
    return dwf_service.submit_answer(payload)


@router.get("/api/v1/dwf/assessment/{assessment_id}/analysis")
def get_dwf_analysis(
    assessment_id: str,
    dwf_service: DwfService = Depends(get_dwf_service),
):
    return dwf_service.get_analysis(assessment_id)
