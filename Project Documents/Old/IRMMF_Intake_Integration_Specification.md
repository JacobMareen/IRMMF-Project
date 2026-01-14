# IRMMF Intake Module Integration Specification

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ASSESSMENT WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐      ┌──────────────────┐      ┌────────────────┐   │
│   │  INTAKE MODULE   │ ───▶ │  CONFIGURATION   │ ───▶ │  PACK DELIVERY │   │
│   │  (This module)   │      │     ENGINE       │      │   & SCORING    │   │
│   └──────────────────┘      └──────────────────┘      └────────────────┘   │
│           │                         │                         │             │
│           ▼                         ▼                         ▼             │
│   ┌──────────────────┐      ┌──────────────────┐      ┌────────────────┐   │
│   │ intake_responses │      │ assessment_config │      │   responses    │   │
│   │ benchmark_tags   │      │ pack_assignments  │      │   scores       │   │
│   └──────────────────┘      └──────────────────┘      └────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Data Flow Specification

### 2.1 Intake Outputs → Assessment Configuration

| Intake Output | Target in IRMMF_Combined_AllPacks | Usage |
|---------------|-----------------------------------|-------|
| `RecommendedDepth` | PackMap.Include_Lightweight/Standard/Deep | Filter questions by mode |
| `AvailablePacks[]` | PackMap.PackID filter | Include only assigned packs |
| `RoleCoverageCI` | CI calculation (§6.6 methodology) | Adjust confidence index |
| `RiskPriorityFlag` | CW multiplier for Axes V, R | Increase criticality weighting |
| `RegionalOverlay` | EvidencePolicyID modifiers | Stricter evidence for EU contexts |
| `BenchmarkCohort` | Assessment metadata | Store for future comparison |

### 2.2 Field-Level Mapping

```yaml
# Configuration object passed to scoring engine
assessment_config:
  assessment_id: UUID
  organization_id: UUID
  
  # From Intake S7 (Assessment Configuration)
  depth_mode: "Standard"  # Computed or override from S7-Q11
  
  # From Intake S7-Q04 to S7-Q10
  active_packs:
    - PackID: "Executive"
      respondent_role: "CFO"
      respondent_type: "internal"
      role_weight: 1.0
    - PackID: "Security"
      respondent_role: "CISO"
      respondent_type: "internal"
      role_weight: 1.0
    - PackID: "HR"
      respondent_role: "CHRO"
      respondent_type: "internal"
      role_weight: 1.0
    - PackID: "Legal"
      respondent_role: "External DPO"
      respondent_type: "external"
      role_weight: 0.85  # Proxy weight per methodology §4.3
  
  # Computed from Intake
  role_coverage_ci: 0.71  # 5 of 7 packs = 5/7
  
  # From Intake S4 (Regulatory Context)
  regulatory_overlay:
    nis2_entity_type: "Essential"
    dora_scope: true
    works_council: true
    evidence_policy_modifier: "EU_STRICT"  # Triggers LEG_STRICT for all L-axis
  
  # From Intake S5 (Risk Profile)
  risk_flags:
    high_priority: true  # Any Yes in S5-Q02, Q03, Q05
    crown_jewels: ["trade_secrets", "source_code", "customer_pii"]
    upcoming_events: ["restructuring"]
  
  # For storage/benchmarking
  benchmark_tags:
    primary_cohort: "Financial_Services_MidMarket"
    secondary_tags:
      - "EU_Primary"
      - "NIS2_Essential"
      - "DORA_Inscope"
      - "High_IP"
      - "Established_Program"
```

## 3. Integration Points in Existing Model

### 3.1 Updates to IRMMF_Combined_AllPacks_v1_8_1

#### 3.1.1 New Sheet: `Intake_Config`

Add a sheet to store the intake-derived configuration:

| Column | Type | Description |
|--------|------|-------------|
| AssessmentID | UUID | Links to Response_Template |
| DepthMode | Enum | Lightweight/Standard/Deep |
| ActivePacks | Text[] | JSON array of pack IDs |
| RoleCoverageCI | Decimal | 0.00-1.00 |
| RegulatoryOverlay | Text | EU_STRICT / STANDARD / LITE |
| RiskPriorityFlag | Boolean | High-priority risk indicators present |
| BenchmarkCohortPrimary | Text | Industry_Size combination |
| BenchmarkTagsJSON | Text | JSON array of secondary tags |
| IntakeCompletedAt | DateTime | Timestamp |
| IntakeRespondent | Text | Who completed intake |

#### 3.1.2 Modify `PackMap` Sheet

Add columns for intake-driven filtering:

| New Column | Purpose |
|------------|---------|
| `DepthModeRequired` | Minimum depth for this question (replaces current Include_* columns logic) |
| `RegulatoryOverlayRequired` | Only include if regulatory overlay matches |
| `RiskFlagBoost` | CW multiplier when RiskPriorityFlag = true |

#### 3.1.3 Modify `Reference` Sheet

Add new sections:

```
Section: IntakeIntegration
Key: DepthMode_Lightweight_Tiers
Value: T1 only

Section: IntakeIntegration  
Key: DepthMode_Standard_Tiers
Value: T1, T2, T3

Section: IntakeIntegration
Key: DepthMode_Deep_Tiers
Value: T1, T2, T3, T4

Section: IntakeIntegration
Key: RoleCoverageCI_Formula
Value: ActivePackCount / 7

Section: IntakeIntegration
Key: EU_STRICT_EvidenceModifier
Value: LEG_STRICT applies to all L-axis questions; Tier A cap = 1 for monitoring questions

Section: IntakeIntegration
Key: RiskPriorityFlag_CWBoost
Value: 1.2x multiplier for V-axis and R-axis questions
```

### 3.2 Updates to Scoring Engine

#### 3.2.1 Question Filtering

```python
def get_active_questions(assessment_config, all_questions, pack_map):
    """Filter questions based on intake configuration."""
    
    active_questions = []
    
    for q in all_questions:
        # Check pack is active
        q_packs = pack_map[pack_map['Q-ID'] == q['Q-ID']]
        if not any(p in assessment_config['active_packs'] for p in q_packs['PackID']):
            continue
        
        # Check depth mode
        depth = assessment_config['depth_mode']
        if depth == 'Lightweight' and q['Tier'] not in ['T1']:
            continue
        if depth == 'Standard' and q['Tier'] not in ['T1', 'T2', 'T3']:
            continue
        # Deep includes all tiers
        
        # Check regulatory overlay requirements
        if q.get('RegulatoryOverlayRequired'):
            if q['RegulatoryOverlayRequired'] != assessment_config['regulatory_overlay']:
                continue
        
        active_questions.append(q)
    
    return active_questions
```

#### 3.2.2 CI Calculation Update

```python
def calculate_ci(evidence_coverage, role_coverage_from_intake, depth_coverage):
    """
    CI formula per methodology §6.6, now using intake-derived role coverage.
    """
    # Role coverage comes directly from intake
    role_coverage = role_coverage_from_intake  # e.g., 5/7 = 0.71
    
    ci = (0.5 * evidence_coverage) + (0.3 * role_coverage) + (0.2 * depth_coverage)
    
    return min(ci, 1.0)
```

#### 3.2.3 CW Adjustment for Risk Priority

```python
def get_adjusted_cw(question, assessment_config):
    """Apply risk priority boost to criticality weight."""
    
    base_cw = question['CW']
    
    if assessment_config['risk_flags']['high_priority']:
        if question['Axis1'] in ['V', 'R'] or question.get('Axis2') in ['V', 'R']:
            return base_cw * 1.2  # 20% boost per Reference.RiskPriorityFlag_CWBoost
    
    return base_cw
```

#### 3.2.4 Evidence Policy Modifier

```python
def get_evidence_cap(question, evidence_tier, assessment_config):
    """Apply regulatory overlay to evidence caps."""
    
    base_policy = question['EvidencePolicyID']
    
    # EU_STRICT overlay upgrades evidence requirements
    if assessment_config['regulatory_overlay']['evidence_policy_modifier'] == 'EU_STRICT':
        if question['Axis1'] == 'L' or question.get('Axis2') == 'L':
            base_policy = 'LEG_STRICT'  # Override to strictest
    
    return EVIDENCE_CAPS[base_policy][evidence_tier]
```

## 4. Database Schema Extensions

### 4.1 New Tables

```sql
-- Intake responses (one row per question answered)
CREATE TABLE intake_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL,
    q_id VARCHAR(20) NOT NULL,
    response_value TEXT,
    response_date TIMESTAMP DEFAULT NOW(),
    respondent_name VARCHAR(255),
    respondent_email VARCHAR(255),
    notes TEXT,
    UNIQUE(assessment_id, q_id)
);

-- Computed intake outputs (one row per assessment)
CREATE TABLE intake_config (
    assessment_id UUID PRIMARY KEY,
    organization_id UUID NOT NULL,
    
    -- Depth determination
    depth_score DECIMAL(3,2),
    depth_mode VARCHAR(20) NOT NULL,  -- Lightweight/Standard/Deep
    depth_override BOOLEAN DEFAULT FALSE,
    
    -- Pack assignment
    active_packs JSONB NOT NULL,  -- [{pack_id, respondent, role_weight}]
    role_coverage_ci DECIMAL(3,2),
    
    -- Regulatory context
    regulatory_overlay VARCHAR(20),  -- EU_STRICT/STANDARD/LITE
    works_council_present BOOLEAN,
    
    -- Risk flags
    risk_priority_flag BOOLEAN,
    crown_jewels JSONB,
    upcoming_events JSONB,
    
    -- Benchmarking
    benchmark_cohort_primary VARCHAR(100),
    benchmark_tags JSONB,
    
    -- Metadata
    intake_completed_at TIMESTAMP,
    intake_respondent VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

-- Benchmark cohort definitions (reference data)
CREATE TABLE benchmark_cohorts (
    cohort_id VARCHAR(100) PRIMARY KEY,
    industry_group VARCHAR(50),
    size_group VARCHAR(50),
    description TEXT,
    min_assessments_for_benchmark INT DEFAULT 50
);

-- Organization master (for multi-assessment tracking)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name VARCHAR(255) NOT NULL,
    trading_name VARCHAR(255),
    industry_code VARCHAR(10),
    hq_country VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.2 Indexes for Benchmarking Queries

```sql
CREATE INDEX idx_intake_config_cohort ON intake_config(benchmark_cohort_primary);
CREATE INDEX idx_intake_config_tags ON intake_config USING GIN(benchmark_tags);
CREATE INDEX idx_intake_config_org ON intake_config(organization_id);
```

## 5. API Endpoints (If Building Web Application)

### 5.1 Intake Submission

```
POST /api/v1/assessments/{assessment_id}/intake
Content-Type: application/json

{
  "responses": [
    {"q_id": "INTAKE-S1-Q01", "value": "Acme Corporation"},
    {"q_id": "INTAKE-S1-Q03", "value": "K - Financial and insurance"},
    ...
  ],
  "respondent": {
    "name": "Jane Smith",
    "email": "jane.smith@acme.com",
    "role": "CISO"
  }
}

Response:
{
  "assessment_id": "uuid",
  "intake_config": {
    "depth_mode": "Standard",
    "depth_score": 1.15,
    "active_packs": ["Executive", "Security", "HR", "Legal", "IT_IAM"],
    "role_coverage_ci": 0.71,
    "benchmark_cohort_primary": "Financial_Services_MidMarket",
    "risk_priority_flag": true,
    "estimated_duration_minutes": 180
  },
  "next_step": "pack_assignment_confirmation"
}
```

### 5.2 Configuration Retrieval

```
GET /api/v1/assessments/{assessment_id}/config

Response:
{
  "assessment_id": "uuid",
  "depth_mode": "Standard",
  "active_packs": [...],
  "question_count": 89,
  "estimated_duration_minutes": 180,
  "regulatory_overlay": "EU_STRICT",
  "benchmark_cohort": "Financial_Services_MidMarket"
}
```

## 6. Validation Rules

### 6.1 Intake Completion Validation

```python
REQUIRED_INTAKE_QUESTIONS = [
    # S1: Organization Identity
    "INTAKE-S1-Q01",  # Organization name
    "INTAKE-S1-Q03",  # Industry
    "INTAKE-S1-Q06",  # HQ country
    
    # S2: Scale
    "INTAKE-S2-Q01",  # Employee count
    "INTAKE-S2-Q02",  # Revenue
    
    # S4: Regulatory
    "INTAKE-S4-Q01",  # NIS2
    "INTAKE-S4-Q07",  # Works council
    
    # S7: Configuration (all role availability questions)
    "INTAKE-S7-Q01",  # Purpose
    "INTAKE-S7-Q04",  # Exec availability
    "INTAKE-S7-Q05",  # Security availability
    "INTAKE-S7-Q06",  # HR availability
    "INTAKE-S7-Q07",  # Legal availability
]

MINIMUM_PACKS_REQUIRED = 3  # Exec + Legal + (Security OR HR)
```

### 6.2 Pack Assignment Validation

```python
def validate_pack_assignment(active_packs):
    """Ensure minimum viable assessment."""
    
    has_exec = "Executive" in active_packs
    has_legal = "Legal" in active_packs
    has_security_or_hr = "Security" in active_packs or "HR" in active_packs
    
    if not (has_exec and has_legal and has_security_or_hr):
        raise ValidationError(
            "Minimum viable assessment requires: Executive + Legal + (Security OR HR)"
        )
    
    return True
```

## 7. Testing Checklist

### 7.1 Integration Tests

- [ ] Intake responses correctly compute depth score
- [ ] Depth mode filters questions appropriately (Lightweight=T1, Standard=T1-T3, Deep=all)
- [ ] Pack filtering excludes questions for unavailable packs
- [ ] Role coverage CI calculated correctly (active_packs / 7)
- [ ] EU_STRICT overlay applies to L-axis questions
- [ ] Risk priority flag boosts CW for V/R axes
- [ ] Benchmark tags derived correctly from responses
- [ ] Minimum pack validation prevents invalid configurations

### 7.2 Edge Cases

- [ ] Single-respondent SME assessment (Lightweight, 2 packs)
- [ ] Full enterprise assessment (Deep, 7 packs)
- [ ] Override depth to Deep when score says Lightweight
- [ ] Works council present → confirms EU_STRICT overlay
- [ ] All risk flags true → verify CW multipliers stack correctly
