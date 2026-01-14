"""Assessment module façade that composes state, intake, and analysis services."""
from sqlalchemy.orm import Session

from app.core.repositories import QuestionRepository, ResponseRepository
from app.core.engines import V6_1BranchingEngine, V6_1ScoringEngine
from app.modules.assessment.analysis import AssessmentAnalysisService
from app.modules.assessment.intake import AssessmentIntakeService
from app.modules.assessment.state import AssessmentStateService


class AssessmentService(AssessmentStateService, AssessmentIntakeService, AssessmentAnalysisService):
    def __init__(self, db: Session):
        self.db = db
        self.q_repo = QuestionRepository(db)
        self.r_repo = ResponseRepository(db)
        self.branch_engine = V6_1BranchingEngine()
        self.scoring_engine = V6_1ScoringEngine()
