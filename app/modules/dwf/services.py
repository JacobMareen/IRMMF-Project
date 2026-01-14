from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.modules.dwf import models as dwf
from app.modules.dwf import schemas
from app.modules.dwf.engine import DwfScoringEngine


class DwfService:
    def __init__(self, db: Session):
        self.db = db
        self.engine = DwfScoringEngine()

    def register_assessment(self, assessment_id: str) -> str:
        existing = (
            self.db.query(dwf.DwfAssessment)
            .filter_by(assessment_id=assessment_id)
            .first()
        )
        if existing:
            return assessment_id
        self.db.add(dwf.DwfAssessment(assessment_id=assessment_id))
        self.db.commit()
        return assessment_id

    def get_questions(self) -> List[dwf.DwfQuestion]:
        return self.db.query(dwf.DwfQuestion).all()

    def submit_answer(self, payload: schemas.DwfResponseCreate) -> Dict[str, Any]:
        self.register_assessment(payload.assessment_id)
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

    def get_analysis(self, assessment_id: str) -> Dict[str, Any]:
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
