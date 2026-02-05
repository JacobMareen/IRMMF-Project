import uuid
from typing import List, Optional
from datetime import datetime, timezone, date

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    case,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# --- UTILITIES ---

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass


class InsiderRiskPolicy(Base):
    """Tenant-specific insider risk policy definition."""
    __tablename__ = "insider_risk_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(64), nullable=False, default="Draft")
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0")
    owner: Mapped[str] = mapped_column(String(128), nullable=True)
    approval: Mapped[str] = mapped_column(String(128), nullable=True)
    scope: Mapped[str] = mapped_column(Text, nullable=True)

    last_reviewed: Mapped[date] = mapped_column(Date, nullable=True)
    next_review: Mapped[date] = mapped_column(Date, nullable=True)

    principles: Mapped[list[str]] = mapped_column(JSONB, nullable=True)
    sections: Mapped[list[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_key", name="uq_insider_risk_policy_tenant"),
    )


class InsiderRiskControl(Base):
    """Controls derived from the insider risk policy and assessment actions."""
    __tablename__ = "insider_risk_controls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    control_id: Mapped[str] = mapped_column(String(64), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=True)
    domain: Mapped[str] = mapped_column(String(64), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    owner: Mapped[str] = mapped_column(String(128), nullable=True)
    frequency: Mapped[str] = mapped_column(String(64), nullable=True)
    evidence: Mapped[str] = mapped_column(Text, nullable=True)

    last_reviewed: Mapped[date] = mapped_column(Date, nullable=True)
    next_review: Mapped[date] = mapped_column(Date, nullable=True)

    linked_actions: Mapped[list[str]] = mapped_column(JSONB, nullable=True)
    linked_rec_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=True)
    linked_categories: Mapped[list[str]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_key", "control_id", name="uq_insider_risk_control_tenant"),
        Index("ix_insider_risk_controls_tenant_domain", "tenant_key", "domain"),
    )


class InsiderRiskRoadmapItem(Base):
    """Roadmap milestones for the insider risk program."""
    __tablename__ = "insider_risk_roadmap_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    phase: Mapped[str] = mapped_column(String(32), nullable=False, default="Now")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    owner: Mapped[str] = mapped_column(String(128), nullable=True)
    target_window: Mapped[str] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_insider_risk_roadmap_tenant_phase", "tenant_key", "phase"),
    )
