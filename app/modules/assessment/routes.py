"""Assessment module API routes."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import get_principal, Principal
from app import schemas
from app.modules.assessment import models
from app.db import get_db
from app.modules.assessment.service import AssessmentService
from app.security.access import ensure_tenant_match, is_admin, rbac_disabled, require_tenant


router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> AssessmentService:
    return AssessmentService(db)


def _ensure_assessment_access(
    assessment_id: str,
    principal: Principal,
    db: Session,
) -> None:
    if rbac_disabled():
        return
    assessment = (
        db.query(models.Assessment)
        .filter_by(assessment_id=assessment_id)
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    if is_admin(principal):
        return
    ensure_tenant_match(principal, assessment.tenant_key, not_found_detail="Assessment not found.")


def _ensure_tenant_context(principal: Principal) -> None:
    require_tenant(principal)


@router.get("/api/v1/questions/all", response_model=list[schemas.QuestionOut])
def get_all_questions(
    assessment_id: str | None = Query(default=None),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    """Returns the full static Question Bank or the depth-eligible set."""
    if assessment_id:
        _ensure_assessment_access(assessment_id, principal, db)
        try:
            return service.get_questions_for_assessment(assessment_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return db.query(models.Question).all()


@router.post("/api/v1/assessment/submit")
def submit_answer(
    payload: schemas.ResponseCreate,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    """Core loop: save answer, run branching, return updated state."""
    _ensure_assessment_access(payload.assessment_id, principal, db)
    return service.submit_answer(payload)


@router.post("/responses/submit")
def submit_answer_alias(
    payload: schemas.ResponseCreate,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    """Compatibility alias for evidence payload submissions."""
    _ensure_assessment_access(payload.assessment_id, principal, db)
    return service.submit_answer(payload)


@router.get("/api/v1/assessment/{assessment_id}/context")
def get_context(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    """Resume logic: return prior answers and reachable path."""
    _ensure_assessment_access(assessment_id, principal, db)
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
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    _ensure_assessment_access(assessment_id, principal, db)
    try:
        override_depth = bool(payload.get("override_depth"))
        return service.set_override_depth(assessment_id, override_depth)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error during override update")


@router.get("/responses/analysis/{assessment_id}")
def get_analysis(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    """Run scoring engine to calculate archetype and axis scores."""
    _ensure_assessment_access(assessment_id, principal, db)
    return service.get_analysis(assessment_id)


@router.get("/responses/table/{assessment_id}")
def get_review_table(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    """Return a flat review table of answers for audit workflows."""
    _ensure_assessment_access(assessment_id, principal, db)
    return service.get_review_table(assessment_id)


@router.get("/api/v1/assessment/{assessment_id}/resume", response_model=schemas.ResumptionState)
def resume_assessment(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    _ensure_assessment_access(assessment_id, principal, db)
    try:
        state = service.get_resumption_state(assessment_id)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error during handshake")


@router.post("/api/v1/assessment/new")
def start_assessment(
    payload: dict | None = Body(default=None),
    principal: Principal = Depends(get_principal),
    service: AssessmentService = Depends(get_service),
):
    """Create a new assessment and return the secure access key."""
    _ensure_tenant_context(principal)
    user_id = payload.get("user_id") if payload else None
    tenant_key = principal.tenant_key or "default"
    # Dev-only fallback: replace with real login-derived user_id and tenant_key once auth is enabled.
    resolved_user = user_id or principal.subject
    opt_in = payload.get("market_research_opt_in", False) if payload else False
    new_key = service.create_new_assessment(
        tenant_key=tenant_key, 
        user_id=resolved_user,
        market_research_opt_in=opt_in
    )
    return {"assessment_id": new_key}


@router.get("/api/v1/assessment/user/{user_id}")
def list_assessments_for_user(
    user_id: str,
    principal: Principal = Depends(get_principal),
    service: AssessmentService = Depends(get_service),
):
    _ensure_tenant_context(principal)
    tenant_key = principal.tenant_key or "default"
    return service.list_assessments_for_user(user_id, tenant_key=tenant_key)


@router.get("/api/v1/assessment/user/{user_id}/latest")
def get_latest_assessment_for_user(
    user_id: str,
    principal: Principal = Depends(get_principal),
    service: AssessmentService = Depends(get_service),
):
    _ensure_tenant_context(principal)
    tenant_key = principal.tenant_key or "default"
    latest = service.get_latest_assessment_for_user(user_id, tenant_key=tenant_key)
    if not latest:
        raise HTTPException(status_code=404, detail="No assessments found for user.")
    return latest


@router.post("/api/v1/assessment/{assessment_id}/reset")
def reset_assessment_data(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    _ensure_assessment_access(assessment_id, principal, db)
    try:
        return service.reset_assessment_data(assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error during reset")


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
def submit_intake(
    payload: dict,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    assessment_id = payload.get("assessment_id")
    answers = payload.get("answers") or {}
    if not assessment_id:
        raise HTTPException(status_code=400, detail="assessment_id is required")
    _ensure_assessment_access(assessment_id, principal, db)
    try:
        return service.submit_intake(assessment_id, answers)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error during intake submit")




@router.get("/api/v1/intake/{assessment_id}")
def get_intake_responses(
    assessment_id: str,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: AssessmentService = Depends(get_service),
):
    _ensure_assessment_access(assessment_id, principal, db)
    return service.get_intake_responses(assessment_id)


# --- RECOMMENDATION ENDPOINTS ---

from typing import Optional
from app.modules.assessment.recommendations import RecommendationService


def get_rec_service(db: Session = Depends(get_db)) -> RecommendationService:
    return RecommendationService(db)


@router.get("/api/v1/assessment/{assessment_id}/recommendations")
def get_recommendations(
    assessment_id: str,
    status: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: RecommendationService = Depends(get_rec_service),
):
    """Get all recommendations for an assessment."""
    _ensure_assessment_access(assessment_id, principal, db)
    try:
        return service.get_recommendations_for_assessment(assessment_id, status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/v1/assessment/{assessment_id}/recommendations/{rec_id}")
def update_recommendation(
    assessment_id: str,
    rec_id: str,
    payload: dict,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: RecommendationService = Depends(get_rec_service),
):
    """Update a recommendation (status, priority, assignment, etc.)."""
    _ensure_assessment_access(assessment_id, principal, db)
    try:
        user_id = payload.pop("user_id", None)
        return service.update_recommendation(assessment_id, rec_id, payload, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/assessment/{assessment_id}/recommendations/{rec_id}/history")
def get_recommendation_history(
    assessment_id: str,
    rec_id: str,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
    service: RecommendationService = Depends(get_rec_service),
):
    """Get change history for a recommendation."""
    _ensure_assessment_access(assessment_id, principal, db)
    history = service.rec_repo.get_recommendation_history(assessment_id, rec_id)
    return [
        {
            "field_changed": h.field_changed,
            "old_value": h.old_value,
            "new_value": h.new_value,
            "change_reason": h.change_reason,
            "changed_by": h.changed_by,
            "changed_at": h.changed_at.isoformat()
        }
        for h in history
    ]


# --- LIBRARY MANAGEMENT ENDPOINTS ---

@router.get("/api/v1/recommendations/library")
def get_recommendation_library(
    category: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    service: RecommendationService = Depends(get_rec_service),
):
    """Browse the master recommendation library."""
    _ensure_tenant_context(principal)
    if category:
        recs = service.rec_repo.search_recommendations(category=category)
    else:
        recs = service.rec_repo.get_all_recommendations()

    return [
        {
            "rec_id": r.rec_id,
            "title": r.title,
            "description": r.description,
            "category": r.category,
            "subcategory": r.subcategory,
            "priority": r.default_priority,
            "timeline": r.typical_timeline,
            "effort": r.estimated_effort,
            "target_axes": r.target_axes,
            "relevant_scenarios": r.relevant_scenarios
        }
        for r in recs
    ]


@router.get("/api/v1/recommendations/library/{rec_id}")
def get_recommendation_details(
    rec_id: str,
    principal: Principal = Depends(get_principal),
    service: RecommendationService = Depends(get_rec_service),
):
    """Get full details of a recommendation from library."""
    _ensure_tenant_context(principal)
    rec = service.rec_repo.get_recommendation_by_id(rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return {
        "rec_id": rec.rec_id,
        "title": rec.title,
        "description": rec.description,
        "rationale": rec.rationale,
        "category": rec.category,
        "subcategory": rec.subcategory,
        "implementation_steps": rec.implementation_steps,
        "success_criteria": rec.success_criteria,
        "prerequisites": rec.prerequisites,
        "estimated_effort": rec.estimated_effort,
        "typical_timeline": rec.typical_timeline,
        "default_priority": rec.default_priority,
        "vendor_suggestions": rec.vendor_suggestions,
        "external_resources": rec.external_resources,
        "target_axes": rec.target_axes,
        "relevant_scenarios": rec.relevant_scenarios,
        "trigger_rules": rec.trigger_rules,
        "version": rec.version
    }
