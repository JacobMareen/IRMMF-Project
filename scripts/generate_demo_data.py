
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta
import random

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from app.db import SessionLocal, engine
from app.modules.tenant import models as tenant_models
from app.modules.users import models as auth_models
from app.modules.assessment import models as assess_models
from app.modules.cases import models as case_models
from app.modules.assessment.service import AssessmentService

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_demo_data():
    db = SessionLocal()
    print("Starting demo data generation...")

    try:
        # 1. Create Tenant
        tenant_key = "demo_corp"
        tenant = db.query(tenant_models.Tenant).filter_by(tenant_key=tenant_key).first()
        if not tenant:
            tenant = tenant_models.Tenant(
                tenant_key=tenant_key,
                tenant_name="Demo Corp (Medium Maturity)",
                environment_type="Production"
            )
            db.add(tenant)
            db.commit()
            print(f"Created tenant: {tenant.tenant_name}")
        else:
            print(f"Tenant exists: {tenant.tenant_name}")

        # 2. Create User
        email = "demo@democorp.com"
        user = db.query(auth_models.User).filter_by(email=email).first()
        if not user:
            user = auth_models.User(
                email=email,
                display_name="Demo User",
                tenant_id=tenant.id,
                status="active"
            )
            db.add(user)
            db.commit()
            print(f"Created user: {user.email}")
        else:
            print(f"User exists: {user.email}")

        # 3. Create Assessment
        assessment_id = f"demo-assess-{uuid.uuid4().hex[:8]}"
        assessment = assess_models.Assessment(
            assessment_id=assessment_id,
            tenant_key=tenant_key,
            user_id=user.email,
            mode="standard",
            depth="comprehensive",
            target_maturity={"overall": 3.0}, # Target level 3
            is_active=True
        )
        db.add(assessment)
        db.commit()
        print(f"Created assessment: {assessment_id}")

        # 4. Populate Answers (Medium Maturity ~ Level 2.5-3.0)
        # Fetch all questions
        questions = db.query(assess_models.Question).all()
        print(f"Found {len(questions)} questions. Answering...")
        
        for q in questions:
            # Randomly decide maturity: 
            # 20% Low (0.0), 50% Medium (0.5), 30% High (1.0)
            roll = random.random()
            if roll < 0.2:
                points = 0.0 # No
                ans_text = "No, we do not have this."
            elif roll < 0.7:
                points = 0.5 # Partial
                ans_text = "Partially implemented in some departments."
            else:
                points = 1.0 # Yes
                ans_text = "Yes, fully implemented and documented."

            # Find matching answer option if possible, or just create a raw response
            # Since we are populating fact_responses, we link to a generic logic
            
            # Find an answer choice that approximates the points?
            # Or just inject scores. The UI displays Answers.
            
            options = q.options
            selected_option = None
            if options:
                # Try to find option with closest points
                # Simplify: just look for 'Yes', 'No', 'Partial' in text or simply pick one
                # Logic: Sort by points
                sorted_opts = sorted(options, key=lambda o: (o.pts_g or 0))
                if points == 0.0:
                    selected_option = sorted_opts[0]
                elif points == 1.0:
                    selected_option = sorted_opts[-1]
                else:
                    # Pick middle
                    mid = len(sorted_opts) // 2
                    selected_option = sorted_opts[mid]
                
                score = selected_option.pts_g or 0.0
            else:
                # Fallback if no options (shouldn't happen for Single choice)
                continue

            response = assess_models.Response(
                assessment_id=assessment_id,
                q_id=q.q_id,
                a_id=selected_option.a_id,
                score_achieved=score,
                origin="demo_script"
            )
            db.add(response)
        
        db.commit()
        print("Assessment answers populated.")

        # 4.5 Populate Intake (Required for Flow unlock)
        print("Populating Intake (T0)...")
        t0_questions = db.query(assess_models.Question).filter(assess_models.Question.tier == 'T0').all()
        
        # Define default answers for key intake questions to drive logic
        intake_defaults = {
            "IndustryCode": "Technology",
            "Region": "Global",
            "EmployeeBand": "100-500",
            "RevenueBand": "10M-50M",
            "DataSensitivity": "High",
            "Regulated": "Yes"
        }

        for q in t0_questions:
            # Map question list_ref to default or generic
            val = intake_defaults.get(q.list_ref, "Standard")
            
            # Create IntakeResponse
            intake_resp = assess_models.IntakeResponse(
                assessment_id=assessment_id,
                q_id=q.q_id,
                value=val
            )
            db.add(intake_resp)

        # Update Assessment Benchmark Tags (Intake Side Effects)
        assessment.benchmark_tags = {
            "industry": "Technology",
            "region": "Global",
            "size_band": "100-500",
            "regulated_flags": ["Yes"]
        }
        db.add(assessment)
        db.commit()
        print("Intake populated.")

        # 5. Create Case (Triage -> Case)
        case_title = "Suspicious Data Exfiltration Attempt"
        case = case_models.Case(
            case_id=f"CASE-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:4]}",
            tenant_key=tenant_key,
            created_by=email,
            title=case_title,
            summary="DLP alert triggered for large file upload to personal cloud storage by employee J. Doe.",
            jurisdiction="US",
            status="OPEN",
            stage="INVESTIGATION",
            case_metadata={"risk_score": "High", "source": "DLP"},
            date_incident_occurred=datetime.now(timezone.utc) - timedelta(days=2),
            date_investigation_started=datetime.now(timezone.utc) - timedelta(hours=4)
        )
        db.add(case)
        db.commit()

        # Add Subjects
        subject = case_models.CaseSubject(
            case_id=case.case_id,
            subject_type="employee",
            display_name="John Doe",
            reference="EMP-12345",
            manager_name="Jane Smith"
        )
        db.add(subject)

        # Add Evidence
        evidence = case_models.CaseEvidenceItem(
            case_id=case.case_id,
            evidence_id=f"EV-{uuid.uuid4().hex[:6]}",
            label="DLP Log Export",
            source="Symantec DLP",
            status="collected",
            notes="Log showing 4GB upload to Dropbox."
        )
        db.add(evidence)
        db.commit()
        print(f"Created case: {case.case_id}")

        # 6. Create Triage Ticket (demonstrate Inbox)
        triage = case_models.CaseTriageTicket(
            ticket_id=f"TKT-{uuid.uuid4().hex[:6]}",
            tenant_key=tenant_key,
            subject="Potential Policy Violation",
            message="I witnessed a colleague accessing restricted data without authorization.",
            reporter_email="anonymous@reporter.com",
            source="dropbox",
            status="new"
        )
        db.add(triage)
        db.commit()
        print(f"Created triage ticket: {triage.ticket_id}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_data()
