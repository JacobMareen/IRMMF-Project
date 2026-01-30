from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.modules.dwf import models as dwf
from app.modules.dwf import schemas
from app.modules.dwf.engine import DwfScoringEngine
from app import models as core_models


class DwfService:
    def __init__(self, db: Session):
        self.db = db
        self.engine = DwfScoringEngine()

    def register_assessment(self, assessment_id: str, tenant_key: str | None = None) -> str:
        if tenant_key:
            self._assert_assessment_tenant(assessment_id, tenant_key)
        existing = (
            self.db.query(dwf.DwfAssessment)
            .filter_by(assessment_id=assessment_id)
            .first()
        )
        if existing:
            return assessment_id
        self.db.add(dwf.DwfAssessment(assessment_id=assessment_id, tenant_key=tenant_key))
        self.db.commit()
        return assessment_id

    def get_questions(self) -> List[dwf.DwfQuestion]:
        return self.db.query(dwf.DwfQuestion).all()

    def submit_answer(self, payload: schemas.DwfResponseCreate, tenant_key: str | None = None) -> Dict[str, Any]:
        self.register_assessment(payload.assessment_id, tenant_key=tenant_key)
        stmt = insert(dwf.DwfResponse).values(
            assessment_id=payload.assessment_id,
            q_id=payload.q_id,
            a_id=payload.a_id,
            score_achieved=payload.score,
            notes=payload.notes,
        ).on_conflict_do_update(
            index_elements=["assessment_id", "q_id"],
            set_={
                "a_id": payload.a_id,
                "score_achieved": payload.score,
                "notes": payload.notes,
            },
        )
        self.db.execute(stmt)
        self.db.commit()
        return {"status": "ok"}

    def get_analysis(self, assessment_id: str, tenant_key: str | None = None) -> Dict[str, Any]:
        if tenant_key:
            self._assert_assessment_tenant(assessment_id, tenant_key)
        questions = self.db.query(dwf.DwfQuestion).all()
        responses = (
            self.db.query(dwf.DwfResponse)
            .filter_by(assessment_id=assessment_id)
            .all()
        )
        result = self.engine.compute_analysis(questions, responses)
        snapshot = dwf.DwfReportSnapshot(assessment_id=assessment_id, snapshot=result)
        self.db.add(snapshot)
        self.db.commit()
        return result

    def _assert_assessment_tenant(self, assessment_id: str, tenant_key: str) -> None:
        assessment = (
            self.db.query(core_models.Assessment)
            .filter_by(assessment_id=assessment_id)
            .first()
        )
        if assessment and assessment.tenant_key and assessment.tenant_key != tenant_key:
            raise ValueError("Assessment not found for tenant.")
