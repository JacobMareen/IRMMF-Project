"""
IRMMF Risk Engine - Integration Code Examples
Copy-paste ready implementations for Python backend

Author: Belfort Advisory
Date: 2026-01-11
License: Internal use only
"""

import numpy as np
import pandas as pd
import yaml
import json
from typing import Dict, List, Tuple


# =============================================================================
# PART 1: CONFIGURATION LOADING
# =============================================================================

def load_risk_scenarios_yaml(filepath='config/risk_scenarios_simple.yaml'):
    """
    Load risk scenarios from YAML file
    
    Args:
        filepath: Path to YAML config file
        
    Returns:
        List of risk scenario dicts
    """
    with open(filepath, 'r') as f:
        config = yaml.safe_load(f)
    return config['risks']


def load_risk_scenarios_csv(filepath='config/risk_scenarios.csv'):
    """
    Load risk scenarios from CSV file
    
    Args:
        filepath: Path to CSV file
        
    Returns:
        List of risk scenario dicts
    """
    df = pd.read_csv(filepath)
    
    scenarios = []
    for _, row in df.iterrows():
        scenario = {
            'id': row['Scenario_ID'],
            'name': row['Scenario_Name'],
            'category': row['Category'],
            'description': row['Description'],
            'axes': {},
            'curves': {},
            'impact_rules': []
        }
        
        # Parse axis weights
        for axis in ['G', 'E', 'T', 'L', 'H', 'V', 'R', 'F', 'W']:
            weight = row[f'Axis_{axis}']
            if weight > 0:
                scenario['axes'][axis] = weight
                scenario['curves'][axis] = row[f'Curve_{axis}']
        
        # Parse impact rules
        for i in range(1, 4):  # Up to 3 rules
            cond_col = f'Impact_Rule_{i}_Condition'
            val_col = f'Impact_Rule_{i}_Value'
            
            if pd.notna(row[cond_col]) and row[cond_col]:
                scenario['impact_rules'].append({
                    'condition': row[cond_col],
                    'value': row[val_col] if row[val_col] != '+1' else '+1'
                })
        
        # Add default rule
        scenario['impact_rules'].append({
            'condition': 'default',
            'value': row['Impact_Default']
        })
        
        scenarios.append(scenario)
    
    return scenarios


# =============================================================================
# PART 2: AXIS SCORE CALCULATION (You already have this)
# =============================================================================

def calculate_axis_scores(responses: Dict[str, int], 
                          questions_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate weighted average score for each axis
    
    Args:
        responses: {Q-ID: BaseScore} from user selections
        questions_df: DataFrame with columns Q-ID, Pts_G, Pts_E, ..., Pts_W
        
    Returns:
        {axis: score} for G, E, T, L, H, V, R, F, W (each 0-4)
    """
    axis_scores = {}
    
    for axis in ['G', 'E', 'T', 'L', 'H', 'V', 'R', 'F', 'W']:
        weighted_sum = 0.0
        total_weight = 0.0
        
        for q_id, answer_score in responses.items():
            # Find question
            question = questions_df[questions_df['Q-ID'] == q_id]
            if question.empty:
                continue
            
            question = question.iloc[0]
            axis_weight = question[f'Pts_{axis}']
            
            if axis_weight > 0:
                weighted_sum += answer_score * axis_weight
                total_weight += axis_weight
        
        axis_scores[axis] = weighted_sum / total_weight if total_weight > 0 else 0.0
    
    return axis_scores


# =============================================================================
# PART 3: MITIGATION CURVE APPLICATION
# =============================================================================

def apply_mitigation_curve(raw_score: float, curve_type: str) -> float:
    """
    Transform axis score (0-4) to mitigation effectiveness (0-1)
    
    Args:
        raw_score: Axis score from calculate_axis_scores (0-4)
        curve_type: "threshold", "standard", or "logarithmic"
        
    Returns:
        Mitigation effectiveness (0-1)
    """
    if curve_type == "threshold":
        # Binary controls (DLP, PAM): have it or don't
        # Below threshold = minimal protection
        if raw_score < 2.0:
            return 0.1
        else:
            return 0.5 + (raw_score - 2.0) * 0.2
    
    elif curve_type == "logarithmic":
        # Diminishing returns (training, speed)
        # Early gains are large, later gains are small
        return 1 - np.exp(-0.5 * raw_score)
    
    else:  # "standard"
        # S-curve (most controls)
        # Slow start, fast middle, slow end
        return 1 / (1 + np.exp(-1.5 * (raw_score - 2.0)))


# =============================================================================
# PART 4: IMPACT CALCULATION FROM INTAKE TAGS
# =============================================================================

def evaluate_condition(condition: str, intake_tags: List[str]) -> bool:
    """
    Evaluate a tag condition (supports OR, AND)
    
    Args:
        condition: e.g., "High-IP OR Technology"
        intake_tags: List of tags from intake module
        
    Returns:
        True if condition is met
    """
    if condition == 'default':
        return True
    
    if ' OR ' in condition:
        parts = condition.split(' OR ')
        return any(part.strip() in intake_tags for part in parts)
    
    elif ' AND ' in condition:
        parts = condition.split(' AND ')
        return all(part.strip() in intake_tags for part in parts)
    
    else:
        return condition.strip() in intake_tags


def calculate_impact(scenario: Dict, intake_tags: List[str]) -> int:
    """
    Determine inherent impact (1-5) from intake tags
    
    Args:
        scenario: Risk scenario dict with impact_rules
        intake_tags: List of tags from intake module
        
    Returns:
        Impact score 1-5
    """
    impact = 1  # Default base
    
    # Check rules in order
    for rule in scenario['impact_rules']:
        if evaluate_condition(rule['condition'], intake_tags):
            if rule['value'] == '+1':
                impact = min(5, impact + 1)
            else:
                impact = rule['value']
            break  # First matching rule wins (except +1 modifiers)
    
    return impact


# =============================================================================
# PART 5: LIKELIHOOD CALCULATION
# =============================================================================

def calculate_mitigation_score(scenario: Dict, 
                               axis_scores: Dict[str, float]) -> float:
    """
    Calculate overall mitigation for a risk scenario
    
    Args:
        scenario: Risk scenario dict with axes and curves
        axis_scores: {axis: score} from calculate_axis_scores
        
    Returns:
        Mitigation score 0-1
    """
    mitigation = 0.0
    
    for axis, weight in scenario['axes'].items():
        raw_score = axis_scores.get(axis, 0.0)
        curve_type = scenario['curves'].get(axis, 'standard')
        
        # Transform score using curve
        axis_mitigation = apply_mitigation_curve(raw_score, curve_type)
        
        # Weight by importance to this risk
        mitigation += weight * axis_mitigation
    
    return mitigation


def calculate_likelihood(mitigation_score: float) -> int:
    """
    Convert mitigation effectiveness to likelihood (1-5)
    
    Perfect mitigation (1.0) → Likelihood 1 (Rare)
    No mitigation (0.0) → Likelihood 5 (Almost Certain)
    
    Args:
        mitigation_score: 0-1 from calculate_mitigation_score
        
    Returns:
        Likelihood 1-5
    """
    raw_likelihood = 5 - (mitigation_score * 4)
    return max(1, min(5, int(round(raw_likelihood))))


# =============================================================================
# PART 6: RISK LEVEL DETERMINATION
# =============================================================================

def determine_risk_level(likelihood: int, impact: int) -> Tuple[str, int]:
    """
    Map (likelihood, impact) to risk level
    
    Args:
        likelihood: 1-5
        impact: 1-5
        
    Returns:
        (risk_level, risk_score) tuple
        risk_level: "RED", "AMBER", "YELLOW", or "GREEN"
        risk_score: likelihood × impact (1-25)
    """
    risk_score = likelihood * impact
    
    if risk_score >= 20:
        return "RED", risk_score
    elif risk_score >= 12:
        return "AMBER", risk_score
    elif risk_score >= 6:
        return "YELLOW", risk_score
    else:
        return "GREEN", risk_score


# =============================================================================
# PART 7: MAIN RISK CALCULATION ENGINE
# =============================================================================

class RiskEngine:
    """Main risk calculation engine"""
    
    LIKELIHOOD_LABELS = {
        1: "Rare",
        2: "Unlikely",
        3: "Possible",
        4: "Likely",
        5: "Almost Certain"
    }
    
    IMPACT_LABELS = {
        1: "Negligible",
        2: "Minor",
        3: "Moderate",
        4: "Major",
        5: "Catastrophic"
    }
    
    def __init__(self, questions_df: pd.DataFrame, risk_scenarios: List[Dict]):
        """
        Args:
            questions_df: Questions with 9-axis weights
            risk_scenarios: List of risk scenario configs
        """
        self.questions = questions_df
        self.scenarios = risk_scenarios
    
    def calculate_risks(self, 
                       responses: Dict[str, int], 
                       intake_tags: List[str]) -> List[Dict]:
        """
        Main entry point: Calculate all risk scenarios
        
        Args:
            responses: {Q-ID: BaseScore} from assessment
            intake_tags: Tags from intake module
            
        Returns:
            List of risk result dicts
        """
        # Step 1: Calculate axis scores (reuse existing code)
        axis_scores = calculate_axis_scores(responses, self.questions)
        
        # Step 2: Calculate each risk scenario
        results = []
        
        for scenario in self.scenarios:
            # Calculate mitigation
            mitigation = calculate_mitigation_score(scenario, axis_scores)
            
            # Calculate likelihood
            likelihood = calculate_likelihood(mitigation)
            
            # Calculate impact
            impact = calculate_impact(scenario, intake_tags)
            
            # Determine risk level
            risk_level, risk_score = determine_risk_level(likelihood, impact)
            
            # Generate advisory (simplified for example)
            advisory = self._generate_advisory(
                scenario, likelihood, impact, risk_level, axis_scores
            )
            
            # Identify key gaps
            key_gaps = self._identify_key_gaps(scenario, axis_scores)
            
            result = {
                'scenario': scenario['name'],
                'scenario_id': scenario['id'],
                'category': scenario['category'],
                'likelihood': likelihood,
                'likelihood_label': self.LIKELIHOOD_LABELS[likelihood],
                'impact': impact,
                'impact_label': self.IMPACT_LABELS[impact],
                'risk_score': risk_score,
                'risk_level': risk_level,
                'mitigation_score': round(mitigation, 3),
                'key_gaps': key_gaps,
                'advisory': advisory
            }
            
            results.append(result)
        
        # Sort by risk score (descending)
        results.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return results
    
    def _identify_key_gaps(self, scenario: Dict, axis_scores: Dict[str, float]) -> List[str]:
        """Identify weakest axes for this risk"""
        gaps = []
        
        for axis, weight in scenario['axes'].items():
            if weight >= 0.15:  # Significant contributor
                score = axis_scores.get(axis, 0)
                if score < 3.0:  # Below "good" threshold
                    axis_names = {
                        'G': 'Governance',
                        'E': 'Execution',
                        'T': 'Technical',
                        'L': 'Legal',
                        'H': 'Human',
                        'V': 'Visibility',
                        'R': 'Resilience',
                        'F': 'Friction',
                        'W': 'Control Lag'
                    }
                    gaps.append(f"{axis_names[axis]}: {score:.1f}/4")
        
        return gaps[:3]  # Top 3 gaps
    
    def _generate_advisory(self, scenario: Dict, likelihood: int, 
                          impact: int, risk_level: str, 
                          axis_scores: Dict[str, float]) -> str:
        """Generate advisory text based on risk level"""
        
        if risk_level == "RED" or risk_level == "AMBER":
            return f"🔴 CRITICAL: {scenario['name']} is highly vulnerable. " \
                   f"Immediate action required to strengthen controls."
        
        elif risk_level == "YELLOW":
            return f"🟡 MODERATE: {scenario['name']} has exploitable gaps. " \
                   f"Priority improvements needed."
        
        else:
            return f"✓ ACCEPTABLE: {scenario['name']} is adequately controlled. " \
                   f"Maintain current posture."


# =============================================================================
# PART 8: USAGE EXAMPLE
# =============================================================================

def main():
    """Example usage"""
    
    # Load configuration
    scenarios = load_risk_scenarios_yaml('risk_scenarios_simple.yaml')
    
    # Load questions (from your existing data)
    questions_df = pd.read_excel('QuestionBank.xlsx', sheet_name='Questions')
    
    # Example user responses (you already capture this)
    responses = {
        'ADD-AI-Q01': 3,
        'SEC-D2-Q04': 2,
        'ITIAM-D1-Q01': 4,
        # ... all 410 questions
    }
    
    # Example intake tags
    intake_tags = ['Technology', 'High-IP', 'Enterprise (5000+)', 'EU-Primary']
    
    # Initialize engine
    engine = RiskEngine(questions_df, scenarios)
    
    # Calculate risks
    results = engine.calculate_risks(responses, intake_tags)
    
    # Print results
    print("\n" + "="*80)
    print("RISK ASSESSMENT RESULTS")
    print("="*80)
    
    for result in results:
        print(f"\n{result['scenario']}")
        print(f"  Category: {result['category']}")
        print(f"  Likelihood: {result['likelihood']}/5 ({result['likelihood_label']})")
        print(f"  Impact: {result['impact']}/5 ({result['impact_label']})")
        print(f"  Risk Score: {result['risk_score']}/25")
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Mitigation: {result['mitigation_score']:.1%}")
        
        if result['key_gaps']:
            print(f"  Key Gaps: {', '.join(result['key_gaps'])}")
        
        print(f"  Advisory: {result['advisory']}")
    
    # Export to JSON for frontend
    with open('risk_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n✓ Results saved to risk_results.json")


if __name__ == "__main__":
    main()


# =============================================================================
# PART 9: QUICK INTEGRATION SNIPPET
# =============================================================================

"""
QUICK INTEGRATION (Add to your existing assessment processing):

# After maturity calculation:
from risk_engine import RiskEngine, load_risk_scenarios_yaml

# Load config (do once at startup)
risk_scenarios = load_risk_scenarios_yaml()
risk_engine = RiskEngine(questions_df, risk_scenarios)

# Calculate risks (do for each assessment)
risk_results = risk_engine.calculate_risks(user_responses, intake_tags)

# Add to output
assessment_output['risks'] = risk_results
"""
