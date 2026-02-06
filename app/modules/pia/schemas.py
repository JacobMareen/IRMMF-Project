from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_KEY_LEN = 64
MAX_TITLE_LEN = 200
MAX_SHORT_LEN = 120
MAX_TEXT_LEN = 2000
MAX_LONG_LEN = 4000
MAX_TAG_LEN = 64
MAX_STATUS_LEN = 32
MAX_ID_LEN = 128
MAX_DATE_LEN = 32


class PiaKeyDate(BaseModel):
    date: str = Field(max_length=MAX_DATE_LEN)
    requirement: str = Field(max_length=MAX_TEXT_LEN)


class PiaBullet(BaseModel):
    title: str = Field(max_length=MAX_TITLE_LEN)
    detail: str = Field(max_length=MAX_TEXT_LEN)
    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: Optional[List[str]]):
        if value is None:
            return value
        for tag in value:
            if len(tag) > MAX_TAG_LEN:
                raise ValueError(f"Tag length must be <= {MAX_TAG_LEN}")
        return value


class PiaSection(BaseModel):
    key: str = Field(max_length=MAX_KEY_LEN)
    title: str = Field(max_length=MAX_TITLE_LEN)
    summary: str = Field(max_length=MAX_TEXT_LEN)
    bullets: List[PiaBullet]


class PiaRoadmapPhase(BaseModel):
    phase: str = Field(max_length=MAX_STATUS_LEN)
    focus: str = Field(max_length=MAX_TITLE_LEN)
    deliverables: List[str]

    @field_validator("deliverables")
    @classmethod
    def validate_deliverables(cls, value: List[str]):
        for item in value or []:
            if len(item) > MAX_TITLE_LEN:
                raise ValueError(f"Deliverable length must be <= {MAX_TITLE_LEN}")
        return value


class PiaOverview(BaseModel):
    module_key: str = Field(max_length=MAX_KEY_LEN)
    title: str = Field(max_length=MAX_TITLE_LEN)
    subtitle: str = Field(max_length=MAX_TITLE_LEN)
    executive_summary: str = Field(max_length=MAX_LONG_LEN)
    key_dates: List[PiaKeyDate]
    sections: List[PiaSection]
    roadmap: List[PiaRoadmapPhase]


class PiaWorkflowStep(BaseModel):
    key: str = Field(max_length=MAX_KEY_LEN)
    title: str = Field(max_length=MAX_TITLE_LEN)
    description: str = Field(max_length=MAX_TEXT_LEN)


class PiaEvidencePlaceholder(BaseModel):
    evidence_id: str = Field(max_length=MAX_ID_LEN)
    label: str = Field(max_length=MAX_TITLE_LEN)
    source: str = Field(max_length=MAX_SHORT_LEN)
    notes: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    status: str = Field(max_length=MAX_STATUS_LEN)
    created_at: str = Field(max_length=MAX_DATE_LEN)


class PiaCaseCreate(BaseModel):
    title: str = Field(max_length=MAX_TITLE_LEN)
    summary: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    jurisdiction: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    user_id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    company_id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)


class PiaCaseAdvance(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    completed_by: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)


class PiaEvidenceCreate(BaseModel):
    label: str = Field(max_length=MAX_TITLE_LEN)
    source: str = Field(max_length=MAX_SHORT_LEN)
    notes: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)


class PiaAnonymizeRequest(BaseModel):
    actor: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    reason: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)


class PiaLegitimacyForm(BaseModel):
    legal_basis: str = Field(max_length=MAX_TITLE_LEN)
    trigger_summary: str = Field(max_length=MAX_TEXT_LEN)
    proportionality_confirmed: bool
    less_intrusive_steps: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    mandate_owner: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    mandate_date: Optional[str] = Field(default=None, max_length=MAX_DATE_LEN)


class PiaAuthorizationForm(BaseModel):
    investigator_name: str = Field(max_length=MAX_SHORT_LEN)
    investigator_role: str = Field(max_length=MAX_SHORT_LEN)
    licensed: bool
    license_id: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    conflict_check_passed: bool
    authorizer: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    authorization_date: Optional[str] = Field(default=None, max_length=MAX_DATE_LEN)


class PiaEvidencePlanForm(BaseModel):
    collection_scope: str = Field(max_length=MAX_TEXT_LEN)
    chain_of_custody_owner: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    relevance_tagging_method: Optional[str] = Field(default=None, max_length=MAX_TITLE_LEN)
    minimization_notes: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)


class PiaInterviewForm(BaseModel):
    invitation_sent: bool
    invitation_date: Optional[str] = Field(default=None, max_length=MAX_DATE_LEN)
    rights_acknowledged: bool
    representative_present: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    interview_summary: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)


class PiaOutcomeForm(BaseModel):
    decision: str = Field(max_length=MAX_TITLE_LEN)
    sanction: Optional[str] = Field(default=None, max_length=MAX_TITLE_LEN)
    erasure_deadline: Optional[str] = Field(default=None, max_length=MAX_DATE_LEN)
    retention_rationale: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    outcome_notes: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)


class PiaCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    case_id: str
    case_uuid: str
    tenant_key: Optional[str] = None
    title: str = Field(max_length=MAX_TITLE_LEN)
    summary: Optional[str] = Field(default=None, max_length=MAX_TEXT_LEN)
    jurisdiction: str = Field(max_length=MAX_SHORT_LEN)
    status: str = Field(max_length=MAX_STATUS_LEN)
    current_step: str = Field(max_length=MAX_KEY_LEN)
    evidence: List[PiaEvidencePlaceholder]
    outcome: Optional[dict] = None
    step_data: dict
    created_by: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    company_id: Optional[str] = Field(default=None, max_length=MAX_ID_LEN)
    is_anonymized: bool
    anonymized_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PiaAuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_type: str = Field(max_length=MAX_STATUS_LEN)
    actor: Optional[str] = Field(default=None, max_length=MAX_SHORT_LEN)
    message: str = Field(max_length=MAX_TEXT_LEN)
    details: Optional[dict] = None
    created_at: datetime


class PiaCaseSummary(BaseModel):
    case: PiaCaseOut
    workflow: List[PiaWorkflowStep]
    audit_log: List[PiaAuditEventOut]
