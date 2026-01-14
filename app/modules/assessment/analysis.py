"""Assessment analytics and scoring outputs."""
from typing import Any, Dict, List

from app import models


class AssessmentAnalysisService:
    def get_analysis(self, assessment_id: str):
        all_qs = self.q_repo.get_all()
        responses = self.r_repo.get_by_assessment(assessment_id)
        evidence = self.db.query(models.EvidenceResponse).filter_by(assessment_id=assessment_id).all()
        intake_tags = self._get_intake_tags(assessment_id)
        valid_map = {r.q_id: r.score_achieved for r in responses if not r.is_deferred}
        reachable = set(self.branch_engine.calculate_reachable_path(all_qs, valid_map))
        # Baseline excludes override answers to keep benchmarks comparable.
        valid_responses = [
            r
            for r in responses
            if r.q_id in reachable and not r.is_deferred and (r.origin or "adaptive") != "override"
        ]
        result = self.scoring_engine.compute_analysis(all_qs, valid_responses, evidence, intake_tags)
        result["recommendations"] = self._build_recommendations(result)
        # Expanded includes override answers for a deeper maturity snapshot.
        expanded_responses = [
            r for r in responses
            if r.q_id in reachable and not r.is_deferred
        ]
        expanded = self.scoring_engine.compute_analysis(all_qs, expanded_responses, evidence, intake_tags)
        result["maturity_scores"] = {
            "baseline": result.get("summary", {}),
            "expanded": expanded.get("summary", {}),
        }
        result["expanded_axes"] = expanded.get("axes", [])
        result["maturity_explanation"] = (
            "Baseline maturity uses adaptive-path answers only for comparability. "
            "Expanded maturity includes override answers and may shift when deeper items are completed."
        )
        try:
            snapshot = models.ReportSnapshot(
                assessment_id=assessment_id,
                bank_version=None,
                snapshot=result,
            )
            self.db.add(snapshot)
            self.db.commit()
        except Exception:
            self.db.rollback()
        return result

    def _build_recommendations(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Placeholder recommendations until rec library is defined."""
        axes = result.get("axes") or []
        if not axes:
            return []
        sorted_axes = sorted(axes, key=lambda a: a.get("score", 0.0))
        low_axes = sorted_axes[:3]
        recs = []
        for axis in low_axes:
            recs.append({
                "title": f"Strengthen {axis.get('axis')}",
                "priority": "High",
                "timeline": "30-60 days",
                "rationale": f"Low maturity on {axis.get('axis')} is limiting overall posture.",
            })
        return recs[:5]
