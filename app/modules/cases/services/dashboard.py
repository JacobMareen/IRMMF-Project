from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from sqlalchemy import or_, func

from auth import Principal
from app.modules.cases import models
from app.modules.cases.schemas import (
    CaseConsistencyOut,
    CaseNotificationOut,
    CaseOutcomeStat,
)
from app.modules.cases.services.base import CaseServiceBase

class CaseDashboardMixin(CaseServiceBase):
    def get_dashboard_stats(self, principal: Principal) -> Dict[str, Any]:
        tenant_key = principal.tenant_key or "default"
        
        # Base query for tenant
        base_query = self.db.query(models.Case).filter(models.Case.tenant_key == tenant_key)
        
        total_cases = base_query.count()
        open_cases = base_query.filter(models.Case.status != "CLOSED").count()
        closed_cases = base_query.filter(models.Case.status == "CLOSED").count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        new_cases_30d = base_query.filter(models.Case.created_at >= thirty_days_ago).count()
        
        # Tasks
        my_tasks = (
            self.db.query(models.CaseTask)
            .join(models.Case)
            .filter(models.Case.tenant_key == tenant_key)
            .filter(models.CaseTask.assignee == principal.subject)
            .filter(models.CaseTask.status == "open")
            .count()
        )
        
        overdue_tasks = (
            self.db.query(models.CaseTask)
            .join(models.Case)
            .filter(models.Case.tenant_key == tenant_key)
            .filter(models.CaseTask.status == "open")
            .filter(models.CaseTask.due_at < datetime.now(timezone.utc))
            .count()
        )

        # Serious Cause Alerts
        serious_cause_alerts = 0
        if self._serious_cause_notifications_enabled(tenant_key):
             serious_cause_alerts = (
                self.db.query(models.CaseSeriousCause)
                .join(models.Case)
                .filter(models.Case.tenant_key == tenant_key)
                .filter(models.CaseSeriousCause.dismissal_due_at < datetime.now(timezone.utc) + timedelta(hours=48))
                .filter(models.CaseSeriousCause.dismissal_recorded_at.is_(None))
                .count()
            )

        return {
            "total_cases": total_cases,
            "open_cases": open_cases,
            "closed_cases": closed_cases,
            "new_cases_30d": new_cases_30d,
            "my_tasks": my_tasks,
            "overdue_tasks": overdue_tasks,
            "serious_cause_alerts": serious_cause_alerts,
        }

    def get_consistency_insights(
        self,
        case_id: str,
        principal: Principal,
    ) -> CaseConsistencyOut:
        case = self._get_case_or_raise(case_id, principal=principal)
        # Placeholder logic for consistency insights
        # In a real system, this would analyze similar cases and their outcomes
        
        similar_cases_count = 0
        most_common_outcome = "None"
        confidence_score = 0.0
        
        return CaseConsistencyOut(
             similar_cases_count=similar_cases_count,
             most_common_outcome=most_common_outcome,
             confidence_score=confidence_score,
             insights=["Insufficient data for consistency analysis."]
        )

    def list_notifications(
        self,
        tenant_key: str,
        case_id: str | None = None,
    ) -> List[CaseNotificationOut]:
        query = self.db.query(models.CaseNotification).filter(models.CaseNotification.tenant_key == tenant_key)
        if case_id:
            query = query.filter(models.CaseNotification.case_id == case_id)
        notifications = query.order_by(models.CaseNotification.created_at.desc()).all()
        now = datetime.now(timezone.utc)
        updated = False
        for item in notifications:
            if item.status == "pending" and item.due_at and item.due_at <= now:
                item.status = "sent"
                item.sent_at = now
                updated = True
                self._log_audit_event(
                    case_id=item.case_id,
                    event_type="notification_sent",
                    actor="system",
                    message="Notification sent.",
                    details={"notification_type": item.notification_type, "severity": item.severity},
                )
        if updated:
            self.db.commit()
        return [CaseNotificationOut.model_validate(item) for item in notifications]

    def acknowledge_notification(
        self,
        notification_id: int,
        principal: Principal,
    ) -> CaseNotificationOut:
        notification = (
            self.db.query(models.CaseNotification)
            .filter(models.CaseNotification.id == notification_id)
            .first()
        )
        if not notification:
            raise ValueError("Notification not found.")
        if notification.tenant_key != (principal.tenant_key or "default"):
            raise ValueError("Notification not found.")
        notification.status = "acknowledged"
        notification.acknowledged_at = datetime.now(timezone.utc)
        notification.acknowledged_by = principal.subject
        self._log_audit_event(
            case_id=notification.case_id,
            event_type="notification_acknowledged",
            actor=principal.subject,
            message="Notification acknowledged.",
            details={"notification_type": notification.notification_type, "severity": notification.severity},
        )
        self.db.commit()
        self.db.refresh(notification)
        return CaseNotificationOut.model_validate(notification)
