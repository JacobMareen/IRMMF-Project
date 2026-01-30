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

# --- DIMENSION TABLES (Static Data) ---

class QuestionBank(Base):
    """Provenance for the Excel bank used to populate dim_* tables."""
    __tablename__ = "question_banks"

    bank_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(64), index=True)
    source_file: Mapped[str] = mapped_column(String(255))
    source_sha256: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Question(Base):
    __tablename__ = "dim_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    q_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    tier: Mapped[str] = mapped_column(String, nullable=True)
    pack_section: Mapped[str] = mapped_column(String, nullable=True)
    axis1: Mapped[str] = mapped_column(String, nullable=True)
    w1: Mapped[float] = mapped_column(Float, nullable=True)
    axis2: Mapped[str] = mapped_column(String, nullable=True)
    w2: Mapped[float] = mapped_column(Float, nullable=True)
    pts_g: Mapped[float] = mapped_column(Float, nullable=True)
    pts_e: Mapped[float] = mapped_column(Float, nullable=True)
    pts_t: Mapped[float] = mapped_column(Float, nullable=True)
    pts_l: Mapped[float] = mapped_column(Float, nullable=True)
    pts_h: Mapped[float] = mapped_column(Float, nullable=True)
    pts_v: Mapped[float] = mapped_column(Float, nullable=True)
    pts_r: Mapped[float] = mapped_column(Float, nullable=True)
    pts_f: Mapped[float] = mapped_column(Float, nullable=True)
    pts_w: Mapped[float] = mapped_column(Float, nullable=True)

    question_title: Mapped[str] = mapped_column(String, nullable=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    guidance: Mapped[str] = mapped_column(Text, nullable=True)
    evidence_policy_id: Mapped[str] = mapped_column(String, nullable=True)

    cw: Mapped[float] = mapped_column(Float, nullable=True)
    th: Mapped[float] = mapped_column(Float, nullable=True)
    scope: Mapped[str] = mapped_column(String, nullable=True)

    branch_type: Mapped[str] = mapped_column(String, nullable=True)
    gate_threshold: Mapped[float] = mapped_column(Float, nullable=True)
    next_if_low: Mapped[str] = mapped_column(String, nullable=True)
    next_if_high: Mapped[str] = mapped_column(String, nullable=True)
    next_default: Mapped[str] = mapped_column(String, nullable=True)
    end_flag: Mapped[str] = mapped_column(String, nullable=True)

    domain: Mapped[str] = mapped_column(String, nullable=True, index=True)
    function: Mapped[str] = mapped_column(String, nullable=True)
    sub_capability: Mapped[str] = mapped_column(String, nullable=True)
    map_score: Mapped[float] = mapped_column(Float, nullable=True)
    map_method: Mapped[str] = mapped_column(String, nullable=True)
    q_id_display: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships
    options: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan",
        primaryjoin="Question.id==Answer.question_id",
        uselist=True,
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_dim_questions_domain_tier", "domain", "tier"),
    )

class Answer(Base):
    __tablename__ = "dim_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    a_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    q_id: Mapped[str] = mapped_column(String(64), nullable=True) # Logic/Display ID
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("dim_questions.id"), nullable=False, index=True)

    option_number: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    base_score: Mapped[float] = mapped_column(Float, nullable=True)
    
    pts_g: Mapped[float] = mapped_column(Float, nullable=True)
    pts_e: Mapped[float] = mapped_column(Float, nullable=True)
    pts_t: Mapped[float] = mapped_column(Float, nullable=True)
    pts_l: Mapped[float] = mapped_column(Float, nullable=True)
    pts_h: Mapped[float] = mapped_column(Float, nullable=True)
    pts_v: Mapped[float] = mapped_column(Float, nullable=True)
    pts_r: Mapped[float] = mapped_column(Float, nullable=True)
    pts_f: Mapped[float] = mapped_column(Float, nullable=True)
    pts_w: Mapped[float] = mapped_column(Float, nullable=True)

    tags: Mapped[str] = mapped_column(String, nullable=True)
    fracture_type: Mapped[str] = mapped_column(String, nullable=True)
    follow_up_trigger: Mapped[str] = mapped_column(String, nullable=True)
    negative_control: Mapped[str] = mapped_column(String, nullable=True)
    evidence_hint: Mapped[str] = mapped_column(Text, nullable=True)

    question: Mapped["Question"] = relationship("Question", back_populates="options")

class IntakeQuestion(Base):
    __tablename__ = "dim_intake_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    intake_q_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    section: Mapped[str] = mapped_column(String, nullable=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    guidance: Mapped[str] = mapped_column(Text, nullable=True)
    input_type: Mapped[str] = mapped_column(String, nullable=False, default="Single")
    list_ref: Mapped[str] = mapped_column(String, nullable=True)
    used_for: Mapped[str] = mapped_column(String, nullable=True)
    benchmark_weight: Mapped[float] = mapped_column(Float, nullable=True)
    depth_logic_ref: Mapped[str] = mapped_column(String, nullable=True)

class IntakeListOption(Base):
    __tablename__ = "dim_intake_list_options"

    list_ref: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    value: Mapped[str] = mapped_column(String, primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("list_ref", "value", name="uq_intake_list_ref_value"),
    )

# --- FACT TABLES (Transactional Data) ---

class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    tenant_key: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=True)
    depth: Mapped[str] = mapped_column(String(32), nullable=True)
    override_depth: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    benchmark_tags: Mapped[dict] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Response(Base):
    __tablename__ = "fact_responses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    
    # Links to Q_ID (Logic ID) rather than PK for easier querying, though PK FK is safer for integrity.
    # Current design assumes q_id is stable.
    q_id: Mapped[str] = mapped_column(String(64), ForeignKey("dim_questions.q_id"), nullable=False)
    a_id: Mapped[str] = mapped_column(String(64), ForeignKey("dim_answers.a_id"), nullable=False)
    
    pack_id: Mapped[str] = mapped_column(String(64), nullable=True)
    score_achieved: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # --- NEW FIELDS FOR P0-03 ---
    is_deferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Origin distinguishes adaptive-path answers from override exploration.
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="adaptive")
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=True)
    evidence_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    evidence_policy_id: Mapped[str] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("assessment_id", "q_id", name="uq_fact_responses_assessment_q"),
    )

class EvidenceResponse(Base):
    __tablename__ = "fact_evidence_responses"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(64), index=True)
    q_id: Mapped[str] = mapped_column(String(64))
    
    challenges_passed: Mapped[int] = mapped_column(Integer, default=0) 
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (UniqueConstraint("assessment_id", "q_id", name="uq_evidence_q"),)

class IntakeResponse(Base):
    __tablename__ = "fact_intake_responses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    intake_q_id: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    intake_question_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint("assessment_id", "intake_q_id", name="uq_fact_intake_assessment_q"),
    )

class ResponseAudit(Base):
    __tablename__ = "fact_response_audits"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(64), index=True)
    q_id: Mapped[str] = mapped_column(String(64))
    a_id: Mapped[str] = mapped_column(String(64))
    score_achieved: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    bank_version: Mapped[str] = mapped_column(String(64), nullable=True)

    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    top_findings: Mapped[dict] = mapped_column(JSONB, nullable=True)
    benchmark_tags: Mapped[dict] = mapped_column(JSONB, nullable=True)


# --- RECOMMENDATION TABLES ---

class Recommendation(Base):
    """Master library of reusable recommendations."""
    __tablename__ = "dim_recommendations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rec_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    # Categorization
    category = mapped_column(String(64), nullable=False)
    subcategory = mapped_column(String(64), nullable=True)

    # Content
    title = mapped_column(String(255), nullable=False)
    description = mapped_column(Text, nullable=False)
    rationale = mapped_column(Text, nullable=True)

    # Actionable Details (JSONB for flexibility)
    implementation_steps = mapped_column(JSONB, nullable=True)
    success_criteria = mapped_column(JSONB, nullable=True)
    prerequisites = mapped_column(ARRAY(String), nullable=True)

    # Effort & Timeline
    estimated_effort = mapped_column(String(32), nullable=True)
    typical_timeline = mapped_column(String(64), nullable=True)
    default_priority = mapped_column(String(16), nullable=False, default="Medium")

    # Resources
    vendor_suggestions = mapped_column(JSONB, nullable=True)
    external_resources = mapped_column(JSONB, nullable=True)

    # Linking Fields (for matching logic)
    target_axes = mapped_column(ARRAY(String(16)), nullable=True)
    relevant_scenarios = mapped_column(ARRAY(String(64)), nullable=True)
    relevant_questions = mapped_column(ARRAY(String(64)), nullable=True)

    # Triggering Logic
    trigger_rules = mapped_column(JSONB, nullable=True)

    # Metadata
    created_at = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    is_active = mapped_column(Boolean, default=True, nullable=False)
    version = mapped_column(String(16), nullable=True, default="1.0")

    __table_args__ = (
        Index("ix_dim_recs_category", "category"),
        Index("ix_dim_recs_target_axes", "target_axes", postgresql_using="gin"),
        Index("ix_dim_recs_scenarios", "relevant_scenarios", postgresql_using="gin"),
        Index("ix_dim_recs_active", "is_active", postgresql_where=text("is_active = TRUE")),
    )


class AssessmentRecommendation(Base):
    """Assessment-specific recommendation instance with status tracking."""
    __tablename__ = "fact_assessment_recommendations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("assessments.assessment_id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    rec_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("dim_recommendations.rec_id", ondelete="CASCADE"),
        nullable=False
    )

    # Personalization
    priority = mapped_column(String(16), nullable=False, default="Medium")
    custom_timeline = mapped_column(String(64), nullable=True)
    custom_notes = mapped_column(Text, nullable=True)

    # Status Tracking
    status = mapped_column(String(32), nullable=False, default="pending")

    # Linkage to Findings
    triggered_by_axes = mapped_column(ARRAY(String(16)), nullable=True)
    triggered_by_risks = mapped_column(ARRAY(String(64)), nullable=True)
    triggered_by_questions = mapped_column(ARRAY(String(64)), nullable=True)

    # Progress Tracking
    assigned_to = mapped_column(String(128), nullable=True)
    due_date = mapped_column(Date, nullable=True)
    started_at = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit Trail
    created_at = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    created_by = mapped_column(String(128), nullable=True)

    # Relationships
    recommendation: Mapped["Recommendation"] = relationship(
        "Recommendation", lazy="joined"
    )

    __table_args__ = (
        UniqueConstraint("assessment_id", "rec_id", name="uq_fact_assessment_rec"),
        Index("ix_fact_assessment_recs_status", "status"),
        Index("ix_fact_assessment_recs_priority", "priority"),
        Index("ix_fact_assessment_recs_due_date", "due_date",
              postgresql_where=text("due_date IS NOT NULL")),
    )


class RecommendationHistory(Base):
    """Audit trail for recommendation changes."""
    __tablename__ = "fact_recommendation_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    rec_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # What Changed
    field_changed = mapped_column(String(64), nullable=False)
    old_value = mapped_column(Text, nullable=True)
    new_value = mapped_column(Text, nullable=True)
    change_reason = mapped_column(Text, nullable=True)

    # Who & When
    changed_by = mapped_column(String(128), nullable=True)
    changed_at = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_fact_rec_history_assessment_rec", "assessment_id", "rec_id"),
        Index("ix_fact_rec_history_timestamp", "changed_at"),
    )


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
