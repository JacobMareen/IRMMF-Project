from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.cases.services.base import (
    CaseServiceBase,
    STAGE_FLOW,
    STAGE_GATES,
    GATE_VALIDATORS,
)
from app.modules.cases.services.core import CaseCoreMixin
from app.modules.cases.services.evidence import CaseEvidenceMixin
from app.modules.cases.services.tasks import CaseTaskMixin
from app.modules.cases.services.documents import CaseDocumentMixin
from app.modules.cases.services.legal import CaseLegalMixin
from app.modules.cases.services.playbooks import CasePlaybookMixin
from app.modules.cases.services.triage import CaseTriageMixin
from app.modules.cases.services.serious_cause import CaseSeriousCauseMixin
from app.modules.cases.services.dashboard import CaseDashboardMixin
from app.modules.cases.services.gates import CaseGateMixin
from app.modules.cases.services.notes import CaseNoteMixin

class CaseService(
    CaseCoreMixin,
    CaseEvidenceMixin,
    CaseTaskMixin,
    CaseDocumentMixin,
    CaseLegalMixin,
    CasePlaybookMixin,
    CaseTriageMixin,
    CaseSeriousCauseMixin,
    CaseDashboardMixin,
    CaseGateMixin,
    CaseNoteMixin,
    CaseServiceBase,
):
    """
    Main CaseService class.
    Refactored to use Mixin pattern for better maintainability.
    Inherits functionality from specialized mixins:
    - Core: CRUD, state transitions, breaking glass.
    - Evidence: Items, suggestions, links.
    - Notes: Notes, flags.
    - Tasks: Task management.
    - Gates: Gate validation and saving.
    - Documents: Generation, download, export.
    - Legal: Holds, Expert Access, Erasure.
    - Triage: Tickets, Reporter Messaging.
    - Playbooks: Applying investigation playbooks.
    - Serious Cause: HR/ER specific dismissal workflows.
    - Dashboard: Analytics and notifications.
    """
    def __init__(self, db: Session):
        super().__init__(db)
