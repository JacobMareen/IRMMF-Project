from __future__ import annotations

import uuid
from datetime import datetime, timezone, date

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Boolean, Date
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _default_jurisdiction_rules() -> dict:
    return {
        "BE": {
            "decision_deadline_days": 3,
            "dismissal_deadline_days": 3,
            "deadline_type": "working_days",
            "requires_registered_mail_receipt": True,
        },
        "NL": {
            "decision_deadline_hours": 48,
            "deadline_type": "hours",
            "requires_suspension_check": True,
        },
        "LU": {
            "min_cooling_off_days": 1,
            "max_dismissal_window_days": 8,
            "trigger_event": "pre_dismissal_interview",
        },
        "IE": {
            "warn_if_decision_under_hours": 24,
            "requires_appeal_checkbox": True,
        },
    }


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Default Tenant")
    environment_type: Mapped[str] = mapped_column(String(32), nullable=False, default="Production")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    settings: Mapped["TenantSettings"] = relationship("TenantSettings", back_populates="tenant", uselist=False)


class TenantSettings(Base):
    __tablename__ = "tenant_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, unique=True, index=True)

    company_name: Mapped[str] = mapped_column(String(255), nullable=True)
    default_jurisdiction: Mapped[str] = mapped_column(String(64), nullable=False, default="Belgium")
    investigation_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    keyword_flagging_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    keyword_list: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    weekend_days: Mapped[list] = mapped_column(JSONB, nullable=False, default=lambda: [5, 6])
    saturday_is_business_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deadline_cutoff_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=17)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    serious_cause_notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    jurisdiction_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=_default_jurisdiction_rules)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="settings")


class TenantHoliday(Base):
    __tablename__ = "tenant_holidays"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
