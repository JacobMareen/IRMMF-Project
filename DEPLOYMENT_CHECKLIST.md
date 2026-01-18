# IRMMF v10 Streamlined Intake - Deployment Checklist

## 📋 Pre-Deployment Verification

### ✅ Question Bank Ready
- [x] **File:** `IRMMF_QuestionBank_v10_StreamlinedIntake_20260117.xlsx`
- [x] **Assessment Questions:** 411 (unchanged from v9)
- [x] **Multi-Select:** 11 questions
- [x] **Answers:** 1,942 options
- [x] **Professional Language:** 100%
- [x] **Intake Questions:** 25 (down from 57, 56% reduction)
- [x] **Open Text Fields:** 0 (100% eliminated)

### ✅ Code Changes Complete
- [x] **Frontend:** Multi-select UI implemented ([AssessmentFlow.tsx](frontend/src/pages/AssessmentFlow.tsx))
- [x] **Frontend:** CSS styling added ([AssessmentFlow.css](frontend/src/pages/AssessmentFlow.css))
- [x] **Backend:** Schema updated ([app/schemas.py](app/schemas.py))
- [x] **Backend:** State management updated ([app/modules/assessment/state.py](app/modules/assessment/state.py))
- [x] **Ingest:** Default file updated ([ingest_excel.py](ingest_excel.py))

### ✅ Testing Complete
- [x] **Automated Tests:** All passing (4/4)
- [x] **Frontend Build:** No TypeScript errors
- [x] **Backend Syntax:** No Python errors
- [x] **Database Ingestion:** Successful (411 questions loaded)

---

## 🚀 Deployment Steps

### Step 1: Backup Current Database (CRITICAL)
```bash
# Export current assessment data
pg_dump -h localhost -U postgres -d irmmf_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Or use the app's export functionality
# Navigate to /admin and export all assessments
```

**⚠️ IMPORTANT:** Do not skip this step. Truncating will erase all existing questions/answers.

---

### Step 2: Ingest New Question Bank
```bash
cd /Users/jacobmareen/Documents/IRMMF\ Project
source venv/bin/activate
TRUNCATE_BANK=1 python ingest_excel.py
```

**Expected Output:**
```
📄 Using Excel file: IRMMF_QuestionBank_v10_StreamlinedIntake_20260117.xlsx
✅ Found 'Question Title' column in Questions sheet.
🆕 Created new bank: bank-20260117-XXXXXX
➡️ Ingesting Questions...
✅ Questions ingested: 411
➡️ Ingesting Answers...
✅ Answers ingested: 1942
➡️ Ingesting Intake Questions...
✅ Intake Questions ingested: 25
➡️ Ingesting Intake Lists...
✅ Intake List values ingested: 152
🎉 Import complete.
```

**Verify:**
- Questions: 411
- Answers: 1,942
- Intake Questions: 25 (down from 57)
- Intake List Values: 152 (up from 103)
- No errors in output

---

### Step 3: Rebuild Frontend
```bash
cd frontend
npm install  # Only if dependencies changed
npm run build
```

**Expected Output:**
```
✓ built in XXXms
dist/index.html
dist/assets/index-XXXX.css
dist/assets/index-XXXX.js
```

**Verify:**
- No TypeScript errors
- Build completes successfully
- `dist/` folder contains compiled assets

---

### Step 4: Restart Backend
```bash
# Stop current backend process (Ctrl+C or kill PID)

# Restart
cd /Users/jacobmareen/Documents/IRMMF\ Project
source venv/bin/activate
python main.py
```

**Expected Output:**
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Verify:**
- Server starts without errors
- Navigate to http://127.0.0.1:8000/docs (API documentation should load)

---

### Step 5: Verification Tests

#### Test 1: Multi-Select Question Detection
```bash
cd /Users/jacobmareen/Documents/IRMMF\ Project
source venv/bin/activate
python test_multiselect.py
```

**Expected:** All 4 tests pass ✅

#### Test 2: Frontend Navigation
1. Open browser: http://127.0.0.1:8000
2. Click "New Assessment"
3. Complete intake form
4. Click "Start Assessment"
5. Navigate to first multi-select question

**Expected:**
- Questions load without errors
- Multi-select questions show:
  - ✅ Blue "Select all that apply" banner
  - ✅ Checkboxes (not radio buttons)
  - ✅ "Confirm Selection" button
- Single-select questions show:
  - ✅ Regular answer buttons
  - ✅ No "Confirm Selection" button

#### Test 3: Multi-Select Functionality
1. Navigate to `FRAUD-DETECT-01` or any multi-select question
2. Click checkboxes to select multiple options
3. **Verify:** Selected options get gold background
4. **Verify:** "Confirm Selection" button is enabled
5. Click "Confirm Selection"
6. **Verify:** Auto-advance to next question (if enabled)
7. Navigate back to the multi-select question
8. **Verify:** Previous selections are restored correctly

#### Test 4: Defer and Flag
1. Select multiple options on a multi-select question
2. Click "Defer / Skip" button
3. **Verify:** Question marked as deferred
4. Return to question later
5. **Verify:** Selections preserved
6. Confirm selection
7. Click star icon to flag question
8. **Verify:** Question marked for review

#### Test 5: Complete Assessment Flow
1. Start new assessment
2. Answer mix of single and multi-select questions
3. Defer some questions
4. Flag some questions
5. Click "View Results"
6. **Verify:** Results page loads
7. **Verify:** Axis scores calculated correctly
8. **Verify:** Recommendations generated

---

## 🔍 Post-Deployment Validation

### Database Checks
```sql
-- Verify question count
SELECT COUNT(*) FROM dim_questions;  -- Should be 411

-- Verify multi-select questions
SELECT q_id, question_title
FROM dim_questions q
WHERE EXISTS (
  SELECT 1 FROM dim_answers a
  WHERE a.q_id = q.q_id AND a.tags = 'multiselect'
);  -- Should return 11 questions

-- Verify answer count
SELECT COUNT(*) FROM dim_answers;  -- Should be 1,942

-- Verify intake questions
SELECT COUNT(*) FROM dim_intake_questions;  -- Should be 57
```

### API Endpoint Checks
```bash
# Get all questions
curl http://127.0.0.1:8000/api/v1/questions/all | jq '. | length'
# Expected: 411

# Create test assessment
curl -X POST http://127.0.0.1:8000/api/v1/assessment/new \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user"}' | jq .
# Expected: {"assessment_id":"..."}

# Resume assessment
curl http://127.0.0.1:8000/api/v1/assessment/{assessment_id}/resume | jq .
# Expected: Full resumption state with responses, reachable_path, etc.
```

### Frontend Checks
1. **Home Page:** Loads without console errors
2. **New Assessment:** Creates assessment successfully
3. **Intake Form:** All fields present and functional
4. **Assessment Flow:**
   - Questions load
   - Sidebar navigation works
   - Progress tracking accurate
   - Multi-select questions render correctly
5. **Results Page:**
   - Axis scores display
   - Spider chart renders
   - Recommendations load
6. **Recommendations Page:**
   - Accessible from navigation
   - Recommendations list displays
   - Filtering works

---

## 🐛 Troubleshooting

### Issue: Questions Not Loading
**Symptoms:** "Assessment data unavailable" error
**Check:**
```bash
# Verify database has data
psql -d irmmf_db -c "SELECT COUNT(*) FROM dim_questions;"

# Check backend logs for errors
# Look for SQL errors or missing columns
```
**Fix:** Re-run ingestion with `TRUNCATE_BANK=1`

---

### Issue: Multi-Select Not Working
**Symptoms:** Checkboxes don't appear, shows regular buttons instead
**Check:**
```bash
# Verify frontend build is current
ls -lh frontend/dist/

# Check browser console for JavaScript errors
# Open DevTools → Console
```
**Fix:**
```bash
cd frontend
npm run build
# Restart backend to serve new build
```

---

### Issue: Selections Not Saving
**Symptoms:** Multi-select selections disappear when navigating
**Check:**
- Browser console for API errors
- Backend logs for submission errors
- Network tab in DevTools for failed requests

**Fix:**
```bash
# Check backend is running latest code
git status  # Should show no uncommitted changes

# Restart backend
python main.py
```

---

### Issue: Score Calculation Wrong
**Symptoms:** Multi-select scores don't match expected maturity levels
**Check:**
```python
# Verify score calculation logic
# frontend/src/pages/AssessmentFlow.tsx lines 257-264
# 0 selections = 0, 1-2 = 1, 3-4 = 2, 5-6 = 3, 7+ = 4
```

**Fix:** Verify frontend and backend logic match

---

## 📊 Monitoring

### Metrics to Track
- **Assessment Completion Rate:** % of assessments reaching "View Results"
- **Multi-Select Usage:** % of multi-select questions answered
- **Average Time per Question:** Compare single vs multi-select
- **Defer Rate:** % of questions deferred (should be <20%)
- **Error Rate:** API errors during submission (should be <1%)

### Logs to Monitor
```bash
# Backend errors
tail -f /path/to/backend/logs

# Frontend errors (browser console)
# Check for:
# - "Submit failed" errors
# - "Assessment data unavailable" errors
# - TypeScript type errors
```

---

## 🎯 Success Criteria

### ✅ Deployment Successful If:
- [ ] 411 questions loaded into database
- [ ] All 11 multi-select questions detected correctly
- [ ] Frontend builds without errors
- [ ] Backend starts without errors
- [ ] Test assessment completes successfully
- [ ] Multi-select checkboxes render correctly
- [ ] Selections save and restore correctly
- [ ] Results page displays axis scores
- [ ] Recommendations generate correctly
- [ ] No console errors in browser
- [ ] No 500 errors from API

### ⚠️ Rollback If:
- Assessment flow broken (questions won't load)
- Multi-select not functioning (checkboxes missing)
- Scores calculating incorrectly
- Critical errors in browser console
- API returning 500 errors on submission

**Rollback Procedure:**
```bash
# 1. Restore database from backup
psql -d irmmf_db < backup_YYYYMMDD_HHMMSS.sql

# 2. Revert code changes
git checkout HEAD -- frontend/src/pages/AssessmentFlow.tsx
git checkout HEAD -- app/modules/assessment/state.py
git checkout HEAD -- app/schemas.py

# 3. Rebuild frontend
cd frontend && npm run build

# 4. Restart backend
python main.py
```

---

## 📝 Post-Deployment Notes

### Document Changes
- [ ] Update internal documentation with multi-select usage
- [ ] Notify users of new multi-select question format
- [ ] Update training materials if needed
- [ ] Add release notes to changelog

### User Communication
**Email Template:**
```
Subject: IRMMF Assessment Update - Streamlined Intake & Multi-Select Questions

We've enhanced the IRMMF assessment with the following improvements:

1. Streamlined Intake: 25 questions (down from 57) - 56% faster completion
2. All Multiple Choice: No text fields - cleaner, faster, more consistent data
3. More Efficient Assessment: 411 questions (down from 423)
4. Multi-Select Questions: 11 questions allow selecting multiple applicable options
5. Professional Language: All questions use assessment-appropriate phrasing

What's New:
- Intake form now takes ~5-8 minutes (down from 15-20 minutes)
- All intake questions use dropdown selections - no typing required
- Assessment questions show checkboxes for multi-select options
- Click "Confirm Selection" after choosing all applicable options
- Better benchmarking through standardized intake data
- Your previous assessments are preserved and unaffected

Questions? Contact [support contact]
```

---

## 📞 Support Contacts

- **Technical Issues:** [Your contact]
- **Question Bank Questions:** [Your contact]
- **User Training:** [Your contact]

---

## ✅ Checklist Complete

**Date Deployed:** ____________________
**Deployed By:** ____________________
**Version:** v10 Streamlined Intake
**Database Version:** ____________________
**Frontend Build:** ____________________
**Backend Commit:** ____________________

**Sign-off:**
- [ ] Technical Lead
- [ ] Product Owner
- [ ] QA Verification Complete
- [ ] User Documentation Updated
- [ ] Backup Verified
- [ ] Monitoring Configured

---

**🎉 Deployment Complete! The enhanced IRMMF assessment is now live.**
