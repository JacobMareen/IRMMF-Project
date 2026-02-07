from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import List

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CaseTaskCreate,
    CaseTaskOut,
    CaseTaskUpdate,
)
from app.modules.cases.services.base import CaseServiceBase

class CaseTaskMixin(CaseServiceBase):
    def add_task(self, case_id: str, payload: CaseTaskCreate, principal: Principal) -> CaseTaskOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        task = models.CaseTask(
            case_id=case.case_id,
            task_id=f"TASK-{uuid.uuid4().hex[:6].upper()}",
            title=payload.title,
            description=payload.description,
            task_type=payload.task_type,
            status=payload.status or "open",
            due_at=payload.due_at,
            assignee=payload.assignee,
        )
        self.db.add(task)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="task_added",
            actor=principal.subject,
            message="Task added.",
            details={"task_id": task.task_id, "title": payload.title},
        )
        self.db.commit()
        self.db.refresh(task)
        return CaseTaskOut.model_validate(task)

    def update_task(
        self,
        case_id: str,
        task_id: str,
        payload: CaseTaskUpdate,
        principal: Principal,
    ) -> CaseTaskOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        self._ensure_not_anonymized(case)
        task = (
            self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .filter(models.CaseTask.task_id == task_id)
            .first()
        )
        if not task:
            raise ValueError("Task not found.")
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return CaseTaskOut.model_validate(task)
        change_log: dict[str, dict[str, str | None]] = {}
        if "status" in updates and updates["status"] is not None:
            status_value = updates["status"]
            if status_value != task.status:
                change_log["status"] = {"from": task.status, "to": status_value}
                task.status = status_value
        if "assignee" in updates:
            assignee_value = (updates.get("assignee") or "").strip() or None
            if assignee_value != task.assignee:
                change_log["assignee"] = {"from": task.assignee, "to": assignee_value}
                task.assignee = assignee_value
        if "due_at" in updates:
            due_value = updates.get("due_at")
            if due_value != task.due_at:
                change_log["due_at"] = {
                    "from": task.due_at.isoformat() if task.due_at else None,
                    "to": due_value.isoformat() if due_value else None,
                }
                task.due_at = due_value
        if change_log:
            self._log_audit_event(
                case_id=case.case_id,
                event_type="task_updated",
                actor=principal.subject,
                message="Task updated.",
                details={"task_id": task.task_id, "changes": change_log},
            )
        self.db.commit()
        self.db.refresh(task)
        return CaseTaskOut.model_validate(task)

    def list_tasks(self, case_id: str, principal: Principal) -> List[CaseTaskOut]:
        case = self._get_case_or_raise(case_id, principal=principal)
        tasks = (
            self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .order_by(models.CaseTask.created_at.desc())
            .all()
        )
        return [CaseTaskOut.model_validate(task) for task in tasks]

    def _schedule_retaliation_task(self, case: models.Case, principal: Principal) -> None:
        existing = (
            self.db.query(models.CaseTask)
            .filter(models.CaseTask.case_id == case.case_id)
            .filter(models.CaseTask.task_type == "retaliation_check")
            .first()
        )
        if existing:
            return
        due_at = datetime.now(timezone.utc) + timedelta(days=90)
        task = models.CaseTask(
            case_id=case.case_id,
            task_id=f"TASK-{uuid.uuid4().hex[:6].upper()}",
            title="Retaliation check-in (3 months)",
            description="Automated follow-up after case closure.",
            task_type="retaliation_check",
            status="open",
            due_at=due_at,
        )
        self.db.add(task)
        self._log_audit_event(
            case_id=case.case_id,
            event_type="retaliation_task_scheduled",
            actor=principal.subject,
            message="Retaliation monitoring task scheduled.",
            details={"task_id": task.task_id, "due_at": due_at.isoformat()},
        )
