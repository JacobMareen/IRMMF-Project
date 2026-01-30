from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PiaKeyDate(BaseModel):
    date: str
    requirement: str


class PiaBullet(BaseModel):
    title: str
    detail: str
    tags: Optional[List[str]] = None


class PiaSection(BaseModel):
    key: str
    title: str
    summary: str
    bullets: List[PiaBullet]


class PiaRoadmapPhase(BaseModel):
    phase: str
    focus: str
    deliverables: List[str]


class PiaOverview(BaseModel):
    module_key: str
    title: str
    subtitle: str
    executive_summary: str
    key_dates: List[PiaKeyDate]
    sections: List[PiaSection]
    roadmap: List[PiaRoadmapPhase]


class PiaWorkflowStep(BaseModel):
    key: str
    title: str
    description: str


class PiaEvidencePlaceholder(BaseModel):
    evidence_id: str
    label: str
    source: str
    notes: Optional[str] = None
    status: str
    created_at: str


class PiaCaseCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    jurisdiction: Optional[str] = None
    user_id: Optional[str] = None
    company_id: Optional[str] = None


class PiaCaseAdvance(BaseModel):
    notes: Optional[str] = None
    completed_by: Optional[str] = None


class PiaEvidenceCreate(BaseModel):
    label: str
    source: str
    notes: Optional[str] = None


class PiaAnonymizeRequest(BaseModel):
    actor: Optional[str] = None
    reason: Optional[str] = None


class PiaLegitimacyForm(BaseModel):
    legal_basis: str
    trigger_summary: str
    proportionality_confirmed: bool
    less_intrusive_steps: Optional[str] = None
    mandate_owner: Optional[str] = None
    mandate_date: Optional[str] = None


class PiaAuthorizationForm(BaseModel):
    investigator_name: str
    investigator_role: str
    licensed: bool
    license_id: Optional[str] = None
    conflict_check_passed: bool
    authorizer: Optional[str] = None
    authorization_date: Optional[str] = None


class PiaEvidencePlanForm(BaseModel):
    collection_scope: str
    chain_of_custody_owner: Optional[str] = None
    relevance_tagging_method: Optional[str] = None
    minimization_notes: Optional[str] = None


class PiaInterviewForm(BaseModel):
    invitation_sent: bool
    invitation_date: Optional[str] = None
    rights_acknowledged: bool
    representative_present: Optional[str] = None
    interview_summary: Optional[str] = None


class PiaOutcomeForm(BaseModel):
    decision: str
    sanction: Optional[str] = None
    erasure_deadline: Optional[str] = None
    retention_rationale: Optional[str] = None
    outcome_notes: Optional[str] = None


class PiaCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    case_id: str
    case_uuid: str
    tenant_key: Optional[str] = None
    title: str
    summary: Optional[str] = None
    jurisdiction: str
    status: str
    current_step: str
    evidence: List[PiaEvidencePlaceholder]
    outcome: Optional[dict] = None
    step_data: dict
    created_by: Optional[str] = None
    company_id: Optional[str] = None
    is_anonymized: bool
    anonymized_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PiaAuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_type: str
    actor: Optional[str] = None
    message: str
    details: Optional[dict] = None
    created_at: datetime


class PiaCaseSummary(BaseModel):
    case: PiaCaseOut
    workflow: List[PiaWorkflowStep]
    audit_log: List[PiaAuditEventOut]
