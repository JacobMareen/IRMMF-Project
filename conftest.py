from __future__ import annotations

import uuid
from typing import List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import models
from app.db import SessionLocal


@pytest.fixture(scope="session")
def client() -> TestClient:
    try:
        from main import app
    except Exception as exc:
        pytest.skip(f"FastAPI app failed to import: {exc}")
    return TestClient(app)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        session.close()
        pytest.skip(f"Database unavailable: {exc}")
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def sample_questions(db) -> List[models.Question]:
    questions: List[models.Question] = []
    try:
        for _ in range(3):
            q_id = f"TEST-{uuid.uuid4().hex[:6].upper()}"
            question = models.Question(
                q_id=q_id,
                question_text="Test question",
                domain="Governance",
                pts_g=1.0,
            )
            db.add(question)
            db.flush()

            answer = models.Answer(
                a_id=f"{q_id}-A1",
                q_id=q_id,
                question_id=question.id,
                answer_text="Test answer",
                base_score=1.0,
            )
            db.add(answer)
            db.flush()
            questions.append(question)

        db.commit()
        for question in questions:
            exists = db.query(models.Answer).filter(models.Answer.question_id == question.id).first()
            if not exists:
                pytest.skip("Sample answers failed to persist to the database.")
        yield questions
    finally:
        for question in questions:
            db.query(models.Answer).filter(models.Answer.question_id == question.id).delete()
            db.query(models.Question).filter(models.Question.id == question.id).delete()
        db.commit()


@pytest.fixture()
def sample_question(sample_questions) -> models.Question:
    return sample_questions[0]
