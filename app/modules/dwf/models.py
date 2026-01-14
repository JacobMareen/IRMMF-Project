from datetime import datetime, timezone
from typing import List

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DwfAssessment(Base):
    __tablename__ = "dwf_assessments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class DwfQuestion(Base):
    __tablename__ = "dwf_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    q_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    section: Mapped[str] = mapped_column(String(128), nullable=True)
    category: Mapped[str] = mapped_column(String(128), nullable=True)
    question_title: Mapped[str] = mapped_column(String(255), nullable=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    guidance: Mapped[str] = mapped_column(Text, nullable=True)

    input_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Single")
    list_ref: Mapped[str] = mapped_column(String(128), nullable=True)
    metric_key: Mapped[str] = mapped_column(String(128), nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=True)
    persona_scope: Mapped[str] = mapped_column(String(128), nullable=True)

    options: Mapped[List["DwfAnswerOption"]] = relationship(
        "DwfAnswerOption",
        back_populates="question",
        cascade="all, delete-orphan",
        primaryjoin="DwfQuestion.q_id==DwfAnswerOption.q_id",
        uselist=True,
        lazy="selectin",
    )


class DwfAnswerOption(Base):
    __tablename__ = "dwf_answer_options"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    a_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    q_id: Mapped[str] = mapped_column(String(64), ForeignKey("dwf_questions.q_id"), nullable=False, index=True)
    option_number: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    base_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tags: Mapped[str] = mapped_column(String(255), nullable=True)

    question: Mapped["DwfQuestion"] = relationship("DwfQuestion", back_populates="options")


class DwfListOption(Base):
    __tablename__ = "dwf_list_options"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    list_ref: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("list_ref", "value", name="uq_dwf_list_ref_value"),)


class DwfResponse(Base):
    __tablename__ = "dwf_responses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(128), ForeignKey("dwf_assessments.assessment_id"), nullable=False, index=True)
    q_id: Mapped[str] = mapped_column(String(64), ForeignKey("dwf_questions.q_id"), nullable=False)
    a_id: Mapped[str] = mapped_column(String(64), ForeignKey("dwf_answer_options.a_id"), nullable=True)
    score_achieved: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (UniqueConstraint("assessment_id", "q_id", name="uq_dwf_assessment_q"),)


class DwfPersonaScore(Base):
    __tablename__ = "dwf_persona_scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(128), ForeignKey("dwf_assessments.assessment_id"), nullable=False, index=True)
    persona_scope: Mapped[str] = mapped_column(String(128), nullable=True)

    risk_likelihood: Mapped[float] = mapped_column(Float, nullable=True)
    risk_impact: Mapped[float] = mapped_column(Float, nullable=True)
    risk_tolerance: Mapped[str] = mapped_column(String(64), nullable=True)

    culture_attitudes: Mapped[float] = mapped_column(Float, nullable=True)
    culture_behaviors: Mapped[float] = mapped_column(Float, nullable=True)
    culture_cognition: Mapped[float] = mapped_column(Float, nullable=True)
    culture_communication: Mapped[float] = mapped_column(Float, nullable=True)
    culture_compliance: Mapped[float] = mapped_column(Float, nullable=True)
    culture_norms: Mapped[float] = mapped_column(Float, nullable=True)
    culture_responsibilities: Mapped[float] = mapped_column(Float, nullable=True)

    friction_score: Mapped[float] = mapped_column(Float, nullable=True)
    mice_money: Mapped[float] = mapped_column(Float, nullable=True)
    mice_ideology: Mapped[float] = mapped_column(Float, nullable=True)
    mice_coercion: Mapped[float] = mapped_column(Float, nullable=True)
    mice_ego: Mapped[float] = mapped_column(Float, nullable=True)
    dark_mach: Mapped[float] = mapped_column(Float, nullable=True)
    dark_narc: Mapped[float] = mapped_column(Float, nullable=True)
    dark_psy: Mapped[float] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DwfReportSnapshot(Base):
    __tablename__ = "dwf_report_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(128), ForeignKey("dwf_assessments.assessment_id"), nullable=False, index=True)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
