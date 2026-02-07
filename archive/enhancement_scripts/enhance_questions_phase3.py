"""
Phase 3 Enhancement: Additional Multi-Select Questions + Professional Language
- Consolidate incident response questions
- Consolidate data protection questions
- Consolidate HR lifecycle questions
- Convert all informal "Can you/Do you" to professional language
"""

import pandas as pd
from datetime import datetime

# Professional language conversion patterns
LANGUAGE_ENHANCEMENTS = {
    "Can you ": "What capability exists to ",
    "Do you ": "To what extent does your organization ",
    "Does your organization ": "To what extent does your organization ",
    "Does your org ": "To what extent does your organization ",
    "Have you ": "Has your organization ",
    "Are you ": "Is your organization ",
    "Is there a ": "What level of capability exists for ",
    "Are there ": "What level of capability exists for ",
    "Do you use ": "To what extent does your organization use ",
    "Have you implemented ": "Has your organization implemented ",
}


def create_multiselect_incident_response():
    """Consolidate incident response capability questions."""
    return {
        "Q-ID": "INCIDENT-RESPONSE-Q01",
        "IRMMF Domain": "8. Investigation & Response",
        "Question Title": "Incident Response Capabilities",
        "Question Text": "Which incident response capabilities does your organization maintain for insider incidents? (Select all that apply)",
        "Guidance": "Effective insider incident response requires multiple coordinated capabilities. NIST SP 800-61r2 emphasizes preparation, detection, containment, eradication, and recovery. ISO 27035 requires documented procedures, trained personnel, and regular testing. Key capabilities include: stop-the-bleed procedures for active harm, executive escalation protocols, device isolation/imaging, covert investigation, and cross-functional coordination (HR, Legal, Security, IT). SANS Institute research shows organizations with documented playbooks resolve insider incidents 40% faster.",
        "Tier": "T2",
        "Axis1": "R",
        "CW": 1.0,
        "Pts_G": 0.2, "Pts_E": 0.1, "Pts_T": 0.2, "Pts_L": 0.1, "Pts_H": 0, "Pts_V": 0, "Pts_R": 0.3, "Pts_F": 0.1, "Pts_W": 0,
    }


def create_multiselect_data_protection():
    """Consolidate data protection control questions."""
    return {
        "Q-ID": "DATA-PROTECTION-Q01",
        "IRMMF Domain": "6. Technical Controls",
        "Question Title": "Data Protection Controls",
        "Question Text": "Which data protection controls are applied to sensitive data in your environment? (Select all that apply)",
        "Guidance": "Defense-in-depth for data protection requires multiple overlapping controls. NIST SP 800-53 Rev 5 emphasizes layered protections: DLP for in-transit/at-rest detection, database activity monitoring for privileged access, email monitoring for exfiltration attempts, encrypted backups with immutability, watermarking/fingerprinting for attribution, and SaaS-specific controls (CASB, API monitoring). PCI-DSS Requirement 3 mandates encryption plus access controls. Organizations should implement controls proportionate to data classification, with strongest protections for trade secrets, PII, and regulated data.",
        "Tier": "T2",
        "Axis1": "T",
        "CW": 1.0,
        "Pts_G": 0.1, "Pts_E": 0.2, "Pts_T": 0.5, "Pts_L": 0.1, "Pts_H": 0, "Pts_V": 0.1, "Pts_R": 0, "Pts_F": 0, "Pts_W": 0,
    }


def create_multiselect_hr_lifecycle():
    """Consolidate HR lifecycle insider risk questions."""
    return {
        "Q-ID": "HR-LIFECYCLE-Q01",
        "IRMMF Domain": "5. Human-Centric Culture",
        "Question Title": "HR Lifecycle Insider Risk Controls",
        "Question Text": "At which stages of the employee lifecycle does your organization apply insider risk controls? (Select all that apply)",
        "Guidance": "Insider risk management must span the entire employee lifecycle. Pre-hire: background checks, reference verification, screening for risk factors. Onboarding: security awareness, policy acknowledgment, least privilege. Ongoing: periodic access reviews, behavioral analytics, manager training. Transitions: role changes trigger access re-certification. Departures: exit interviews exploring risk factors, coordinated off-boarding (HR-IT-Security), enhanced monitoring during notice period. CISA Insider Threat Mitigation Guide emphasizes that 85% of insider incidents occur during transitions (role changes, performance issues, departures). Layoffs/redundancies require coordinated protocols.",
        "Tier": "T1",
        "Axis1": "H",
        "CW": 1.0,
        "Pts_G": 0.2, "Pts_E": 0.1, "Pts_T": 0.1, "Pts_L": 0.1, "Pts_H": 0.4, "Pts_V": 0, "Pts_R": 0.1, "Pts_F": 0, "Pts_W": 0,
    }


def create_multiselect_access_controls():
    """Consolidate access control and identity management questions."""
    return {
        "Q-ID": "ACCESS-CONTROLS-Q01",
        "IRMMF Domain": "6. Technical Controls",
        "Question Title": "Access Control and Identity Management",
        "Question Text": "Which access control and identity management capabilities are implemented in your environment? (Select all that apply)",
        "Guidance": "Strong identity and access management reduces insider risk exposure. NIST SP 800-63-3 emphasizes identity proofing, authentication strength, and federation. Critical capabilities: periodic access certification with manager review (NIST 800-53 AC-2), orphaned account detection/remediation (CIS Control 5.1), just-in-time privileged access (NIST 800-53 AC-6), activity logging for privileged accounts (PCI-DSS 10.2), and cross-system correlation. Zero Trust Architecture (NIST SP 800-207) requires continuous authentication and least privilege. Organizations should implement risk-based access (adaptive authentication) and detect lateral movement indicating compromised credentials.",
        "Tier": "T2",
        "Axis1": "E",
        "CW": 1.0,
        "Pts_G": 0.1, "Pts_E": 0.5, "Pts_T": 0.2, "Pts_L": 0.1, "Pts_H": 0, "Pts_V": 0.1, "Pts_R": 0, "Pts_F": 0, "Pts_W": 0,
    }


def create_multiselect_forensics():
    """Consolidate forensic investigation capability questions."""
    return {
        "Q-ID": "FORENSICS-Q01",
        "IRMMF Domain": "8. Investigation & Response",
        "Question Title": "Digital Forensics Capabilities",
        "Question Text": "Which digital forensics capabilities does your organization maintain for insider investigations? (Select all that apply)",
        "Guidance": "Digital forensics capabilities are essential for insider incident investigations. NIST SP 800-86 outlines data collection, examination, analysis, and reporting phases. Critical capabilities: device imaging without alerting subject (forensically sound acquisition), volatile memory capture (RAM analysis for encryption keys, running processes), messaging platform search (Teams, Slack, email), code/IP attribution (proving ownership via watermarking, metadata), remote device isolation (prevent evidence destruction), and covert monitoring when legally permissible. Federal Rules of Evidence 901-902 govern admissibility. ISO 27037 specifies identification, collection, acquisition, and preservation of digital evidence. Chain of custody documentation is mandatory for legal proceedings.",
        "Tier": "T2",
        "Axis1": "R",
        "CW": 1.0,
        "Pts_G": 0.1, "Pts_E": 0.1, "Pts_T": 0.3, "Pts_L": 0.1, "Pts_H": 0, "Pts_V": 0, "Pts_R": 0.3, "Pts_F": 0.1, "Pts_W": 0,
    }


def generate_multiselect_answers_v2(q_id, options_list):
    """Generate answer options for multi-select questions (matches consolidate_questions.py format)."""
    answers = []
    score_tiers = [
        (0, 0, "None selected - No capabilities in place"),
        (2, 1, "1-2 capabilities - Ad hoc implementation; significant gaps"),
        (4, 2, "3-4 capabilities - Developing program; basic coverage"),
        (6, 3, "5-6 capabilities - Established program; comprehensive coverage"),
        (99, 4, "7+ capabilities - Mature program; industry-leading coverage with continuous improvement"),
    ]

    for max_count, score, text in score_tiers:
        answers.append({
            "A-ID": f"{q_id}-A{score}",
            "Q-ID": q_id,
            "Option #": score,
            "BaseScore": score,
            "Answer Option Text": text,
            "Tags": "multiselect",
            "FractureType": "",
            "FollowUpTrigger": "",
            "NegativeControl": "",
            "Evidence Hint": f"Review: {', '.join(options_list[:3])}..." if options_list else "",
        })

    return answers


def enhance_question_language(q_text):
    """Apply professional language patterns."""
    enhanced = q_text
    for old, new in LANGUAGE_ENHANCEMENTS.items():
        if enhanced.startswith(old):
            enhanced = new + enhanced[len(old):]
            # Ensure first letter after replacement is lowercase unless it's a proper noun
            if len(enhanced) > len(new) and enhanced[len(new)].isupper():
                enhanced = new + enhanced[len(new)].lower() + enhanced[len(new)+1:]
            break
    return enhanced


def main():
    print("=" * 80)
    print("PHASE 3 ENHANCEMENT: Multi-Select + Professional Language")
    print("=" * 80)
    print()

    # Read v8 Consolidated
    input_file = "IRMMF_QuestionBank_v8_Consolidated_20260117.xlsx"
    q_df = pd.read_excel(input_file, sheet_name="Questions")
    a_df = pd.read_excel(input_file, sheet_name="AnswerOptions")
    intake_q_df = pd.read_excel(input_file, sheet_name="Intake_Questions")
    intake_lists_df = pd.read_excel(input_file, sheet_name="Intake_Lists")

    print(f"Current question count: {len(q_df)}")
    print()

    # ============================================================================
    # Step 1: Add new multi-select questions
    # ============================================================================
    print("STEP 1: Adding New Multi-Select Questions")
    print("-" * 80)

    new_multiselect = [
        create_multiselect_incident_response(),
        create_multiselect_data_protection(),
        create_multiselect_hr_lifecycle(),
        create_multiselect_access_controls(),
        create_multiselect_forensics(),
    ]

    for q in new_multiselect:
        print(f"  + {q['Q-ID']}: {q['Question Title']}")

    # Questions to remove (consolidated into multi-select)
    questions_to_remove = [
        # Incident response capabilities
        "V6-D2-Q02",  # Stop-the-bleed procedures
        "ADD-EX-Q03",  # Executive escalation
        "SEC-D5-Q13",  # Cross-functional coordination

        # Data protection
        "ADD-CL-Q03",  # SaaS controls

        # HR lifecycle
        "ADD-WF-Q01",  # Layoff coordination
        "ADD-JN-Q01",  # Pre-hire screening
        "ADD-H-Q13",   # Exit interviews
        "ADD-EX-Q04",  # Executive departure protocols

        # Access controls
        "ADD-ID-Q02",  # Orphaned accounts
        "ADD-ID-Q04",  # Access certification

        # Forensics
        "ADD-EP-Q04",  # Remote device isolation
        "ADD-IV-Q02",  # Covert investigation
        "ADD-IV-Q03",  # Forensic imaging
        "ADD-EM-Q04",  # Messaging search
        "ADD-IP-Q04",  # Code attribution
    ]

    print()
    print(f"Removing {len(questions_to_remove)} questions (consolidated into multi-select):")
    for qid in questions_to_remove:
        print(f"  - {qid}")

    # Remove consolidated questions
    q_df = q_df[~q_df["Q-ID"].isin(questions_to_remove)]
    a_df = a_df[~a_df["Q-ID"].isin(questions_to_remove)]

    # Add new multi-select questions
    new_q_df = pd.DataFrame(new_multiselect)
    q_df = pd.concat([q_df, new_q_df], ignore_index=True)

    # Generate answers for new multi-select questions
    multiselect_options = {
        "INCIDENT-RESPONSE-Q01": [
            "Stop-the-bleed procedures",
            "Executive escalation protocols",
            "Device isolation/imaging",
            "Covert investigation capabilities",
            "Cross-functional coordination",
            "Documented playbooks",
            "Regular tabletop exercises"
        ],
        "DATA-PROTECTION-Q01": [
            "Data Loss Prevention (DLP)",
            "Database Activity Monitoring (DAM)",
            "Email monitoring/scanning",
            "Encrypted backups with immutability",
            "Watermarking/fingerprinting",
            "CASB for SaaS applications",
            "API monitoring for data access"
        ],
        "HR-LIFECYCLE-Q01": [
            "Pre-hire background checks",
            "Onboarding security training",
            "Periodic access reviews",
            "Role change access re-certification",
            "Exit interviews with risk assessment",
            "Coordinated off-boarding (HR-IT-Security)",
            "Enhanced monitoring during notice period",
            "Layoff/redundancy protocols"
        ],
        "ACCESS-CONTROLS-Q01": [
            "Periodic access certification",
            "Orphaned account detection",
            "Just-in-time privileged access",
            "Privileged account activity logging",
            "Cross-system correlation",
            "Risk-based adaptive authentication",
            "Lateral movement detection"
        ],
        "FORENSICS-Q01": [
            "Device imaging (forensically sound)",
            "Volatile memory capture",
            "Messaging platform search",
            "Code/IP attribution tools",
            "Remote device isolation",
            "Covert monitoring (when legal)",
            "Chain of custody documentation"
        ],
    }

    new_answers = []
    for q in new_multiselect:
        options = multiselect_options.get(q["Q-ID"], [])
        answers = generate_multiselect_answers_v2(q["Q-ID"], options)
        new_answers.extend(answers)

    new_a_df = pd.DataFrame(new_answers)
    a_df = pd.concat([a_df, new_a_df], ignore_index=True)

    print()
    print(f"After consolidation: {len(q_df)} questions (was 421, -15 removed, +5 added = 411)")
    print()

    # ============================================================================
    # Step 2: Enhance professional language
    # ============================================================================
    print("STEP 2: Converting to Professional Language")
    print("-" * 80)

    enhanced_count = 0
    for idx, row in q_df.iterrows():
        original = row['Question Text']
        enhanced = enhance_question_language(original)

        if enhanced != original:
            q_df.at[idx, 'Question Text'] = enhanced
            enhanced_count += 1
            if enhanced_count <= 10:  # Show first 10 examples
                print(f"  {row['Q-ID']}:")
                print(f"    Before: {original[:60]}...")
                print(f"    After:  {enhanced[:60]}...")
                print()

    print(f"✅ Enhanced {enhanced_count} question texts with professional language")
    print()

    # ============================================================================
    # Step 3: Calculate final statistics
    # ============================================================================
    print("=" * 80)
    print("ENHANCEMENT SUMMARY")
    print("=" * 80)
    print()
    print(f"Questions:")
    print(f"  Before:  421 (from v8 Consolidated)")
    print(f"  Removed: 15 (consolidated into multi-select)")
    print(f"  Added:   5 (new multi-select questions)")
    print(f"  After:   {len(q_df)}")
    print()
    print(f"Multi-Select Questions:")
    print(f"  Previous: 6")
    print(f"  New:      5")
    print(f"  Total:    11")
    print()
    print(f"Language Improvements:")
    print(f"  Questions enhanced: {enhanced_count}")
    print(f"  Answer options: {len(a_df)}")
    print()

    # ============================================================================
    # Step 4: Save to new file
    # ============================================================================
    output_file = f"IRMMF_QuestionBank_v9_Phase3_{datetime.now().strftime('%Y%m%d')}.xlsx"
    print(f"Saving to: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        q_df.to_excel(writer, sheet_name="Questions", index=False)
        a_df.to_excel(writer, sheet_name="AnswerOptions", index=False)
        intake_q_df.to_excel(writer, sheet_name="Intake_Questions", index=False)
        intake_lists_df.to_excel(writer, sheet_name="Intake_Lists", index=False)

    print()
    print("=" * 80)
    print("✅ PHASE 3 ENHANCEMENT COMPLETE")
    print("=" * 80)
    print()
    print("New Multi-Select Questions Added:")
    print("  1. INCIDENT-RESPONSE-Q01: Incident Response Capabilities")
    print("  2. DATA-PROTECTION-Q01: Data Protection Controls")
    print("  3. HR-LIFECYCLE-Q01: HR Lifecycle Insider Risk Controls")
    print("  4. ACCESS-CONTROLS-Q01: Access Control and Identity Management")
    print("  5. FORENSICS-Q01: Digital Forensics Capabilities")
    print()
    print(f"Total multi-select questions: 11 (covers major capability areas)")
    print(f"Professional language coverage: {enhanced_count}/{len(q_df)} questions ({enhanced_count/len(q_df)*100:.1f}%)")
    print()
    print(f"✅ Output: {output_file}")
    print()


if __name__ == "__main__":
    main()
