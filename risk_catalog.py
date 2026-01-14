RISK_CATALOG = [
    {
        "id": "ip_leakage",
        "name": "IP Leakage",
        "axes": ["G", "V", "L"],
        "description": "Exposure of sensitive IP through weak controls or oversight."
    },
    {
        "id": "privileged_misuse",
        "name": "Privileged Misuse",
        "axes": ["G", "T", "H"],
        "description": "Abuse of privileged access by insiders or admins."
    },
    {
        "id": "shadow_ai_exfil",
        "name": "Shadow AI Exfiltration",
        "axes": ["T", "V", "F"],
        "description": "Use of unapproved AI tools leading to data leakage."
    },
    {
        "id": "insider_sabotage",
        "name": "Insider Sabotage",
        "axes": ["H", "R", "E"],
        "description": "Intentional disruption by insiders with access."
    },
    {
        "id": "compliance_breach",
        "name": "Regulatory Breach",
        "axes": ["L", "G", "V"],
        "description": "Failure to meet regulatory or contractual obligations."
    },
    {
        "id": "supply_chain_leak",
        "name": "Supply Chain Exposure",
        "axes": ["G", "V", "E"],
        "description": "Risk introduced through vendors and partners."
    },
    {
        "id": "detection_failure",
        "name": "Detection Failure",
        "axes": ["T", "V"],
        "description": "Low visibility into abnormal insider activity."
    },
    {
        "id": "policy_drift",
        "name": "Policy Drift",
        "axes": ["G", "H", "E"],
        "description": "Policies exist but are not enforced in practice."
    },
    {
        "id": "data_mishandling",
        "name": "Data Mishandling",
        "axes": ["V", "H", "F"],
        "description": "Incorrect handling or sharing of sensitive data."
    },
    {
        "id": "segregation_gaps",
        "name": "Segregation of Duties Gaps",
        "axes": ["G", "T"],
        "description": "Inadequate separation of critical responsibilities."
    },
    {
        "id": "weak_offboarding",
        "name": "Weak Offboarding",
        "axes": ["H", "G"],
        "description": "Lingering access and data exposure after exits."
    },
    {
        "id": "response_immaturity",
        "name": "Incident Response Immaturity",
        "axes": ["R", "E", "T"],
        "description": "Limited response readiness for insider incidents."
    },
]
