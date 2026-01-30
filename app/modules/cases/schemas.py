from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


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


class CaseCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    jurisdiction: Optional[str] = None
    vip_flag: Optional[bool] = None
    external_report_id: Optional[str] = None
    reporter_channel_id: Optional[str] = None
    reporter_key: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    jurisdiction: Optional[str] = None
    vip_flag: Optional[bool] = None
    external_report_id: Optional[str] = None
    reporter_channel_id: Optional[str] = None
    reporter_key: Optional[str] = None


class CaseStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None

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
    subject_type: str
    display_name: str
    reference: Optional[str] = None
    manager_name: Optional[str] = None


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
    contact_name: str
    contact_email: Optional[str] = None
    contact_role: Optional[str] = None
    preservation_scope: Optional[str] = None
    delivery_channel: Optional[str] = None
    access_code: Optional[str] = None
    conflict_override_reason: Optional[str] = None


class CaseEvidenceCreate(BaseModel):
    label: str
    source: str
    link: Optional[str] = None
    notes: Optional[str] = None
    evidence_hash: Optional[str] = None


class CaseTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    status: Optional[str] = None
    due_at: Optional[datetime] = None
    assignee: Optional[str] = None


class CaseNoteCreate(BaseModel):
    note_type: Optional[str] = None
    body: str


class CaseLegitimacyForm(BaseModel):
    legal_basis: str
    trigger_summary: str
    proportionality_confirmed: bool
    less_intrusive_steps: Optional[str] = None
    mandate_owner: Optional[str] = None
    mandate_date: Optional[str] = None


class CaseCredentialingForm(BaseModel):
    investigator_name: str
    investigator_role: str
    licensed: bool
    license_id: Optional[str] = None
    conflict_check_passed: bool
    conflict_override_reason: Optional[str] = None
    authorizer: Optional[str] = None
    authorization_date: Optional[str] = None


class CaseAdversarialForm(BaseModel):
    invitation_sent: bool
    invitation_date: Optional[str] = None
    rights_acknowledged: bool
    representative_present: Optional[str] = None
    interview_summary: Optional[str] = None


class CaseSeriousCauseUpsert(BaseModel):
    enabled: bool = True
    facts_confirmed_at: Optional[datetime] = None
    decision_due_at: Optional[datetime] = None
    dismissal_due_at: Optional[datetime] = None
    override_reason: Optional[str] = None


class CaseSeriousCauseToggle(BaseModel):
    enabled: bool = True
    date_incident_occurred: Optional[datetime] = None
    date_investigation_started: Optional[datetime] = None
    decision_maker: Optional[str] = None


class CaseSubmitFindings(BaseModel):
    confirmed_at: Optional[datetime] = None
    decision_maker: Optional[str] = None


class CaseRecordDismissal(BaseModel):
    dismissal_recorded_at: Optional[datetime] = None
    notes: Optional[str] = None


class CaseRecordReasonsSent(BaseModel):
    sent_at: Optional[datetime] = None
    delivery_method: Optional[str] = None
    proof_uri: Optional[str] = None


class CaseAcknowledgeMissed(BaseModel):
    reason: Optional[str] = None


class CaseAnonymizeRequest(BaseModel):
    reason: Optional[str] = None


class CaseApplyPlaybook(BaseModel):
    playbook_key: str


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
    format: Optional[str] = None


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
    note: Optional[str] = None


class CaseRemediationExportCreate(BaseModel):
    remediation_statement: Optional[str] = None
    format: Optional[str] = "json"


class CaseDecisionCreate(BaseModel):
    outcome: str
    decision: Optional[str] = None
    summary: Optional[str] = None
    decided_at: Optional[datetime] = None
    role_separation_override_reason: Optional[str] = None


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
    reason: Optional[str] = None


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


class CaseReporterMessageCreate(BaseModel):
    body: str


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
