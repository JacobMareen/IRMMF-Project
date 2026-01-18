"""
Enhance IRMMF Question Bank for Senior Audience
Improves language maturity, specificity, and cross-sector applicability
"""
import pandas as pd
import os
from datetime import datetime

# Enhancement mappings for professional language
QUESTION_ENHANCEMENTS = {
    # Casual to Professional transformations
    "Do you have": "To what extent does your organization maintain",
    "Can you detect": "What level of capability exists to identify and investigate",
    "Do you provide": "To what extent does your organization provide",
    "Are ": "To what extent are ",
    "Do employees": "To what extent do employees",
    "Do managers": "To what extent do managers",
    "Can you operate": "What level of operational resilience exists to maintain",
    "Do you systematically": "To what extent does your organization systematically",
    "Is insider risk": "To what extent is insider risk",
}

# Enhanced answer option templates by maturity level
ANSWER_TEMPLATES = {
    0: {
        "No": "No capability - No controls, procedures, or resources in place",
        "No visibility": "No capability - No detection or monitoring capability; would not identify this activity",
        "No systematic": "No capability - No systematic process; entirely ad hoc or reactive",
        "Not executed": "No capability - Control exists only on paper; not operationalized",
        "No formal": "No capability - No formal program, policy, or designated ownership",
    },
    1: {
        "Limited": "Ad hoc approach - Informal procedures without documentation; inconsistent application; no assigned ownership or metrics",
        "Limited visibility": "Basic capability - Minimal detection via basic logging; manual review only; no real-time alerting",
        "Inconsistent": "Ad hoc approach - Procedures exist informally; execution varies by team; no standardization",
        "Anecdotal": "Ad hoc approach - Feedback collected informally; no systematic measurement",
    },
    2: {
        "Partial": "Developing capability - Documented procedures with some standardization; gaps in coverage or consistency; basic metrics tracked",
        "Partial visibility": "Developing capability - Monitoring covers some scenarios; limited automation; gaps in detection",
        "Some": "Developing capability - Basic program with documented procedures; inconsistent application; limited oversight",
        "Occasional": "Developing capability - Periodic reviews or assessments; limited continuous monitoring",
    },
    3: {
        "Good": "Established program - Documented and standardized procedures consistently applied; dedicated resources; governance oversight; KPIs tracked and reported; meets minimum regulatory requirements",
        "Good visibility": "Established program - Active monitoring with defined detection rules; automated alerting to SOC or risk team; SLA-driven response; covers primary risk scenarios",
        "Yes; documented": "Established program - Formalized procedures with cross-functional governance; regular audits and reporting",
        "Regular": "Established program - Systematic and recurring process with documented results and action tracking",
    },
    4: {
        "Comprehensive": "Mature program - Continuous improvement culture; advanced capabilities and automation; benchmarking and industry alignment; proactive with predictive analytics; exceeds regulatory requirements; independent assurance",
        "Comprehensive visibility": "Mature program - Real-time behavioral analytics across all channels; ML-driven risk scoring; automated response capabilities; continuous tuning; independent validation; meets/exceeds regulatory standards (NIS2, DORA, etc.)",
        "Yes; mature": "Mature program - Advanced program with continuous improvement; integrated with enterprise risk management; strategic partnerships; industry leadership",
        "Continuous": "Mature program - Continuous monitoring and optimization; real-time dashboards; predictive capabilities; independent assurance",
    }
}

def enhance_question_text(text):
    """Transform question text to professional assessment language"""
    enhanced = text

    # Apply professional language transformations
    for old, new in QUESTION_ENHANCEMENTS.items():
        if text.startswith(old):
            enhanced = text.replace(old, new, 1)
            break

    # Ensure ends with question mark
    if not enhanced.endswith('?'):
        enhanced += '?'

    return enhanced

def enhance_answer_option(text, option_num):
    """Enhance answer option with more specific maturity language"""
    # Return original if empty
    if not text or pd.isna(text):
        return text

    text = str(text).strip()

    # Map to appropriate template based on maturity level
    if option_num == 0:
        # Level 0: Non-existent
        for keyword, template in ANSWER_TEMPLATES[0].items():
            if keyword.lower() in text.lower()[:20]:
                return template
        return f"No capability - {text}"

    elif option_num == 1:
        # Level 1: Ad hoc
        for keyword, template in ANSWER_TEMPLATES[1].items():
            if keyword.lower() in text.lower()[:20]:
                # Preserve specific details from original
                return f"Ad hoc approach - {text.replace(keyword, '').strip('; ')}"
        return f"Ad hoc approach - {text}"

    elif option_num == 2:
        # Level 2: Developing
        for keyword, template in ANSWER_TEMPLATES[2].items():
            if keyword.lower() in text.lower()[:20]:
                return f"Developing capability - {text.replace(keyword, '').strip('; ')}"
        return f"Developing capability - {text}"

    elif option_num == 3:
        # Level 3: Established
        if text.lower().startswith(('yes', 'good', 'active', 'regular')):
            details = text.split(';')[0] if ';' in text else text
            return f"Established program - {details}; documented procedures consistently applied; dedicated resources; governance oversight; meets minimum regulatory requirements"
        return f"Established program - {text}; meets minimum regulatory requirements"

    elif option_num == 4:
        # Level 4: Mature
        if text.lower().startswith(('comprehensive', 'yes; mature', 'continuous', 'embedded')):
            details = text.split(';')[0] if ';' in text else text
            return f"Mature program - {details}; continuous improvement; advanced automation; industry benchmarking; exceeds regulatory requirements; independent assurance"
        return f"Mature program - {text}; continuous improvement; industry leadership; independent assurance"

    return text

def enhance_guidance(text):
    """Enhance guidance with regulatory references and sector examples"""
    if not text or pd.isna(text) or str(text).strip() == "":
        return text

    enhanced = str(text).strip()

    # Add regulatory context if missing
    regulatory_keywords = ['NIS2', 'DORA', 'GDPR', 'SOX', 'HIPAA', 'PCI-DSS']
    has_regulatory = any(keyword in enhanced for keyword in regulatory_keywords)

    if not has_regulatory:
        # Add generic regulatory note
        enhanced += "\n\nRegulatory Considerations: Assess alignment with applicable frameworks (NIS2, DORA, SOX 404, GDPR Article 32, sector-specific requirements)."

    return enhanced

def main():
    print("=" * 80)
    print("IRMMF QUESTION BANK ENHANCEMENT")
    print("=" * 80)

    excel_file = "IRMMF_QuestionBank_v6_with_IntakeModule_v2.4_P0P1.xlsx"

    # Read all sheets
    print("\nReading Excel file...")
    q_df = pd.read_excel(excel_file, sheet_name='Questions')
    a_df = pd.read_excel(excel_file, sheet_name='AnswerOptions')
    intake_q_df = pd.read_excel(excel_file, sheet_name='Intake_Questions')
    intake_lists_df = pd.read_excel(excel_file, sheet_name='Intake_Lists')

    print(f"Loaded: {len(q_df)} questions, {len(a_df)} answer options")

    # Create backup
    backup_file = f"BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{excel_file}"
    print(f"\nCreating backup: {backup_file}")
    with pd.ExcelWriter(backup_file, engine='openpyxl') as writer:
        q_df.to_excel(writer, sheet_name='Questions', index=False)
        a_df.to_excel(writer, sheet_name='AnswerOptions', index=False)
        intake_q_df.to_excel(writer, sheet_name='Intake_Questions', index=False)
        intake_lists_df.to_excel(writer, sheet_name='Intake_Lists', index=False)

    # Enhance Questions
    print("\n" + "=" * 80)
    print("ENHANCING QUESTIONS")
    print("=" * 80)

    enhanced_count = 0
    for idx, row in q_df.iterrows():
        original_text = row['Question Text']
        if pd.notna(original_text):
            enhanced_text = enhance_question_text(str(original_text))
            if enhanced_text != original_text:
                q_df.at[idx, 'Question Text'] = enhanced_text
                enhanced_count += 1

                if enhanced_count <= 5:  # Show first 5 examples
                    print(f"\n[{row['Q-ID']}]")
                    print(f"Before: {original_text[:80]}...")
                    print(f"After:  {enhanced_text[:80]}...")

        # Enhance Guidance
        if pd.notna(row['Guidance']):
            enhanced_guidance = enhance_guidance(row['Guidance'])
            q_df.at[idx, 'Guidance'] = enhanced_guidance

    print(f"\n✓ Enhanced {enhanced_count} question texts")

    # Enhance Answer Options
    print("\n" + "=" * 80)
    print("ENHANCING ANSWER OPTIONS")
    print("=" * 80)

    answer_enhanced_count = 0
    for idx, row in a_df.iterrows():
        original_text = row['Answer Option Text']
        option_num = row['Option #']

        if pd.notna(original_text) and pd.notna(option_num):
            try:
                option_num = int(option_num)
                enhanced_text = enhance_answer_option(str(original_text), option_num)

                # Only update if meaningfully different
                if enhanced_text != original_text and len(enhanced_text) > len(original_text):
                    a_df.at[idx, 'Answer Option Text'] = enhanced_text
                    answer_enhanced_count += 1

                    if answer_enhanced_count <= 10:  # Show first 10 examples
                        print(f"\n[{row['Q-ID']}] Option {option_num}")
                        print(f"Before: {original_text}")
                        print(f"After:  {enhanced_text[:100]}...")
            except (ValueError, TypeError):
                pass

    print(f"\n✓ Enhanced {answer_enhanced_count} answer options")

    # Save enhanced version
    output_file = f"IRMMF_QuestionBank_v7_Enhanced_{datetime.now().strftime('%Y%m%d')}.xlsx"
    print(f"\n" + "=" * 80)
    print(f"SAVING ENHANCED VERSION: {output_file}")
    print("=" * 80)

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        q_df.to_excel(writer, sheet_name='Questions', index=False)
        a_df.to_excel(writer, sheet_name='AnswerOptions', index=False)
        intake_q_df.to_excel(writer, sheet_name='Intake_Questions', index=False)
        intake_lists_df.to_excel(writer, sheet_name='Intake_Lists', index=False)

    print(f"\n✅ Enhancement complete!")
    print(f"   Original file: {excel_file}")
    print(f"   Backup file: {backup_file}")
    print(f"   Enhanced file: {output_file}")
    print(f"\n   Questions enhanced: {enhanced_count}")
    print(f"   Answer options enhanced: {answer_enhanced_count}")

    # Show summary
    print("\n" + "=" * 80)
    print("SAMPLE ENHANCED QUESTIONS")
    print("=" * 80)

    # Show before/after for a few questions
    sample_qids = ['ADD-AI-Q02', 'ADD-CR-Q02']
    for qid in sample_qids:
        q_row = q_df[q_df['Q-ID'] == qid]
        if not q_row.empty:
            print(f"\n[{qid}] {q_row.iloc[0]['IRMMF Domain']}")
            print(f"Enhanced Question: {q_row.iloc[0]['Question Text']}")

            answers = a_df[a_df['Q-ID'] == qid].sort_values('Option #')
            print("Enhanced Answer Options:")
            for _, ans in answers.iterrows():
                opt_text = ans['Answer Option Text']
                print(f"  [{int(ans['Option #'])}] {opt_text[:100]}{'...' if len(opt_text) > 100 else ''}")

if __name__ == "__main__":
    main()
