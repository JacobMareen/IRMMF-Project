"""Recommendation matching and generation service."""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.modules.assessment import models
from app.core.repositories import RecommendationRepository
from app.models import utcnow


class RecommendationMatchingEngine:
    """
    Intelligent recommendation matching based on:
    1. Low axis scores (< threshold)
    2. High-risk scenarios (RED/AMBER)
    3. Specific weak questions
    """

    # Thresholds for matching
    AXIS_LOW_THRESHOLD = 50.0  # Axis scores below this trigger recommendations
    AXIS_CRITICAL_THRESHOLD = 30.0  # Extra urgent recommendations

    def __init__(self, db: Session):
        self.db = db
        self.rec_repo = RecommendationRepository(db)

    def generate_recommendations(
        self,
        assessment_id: str,
        analysis_result: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on analysis results.

        Args:
            assessment_id: Assessment ID
            analysis_result: Output from V6_1ScoringEngine.compute_analysis()
            user_id: User generating recommendations

        Returns:
            List of matched recommendations with metadata
        """
        axes = analysis_result.get("axes", [])
        top_risks = analysis_result.get("top_risks", [])

        matched_recs = []

        # 1. Match by Low Axes
        low_axes = [a for a in axes if a.get("score", 100) < self.AXIS_LOW_THRESHOLD]
        for axis_data in low_axes:
            axis_code = axis_data.get("code")
            axis_score = axis_data.get("score", 0)

            # Get recommendations targeting this axis
            recs = self.rec_repo.get_recommendations_by_axis(axis_code)

            for rec in recs:
                # Check if trigger rules match
                if self._matches_trigger_rules(rec, axis_data, analysis_result):
                    priority = self._calculate_priority(rec, axis_score)

                    matched_recs.append({
                        "rec": rec,
                        "priority": priority,
                        "triggered_by_axes": [axis_code],
                        "triggered_by_risks": [],
                        "triggered_by_questions": [],
                        "match_reason": f"Low {axis_data.get('axis')} score: {axis_score:.1f}%"
                    })

        # 2. Match by High-Risk Scenarios
        high_risks = [r for r in top_risks if r.get("risk_level") in ["RED", "AMBER"]]
        for risk in high_risks:
            scenario_id = risk.get("scenario_id")
            key_gaps = risk.get("key_gaps", [])

            # Get recommendations for this scenario
            recs = self.rec_repo.get_recommendations_by_scenario(scenario_id)

            for rec in recs:
                if self._matches_trigger_rules(rec, risk, analysis_result):
                    # Extract axis codes from key_gaps (format: "Governance: 3.5/6")
                    gap_axes = []
                    for gap in key_gaps:
                        if ":" in gap:
                            axis_name = gap.split(":")[0].strip()
                            # Map full name back to code
                            axis_map = {
                                "Governance": "G", "Execution": "E", "Technical": "T",
                                "Legal": "L", "Human": "H", "Visibility": "V",
                                "Resilience": "R", "Friction": "F", "Control Lag": "W"
                            }
                            if axis_name in axis_map:
                                gap_axes.append(axis_map[axis_name])

                    priority = "Critical" if risk.get("risk_level") == "RED" else "High"

                    matched_recs.append({
                        "rec": rec,
                        "priority": priority,
                        "triggered_by_axes": gap_axes,
                        "triggered_by_risks": [scenario_id],
                        "triggered_by_questions": [],
                        "match_reason": f"{risk.get('risk_level')} risk: {risk.get('scenario')}"
                    })

        # 3. Deduplicate and consolidate
        consolidated = self._consolidate_recommendations(matched_recs)

        # 4. Persist to database
        for item in consolidated:
            self.rec_repo.upsert_assessment_recommendation(
                assessment_id=assessment_id,
                rec_id=item["rec"].rec_id,
                priority=item["priority"],
                triggered_by_axes=item["triggered_by_axes"],
                triggered_by_risks=item["triggered_by_risks"],
                triggered_by_questions=item["triggered_by_questions"],
                custom_notes=item.get("match_reason"),
                created_by=user_id
            )

        # 5. Return formatted recommendations
        return [self._format_recommendation(item) for item in consolidated]

    def _matches_trigger_rules(
        self,
        rec: models.Recommendation,
        finding: Dict[str, Any],
        full_analysis: Dict[str, Any]
    ) -> bool:
        """Check if recommendation's trigger rules match the finding."""
        trigger_rules = rec.trigger_rules or {}

        # No rules = always match
        if not trigger_rules:
            return True

        # Check axis threshold rules
        if "axis_threshold" in trigger_rules:
            thresholds = trigger_rules["axis_threshold"]
            for axis, min_score in thresholds.items():
                axis_data = next(
                    (a for a in full_analysis.get("axes", []) if a.get("code") == axis),
                    None
                )
                if axis_data and axis_data.get("score", 100) < min_score:
                    return True

        # Check risk level rules
        if "risk_level" in trigger_rules:
            allowed_levels = trigger_rules["risk_level"]
            if finding.get("risk_level") in allowed_levels:
                return True

        # Check trust index rules
        if "trust_index_below" in trigger_rules:
            threshold = trigger_rules["trust_index_below"]
            trust_index = full_analysis.get("summary", {}).get("trust_index", 100)
            if trust_index < threshold:
                return True

        return True  # Default to match if no specific rules failed

    def _calculate_priority(self, rec: models.Recommendation, axis_score: float) -> str:
        """Calculate priority based on axis score severity."""
        if axis_score < self.AXIS_CRITICAL_THRESHOLD:
            return "Critical"
        elif axis_score < self.AXIS_LOW_THRESHOLD * 0.75:  # Below 37.5%
            return "High"
        else:
            return rec.default_priority

    def _consolidate_recommendations(
        self,
        matched_recs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Deduplicate and consolidate recommendations by rec_id."""
        consolidated_map = {}

        for item in matched_recs:
            rec_id = item["rec"].rec_id

            if rec_id not in consolidated_map:
                consolidated_map[rec_id] = item
            else:
                # Merge triggers and upgrade priority if needed
                existing = consolidated_map[rec_id]
                existing["triggered_by_axes"] = list(set(
                    existing["triggered_by_axes"] + item["triggered_by_axes"]
                ))
                existing["triggered_by_risks"] = list(set(
                    existing["triggered_by_risks"] + item["triggered_by_risks"]
                ))

                # Keep highest priority
                priority_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
                if priority_order.get(item["priority"], 5) < priority_order.get(existing["priority"], 5):
                    existing["priority"] = item["priority"]

        # Sort by priority
        priority_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        return sorted(
            consolidated_map.values(),
            key=lambda x: priority_order.get(x["priority"], 5)
        )

    def _format_recommendation(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Format recommendation for API response."""
        rec = item["rec"]

        return {
            "rec_id": rec.rec_id,
            "title": rec.title,
            "description": rec.description,
            "rationale": rec.rationale,
            "priority": item["priority"],
            "timeline": rec.typical_timeline,
            "effort": rec.estimated_effort,
            "category": rec.category,
            "subcategory": rec.subcategory,
            "implementation_steps": rec.implementation_steps,
            "success_criteria": rec.success_criteria,
            "prerequisites": rec.prerequisites,
            "vendor_suggestions": rec.vendor_suggestions,
            "external_resources": rec.external_resources,
            "triggered_by": {
                "axes": item["triggered_by_axes"],
                "risks": item["triggered_by_risks"],
                "questions": item["triggered_by_questions"]
            },
            "match_reason": item.get("match_reason")
        }


class RecommendationService:
    """High-level service for recommendation operations."""

    def __init__(self, db: Session):
        self.db = db
        self.rec_repo = RecommendationRepository(db)
        self.matcher = RecommendationMatchingEngine(db)

    def get_recommendations_for_assessment(
        self,
        assessment_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all recommendations for an assessment with full details."""
        assessment_recs = self.rec_repo.get_assessment_recommendations(
            assessment_id, status
        )

        result = []
        for ar in assessment_recs:
            rec = ar.recommendation
            result.append({
                "rec_id": rec.rec_id,
                "title": rec.title,
                "description": rec.description,
                "rationale": rec.rationale,
                "priority": ar.priority,
                "status": ar.status,
                "timeline": ar.custom_timeline or rec.typical_timeline,
                "effort": rec.estimated_effort,
                "category": rec.category,
                "subcategory": rec.subcategory,
                "implementation_steps": rec.implementation_steps,
                "success_criteria": rec.success_criteria,
                "prerequisites": rec.prerequisites,
                "vendor_suggestions": rec.vendor_suggestions,
                "external_resources": rec.external_resources,
                "triggered_by": {
                    "axes": ar.triggered_by_axes,
                    "risks": ar.triggered_by_risks,
                    "questions": ar.triggered_by_questions
                },
                "assigned_to": ar.assigned_to,
                "due_date": ar.due_date.isoformat() if ar.due_date else None,
                "custom_notes": ar.custom_notes,
                "created_at": ar.created_at.isoformat(),
                "updated_at": ar.updated_at.isoformat()
            })

        return result

    def update_recommendation(
        self,
        assessment_id: str,
        rec_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update recommendation fields and track in history."""
        ar = (
            self.db.query(models.AssessmentRecommendation)
            .filter_by(assessment_id=assessment_id, rec_id=rec_id)
            .first()
        )

        if not ar:
            raise ValueError(f"Recommendation {rec_id} not found for assessment {assessment_id}")

        # Track changes
        for field, new_value in updates.items():
            if hasattr(ar, field):
                old_value = getattr(ar, field)
                if old_value != new_value:
                    # Log to history
                    history = models.RecommendationHistory(
                        assessment_id=assessment_id,
                        rec_id=rec_id,
                        field_changed=field,
                        old_value=str(old_value) if old_value else None,
                        new_value=str(new_value) if new_value else None,
                        changed_by=user_id
                    )
                    self.db.add(history)

                    # Update field
                    setattr(ar, field, new_value)

        ar.updated_at = utcnow()
        self.db.commit()

        return {"status": "success", "rec_id": rec_id}
