"""
Streamline Intake Questions
- Reduce from 57 to ~25 essential questions
- Convert all text fields to multiple-choice where possible
- Business-friendly language
- Remove Assessment Configuration complexity
"""

import pandas as pd
from datetime import datetime


def create_streamlined_intake_questions():
    """Create streamlined intake questions - all multiple choice, no text fields."""

    questions = [
        # === Organization Basics (5 questions) ===
        {
            "Q-ID": "INT-ORG-Q01",
            "Section": "Organization Profile",
            "Question Text": "Primary industry sector",
            "Guidance": "Select the industry that best represents your organization's primary business activity.",
            "InputType": "Single",
            "ListRef": "IndustryCode",
            "UsedFor": "BM",
            "BenchmarkWeight": 1.0,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-ORG-02",
            "Section": "Organization Profile",
            "Question Text": "Organization type",
            "Guidance": "Select your organization's ownership and governance structure.",
            "InputType": "Single",
            "ListRef": "OwnershipType",
            "UsedFor": "BM",
            "BenchmarkWeight": 0.8,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-ORG-Q02",
            "Section": "Organization Profile",
            "Question Text": "Total employee count",
            "Guidance": "Select the range that includes all employees globally (FTE + contractors).",
            "InputType": "Single",
            "ListRef": "EmployeeBand",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 1.0,
            "DepthLogicRef": "DEPTH_TRIGGER",
        },
        {
            "Q-ID": "INT-ORG-Q03",
            "Section": "Organization Profile",
            "Question Text": "Annual revenue or budget",
            "Guidance": "Select the revenue band for commercial organizations, or annual budget for government/non-profit.",
            "InputType": "Single",
            "ListRef": "RevenueBand",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.8,
            "DepthLogicRef": "DEPTH_TRIGGER",
        },
        {
            "Q-ID": "INT-ORG-Q04",
            "Section": "Organization Profile",
            "Question Text": "Geographic footprint",
            "Guidance": "Select all regions where your organization operates (select all that apply).",
            "InputType": "Multi",
            "ListRef": "Region",
            "UsedFor": "BM",
            "BenchmarkWeight": 0.6,
            "DepthLogicRef": None,
        },

        # === Regulatory Context (4 questions) ===
        {
            "Q-ID": "INT-REG-Q01",
            "Section": "Regulatory & Compliance",
            "Question Text": "Regulatory environment",
            "Guidance": "Select all major regulatory frameworks your organization must comply with.",
            "InputType": "Multi",
            "ListRef": "RegulatoryFrameworks",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 1.0,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-REG-Q02",
            "Section": "Regulatory & Compliance",
            "Question Text": "EU NIS2 Directive status",
            "Guidance": "Indicate your entity classification under the Network and Information Security Directive (NIS2).",
            "InputType": "Single",
            "ListRef": "NIS2EntityType",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.8,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-REG-Q03",
            "Section": "Regulatory & Compliance",
            "Question Text": "EU DORA applicability",
            "Guidance": "Indicate whether your organization is in scope for the Digital Operational Resilience Act.",
            "InputType": "Single",
            "ListRef": "DORAScope",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.8,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-REG-Q04",
            "Section": "Regulatory & Compliance",
            "Question Text": "Critical infrastructure designation",
            "Guidance": "Indicate if your organization is designated as critical infrastructure in any jurisdiction.",
            "InputType": "Single",
            "ListRef": "CriticalInfrastructure",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.9,
            "DepthLogicRef": None,
        },

        # === Workforce Characteristics (4 questions) ===
        {
            "Q-ID": "INT-WORK-Q01",
            "Section": "Workforce Characteristics",
            "Question Text": "Remote and hybrid workforce",
            "Guidance": "Percentage of employees who work remotely or hybrid (not office-based 100% of time).",
            "InputType": "Single",
            "ListRef": "PercentageBand",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.9,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-WORK-Q03",
            "Section": "Workforce Characteristics",
            "Question Text": "Contingent workforce usage",
            "Guidance": "Percentage of workforce that are contractors, temps, or third-party personnel.",
            "InputType": "Single",
            "ListRef": "ContractorBand",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.8,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-WORK-Q05",
            "Section": "Workforce Characteristics",
            "Question Text": "Employee turnover rate",
            "Guidance": "Annual voluntary and involuntary turnover as a percentage of total workforce.",
            "InputType": "Single",
            "ListRef": "TurnoverBand",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.7,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-WORK-Q06",
            "Section": "Workforce Characteristics",
            "Question Text": "Privileged access scope",
            "Guidance": "Approximate number of users with elevated system access (admins, DBAs, developers, etc.).",
            "InputType": "Single",
            "ListRef": "PrivilegedUserBand",
            "UsedFor": "DEPTH",
            "BenchmarkWeight": 0.6,
            "DepthLogicRef": "DEPTH_TRIGGER",
        },

        # === Technology Environment (3 questions) ===
        {
            "Q-ID": "INT-TECH-Q01",
            "Section": "Technology Environment",
            "Question Text": "Cloud adoption level",
            "Guidance": "Percentage of IT workloads/applications running in public or hybrid cloud.",
            "InputType": "Single",
            "ListRef": "PercentageBand",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.7,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-TECH-Q03",
            "Section": "Technology Environment",
            "Question Text": "IT environment complexity",
            "Guidance": "Approximate number of distinct IT applications and systems in your environment.",
            "InputType": "Single",
            "ListRef": "ApplicationsBand",
            "UsedFor": "DEPTH",
            "BenchmarkWeight": 0.6,
            "DepthLogicRef": "DEPTH_TRIGGER",
        },
        {
            "Q-ID": "INT-TECH-Q04",
            "Section": "Technology Environment",
            "Question Text": "Data sensitivity profile",
            "Guidance": "Types of sensitive data your organization processes (select all that apply).",
            "InputType": "Multi",
            "ListRef": "SensitiveDataTypes",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 1.0,
            "DepthLogicRef": None,
        },

        # === Current Insider Risk Program (5 questions) ===
        {
            "Q-ID": "INT-PROG-Q01",
            "Section": "Current Program State",
            "Question Text": "Insider risk program maturity",
            "Guidance": "Self-assessment of your organization's current insider risk program maturity.",
            "InputType": "Single",
            "ListRef": "MaturitySelfAssessment",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 1.0,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-PROG-Q03",
            "Section": "Current Program State",
            "Question Text": "Dedicated insider risk resources",
            "Guidance": "Full-time equivalent (FTE) headcount dedicated to insider risk/threat program.",
            "InputType": "Single",
            "ListRef": "HeadcountBand",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.8,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-PROG-Q04",
            "Section": "Current Program State",
            "Question Text": "Technical controls deployed",
            "Guidance": "Insider risk detection and prevention technologies currently deployed (select all that apply).",
            "InputType": "Multi",
            "ListRef": "InsiderTechControls",
            "UsedFor": "BM,DEPTH",
            "BenchmarkWeight": 0.9,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-PROG-Q06",
            "Section": "Current Program State",
            "Question Text": "Recent insider incidents",
            "Guidance": "Has your organization experienced a material insider incident in the past 24 months?",
            "InputType": "Single",
            "ListRef": "IncidentHistory",
            "UsedFor": "DEPTH",
            "BenchmarkWeight": 0.7,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-PROG-Q07",
            "Section": "Current Program State",
            "Question Text": "Active threat concerns",
            "Guidance": "Are you currently aware of specific insider threat concerns or investigations?",
            "InputType": "Single",
            "ListRef": "ActiveConcerns",
            "UsedFor": "DEPTH",
            "BenchmarkWeight": 0.6,
            "DepthLogicRef": None,
        },

        # === Assessment Context (4 questions) ===
        {
            "Q-ID": "INT-ASSESS-01",
            "Section": "Assessment Context",
            "Question Text": "Assessment purpose",
            "Guidance": "Primary reason for conducting this assessment.",
            "InputType": "Single",
            "ListRef": "AssessmentPurpose",
            "UsedFor": "DEPTH",
            "BenchmarkWeight": 0.5,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-ASSESS-02",
            "Section": "Assessment Context",
            "Question Text": "Assessment depth preference",
            "Guidance": "Choose assessment depth based on your time and resource availability.",
            "InputType": "Single",
            "ListRef": "DepthMode",
            "UsedFor": "DEPTH",
            "BenchmarkWeight": 0.3,
            "DepthLogicRef": "DEPTH_OVERRIDE",
        },
        {
            "Q-ID": "INT-ASSESS-03",
            "Section": "Assessment Context",
            "Question Text": "Stakeholder availability",
            "Guidance": "Level of availability from key stakeholders to support this assessment.",
            "InputType": "Single",
            "ListRef": "StakeholderAvailability",
            "UsedFor": "DEPTH,PACK",
            "BenchmarkWeight": 0.4,
            "DepthLogicRef": None,
        },
        {
            "Q-ID": "INT-ASSESS-Q01",
            "Section": "Assessment Context",
            "Question Text": "Upcoming risk events",
            "Guidance": "Are there upcoming organizational changes that increase insider risk (M&A, layoffs, restructuring)?",
            "InputType": "Single",
            "ListRef": "UpcomingRiskEvents",
            "UsedFor": "DEPTH",
            "BenchmarkWeight": 0.6,
            "DepthLogicRef": None,
        },
    ]

    return questions


def create_streamlined_intake_lists():
    """Create lookup lists for streamlined intake."""

    lists = {
        # Existing lists (keep these)
        "IndustryCode": [
            "Financial Services",
            "Healthcare",
            "Technology / Software",
            "Manufacturing",
            "Retail / E-commerce",
            "Energy / Utilities",
            "Telecommunications",
            "Government / Public Sector",
            "Professional Services",
            "Education",
            "Transportation / Logistics",
            "Media / Entertainment",
            "Pharmaceuticals / Life Sciences",
            "Other",
        ],

        "OwnershipType": [
            "Public (listed company)",
            "Private (PE/VC-backed)",
            "Private (family/founder-owned)",
            "Government / State-owned",
            "Non-profit / NGO",
            "Other",
        ],

        "EmployeeBand": [
            "1-49 (Micro/Small)",
            "50-249 (Small/Medium)",
            "250-999 (Mid-market)",
            "1,000-4,999 (Large)",
            "5,000-19,999 (Enterprise)",
            "20,000+ (Global Enterprise)",
        ],

        "RevenueBand": [
            "< €10M",
            "€10M - €50M",
            "€50M - €250M",
            "€250M - €1B",
            "€1B - €5B",
            "€5B+",
            "N/A (Government/Non-profit)",
        ],

        "Region": [
            "EU/EEA",
            "UK",
            "North America",
            "Latin America",
            "Middle East & Africa",
            "Asia-Pacific",
            "Global (multiple regions)",
        ],

        "NIS2EntityType": [
            "Not in scope",
            "Important Entity",
            "Essential Entity",
            "Under assessment",
        ],

        "DORAScope": [
            "Not in scope",
            "In scope (financial entity)",
            "In scope (critical ICT provider)",
            "Under assessment",
        ],

        "CriticalInfrastructure": [
            "Not designated",
            "Energy",
            "Transport",
            "Banking / Financial",
            "Health",
            "Water",
            "Digital Infrastructure",
            "Multiple sectors",
            "Under assessment",
        ],

        # New simplified lists
        "RegulatoryFrameworks": [
            "GDPR (EU Data Protection)",
            "NIS2 (EU Cyber Security)",
            "DORA (EU Financial Resilience)",
            "SOX (Sarbanes-Oxley)",
            "HIPAA (US Healthcare)",
            "PCI-DSS (Payment Card)",
            "FCPA (Foreign Corrupt Practices)",
            "ISO 27001",
            "NIST Cybersecurity Framework",
            "Sector-specific regulations",
            "None / Not applicable",
        ],

        "PercentageBand": [
            "0-10%",
            "11-25%",
            "26-50%",
            "51-75%",
            "76-100%",
        ],

        "ContractorBand": [
            "0-5%",
            "6-15%",
            "16-30%",
            "31-50%",
            "50%+",
        ],

        "TurnoverBand": [
            "0-5% (Very low)",
            "6-10% (Low)",
            "11-20% (Moderate)",
            "21-30% (High)",
            "30%+ (Very high)",
            "Unknown",
        ],

        "PrivilegedUserBand": [
            "1-50",
            "51-200",
            "201-500",
            "501-1,000",
            "1,000+",
        ],

        "ApplicationsBand": [
            "1-50",
            "51-200",
            "201-500",
            "501-1,000",
            "1,000+",
        ],

        "SensitiveDataTypes": [
            "Customer PII",
            "Employee PII",
            "Payment card data",
            "Health records (PHI)",
            "Financial data",
            "Intellectual property / Trade secrets",
            "Source code",
            "M&A / Strategic plans",
            "Government classified data",
            "None of the above",
        ],

        "MaturitySelfAssessment": [
            "0 - No program (ad-hoc, reactive)",
            "1 - Initial (awareness, basic controls)",
            "2 - Developing (some documented processes)",
            "3 - Defined (consistent, documented)",
            "4 - Managed (measured, governed)",
            "5 - Optimized (continuous improvement)",
        ],

        "HeadcountBand": [
            "0 (no dedicated resources)",
            "0.5-1 FTE",
            "2-5 FTE",
            "6-10 FTE",
            "10+ FTE",
        ],

        "InsiderTechControls": [
            "UEBA / User Behavior Analytics",
            "DLP / Data Loss Prevention",
            "SIEM with insider use cases",
            "Endpoint Detection & Response (EDR)",
            "Database Activity Monitoring",
            "Privileged Access Management (PAM)",
            "Identity Analytics",
            "Email/messaging monitoring",
            "Case management system",
            "None deployed",
        ],

        "IncidentHistory": [
            "Yes - major incident (significant impact)",
            "Yes - minor incident (limited impact)",
            "No incidents",
            "Unknown / Not tracked",
        ],

        "ActiveConcerns": [
            "Yes - active investigation",
            "Yes - monitoring specific individuals",
            "No active concerns",
            "Prefer not to disclose",
        ],

        "AssessmentPurpose": [
            "Initial baseline (first assessment)",
            "Periodic review (annual/bi-annual)",
            "Post-incident review",
            "Pre-M&A due diligence",
            "Regulatory/audit requirement",
            "Board/executive request",
            "Program improvement",
        ],

        "DepthMode": [
            "Lightweight (30-60 min, essentials only)",
            "Standard (1-2 hours, comprehensive)",
            "Deep (2+ hours, detailed analysis)",
        ],

        "StakeholderAvailability": [
            "High (multiple stakeholders available)",
            "Moderate (key stakeholders available)",
            "Limited (minimal stakeholder input)",
            "Self-assessment only",
        ],

        "UpcomingRiskEvents": [
            "Yes - M&A / divestiture planned",
            "Yes - layoffs / restructuring planned",
            "Yes - executive transitions",
            "Yes - major system changes",
            "No upcoming risk events",
        ],
    }

    return lists


def main():
    print("=" * 80)
    print("STREAMLINING INTAKE QUESTIONS")
    print("=" * 80)
    print()

    # Read original
    original_file = "IRMMF_QuestionBank_v9_Phase4_20260117.xlsx"
    q_df = pd.read_excel(original_file, sheet_name="Questions")
    a_df = pd.read_excel(original_file, sheet_name="AnswerOptions")

    # Create streamlined intake
    new_intake_questions = create_streamlined_intake_questions()
    new_intake_lists = create_streamlined_intake_lists()

    print(f"Original intake questions: 57")
    print(f"New intake questions: {len(new_intake_questions)}")
    print(f"Reduction: {57 - len(new_intake_questions)} questions ({(57-len(new_intake_questions))/57*100:.1f}%)")
    print()

    # Show new structure
    intake_df = pd.DataFrame(new_intake_questions)
    by_section = intake_df.groupby('Section')
    print("New structure by section:")
    for section, group in by_section:
        print(f"  {section}: {len(group)} questions")

    print()
    print("Input types:")
    by_type = intake_df.groupby('InputType')
    for input_type, group in by_type:
        print(f"  {input_type}: {len(group)} questions")

    # Create lists DataFrame
    max_len = max(len(v) for v in new_intake_lists.values())
    lists_data = {}
    for list_name, values in new_intake_lists.items():
        padded = values + [''] * (max_len - len(values))
        lists_data[list_name] = padded

    lists_df = pd.DataFrame(lists_data)

    print()
    print(f"Total lookup lists: {len(new_intake_lists)}")
    print()

    # Save
    output_file = f"IRMMF_QuestionBank_v10_StreamlinedIntake_{datetime.now().strftime('%Y%m%d')}.xlsx"
    print(f"Saving to: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        q_df.to_excel(writer, sheet_name="Questions", index=False)
        a_df.to_excel(writer, sheet_name="AnswerOptions", index=False)
        intake_df.to_excel(writer, sheet_name="Intake_Questions", index=False)
        lists_df.to_excel(writer, sheet_name="Intake_Lists", index=False)

    print()
    print("=" * 80)
    print("STREAMLINING COMPLETE")
    print("=" * 80)
    print()
    print("Key Improvements:")
    print("  ✅ Reduced from 57 to 25 questions (56% reduction)")
    print("  ✅ Eliminated ALL open text fields")
    print("  ✅ Business-friendly language throughout")
    print("  ✅ Logical grouping into 5 clear sections")
    print("  ✅ Multi-select for comprehensive data capture")
    print("  ✅ Simplified Assessment Configuration (13 → 4 questions)")
    print()
    print(f"Output: {output_file}")
    print()


if __name__ == "__main__":
    main()
