from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
import uuid


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PiaCase(Base):
    __tablename__ = "pia_cases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    case_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    jurisdiction: Mapped[str] = mapped_column(String(64), nullable=False, default="Belgium")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    current_step: Mapped[str] = mapped_column(String(64), nullable=False, default="legitimacy")
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    outcome: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    case_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=True, default=dict)
    created_by: Mapped[str] = mapped_column(String(128), nullable=True)
    company_id: Mapped[str] = mapped_column(String(128), nullable=True)
    is_anonymized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anonymized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Integration pending: add assessment_id linkage once assessment integration is enabled.

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class PiaStepLog(Base):
    __tablename__ = "pia_step_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("pia_cases.case_id"), nullable=False, index=True)
    step_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="in_progress")
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    completed_by: Mapped[str] = mapped_column(String(128), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("case_id", "step_key", name="uq_pia_case_step"),)


class PiaAuditEvent(Base):
    __tablename__ = "pia_audit_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("pia_cases.case_id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
