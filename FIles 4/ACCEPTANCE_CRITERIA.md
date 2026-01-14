# ACCEPTANCE CRITERIA - Risk Module Implementation
## IRMMF Assessment Platform
## Belfort Advisory BV - 2026-01-11

---

## DEFINITION OF DONE

This document defines the acceptance criteria for the risk scoring module integration.

**Developer:** You can use this as a checklist before marking the work complete.

**Jacob:** You can use this to validate the implementation meets requirements.

---

## FUNCTIONAL REQUIREMENTS

### FR-1: Risk Calculation Accuracy

**Requirement:** System calculates 10 risk scenarios with correct likelihood and impact

**Test:**
```python
# Given
responses = test_data['test_case_1']['responses']
intake_tags = test_data['test_case_1']['intake_tags']

# When
results = engine.calculate_risks(responses, intake_tags)

# Then
assert len(results) == 10
assert all(1 <= r['likelihood'] <= 5 for r in results)
assert all(1 <= r['impact'] <= 5 for r in results)
assert all(r['risk_level'] in ['RED','AMBER','YELLOW','GREEN'] for r in results)
```

**Status:** ☐ Pass / ☐ Fail

---

### FR-2: Axis Score Consistency

**Requirement:** Risk module uses same axis scores as maturity module

**Test:**
```python
# Calculate using both methods
maturity_axes = calculate_maturity_axes(responses)  # Existing
risk_axes = calculate_axis_scores(responses, questions_df)  # New

# Should match within rounding tolerance
for axis in ['G', 'E', 'T', 'L', 'H', 'V', 'R', 'F', 'W']:
    assert abs(maturity_axes[axis] - risk_axes[axis]) < 0.01
```

**Status:** ☐ Pass / ☐ Fail

---

### FR-3: Impact Rules Evaluation

**Requirement:** Impact correctly determined from intake tags

**Test Cases:**

| Intake Tags | Risk | Expected Impact | Rationale |
|-------------|------|-----------------|-----------|
| Technology, High-IP | IP_Theft | 5 | Matches "High-IP OR Technology" rule |
| Manufacturing | IP_Theft | 4 | Matches "Manufacturing" rule |
| Retail | IP_Theft | 2 | Uses default rule |
| Healthcare, High-PII | Customer_Data_Breach | 5 | Matches "Healthcare OR Financial Services" |
| Enterprise (5000+) | Post_Termination_Access | 5 | Matches "Enterprise (5000+)" rule |
| SME (<250) | Post_Termination_Access | 2 | Uses default rule |

**Status:** ☐ Pass / ☐ Fail

---

### FR-4: Mitigation Curve Application

**Requirement:** Curves transform axis scores correctly

**Test:**
```python
# Threshold curve
assert apply_curve(1.5, 'threshold') == 0.1  # Below threshold
assert apply_curve(2.0, 'threshold') == 0.5  # At threshold
assert apply_curve(3.0, 'threshold') == 0.7  # Above threshold

# Standard curve (S-curve)
s1 = apply_curve(1.0, 'standard')
s2 = apply_curve(2.0, 'standard')
s3 = apply_curve(3.0, 'standard')
assert s1 < s2 < s3  # Monotonically increasing
assert 0.45 <= s2 <= 0.55  # Midpoint around 0.5

# Logarithmic curve
l1 = apply_curve(1.0, 'logarithmic')
l2 = apply_curve(2.0, 'logarithmic')
l4 = apply_curve(4.0, 'logarithmic')
assert l2 - l1 > l4 - l2  # Diminishing returns
```

**Status:** ☐ Pass / ☐ Fail

---

### FR-5: Risk Level Mapping

**Requirement:** Risk scores correctly mapped to levels

**Test Cases:**

| Likelihood | Impact | Risk Score | Expected Level |
|------------|--------|------------|----------------|
| 5 | 5 | 25 | RED |
| 4 | 5 | 20 | RED |
| 3 | 5 | 15 | AMBER |
| 3 | 4 | 12 | AMBER |
| 2 | 5 | 10 | YELLOW |
| 3 | 2 | 6 | YELLOW |
| 2 | 2 | 4 | GREEN |
| 1 | 3 | 3 | GREEN |

**Status:** ☐ Pass / ☐ Fail

---

## DATA VALIDATION REQUIREMENTS

### DV-1: Configuration File Integrity

**Requirement:** Risk scenarios config is valid

**Checks:**
- [ ] All 10 risk scenarios present
- [ ] Axis weights sum to 1.0 (±0.01) for each scenario
- [ ] All curve types are valid ("threshold", "standard", or "logarithmic")
- [ ] All impact rules reference valid intake tags
- [ ] No missing required fields

**Test:**
```python
scenarios = load_risk_scenarios()

for scenario in scenarios:
    # Check weights sum to 1.0
    total = sum(scenario['axes'].values())
    assert 0.99 <= total <= 1.01, f"{scenario['id']}: weights = {total}"
    
    # Check curve types
    for axis, curve in scenario['curves'].items():
        assert curve in ['threshold', 'standard', 'logarithmic']
    
    # Check impact rules exist
    assert len(scenario['impact_rules']) >= 1
```

**Status:** ☐ Pass / ☐ Fail

---

### DV-2: Input Data Validation

**Requirement:** System handles invalid input gracefully

**Test Cases:**

| Invalid Input | Expected Behavior |
|---------------|-------------------|
| responses = {} (empty) | Return all axis_scores = 0, likelihood = 5 |
| responses with invalid Q-ID | Ignore invalid Q-ID, process valid ones |
| intake_tags = [] (empty) | Use default impact for all risks |
| intake_tags with unknown tag | Ignore unknown tag, process valid ones |
| axis_score = 5.0 (out of range) | Clip to 4.0 |
| axis_score = -1.0 (negative) | Clip to 0.0 |

**Status:** ☐ Pass / ☐ Fail

---

## PERFORMANCE REQUIREMENTS

### PF-1: Calculation Speed

**Requirement:** Risk calculation completes in <200ms for full assessment

**Test:**
```python
import time

responses = {all 410 questions}
intake_tags = ['Technology', 'High-IP', ...]

start = time.time()
results = engine.calculate_risks(responses, intake_tags)
elapsed = time.time() - start

assert elapsed < 0.2, f"Took {elapsed:.3f}s (limit: 0.2s)"
```

**Status:** ☐ Pass / ☐ Fail

**Actual Performance:** __________ ms

---

### PF-2: Memory Usage

**Requirement:** No memory leaks, reasonable memory footprint

**Test:**
- Run 100 consecutive risk calculations
- Memory usage should stabilize (not continuously grow)
- Peak memory < 500MB

**Status:** ☐ Pass / ☐ Fail

---

## BUSINESS VALIDATION REQUIREMENTS

### BV-1: Known Client Validation

**Requirement:** Risk positions match consultant judgment for 3 real assessments

**Test:**
Run risk engine on 3 completed client assessments:
1. Noventiq (Technology, Enterprise)
2. EVS (Manufacturing, Mid-Market)
3. Virya Energy (Energy/Utilities, Enterprise)

For each:
- [ ] Top 3 risks make sense for industry/profile
- [ ] Risk levels align with consultant assessment
- [ ] No obviously wrong risk positions
- [ ] Advisory text is actionable

**Consultant Sign-Off:**
- [ ] Assessment 1: ________________ (initials)
- [ ] Assessment 2: ________________ (initials)
- [ ] Assessment 3: ________________ (initials)

**Agreement Rate:** Target >85%

**Status:** ☐ Pass / ☐ Fail

---

### BV-2: Sensitivity Analysis

**Requirement:** Risk positions change appropriately when inputs change

**Test Cases:**

| Change | Expected Impact |
|--------|-----------------|
| Increase V-axis by 1.0 | IP_Theft likelihood decreases by 1-2 |
| Add "Healthcare" tag | Customer_Data_Breach impact increases to 5 |
| Remove "High-IP" tag | IP_Theft impact decreases |
| Increase all axes by 0.5 | All likelihoods decrease |
| Decrease all axes by 0.5 | All likelihoods increase |

**Status:** ☐ Pass / ☐ Fail

---

### BV-3: Explainability

**Requirement:** Consultants can explain any risk position to client

**Test:**
Present consultant with random risk result:
```
Risk: Privileged Account Abuse
Likelihood: 3/5 (Possible)
Impact: 5/5 (Catastrophic)
Risk Level: AMBER
```

Consultant should be able to explain:
- Why likelihood is 3 (which controls are weak?)
- Why impact is 5 (which intake tags drove this?)
- What to do to move to YELLOW or GREEN

**Status:** ☐ Pass / ☐ Fail

---

## INTEGRATION REQUIREMENTS

### INT-1: Backend Integration

**Requirement:** Risk module integrates with existing assessment pipeline

**Checklist:**
- [ ] Risk engine callable from main assessment processor
- [ ] No changes required to existing Questions/AnswerOptions tables
- [ ] No changes to user-facing assessment flow
- [ ] No changes to maturity score calculation
- [ ] Risk results added to assessment output JSON/dict

**Status:** ☐ Pass / ☐ Fail

---

### INT-2: Report Integration

**Requirement:** Risk section added to PDF/Excel reports

**Checklist:**
- [ ] Risk heatmap image generated
- [ ] Risk table included (10 rows, sorted by risk_score)
- [ ] Top 3 risks have detail pages with full advisory
- [ ] Report generation time increase <5 seconds
- [ ] Report layout/branding consistent with existing

**Status:** ☐ Pass / ☐ Fail

---

### INT-3: UI Integration

**Requirement:** Risk heatmap displays in web interface

**Checklist:**
- [ ] Heatmap component renders 5×5 grid
- [ ] 10 risk dots positioned correctly
- [ ] Color coding matches risk level (RED/AMBER/YELLOW/GREEN)
- [ ] Hover shows scenario name + risk score
- [ ] Click shows full risk detail (advisory, gaps)
- [ ] Responsive design (works on mobile/tablet)

**Status:** ☐ Pass / ☐ Fail

---

## DOCUMENTATION REQUIREMENTS

### DOC-1: Code Documentation

**Requirement:** Code is documented for maintainability

**Checklist:**
- [ ] All functions have docstrings (args, returns, examples)
- [ ] Complex logic has inline comments
- [ ] README.md explains how to run/test
- [ ] Configuration format documented
- [ ] API/interface documented

**Status:** ☐ Pass / ☐ Fail

---

### DOC-2: User Documentation

**Requirement:** Consultants know how to interpret risk output

**Checklist:**
- [ ] Risk taxonomy documented (what each risk means)
- [ ] Risk level definitions clear (RED/AMBER/YELLOW/GREEN)
- [ ] Advisory interpretation guide created
- [ ] Training deck prepared
- [ ] FAQ document created

**Status:** ☐ Pass / ☐ Fail

---

## TESTING REQUIREMENTS

### TEST-1: Unit Test Coverage

**Requirement:** >80% code coverage

**Tests Required:**
- [ ] test_load_risk_scenarios()
- [ ] test_calculate_axis_scores()
- [ ] test_apply_mitigation_curve()
- [ ] test_calculate_impact()
- [ ] test_calculate_likelihood()
- [ ] test_determine_risk_level()
- [ ] test_full_risk_calculation()

**Status:** ☐ Pass / ☐ Fail

**Coverage:** __________ %

---

### TEST-2: Integration Tests

**Requirement:** End-to-end tests pass

**Tests Required:**
- [ ] test_with_real_client_data()
- [ ] test_with_test_case_1()
- [ ] test_with_test_case_2()
- [ ] test_with_test_case_3()
- [ ] test_report_generation()
- [ ] test_heatmap_rendering()

**Status:** ☐ Pass / ☐ Fail

---

### TEST-3: Edge Cases

**Requirement:** System handles edge cases gracefully

**Test Cases:**
- [ ] Empty responses (no questions answered)
- [ ] Partial responses (50% questions answered)
- [ ] All answers = 0 (worst case)
- [ ] All answers = 4 (best case)
- [ ] No intake tags
- [ ] Unknown intake tags
- [ ] Malformed config file (should error gracefully)

**Status:** ☐ Pass / ☐ Fail

---

## DEPLOYMENT REQUIREMENTS

### DEP-1: Deployment Checklist

**Requirement:** Smooth deployment to production

**Pre-Deployment:**
- [ ] All tests pass in dev environment
- [ ] All tests pass in staging environment
- [ ] Performance benchmarks met
- [ ] Security review completed (if applicable)
- [ ] Database migrations tested (if applicable)
- [ ] Rollback plan documented

**Deployment:**
- [ ] Code deployed to production
- [ ] Config files deployed
- [ ] Database migrations run (if applicable)
- [ ] Health check passes
- [ ] Smoke tests pass

**Post-Deployment:**
- [ ] Monitor logs for errors (24 hours)
- [ ] Run 3 live assessments to validate
- [ ] Consultant feedback collected
- [ ] Performance metrics validated

**Status:** ☐ Pass / ☐ Fail

---

## SIGN-OFF

### Developer Sign-Off

I certify that:
- All functional requirements are met
- All tests pass
- Code is documented
- Ready for business validation

**Developer:** __________________ **Date:** __________

---

### Business Validation Sign-Off

I certify that:
- Risk positions match consultant judgment (>85% agreement)
- Risk output is explainable to clients
- Consultants are trained on interpretation
- Ready for production deployment

**Jacob Mortier:** __________________ **Date:** __________

---

## OPTIONAL ENHANCEMENTS (Future)

These are NOT required for initial deployment but may be added later:

- [ ] **Amplification Factors:** Add Detection Maturity, Response Capability, Control Drift (from v2 spec)
- [ ] **Trend Analysis:** Compare risk positions over time (quarterly assessments)
- [ ] **Peer Benchmarking:** Show client's risks vs industry average
- [ ] **Scenario Simulation:** "What if we improve axis X to 3.5?"
- [ ] **Risk Prioritization:** Auto-generate roadmap based on risk gaps
- [ ] **Custom Risk Scenarios:** Allow clients to define their own risks
- [ ] **Export to GRC Tools:** Integration with third-party risk systems

---

## FINAL CHECKLIST

Before closing this ticket:

**Technical:**
- [ ] All FR tests pass
- [ ] All DV tests pass
- [ ] All PF tests pass
- [ ] All INT tests pass
- [ ] All TEST requirements met

**Business:**
- [ ] All BV tests pass
- [ ] Consultants trained
- [ ] Documentation complete
- [ ] 3 pilot clients validated

**Deployment:**
- [ ] Deployed to production
- [ ] Monitoring in place
- [ ] No critical bugs in first week

**Sign-Off:**
- [ ] Developer sign-off
- [ ] Business sign-off

---

**DEFINITION OF DONE:** All items above marked as PASS and signed off.
