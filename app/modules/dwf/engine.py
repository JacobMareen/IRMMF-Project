from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from app.modules.dwf.models import DwfQuestion, DwfResponse


class DwfScoringEngine:
    def _risk_tolerance(self, likelihood: Optional[float], impact: Optional[float]) -> Optional[str]:
        if likelihood is None or impact is None:
            return None
        risk_score = (likelihood + impact) / 2.0
        if risk_score >= 4.0:
            return "Low"
        if risk_score >= 2.5:
            return "Medium"
        return "High"

    def _risk_recommendation(self, likelihood: Optional[float], impact: Optional[float]) -> Optional[str]:
        if likelihood is None or impact is None:
            return None
        risk_score = (likelihood + impact) / 2.0
        if risk_score >= 4.0:
            return "Zero Trust continuous verification; session recording."
        if risk_score >= 2.5:
            return "Adaptive step-up controls; focused monitoring."
        return "Baseline RBAC; emphasize awareness."

    def _score_metrics(
        self,
        questions: Dict[str, DwfQuestion],
        responses: Iterable[DwfResponse],
    ) -> Dict[str, Dict[str, float]]:
        totals: Dict[str, Dict[str, float]] = defaultdict(lambda: {"sum": 0.0, "weight": 0.0})
        for r in responses:
            q = questions.get(r.q_id)
            if not q or not q.metric_key:
                continue
            weight = q.weight if q.weight is not None else 1.0
            totals[q.metric_key]["sum"] += (r.score_achieved or 0.0) * weight
            totals[q.metric_key]["weight"] += weight
        results: Dict[str, float] = {}
        for key, agg in totals.items():
            if agg["weight"] > 0:
                results[key] = round(agg["sum"] / agg["weight"], 3)
        return {"metrics": results, "raw": totals}

    def compute_analysis(
        self,
        questions: List[DwfQuestion],
        responses: List[DwfResponse],
    ) -> Dict[str, Dict[str, float]]:
        q_map = {q.q_id: q for q in questions}
        by_persona: Dict[str, List[DwfResponse]] = defaultdict(list)
        for r in responses:
            q = q_map.get(r.q_id)
            persona = (q.persona_scope if q and q.persona_scope else "All")
            by_persona[persona].append(r)

        personas: Dict[str, Dict[str, float]] = {}
        for persona, resp_list in by_persona.items():
            scored = self._score_metrics(q_map, resp_list)
            metrics = scored["metrics"]
            likelihood = metrics.get("risk_likelihood")
            impact = metrics.get("risk_impact")
            personas[persona] = {
                **metrics,
                "risk_likelihood": likelihood,
                "risk_impact": impact,
                "risk_tolerance": self._risk_tolerance(likelihood, impact),
                "risk_recommendation": self._risk_recommendation(likelihood, impact),
            }
        return {
            "summary": self._score_metrics(q_map, responses)["metrics"],
            "personas": personas,
        }
