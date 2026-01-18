"""Thin data-access helpers used by services to keep query logic centralized."""
from typing import List, Optional
from sqlalchemy import case
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert # USE POSTGRES DIALECT
from app import models
from app.models import utcnow

class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db
    def get_all(self): return self.db.query(models.Question).all()
    def get_by_id(self, q_id: str): return self.db.query(models.Question).filter_by(q_id=q_id).first()

class ResponseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_assessment(self, assessment_id: str) -> List[models.Response]:
        return self.db.query(models.Response).filter_by(assessment_id=assessment_id).all()

    def upsert_response(self, assessment_id: str, q_id: str, a_id: str, score: float, pack_id: str):
        # Upsert ensures a single response per assessment/question.
        stmt = insert(models.Response).values(
            assessment_id=assessment_id, q_id=q_id, a_id=a_id,
            score_achieved=score, pack_id=pack_id
        ).on_conflict_do_update(
            index_elements=['assessment_id', 'q_id'], # Identify conflict by columns
            set_={"a_id": a_id, "score_achieved": score}
        )
        self.db.execute(stmt)
        self.db.commit()


class RecommendationRepository:
    """Data access for recommendations library and assessment-specific instances."""

    def __init__(self, db: Session):
        self.db = db

    # --- Library Management ---

    def get_all_recommendations(self, active_only: bool = True) -> List[models.Recommendation]:
        """Fetch all recommendations from library."""
        query = self.db.query(models.Recommendation)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()

    def get_recommendation_by_id(self, rec_id: str) -> Optional[models.Recommendation]:
        """Fetch single recommendation by rec_id."""
        return self.db.query(models.Recommendation).filter_by(rec_id=rec_id).first()

    def get_recommendations_by_axis(self, axis: str) -> List[models.Recommendation]:
        """Find recommendations that target a specific axis."""
        return (
            self.db.query(models.Recommendation)
            .filter(models.Recommendation.target_axes.contains([axis]))
            .filter_by(is_active=True)
            .all()
        )

    def get_recommendations_by_scenario(self, scenario_id: str) -> List[models.Recommendation]:
        """Find recommendations relevant to a risk scenario."""
        return (
            self.db.query(models.Recommendation)
            .filter(models.Recommendation.relevant_scenarios.contains([scenario_id]))
            .filter_by(is_active=True)
            .all()
        )

    def search_recommendations(
        self,
        category: Optional[str] = None,
        axes: Optional[List[str]] = None,
        scenarios: Optional[List[str]] = None,
        priority: Optional[str] = None
    ) -> List[models.Recommendation]:
        """Search recommendations with multiple filters."""
        query = self.db.query(models.Recommendation).filter_by(is_active=True)

        if category:
            query = query.filter_by(category=category)
        if priority:
            query = query.filter_by(default_priority=priority)
        if axes:
            query = query.filter(
                models.Recommendation.target_axes.overlap(axes)
            )
        if scenarios:
            query = query.filter(
                models.Recommendation.relevant_scenarios.overlap(scenarios)
            )

        return query.all()

    # --- Assessment-Specific Recommendations ---

    def get_assessment_recommendations(
        self,
        assessment_id: str,
        status: Optional[str] = None
    ) -> List[models.AssessmentRecommendation]:
        """Get all recommendations for an assessment, optionally filtered by status."""
        query = self.db.query(models.AssessmentRecommendation).filter_by(
            assessment_id=assessment_id
        )
        if status:
            query = query.filter_by(status=status)
        return query.order_by(
            # Priority order: Critical > High > Medium > Low
            case(
                (models.AssessmentRecommendation.priority == "Critical", 1),
                (models.AssessmentRecommendation.priority == "High", 2),
                (models.AssessmentRecommendation.priority == "Medium", 3),
                else_=4
            ),
            models.AssessmentRecommendation.created_at.desc()
        ).all()

    def upsert_assessment_recommendation(
        self,
        assessment_id: str,
        rec_id: str,
        priority: str = "Medium",
        triggered_by_axes: Optional[List[str]] = None,
        triggered_by_risks: Optional[List[str]] = None,
        triggered_by_questions: Optional[List[str]] = None,
        custom_notes: Optional[str] = None,
        created_by: Optional[str] = None
    ):
        """Create or update an assessment recommendation."""
        stmt = insert(models.AssessmentRecommendation).values(
            assessment_id=assessment_id,
            rec_id=rec_id,
            priority=priority,
            triggered_by_axes=triggered_by_axes or [],
            triggered_by_risks=triggered_by_risks or [],
            triggered_by_questions=triggered_by_questions or [],
            custom_notes=custom_notes,
            created_by=created_by,
            status="pending"
        ).on_conflict_do_update(
            index_elements=["assessment_id", "rec_id"],
            set_={
                "priority": priority,
                "triggered_by_axes": triggered_by_axes or [],
                "triggered_by_risks": triggered_by_risks or [],
                "triggered_by_questions": triggered_by_questions or [],
                "updated_at": utcnow()
            }
        )
        self.db.execute(stmt)
        self.db.commit()

    def update_recommendation_status(
        self,
        assessment_id: str,
        rec_id: str,
        new_status: str,
        changed_by: Optional[str] = None,
        change_reason: Optional[str] = None
    ):
        """Update status and log to history."""
        rec = (
            self.db.query(models.AssessmentRecommendation)
            .filter_by(assessment_id=assessment_id, rec_id=rec_id)
            .first()
        )

        if not rec:
            raise ValueError(f"Recommendation {rec_id} not found for assessment {assessment_id}")

        old_status = rec.status
        rec.status = new_status
        rec.updated_at = utcnow()

        # Set timestamps based on status
        if new_status == "in_progress" and not rec.started_at:
            rec.started_at = utcnow()
        elif new_status == "completed" and not rec.completed_at:
            rec.completed_at = utcnow()

        # Log to history
        history = models.RecommendationHistory(
            assessment_id=assessment_id,
            rec_id=rec_id,
            field_changed="status",
            old_value=old_status,
            new_value=new_status,
            change_reason=change_reason,
            changed_by=changed_by
        )
        self.db.add(history)
        self.db.commit()

    def get_recommendation_history(
        self,
        assessment_id: str,
        rec_id: str
    ) -> List[models.RecommendationHistory]:
        """Get change history for a recommendation."""
        return (
            self.db.query(models.RecommendationHistory)
            .filter_by(assessment_id=assessment_id, rec_id=rec_id)
            .order_by(models.RecommendationHistory.changed_at.desc())
            .all()
        )
