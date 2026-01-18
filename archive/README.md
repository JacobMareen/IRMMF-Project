# Archive - Historical Enhancement Scripts

This folder contains historical scripts used to develop the final question bank. These are kept for reference and documentation purposes but are **not needed for production deployment**.

## Enhancement Scripts (enhancement_scripts/)

### Phase-by-Phase Development

1. **enhance_questions.py** - Initial language enhancements (v7)
   - Enhanced 107 question texts
   - Enhanced 1,801 answer options
   - First professional language pass

2. **enhance_questions_phase2.py** - Fraud/regulatory questions (v8)
   - Added 13 new questions (fraud investigation, executive oversight, regulatory)
   - Professional language patterns
   - Guidance with regulatory references

3. **consolidate_questions.py** - First multi-select consolidation (v8)
   - Created 6 multi-select questions
   - Removed 8 individual questions
   - Net: 421 questions (down from 423)

4. **enhance_questions_phase3.py** - Additional multi-select + language (v9)
   - Added 5 more multi-select questions (total: 11)
   - Removed 15 individual questions
   - Enhanced 48 question texts
   - Net: 411 questions

5. **enhance_questions_phase4.py** - Comprehensive language conversion (v9 final)
   - Enhanced 36 more question texts
   - Comprehensive pattern transformations
   - Final professional language coverage

6. **streamline_intake.py** - Intake question streamlining (v10)
   - Reduced intake from 57 to 25 questions (56% reduction)
   - Eliminated ALL open text fields
   - Converted all to multiple choice with dropdown lists
   - Business-friendly language throughout
   - Net: 25 intake questions (down from 57)

### Final Result
**IRMMF_QuestionBank_v10_StreamlinedIntake_20260117.xlsx**
- 411 assessment questions (unchanged from v9)
- 11 multi-select questions
- 1,942 answer options
- 100% professional language
- 25 streamlined intake questions (down from 57)

## Old Documentation

**Question_Bank_Enhancement_Recommendations.md**
- 55-page analysis document from initial review
- Identified language issues and suggested improvements
- Historical reference for enhancement rationale

## Usage

These scripts are **read-only reference material**. Do not run them as they:
- Expect specific input files that no longer exist
- Would create duplicate/outdated versions
- Are superseded by the final v9 Phase 4 question bank

## Production Files

For production deployment, use:
- **Question Bank:** `IRMMF_QuestionBank_v10_StreamlinedIntake_20260117.xlsx`
- **Ingest Script:** `ingest_excel.py` (already configured for v10)
- **Documentation:**
  - `MULTISELECT_IMPLEMENTATION.md`
  - `MULTISELECT_USER_GUIDE.md`
  - `PHASE_4_SUMMARY.md`
  - `DEPLOYMENT_CHECKLIST.md`
- **Tests:** `test_multiselect.py`

---

**Archive Created:** January 17, 2026
**Purpose:** Historical reference and documentation
**Status:** Read-only, not for production use
