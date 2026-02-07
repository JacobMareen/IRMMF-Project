export type CaseSubject = {
    subject_type: string
    display_name: string
    reference?: string | null
    manager_name?: string | null
    created_at: string
}

export type CaseEvidence = {
    evidence_id: string
    label: string
    source: string
    link?: string | null
    evidence_hash?: string | null
    status: string
    created_at: string
}

export type CaseTask = {
    task_id: string
    title: string
    description?: string | null
    task_type?: string | null
    status: string
    due_at?: string | null
    assignee?: string | null
    created_at: string
}

export type CaseLink = {
    id: number
    case_id: string
    linked_case_id: string
    relation_type: string
    created_by?: string | null
    created_at: string
}

export type CaseLegalHold = {
    id: number
    case_id: string
    hold_id: string
    contact_name: string
    contact_email?: string | null
    contact_role?: string | null
    preservation_scope?: string | null
    delivery_channel?: string | null
    access_code?: string | null
    conflict_override_reason?: string | null
    conflict_override_by?: string | null
    document_id?: number | null
    created_by?: string | null
    created_at: string
}

export type CaseExpertAccess = {
    id: number
    case_id: string
    access_id: string
    expert_email: string
    expert_name?: string | null
    organization?: string | null
    reason?: string | null
    status: string
    granted_by?: string | null
    granted_at: string
    expires_at: string
    revoked_at?: string | null
    revoked_by?: string | null
}

export type CaseReporterMessage = {
    id: number
    case_id: string
    sender: string
    body: string
    created_at: string
}

export type CaseNote = {
    id: number
    note_type: string
    body: string
    created_by?: string | null
    flags: Record<string, unknown>
    created_at: string
}

export type CaseGateRecord = {
    gate_key: string
    status: string
    data: Record<string, unknown>
    completed_by?: string | null
    completed_at?: string | null
    updated_at: string
}

export type CaseAuditEvent = {
    event_type: string
    actor?: string | null
    message: string
    details: Record<string, unknown>
    created_at: string
}

export type CaseSanityCheck = {
    score: number
    completed: number
    total: number
    missing: string[]
    warnings: string[]
}

export type CaseSeriousCause = {
    enabled: boolean
    facts_confirmed_at?: string | null
    decision_due_at?: string | null
    dismissal_due_at?: string | null
    dismissal_recorded_at?: string | null
    reasons_sent_at?: string | null
    reasons_delivery_method?: string | null
    reasons_delivery_proof_uri?: string | null
    override_reason?: string | null
    override_by?: string | null
    missed_acknowledged_at?: string | null
    missed_acknowledged_by?: string | null
    missed_acknowledged_reason?: string | null
    missed_reason?: string | null
    decision_maker?: string | null
    updated_at: string
}

export type CaseFlag = {
    id: number
    note_id?: number | null
    flag_type: string
    terms: string[]
    status: string
    resolved_by?: string | null
    resolved_at?: string | null
    created_at: string
}

export type CaseOutcome = {
    outcome: string
    decision?: string | null
    summary?: string | null
    role_separation_override_reason?: string | null
    role_separation_override?: string | null
    role_separation_override_by?: string | null
    decision_maker?: string | null
    decision_date?: string | null
}

export type CaseDocument = {
    id: number
    doc_type: string
    version: number
    format: string
    title: string
    created_by?: string | null
    created_at: string
    content?: Record<string, unknown>
}

export type Playbook = {
    key: string
    title: string
    description: string
}

export type CaseSuggestion = {
    suggestion_id: string
    playbook_key: string
    label: string
    source: string
    description?: string | null
    status: string
    created_at: string
    updated_at: string
}

export type ConsistencyOutcome = {
    outcome: string
    count: number
    percent: number
}

export type CaseConsistency = {
    sample_size: number
    jurisdiction: string
    playbook_key?: string | null
    outcomes: ConsistencyOutcome[]
    recommendation: string
    warning?: string | null
}

export type CaseRecord = {
    case_id: string
    case_uuid: string
    title: string
    summary?: string | null
    jurisdiction: string
    vip_flag?: boolean
    urgent_dismissal?: boolean | null
    subject_suspended?: boolean | null
    evidence_locked?: boolean | null
    external_report_id?: string | null
    reporter_channel_id?: string | null
    reporter_key?: string | null
    status: string
    stage: string
    created_by?: string | null
    created_at: string
    is_anonymized: boolean
    serious_cause_enabled: boolean
    date_incident_occurred?: string | null
    date_investigation_started?: string | null
    remediation_statement?: string | null
    remediation_exported_at?: string | null
    subjects: CaseSubject[]
    evidence: CaseEvidence[]
    tasks: CaseTask[]
    notes: CaseNote[]
    gates: CaseGateRecord[]
    serious_cause?: CaseSeriousCause | null
    outcome?: CaseOutcome | null
    erasure_approved_at?: string | null
    erasure_approved_by?: string | null
    erasure_executed_at?: string | null
}
