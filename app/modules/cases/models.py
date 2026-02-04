from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    case_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4)
    tenant_key: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    created_by: Mapped[str] = mapped_column(String(128), nullable=True)
    company_id: Mapped[str] = mapped_column(String(128), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    jurisdiction: Mapped[str] = mapped_column(String(64), nullable=False, default="Belgium")
    vip_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    external_report_id: Mapped[str] = mapped_column(String(128), nullable=True)
    reporter_channel_id: Mapped[str] = mapped_column(String(128), nullable=True)
    reporter_key: Mapped[str] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    stage: Mapped[str] = mapped_column(String(64), nullable=False, default="INTAKE")
    case_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    is_anonymized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anonymized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    serious_cause_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    date_incident_occurred: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    date_investigation_started: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CaseSubject(Base):
    __tablename__ = "case_subjects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reference: Mapped[str] = mapped_column(String(128), nullable=True)
    manager_name: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseEvidenceItem(Base):
    __tablename__ = "case_evidence_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    evidence_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    link: Mapped[str] = mapped_column(String(512), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    evidence_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="registered")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseEvidenceSuggestion(Base):
    __tablename__ = "case_evidence_suggestions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    suggestion_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    playbook_key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (UniqueConstraint("case_id", "suggestion_id", name="uq_case_suggestion"),)


class CaseDocument(Base):
    __tablename__ = "case_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    format: Mapped[str] = mapped_column(String(16), nullable=False, default="txt")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    redaction_log: Mapped[dict] = mapped_column(JSONB, nullable=True)
    storage_uri: Mapped[str] = mapped_column(String(512), nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (UniqueConstraint("case_id", "doc_type", "version", name="uq_case_doc_version"),)


class CaseTask(Base):
    __tablename__ = "case_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    assignee: Mapped[str] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CaseLink(Base):
    __tablename__ = "case_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    linked_case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False, default="RELATED")
    created_by: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (UniqueConstraint("case_id", "linked_case_id", "relation_type", name="uq_case_link_pair"),)


class CaseLegalHold(Base):
    __tablename__ = "case_legal_holds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    hold_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=True)
    contact_role: Mapped[str] = mapped_column(String(255), nullable=True)
    preservation_scope: Mapped[str] = mapped_column(Text, nullable=True)
    delivery_channel: Mapped[str] = mapped_column(String(64), nullable=True)
    access_code: Mapped[str] = mapped_column(String(64), nullable=True)
    conflict_override_reason: Mapped[str] = mapped_column(Text, nullable=True)
    conflict_override_by: Mapped[str] = mapped_column(String(128), nullable=True)
    document_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("case_documents.id"), nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseExpertAccess(Base):
    __tablename__ = "case_expert_access"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    access_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expert_email: Mapped[str] = mapped_column(String(255), nullable=False)
    expert_name: Mapped[str] = mapped_column(String(255), nullable=True)
    organization: Mapped[str] = mapped_column(String(255), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    granted_by: Mapped[str] = mapped_column(String(128), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[str] = mapped_column(String(128), nullable=True)


class CaseTriageTicket(Base):
    __tablename__ = "case_triage_tickets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    tenant_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reporter_name: Mapped[str] = mapped_column(String(255), nullable=True)
    reporter_email: Mapped[str] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="dropbox")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    triage_notes: Mapped[str] = mapped_column(Text, nullable=True)
    linked_case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CaseReporterMessage(Base):
    __tablename__ = "case_reporter_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(32), nullable=False, default="reporter")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseStatusEvent(Base):
    __tablename__ = "case_status_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseGateRecord(Base):
    __tablename__ = "case_gate_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    gate_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    completed_by: Mapped[str] = mapped_column(String(128), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (UniqueConstraint("case_id", "gate_key", name="uq_case_gate_record"),)


class CaseNote(Base):
    __tablename__ = "case_notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    note_type: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(128), nullable=True)
    flags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseContentFlag(Base):
    __tablename__ = "case_content_flags"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    note_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("case_notes.id"), nullable=True, index=True)
    flag_type: Mapped[str] = mapped_column(String(64), nullable=False, default="keyword")
    terms: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    resolved_by: Mapped[str] = mapped_column(String(128), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseAuditEvent(Base):
    __tablename__ = "case_audit_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CaseSeriousCause(Base):
    __tablename__ = "case_serious_cause"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    facts_confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissal_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissal_recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    reasons_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    reasons_delivery_method: Mapped[str] = mapped_column(String(64), nullable=True)
    reasons_delivery_proof_uri: Mapped[str] = mapped_column(String(512), nullable=True)
    override_reason: Mapped[str] = mapped_column(Text, nullable=True)
    override_by: Mapped[str] = mapped_column(String(128), nullable=True)
    missed_acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    missed_acknowledged_by: Mapped[str] = mapped_column(String(128), nullable=True)
    missed_acknowledged_reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CaseOutcome(Base):
    __tablename__ = "case_outcomes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, unique=True, index=True)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False, default="PENDING")
    decision: Mapped[str] = mapped_column(String(128), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str] = mapped_column(String(128), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    role_separation_override_reason: Mapped[str] = mapped_column(Text, nullable=True)
    role_separation_override_by: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CaseErasureJob(Base):
    __tablename__ = "case_erasure_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    execute_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str] = mapped_column(String(128), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    certificate_doc_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("case_documents.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class DashboardAlertEvent(Base):
    __tablename__ = "dashboard_alert_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    alert_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="warning")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class CaseNotification(Base):
    __tablename__ = "case_notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id"), nullable=False, index=True)
    tenant_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    recipient_role: Mapped[str] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
