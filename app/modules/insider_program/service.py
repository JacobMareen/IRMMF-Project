from __future__ import annotations

from datetime import date
import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.modules.insider_program.schemas import (
    InsiderRiskPolicyIn,
    InsiderRiskControlIn,
    InsiderRiskControlUpdate,
    PolicySection,
    InsiderRiskRoadmapIn,
    InsiderRiskRoadmapUpdate,
)


DEFAULT_POLICY = InsiderRiskPolicyIn(
    status="Draft",
    version="v1.0",
    owner="IR Program Lead",
    approval="Pending GC + HR approval",
    scope="Employees, contractors, and trusted third parties with access to sensitive data, systems, or facilities.",
    last_reviewed=date(2026, 2, 3),
    next_review=date(2026, 5, 3),
    principles=[
        "Lawful, fair, and transparent handling of insider risk signals.",
        "Least intrusive monitoring with strict access controls and audit trails.",
        "Clear escalation paths with legal, HR, and privacy oversight.",
        "Documented decision-making and proportional response.",
        "Consistent triage decisions based on an approved business-impact rubric.",
    ],
    sections=[
        PolicySection(
            title="Governance & Accountability",
            intent="Define program ownership, decision rights, and reporting cadence.",
            bullets=[
                "IR Steering Group chaired by Legal/HR with Security and Privacy representation.",
                "Case approvals required for elevated monitoring or investigative steps.",
                "Quarterly program review with KPI reporting to leadership.",
            ],
            owner="Legal + HR",
            artifacts=["RACI matrix", "Approval workflow", "Quarterly KPI pack"],
        ),
        PolicySection(
            title="Detection & Monitoring",
            intent="Establish what is monitored, how signals are reviewed, and how privacy is protected.",
            bullets=[
                "Signals limited to approved telemetry and contextualized with business need.",
                "Alert triage within 5 business days with documented rationale.",
                "Sensitive access requires justification and audit log retention.",
            ],
            owner="Security Operations",
            artifacts=["Monitoring charter", "Signal catalog", "Triage checklist"],
        ),
        PolicySection(
            title="Intake & Triage",
            intent="Capture early context and apply a consistent, business-friendly triage rubric.",
            bullets=[
                "Intake records trigger source, data sensitivity, jurisdiction, stakeholders, and initial evidence quality.",
                "Triage rubric uses Impact (Minimal–Severe), Likelihood (Unlikely–Confirmed), and Confidence (Low/Medium/High) with clear examples.",
                "Outcome choices are documented as No further action, HR/ER review, or Open investigation.",
                "SLA targets scale by environment size (e.g., Small: 5 business days, Mid: 3 days, Large: 24–48 hours).",
            ],
            owner="Investigations Lead",
            artifacts=["Intake checklist", "Triage rubric", "Triage SLA matrix", "Stakeholder notification map"],
        ),
        PolicySection(
            title="Investigation & Response",
            intent="Standardize case intake, evidence handling, and response actions.",
            bullets=[
                "Intake requires scope, jurisdiction, and legal basis.",
                "Evidence register maintained with chain-of-custody tracking.",
                "Escalations follow predefined decision gates and HR/legal review.",
            ],
            owner="Investigations Lead",
            artifacts=["Case workflow", "Evidence register", "Decision log"],
        ),
        PolicySection(
            title="Privacy, Ethics, and Data Retention",
            intent="Protect employee rights and ensure proportionality and retention controls.",
            bullets=[
                "Data minimization applied to all case artifacts and exports.",
                "Retention periods enforced with erasure workflows and approvals.",
                "Ethics review required for high-impact monitoring changes.",
            ],
            owner="Privacy Office",
            artifacts=["Retention schedule", "Erasure certificate", "Ethics checklist"],
        ),
    ],
)


def _normalize_list(value: Iterable[str] | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value if item and item.strip()]


class InsiderRiskProgramService:
    def __init__(self, db: Session):
        self.db = db

    def get_policy(self, tenant_key: str) -> models.InsiderRiskPolicy | None:
        stmt = select(models.InsiderRiskPolicy).where(models.InsiderRiskPolicy.tenant_key == tenant_key)
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert_policy(self, tenant_key: str, payload: InsiderRiskPolicyIn) -> models.InsiderRiskPolicy:
        policy = self.get_policy(tenant_key)
        if policy is None:
            policy = models.InsiderRiskPolicy(tenant_key=tenant_key)
            self.db.add(policy)
        policy.status = payload.status
        policy.version = payload.version
        policy.owner = payload.owner
        policy.approval = payload.approval
        policy.scope = payload.scope
        policy.last_reviewed = payload.last_reviewed
        policy.next_review = payload.next_review
        policy.principles = _normalize_list(payload.principles)
        policy.sections = [section.model_dump() for section in payload.sections]
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def list_controls(self, tenant_key: str) -> list[models.InsiderRiskControl]:
        stmt = (
            select(models.InsiderRiskControl)
            .where(models.InsiderRiskControl.tenant_key == tenant_key)
            .order_by(models.InsiderRiskControl.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_control(self, tenant_key: str, payload: InsiderRiskControlIn) -> models.InsiderRiskControl:
        existing = self.get_control(tenant_key, payload.control_id)
        if existing is not None:
            raise ValueError("Control ID already exists.")
        control = models.InsiderRiskControl(
            tenant_key=tenant_key,
            control_id=payload.control_id,
            title=payload.title,
            domain=payload.domain,
            objective=payload.objective,
            status=payload.status,
            owner=payload.owner,
            frequency=payload.frequency,
            evidence=payload.evidence,
            last_reviewed=payload.last_reviewed,
            next_review=payload.next_review,
            linked_actions=_normalize_list(payload.linked_actions),
            linked_rec_ids=_normalize_list(payload.linked_rec_ids),
            linked_categories=_normalize_list(payload.linked_categories),
        )
        self.db.add(control)
        self.db.commit()
        self.db.refresh(control)
        return control

    def update_control(
        self,
        tenant_key: str,
        control_id: str,
        payload: InsiderRiskControlUpdate,
    ) -> models.InsiderRiskControl:
        control = self.get_control(tenant_key, control_id)
        if control is None:
            raise ValueError("Control not found.")
        if payload.title is not None:
            control.title = payload.title
        if payload.domain is not None:
            control.domain = payload.domain
        if payload.objective is not None:
            control.objective = payload.objective
        if payload.status is not None:
            control.status = payload.status
        if payload.owner is not None:
            control.owner = payload.owner
        if payload.frequency is not None:
            control.frequency = payload.frequency
        if payload.evidence is not None:
            control.evidence = payload.evidence
        if payload.last_reviewed is not None:
            control.last_reviewed = payload.last_reviewed
        if payload.next_review is not None:
            control.next_review = payload.next_review
        if payload.linked_actions is not None:
            control.linked_actions = _normalize_list(payload.linked_actions)
        if payload.linked_rec_ids is not None:
            control.linked_rec_ids = _normalize_list(payload.linked_rec_ids)
        if payload.linked_categories is not None:
            control.linked_categories = _normalize_list(payload.linked_categories)
        self.db.commit()
        self.db.refresh(control)
        return control

    def get_control(self, tenant_key: str, control_id: str) -> models.InsiderRiskControl | None:
        stmt = select(models.InsiderRiskControl).where(
            models.InsiderRiskControl.tenant_key == tenant_key,
            models.InsiderRiskControl.control_id == control_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_roadmap(self, tenant_key: str) -> list[models.InsiderRiskRoadmapItem]:
        stmt = (
            select(models.InsiderRiskRoadmapItem)
            .where(models.InsiderRiskRoadmapItem.tenant_key == tenant_key)
            .order_by(models.InsiderRiskRoadmapItem.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_roadmap_item(
        self,
        tenant_key: str,
        payload: InsiderRiskRoadmapIn,
    ) -> models.InsiderRiskRoadmapItem:
        item = models.InsiderRiskRoadmapItem(
            tenant_key=tenant_key,
            phase=payload.phase,
            title=payload.title,
            description=payload.description,
            owner=payload.owner,
            target_window=payload.target_window,
            status=payload.status,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_roadmap_item(
        self,
        tenant_key: str,
        item_id: str,
        payload: InsiderRiskRoadmapUpdate,
    ) -> models.InsiderRiskRoadmapItem:
        item = self.get_roadmap_item(tenant_key, item_id)
        if item is None:
            raise ValueError("Roadmap item not found.")
        if payload.phase is not None:
            item.phase = payload.phase
        if payload.title is not None:
            item.title = payload.title
        if payload.description is not None:
            item.description = payload.description
        if payload.owner is not None:
            item.owner = payload.owner
        if payload.target_window is not None:
            item.target_window = payload.target_window
        if payload.status is not None:
            item.status = payload.status
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_roadmap_item(self, tenant_key: str, item_id: str) -> None:
        item = self.get_roadmap_item(tenant_key, item_id)
        if item is None:
            raise ValueError("Roadmap item not found.")
        self.db.delete(item)
        self.db.commit()

    def get_roadmap_item(self, tenant_key: str, item_id: str) -> models.InsiderRiskRoadmapItem | None:
        try:
            parsed_id = uuid.UUID(item_id)
        except ValueError:
            return None
        stmt = select(models.InsiderRiskRoadmapItem).where(
            models.InsiderRiskRoadmapItem.tenant_key == tenant_key,
            models.InsiderRiskRoadmapItem.id == parsed_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()
