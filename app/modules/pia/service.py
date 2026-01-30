from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.modules.pia import models
from app.modules.pia.content import PIA_OVERVIEW
from app.modules.pia.schemas import (
    PiaAuthorizationForm,
    PiaCaseAdvance,
    PiaCaseCreate,
    PiaCaseOut,
    PiaCaseSummary,
    PiaEvidenceCreate,
    PiaEvidencePlaceholder,
    PiaEvidencePlanForm,
    PiaInterviewForm,
    PiaLegitimacyForm,
    PiaOutcomeForm,
    PiaOverview,
    PiaWorkflowStep,
    PiaAuditEventOut,
)
from app.modules.tenant import models as tenant_models


PIA_WORKFLOW: List[PiaWorkflowStep] = [
    PiaWorkflowStep(
        key="legitimacy",
        title="Legitimacy & Proportionality",
        description="Establish legal basis, scope, and least-intrusive justification.",
    ),
    PiaWorkflowStep(
        key="authorization",
        title="Authorization & Assignment",
        description="Confirm mandate, investigator credentials, and conflicts of interest.",
    ),
    PiaWorkflowStep(
        key="evidence",
        title="Evidence Collection",
        description="Capture evidence metadata, chain-of-custody, and relevance tagging.",
    ),
    PiaWorkflowStep(
        key="interview",
        title="Adversarial Debate",
        description="Document interview rights, invitations, and response logs.",
    ),
    PiaWorkflowStep(
        key="outcome",
        title="Outcome & Erasure",
        description="Record decision, retention plan, and erasure schedule.",
    ),
]


class PiaService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview(self) -> PiaOverview:
        return PIA_OVERVIEW

    def get_workflow(self) -> List[PiaWorkflowStep]:
        return PIA_WORKFLOW

    def create_case(self, payload: PiaCaseCreate, tenant_key: str | None = None) -> PiaCaseOut:
        case_id = f"PIA-{uuid.uuid4().hex[:8].upper()}"
        jurisdiction = payload.jurisdiction or "Belgium"
        company_id = payload.company_id
        if not company_id:
            lookup_key = tenant_key or "default"
            tenant = (
                self.db.query(tenant_models.Tenant)
                .filter(tenant_models.Tenant.tenant_key == lookup_key)
                .first()
            )
            if tenant and tenant.settings and tenant.settings.company_name:
                company_id = tenant.settings.company_name
        if not company_id:
            company_id = "TBD-COMPANY"
        case = models.PiaCase(
            case_id=case_id,
            title=payload.title.strip(),
            summary=payload.summary,
            jurisdiction=jurisdiction,
            status="open",
            current_step=PIA_WORKFLOW[0].key,
            evidence={"items": []},
            outcome={},
            case_metadata={
                "steps": {},
                "reminders": ["Integration pending: link to assessment_id when assessment integration is enabled."],
            },
            created_by=payload.user_id,
            # Integration pending: derive company from auth/tenant context once auth is enabled.
            company_id=company_id,
            tenant_key=tenant_key or "default",
        )
        self.db.add(case)
        self.db.flush()

        first_step = models.PiaStepLog(
            case_id=case.case_id,
            step_key=PIA_WORKFLOW[0].key,
            status="in_progress",
        )
        self.db.add(first_step)
        self._log_event(
            case.case_id,
            event_type="case_created",
            message="Case created and workflow initialized.",
            details={
                "jurisdiction": jurisdiction,
                "created_by": payload.user_id,
                "company_id": payload.company_id,
                "tenant_key": tenant_key or "default",
            },
        )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def list_cases(self, tenant_key: str | None = None) -> List[PiaCaseOut]:
        query = self.db.query(models.PiaCase)
        if tenant_key:
            query = query.filter(models.PiaCase.tenant_key == tenant_key)
        cases = query.order_by(models.PiaCase.created_at.desc()).all()
        return [self._serialize_case(case) for case in cases]

    def get_case(self, case_id: str, tenant_key: str | None = None) -> PiaCaseOut:
        case = self._get_case_or_raise(case_id)
        if tenant_key and case.tenant_key != tenant_key:
            raise ValueError("Case not found")
        return self._serialize_case(case)

    def advance_case(self, case_id: str, payload: PiaCaseAdvance, tenant_key: str | None = None) -> PiaCaseOut:
        case = self._get_case_or_raise(case_id)
        if tenant_key and case.tenant_key != tenant_key:
            raise ValueError("Case not found")
        if case.is_anonymized:
            raise ValueError("Cannot advance an anonymized case.")
        current_index = self._workflow_index(case.current_step)

        current_step = PIA_WORKFLOW[current_index].key
        step_log = (
            self.db.query(models.PiaStepLog)
            .filter(models.PiaStepLog.case_id == case.case_id)
            .filter(models.PiaStepLog.step_key == current_step)
            .first()
        )
        if step_log:
            step_log.status = "completed"
            step_log.notes = payload.notes
            step_log.completed_by = payload.completed_by
            step_log.completed_at = datetime.now(timezone.utc)

        if current_index >= len(PIA_WORKFLOW) - 1:
            case.status = "closed"
            self._log_event(
                case.case_id,
                event_type="case_closed",
                actor=payload.completed_by,
                message="Case closed after final workflow step.",
            )
            self.db.commit()
            self.db.refresh(case)
            return self._serialize_case(case)

        next_step = PIA_WORKFLOW[current_index + 1].key
        existing_next = (
            self.db.query(models.PiaStepLog)
            .filter(models.PiaStepLog.case_id == case.case_id)
            .filter(models.PiaStepLog.step_key == next_step)
            .first()
        )
        if not existing_next:
            self.db.add(
                models.PiaStepLog(
                    case_id=case.case_id,
                    step_key=next_step,
                    status="in_progress",
                )
            )

        case.current_step = next_step
        self._log_event(
            case.case_id,
            event_type="step_advanced",
            actor=payload.completed_by,
            message=f"Advanced from {current_step} to {next_step}.",
            details={"from": current_step, "to": next_step, "notes": payload.notes},
        )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def add_evidence(self, case_id: str, payload: PiaEvidenceCreate, tenant_key: str | None = None) -> PiaCaseOut:
        case = self._get_case_or_raise(case_id)
        if tenant_key and case.tenant_key != tenant_key:
            raise ValueError("Case not found")
        if case.is_anonymized:
            raise ValueError("Cannot add evidence to an anonymized case.")
        evidence = case.evidence or {"items": []}
        items = evidence.get("items") or []
        placeholder = PiaEvidencePlaceholder(
            evidence_id=f"EV-{uuid.uuid4().hex[:6].upper()}",
            label=payload.label,
            source=payload.source,
            notes=payload.notes,
            status="placeholder",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        items.append(placeholder.model_dump())
        evidence["items"] = items
        case.evidence = evidence
        self._log_event(
            case.case_id,
            event_type="evidence_added",
            message="Evidence placeholder added.",
            details={"evidence_id": placeholder.evidence_id, "label": payload.label, "source": payload.source},
        )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def save_step(self, case_id: str, step_key: str, payload: dict, tenant_key: str | None = None) -> PiaCaseOut:
        case = self._get_case_or_raise(case_id)
        if tenant_key and case.tenant_key != tenant_key:
            raise ValueError("Case not found")
        if case.is_anonymized:
            raise ValueError("Cannot modify an anonymized case.")
        validated = self._validate_step(step_key, payload)
        case_metadata = case.case_metadata or {"steps": {}}
        steps = case_metadata.get("steps") or {}
        steps[step_key] = {
            "data": validated,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        case_metadata["steps"] = steps
        case.case_metadata = case_metadata
        self._log_event(
            case.case_id,
            event_type="step_saved",
            message=f"Saved form data for {step_key}.",
            details={"step_key": step_key},
        )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def get_audit_log(self, case_id: str, tenant_key: str | None = None) -> List[PiaAuditEventOut]:
        case = self._get_case_or_raise(case_id)
        if tenant_key and case.tenant_key != tenant_key:
            raise ValueError("Case not found")
        events = (
            self.db.query(models.PiaAuditEvent)
            .filter(models.PiaAuditEvent.case_id == case_id)
            .order_by(models.PiaAuditEvent.created_at.desc())
            .all()
        )
        return [PiaAuditEventOut.model_validate(event) for event in events]

    def get_summary(self, case_id: str, tenant_key: str | None = None) -> PiaCaseSummary:
        case = self._get_case_or_raise(case_id)
        if tenant_key and case.tenant_key != tenant_key:
            raise ValueError("Case not found")
        return PiaCaseSummary(
            case=self._serialize_case(case),
            workflow=PIA_WORKFLOW,
            audit_log=self.get_audit_log(case_id, tenant_key=tenant_key),
        )

    def anonymize_case(
        self,
        case_id: str,
        actor: str | None = None,
        reason: str | None = None,
        tenant_key: str | None = None,
    ) -> PiaCaseOut:
        case = self._get_case_or_raise(case_id)
        if tenant_key and case.tenant_key != tenant_key:
            raise ValueError("Case not found")
        case.title = "Anonymized case"
        case.summary = None
        case.evidence = {"items": []}
        case.outcome = {}
        case.created_by = None
        case.company_id = None
        case_metadata = case.case_metadata or {}
        case_metadata["steps"] = {}
        case.case_metadata = case_metadata
        case.is_anonymized = True
        case.anonymized_at = datetime.now(timezone.utc)

        self.db.query(models.PiaStepLog).filter(models.PiaStepLog.case_id == case_id).update(
            {"notes": None, "completed_by": None},
            synchronize_session=False,
        )
        self.db.query(models.PiaAuditEvent).filter(models.PiaAuditEvent.case_id == case_id).update(
            {"message": "Event redacted due to anonymization.", "details": {}, "actor": None},
            synchronize_session=False,
        )
        self._log_event(
            case.case_id,
            event_type="case_anonymized",
            actor=actor,
            message="Case data anonymized.",
            details={"reason": reason},
        )
        self.db.commit()
        self.db.refresh(case)
        return self._serialize_case(case)

    def _get_case_or_raise(self, case_id: str) -> models.PiaCase:
        case = (
            self.db.query(models.PiaCase)
            .filter(models.PiaCase.case_id == case_id)
            .first()
        )
        if not case:
            raise ValueError("Case not found")
        return case

    def _workflow_index(self, step_key: str) -> int:
        for idx, step in enumerate(PIA_WORKFLOW):
            if step.key == step_key:
                return idx
        return 0

    def _serialize_case(self, case: models.PiaCase) -> PiaCaseOut:
        evidence_items = (case.evidence or {}).get("items") or []
        case_metadata = case.case_metadata or {}
        step_data = case_metadata.get("steps") or {}
        return PiaCaseOut(
            case_id=case.case_id,
            case_uuid=str(case.case_uuid),
            tenant_key=case.tenant_key,
            title=case.title,
            summary=case.summary,
            jurisdiction=case.jurisdiction,
            status=case.status,
            current_step=case.current_step,
            evidence=[PiaEvidencePlaceholder(**item) for item in evidence_items],
            outcome=case.outcome or {},
            step_data=step_data,
            created_by=case.created_by,
            company_id=case.company_id,
            is_anonymized=case.is_anonymized,
            anonymized_at=case.anonymized_at,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )

    def _validate_step(self, step_key: str, payload: dict) -> dict:
        validators = {
            "legitimacy": PiaLegitimacyForm,
            "authorization": PiaAuthorizationForm,
            "evidence": PiaEvidencePlanForm,
            "interview": PiaInterviewForm,
            "outcome": PiaOutcomeForm,
        }
        if step_key not in validators:
            raise ValueError("Unknown workflow step.")
        return validators[step_key](**payload).model_dump()

    def _log_event(
        self,
        case_id: str,
        event_type: str,
        message: str,
        actor: str | None = None,
        details: dict | None = None,
    ) -> None:
        event = models.PiaAuditEvent(
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            message=message,
            details=details or {},
        )
        self.db.add(event)
