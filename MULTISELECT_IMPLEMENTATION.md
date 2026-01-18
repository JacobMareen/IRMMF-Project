# Multi-Select Question Implementation

## Overview
Full multi-select support has been implemented for both frontend and backend, allowing questions to accept multiple answer selections with maturity-based scoring.

## How It Works

### Question Detection
Multi-select questions are identified by the `tags` field in answer options:
- If any answer option has `tags="multiselect"`, the question is treated as multi-select
- Single-select questions continue to work as before (radio button style)

### Scoring Logic
Multi-select questions use a maturity-based scoring system:
- **0 selections** → Score: 0 (No capabilities)
- **1-2 selections** → Score: 1 (Ad hoc implementation)
- **3-4 selections** → Score: 2 (Developing program)
- **5-6 selections** → Score: 3 (Established program)
- **7+ selections** → Score: 4 (Mature program)

This scoring reflects the comprehensiveness of controls rather than individual option values.

## Frontend Changes

### Files Modified
1. **AssessmentFlow.tsx** (frontend/src/pages/AssessmentFlow.tsx)
2. **AssessmentFlow.css** (frontend/src/pages/AssessmentFlow.css)

### Key Frontend Features

#### UI Rendering
- Multi-select questions show a blue note: "Select all that apply (multiple selections allowed)"
- Options render as checkboxes instead of buttons
- Selected options get a gold-tinted background
- "Confirm Selection" button appears for multi-select questions
- Button is disabled until at least one option is selected

#### State Management
- `responses` state now accepts `string | string[]`
- Single-select: stores single answer ID as string
- Multi-select: stores array of selected answer IDs
- Local state updates immediately for responsive UI
- Submission to backend happens on "Confirm Selection" click

#### Type Definitions
```typescript
type AnswerOption = {
  a_id: string
  answer_text: string
  base_score: number
  tags?: string  // "multiselect" indicates multi-select question
}

type Question = {
  q_id: string
  domain: string
  question_title?: string
  question_text: string
  guidance?: string
  evidence_policy_id?: string | null
  options: AnswerOption[]
  is_multiselect?: boolean
}
```

#### Key Functions
- `isMultiSelectQuestion(q: Question)` - Detects multi-select via tags
- `calculateMultiSelectScore(q, selectedIds)` - Calculates score based on selection count
- `handleAnswer(opt)` - Toggles selections for multi-select, submits immediately for single-select
- `handleMultiSelectConfirm()` - Submits multi-select answers as comma-separated string

## Backend Changes

### Files Modified
1. **app/schemas.py**
2. **app/modules/assessment/state.py**

### Key Backend Features

#### Data Storage
- Multi-select answers are stored as comma-separated a_ids (e.g., "FRAUD-DETECT-01-A1,FRAUD-DETECT-01-A2,FRAUD-DETECT-01-A3")
- Single-select answers remain as single a_id string
- Existing database schema works without migration

#### State Resumption
When loading saved responses via `get_resumption_state()`:
1. Backend checks if question has multi-select options (via tags field)
2. If multi-select AND a_id contains commas, splits into array
3. Returns array for multi-select questions, string for single-select
4. Frontend receives correct format for resuming assessment

#### Schema Updates
```python
class ResumptionState(BaseModel):
    responses: Dict[str, str | List[str]]  # Now supports both formats
    # ... other fields unchanged
```

## Multi-Select Questions in Database

The following 6 multi-select questions are included in v8_Consolidated:

### 1. FRAUD-DETECT-01: Fraud Detection Capabilities
**Domain:** 7. Behavioral Analytics & Detection
**Options:** Behavioral analytics, Transaction monitoring, Data analytics, Periodic audits, Anonymous tips, Manager escalations, Automated alerts
**Replaced:** FRAUD-01

### 2. WHISTLEBLOW-01: Whistleblower Reporting Channels
**Domain:** 4. Legal & Compliance
**Options:** Anonymous hotline, Web portal, Email, In-person reporting, Third-party service, Mobile app
**Replaced:** FRAUD-03, FRAUD-04

### 3. EXEC-MONITOR-01: Executive Monitoring Controls
**Domain:** 6. Technical Controls
**Options:** Email monitoring, Travel tracking, Expense reviews, Gift registry, Trading windows, Third-party relationships
**Replaced:** EXEC-01, EXEC-03

### 4. REGULATORY-01: Regulatory Compliance Frameworks
**Domain:** 4. Legal & Compliance
**Options:** SOX, GDPR, NIS2, DORA, HIPAA, PCI-DSS, FCPA, Whistleblowing Directive
**Replaced:** REG-NIS2-01, REG-DORA-01, REG-GDPR-01

### 5. PRIVILEGED-01: Privileged User Coverage
**Domain:** 2. Threat Model & Operations
**Options:** Executives, Board members, Sys admins, DBAs, Cloud admins, Developers, Security team, M&A team

### 6. INVESTIGATE-01: Investigation Capabilities
**Domain:** 8. Investigation & Response
**Options:** Digital forensics, Interview skills, Chain of custody, Data analytics, Legal coordination, Evidence preservation, Timeline reconstruction

## Testing

### Manual Testing Steps
1. Start assessment flow
2. Navigate to any multi-select question (e.g., FRAUD-DETECT-01)
3. Verify UI shows:
   - Blue "Select all that apply" note
   - Checkboxes instead of buttons
   - "Confirm Selection" button
4. Select multiple options:
   - Verify checkboxes toggle correctly
   - Verify selected options get gold background
   - Verify button enables/disables appropriately
5. Click "Confirm Selection"
   - Verify submission succeeds
   - Verify score calculated correctly based on selection count
   - Verify auto-advance works (if enabled)
6. Navigate away and return:
   - Verify selections are restored correctly
   - Verify checkboxes show previously selected options
7. Test defer/flag functionality:
   - Verify defer preserves multi-select answers
   - Verify flagging works with multi-select questions

### Edge Cases Handled
- **Empty selection:** Confirm button disabled, cannot submit
- **Defer with multi-select:** Converts array to comma-separated string
- **Flag toggle with multi-select:** Recalculates score based on current selections
- **Resume assessment:** Backend converts comma-separated back to array
- **Mixed question types:** Single and multi-select work side-by-side

## CSS Styling

### New CSS Classes
```css
.af-multiselect-note {
  /* Blue note banner */
  color: var(--brand-gold);
  background: rgba(232, 179, 115, 0.1);
  border-left: 3px solid var(--brand-gold);
}

.af-checkbox-option {
  /* Checkbox-style option with flex layout */
  display: flex;
  align-items: center;
  gap: 12px;
}

.af-checkbox-option.selected {
  /* Gold-tinted background for selected */
  background: rgba(232, 179, 115, 0.15);
  border-color: var(--brand-gold);
}

.af-multiselect-actions {
  /* Centers the confirm button */
  display: flex;
  justify-content: center;
}

.af-btn:disabled {
  /* Grayed-out disabled state */
  opacity: 0.5;
  cursor: not-allowed;
}
```

## Benefits

### User Experience
1. **Faster Assessment:** 6 multi-select questions replace 8 individual questions (net -2 questions)
2. **Better Context:** Users see all options together, making informed selections easier
3. **Realistic Scoring:** Maturity score reflects breadth of capabilities
4. **Clear UI:** Visual distinction between single and multi-select questions

### Technical
1. **Backward Compatible:** Single-select questions unchanged
2. **No Migration Required:** Uses existing database schema
3. **Flexible Scoring:** Score calculation centralized and easy to adjust
4. **Audit Trail:** Full selection history preserved in comma-separated format

## Future Enhancements

Potential improvements for future versions:

1. **Individual Option Scoring:** Allow each option to contribute specific points to different axes
2. **Required Minimum Selections:** Set minimum number of selections for certain questions
3. **Conditional Options:** Show/hide options based on intake data or previous answers
4. **Weighted Options:** Give certain options higher maturity weight
5. **Multi-Select Evidence:** Extend evidence attestation to support multi-select questions

## Migration from v7 to v8

No database migration required. Simply:
1. Deploy updated backend code
2. Deploy updated frontend build
3. Ingest v8_Consolidated Excel file: `python ingest_excel.py`

Existing assessments will continue to work. New assessments will support multi-select questions.
