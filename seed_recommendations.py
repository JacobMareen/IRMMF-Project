"""Seed the recommendation library with initial recommendations."""
import sys
from app.db import SessionLocal
from app.core.bootstrap import init_database
from app import models


def seed_recommendations():
    """Populate dim_recommendations with starter recommendations."""
    print("Initializing database...")
    init_database()
    db = SessionLocal()

    recommendations = [
        {
            "rec_id": "REC_G_001",
            "category": "Governance",
            "subcategory": "Policy & Oversight",
            "title": "Establish Insider Risk Management Steering Committee",
            "description": "Form a cross-functional steering committee with representatives from Security, Legal, HR, and IT to oversee insider risk program.",
            "rationale": "Without executive sponsorship and cross-functional collaboration, insider risk controls remain siloed and ineffective.",
            "implementation_steps": {
                "steps": [
                    {"step": 1, "action": "Identify executive sponsor (CISO or CRO)", "owner": "Security Leadership"},
                    {"step": 2, "action": "Draft steering committee charter with clear responsibilities", "owner": "Security Lead"},
                    {"step": 3, "action": "Recruit members from HR, Legal, IT, Compliance", "owner": "Executive Sponsor"},
                    {"step": 4, "action": "Schedule quarterly meetings and establish reporting cadence", "owner": "Committee Chair"}
                ]
            },
            "success_criteria": {
                "metrics": [
                    {"metric": "Committee meets quarterly", "target": "100%"},
                    {"metric": "Cross-functional attendance", "target": ">80%"},
                    {"metric": "Action items tracked to completion", "target": ">90%"}
                ]
            },
            "estimated_effort": "Medium",
            "typical_timeline": "30-60 days",
            "default_priority": "High",
            "target_axes": ["G"],
            "relevant_scenarios": ["IP_Theft", "Customer_Data_Breach", "Regulatory_Compliance"],
            "trigger_rules": {"axis_threshold": {"G": 50}}
        },
        {
            "rec_id": "REC_V_001",
            "category": "Technical",
            "subcategory": "Visibility & Monitoring",
            "title": "Deploy User Behavior Analytics (UBA) Solution",
            "description": "Implement UBA/UEBA platform to detect anomalous insider activity across endpoints, SaaS apps, and networks.",
            "rationale": "Without behavioral monitoring, malicious or accidental insider activity goes undetected until damage occurs.",
            "implementation_steps": {
                "steps": [
                    {"step": 1, "action": "Define use cases (data exfiltration, privilege abuse, anomalous access)", "owner": "Security Team"},
                    {"step": 2, "action": "Evaluate UBA vendors (UEBA, SIEM with ML, DLP with behavior analytics)", "owner": "Security Architect"},
                    {"step": 3, "action": "Pilot with high-risk user cohort (admins, developers, executives)", "owner": "SOC Lead"},
                    {"step": 4, "action": "Integrate alerts into SOC workflow and tune detection rules", "owner": "SOC Analyst"},
                    {"step": 5, "action": "Roll out to full user base with escalation procedures", "owner": "Security Operations"}
                ]
            },
            "success_criteria": {
                "metrics": [
                    {"metric": "UBA covers >95% of workforce", "target": ">95%"},
                    {"metric": "False positive rate", "target": "<5%"},
                    {"metric": "Mean time to detect anomaly", "target": "<24 hours"}
                ]
            },
            "vendor_suggestions": {
                "vendors": [
                    {"name": "Microsoft Sentinel", "type": "SIEM with UBA", "notes": "Native Azure integration"},
                    {"name": "Splunk UBA", "type": "Standalone UBA", "notes": "Strong ML capabilities"},
                    {"name": "Exabeam", "type": "SIEM with UEBA", "notes": "Insider threat focus"},
                    {"name": "Securonix", "type": "SIEM with UBA", "notes": "Good for large enterprises"}
                ]
            },
            "estimated_effort": "High",
            "typical_timeline": "3-6 months",
            "default_priority": "High",
            "target_axes": ["V", "T"],
            "relevant_scenarios": ["IP_Theft", "Privileged_Abuse", "Insider_Sabotage"],
            "trigger_rules": {"axis_threshold": {"V": 50}}
        },
        {
            "rec_id": "REC_T_001",
            "category": "Technical",
            "subcategory": "Data Loss Prevention",
            "title": "Implement Data Loss Prevention (DLP) Controls",
            "description": "Deploy DLP solution to monitor and block sensitive data exfiltration via email, web, cloud apps, and endpoints.",
            "rationale": "Without DLP, sensitive data can leave the organization undetected through multiple channels.",
            "implementation_steps": {
                "steps": [
                    {"step": 1, "action": "Classify sensitive data (PII, IP, financial, regulated)", "owner": "Data Governance"},
                    {"step": 2, "action": "Select DLP solution (cloud-native vs. endpoint-based)", "owner": "Security Architect"},
                    {"step": 3, "action": "Deploy in monitor mode to baseline data flows", "owner": "Security Engineering"},
                    {"step": 4, "action": "Create policies for high-risk scenarios (email, USB, cloud uploads)", "owner": "Security Policy"},
                    {"step": 5, "action": "Enable blocking mode for critical data with user education", "owner": "Security Operations"}
                ]
            },
            "success_criteria": {
                "metrics": [
                    {"metric": "DLP coverage across email, web, endpoints, cloud", "target": "100%"},
                    {"metric": "Policy violations detected and logged", "target": ">99%"},
                    {"metric": "False positive rate after tuning", "target": "<2%"}
                ]
            },
            "vendor_suggestions": {
                "vendors": [
                    {"name": "Microsoft Purview DLP", "type": "Cloud DLP", "notes": "M365 native"},
                    {"name": "Proofpoint DLP", "type": "Enterprise DLP", "notes": "Strong email/cloud"},
                    {"name": "Forcepoint DLP", "type": "Endpoint + Network", "notes": "Comprehensive"},
                    {"name": "Symantec DLP", "type": "Enterprise DLP", "notes": "Mature platform"}
                ]
            },
            "estimated_effort": "High",
            "typical_timeline": "4-6 months",
            "default_priority": "Critical",
            "target_axes": ["T", "V"],
            "relevant_scenarios": ["IP_Theft", "Customer_Data_Breach", "Shadow_IT_Leakage", "Accidental_Exposure"],
            "trigger_rules": {"risk_level": ["RED", "AMBER"]}
        },
        {
            "rec_id": "REC_E_001",
            "category": "Process",
            "subcategory": "Joiner-Mover-Leaver",
            "title": "Automate Joiner-Mover-Leaver (JML) Workflows",
            "description": "Implement automated provisioning/deprovisioning for all user accounts, with same-day termination revocation.",
            "rationale": "Manual JML processes are error-prone and slow, leaving orphan accounts and excess privileges active.",
            "implementation_steps": {
                "steps": [
                    {"step": 1, "action": "Integrate HRIS with IAM system (Okta, Entra ID, etc.)", "owner": "IT Operations"},
                    {"step": 2, "action": "Define account lifecycle rules (onboard, role change, offboard)", "owner": "HR + IT"},
                    {"step": 3, "action": "Automate provisioning for standard roles (self-service where possible)", "owner": "IAM Team"},
                    {"step": 4, "action": "Implement same-day termination triggers with pre-offboarding workflow", "owner": "HR + Security"},
                    {"step": 5, "action": "Set up periodic access reviews to catch orphan accounts", "owner": "Compliance"}
                ]
            },
            "success_criteria": {
                "metrics": [
                    {"metric": "Accounts deprovisioned same-day for terminations", "target": "100%"},
                    {"metric": "Zero orphan accounts in quarterly audit", "target": "0"},
                    {"metric": "Onboarding time for standard roles", "target": "<1 day"}
                ]
            },
            "prerequisites": ["Identity and Access Management (IAM) platform", "HRIS integration"],
            "estimated_effort": "High",
            "typical_timeline": "3-6 months",
            "default_priority": "High",
            "target_axes": ["E", "W"],
            "relevant_scenarios": ["Post_Termination_Access", "Privileged_Abuse"],
            "trigger_rules": {"axis_threshold": {"E": 50, "W": 50}}
        },
        {
            "rec_id": "REC_H_001",
            "category": "Training",
            "subcategory": "Awareness & Culture",
            "title": "Launch Insider Risk Awareness Training Program",
            "description": "Deploy mandatory annual training on insider threats, acceptable use, data handling, and reporting suspicious behavior.",
            "rationale": "Human error is a leading cause of insider incidents. Educated users are the first line of defense.",
            "implementation_steps": {
                "steps": [
                    {"step": 1, "action": "Develop training content covering accidental and malicious threats", "owner": "Security Awareness"},
                    {"step": 2, "action": "Include real-world examples and role-specific scenarios", "owner": "Training Team"},
                    {"step": 3, "action": "Deploy via LMS with tracking and completion metrics", "owner": "HR/Training"},
                    {"step": 4, "action": "Add phishing simulations and data handling tests", "owner": "Security Team"},
                    {"step": 5, "action": "Measure behavior change (incident reports, phishing click rates)", "owner": "Security Metrics"}
                ]
            },
            "success_criteria": {
                "metrics": [
                    {"metric": "Training completion rate", "target": ">95%"},
                    {"metric": "Post-training quiz pass rate", "target": ">80%"},
                    {"metric": "Phishing click rate reduction", "target": "-50% YoY"}
                ]
            },
            "estimated_effort": "Medium",
            "typical_timeline": "2-3 months",
            "default_priority": "Medium",
            "target_axes": ["H"],
            "relevant_scenarios": ["Accidental_Exposure", "Shadow_IT_Leakage"],
            "trigger_rules": {"axis_threshold": {"H": 50}}
        },
        {
            "rec_id": "REC_L_001",
            "category": "Legal & Compliance",
            "subcategory": "Privacy & GDPR",
            "title": "Conduct Data Protection Impact Assessment (DPIA) for Monitoring",
            "description": "Complete DPIA to ensure insider risk monitoring complies with GDPR, employee privacy laws, and works council requirements.",
            "rationale": "Failure to address privacy/legal obligations can lead to regulatory fines, employee lawsuits, and program shutdown.",
            "implementation_steps": {
                "steps": [
                    {"step": 1, "action": "Identify monitoring systems and data processed (UBA, DLP, email)", "owner": "Privacy Officer"},
                    {"step": 2, "action": "Document legal basis (legitimate interest, consent, legal obligation)", "owner": "Legal Counsel"},
                    {"step": 3, "action": "Consult works council or employee representatives where required", "owner": "HR + Legal"},
                    {"step": 4, "action": "Implement privacy safeguards (pseudonymization, access controls, retention limits)", "owner": "Security + Privacy"},
                    {"step": 5, "action": "Update privacy notices and transparency communications", "owner": "Privacy Team"}
                ]
            },
            "success_criteria": {
                "metrics": [
                    {"metric": "DPIA completed and approved by DPO", "target": "Yes"},
                    {"metric": "Works council consultation completed (if required)", "target": "Yes"},
                    {"metric": "Privacy notices updated", "target": "Yes"}
                ]
            },
            "external_resources": {
                "resources": [
                    {"title": "ICO DPIA Guidance", "url": "https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/accountability-and-governance/data-protection-impact-assessments/", "type": "guide"},
                    {"title": "CNIL Employee Monitoring Guidance", "url": "https://www.cnil.fr/en/employee-monitoring", "type": "regulation"}
                ]
            },
            "estimated_effort": "Medium",
            "typical_timeline": "1-2 months",
            "default_priority": "Critical",
            "target_axes": ["L", "G"],
            "relevant_scenarios": ["Regulatory_Compliance"],
            "trigger_rules": {"axis_threshold": {"L": 40}}
        },
        {
            "rec_id": "REC_F_001",
            "category": "Process",
            "subcategory": "Friction Reduction",
            "title": "Provide Approved Collaboration & GenAI Tools",
            "description": "Deploy sanctioned alternatives (secure file sharing, approved GenAI) to reduce shadow IT usage.",
            "rationale": "Users turn to unapproved tools when approved alternatives are too slow, complex, or unavailable.",
            "implementation_steps": {
                "steps": [
                    {"step": 1, "action": "Survey users to understand shadow IT drivers (speed, ease, features)", "owner": "IT + Security"},
                    {"step": 2, "action": "Evaluate secure alternatives (M365 Copilot, Google Workspace, secure file share)", "owner": "IT Architecture"},
                    {"step": 3, "action": "Deploy approved tools with easy onboarding and training", "owner": "IT Operations"},
                    {"step": 4, "action": "Communicate approved alternatives and block high-risk shadow IT", "owner": "Security + IT"},
                    {"step": 5, "action": "Monitor adoption and iterate based on feedback", "owner": "Product Owner"}
                ]
            },
            "success_criteria": {
                "metrics": [
                    {"metric": "Adoption of approved tools", "target": ">80%"},
                    {"metric": "Shadow IT usage reduction", "target": "-50% YoY"},
                    {"metric": "User satisfaction with approved tools", "target": ">4/5"}
                ]
            },
            "estimated_effort": "Medium",
            "typical_timeline": "2-4 months",
            "default_priority": "High",
            "target_axes": ["F"],
            "relevant_scenarios": ["Shadow_IT_Leakage"],
            "trigger_rules": {"axis_threshold": {"F": 50}}
        },
        {
            "rec_id": "REC_R_001",
            "category": "Technical",
            "subcategory": "Resilience & Recovery",
            "title": "Implement Immutable Backup Strategy",
            "description": "Deploy immutable backups (air-gapped or cloud-native) to protect against insider sabotage and ransomware.",
            "rationale": "Without immutable backups, insiders with admin access can delete backups, leaving no recovery path.",
            "implementation_steps": {
                "steps": [
                    {"step": 1, "action": "Assess current backup architecture and identify gaps", "owner": "IT Operations"},
                    {"step": 2, "action": "Select immutable backup solution (Veeam, Rubrik, AWS S3 Object Lock)", "owner": "Backup Architect"},
                    {"step": 3, "action": "Deploy immutable backups for critical systems (file servers, databases, VMs)", "owner": "Backup Team"},
                    {"step": 4, "action": "Test restoration from immutable backups quarterly", "owner": "DR Team"},
                    {"step": 5, "action": "Document restoration procedures and train IR team", "owner": "Incident Response"}
                ]
            },
            "success_criteria": {
                "metrics": [
                    {"metric": "Critical systems backed up immutably", "target": "100%"},
                    {"metric": "Successful quarterly restore tests", "target": "100%"},
                    {"metric": "Recovery time objective (RTO) met in tests", "target": "<24 hours"}
                ]
            },
            "vendor_suggestions": {
                "vendors": [
                    {"name": "Veeam", "type": "Backup", "notes": "Immutability feature in v12+"},
                    {"name": "Rubrik", "type": "Backup", "notes": "Cloud-native immutable snapshots"},
                    {"name": "AWS S3 Object Lock", "type": "Cloud Storage", "notes": "WORM compliance mode"},
                    {"name": "Commvault", "type": "Backup", "notes": "Enterprise-grade"}
                ]
            },
            "estimated_effort": "High",
            "typical_timeline": "3-6 months",
            "default_priority": "Critical",
            "target_axes": ["R"],
            "relevant_scenarios": ["Insider_Sabotage"],
            "trigger_rules": {"risk_level": ["RED"]}
        }
    ]

    try:
        added_count = 0
        updated_count = 0

        for rec_data in recommendations:
            existing = db.query(models.Recommendation).filter_by(rec_id=rec_data["rec_id"]).first()
            if not existing:
                rec = models.Recommendation(**rec_data)
                db.add(rec)
                print(f"  [+] Added: {rec_data['rec_id']} - {rec_data['title']}")
                added_count += 1
            else:
                print(f"  [~] Already exists: {rec_data['rec_id']} - {existing.title}")
                updated_count += 1

        db.commit()
        print(f"\n✓ Seeding complete!")
        print(f"  - {added_count} recommendations added")
        print(f"  - {updated_count} recommendations already existed")
        print(f"  - Total in library: {added_count + updated_count}")
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error seeding recommendations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("IRMMF Recommendation Library Seeder")
    print("=" * 60)
    seed_recommendations()
    print("=" * 60)
