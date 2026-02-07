"""
Phase 2 Question Bank Enhancement Script
- Apply professional language to remaining 302 questions
- Add fraud investigation questions (ACFE frameworks, chain of custody)
- Add regulatory compliance questions (NIS2, DORA, SOX, FCPA)
- Expand privileged user/executive oversight questions
"""

import pandas as pd
from datetime import datetime
import shutil

# Professional question transformations (expanded from Phase 1)
QUESTION_ENHANCEMENTS = {
    # Phase 1 patterns (existing)
    "Do you have": "To what extent does your organization maintain",
    "Can you detect": "What level of capability exists to identify and investigate",
    "Do you provide": "To what extent does your organization provide",
    "Do managers": "To what extent do managers",
    "Do employees": "To what extent do employees",
    "Are executives": "To what extent are executives",

    # Phase 2 patterns (new)
    "Do you test": "To what extent does your organization test",
    "How do you handle": "What approach does your organization employ to manage",
    "Can you rapidly": "What level of capability exists to rapidly",
    "Do business continuity": "To what extent do business continuity",
    "Do you monitor": "What level of monitoring capability exists for",
    "Do you restrict": "To what extent does your organization restrict",
    "Is there a": "To what extent does your organization maintain a",
    "Are there": "To what extent are there",
    "Does your organization": "To what extent does your organization",
    "Can your organization": "What level of capability does your organization have to",
    "Have you": "To what extent has your organization",
    "Will you": "To what extent will your organization",
}

# Guidance enhancements with regulatory references
GUIDANCE_REGULATORY_ADDITIONS = {
    "NIS2": "NIS2 (Network and Information Security Directive 2) requires robust insider risk management, incident reporting within 24 hours, and supply chain security controls.",
    "DORA": "DORA (Digital Operational Resilience Act) mandates ICT risk management, incident classification, and third-party risk oversight for financial entities.",
    "SOX": "SOX Section 404 requires internal controls over financial reporting, including prevention of insider fraud and unauthorized financial transactions.",
    "FCPA": "FCPA (Foreign Corrupt Practices Act) compliance requires anti-bribery controls, gift/hospitality monitoring, and third-party due diligence.",
    "GDPR": "GDPR Article 32 requires appropriate security measures including access controls, monitoring, and pseudonymization to prevent insider data breaches.",
    "HIPAA": "HIPAA Security Rule requires administrative, physical, and technical safeguards against workforce member access violations and PHI breaches.",
    "PCI-DSS": "PCI-DSS Requirement 7-10 mandate least privilege access, monitoring, and logging of all access to cardholder data by privileged users.",
}

def enhance_question_text(text):
    """Apply professional language transformations to question text."""
    for pattern, replacement in QUESTION_ENHANCEMENTS.items():
        if text.startswith(pattern):
            text = text.replace(pattern, replacement, 1)
            break
    return text

def add_regulatory_guidance(guidance, domain, question_text):
    """Add relevant regulatory references to guidance text."""
    if pd.isna(guidance) or guidance == "":
        guidance = ""

    # Add regulatory references based on content keywords
    regulations_to_add = []

    # Financial/accounting questions
    if any(kw in question_text.lower() for kw in ["financial", "accounting", "sox", "fraud", "bribery", "corruption"]):
        if "SOX" not in guidance:
            regulations_to_add.append("SOX")
        if "fcpa" in question_text.lower() or "bribery" in question_text.lower():
            if "FCPA" not in guidance:
                regulations_to_add.append("FCPA")

    # Technology/cyber questions
    if any(kw in question_text.lower() for kw in ["cyber", "network", "security", "incident", "breach"]):
        if "NIS2" not in guidance:
            regulations_to_add.append("NIS2")

    # Financial services questions
    if any(kw in question_text.lower() for kw in ["operational resilience", "recovery", "ict", "third-party"]):
        if domain in ["3. Risk Management", "9. Performance & Resilience"]:
            if "DORA" not in guidance:
                regulations_to_add.append("DORA")

    # Privacy/data protection
    if any(kw in question_text.lower() for kw in ["personal data", "privacy", "gdpr", "data protection"]):
        if "GDPR" not in guidance:
            regulations_to_add.append("GDPR")

    # Healthcare
    if any(kw in question_text.lower() for kw in ["healthcare", "phi", "medical", "hipaa"]):
        if "HIPAA" not in guidance:
            regulations_to_add.append("HIPAA")

    # Payment card
    if any(kw in question_text.lower() for kw in ["payment", "cardholder", "pci"]):
        if "PCI-DSS" not in guidance:
            regulations_to_add.append("PCI-DSS")

    # Append regulatory references
    for reg in regulations_to_add:
        if guidance and not guidance.endswith("."):
            guidance += ". "
        guidance += f" {GUIDANCE_REGULATORY_ADDITIONS[reg]}"

    return guidance.strip()

def create_new_fraud_questions():
    """Create new fraud investigation and compliance questions."""
    new_questions = []

    # Fraud Investigation Questions (ACFE Framework)
    fraud_questions = [
        {
            "Q-ID": "FRAUD-01",
            "IRMMF Domain": "8. Investigation & Response",
            "Question Title": "Fraud Examination Capability",
            "Question Text": "To what extent does your organization maintain fraud examination capabilities aligned with ACFE (Association of Certified Fraud Examiners) standards?",
            "Guidance": "ACFE standards require trained fraud examiners, documented investigation procedures, interview protocols, and evidence handling procedures. Investigations should follow the Fraud Triangle model (opportunity, pressure, rationalization) and maintain independence from operational management.",
            "Tier": "T2",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "F",
            "CW": 1.0,
            "Pts_G": 0, "Pts_E": 0, "Pts_T": 0, "Pts_L": 0, "Pts_H": 0, "Pts_V": 0, "Pts_R": 0.2, "Pts_F": 0.5, "Pts_W": 0.3,
        },
        {
            "Q-ID": "FRAUD-Q01",
            "IRMMF Domain": "8. Investigation & Response",
            "Question Title": "Chain of Custody Procedures",
            "Question Text": "To what extent does your organization maintain documented chain of custody procedures for digital and physical evidence in insider investigations?",
            "Guidance": "Chain of custody requires: (1) Evidence identification and documentation at collection; (2) Secure storage with access logs; (3) Transfer documentation with signatures; (4) Forensic imaging with hash verification; (5) Tamper-evident packaging for physical evidence. Essential for legal admissibility under Federal Rules of Evidence 901-902.",
            "Tier": "T2",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "F",
            "CW": 1.0,
            "Pts_G": 0, "Pts_E": 0, "Pts_T": 0.2, "Pts_L": 0.3, "Pts_H": 0, "Pts_V": 0, "Pts_R": 0.2, "Pts_F": 0.3, "Pts_W": 0,
        },
        {
            "Q-ID": "FRAUD-03",
            "IRMMF Domain": "4. Legal & Compliance",
            "Question Title": "Whistleblower Intake Process",
            "Question Text": "To what extent does your organization maintain a structured whistleblower intake process that ensures confidentiality, non-retaliation, and timely case assessment?",
            "Guidance": "SOX Section 301 and Dodd-Frank Section 922 require confidential whistleblower channels for financial misconduct. Best practices include: anonymous reporting options (hotline, web portal), dedicated intake team independent of management, standardized triage and risk assessment, prohibition of retaliation (SOX 806), and feedback mechanisms. NIS2 extends whistleblower protection to cybersecurity incidents.",
            "Tier": "T1",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "L",
            "CW": 1.0,
            "Pts_G": 0.2, "Pts_E": 0, "Pts_T": 0, "Pts_L": 0.4, "Pts_H": 0.2, "Pts_V": 0, "Pts_R": 0.2, "Pts_F": 0, "Pts_W": 0,
        },
        {
            "Q-ID": "FRAUD-04",
            "IRMMF Domain": "4. Legal & Compliance",
            "Question Title": "Whistleblower Case Management",
            "Question Text": "To what extent does your organization track whistleblower cases from intake through resolution, including retaliation monitoring and outcome reporting?",
            "Guidance": "Effective case management requires: (1) Unique case identifiers preserving anonymity; (2) Investigation timelines (SOX requires 'prompt' investigation); (3) Substantiation rates and trending; (4) Retaliation monitoring (employment actions, performance reviews) for 180 days post-report; (5) Board/Audit Committee reporting on material cases. EU Whistleblowing Directive requires feedback within 3 months.",
            "Tier": "T2",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "L",
            "CW": 1.0,
            "Pts_G": 0.3, "Pts_E": 0, "Pts_T": 0, "Pts_L": 0.3, "Pts_H": 0, "Pts_V": 0, "Pts_R": 0.2, "Pts_F": 0.2, "Pts_W": 0,
        },
        {
            "Q-ID": "FRAUD-Q02",
            "IRMMF Domain": "4. Legal & Compliance",
            "Question Title": "SOX Internal Controls Testing",
            "Question Text": "To what extent does your organization test insider risk controls over financial reporting as part of SOX Section 404 compliance?",
            "Guidance": "SOX 404 requires annual assessment of internal controls over financial reporting (ICFR). Insider risk controls to test include: segregation of duties in financial systems, privileged access reviews for accounting staff, monitoring of journal entry approvals, detection of unauthorized transactions, and controls over period-end close processes. PCAOB AS 2201 requires substantive testing, not just walkthroughs.",
            "Tier": "T2",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "L",
            "CW": 1.0,
            "Pts_G": 0.2, "Pts_E": 0.2, "Pts_T": 0.2, "Pts_L": 0.3, "Pts_H": 0, "Pts_V": 0, "Pts_R": 0, "Pts_F": 0.1, "Pts_W": 0,
        },
        {
            "Q-ID": "FRAUD-Q03",
            "IRMMF Domain": "3. Risk Management",
            "Question Title": "FCPA Anti-Bribery Controls",
            "Question Text": "To what extent does your organization monitor employees for FCPA violations including gifts to foreign officials, improper payments, and falsified records?",
            "Guidance": "FCPA requires: (1) Prohibition of payments to foreign officials to obtain/retain business; (2) Accurate books and records (no off-book accounts); (3) Internal controls preventing corrupt payments. Detection controls include: expense report screening for government interactions, third-party due diligence, political contributions monitoring, and gift/hospitality registries with thresholds. DOJ Evaluation of Corporate Compliance Programs emphasizes monitoring effectiveness.",
            "Tier": "T3",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "L",
            "CW": 1.0,
            "Pts_G": 0.1, "Pts_E": 0.2, "Pts_T": 0.1, "Pts_L": 0.4, "Pts_H": 0, "Pts_V": 0.1, "Pts_R": 0.1, "Pts_F": 0, "Pts_W": 0,
        },
    ]

    # Privileged User / Executive Oversight Questions
    privileged_questions = [
        {
            "Q-ID": "EXEC-01",
            "IRMMF Domain": "1. Strategy & Governance",
            "Question Title": "Executive Insider Risk Governance",
            "Question Text": "To what extent does the Board of Directors receive regular reporting on executive and privileged user insider risk exposures, incidents, and control effectiveness?",
            "Guidance": "Board oversight of executive insider risk is critical given higher-impact potential. Reporting should include: (1) Privileged access review results (C-suite, board members); (2) Policy exception requests from executives; (3) Investigations involving senior leadership; (4) Third-party relationships managed by executives; (5) Travel to high-risk jurisdictions. NIS2 Article 20 requires management body accountability for cyber risk, including insider threats.",
            "Tier": "T1",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "G",
            "CW": 1.0,
            "Pts_G": 0.5, "Pts_E": 0.1, "Pts_T": 0, "Pts_L": 0.2, "Pts_H": 0.1, "Pts_V": 0.1, "Pts_R": 0, "Pts_F": 0, "Pts_W": 0,
        },
        {
            "Q-ID": "EXEC-Q01",
            "IRMMF Domain": "2. Threat Model & Operations",
            "Question Title": "Executive Threat Assessment",
            "Question Text": "To what extent does your organization maintain specific threat assessments for executives and board members considering elevated access, external targeting, and reputational impact?",
            "Guidance": "Executive threat assessment should address: (1) Espionage/recruitment by nation-states or competitors; (2) Unauthorized disclosure of M&A, earnings, strategy; (3) Conflicts of interest (board seats, investments, family employment); (4) Succession planning risks (key person dependencies); (5) Extortion/blackmail vulnerabilities. DORA Article 6 requires scenario-based testing including senior management compromise.",
            "Tier": "T2",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "E",
            "CW": 1.0,
            "Pts_G": 0.2, "Pts_E": 0.4, "Pts_T": 0.1, "Pts_L": 0.1, "Pts_H": 0, "Pts_V": 0.1, "Pts_R": 0.1, "Pts_F": 0, "Pts_W": 0,
        },
        {
            "Q-ID": "EXEC-03",
            "IRMMF Domain": "6. Technical Controls",
            "Question Title": "Privileged Access Monitoring",
            "Question Text": "What level of monitoring capability exists for privileged user activities including executives, system administrators, DBAs, and cloud administrators?",
            "Guidance": "Privileged access monitoring should include: (1) Session recording for admin consoles, databases, cloud management planes; (2) Command logging with anomaly detection (unusual commands, off-hours, bulk operations); (3) Privilege escalation alerts (sudo, runas); (4) Multi-person authorization for sensitive operations; (5) Just-in-time access with automatic revocation. PCI-DSS 10.2-10.3 mandate detailed logging of privileged actions. DORA Article 30 requires monitoring of ICT services including privileged access.",
            "Tier": "T2",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "T",
            "CW": 1.0,
            "Pts_G": 0, "Pts_E": 0.1, "Pts_T": 0.5, "Pts_L": 0.1, "Pts_H": 0, "Pts_V": 0.2, "Pts_R": 0, "Pts_F": 0.1, "Pts_W": 0,
        },
        {
            "Q-ID": "EXEC-Q02",
            "IRMMF Domain": "8. Investigation & Response",
            "Question Title": "Executive Investigation Protocols",
            "Question Text": "To what extent does your organization maintain pre-defined protocols for investigating allegations involving executives, including independence requirements and legal privilege considerations?",
            "Guidance": "Executive investigations require heightened independence and legal rigor: (1) Board/Audit Committee oversight (not reporting line management); (2) External counsel engagement for legal privilege; (3) Forensic preservation without tipping off subject; (4) Consideration of regulatory reporting obligations (SOX, SEC); (5) Communications plan for stakeholders/investors. NYSE and Nasdaq listing rules require audit committee oversight of legal/regulatory compliance.",
            "Tier": "T3",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "R",
            "CW": 1.0,
            "Pts_G": 0.3, "Pts_E": 0, "Pts_T": 0.1, "Pts_L": 0.3, "Pts_H": 0, "Pts_V": 0, "Pts_R": 0.2, "Pts_F": 0.1, "Pts_W": 0,
        },
    ]

    # Regulatory Compliance Questions
    regulatory_questions = [
        {
            "Q-ID": "REG-NIS2-01",
            "IRMMF Domain": "4. Legal & Compliance",
            "Question Title": "NIS2 Insider Risk Management",
            "Question Text": "To what extent does your organization address insider threats as part of NIS2 (Network and Information Security Directive 2) cybersecurity risk management?",
            "Guidance": "NIS2 Article 21 requires cybersecurity risk management measures including: (1) Policies on risk analysis and information system security (including insider threats); (2) Incident handling (24-hour notification for significant incidents); (3) Business continuity and crisis management; (4) Supply chain security; (5) Security in network and information systems acquisition, development, and maintenance. Article 20 mandates management body approval and oversight.",
            "Tier": "T3",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "L",
            "CW": 1.0,
            "Pts_G": 0.2, "Pts_E": 0.1, "Pts_T": 0.2, "Pts_L": 0.4, "Pts_H": 0, "Pts_V": 0, "Pts_R": 0.1, "Pts_F": 0, "Pts_W": 0,
        },
        {
            "Q-ID": "REG-DORA-01",
            "IRMMF Domain": "9. Performance & Resilience",
            "Question Title": "DORA Operational Resilience",
            "Question Text": "To what extent does your organization incorporate insider threat scenarios into DORA (Digital Operational Resilience Act) ICT risk management and resilience testing?",
            "Guidance": "DORA Article 6 requires scenario-based testing including cyber attacks and system failures. Insider threat scenarios should include: (1) Privileged user sabotage of critical systems; (2) Data exfiltration by developers/DBAs; (3) Disruption of payment/settlement systems; (4) Compromise of third-party service providers. Article 11 requires Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) considering insider-caused disruptions.",
            "Tier": "T3",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "W",
            "CW": 1.0,
            "Pts_G": 0.1, "Pts_E": 0.2, "Pts_T": 0.1, "Pts_L": 0.2, "Pts_H": 0, "Pts_V": 0, "Pts_R": 0.1, "Pts_F": 0, "Pts_W": 0.3,
        },
        {
            "Q-ID": "REG-GDPR-01",
            "IRMMF Domain": "4. Legal & Compliance",
            "Question Title": "GDPR Insider Risk Controls",
            "Question Text": "To what extent does your organization implement technical and organizational measures to prevent insider breaches of personal data as required by GDPR Article 32?",
            "Guidance": "GDPR Article 32 requires: (1) Pseudonymization and encryption of personal data; (2) Ability to ensure ongoing confidentiality, integrity, availability, and resilience; (3) Ability to restore availability after incidents; (4) Regular testing and evaluation. Article 33 requires breach notification within 72 hours. Insider-specific controls include: access logging (Article 30), employee training (Article 39), and data protection by design (Article 25).",
            "Tier": "T2",
            "BranchType": "",
            "GateThreshold": "",
            "NextIfLow": "",
            "NextIfHigh": "",
            "NextDefault": "",
            "EndFlag": "",
            "Axis1": "L",
            "CW": 1.0,
            "Pts_G": 0.1, "Pts_E": 0, "Pts_T": 0.3, "Pts_L": 0.4, "Pts_H": 0.1, "Pts_V": 0.1, "Pts_R": 0, "Pts_F": 0, "Pts_W": 0,
        },
    ]

    return fraud_questions + privileged_questions + regulatory_questions

def generate_answer_options(q_id, question_text):
    """Generate maturity-based answer options for new questions."""
    answers = []

    # Base answer templates by maturity level
    templates = [
        {
            "Option #": 0,
            "BaseScore": 0,
            "Answer Option Text": "No capability - No controls, procedures, or resources in place",
        },
        {
            "Option #": 1,
            "BaseScore": 1,
            "Answer Option Text": "Ad hoc approach - Informal procedures without documentation or standardization",
        },
        {
            "Option #": 2,
            "BaseScore": 2,
            "Answer Option Text": "Developing capability - Documented procedures with some standardization; gaps in implementation",
        },
        {
            "Option #": 3,
            "BaseScore": 3,
            "Answer Option Text": "Established program - Documented and standardized procedures consistently applied; dedicated resources; governance oversight; meets minimum regulatory requirements",
        },
        {
            "Option #": 4,
            "BaseScore": 4,
            "Answer Option Text": "Mature program - Continuous improvement culture; advanced capabilities; industry benchmarking; exceeds regulatory requirements; independent assurance",
        },
    ]

    for tmpl in templates:
        answers.append({
            "A-ID": f"{q_id}-A{tmpl['Option #']}",
            "Q-ID": q_id,
            "Option #": tmpl["Option #"],
            "BaseScore": tmpl["BaseScore"],
            "Answer Option Text": tmpl["Answer Option Text"],
            "Tags": "",
            "FractureType": "",
            "FollowUpTrigger": "",
            "NegativeControl": "",
            "Evidence Hint": "",
        })

    return answers

def main():
    print("=" * 80)
    print("PHASE 2 QUESTION BANK ENHANCEMENT")
    print("=" * 80)
    print()

    # Read current enhanced version
    input_file = "IRMMF_QuestionBank_v7_Enhanced_20260116.xlsx"
    q_df = pd.read_excel(input_file, sheet_name="Questions")
    a_df = pd.read_excel(input_file, sheet_name="AnswerOptions")
    intake_q_df = pd.read_excel(input_file, sheet_name="Intake_Questions")
    intake_lists_df = pd.read_excel(input_file, sheet_name="Intake_Lists")

    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"BACKUP_{timestamp}_{input_file}"
    shutil.copy(input_file, backup_file)
    print(f"✓ Created backup: {backup_file}")
    print()

    # Phase 2.1: Enhance remaining question texts
    print("Phase 2.1: Enhancing remaining question texts...")
    print("-" * 80)
    enhanced_count = 0
    for i in range(len(q_df)):
        original_text = str(q_df.at[i, "Question Text"])
        enhanced_text = enhance_question_text(original_text)

        if enhanced_text != original_text:
            q_df.at[i, "Question Text"] = enhanced_text
            enhanced_count += 1

    print(f"✓ Enhanced {enhanced_count} additional questions")
    print()

    # Phase 2.2: Add regulatory references to guidance
    print("Phase 2.2: Adding regulatory references to guidance...")
    print("-" * 80)
    guidance_count = 0
    for i in range(len(q_df)):
        original_guidance = q_df.at[i, "Guidance"]
        question_text = str(q_df.at[i, "Question Text"])
        domain = str(q_df.at[i, "IRMMF Domain"])

        enhanced_guidance = add_regulatory_guidance(original_guidance, domain, question_text)

        if str(enhanced_guidance) != str(original_guidance):
            q_df.at[i, "Guidance"] = enhanced_guidance
            guidance_count += 1

    print(f"✓ Enhanced guidance for {guidance_count} questions with regulatory references")
    print()

    # Phase 2.3: Add new fraud investigation and compliance questions
    print("Phase 2.3: Adding new fraud investigation and compliance questions...")
    print("-" * 80)
    new_questions = create_new_fraud_questions()
    new_q_df = pd.DataFrame(new_questions)
    print(f"✓ Created {len(new_questions)} new questions:")
    for nq in new_questions:
        print(f"  - {nq['Q-ID']}: {nq['Question Title']}")
    print()

    # Append new questions
    q_df = pd.concat([q_df, new_q_df], ignore_index=True)

    # Generate answers for new questions
    print("Phase 2.4: Generating answer options for new questions...")
    print("-" * 80)
    new_answers = []
    for nq in new_questions:
        answers = generate_answer_options(nq["Q-ID"], nq["Question Text"])
        new_answers.extend(answers)

    new_a_df = pd.DataFrame(new_answers)
    a_df = pd.concat([a_df, new_a_df], ignore_index=True)
    print(f"✓ Generated {len(new_answers)} answer options")
    print()

    # Save enhanced version
    output_file = f"IRMMF_QuestionBank_v8_Phase2_Enhanced_{datetime.now().strftime('%Y%m%d')}.xlsx"
    print(f"Saving enhanced question bank to: {output_file}")
    print("-" * 80)

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        q_df.to_excel(writer, sheet_name="Questions", index=False)
        a_df.to_excel(writer, sheet_name="AnswerOptions", index=False)
        intake_q_df.to_excel(writer, sheet_name="Intake_Questions", index=False)
        intake_lists_df.to_excel(writer, sheet_name="Intake_Lists", index=False)

    print(f"✓ Saved: {output_file}")
    print()

    # Summary statistics
    print("=" * 80)
    print("PHASE 2 ENHANCEMENT SUMMARY")
    print("=" * 80)
    print(f"Total Questions:              {len(q_df)} (was {len(q_df) - len(new_questions)})")
    print(f"New Questions Added:          {len(new_questions)}")
    print(f"Questions Text Enhanced:      {enhanced_count}")
    print(f"Guidance Enhanced:            {guidance_count}")
    print(f"Total Answer Options:         {len(a_df)}")
    print(f"New Answer Options:           {len(new_answers)}")
    print()
    print("New Question Breakdown:")
    print(f"  - Fraud Investigation (ACFE, Chain of Custody, Whistleblower): 6")
    print(f"  - Privileged User / Executive Oversight: 4")
    print(f"  - Regulatory Compliance (NIS2, DORA, GDPR): 3")
    print()
    print(f"✅ Phase 2 Enhancement Complete!")
    print(f"📄 Output: {output_file}")

if __name__ == "__main__":
    main()
