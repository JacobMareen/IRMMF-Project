from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


CASE_STATUSES = {"OPEN", "ON_HOLD", "CLOSED", "ERASURE_PENDING", "ERASED"}
CASE_STAGES = {
    "INTAKE",
    "LEGITIMACY_GATE",
    "CREDENTIALING",
    "INVESTIGATION",
    "ADVERSARIAL_DEBATE",
    "DECISION",
    "CLOSURE",
}
CASE_LINK_RELATIONS = {"RELATED", "DUPLICATE", "PARENT", "CHILD"}

MAX_TINY_LEN = 64
MAX_SHORT_LEN = 200
MAX_SUMMARY_LEN = 2000
MAX_MEDIUM_LEN = 1000
MAX_LONG_LEN = 4000
MAX_URL_LEN = 2048
MAX_EMAIL_LEN = 320
MAX_ID_LEN = 128
MAX_DATE_LEN = 32


class CaseCreate(BaseModel):
    title: str = Field(max_length=MAX_SHORT_LEN)
    summary: Optional[str] = Field(default=None, max_length=MAX_SUMMARY_LEN)
    jurisdiction: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    vip_flag: Optional[bool] = None
    external_report_id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    reporter_channel_id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    reporter_key: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    urgent_dismissal: Optional[bool] = None
    subject_suspended: Optional[bool] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    summary: Optional[str] = Field(default=None, max_length=MAX_SUMMARY_LEN)
    jurisdiction: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    vip_flag: Optional[bool] = None
    external_report_id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    reporter_channel_id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    reporter_key: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    urgent_dismissal: Optional[bool] = None
    subject_suspended: Optional[bool] = None


class CaseStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in CASE_STATUSES:
            raise ValueError(f"Invalid status: {normalized}")
        return normalized


class CaseStageUpdate(BaseModel):
    stage: str

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in CASE_STAGES:
            raise ValueError(f"Invalid stage: {normalized}")
        return normalized


class CaseSubjectCreate(BaseModel):
    subject_type: str = Field(max_length=MAX_TINY_LEN)
    display_name: str = Field(max_length=MAX_SHORT_LEN)
    reference: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    manager_name: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)


class CaseLinkCreate(BaseModel):
    linked_case_id: str
    relation_type: str = "RELATED"

    @field_validator("relation_type")
    @classmethod
    def validate_relation_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in CASE_LINK_RELATIONS:
            raise ValueError(f"Invalid relation type: {normalized}")
        return normalized


class CaseLegalHoldCreate(BaseModel):
    contact_name: str = Field(max_length=MAX_SHORT_LEN)
    contact_email: Optional[str] = Field(default=None, max_length=MAX_EMAIL_LEN)
    contact_role: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    preservation_scope: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)
    delivery_channel: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    access_code: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    conflict_override_reason: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseExpertAccessCreate(BaseModel):
    expert_email: str = Field(max_length=MAX_EMAIL_LEN)
    expert_name: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    organization: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    reason: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)

    @field_validator("expert_email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip()
        if "@" not in email or "." not in email:
            raise ValueError("Expert email must be valid")
        return email


class CaseTriageTicketCreate(BaseModel):
    subject: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    message: str = Field(max_length=MAX_LONG_LEN)
    reporter_name: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    reporter_email: Optional[str] = Field(default=None, max_length=MAX_EMAIL_LEN)
    source: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("Message is required.")
        return message


class CaseTriageTicketUpdate(BaseModel):
    status: Optional[str] = None
    triage_notes: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in {"new", "triaged", "closed"}:
            raise ValueError("Invalid triage status")
        return normalized


class CaseTriageTicketConvert(BaseModel):
    case_title: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    case_summary: Optional[str] = Field(default=None, max_length=MAX_SUMMARY_LEN)
    jurisdiction: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    vip_flag: Optional[bool] = None


class CaseEvidenceCreate(BaseModel):
    label: str = Field(max_length=MAX_SHORT_LEN)
    source: str = Field(max_length=MAX_SHORT_LEN)
    link: Optional[str] = Field(default=None, max_length=MAX_URL_LEN)
    notes: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)
    evidence_hash: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)


class CaseTaskCreate(BaseModel):
    title: str = Field(max_length=MAX_SHORT_LEN)
    description: Optional[str] = Field(default=None, max_length=MAX_SUMMARY_LEN)
    task_type: Optional[str] = Field(default=None, max_length=MAX_TINY_LEN)
    status: Optional[str] = Field(default=None, max_length=MAX_TINY_LEN)
    due_at: Optional[datetime] = None
    assignee: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)


class CaseTaskUpdate(BaseModel):
    status: Optional[str] = None
    due_at: Optional[datetime] = None
    assignee: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in {"open", "in_progress", "completed"}:
            raise ValueError("Invalid task status")
        return normalized


class CaseNoteCreate(BaseModel):
    note_type: Optional[str] = Field(default=None, max_length=MAX_TINY_LEN)
    body: str = Field(max_length=MAX_LONG_LEN)


class CaseLegitimacyForm(BaseModel):
    legal_basis: str = Field(max_length=MAX_SHORT_LEN)
    trigger_summary: str = Field(max_length=MAX_LONG_LEN)
    proportionality_confirmed: bool
    less_intrusive_steps: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)
    mandate_owner: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    mandate_date: Optional[str] = Field(default=None, max_length=MAX_DATE_LEN)


class CaseCredentialingForm(BaseModel):
    investigator_name: str = Field(max_length=MAX_SHORT_LEN)
    investigator_role: str = Field(max_length=MAX_SHORT_LEN)
    licensed: bool
    license_id: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    conflict_check_passed: bool
    conflict_override_reason: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)
    authorizer: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    authorization_date: Optional[str] = Field(default=None, max_length=MAX_DATE_LEN)


class CaseAdversarialForm(BaseModel):
    invitation_sent: bool
    invitation_date: Optional[str] = Field(default=None, max_length=MAX_DATE_LEN)
    rights_acknowledged: bool
    representative_present: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    interview_summary: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseLegalApprovalForm(BaseModel):
    approved_at: Optional[str] = Field(default=None, max_length=MAX_DATE_LEN)
    approval_note: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseWorksCouncilForm(BaseModel):
    monitoring: bool
    approval_document_uri: Optional[str] = Field(default=None, max_length=MAX_URL_LEN)
    approval_received_at: Optional[str] = Field(default=None, max_length=MAX_DATE_LEN)
    approval_notes: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseTriageForm(BaseModel):
    impact: int
    probability: int
    risk_score: int
    outcome: str = Field(max_length=MAX_TINY_LEN)
    notes: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)
    trigger_source: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    business_impact: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)
    exposure_summary: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)
    data_sensitivity: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)
    stakeholders: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)
    confidence_level: Optional[str] = Field(default=None, max_length=MAX_TINY_LEN)
    recommended_actions: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)

    @field_validator("impact", "probability", "risk_score")
    @classmethod
    def validate_scores(cls, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("Score must be between 1 and 5.")
        return value

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, value: str) -> str:
        normalized = value.strip().upper()
        allowed = {"DISMISS", "ROUTE_TO_HR", "OPEN_FULL_INVESTIGATION"}
        if normalized not in allowed:
            raise ValueError("Invalid triage outcome.")
        return normalized


class CaseImpactAnalysisForm(BaseModel):
    estimated_loss: Optional[float] = None
    regulation_breached: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)
    operational_impact: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)
    reputational_impact: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)
    people_impact: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)
    financial_impact: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)


class CaseSeriousCauseUpsert(BaseModel):
    enabled: bool = True
    facts_confirmed_at: Optional[datetime] = None
    decision_due_at: Optional[datetime] = None
    dismissal_due_at: Optional[datetime] = None
    override_reason: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseSeriousCauseToggle(BaseModel):
    enabled: bool = True
    date_incident_occurred: Optional[datetime] = None
    date_investigation_started: Optional[datetime] = None
    decision_maker: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)


class CaseSubmitFindings(BaseModel):
    confirmed_at: Optional[datetime] = None
    decision_maker: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)


class CaseRecordDismissal(BaseModel):
    dismissal_recorded_at: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseRecordReasonsSent(BaseModel):
    sent_at: Optional[datetime] = None
    delivery_method: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    proof_uri: Optional[str] = Field(default=None, max_length=MAX_URL_LEN)


class CaseAcknowledgeMissed(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseAnonymizeRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseBreakGlassRequest(BaseModel):
    reason: str = Field(max_length=MAX_LONG_LEN)
    scope: Optional[str] = Field(default=None, max_length=MAX_MEDIUM_LEN)
    duration_minutes: Optional[int] = 60

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Break-glass reason required")
        return value.strip()

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value < 5 or value > 480:
            raise ValueError("Duration must be between 5 and 480 minutes")
        return value


class CaseBreakGlassOut(BaseModel):
    status: str
    expires_at: datetime


class CaseApplyPlaybook(BaseModel):
    playbook_key: str = Field(max_length=MAX_ID_LEN)


class CaseEvidenceSuggestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    suggestion_id: str
    playbook_key: str
    label: str
    source: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class CaseEvidenceSuggestionUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"open", "converted", "dismissed"}:
            raise ValueError("Invalid suggestion status")
        return normalized


class CasePlaybookOut(BaseModel):
    key: str
    title: str
    description: str


class CaseDocumentCreate(BaseModel):
    format: Optional[str] = Field(default=None, max_length=MAX_TINY_LEN)

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized in {"text", "plain"}:
            normalized = "txt"
        if normalized not in {"txt", "pdf", "docx"}:
            raise ValueError("Unsupported document format")
        return normalized


class CaseDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    doc_type: str
    version: int
    format: str
    title: str
    redaction_log: Optional[dict] = None
    created_by: Optional[str] = None
    created_at: datetime


class CaseExportRedactionCreate(BaseModel):
    redactions: list[dict] = []
    note: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseRemediationExportCreate(BaseModel):
    remediation_statement: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)
    format: Optional[str] = Field(default="json", max_length=MAX_TINY_LEN)


class CaseDecisionCreate(BaseModel):
    outcome: str = Field(max_length=MAX_SHORT_LEN)
    decision: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)
    summary: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)
    decided_at: Optional[datetime] = None
    role_separation_override_reason: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseOutcomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    outcome: str
    decision: Optional[str] = None
    summary: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    role_separation_override_reason: Optional[str] = None
    role_separation_override_by: Optional[str] = None
    updated_at: datetime


class CaseErasureApprove(BaseModel):
    execute_after: Optional[datetime] = None


class CaseErasureExecute(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=MAX_LONG_LEN)


class CaseErasureJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    requested_at: datetime
    execute_after: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    certificate_doc_id: Optional[int] = None


class CaseNotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: str
    tenant_key: str
    notification_type: str
    severity: str
    message: str
    recipient_role: Optional[str] = None
    status: str
    due_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    created_at: datetime


class CaseNotificationAck(BaseModel):
    status: Optional[str] = None
    updated_at: datetime


class CaseSubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    subject_type: str
    display_name: str
    reference: Optional[str] = None
    manager_name: Optional[str] = None
    created_at: datetime


class CaseEvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    evidence_id: str
    label: str
    source: str
    link: Optional[str] = None
    notes: Optional[str] = None
    evidence_hash: Optional[str] = None
    status: str
    created_at: datetime


class CaseTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: str
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    status: str
    due_at: Optional[datetime] = None
    assignee: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CaseLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: str
    linked_case_id: str
    relation_type: str
    created_by: Optional[str] = None
    created_at: datetime


class CaseLegalHoldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: str
    hold_id: str
    contact_name: str
    contact_email: Optional[str] = None
    contact_role: Optional[str] = None
    preservation_scope: Optional[str] = None
    delivery_channel: Optional[str] = None
    access_code: Optional[str] = None
    conflict_override_reason: Optional[str] = None
    conflict_override_by: Optional[str] = None
    document_id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: datetime


class CaseExpertAccessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: str
    access_id: str
    expert_email: str
    expert_name: Optional[str] = None
    organization: Optional[str] = None
    reason: Optional[str] = None
    status: str
    granted_by: Optional[str] = None
    granted_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None


class CaseTriageTicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: str
    tenant_key: str
    subject: Optional[str] = None
    message: str
    reporter_name: Optional[str] = None
    reporter_email: Optional[str] = None
    source: str
    status: str
    triage_notes: Optional[str] = None
    linked_case_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CaseSummaryDraftOut(BaseModel):
    summary: str
    note_count: int
    generated_at: datetime


class CaseRedactionSuggestionOut(BaseModel):
    value: str
    match_type: str
    source: str
    reason: str


class CaseOutcomeStat(BaseModel):
    outcome: str
    count: int
    percent: float


class CaseConsistencyOut(BaseModel):
    sample_size: int
    jurisdiction: str
    playbook_key: Optional[str] = None
    outcomes: List[CaseOutcomeStat]
    recommendation: str
    warning: Optional[str] = None


class CaseReporterMessageCreate(BaseModel):
    body: str = Field(max_length=MAX_LONG_LEN)


class CaseReporterMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    case_id: str
    sender: str
    body: str
    created_by: Optional[str] = None
    created_at: datetime


class CaseNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    note_type: str
    body: str
    created_by: Optional[str] = None
    flags: dict
    created_at: datetime


class CaseContentFlagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    note_id: Optional[int] = None
    flag_type: str
    terms: list
    status: str
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class CaseContentFlagUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"open", "resolved"}:
            raise ValueError("Invalid flag status")
        return normalized


class CaseAuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_type: str
    actor: Optional[str] = None
    message: str
    details: dict
    created_at: datetime


class CaseGateRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    gate_key: str
    status: str
    data: dict
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime


class CaseSanityCheckOut(BaseModel):
    score: int
    completed: int
    total: int
    missing: List[str]
    warnings: List[str]


class CaseSeriousCauseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    enabled: bool
    facts_confirmed_at: Optional[datetime] = None
    decision_due_at: Optional[datetime] = None
    dismissal_due_at: Optional[datetime] = None
    dismissal_recorded_at: Optional[datetime] = None
    reasons_sent_at: Optional[datetime] = None
    reasons_delivery_method: Optional[str] = None
    reasons_delivery_proof_uri: Optional[str] = None
    override_reason: Optional[str] = None
    override_by: Optional[str] = None
    missed_acknowledged_at: Optional[datetime] = None
    missed_acknowledged_by: Optional[str] = None
    missed_acknowledged_reason: Optional[str] = None
    updated_at: datetime


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    case_id: str
    case_uuid: str
    tenant_key: Optional[str] = None
    company_id: Optional[str] = None
    title: str
    summary: Optional[str] = None
    jurisdiction: str
    vip_flag: bool
    external_report_id: Optional[str] = None
    reporter_channel_id: Optional[str] = None
    reporter_key: Optional[str] = None
    status: str
    stage: str
    created_by: Optional[str] = None
    is_anonymized: bool
    anonymized_at: Optional[datetime] = None
    serious_cause_enabled: bool
    date_incident_occurred: Optional[datetime] = None
    date_investigation_started: Optional[datetime] = None
    remediation_statement: Optional[str] = None
    remediation_exported_at: Optional[datetime] = None
    urgent_dismissal: Optional[bool] = None
    subject_suspended: Optional[bool] = None
    evidence_locked: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    subjects: List[CaseSubjectOut]
    evidence: List[CaseEvidenceOut]
    tasks: List[CaseTaskOut]
    notes: List[CaseNoteOut]
    gates: List[CaseGateRecordOut]
    serious_cause: Optional[CaseSeriousCauseOut] = None
    outcome: Optional[CaseOutcomeOut] = None
    erasure_job: Optional[CaseErasureJobOut] = None
