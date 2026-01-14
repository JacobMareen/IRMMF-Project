"""Assessment module API routes."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.modules.assessment.service import AssessmentService


router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> AssessmentService:
    return AssessmentService(db)


@router.get("/api/v1/questions/all", response_model=list[schemas.QuestionOut])
def get_all_questions(db: Session = Depends(get_db)):
    """Returns the full static Question Bank."""
    return db.query(models.Question).all()


@router.post("/api/v1/assessment/submit")
def submit_answer(payload: schemas.ResponseCreate, service: AssessmentService = Depends(get_service)):
    """Core loop: save answer, run branching, return updated state."""
    return service.submit_answer(payload)


@router.post("/responses/submit")
def submit_answer_alias(payload: schemas.ResponseCreate, service: AssessmentService = Depends(get_service)):
    """Compatibility alias for evidence payload submissions."""
    return service.submit_answer(payload)


@router.get("/api/v1/assessment/{assessment_id}/context")
def get_context(assessment_id: str, service: AssessmentService = Depends(get_service)):
    """Resume logic: return prior answers and reachable path."""
    try:
        return service.get_context(assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error during context lookup")


@router.post("/api/v1/assessment/{assessment_id}/override")
def set_override_depth(
    assessment_id: str,
    payload: dict,
    service: AssessmentService = Depends(get_service),
):
    try:
        override_depth = bool(payload.get("override_depth"))
        return service.set_override_depth(assessment_id, override_depth)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error during override update")


@router.get("/responses/analysis/{assessment_id}")
def get_analysis(assessment_id: str, service: AssessmentService = Depends(get_service)):
    """Run scoring engine to calculate archetype and axis scores."""
    return service.get_analysis(assessment_id)


@router.get("/responses/table/{assessment_id}")
def get_review_table(assessment_id: str, service: AssessmentService = Depends(get_service)):
    """Return a flat review table of answers for audit workflows."""
    return service.get_review_table(assessment_id)


@router.get("/api/v1/assessment/{assessment_id}/resume", response_model=schemas.ResumptionState)
def resume_assessment(assessment_id: str, service: AssessmentService = Depends(get_service)):
    try:
        state = service.get_resumption_state(assessment_id)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error during handshake")


@router.post("/api/v1/assessment/new")
def start_assessment(payload: dict | None = Body(default=None), service: AssessmentService = Depends(get_service)):
    """Create a new assessment and return the secure access key."""
    user_id = payload.get("user_id") if payload else None
    new_key = service.create_new_assessment(user_id=user_id)
    return {"assessment_id": new_key}


@router.get("/api/v1/intake/options")
def get_intake_options(service: AssessmentService = Depends(get_service)):
    return service.get_intake_options()


@router.get("/api/v1/intake/start")
def get_intake_start(service: AssessmentService = Depends(get_service)):
    try:
        data = service.get_intake_questions()
        return data
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/intake/debug")
def get_intake_debug(service: AssessmentService = Depends(get_service)):
    """Debug intake tables for local troubleshooting."""
    db = service.db
    iq_count = db.execute(text("SELECT COUNT(*) FROM dim_intake_questions")).scalar()
    lo_count = db.execute(text("SELECT COUNT(*) FROM dim_intake_list_options")).scalar()
    sample = db.execute(text("SELECT intake_q_id, section, input_type, list_ref FROM dim_intake_questions ORDER BY intake_q_id LIMIT 3")).all()
    return {
        "intake_questions": int(iq_count or 0),
        "intake_list_options": int(lo_count or 0),
        "sample_questions": [dict(r._mapping) for r in sample],
    }


@router.post("/api/v1/intake/submit")
def submit_intake(payload: dict, service: AssessmentService = Depends(get_service)):
    assessment_id = payload.get("assessment_id")
    answers = payload.get("answers") or {}
    if not assessment_id:
        raise HTTPException(status_code=400, detail="assessment_id is required")
    try:
        return service.submit_intake(assessment_id, answers)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error during intake submit")


@router.get("/api/v1/intake/{assessment_id}")
def get_intake_responses(assessment_id: str, service: AssessmentService = Depends(get_service)):
    return service.get_intake_responses(assessment_id)
