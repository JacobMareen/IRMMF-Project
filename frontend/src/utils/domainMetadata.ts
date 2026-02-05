
export type DomainMeta = {
    id: string
    label: string
    description: string // Short summary for Radar
    longDescription?: string // Full methodology text
    capabilities?: string[] // Sub-capabilities from Taxonomy
    icon: string
    color: string
}

export const DOMAIN_METADATA: Record<string, DomainMeta> = {
    'Strategy & Governance': {
        id: 'Strategy & Governance',
        label: 'Strategy & Governance',
        description: 'Mandate, sponsorship, scope, ownership, funding, and program management.',
        longDescription: 'Establishes the structural foundation of the insider risk program. This domain ensures executive oversight, clear ownership, consistent funding, and cross-functional alignment between HR, Legal, Security, and Leadership.',
        capabilities: [
            'Organization & RACI',
            'Program Management',
            'Scope & Boundaries',
            'Executive Sponsorship'
        ],
        icon: '⚖️',
        color: '#d4af37'
    },
    'Threat Model & Operations': {
        id: 'Threat Model & Operations',
        label: 'Threat Model & Operations',
        description: 'Scenarios, deterrence, hunting, intelligence, and operational loop.',
        longDescription: 'Defines the operational engine of the program. It includes the development of realistic threat scenarios, proactive threat hunting, and the continuous learning loop that adapts defenses based on intelligence and incidents.',
        capabilities: [
            'Deterrence & Disruption',
            'Intelligence & Learning Loop',
            'Threat Hunting & Validation',
            'Threat Taxonomy & Scenarios'
        ],
        icon: '🎯',
        color: '#ef4444'
    },
    'Risk Management': {
        id: 'Risk Management',
        label: 'Risk Management',
        description: 'Inventory, assessment, treatment, and exceptions aligned to business risk.',
        longDescription: 'Focuses on identifying and quantifying insider risks associated with critical assets and processes. It aligns risk treatment decisions with the organization’s broader risk appetite and tolerance.',
        capabilities: [
            'Assessment & Analysis',
            'Inventory & Scope',
            'Risk Treatment & Exceptions',
            'Critical Process Mapping'
        ],
        icon: '📊',
        color: '#f59e0b'
    },
    'Legal, Privacy & Ethics': {
        id: 'Legal, Privacy & Ethics',
        label: 'Legal, Privacy & Ethics',
        description: 'Lawful basis, proportionality, transparency, and defensibility.',
        longDescription: 'Ensures that all insider risk activities are legally defensible, ethically sound, and privacy-preserving. It covers regulatory compliance, works council engagement, and the specific engineering required to protect employee privacy.',
        capabilities: [
            'Compliance & Policy',
            'Oversight & Safeguards',
            'Privacy Engineering',
            'Data Minimization'
        ],
        icon: '⚖️',
        color: '#8b5cf6'
    },
    'Human-Centric Culture': {
        id: 'Human-Centric Culture',
        label: 'Human-Centric Culture',
        description: 'Speak-up, fairness, training, and behavioral norms shaping insider risk.',
        longDescription: 'Addresses the human element of security. It promotes a culture of psychological safety and fairness while implementing necessary personnel security controls like vetting and offboarding protocols.',
        capabilities: [
            'Awareness & Wellbeing',
            'Human Lifecycle (Joiners/Movers/Leavers)',
            'Personnel Security',
            'Speak-Up Culture'
        ],
        icon: '🤝',
        color: '#27ae60'
    },
    'Technical Controls': {
        id: 'Technical Controls',
        label: 'Technical Controls',
        description: 'Identity, data, endpoint, network, and tooling controls for insider pathways.',
        longDescription: 'Implements the technical safeguards required to detect and prevent unauthorized activity. This includes Identity and Access Management (IAM), Data Loss Prevention (DLP), and controls for privileged users and physical assets.',
        capabilities: [
            'Data, Endpoint & Cloud Controls',
            'Identity & Access Management',
            'Logging & Telemetry Strategy',
            'Physical/OT Overlay'
        ],
        icon: '🔒',
        color: '#3b82f6'
    },
    'Behavioral Analytics & Detection': {
        id: 'Behavioral Analytics & Detection',
        label: 'Behavioral Analytics',
        description: 'Signals, detection logic, tuning, and monitoring for insider behaviors.',
        longDescription: 'Leverages data science and detection engineering to identify anomalous or high-risk behaviors. It focuses on signal fusion, reducing false positives, and mapping detections to specific threat scenarios.',
        capabilities: [
            'Detection Engineering',
            'Modeling & Detection',
            'Signal Fusion',
            'Risk Scoring Governance'
        ],
        icon: '📡',
        color: '#6366f1'
    },
    'Investigation & Response': {
        id: 'Investigation & Response',
        label: 'Investigation & Response',
        description: 'Triage, investigations, HR/legal coordination, and response execution.',
        longDescription: 'Governs the response to potential insider incidents. It ensures investigations are conducted consistently, fairly, and with appropriate cross-functional coordination (Legal/HR), from triage to remediation.',
        capabilities: [
            'Incident Action',
            'Operational Readiness',
            'Remediation & Follow-up',
            'Case Management'
        ],
        icon: '🔍',
        color: '#ec4899'
    },
    'Performance & Resilience': {
        id: 'Performance & Resilience',
        label: 'Performance & Resilience',
        description: 'Metrics, assurance, exercises, learning, and sustained effectiveness.',
        longDescription: 'Measures the effectiveness of the program and ensures resilience. It includes continuous assurance testing, KPI dashboards, and exercises (like tabletops) to validate readiness.',
        capabilities: [
            'Assurance & Metrics',
            'Resilience & Continuity',
            'Testing & Exercising',
            'Audit Readiness'
        ],
        icon: '📈',
        color: '#10b981'
    }
}

export const getDomainMeta = (domain: string): DomainMeta => {
    // 1. Clean the input string (remove "1. ", "02. ", etc.)
    const cleanLabel = domain.replace(/^\d+\.?\s*/, '').trim()
    const search = cleanLabel.toLowerCase()

    // 2. Try to find a matching key in metadata
    // Check specific aliases first? No, fuzzy match against keys.
    const key = Object.keys(DOMAIN_METADATA).find(k => {
        const normalizedKey = k.toLowerCase()
        return search.includes(normalizedKey) || normalizedKey.includes(search)
    })

    if (key) {
        return {
            ...DOMAIN_METADATA[key],
            label: cleanLabel // Use the actual clean label from data, or keep metadata label? 
            // Better to use metadata label for consistency, OR cleanLabel if we want to match source.
            // The user wants to remove the number. Metadata label is clean.
        }
    }

    // 3. Fallback: Use the cleaned label
    return {
        id: domain,
        label: cleanLabel,
        description: 'Domain analysis and controls.',
        icon: '📁',
        color: '#94a3b8'
    }
}
