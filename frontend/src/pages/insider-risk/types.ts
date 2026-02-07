export type Recommendation = {
    rec_id: string
    assessment_id?: string
    title: string
    category: string
    priority: string
    status?: string
    description: string
    rationale?: string
    implementation_steps?: {
        steps: Array<{
            step: number
            action: string
            owner: string
        }>
    }
    effort?: string
    timeline?: string
    subcategory?: string
    assigned_to?: string
    due_date?: string
    custom_notes?: string
    triggered_by?: {
        axes?: string[]
        risks?: string[]
    }
}

export type PolicySection = {
    title: string
    intent?: string
    bullets?: string[]
    owner?: string
    artifacts?: string[]
}

export type InsiderRiskPolicy = {
    status: string
    version: string
    owner: string
    approval: string
    scope: string
    last_reviewed?: string
    next_review?: string
    principles: string[]
    sections: PolicySection[]
    is_template?: boolean
}

export type ControlStatus = 'planned' | 'in_progress' | 'implemented' | 'monitored'

export type Control = {
    control_id: string
    title?: string
    domain: string
    objective?: string
    status: ControlStatus
    owner?: string
    frequency?: string
    evidence?: string
    last_reviewed?: string
    next_review?: string
    linked_actions?: string[]
    linked_rec_ids?: string[]
    linked_categories?: string[]
}

export type InsiderRiskProgramView = 'overview' | 'policy' | 'controls' | 'actions'
