"""Thin data-access helpers used by services to keep query logic centralized."""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert # USE POSTGRES DIALECT
from app import models

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
