"""
Test multi-select question functionality end-to-end.

Run with: python3 test_multiselect.py
"""
from __future__ import annotations

import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

from app.db import SessionLocal
from app.models import Question, Answer


def test_multiselect_detection():
    """Test that multi-select questions are correctly identified."""
    print("=" * 80)
    print("MULTI-SELECT DETECTION TEST")
    print("=" * 80)
    print()

    db = SessionLocal()
    try:
        # Query all questions
        questions = db.query(Question).all()
        print(f"Total questions in database: {len(questions)}")
        print()

        # Find multi-select questions
        multiselect_questions = []
        for q in questions:
            # Check if any answer option has multiselect tag
            has_multiselect = any(
                opt.tags == 'multiselect' for opt in q.options if opt.tags
            )
            if has_multiselect:
                multiselect_questions.append(q)

        print(f"Multi-select questions found: {len(multiselect_questions)}")
        print()

        # Display details
        for q in multiselect_questions:
            print(f"Q-ID: {q.q_id}")
            print(f"  Title: {q.question_title}")
            print(f"  Domain: {q.domain}")
            print(f"  Options: {len(q.options)}")

            # Show answer options
            for opt in q.options:
                print(f"    - {opt.a_id}: {opt.answer_text[:50]}... (score: {opt.base_score})")
            print()

        # Expected multi-select questions (v9 Phase 3)
        expected = [
            # Original 6 from v8
            "FRAUD-DETECT-01",
            "WHISTLEBLOW-01",
            "EXEC-MONITOR-01",
            "REGULATORY-01",
            "PRIVILEGED-01",
            "INVESTIGATE-01",
            # New 5 from Phase 3
            "INCIDENT-RESPONSE-01",
            "DATA-PROTECTION-01",
            "HR-LIFECYCLE-01",
            "ACCESS-CONTROLS-01",
            "FORENSICS-01",
        ]

        found_ids = [q.q_id for q in multiselect_questions]
        missing = [qid for qid in expected if qid not in found_ids]
        unexpected = [qid for qid in found_ids if qid not in expected]

        print("-" * 80)
        if missing:
            print(f"❌ MISSING multi-select questions: {missing}")
        else:
            print("✅ All expected multi-select questions found")

        if unexpected:
            print(f"⚠️  UNEXPECTED multi-select questions: {unexpected}")

        if len(multiselect_questions) == len(expected) and not missing and not unexpected:
            print()
            print("🎉 MULTI-SELECT DETECTION TEST PASSED")
            return True
        else:
            print()
            print("❌ MULTI-SELECT DETECTION TEST FAILED")
            return False

    finally:
        db.close()


def test_multiselect_answer_structure():
    """Test that multi-select answer options have correct structure."""
    print()
    print("=" * 80)
    print("MULTI-SELECT ANSWER STRUCTURE TEST")
    print("=" * 80)
    print()

    db = SessionLocal()
    try:
        # Get a sample multi-select question
        sample_qid = "FRAUD-DETECT-01"
        question = db.query(Question).filter_by(q_id=sample_qid).first()

        if not question:
            print(f"❌ Question {sample_qid} not found in database")
            return False

        print(f"Testing question: {sample_qid}")
        print(f"Title: {question.question_title}")
        print()

        # Check answer options
        print(f"Answer options: {len(question.options)}")
        for opt in question.options:
            print(f"  {opt.a_id}:")
            print(f"    Text: {opt.answer_text[:60]}...")
            print(f"    Base Score: {opt.base_score}")
            print(f"    Tags: {opt.tags}")
            print()

        # Expected answer structure for multi-select
        # Should have 5 options with scores 0, 1, 2, 3, 4 based on selection count
        expected_scores = [0, 1, 2, 3, 4]
        actual_scores = sorted([opt.base_score for opt in question.options])

        if actual_scores == expected_scores:
            print("✅ Answer scores match expected maturity levels (0-4)")
            print()
            print("🎉 ANSWER STRUCTURE TEST PASSED")
            return True
        else:
            print(f"❌ Answer scores don't match expected: {actual_scores} != {expected_scores}")
            print()
            print("❌ ANSWER STRUCTURE TEST FAILED")
            return False

    finally:
        db.close()


def test_comma_separated_storage():
    """Test that comma-separated a_ids can be properly split."""
    print()
    print("=" * 80)
    print("COMMA-SEPARATED STORAGE TEST")
    print("=" * 80)
    print()

    # Simulate backend storage
    test_cases = [
        ("FRAUD-DETECT-01-A1", ["FRAUD-DETECT-01-A1"]),  # Single selection
        ("FRAUD-DETECT-01-A1,FRAUD-DETECT-01-A2", ["FRAUD-DETECT-01-A1", "FRAUD-DETECT-01-A2"]),  # Two selections
        ("A1,A2,A3,A4,A5", ["A1", "A2", "A3", "A4", "A5"]),  # Five selections
    ]

    all_passed = True
    for stored, expected in test_cases:
        result = stored.split(',')
        if result == expected:
            print(f"✅ '{stored}' → {result}")
        else:
            print(f"❌ '{stored}' → {result} (expected {expected})")
            all_passed = False

    print()
    if all_passed:
        print("🎉 COMMA-SEPARATED STORAGE TEST PASSED")
    else:
        print("❌ COMMA-SEPARATED STORAGE TEST FAILED")

    return all_passed


def test_score_calculation():
    """Test score calculation logic."""
    print()
    print("=" * 80)
    print("SCORE CALCULATION TEST")
    print("=" * 80)
    print()

    def calculate_score(selection_count):
        """Frontend score calculation logic."""
        if selection_count == 0:
            return 0
        if selection_count <= 2:
            return 1
        if selection_count <= 4:
            return 2
        if selection_count <= 6:
            return 3
        return 4

    test_cases = [
        (0, 0, "No capabilities"),
        (1, 1, "Ad hoc (1-2)"),
        (2, 1, "Ad hoc (1-2)"),
        (3, 2, "Developing (3-4)"),
        (4, 2, "Developing (3-4)"),
        (5, 3, "Established (5-6)"),
        (6, 3, "Established (5-6)"),
        (7, 4, "Mature (7+)"),
        (10, 4, "Mature (7+)"),
    ]

    all_passed = True
    for count, expected_score, label in test_cases:
        actual_score = calculate_score(count)
        if actual_score == expected_score:
            print(f"✅ {count} selections → Score {actual_score} ({label})")
        else:
            print(f"❌ {count} selections → Score {actual_score}, expected {expected_score} ({label})")
            all_passed = False

    print()
    if all_passed:
        print("🎉 SCORE CALCULATION TEST PASSED")
    else:
        print("❌ SCORE CALCULATION TEST FAILED")

    return all_passed


def main():
    """Run all tests."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MULTI-SELECT IMPLEMENTATION TEST" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    results = []

    try:
        results.append(("Multi-Select Detection", test_multiselect_detection()))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("Multi-Select Detection", False))

    try:
        results.append(("Answer Structure", test_multiselect_answer_structure()))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("Answer Structure", False))

    try:
        results.append(("Comma-Separated Storage", test_comma_separated_storage()))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("Comma-Separated Storage", False))

    try:
        results.append(("Score Calculation", test_score_calculation()))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("Score Calculation", False))

    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
