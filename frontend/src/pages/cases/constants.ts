export const STEPS = [
    { key: 'intake', label: 'Intake', stage: 'INTAKE' },
    { key: 'legitimacy', label: 'Legitimacy', stage: 'LEGITIMACY_GATE' },
    { key: 'credentialing', label: 'Credentialing', stage: 'CREDENTIALING' },
    { key: 'investigation', label: 'Investigation', stage: 'INVESTIGATION' },
    { key: 'adversarial', label: 'Adversarial', stage: 'ADVERSARIAL_DEBATE' },
    { key: 'decision', label: 'Decision', stage: 'DECISION' },
    { key: 'closure', label: 'Closure', stage: 'CLOSURE' },
    { key: 'audit', label: 'Audit', stage: 'CLOSURE' },
]

export const LEGAL_BASIS_OPTIONS = [
    { value: 'Suspicion of Fraud', label: 'Suspicion of fraud' },
    { value: 'Protection of IP', label: 'Protection of IP' },
    { value: 'Compliance Breach', label: 'Compliance breach' },
    { value: 'Workplace Safety', label: 'Workplace safety' },
    { value: 'Data Exfiltration', label: 'Data exfiltration' },
    { value: 'Other', label: 'Other (specify)' },
]

export const NOTE_TYPE_OPTIONS = [
    'general',
    'interview',
    'decision',
    'proven_facts',
    'evidence',
    'compliance',
    'meeting',
    'lessons_learned',
    'root_cause',
]

export const SUBJECT_TYPE_OPTIONS = ['Employee', 'Contractor', 'Vendor', 'Third party', 'Unknown']
export const EVIDENCE_SOURCE_OPTIONS = ['SIEM', 'DLP', 'HR report', 'Email', 'Access logs', 'Physical security', 'Other']
export const INVESTIGATOR_ROLE_OPTIONS = ['Internal security', 'HR', 'Legal', 'External counsel', 'Compliance']
export const DELIVERY_METHOD_OPTIONS = ['STANDARD', 'REGISTERED_MAIL', 'HAND_DELIVERY', 'OTHER']
export const STATUS_OPTIONS = ['OPEN', 'ON_HOLD', 'CLOSED', 'ERASURE_PENDING', 'ERASED']
export const TASK_STATUS_OPTIONS = ['open', 'in_progress', 'completed']
export const JURISDICTION_OPTIONS = ['Belgium', 'Netherlands', 'Luxembourg', 'Ireland', 'EU (non-Belgium)', 'UK', 'US', 'Other']

export const LINK_RELATION_OPTIONS = [
    { value: 'RELATED', label: 'Related' },
    { value: 'DUPLICATE', label: 'Duplicate' },
    { value: 'PARENT', label: 'Parent (linked case is parent)' },
    { value: 'CHILD', label: 'Child (linked case is child)' },
]

export const LEGAL_HOLD_CHANNEL_OPTIONS = ['SECURE_PORTAL', 'EMAIL', 'IN_PERSON', 'OTHER']

export const TRIAGE_OUTCOME_OPTIONS = [
    { value: 'DISMISS', label: 'No further action' },
    { value: 'ROUTE_TO_HR', label: 'HR / Employee Relations review' },
    { value: 'OPEN_FULL_INVESTIGATION', label: 'Open investigation' },
]

export const TRIAGE_IMPACT_LEVELS = [
    { value: 1, label: 'Minimal', detail: 'Localized impact, easily reversible.' },
    { value: 2, label: 'Low', detail: 'Limited disruption or exposure.' },
    { value: 3, label: 'Moderate', detail: 'Noticeable impact, potential compliance risk.' },
    { value: 4, label: 'High', detail: 'Significant business, legal, or reputational exposure.' },
    { value: 5, label: 'Severe', detail: 'Critical harm or regulatory breach likely.' },
]

export const TRIAGE_PROBABILITY_LEVELS = [
    { value: 1, label: 'Unlikely', detail: 'Single weak signal, no corroboration.' },
    { value: 2, label: 'Possible', detail: 'Some indicators, limited evidence.' },
    { value: 3, label: 'Likely', detail: 'Multiple indicators or partial evidence.' },
    { value: 4, label: 'Very likely', detail: 'Strong signals with supporting data.' },
    { value: 5, label: 'Confirmed', detail: 'Clear evidence or admission.' },
]

export const TRIAGE_RISK_LEVELS = [
    { value: 1, label: 'Minimal' },
    { value: 2, label: 'Low' },
    { value: 3, label: 'Moderate' },
    { value: 4, label: 'High' },
    { value: 5, label: 'Severe' },
]

export const TRIAGE_CONFIDENCE_OPTIONS = ['Low', 'Medium', 'High']
export const DATA_SENSITIVITY_OPTIONS = ['Public', 'Internal', 'Confidential', 'Highly confidential']

export const RECOMMENDED_TASKS = [
    'Preserve relevant logs and access records',
    'Confirm data classification and sensitivity',
    'Notify DPO / privacy counsel',
    'Document chain-of-custody for evidence',
    'Review least-intrusive alternatives',
    'Prepare interview plan and questions',
]

export const REPORT_TEMPLATES = [
    'Thank you for your message. We are reviewing the matter and will respond with next steps.',
    'Please confirm the date/time and individuals involved so we can verify the timeline.',
    'If you have supporting files or screenshots, please upload them through the secure portal.',
    'We have received your report. You will be updated as the review progresses.',
]
