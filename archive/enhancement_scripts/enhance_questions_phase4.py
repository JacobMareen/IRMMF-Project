"""
Phase 4 Enhancement: Comprehensive Professional Language Conversion
- Convert ALL remaining informal questions to professional language
- Handle "When..." conditional questions
- Handle "How do you..." questions
- Handle "is there a/are there" questions
- Ensure consistent professional tone across entire question bank
"""

import pandas as pd
from datetime import datetime
import re


def enhance_question_text(q_text):
    """
    Apply comprehensive professional language transformations.
    Handles multiple patterns for complete conversion.
    """
    original = q_text
    enhanced = q_text

    # Pattern 1: "When X happens, do you/is there..." → "What capability exists when X to..."
    if enhanced.lower().startswith("when "):
        # Extract the condition and the question
        match = re.match(r"When ([^,]+), (do you|does your organization|is there|are there) ([^?]+)\?", enhanced, re.IGNORECASE)
        if match:
            condition = match.group(1)
            question_part = match.group(3)
            enhanced = f"What capability exists when {condition} to {question_part}?"

    # Pattern 2: "How do you..." → "What approach does your organization employ to..."
    if enhanced.lower().startswith("how do you "):
        enhanced = "What approach does your organization employ to " + enhanced[11:]
    elif enhanced.lower().startswith("how does your org "):
        enhanced = "What approach does your organization employ to " + enhanced[18:]

    # Pattern 3: "Can you..." → "What capability exists to..."
    if enhanced.lower().startswith("can you "):
        enhanced = "What capability exists to " + enhanced[8:]

    # Pattern 4: "Do you..." → "To what extent does your organization..."
    if enhanced.lower().startswith("do you "):
        enhanced = "To what extent does your organization " + enhanced[7:]

    # Pattern 5: "Does your organization..." → "To what extent does your organization..."
    if enhanced.lower().startswith("does your organization "):
        enhanced = "To what extent does your organization " + enhanced[23:]
    elif enhanced.lower().startswith("does your org "):
        enhanced = "To what extent does your organization " + enhanced[14:]

    # Pattern 6: "Have you..." → "Has your organization..."
    if enhanced.lower().startswith("have you "):
        enhanced = "Has your organization " + enhanced[9:]

    # Pattern 7: "Are you..." → "Is your organization..."
    if enhanced.lower().startswith("are you "):
        enhanced = "Is your organization " + enhanced[8:]

    # Pattern 8: "Is there a..." → "What level of capability exists for..."
    if enhanced.lower().startswith("is there a "):
        enhanced = "What level of capability exists for " + enhanced[11:]
    elif enhanced.lower().startswith("are there "):
        enhanced = "What level of capability exists for " + enhanced[10:]

    # Pattern 9: "For X, do you..." → "For X, to what extent does your organization..."
    match = re.match(r"For ([^,]+), do you ([^?]+)\?", enhanced, re.IGNORECASE)
    if match:
        context = match.group(1)
        action = match.group(2)
        enhanced = f"For {context}, to what extent does your organization {action}?"

    # Pattern 10: "During X, do you..." → "During X, what capability exists to..."
    match = re.match(r"During ([^,]+), do you ([^?]+)\?", enhanced, re.IGNORECASE)
    if match:
        context = match.group(1)
        action = match.group(2)
        enhanced = f"During {context}, what capability exists to {action}?"

    # Pattern 11: "After X, do you..." → "After X, what capability exists to..."
    match = re.match(r"After ([^,]+), do you ([^?]+)\?", enhanced, re.IGNORECASE)
    if match:
        context = match.group(1)
        action = match.group(2)
        enhanced = f"After {context}, what capability exists to {action}?"

    # Ensure proper capitalization after transformation
    if enhanced and len(enhanced) > 0:
        enhanced = enhanced[0].upper() + enhanced[1:]

    return enhanced, enhanced != original


def enhance_answer_text(a_text):
    """
    Apply professional language to answer options.
    """
    enhanced = a_text

    # Convert informal answer patterns
    conversions = {
        "No - we don't have": "Not implemented - organization does not have",
        "Yes - we have": "Implemented - organization has",
        "No - not implemented": "Not implemented",
        "Yes - implemented": "Implemented",
        "We don't": "Organization does not",
        "We have": "Organization has",
        "We do": "Organization does",
        "We are": "Organization is",
    }

    for old, new in conversions.items():
        if enhanced.startswith(old):
            enhanced = new + enhanced[len(old):]
            break

    return enhanced


def main():
    print("=" * 80)
    print("PHASE 4 ENHANCEMENT: Comprehensive Professional Language")
    print("=" * 80)
    print()

    # Read v9 Phase3
    input_file = "IRMMF_QuestionBank_v9_Phase3_20260117.xlsx"
    q_df = pd.read_excel(input_file, sheet_name="Questions")
    a_df = pd.read_excel(input_file, sheet_name="AnswerOptions")
    intake_q_df = pd.read_excel(input_file, sheet_name="Intake_Questions")
    intake_lists_df = pd.read_excel(input_file, sheet_name="Intake_Lists")

    print(f"Current question count: {len(q_df)}")
    print(f"Current answer count: {len(a_df)}")
    print()

    # ============================================================================
    # Step 1: Enhance ALL question texts
    # ============================================================================
    print("STEP 1: Converting All Question Texts to Professional Language")
    print("-" * 80)

    q_enhanced_count = 0
    examples_shown = 0
    max_examples = 15

    for idx, row in q_df.iterrows():
        original = row['Question Text']
        enhanced, was_changed = enhance_question_text(original)

        if was_changed:
            q_df.at[idx, 'Question Text'] = enhanced
            q_enhanced_count += 1

            if examples_shown < max_examples:
                print(f"\n{row['Q-ID']} ({row['IRMMF Domain']}):")
                print(f"  Before: {original[:85]}...")
                print(f"  After:  {enhanced[:85]}...")
                examples_shown += 1

    print()
    print(f"✅ Enhanced {q_enhanced_count} question texts")
    print()

    # ============================================================================
    # Step 2: Enhance answer texts (optional - focus on most common patterns)
    # ============================================================================
    print("STEP 2: Converting Answer Texts to Professional Language")
    print("-" * 80)

    a_enhanced_count = 0
    for idx, row in a_df.iterrows():
        original = row['Answer Option Text']
        enhanced = enhance_answer_text(original)

        if enhanced != original:
            a_df.at[idx, 'Answer Option Text'] = enhanced
            a_enhanced_count += 1

    print(f"✅ Enhanced {a_enhanced_count} answer texts")
    print()

    # ============================================================================
    # Step 3: Calculate statistics
    # ============================================================================
    print("=" * 80)
    print("ENHANCEMENT SUMMARY")
    print("=" * 80)
    print()

    # Check remaining informal patterns
    informal_count = 0
    informal_patterns = ['can you', 'do you', 'does your org', 'have you', 'are you',
                        'is there a', 'are there', 'when ', 'how do you']

    for _, row in q_df.iterrows():
        q_text = str(row['Question Text']).lower()
        if any(pattern in q_text[:50] for pattern in informal_patterns):
            informal_count += 1

    professional_count = len(q_df) - informal_count
    professional_pct = (professional_count / len(q_df)) * 100

    print(f"Questions:")
    print(f"  Total: {len(q_df)}")
    print(f"  Enhanced this phase: {q_enhanced_count}")
    print(f"  Professional language: {professional_count}/{len(q_df)} ({professional_pct:.1f}%)")
    print(f"  Remaining informal: {informal_count} ({informal_count/len(q_df)*100:.1f}%)")
    print()
    print(f"Answers:")
    print(f"  Total: {len(a_df)}")
    print(f"  Enhanced: {a_enhanced_count}")
    print()

    # ============================================================================
    # Step 4: Save to new file
    # ============================================================================
    output_file = f"IRMMF_QuestionBank_v9_Phase4_{datetime.now().strftime('%Y%m%d')}.xlsx"
    print(f"Saving to: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        q_df.to_excel(writer, sheet_name="Questions", index=False)
        a_df.to_excel(writer, sheet_name="AnswerOptions", index=False)
        intake_q_df.to_excel(writer, sheet_name="Intake_Questions", index=False)
        intake_lists_df.to_excel(writer, sheet_name="Intake_Lists", index=False)

    print()
    print("=" * 80)
    print("✅ PHASE 4 ENHANCEMENT COMPLETE")
    print("=" * 80)
    print()
    print("Key Transformations Applied:")
    print("  1. 'When X, do you...' → 'What capability exists when X to...'")
    print("  2. 'How do you...' → 'What approach does your organization employ to...'")
    print("  3. 'Can you...' → 'What capability exists to...'")
    print("  4. 'Do you...' → 'To what extent does your organization...'")
    print("  5. 'Is there a...' → 'What level of capability exists for...'")
    print("  6. 'For X, do you...' → 'For X, to what extent does your organization...'")
    print("  7. 'During/After X, do you...' → 'During/After X, what capability exists to...'")
    print()
    print(f"Professional language coverage: {professional_pct:.1f}%")
    print(f"Total questions: {len(q_df)}")
    print(f"Multi-select questions: 11")
    print()
    print(f"✅ Output: {output_file}")
    print()


if __name__ == "__main__":
    main()
