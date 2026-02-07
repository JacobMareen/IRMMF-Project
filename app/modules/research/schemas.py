from pydantic import BaseModel
from typing import Optional, Dict

class ResearchExportRow(BaseModel):
    """
    Represents a single row in the anonymized research export.
    Strictly excludes PII (Name, Email, UserID).
    """
    # Organization Demographics
    industry_sector: Optional[str] = "Unknown"
    employee_count: Optional[str] = "Unknown"
    region: str = "Unknown"  # from Default Jurisdiction
    
    # Assessment Metadata
    assessment_date: str
    mode: str  # "rapid" or "full"
    
    # Scores (0.0 - 4.0)
    domain_1_score: float = 0.0
    domain_2_score: float = 0.0
    domain_3_score: float = 0.0
    domain_4_score: float = 0.0
    domain_5_score: float = 0.0
    domain_6_score: float = 0.0
    domain_7_score: float = 0.0
    domain_8_score: float = 0.0
    
    # Top Risk
    top_risk_scenario: Optional[str] = None
    
    # Targets (Gap Analysis)
    target_maturity_avg: float = 0.0
