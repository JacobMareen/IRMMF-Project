from __future__ import annotations

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.third_party import models
from app.modules.third_party.schemas import ThirdPartyAssessmentIn, ThirdPartyAssessmentUpdate, ThirdPartyResponseIn
from app.modules.third_party.question_bank import get_question_bank


class ThirdPartyService:
    def __init__(self, db: Session):
        self.db = db

    def list_assessments(self, tenant_key: str) -> List[models.ThirdPartyAssessment]:
        return (
            self.db.query(models.ThirdPartyAssessment)
            .filter(models.ThirdPartyAssessment.tenant_key == tenant_key)
            .order_by(models.ThirdPartyAssessment.created_at.desc())
            .all()
        )

    def get_questions(self) -> List[Dict[str, Any]]:
        return get_question_bank()

    def create_assessment(
        self,
        tenant_key: str,
        assessment_id: str,
        payload: ThirdPartyAssessmentIn,
    ) -> models.ThirdPartyAssessment:
        assessment = models.ThirdPartyAssessment(
            tenant_key=tenant_key,
            assessment_id=assessment_id,
            partner_name=payload.partner_name,
            partner_type=payload.partner_type or "Supplier",
            risk_tier=payload.risk_tier or "Tier-2",
            status=payload.status or "draft",
            summary=payload.summary,
            responses=payload.responses,
            score=payload.score,
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_assessment(self, third_party_id: str, tenant_key: str) -> models.ThirdPartyAssessment:
        return self._get_assessment(third_party_id, tenant_key)

    def update_assessment(
        self,
        third_party_id: str,
        payload: ThirdPartyAssessmentUpdate,
        tenant_key: str,
    ) -> models.ThirdPartyAssessment:
        assessment = self._get_assessment(third_party_id, tenant_key)
        updates = payload.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(assessment, key, value)
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def submit_responses(
        self,
        third_party_id: str,
        payload: ThirdPartyResponseIn,
        tenant_key: str,
    ) -> models.ThirdPartyAssessment:
        assessment = self._get_assessment(third_party_id, tenant_key)
        resolved, total_questions = self._resolve_responses(payload)
        computed = self._score_responses(resolved, total_questions)
        responses_payload = {
            "responses": resolved,
            "computed": computed,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        assessment.responses = responses_payload
        assessment.score = computed.get("score")
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_analysis(self, third_party_id: str, tenant_key: str) -> Dict[str, Any]:
        assessment = self._get_assessment(third_party_id, tenant_key)
        total_questions = len(self.get_questions())
        responses_payload = assessment.responses if isinstance(assessment.responses, dict) else {}
        computed = responses_payload.get("computed") if isinstance(responses_payload, dict) else None
        if isinstance(computed, dict) and computed.get("score") is not None:
            answered = int(computed.get("answered") or 0)
            coverage = float(computed.get("coverage") or (answered / total_questions if total_questions else 0.0))
            risk_band = computed.get("risk_band") or self._risk_band(computed.get("score"))
            return {
                "partner_id": str(assessment.id),
                "assessment_id": assessment.assessment_id,
                "partner_name": assessment.partner_name,
                "score": computed.get("score"),
                "risk_band": risk_band,
                "answered": answered,
                "total": total_questions,
                "coverage": coverage,
                "responses": responses_payload,
            }

        resolved = self._resolve_from_payload(responses_payload)
        computed = self._score_responses(resolved, total_questions)
        return {
            "partner_id": str(assessment.id),
            "assessment_id": assessment.assessment_id,
            "partner_name": assessment.partner_name,
            "score": computed.get("score"),
            "risk_band": computed.get("risk_band"),
            "answered": computed.get("answered"),
            "total": computed.get("total"),
            "coverage": computed.get("coverage"),
            "responses": responses_payload,
        }

    def _get_assessment(self, third_party_id: str, tenant_key: str) -> models.ThirdPartyAssessment:
        try:
            assessment_uuid = uuid.UUID(third_party_id)
        except ValueError as exc:
            raise ValueError("Invalid third-party assessment id.") from exc
        assessment = (
            self.db.query(models.ThirdPartyAssessment)
            .filter_by(id=assessment_uuid)
            .first()
        )
        if not assessment or assessment.tenant_key != tenant_key:
            raise ValueError("Third-party assessment not found for tenant.")
        return assessment

    def _resolve_responses(self, payload: ThirdPartyResponseIn) -> tuple[List[Dict[str, Any]], int]:
        bank = self.get_questions()
        q_index = {q["q_id"]: q for q in bank}
        errors: List[str] = []
        resolved: List[Dict[str, Any]] = []
        for answer in payload.responses:
            q = q_index.get(answer.q_id)
            if not q:
                errors.append(f"Unknown question {answer.q_id}")
                continue
            options = q.get("options") or []
            opt = next((item for item in options if item.get("a_id") == answer.a_id), None)
            if not opt:
                errors.append(f"Unknown option {answer.a_id} for {answer.q_id}")
                continue
            weight = float(q.get("weight") or 1.0)
            resolved.append(
                {
                    "q_id": q.get("q_id"),
                    "a_id": opt.get("a_id"),
                    "category": q.get("category"),
                    "question_text": q.get("question_text"),
                    "answer_text": opt.get("label"),
                    "score": float(opt.get("score") or 0.0),
                    "weight": weight,
                }
            )
        if errors:
            raise ValueError("; ".join(errors))
        return resolved, len(bank)

    def _resolve_from_payload(self, responses_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not isinstance(responses_payload, dict):
            return []
        raw = responses_payload.get("responses")
        if not isinstance(raw, list):
            return []
        resolved: List[Dict[str, Any]] = []
        bank_index = {q["q_id"]: q for q in self.get_questions()}
        for item in raw:
            if not isinstance(item, dict):
                continue
            if "score" in item and "weight" in item:
                resolved.append(item)
                continue
            q_id = item.get("q_id")
            a_id = item.get("a_id")
            if not q_id or not a_id:
                continue
            q = bank_index.get(q_id)
            if not q:
                continue
            opt = next((opt for opt in q.get("options", []) if opt.get("a_id") == a_id), None)
            if not opt:
                continue
            resolved.append(
                {
                    "q_id": q.get("q_id"),
                    "a_id": opt.get("a_id"),
                    "category": q.get("category"),
                    "question_text": q.get("question_text"),
                    "answer_text": opt.get("label"),
                    "score": float(opt.get("score") or 0.0),
                    "weight": float(q.get("weight") or 1.0),
                }
            )
        return resolved

    def _score_responses(self, resolved: List[Dict[str, Any]], total_questions: int) -> Dict[str, Any]:
        total_weight = sum(float(item.get("weight") or 1.0) for item in resolved)
        if total_weight <= 0:
            score = None
        else:
            weighted_sum = sum(float(item.get("score") or 0.0) * float(item.get("weight") or 1.0) for item in resolved)
            score = round(weighted_sum / total_weight, 2)
        answered = len(resolved)
        coverage = round(answered / total_questions, 3) if total_questions else 0.0
        risk_band = self._risk_band(score)
        return {
            "score": score,
            "risk_band": risk_band,
            "answered": answered,
            "total": total_questions,
            "coverage": coverage,
        }

    def _risk_band(self, score: Optional[float]) -> Optional[str]:
        if score is None:
            return None
        if score >= 3.2:
            return "Low"
        if score >= 2.4:
            return "Moderate"
        if score >= 1.6:
            return "Elevated"
        return "High"
