from __future__ import annotations

from typing import Dict, List


QUESTION_BANK: List[Dict[str, object]] = [
    {
        "q_id": "TPR-GOV-1",
        "category": "Governance",
        "question_text": "Is there a signed security addendum (DPA/SLA) with breach notification terms?",
        "weight": 1.0,
        "options": [
            {"a_id": "TPR-GOV-1-0", "label": "No documented agreement", "score": 0.0},
            {"a_id": "TPR-GOV-1-1", "label": "Draft or expired agreement", "score": 1.0},
            {"a_id": "TPR-GOV-1-2", "label": "Signed, reviewed >12 months ago", "score": 2.0},
            {"a_id": "TPR-GOV-1-3", "label": "Signed within 12 months", "score": 3.0},
            {"a_id": "TPR-GOV-1-4", "label": "Signed + audit rights + 72h notification", "score": 4.0},
        ],
    },
    {
        "q_id": "TPR-SEC-1",
        "category": "Security Assurance",
        "question_text": "Which security assurance evidence is current?",
        "weight": 1.0,
        "options": [
            {"a_id": "TPR-SEC-1-0", "label": "No third-party assurance", "score": 0.0},
            {"a_id": "TPR-SEC-1-1", "label": "Self-attested controls", "score": 1.0},
            {"a_id": "TPR-SEC-1-2", "label": "ISO 27001 or SOC 1 Type I", "score": 2.0},
            {"a_id": "TPR-SEC-1-3", "label": "SOC 2 Type II or ISO 27001 + annual audit", "score": 3.0},
            {"a_id": "TPR-SEC-1-4", "label": "SOC 2 Type II + continuous monitoring", "score": 4.0},
        ],
    },
    {
        "q_id": "TPR-DATA-1",
        "category": "Data Handling",
        "question_text": "What level of data sensitivity does the partner process or access?",
        "weight": 1.2,
        "options": [
            {"a_id": "TPR-DATA-1-4", "label": "No sensitive data (public/internal only)", "score": 4.0},
            {"a_id": "TPR-DATA-1-3", "label": "Internal confidential data", "score": 3.0},
            {"a_id": "TPR-DATA-1-2", "label": "Limited customer/employee PII", "score": 2.0},
            {"a_id": "TPR-DATA-1-1", "label": "Regulated data (PCI/PHI/ID)", "score": 1.0},
            {"a_id": "TPR-DATA-1-0", "label": "Unknown or uncontrolled data scope", "score": 0.0},
        ],
    },
    {
        "q_id": "TPR-ACCESS-1",
        "category": "Access Controls",
        "question_text": "How does the partner access your environment?",
        "weight": 1.2,
        "options": [
            {"a_id": "TPR-ACCESS-1-4", "label": "No direct access (data exchange only)", "score": 4.0},
            {"a_id": "TPR-ACCESS-1-3", "label": "SSO + least-privilege accounts", "score": 3.0},
            {"a_id": "TPR-ACCESS-1-2", "label": "VPN with MFA", "score": 2.0},
            {"a_id": "TPR-ACCESS-1-1", "label": "Shared accounts or local admin", "score": 1.0},
            {"a_id": "TPR-ACCESS-1-0", "label": "Persistent privileged access without MFA", "score": 0.0},
        ],
    },
    {
        "q_id": "TPR-IR-1",
        "category": "Incident Readiness",
        "question_text": "How mature is the joint incident response process?",
        "weight": 1.0,
        "options": [
            {"a_id": "TPR-IR-1-0", "label": "No defined incident process", "score": 0.0},
            {"a_id": "TPR-IR-1-1", "label": "Ad-hoc escalation", "score": 1.0},
            {"a_id": "TPR-IR-1-2", "label": "Documented but untested", "score": 2.0},
            {"a_id": "TPR-IR-1-3", "label": "Tested annually with SLAs", "score": 3.0},
            {"a_id": "TPR-IR-1-4", "label": "Joint exercises + 24/7 contacts", "score": 4.0},
        ],
    },
    {
        "q_id": "TPR-BCP-1",
        "category": "Resilience",
        "question_text": "How recent is the partner's business continuity testing?",
        "weight": 1.0,
        "options": [
            {"a_id": "TPR-BCP-1-0", "label": "No documented continuity plan", "score": 0.0},
            {"a_id": "TPR-BCP-1-1", "label": "Plan documented, not tested", "score": 1.0},
            {"a_id": "TPR-BCP-1-2", "label": "Tested >12 months ago", "score": 2.0},
            {"a_id": "TPR-BCP-1-3", "label": "Tested within 12 months", "score": 3.0},
            {"a_id": "TPR-BCP-1-4", "label": "Tested within 6 months with RTO/RPO met", "score": 4.0},
        ],
    },
]


def get_question_bank() -> List[Dict[str, object]]:
    return QUESTION_BANK
