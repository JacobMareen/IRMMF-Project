# DEVELOPER BRIEF: Risk Scoring Module
## IRMMF Assessment Platform - Risk Module Integration
## Belfort Advisory BV

---

## EXECUTIVE SUMMARY

**What:** Add insider risk scoring to existing IRMMF assessment platform

**Why:** Clients want to see "Which risks am I exposed to?" not just "What's my maturity score?"

**How:** Add 10 risk scenario calculations using existing question/answer data

**Effort:** ~40 hours (1 week)

**Impact:** No changes to existing questions, answers, or user flow

---

## WHAT YOU'RE BUILDING

### Current State (Existing)
```
User completes assessment 
  → System calculates maturity scores (0-4) across 9 axes
  → Output: Spider chart, domain scores, overall maturity
```

### Future State (After This Work)
```
User completes assessment 
  → System calculates maturity scores (existing, unchanged)
  → System calculates risk scores (NEW)
  → Output: Spider chart + Risk heatmap (5×5 grid with 10 risk dots)
```

**User sees no difference in assessment flow.** Risk is additional output.

---

## ARCHITECTURE OVERVIEW

### Existing Data You'll Use

**1. Questions Table** (410 rows)
```
Q-ID          | Pts_G | Pts_E | Pts_T | Pts_L | Pts_H | Pts_V | Pts_R | Pts_F | Pts_W
ADD-AI-Q01    | 0.10  | 0.00  | 0.30  | 0.15  | 0.00  | 0.40  | 0.00  | 0.05  | 0.00
SEC-D2-Q01    | 0.15  | 0.25  | 0.30  | 0.00  | 0.00  | 0.30  | 0.00  | 0.00  | 0.00
...
```
These 9-axis weights already exist. You just read them.

**2. AnswerOptions Table** (1,936 rows)
```
Q-ID          | A-ID           | BaseScore
ADD-AI-Q01    | ADD-AI-Q01-A0  | 0
ADD-AI-Q01    | ADD-AI-Q01-A1  | 1
ADD-AI-Q01    | ADD-AI-Q01-A2  | 2
ADD-AI-Q01    | ADD-AI-Q01-A3  | 3
ADD-AI-Q01    | ADD-AI-Q01-A4  | 4
...
```
BaseScore (0-4 ordinal) already exists. You just read it.

**3. Intake Tags** (list of strings)
```
['Technology', 'High-IP', 'Enterprise (5000+)', 'EU-Primary', 'NIS2-Essential']
```
Generated from intake module. Already exists.

**4. User Responses** (dict)
```json
{
  "ADD-AI-Q01": 3,
  "SEC-D2-Q01": 2,
  "ITIAM-D1-Q01": 4,
  ...
}
```
Maps Q-ID → BaseScore. You already capture this.

---

### New Data You'll Add

**5. Risk Scenarios Configuration** (10 rows)

I'm providing this in 3 formats:
- `risk_scenarios.yaml` - Recommended, easiest to maintain
- `risk_scenarios.csv` - For Excel import
- `risk_scenarios.sql` - For database import

Pick whichever fits your stack.

**Structure:**
```yaml
IP_Theft:
  name: "Intellectual Property Theft"
  axis_weights:
    V: 0.40  # Visibility
    T: 0.30  # Technical
    R: 0.15  # Resilience
    W: 0.15  # Control Lag
    # Other axes: 0.00 (implicit)
  curve_types:
    V: "threshold"
    T: "threshold"
    R: "standard"
    W: "logarithmic"
  impact_rules:
    - condition: "High-IP OR Technology"
      impact: 5
    - condition: "Manufacturing"
      impact: 4
    - condition: "default"
      impact: 2
```

---

## CALCULATION FLOW

### Step 1: Calculate Axis Scores (You Already Do This)

```python
# For each axis (G, E, T, L, H, V, R, F, W):
axis_score = weighted_average(
    all questions answered,
    weighted by Pts_{axis} from Questions table
)

# Example:
# V-axis score = (
#   Q1_answer * Q1_Pts_V + 
#   Q2_answer * Q2_Pts_V + 
#   ...
# ) / sum(all Pts_V weights)

# Result: 
axis_scores = {
  'G': 2.3,
  'E': 2.8,
  'T': 2.1,
  'L': 2.5,
  'H': 2.7,
  'V': 2.9,
  'R': 2.4,
  'F': 2.2,
  'W': 2.6
}
```

**You already have this code.** It's how you calculate domain/subdomain maturity.

---

### Step 2: Apply Mitigation Curves (NEW)

Transform axis score (0-4) to mitigation effectiveness (0-1) using non-linear curves:

```python
def apply_curve(axis_score, curve_type):
    """
    axis_score: 0-4 (from Step 1)
    curve_type: "threshold", "standard", or "logarithmic"
    returns: 0-1 (mitigation effectiveness)
    """
    if curve_type == "threshold":
        # Binary controls (DLP: have it or don't)
        if axis_score < 2.0:
            return 0.1
        else:
            return 0.5 + (axis_score - 2.0) * 0.2
    
    elif curve_type == "logarithmic":
        # Diminishing returns (training, speed)
        return 1 - exp(-0.5 * axis_score)
    
    else:  # "standard"
        # S-curve (most controls)
        return 1 / (1 + exp(-1.5 * (axis_score - 2.0)))

# Example:
V_score = 2.9
V_curve = "threshold"
V_mitigation = apply_curve(2.9, "threshold")
# = 0.5 + (2.9 - 2.0) * 0.2 = 0.68
```

---

### Step 3: Calculate Mitigation Score for Each Risk (NEW)

```python
# For IP_Theft scenario:
scenario = {
    'axis_weights': {'V': 0.40, 'T': 0.30, 'R': 0.15, 'W': 0.15},
    'curve_types': {'V': 'threshold', 'T': 'threshold', 'R': 'standard', 'W': 'logarithmic'}
}

mitigation = 0
for axis, weight in scenario['axis_weights'].items():
    axis_score = axis_scores[axis]  # From Step 1
    curve_type = scenario['curve_types'][axis]
    
    # Transform score
    axis_mitigation = apply_curve(axis_score, curve_type)
    
    # Weight by importance
    mitigation += weight * axis_mitigation

# Example:
# V: 0.40 × 0.68 = 0.272
# T: 0.30 × 0.53 = 0.159
# R: 0.15 × 0.62 = 0.093
# W: 0.15 × 0.71 = 0.107
# Total mitigation = 0.631
```

---

### Step 4: Calculate Likelihood (NEW)

```python
likelihood = max(1, min(5, int(5 - (mitigation * 4))))

# Example:
# mitigation = 0.631
# likelihood = 5 - (0.631 * 4) = 5 - 2.52 = 2.48 → round to 2
```

---

### Step 5: Calculate Impact from Intake Tags (NEW)

```python
def calculate_impact(scenario, intake_tags):
    # Check rules in order
    for rule in scenario['impact_rules']:
        if rule['condition'] == 'default':
            continue  # Apply default last
        
        # Evaluate condition
        if evaluate_condition(rule['condition'], intake_tags):
            return rule['impact']
    
    # No rule matched, use default
    return scenario['default_impact']

def evaluate_condition(condition, tags):
    # Example: "High-IP OR Technology"
    if ' OR ' in condition:
        parts = condition.split(' OR ')
        return any(part.strip() in tags for part in parts)
    elif ' AND ' in condition:
        parts = condition.split(' AND ')
        return all(part.strip() in tags for part in parts)
    else:
        return condition in tags

# Example:
intake_tags = ['Technology', 'High-IP', 'Enterprise (5000+)']
impact_rules = [
    {'condition': 'High-IP OR Technology', 'impact': 5},
    {'condition': 'Manufacturing', 'impact': 4},
    {'condition': 'default', 'impact': 2}
]

impact = calculate_impact(scenario, intake_tags)
# → Matches "High-IP OR Technology" → impact = 5
```

---

### Step 6: Determine Risk Level (NEW)

```python
risk_score = likelihood * impact

if risk_score >= 20:
    risk_level = "RED"
elif risk_score >= 12:
    risk_level = "AMBER"
elif risk_score >= 6:
    risk_level = "YELLOW"
else:
    risk_level = "GREEN"

# Example:
# likelihood = 2
# impact = 5
# risk_score = 2 × 5 = 10
# risk_level = "YELLOW"
```

---

### Step 7: Repeat for All 10 Risks

```python
risk_results = []

for scenario in risk_scenarios:  # 10 scenarios
    # Calculate mitigation (Steps 2-3)
    mitigation = calculate_mitigation(scenario, axis_scores)
    
    # Calculate likelihood (Step 4)
    likelihood = calculate_likelihood(mitigation)
    
    # Calculate impact (Step 5)
    impact = calculate_impact(scenario, intake_tags)
    
    # Determine risk level (Step 6)
    risk_level = determine_risk_level(likelihood, impact)
    
    risk_results.append({
        'scenario': scenario['name'],
        'likelihood': likelihood,
        'impact': impact,
        'risk_score': likelihood * impact,
        'risk_level': risk_level
    })

# Result: 10 risk positions ready for heatmap
```

---

## OUTPUT FORMAT

### JSON Response

```json
{
  "assessment_id": "ASM-2026-001",
  "client_name": "TechCorp",
  "completed_date": "2026-01-15",
  
  "maturity": {
    "overall": 2.8,
    "axes": {
      "G": 2.3,
      "E": 2.8,
      "T": 2.1,
      "L": 2.5,
      "H": 2.7,
      "V": 2.9,
      "R": 2.4,
      "F": 2.2,
      "W": 2.6
    }
  },
  
  "risks": [
    {
      "scenario": "Intellectual Property Theft",
      "category": "Data Loss & Exfiltration",
      "likelihood": 2,
      "likelihood_label": "Unlikely",
      "impact": 5,
      "impact_label": "Catastrophic",
      "risk_score": 10,
      "risk_level": "YELLOW",
      "mitigation_score": 0.631,
      "key_gaps": [
        "Technical controls: 2.1/4",
        "Resilience: 2.4/4"
      ],
      "advisory": "Despite high IP value, you have adequate visibility (2.9/4). Priority: Strengthen technical controls (DLP/CASB) to reach GREEN."
    },
    {
      "scenario": "Privileged Account Abuse",
      "category": "Access & Privilege Abuse",
      "likelihood": 3,
      "likelihood_label": "Possible",
      "impact": 5,
      "impact_label": "Catastrophic",
      "risk_score": 15,
      "risk_level": "AMBER",
      "mitigation_score": 0.512,
      "key_gaps": [
        "Technical (PAM): 2.1/4",
        "Execution (reviews): 2.8/4"
      ],
      "advisory": "CRITICAL: Privileged accounts are inadequately monitored. Technical controls (2.1/4) and review execution (2.8/4) both need improvement. Priority: Deploy PAM with session recording."
    }
    // ... 8 more risks
  ]
}
```

---

## DELIVERABLES

### 1. Backend: Risk Calculation Module

**Language:** Python (or JavaScript if your stack requires)

**Input:** 
- `responses`: dict {Q-ID: BaseScore}
- `intake_tags`: list of strings
- `questions_df`: DataFrame/table with 9-axis weights
- `risk_scenarios`: Configuration (YAML/CSV/DB)

**Output:**
- List of 10 risk objects (as shown in JSON above)

**Performance:** 
- Must complete in <200ms for 410 questions

**Files to create:**
- `risk_engine.py` (or `risk_engine.js`)
- Unit tests: `test_risk_engine.py`

---

### 2. Frontend: Risk Heatmap Component

**Framework:** React/Vue/Angular (match existing platform)

**Input:** 
- `riskResults`: Array of 10 risk objects from backend

**Output:**
- Interactive 5×5 heatmap
- Risk dots positioned at (likelihood, impact)
- Color-coded by risk_level
- Hover shows scenario name + risk score
- Click shows full advisory

**Design specs:**
- Canvas size: 600×600 px
- Grid: 5×5 cells, 100px each
- Dots: 20px radius circles
- Colors: 
  - RED: #DC2626
  - AMBER: #F59E0B
  - YELLOW: #FCD34D
  - GREEN: #10B981

**Files to create:**
- `RiskHeatmap.jsx` (or `.vue`, `.tsx`)
- `RiskHeatmap.css`

---

### 3. Report Output: PDF/Excel Integration

**Requirement:** Add risk heatmap to existing PDF reports

**Location:** New section after maturity spider chart

**Content:**
1. Risk heatmap (image)
2. Risk table (sorted by risk_score, descending)
3. Top 3 risks detail pages (full advisory text)

**Files to modify:**
- `report_generator.py` (or equivalent)
- `report_template.html` (if HTML→PDF)

---

### 4. Configuration Loading

**Choose ONE:**

**Option A: YAML file** (Recommended)
```python
import yaml

with open('config/risk_scenarios.yaml') as f:
    risk_scenarios = yaml.safe_load(f)['risk_scenarios']
```

**Option B: CSV/Excel**
```python
import pandas as pd

risk_scenarios = pd.read_csv('config/risk_scenarios.csv').to_dict('records')
```

**Option C: Database table**
```sql
SELECT * FROM risk_scenarios ORDER BY scenario_id;
```

---

## TESTING REQUIREMENTS

### Unit Tests

```python
def test_axis_score_calculation():
    """Axis scores should match maturity module"""
    responses = {...}
    axis_scores = calculate_axis_scores(responses)
    
    assert 0 <= axis_scores['V'] <= 4
    assert 0 <= axis_scores['T'] <= 4
    # ... all 9 axes

def test_curve_application():
    """Curves should transform 0-4 to 0-1"""
    assert apply_curve(0, 'standard') < 0.2
    assert apply_curve(4, 'standard') > 0.8
    assert apply_curve(2, 'threshold') == 0.5
    
def test_likelihood_calculation():
    """Likelihood should be 1-5"""
    assert calculate_likelihood(0.0) == 5  # No mitigation
    assert calculate_likelihood(1.0) == 1  # Perfect mitigation
    
def test_impact_calculation():
    """Impact should match intake tags"""
    tags = ['Technology', 'High-IP']
    impact = calculate_impact(IP_Theft_scenario, tags)
    assert impact == 5
```

### Integration Tests

```python
def test_full_risk_calculation():
    """End-to-end test with sample data"""
    responses = load_test_responses()  # Provided in test_data.json
    intake_tags = ['Technology', 'High-IP', 'Enterprise (5000+)']
    
    results = calculate_risks(responses, intake_tags)
    
    assert len(results) == 10
    assert all(1 <= r['likelihood'] <= 5 for r in results)
    assert all(1 <= r['impact'] <= 5 for r in results)
    assert all(r['risk_level'] in ['RED','AMBER','YELLOW','GREEN'] for r in results)
```

### Validation Tests

```python
def test_against_known_client():
    """Compare output to consultant judgment"""
    # Use real client data from Noventiq assessment
    responses = load_client_assessment('noventiq-2025-11')
    intake_tags = ['Technology', 'Enterprise (5000+)', 'EU-Primary']
    
    results = calculate_risks(responses, intake_tags)
    
    # Expected: IP Theft should be YELLOW (high impact, medium likelihood)
    ip_theft = [r for r in results if r['scenario'] == 'Intellectual Property Theft'][0]
    assert ip_theft['risk_level'] in ['YELLOW', 'AMBER']
    assert ip_theft['impact'] >= 4
```

---

## ACCEPTANCE CRITERIA

### Functional Requirements

- [ ] Risk calculation produces 10 risk positions
- [ ] Each risk has likelihood 1-5, impact 1-5
- [ ] Risk level correctly mapped (RED/AMBER/YELLOW/GREEN)
- [ ] Heatmap displays all 10 risks
- [ ] Risk section added to PDF reports
- [ ] Calculation completes in <200ms

### Data Validation

- [ ] Axis scores match existing maturity calculation
- [ ] Risk scenarios config validates (weights sum to 1.0)
- [ ] All intake tags referenced in impact rules exist

### Business Validation

- [ ] Run on 3 completed assessments
- [ ] Compare output to consultant judgment (>85% agreement)
- [ ] Consultants can explain any risk position to client

### Performance

- [ ] Risk calculation: <200ms
- [ ] Heatmap rendering: <100ms
- [ ] PDF generation: <5 seconds (including risk section)

---

## TIMELINE

**Week 1:**
- Day 1-2: Set up risk scenarios config (YAML/CSV/DB)
- Day 3-4: Implement risk calculation module
- Day 5: Unit testing

**Week 2:**
- Day 1-2: Build heatmap component
- Day 3-4: Integrate into report generation
- Day 5: Integration testing

**Week 3:**
- Day 1-2: Run on 3 real assessments
- Day 3-4: Fix any issues, tune if needed
- Day 5: Documentation & handoff

**Total: 40 hours**

---

## SUPPORT & QUESTIONS

**Technical questions:** 
- Check `integration_code_examples.py` for copy-paste ready code
- See `test_data.json` for sample inputs/outputs

**Business questions:**
- Why these 10 risks? See `Big4_Risk_Methodology.md`
- Why these axis weights? See risk scenario documentation

**Stuck?**
- Email: jacob@belfortadvisory.be
- Slack: #irmmf-development

---

## FILES PROVIDED

```
/risk_module_package/
├── DEVELOPER_BRIEF.md                    ← This file
├── risk_scenarios.yaml                   ← Config (YAML format)
├── risk_scenarios.csv                    ← Config (Excel/CSV format)
├── risk_scenarios.sql                    ← Config (Database format)
├── integration_code_examples.py          ← Copy-paste ready code
├── test_data.json                        ← Sample inputs/outputs
├── ACCEPTANCE_CRITERIA.md                ← Definition of done
└── Big4_Risk_Methodology.md              ← Why these weights (optional reading)
```

---

## FINAL CHECKLIST

Before starting:
- [ ] Read this brief (20 min)
- [ ] Review `integration_code_examples.py` (30 min)
- [ ] Choose config format (YAML/CSV/DB)
- [ ] Set up dev environment with test data

Before shipping:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Ran on 3 real assessments
- [ ] Consultants validated output
- [ ] Documentation updated

---

**Questions? Start here, then reach out if stuck.**
