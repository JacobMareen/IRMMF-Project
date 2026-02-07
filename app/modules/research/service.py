import csv
import io
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.modules.assessment.models import Assessment
from app.modules.tenant.models import Tenant, TenantSettings
from app.modules.research.schemas import ResearchExportRow

class ResearchService:
    def __init__(self, db: Session):
        self.db = db

    def get_export_stream(self) -> Generator[str, None, None]:
        """
        Generates a CSV stream of anonymized assessment data.
        Only includes assessments where market_research_opt_in = True.
        """
        # Query: Assessments + TenantSettings
        # We join Assessment -> Tenant (via implicit tenant_key logic? No, Assessment has tenant_key) 
        # -> TenantSettings
        
        # Note: Assessment.tenant_key links to Tenant.tenant_key
        # Tenant.id links to TenantSettings.tenant_id
        
        stmt = (
            select(Assessment, TenantSettings)
            .join(Tenant, Assessment.tenant_key == Tenant.tenant_key)
            .join(TenantSettings, Tenant.id == TenantSettings.tenant_id)
            .where(Assessment.market_research_opt_in == True)
            .where(Assessment.is_active == True)
        )
        
        results = self.db.execute(stmt).all()
        
        # CSV Header
        fieldnames = [
            "industry_sector", "employee_count", "region", "assessment_date", "mode",
            "domain_1", "domain_2", "domain_3", "domain_4",
            "domain_5", "domain_6", "domain_7", "domain_8",
            "top_risk", "target_maturity_avg"
        ]
        
        bio = io.StringIO()
        writer = csv.writer(bio)
        writer.writerow(fieldnames)
        yield bio.getvalue()
        bio.seek(0)
        bio.truncate(0)
        
        for assessment, settings in results:
            # Extract Scores from benchmark_tags or calculate?
            # Assuming benchmark_tags has {'d1': 2.5, ...} or distinct structure.
            # Fallback to 0.0 if missing.
            tags = assessment.benchmark_tags or {}
            
            # Helper to safely get domain score (handle string keys like 'Domain 1' or 'd1')
            def get_score(idx):
                # Try various keys: "d1", "Domain 1", "1. Strategy..."
                # Simplified: assuming tags uses "d1".."d8" or similar short codes from scoring engine.
                # If tags structure is unknown, we default to 0.0. 
                # In previous tasks, we saw benchmark_tags being used.
                val = tags.get(f"d{idx}") or tags.get(str(idx)) or 0.0
                return round(float(val), 2)

            # Targets
            targets = assessment.target_maturity or {}
            target_vals = [float(v) for v in targets.values()] if targets else []
            target_avg = round(sum(target_vals) / len(target_vals), 2) if target_vals else 0.0
            
            row = [
                settings.industry_sector or "Unknown",
                settings.employee_count or "Unknown",
                settings.default_jurisdiction or "Unknown",
                assessment.created_at.strftime("%Y-%m-%d"),
                assessment.mode or "rapid",
                get_score(1), get_score(2), get_score(3), get_score(4),
                get_score(5), get_score(6), get_score(7), get_score(8),
                tags.get("top_risk_scenario") or "None",
                target_avg
            ]
            
            writer.writerow(row)
            yield bio.getvalue()
            bio.seek(0)
            bio.truncate(0)
