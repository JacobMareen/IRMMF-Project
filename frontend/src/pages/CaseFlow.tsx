import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { apiFetch, apiBlob, API_BASE } from '../lib/api'
import './CaseFlow.css'

type CaseSubject = {
  subject_type: string
  display_name: string
  reference?: string | null
  manager_name?: string | null
  created_at: string
}

type CaseEvidence = {
  evidence_id: string
  label: string
  source: string
  link?: string | null
  evidence_hash?: string | null
  status: string
  created_at: string
}

type CaseTask = {
  task_id: string
  title: string
  description?: string | null
  task_type?: string | null
  status: string
  due_at?: string | null
  assignee?: string | null
  created_at: string
}

type CaseLink = {
  id: number
  case_id: string
  linked_case_id: string
  relation_type: string
  created_by?: string | null
  created_at: string
}

type CaseLegalHold = {
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

type CaseExpertAccess = {
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

type CaseReporterMessage = {
  id: number
  case_id: string
  sender: string
  body: string
  created_at: string
}

type CaseNote = {
  id: number
  note_type: string
  body: string
  created_by?: string | null
  flags: Record<string, unknown>
  created_at: string
}

type CaseGateRecord = {
  gate_key: string
  status: string
  data: Record<string, unknown>
  completed_by?: string | null
  completed_at?: string | null
  updated_at: string
}

type CaseAuditEvent = {
  event_type: string
  actor?: string | null
  message: string
  details: Record<string, unknown>
  created_at: string
}

type CaseSanityCheck = {
  score: number
  completed: number
  total: number
  missing: string[]
  warnings: string[]
}
type CaseSeriousCause = {
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
  updated_at: string
}

type CaseFlag = {
  id: number
  note_id?: number | null
  flag_type: string
  terms: string[]
  status: string
  resolved_by?: string | null
  resolved_at?: string | null
  created_at: string
}

type CaseOutcome = {
  outcome: string
  decision?: string | null
  summary?: string | null
  role_separation_override_reason?: string | null
  role_separation_override_by?: string | null
}

type CaseDocument = {
  id: number
  doc_type: string
  version: number
  format: string
  title: string
  created_by?: string | null
  created_at: string
}

type Playbook = {
  key: string
  title: string
  description: string
}

type CaseSuggestion = {
  suggestion_id: string
  playbook_key: string
  label: string
  source: string
  description?: string | null
  status: string
  created_at: string
  updated_at: string
}

type ConsistencyOutcome = {
  outcome: string
  count: number
  percent: number
}

type CaseConsistency = {
  sample_size: number
  jurisdiction: string
  playbook_key?: string | null
  outcomes: ConsistencyOutcome[]
  recommendation: string
  warning?: string | null
}

type CaseRecord = {
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
}

const STEPS = [
  { key: 'intake', label: 'Intake', stage: 'INTAKE' },
  { key: 'legitimacy', label: 'Legitimacy', stage: 'LEGITIMACY_GATE' },
  { key: 'credentialing', label: 'Credentialing', stage: 'CREDENTIALING' },
  { key: 'investigation', label: 'Investigation', stage: 'INVESTIGATION' },
  { key: 'adversarial', label: 'Adversarial', stage: 'ADVERSARIAL_DEBATE' },
  { key: 'decision', label: 'Decision', stage: 'DECISION' },
  { key: 'closure', label: 'Closure', stage: 'CLOSURE' },
  { key: 'audit', label: 'Audit', stage: 'CLOSURE' },
]

const LEGAL_BASIS_OPTIONS = [
  { value: 'Suspicion of Fraud', label: 'Suspicion of fraud' },
  { value: 'Protection of IP', label: 'Protection of IP' },
  { value: 'Compliance Breach', label: 'Compliance breach' },
  { value: 'Workplace Safety', label: 'Workplace safety' },
  { value: 'Data Exfiltration', label: 'Data exfiltration' },
  { value: 'Other', label: 'Other (specify)' },
]

const NOTE_TYPE_OPTIONS = [
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
const SUBJECT_TYPE_OPTIONS = ['Employee', 'Contractor', 'Vendor', 'Third party', 'Unknown']
const EVIDENCE_SOURCE_OPTIONS = ['SIEM', 'DLP', 'HR report', 'Email', 'Access logs', 'Physical security', 'Other']
const INVESTIGATOR_ROLE_OPTIONS = ['Internal security', 'HR', 'Legal', 'External counsel', 'Compliance']
const DELIVERY_METHOD_OPTIONS = ['STANDARD', 'REGISTERED_MAIL', 'HAND_DELIVERY', 'OTHER']
const STATUS_OPTIONS = ['OPEN', 'ON_HOLD', 'CLOSED', 'ERASURE_PENDING', 'ERASED']
const TASK_STATUS_OPTIONS = ['open', 'in_progress', 'completed']
const JURISDICTION_OPTIONS = ['Belgium', 'Netherlands', 'Luxembourg', 'Ireland', 'EU (non-Belgium)', 'UK', 'US', 'Other']
const LINK_RELATION_OPTIONS = [
  { value: 'RELATED', label: 'Related' },
  { value: 'DUPLICATE', label: 'Duplicate' },
  { value: 'PARENT', label: 'Parent (linked case is parent)' },
  { value: 'CHILD', label: 'Child (linked case is child)' },
]
const LEGAL_HOLD_CHANNEL_OPTIONS = ['SECURE_PORTAL', 'EMAIL', 'IN_PERSON', 'OTHER']
const TRIAGE_OUTCOME_OPTIONS = [
  { value: 'DISMISS', label: 'No further action' },
  { value: 'ROUTE_TO_HR', label: 'HR / Employee Relations review' },
  { value: 'OPEN_FULL_INVESTIGATION', label: 'Open investigation' },
]
const TRIAGE_IMPACT_LEVELS = [
  { value: 1, label: 'Minimal', detail: 'Localized impact, easily reversible.' },
  { value: 2, label: 'Low', detail: 'Limited disruption or exposure.' },
  { value: 3, label: 'Moderate', detail: 'Noticeable impact, potential compliance risk.' },
  { value: 4, label: 'High', detail: 'Significant business, legal, or reputational exposure.' },
  { value: 5, label: 'Severe', detail: 'Critical harm or regulatory breach likely.' },
]
const TRIAGE_PROBABILITY_LEVELS = [
  { value: 1, label: 'Unlikely', detail: 'Single weak signal, no corroboration.' },
  { value: 2, label: 'Possible', detail: 'Some indicators, limited evidence.' },
  { value: 3, label: 'Likely', detail: 'Multiple indicators or partial evidence.' },
  { value: 4, label: 'Very likely', detail: 'Strong signals with supporting data.' },
  { value: 5, label: 'Confirmed', detail: 'Clear evidence or admission.' },
]
const TRIAGE_RISK_LEVELS = [
  { value: 1, label: 'Minimal' },
  { value: 2, label: 'Low' },
  { value: 3, label: 'Moderate' },
  { value: 4, label: 'High' },
  { value: 5, label: 'Severe' },
]
const TRIAGE_CONFIDENCE_OPTIONS = ['Low', 'Medium', 'High']
const DATA_SENSITIVITY_OPTIONS = ['Public', 'Internal', 'Confidential', 'Highly confidential']
const RECOMMENDED_TASKS = [
  'Preserve relevant logs and access records',
  'Confirm data classification and sensitivity',
  'Notify DPO / privacy counsel',
  'Document chain-of-custody for evidence',
  'Review least-intrusive alternatives',
  'Prepare interview plan and questions',
]
const REPORT_TEMPLATES = [
  'Thank you for your message. We are reviewing the matter and will respond with next steps.',
  'Please confirm the date/time and individuals involved so we can verify the timeline.',
  'If you have supporting files or screenshots, please upload them through the secure portal.',
  'We have received your report. You will be updated as the review progresses.',
]

const CaseFlow = () => {
  const { caseId, step = 'intake' } = useParams()
  const navigate = useNavigate()
  const currentStep = useMemo(() => STEPS.find((s) => s.key === step) || STEPS[0], [step])
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const computeRiskScore = (impact: number, probability: number) =>
    Math.min(5, Math.max(1, Math.ceil((impact * probability) / 5)))

  const [caseData, setCaseData] = useState<CaseRecord | null>(null)
  const [status, setStatus] = useState('')
  const [guidanceOpen, setGuidanceOpen] = useState<Record<string, boolean>>({})
  const [playbooks, setPlaybooks] = useState<Playbook[]>([])
  const [suggestions, setSuggestions] = useState<CaseSuggestion[]>([])
  const [documents, setDocuments] = useState<CaseDocument[]>([])
  const [flags, setFlags] = useState<CaseFlag[]>([])
  const [links, setLinks] = useState<CaseLink[]>([])
  const [linkDraft, setLinkDraft] = useState({ linked_case_id: '', relation_type: 'RELATED' })
  const [linkStatus, setLinkStatus] = useState('')
  const [legalHolds, setLegalHolds] = useState<CaseLegalHold[]>([])
  const [legalHoldDraft, setLegalHoldDraft] = useState({
    contact_name: '',
    contact_email: '',
    contact_role: '',
    preservation_scope: '',
    delivery_channel: 'SECURE_PORTAL',
    access_code: '',
    conflict_override_reason: '',
  })
  const [legalHoldStatus, setLegalHoldStatus] = useState('')
  const [expertAccess, setExpertAccess] = useState<CaseExpertAccess[]>([])
  const [expertDraft, setExpertDraft] = useState({
    expert_email: '',
    expert_name: '',
    organization: '',
    reason: '',
  })
  const [expertStatus, setExpertStatus] = useState('')
  const [reporterMessages, setReporterMessages] = useState<CaseReporterMessage[]>([])
  const [reporterReply, setReporterReply] = useState('')
  const [piiUnlocked, setPiiUnlocked] = useState(false)
  const [breakGlassOpen, setBreakGlassOpen] = useState(false)
  const [breakGlassReason, setBreakGlassReason] = useState('')
  const [breakGlassDuration, setBreakGlassDuration] = useState(60)
  const [breakGlassExpiresAt, setBreakGlassExpiresAt] = useState<number | null>(null)
  const [auditEvents, setAuditEvents] = useState<CaseAuditEvent[]>([])
  const [auditActorFilter, setAuditActorFilter] = useState('')
  const [auditFromFilter, setAuditFromFilter] = useState('')
  const [auditToFilter, setAuditToFilter] = useState('')
  const [sanityCheck, setSanityCheck] = useState<CaseSanityCheck | null>(null)
  const [docFormat, setDocFormat] = useState(() => localStorage.getItem('case_doc_format') || 'txt')
  const [decisionOutcome, setDecisionOutcome] = useState('NO_SANCTION')
  const [decisionSummary, setDecisionSummary] = useState('')
  const [decisionOverrideReason, setDecisionOverrideReason] = useState('')
  const [redactionInput, setRedactionInput] = useState('')
  const [remediationInput, setRemediationInput] = useState('')
  const [remediationFormat, setRemediationFormat] = useState('json')
  const [consistency, setConsistency] = useState<CaseConsistency | null>(null)
  const [transitionBlockers, setTransitionBlockers] = useState<{ code: string; message: string }[]>([])
  const [transitionModalOpen, setTransitionModalOpen] = useState(false)
  const [caseMetaDraft, setCaseMetaDraft] = useState({
    title: '',
    summary: '',
    jurisdiction: '',
    jurisdiction_other: '',
    vip_flag: false,
    urgent_dismissal: false,
    subject_suspended: false,
    external_report_id: '',
    reporter_channel_id: '',
    reporter_key: '',
  })
  const [showSuspensionModal, setShowSuspensionModal] = useState(false)
  const [suspensionOverride, setSuspensionOverride] = useState(false)
  const [legitimacyGate, setLegitimacyGate] = useState({
    legal_basis: '',
    legal_basis_other: '',
    trigger_summary: '',
    proportionality_confirmed: false,
    less_intrusive_steps: '',
    mandate_owner: '',
    mandate_date: '',
  })
  const [triageGate, setTriageGate] = useState({
    impact: 3,
    probability: 3,
    risk_score: 3,
    outcome: '',
    notes: '',
    trigger_source: '',
    business_impact: '',
    exposure_summary: '',
    data_sensitivity: '',
    stakeholders: '',
    confidence_level: '',
    recommended_actions: '',
  })
  const [credentialingGate, setCredentialingGate] = useState({
    investigator_name: '',
    investigator_role: '',
    licensed: false,
    license_id: '',
    conflict_check_passed: false,
    conflict_override_reason: '',
    authorizer: '',
    authorization_date: '',
  })
  const [adversarialGate, setAdversarialGate] = useState({
    invitation_sent: false,
    invitation_date: '',
    rights_acknowledged: false,
    representative_present: '',
    interview_summary: '',
  })
  const [worksCouncilGate, setWorksCouncilGate] = useState({
    monitoring: false,
    approval_document_uri: '',
    approval_received_at: '',
    approval_notes: '',
  })
  const [legalGate, setLegalGate] = useState({
    approved_at: '',
    approval_note: '',
  })
  const [impactAnalysis, setImpactAnalysis] = useState({
    estimated_loss: '',
    regulation_breached: '',
    operational_impact: '',
    reputational_impact: '',
    people_impact: '',
    financial_impact: '',
  })
  const [subjectDraft, setSubjectDraft] = useState({
    subject_type: '',
    display_name: '',
    reference: '',
    manager_name: '',
  })
  const [evidenceDraft, setEvidenceDraft] = useState({
    label: '',
    source: '',
    link: '',
    evidence_hash: '',
  })
  const [taskDraft, setTaskDraft] = useState({
    title: '',
    assignee: '',
  })
  const [noteDraft, setNoteDraft] = useState({
    note_type: 'general',
    body: '',
  })
  const [lessonsDraft, setLessonsDraft] = useState({
    root_cause: '',
    action_items: '',
  })
  const [seriousEnabledDraft, setSeriousEnabledDraft] = useState(false)
  const [meetingDraft, setMeetingDraft] = useState({
    meeting_date: '',
    attendees: '',
    summary: '',
    minutes: '',
  })
  const [seriousDraft, setSeriousDraft] = useState({
    date_incident_occurred: '',
    date_investigation_started: '',
    decision_maker: '',
    facts_confirmed_at: '',
    dismissal_recorded_at: '',
    reasons_sent_at: '',
    reasons_delivery_method: '',
    reasons_delivery_proof_uri: '',
    missed_reason: '',
  })

  const toLocalInput = (value?: string | null) => (value ? value.slice(0, 16) : '')
  const toIso = (value: string) => (value ? new Date(value).toISOString() : null)
  const relationLabel = (value: string) =>
    LINK_RELATION_OPTIONS.find((option) => option.value === value)?.label || value
  const normalizeName = (value?: string | null) => (value || '').trim().toLowerCase()
  const breakGlassKey = caseId ? `break_glass_${caseId}` : ''
  const maskFieldValue = (value?: string | null) => {
    if (piiUnlocked) return value || ''
    return value ? 'Hidden' : ''
  }
  const maskText = (value?: string | null, fallback = 'Hidden') => (piiUnlocked ? value || '' : fallback)
  const maskIndexed = (value: string, index: number, label: string) =>
    piiUnlocked ? value : `${label} ${index + 1}`
  const investigatorName = credentialingGate.investigator_name
  const decisionMakerName = seriousDraft.decision_maker
  const roleSeparationConflicts: string[] = []
  if (
    normalizeName(decisionMakerName) &&
    normalizeName(decisionMakerName) === normalizeName(investigatorName)
  ) {
    roleSeparationConflicts.push('Decision maker matches investigator')
  }
  if (normalizeName(investigatorName) && normalizeName(investigatorName) === normalizeName(currentUser)) {
    roleSeparationConflicts.push('Investigator cannot record the decision')
  }
  const hasRoleSeparationConflict = roleSeparationConflicts.length > 0
  const isBelgiumCase = useMemo(() => {
    const jurisdiction = (caseData?.jurisdiction || '').trim().toLowerCase()
    if (!jurisdiction) return false
    if (jurisdiction === 'be' || jurisdiction === 'belgium' || jurisdiction === 'belgique') return true
    return jurisdiction.includes('belgium') || jurisdiction.includes('belgique')
  }, [caseData?.jurisdiction])
  const remediationBlocked = !caseData?.outcome || caseData.outcome.outcome === 'NO_SANCTION'
  const isNetherlandsDraft = useMemo(() => {
    const base = (caseMetaDraft.jurisdiction || '').trim().toLowerCase()
    const other = (caseMetaDraft.jurisdiction_other || '').trim().toLowerCase()
    if (base === 'netherlands') return true
    return base === 'other' ? other.includes('netherlands') || other === 'nl' : base.includes('netherlands')
  }, [caseMetaDraft.jurisdiction, caseMetaDraft.jurisdiction_other])
  const needsSuspensionWarning =
    isNetherlandsDraft && caseMetaDraft.urgent_dismissal && !caseMetaDraft.subject_suspended
  const isWorksCouncilJurisdiction = useMemo(() => {
    const jurisdiction = (caseData?.jurisdiction || '').trim().toLowerCase()
    if (!jurisdiction) return false
    return (
      jurisdiction === 'germany' ||
      jurisdiction === 'de' ||
      jurisdiction.includes('germany') ||
      jurisdiction === 'france' ||
      jurisdiction === 'fr' ||
      jurisdiction.includes('france')
    )
  }, [caseData?.jurisdiction])
  const taskTotal = caseData?.tasks.length || 0
  const taskCompleted = caseData?.tasks.filter((task) => task.status === 'completed').length || 0
  const taskProgress = taskTotal ? Math.round((taskCompleted / taskTotal) * 100) : 0
  const reportSignals = {
    triage: !!caseData?.gates.find((gate) => gate.gate_key === 'triage'),
    impact: !!caseData?.gates.find((gate) => gate.gate_key === 'impact_analysis'),
    decision: !!caseData?.outcome,
    lessons: !!caseData?.notes.find((note) => note.note_type === 'lessons_learned'),
  }

  const loadCase = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setCaseData(data))
      .catch(() => setCaseData(null))
  }

  const loadPlaybooks = () => {
    apiFetch(`/cases/playbooks`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: Playbook[]) => setPlaybooks(data || []))
      .catch(() => setPlaybooks([]))
  }

  const loadSuggestions = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/suggestions`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: CaseSuggestion[]) => setSuggestions(data || []))
      .catch(() => setSuggestions([]))
  }

  const loadDocuments = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/documents`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: CaseDocument[]) => setDocuments(data || []))
      .catch(() => setDocuments([]))
  }

  const loadFlags = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/flags`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: CaseFlag[]) => setFlags(data || []))
      .catch(() => setFlags([]))
  }

  const loadLinks = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/links`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: CaseLink[]) => setLinks(data || []))
      .catch(() => setLinks([]))
  }

  const loadLegalHolds = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/legal-holds`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: CaseLegalHold[]) => setLegalHolds(data || []))
      .catch(() => setLegalHolds([]))
  }

  const loadExpertAccess = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/experts`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: CaseExpertAccess[]) => setExpertAccess(data || []))
      .catch(() => setExpertAccess([]))
  }

  const loadReporterMessages = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/reporter-messages`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: CaseReporterMessage[]) => setReporterMessages(data || []))
      .catch(() => setReporterMessages([]))
  }

  const loadAuditEvents = (actorOverride?: string) => {
    if (!caseId) return
    const actor = (actorOverride ?? auditActorFilter).trim()
    const params = new URLSearchParams({ case_id: caseId })
    if (actor) {
      params.set('actor', actor)
    }
    apiFetch(`/audit?${params.toString()}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: CaseAuditEvent[]) => setAuditEvents(data || []))
      .catch(() => setAuditEvents([]))
  }

  const loadSanityCheck = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/sanity-check`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data: CaseSanityCheck | null) => setSanityCheck(data))
      .catch(() => setSanityCheck(null))
  }

  useEffect(() => {
    loadCase()
    loadPlaybooks()
    loadSuggestions()
    loadDocuments()
    loadFlags()
    loadLinks()
    loadLegalHolds()
    loadExpertAccess()
    loadReporterMessages()
    loadAuditEvents()
  }, [caseId])

  useEffect(() => {
    if (!caseId) return
    if (!breakGlassKey) return
    const stored = localStorage.getItem(breakGlassKey)
    if (!stored) {
      setPiiUnlocked(false)
      setBreakGlassExpiresAt(null)
      return
    }
    try {
      const parsed = JSON.parse(stored) as { expiresAt?: number }
      if (parsed.expiresAt && parsed.expiresAt > Date.now()) {
        setPiiUnlocked(true)
        setBreakGlassExpiresAt(parsed.expiresAt)
      } else {
        localStorage.removeItem(breakGlassKey)
        setPiiUnlocked(false)
        setBreakGlassExpiresAt(null)
      }
    } catch {
      localStorage.removeItem(breakGlassKey)
      setPiiUnlocked(false)
      setBreakGlassExpiresAt(null)
    }
  }, [caseId, breakGlassKey])

  useEffect(() => {
    if (!breakGlassExpiresAt || !breakGlassKey) return
    const timer = window.setInterval(() => {
      if (Date.now() > breakGlassExpiresAt) {
        localStorage.removeItem(breakGlassKey)
        setPiiUnlocked(false)
        setBreakGlassExpiresAt(null)
      }
    }, 30000)
    return () => window.clearInterval(timer)
  }, [breakGlassExpiresAt, breakGlassKey])

  const filteredAuditEvents = useMemo(() => {
    if (!auditFromFilter && !auditToFilter) {
      return auditEvents
    }
    const start = auditFromFilter ? new Date(`${auditFromFilter}T00:00:00`) : null
    const end = auditToFilter ? new Date(`${auditToFilter}T23:59:59`) : null
    return auditEvents.filter((event) => {
      const eventDate = new Date(event.created_at)
      if (start && eventDate < start) return false
      if (end && eventDate > end) return false
      return true
    })
  }, [auditEvents, auditFromFilter, auditToFilter])

  const formatAuditChanges = (details?: Record<string, unknown>) => {
    if (!details) return []
    const base =
      typeof details.changes === 'object' && details.changes !== null
        ? (details.changes as Record<string, unknown>)
        : details
    return Object.entries(base)
      .filter(([key]) => key !== '_context')
      .map(([key, value]) => {
        if (value && typeof value === 'object' && 'from' in value && 'to' in value) {
          const entry = value as { from?: string | number | boolean | null; to?: string | number | boolean | null }
          return `${key}: ${entry.from ?? '—'} → ${entry.to ?? '—'}`
        }
        return `${key}: ${typeof value === 'string' ? value : JSON.stringify(value)}`
      })
  }

  useEffect(() => {
    if (!caseData) return

    const matchJurisdiction = JURISDICTION_OPTIONS.includes(caseData.jurisdiction)
    setCaseMetaDraft({
      title: caseData.title,
      summary: caseData.summary || '',
      jurisdiction: matchJurisdiction ? caseData.jurisdiction : 'Other',
      jurisdiction_other: matchJurisdiction ? '' : caseData.jurisdiction,
      vip_flag: !!caseData.vip_flag,
      urgent_dismissal: !!caseData.urgent_dismissal,
      subject_suspended: !!caseData.subject_suspended,
      external_report_id: caseData.external_report_id || '',
      reporter_channel_id: caseData.reporter_channel_id || '',
      reporter_key: caseData.reporter_key || '',
    })
    setSeriousEnabledDraft(caseData.serious_cause_enabled)
    setRemediationInput(caseData.remediation_statement || '')

    if (caseData.outcome?.outcome) {
      setDecisionOutcome(caseData.outcome.outcome)
    }
    if (caseData.outcome?.summary) {
      setDecisionSummary(caseData.outcome.summary)
    }
    if (caseData.outcome?.role_separation_override_reason) {
      setDecisionOverrideReason(caseData.outcome.role_separation_override_reason)
    } else {
      setDecisionOverrideReason('')
    }

    const legitimacy = caseData.gates.find((gate) => gate.gate_key === 'legitimacy')
    if (legitimacy?.data) {
      const legalBasisValue = (legitimacy.data.legal_basis as string | undefined) || ''
      const match = LEGAL_BASIS_OPTIONS.some((option) => option.value === legalBasisValue)
      setLegitimacyGate({
        legal_basis: legalBasisValue ? (match ? legalBasisValue : 'Other') : '',
        legal_basis_other: match ? '' : legalBasisValue,
        trigger_summary: (legitimacy.data.trigger_summary as string | undefined) || '',
        proportionality_confirmed: !!legitimacy.data.proportionality_confirmed,
        less_intrusive_steps: (legitimacy.data.less_intrusive_steps as string | undefined) || '',
        mandate_owner: (legitimacy.data.mandate_owner as string | undefined) || '',
        mandate_date: (legitimacy.data.mandate_date as string | undefined) || '',
      })
    }

    const triage = caseData.gates.find((gate) => gate.gate_key === 'triage')
    if (triage?.data) {
      setTriageGate({
        impact: Number(triage.data.impact || 3),
        probability: Number(triage.data.probability || 3),
        risk_score: Number(triage.data.risk_score || 3),
        outcome: (triage.data.outcome as string | undefined) || '',
        notes: (triage.data.notes as string | undefined) || '',
        trigger_source: (triage.data.trigger_source as string | undefined) || '',
        business_impact: (triage.data.business_impact as string | undefined) || '',
        exposure_summary: (triage.data.exposure_summary as string | undefined) || '',
        data_sensitivity: (triage.data.data_sensitivity as string | undefined) || '',
        stakeholders: (triage.data.stakeholders as string | undefined) || '',
        confidence_level: (triage.data.confidence_level as string | undefined) || '',
        recommended_actions: (triage.data.recommended_actions as string | undefined) || '',
      })
    }

    const credentialing = caseData.gates.find((gate) => gate.gate_key === 'credentialing')
    if (credentialing?.data) {
      setCredentialingGate({
        investigator_name: (credentialing.data.investigator_name as string | undefined) || '',
        investigator_role: (credentialing.data.investigator_role as string | undefined) || '',
        licensed: !!credentialing.data.licensed,
        license_id: (credentialing.data.license_id as string | undefined) || '',
        conflict_check_passed: !!credentialing.data.conflict_check_passed,
        conflict_override_reason: (credentialing.data.conflict_override_reason as string | undefined) || '',
        authorizer: (credentialing.data.authorizer as string | undefined) || '',
        authorization_date: (credentialing.data.authorization_date as string | undefined) || '',
      })
    }

    const adversarial = caseData.gates.find((gate) => gate.gate_key === 'adversarial')
    if (adversarial?.data) {
      setAdversarialGate({
        invitation_sent: !!adversarial.data.invitation_sent,
        invitation_date: (adversarial.data.invitation_date as string | undefined) || '',
        rights_acknowledged: !!adversarial.data.rights_acknowledged,
        representative_present: (adversarial.data.representative_present as string | undefined) || '',
        interview_summary: (adversarial.data.interview_summary as string | undefined) || '',
      })
    }

    const works = caseData.gates.find((gate) => gate.gate_key === 'works_council')
    if (works?.data) {
      setWorksCouncilGate({
        monitoring: !!works.data.monitoring,
        approval_document_uri: (works.data.approval_document_uri as string | undefined) || '',
        approval_received_at: toLocalInput(works.data.approval_received_at as string | undefined),
        approval_notes: (works.data.approval_notes as string | undefined) || '',
      })
    } else {
      setWorksCouncilGate({
        monitoring: false,
        approval_document_uri: '',
        approval_received_at: '',
        approval_notes: '',
      })
    }

    const impact = caseData.gates.find((gate) => gate.gate_key === 'impact_analysis')
    if (impact?.data) {
      const lossValue = impact.data.estimated_loss
      setImpactAnalysis({
        estimated_loss: lossValue !== null && lossValue !== undefined ? String(lossValue) : '',
        regulation_breached: (impact.data.regulation_breached as string | undefined) || '',
        operational_impact: (impact.data.operational_impact as string | undefined) || '',
        reputational_impact: (impact.data.reputational_impact as string | undefined) || '',
        people_impact: (impact.data.people_impact as string | undefined) || '',
        financial_impact: (impact.data.financial_impact as string | undefined) || '',
      })
    }

    const legal = caseData.gates.find((gate) => gate.gate_key === 'legal')
    if (legal?.data) {
      setLegalGate({
        approved_at: toLocalInput(legal.data.approved_at as string | undefined),
        approval_note: (legal.data.approval_note as string | undefined) || '',
      })
    } else {
      setLegalGate({ approved_at: '', approval_note: '' })
    }
  }, [caseData])

  useEffect(() => {
    if (currentUser && !credentialingGate.investigator_name) {
      setCredentialingGate((prev) => ({ ...prev, investigator_name: currentUser }))
    }
  }, [currentUser, credentialingGate.investigator_name])

  useEffect(() => {
    setSuspensionOverride(false)
  }, [caseMetaDraft.urgent_dismissal, caseMetaDraft.subject_suspended, caseMetaDraft.jurisdiction, caseMetaDraft.jurisdiction_other])

  const goToStep = (key: string) => {
    if (!caseId) return
    navigate(`/cases/${caseId}/flow/${key}`)
  }

  const nextStep = () => {
    const idx = STEPS.findIndex((s) => s.key === currentStep.key)
    if (idx < STEPS.length - 1 && caseId) {
      const next = STEPS[idx + 1]
      apiFetch(`/cases/${caseId}/stage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stage: next.stage }),
      })
        .then(async (res) => {
          if (!res.ok) {
            const payload = await res.json().catch(() => null)
            const detail = payload?.detail
            if (detail?.blockers?.length) {
              setTransitionBlockers(detail.blockers)
              setTransitionModalOpen(true)
            }
            setStatus(detail?.message || payload?.detail || 'Blocked. Complete required step.')
            return null
          }
          return res.json()
        })
        .then((data) => {
          if (data) {
            setStatus('')
            setTransitionBlockers([])
            setTransitionModalOpen(false)
            goToStep(next.key)
          }
        })
        .catch(() => setStatus('Unable to advance stage.'))
    }
  }

  const toggleGuidance = () => {
    setGuidanceOpen((prev) => ({ ...prev, [currentStep.key]: !prev[currentStep.key] }))
  }

  const performSaveCaseDetails = (force = false) => {
    if (!caseId) return
    const jurisdictionValue =
      caseMetaDraft.jurisdiction === 'Other'
        ? caseMetaDraft.jurisdiction_other.trim()
        : caseMetaDraft.jurisdiction
    if (!caseMetaDraft.title.trim()) {
      setStatus('Case title cannot be empty.')
      return
    }
    if (!jurisdictionValue) {
      setStatus('Select a jurisdiction.')
      return
    }
    if (needsSuspensionWarning && !force && !suspensionOverride) {
      setShowSuspensionModal(true)
      return
    }
    apiFetch(`/cases/${caseId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: caseMetaDraft.title.trim(),
        summary: caseMetaDraft.summary.trim() || null,
        jurisdiction: jurisdictionValue,
        vip_flag: caseMetaDraft.vip_flag,
        urgent_dismissal: caseMetaDraft.urgent_dismissal,
        subject_suspended: caseMetaDraft.subject_suspended,
        external_report_id: caseMetaDraft.external_report_id.trim() || null,
        reporter_channel_id: caseMetaDraft.reporter_channel_id.trim() || null,
        reporter_key: caseMetaDraft.reporter_key.trim() || null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        if (needsSuspensionWarning) {
          setSuspensionOverride(true)
        }
        setStatus('Case details saved.')
        loadCase()
      })
      .catch(() => setStatus('Unable to save case details.'))
  }

  const saveCaseDetails = () => performSaveCaseDetails(false)

  const saveGate = (gateKey: string, payload: Record<string, unknown>) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/gates/${gateKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text()
          let message = text || 'Unable to save gate.'
          try {
            const data = JSON.parse(text)
            if (data?.detail) message = data.detail
          } catch {
            // keep raw text
          }
          throw new Error(message)
        }
        return res.json()
      })
      .then(() => {
        setStatus('Saved.')
        loadCase()
      })
      .catch((err) => setStatus(err.message || 'Unable to save gate.'))
  }

  const createTask = (title: string, assignee?: string) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title.trim(),
        assignee: assignee?.trim() || null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCase())
      .catch(() => setStatus('Failed to add task.'))
  }

  const addSubject = () => {
    if (!caseId) return
    if (!subjectDraft.subject_type.trim() || !subjectDraft.display_name.trim()) {
      setStatus('Subject type and name are required.')
      return
    }
    apiFetch(`/cases/${caseId}/subjects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject_type: subjectDraft.subject_type.trim(),
          display_name: subjectDraft.display_name.trim(),
          reference: subjectDraft.reference.trim() || null,
          manager_name: subjectDraft.manager_name.trim() || null,
        }),
      })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setSubjectDraft({ subject_type: '', display_name: '', reference: '', manager_name: '' })
        loadCase()
      })
      .catch(() => setStatus('Failed to add subject.'))
  }

  const addLink = () => {
    if (!caseId) return
    if (!linkDraft.linked_case_id.trim()) {
      setLinkStatus('Linked case ID is required.')
      return
    }
    setLinkStatus('Linking case...')
    apiFetch(`/cases/${caseId}/links`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        linked_case_id: linkDraft.linked_case_id.trim(),
        relation_type: linkDraft.relation_type,
      }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text()
          let message = text || 'Failed to link case.'
          try {
            const data = JSON.parse(text)
            if (data?.detail) message = data.detail
          } catch {
            // keep raw text
          }
          throw new Error(message)
        }
        return res.json()
      })
      .then(() => {
        setLinkStatus('Case linked.')
        setLinkDraft({ linked_case_id: '', relation_type: 'RELATED' })
        loadLinks()
      })
      .catch((err) => setLinkStatus(err.message || 'Failed to link case.'))
  }

  const removeLink = (linkId: number) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/links/${linkId}`, { method: 'DELETE' })
      .then((res) => {
        if (!res.ok) {
          throw new Error('Failed to unlink case.')
        }
        return res.json()
      })
      .then(() => {
        setLinkStatus('Case link removed.')
        loadLinks()
      })
      .catch((err) => setLinkStatus(err.message || 'Failed to unlink case.'))
  }

  const createLegalHold = () => {
    if (!caseId) return
    if (!legalHoldDraft.contact_name.trim()) {
      setLegalHoldStatus('Contact name is required.')
      return
    }
    setLegalHoldStatus('Generating legal hold...')
    apiFetch(`/cases/${caseId}/legal-hold`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contact_name: legalHoldDraft.contact_name.trim(),
        contact_email: legalHoldDraft.contact_email.trim() || null,
        contact_role: legalHoldDraft.contact_role.trim() || null,
        preservation_scope: legalHoldDraft.preservation_scope.trim() || null,
        delivery_channel: legalHoldDraft.delivery_channel,
        access_code: legalHoldDraft.access_code.trim() || null,
        conflict_override_reason: legalHoldDraft.conflict_override_reason.trim() || null,
      }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text()
          let message = text || 'Legal hold failed.'
          try {
            const data = JSON.parse(text)
            if (data?.detail) message = data.detail
          } catch {
            // keep raw text
          }
          throw new Error(message)
        }
        return res.json()
      })
      .then(() => {
        setLegalHoldStatus('Legal hold generated.')
        setLegalHoldDraft({
          contact_name: '',
          contact_email: '',
          contact_role: '',
          preservation_scope: '',
          delivery_channel: 'SECURE_PORTAL',
          access_code: '',
          conflict_override_reason: '',
        })
        loadLegalHolds()
        loadDocuments()
      })
      .catch((err) => setLegalHoldStatus(err.message || 'Legal hold failed.'))
  }

  const grantExpertAccess = () => {
    if (!caseId) return
    if (!expertDraft.expert_email.trim()) {
      setExpertStatus('Expert email is required.')
      return
    }
    setExpertStatus('Granting access...')
    apiFetch(`/cases/${caseId}/experts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        expert_email: expertDraft.expert_email.trim(),
        expert_name: expertDraft.expert_name.trim() || null,
        organization: expertDraft.organization.trim() || null,
        reason: expertDraft.reason.trim() || null,
      }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text()
          let message = text || 'Failed to grant access.'
          try {
            const data = JSON.parse(text)
            if (data?.detail) message = data.detail
          } catch {
            // keep raw text
          }
          throw new Error(message)
        }
        return res.json()
      })
      .then(() => {
        setExpertStatus('Access granted for 48 hours.')
        setExpertDraft({ expert_email: '', expert_name: '', organization: '', reason: '' })
        loadExpertAccess()
      })
      .catch((err) => setExpertStatus(err.message || 'Failed to grant access.'))
  }

  const revokeExpertAccess = (accessId: string) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/experts/${accessId}/revoke`, { method: 'POST' })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text()
          let message = text || 'Failed to revoke access.'
          try {
            const data = JSON.parse(text)
            if (data?.detail) message = data.detail
          } catch {
            // keep raw text
          }
          throw new Error(message)
        }
        return res.json()
      })
      .then(() => {
        setExpertStatus('Access revoked.')
        loadExpertAccess()
      })
      .catch((err) => setExpertStatus(err.message || 'Failed to revoke access.'))
  }

  const draftDecisionSummary = () => {
    if (!caseId) return
    setStatus('Drafting summary from case notes...')
    apiFetch(`/cases/${caseId}/summary/draft`)
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text()
          let message = text || 'Failed to draft summary.'
          try {
            const data = JSON.parse(text)
            if (data?.detail) message = data.detail
          } catch {
            // keep raw text
          }
          throw new Error(message)
        }
        return res.json() as Promise<{ summary?: string }>
      })
      .then((data) => {
        if (data?.summary) {
          setDecisionSummary(data.summary)
          setStatus('Draft summary loaded. Review and edit as needed.')
        } else {
          setStatus('Draft summary unavailable.')
        }
      })
      .catch((err) => setStatus(err.message || 'Failed to draft summary.'))
  }

  const sendReporterReply = () => {
    if (!caseId) return
    if (!reporterReply.trim()) {
      setStatus('Reporter reply cannot be empty.')
      return
    }
    apiFetch(`/cases/${caseId}/reporter-messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body: reporterReply.trim() }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text()
          let message = text || 'Failed to send reply.'
          try {
            const data = JSON.parse(text)
            if (data?.detail) message = data.detail
          } catch {
            // keep raw text
          }
          throw new Error(message)
        }
        return res.json()
      })
      .then(() => {
        setReporterReply('')
        loadReporterMessages()
      })
      .catch((err) => setStatus(err.message || 'Failed to send reply.'))
  }

  const addEvidence = () => {
    if (!caseId) return
    if (!evidenceDraft.label.trim() || !evidenceDraft.source.trim()) {
      setStatus('Evidence label and source are required.')
      return
    }
    apiFetch(`/cases/${caseId}/evidence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        label: evidenceDraft.label.trim(),
        source: evidenceDraft.source.trim(),
        link: evidenceDraft.link.trim() || null,
        evidence_hash: evidenceDraft.evidence_hash.trim() || null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setEvidenceDraft({ label: '', source: '', link: '', evidence_hash: '' })
        loadCase()
      })
      .catch(() => setStatus('Failed to add evidence.'))
  }

  const addTask = () => {
    if (!taskDraft.title.trim()) {
      setStatus('Task title is required.')
      return
    }
    createTask(taskDraft.title, taskDraft.assignee)
    setTaskDraft({ title: '', assignee: '' })
  }

  const updateTaskStatus = (taskId: string, status: string) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/tasks/${taskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCase())
      .catch(() => setStatus('Failed to update task.'))
  }

  const addRecommendedTask = (title: string) => {
    if (!caseData) return
    if (caseData.tasks.some((task) => task.title.toLowerCase() === title.toLowerCase())) {
      setStatus('Recommended task already added.')
      return
    }
    createTask(title)
  }

  const addAllRecommendedTasks = () => {
    if (!caseData) return
    const existing = new Set(caseData.tasks.map((task) => task.title.toLowerCase()))
    const toAdd = RECOMMENDED_TASKS.filter((task) => !existing.has(task.toLowerCase()))
    if (toAdd.length === 0) {
      setStatus('All recommended tasks already added.')
      return
    }
    toAdd.forEach((task) => createTask(task))
  }

  const addNote = () => {
    if (!caseId) return
    if (!noteDraft.body.trim()) {
      setStatus('Note body is required.')
      return
    }
    apiFetch(`/cases/${caseId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        note_type: noteDraft.note_type.trim() || 'general',
        body: noteDraft.body.trim(),
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setNoteDraft({ note_type: 'general', body: '' })
        loadCase()
        loadFlags()
      })
      .catch(() => setStatus('Failed to add note.'))
  }

  const saveLessonsLearned = () => {
    if (!caseId) return
    if (!lessonsDraft.root_cause.trim() && !lessonsDraft.action_items.trim()) {
      setStatus('Add root cause or action items before saving.')
      return
    }
    const body = [
      `Root cause: ${lessonsDraft.root_cause.trim() || 'Not provided'}`,
      `Action items: ${lessonsDraft.action_items.trim() || 'Not provided'}`,
    ].join('\n')
    apiFetch(`/cases/${caseId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        note_type: 'lessons_learned',
        body,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setLessonsDraft({ root_cause: '', action_items: '' })
        loadCase()
      })
      .catch(() => setStatus('Failed to save lessons learned.'))
  }

  const addMeetingNote = () => {
    if (!caseId) return
    if (!meetingDraft.summary.trim()) {
      setStatus('Meeting summary is required.')
      return
    }
    const body = [
      `Meeting date: ${meetingDraft.meeting_date || 'Not specified'}`,
      `Attendees: ${meetingDraft.attendees || 'Not specified'}`,
      `Summary: ${meetingDraft.summary}`,
      'Minutes:',
      meetingDraft.minutes || '(none)',
    ].join('\\n')
    apiFetch(`/cases/${caseId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        note_type: 'meeting',
        body,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setMeetingDraft({ meeting_date: '', attendees: '', summary: '', minutes: '' })
        loadCase()
        loadFlags()
      })
      .catch(() => setStatus('Failed to add meeting note.'))
  }

  const resolveFlag = (flagId: number) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/flags/${flagId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'resolved' }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadFlags())
      .catch(() => setStatus('Failed to resolve flag.'))
  }

  const applyPlaybook = (playbookKey: string) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/apply-playbook`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playbook_key: playbookKey }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        loadCase()
        loadSuggestions()
      })
      .catch(() => setStatus('Playbook failed.'))
  }

  const convertSuggestion = (suggestionId: string) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/suggestions/${suggestionId}/convert`, { method: 'POST' })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        loadCase()
        loadSuggestions()
      })
      .catch(() => setStatus('Convert failed.'))
  }

  const dismissSuggestion = (suggestionId: string) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/suggestions/${suggestionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'dismissed' }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadSuggestions())
      .catch(() => setStatus('Dismiss failed.'))
  }

  const generateDocument = (docType: string) => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/documents/${docType}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format: docFormat }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const payload = await res.json().catch(() => null)
          setStatus(payload?.detail || 'Document failed.')
          return null
        }
        return res.json()
      })
      .then(() => loadDocuments())
      .catch(() => setStatus('Document failed.'))
  }

  useEffect(() => {
    localStorage.setItem('case_doc_format', docFormat)
  }, [docFormat])

  const exportPack = () => {
    if (!caseId) return
    apiBlob(`/cases/${caseId}/export`)
      .then((blob) => {
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${caseId}_export.zip`
        link.click()
        window.URL.revokeObjectURL(url)
      })
      .catch(() => setStatus('Failed to export case pack.'))
  }

  const exportRedactedPack = () => {
    if (!caseId) return
    let redactions: unknown = []
    let note: string | null = redactionInput.trim() || null
    if (redactionInput.trim()) {
      try {
        const parsed = JSON.parse(redactionInput)
        redactions = parsed
        note = null
      } catch {
        // treat input as a note
      }
    }
    apiBlob(`/cases/${caseId}/export/redact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        redactions: Array.isArray(redactions) ? redactions : [redactions],
        note,
      }),
    })
      .then((blob) => {
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${caseId}_export_redacted.zip`
        link.click()
        window.URL.revokeObjectURL(url)
      })
      .catch(() => setStatus('Failed to export redacted pack.'))
  }

  const suggestRedactions = () => {
    if (!caseId) return
    setStatus('Scanning for potential PII...')
    apiFetch(`/cases/${caseId}/redactions/suggest`)
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text()
          let message = text || 'Failed to suggest redactions.'
          try {
            const data = JSON.parse(text)
            if (data?.detail) message = data.detail
          } catch {
            // keep raw text
          }
          throw new Error(message)
        }
        return res.json() as Promise<Array<Record<string, unknown>>>
      })
      .then((data) => {
        if (!data || data.length === 0) {
          setStatus('No redaction suggestions found.')
          return
        }
        setRedactionInput(JSON.stringify(data, null, 2))
        setStatus('Redaction suggestions loaded. Review before exporting.')
      })
      .catch((err) => setStatus(err.message || 'Failed to suggest redactions.'))
  }

  const runConsistencyCheck = () => {
    if (!caseId) return
    setStatus('Running consistency check...')
    apiFetch(`/cases/${caseId}/consistency`)
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text()
          let message = text || 'Failed to run consistency check.'
          try {
            const data = JSON.parse(text)
            if (data?.detail) message = data.detail
          } catch {
            // keep raw text
          }
          throw new Error(message)
        }
        return res.json() as Promise<CaseConsistency>
      })
      .then((data) => {
        setConsistency(data)
        setStatus('')
      })
      .catch((err) => setStatus(err.message || 'Failed to run consistency check.'))
  }

  const exportRemediation = () => {
    if (!caseId) return
    apiBlob(`/cases/${caseId}/remediation-export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        remediation_statement: remediationInput.trim() || null,
        format: remediationFormat,
      }),
    })
      .then((blob) => {
        if (!blob) return
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${caseId}_remediation.${remediationFormat === 'csv' ? 'csv' : 'json'}`
        link.click()
        window.URL.revokeObjectURL(url)
        loadCase()
      })
      .catch(() => setStatus('Failed to export remediation data.'))
  }

  const recordDecision = () => {
    if (!caseId) return
    if (hasRoleSeparationConflict && !decisionOverrideReason.trim()) {
      setStatus('Role separation conflict detected. Provide a legal override reason.')
      return
    }
    apiFetch(`/cases/${caseId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        outcome: decisionOutcome,
        summary: decisionSummary || null,
        role_separation_override_reason: decisionOverrideReason.trim() || null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCase())
      .catch(() => setStatus('Decision failed.'))
  }

  const approveErasure = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/erasure/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => setStatus('Erasure approved.'))
      .catch(() => setStatus('Erasure approval failed.'))
  }

  const executeErasure = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/erasure/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setStatus('Erasure executed.')
        loadCase()
      })
      .catch(() => setStatus('Erasure execute failed.'))
  }

  const toggleSeriousCause = (enabled: boolean) => {
    if (!caseId) return
    const incidentValue =
      seriousDraft.date_incident_occurred || (caseData?.date_incident_occurred ? toLocalInput(caseData.date_incident_occurred) : '')
    const investigationValue =
      seriousDraft.date_investigation_started || (caseData?.date_investigation_started ? toLocalInput(caseData.date_investigation_started) : '')
    apiFetch(`/cases/${caseId}/serious-cause/enable`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        enabled,
        date_incident_occurred: incidentValue ? toIso(incidentValue) : null,
        date_investigation_started: investigationValue ? toIso(investigationValue) : null,
        decision_maker: seriousDraft.decision_maker || null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCase())
      .catch(() => setStatus('Failed to toggle serious cause.'))
  }

  const submitFindings = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/actions/submit-findings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        confirmed_at: seriousDraft.facts_confirmed_at ? toIso(seriousDraft.facts_confirmed_at) : null,
        decision_maker: seriousDraft.decision_maker || null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCase())
      .catch(() => setStatus('Failed to submit findings.'))
  }

  const recordDismissal = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/serious-cause/record-dismissal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dismissal_recorded_at: seriousDraft.dismissal_recorded_at
          ? toIso(seriousDraft.dismissal_recorded_at)
          : null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCase())
      .catch(() => setStatus('Failed to record dismissal.'))
  }

  const recordReasonsSent = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/serious-cause/record-reasons-sent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sent_at: seriousDraft.reasons_sent_at ? toIso(seriousDraft.reasons_sent_at) : null,
        delivery_method: seriousDraft.reasons_delivery_method || null,
        proof_uri: seriousDraft.reasons_delivery_proof_uri || null,
      }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const payload = await res.json().catch(() => null)
          setStatus(payload?.detail || 'Failed to record reasons sent.')
          return null
        }
        return res.json()
      })
      .then((data) => {
        if (data) loadCase()
      })
      .catch(() => setStatus('Failed to record reasons sent.'))
  }

  const acknowledgeMissed = () => {
    if (!caseId) return
    apiFetch(`/cases/${caseId}/serious-cause/acknowledge-missed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: seriousDraft.missed_reason || null }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCase())
      .catch(() => setStatus('Failed to acknowledge missed deadline.'))
  }

  const anonymizeCase = () => {
    if (!caseId) return
    const proceed = window.confirm('Anonymize this case? Sensitive data will be cleared.')
    if (!proceed) return
    apiFetch(`/cases/${caseId}/anonymize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: 'User initiated anonymization.' }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCase())
      .catch(() => setStatus('Failed to anonymize case.'))
  }

  const updateStatus = (statusValue: string) => {
    if (!caseId || !caseData) return
    if (caseData.is_anonymized) {
      setStatus('Cannot change status on an anonymized case.')
      return
    }
    if (statusValue === caseData.status) return
    const closing = statusValue === 'CLOSED' && caseData.status !== 'CLOSED'
    const reopening = caseData.status === 'CLOSED' && statusValue !== 'CLOSED'
    if (closing) {
      const confirmed = window.confirm('Close this case? You can reopen it until anonymized.')
      if (!confirmed) return
    }
    if (reopening) {
      const confirmed = window.confirm('Re-open this case?')
      if (!confirmed) return
    }
    apiFetch(`/cases/${caseId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: statusValue }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCase())
      .catch(() => setStatus('Failed to update status.'))
  }

  const lockPII = () => {
    if (!breakGlassKey) return
    localStorage.removeItem(breakGlassKey)
    setPiiUnlocked(false)
    setBreakGlassExpiresAt(null)
    setStatus('PII view locked.')
  }

  const submitBreakGlass = () => {
    if (!caseId) return
    const reason = breakGlassReason.trim()
    if (!reason) {
      setStatus('Break-glass reason is required.')
      return
    }
    const duration = Math.min(480, Math.max(15, Number(breakGlassDuration) || 60))
    apiFetch(`/cases/${caseId}/break-glass`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reason,
        scope: 'case_flow',
        duration_minutes: duration,
      }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const payload = await res.json().catch(() => null)
          throw new Error(payload?.detail || 'Failed to record break-glass action.')
        }
        return res.json()
      })
      .then(() => {
        const expiresAt = Date.now() + duration * 60 * 1000
        if (breakGlassKey) {
          localStorage.setItem(breakGlassKey, JSON.stringify({ expiresAt }))
        }
        setPiiUnlocked(true)
        setBreakGlassExpiresAt(expiresAt)
        setBreakGlassReason('')
        setBreakGlassDuration(duration)
        setBreakGlassOpen(false)
        setStatus(`PII unlocked for ${duration} minutes.`)
      })
      .catch((err) => setStatus(err instanceof Error ? err.message : 'Failed to record break-glass action.'))
  }

  if (!caseData) {
    return <div className="case-flow">Loading case...</div>
  }

  const isAnonymized = caseData.is_anonymized
  const showGuidance = !!guidanceOpen[currentStep.key]
  const triageImpactOption = TRIAGE_IMPACT_LEVELS.find((option) => option.value === triageGate.impact)
  const triageProbabilityOption = TRIAGE_PROBABILITY_LEVELS.find((option) => option.value === triageGate.probability)
  const triageRiskOption = TRIAGE_RISK_LEVELS.find((option) => option.value === triageGate.risk_score)
  const breakGlassUntil = breakGlassExpiresAt ? new Date(breakGlassExpiresAt).toLocaleTimeString() : ''
  const canEditPII = piiUnlocked && !isAnonymized

  return (
    <section className="case-flow">
      <header className="case-flow-header">
        <div>
          <h1>{caseData.title}</h1>
          <div className="case-flow-meta">
            {caseData.case_id} · {caseData.jurisdiction} · Status {caseData.status} · Stage {caseData.stage}
          </div>
          {isBelgiumCase ? (
            <div className="case-flow-banner">Belgium jurisdiction: strict deadlines apply.</div>
          ) : null}
          {caseData.vip_flag ? <div className="case-flow-warning">VIP case access restricted.</div> : null}
          <div className="case-flow-meta">Immutable ID: {caseData.case_uuid}</div>
        </div>
        <div className="case-flow-actions">
          <div className="case-flow-pii">
            <div className="case-flow-pii-row">
              <span className={`case-flow-pill ${piiUnlocked ? 'good' : ''}`}>PII {piiUnlocked ? 'Unlocked' : 'Locked'}</span>
              {breakGlassUntil ? <span className="case-flow-muted">until {breakGlassUntil}</span> : null}
            </div>
            {piiUnlocked ? (
              <button className="case-flow-btn outline small" onClick={lockPII}>
                Lock PII
              </button>
            ) : (
              <button className="case-flow-btn outline small" onClick={() => setBreakGlassOpen(true)} disabled={isAnonymized}>
                Break Glass
              </button>
            )}
          </div>
          <button className="case-flow-btn" onClick={() => navigate('/case-management/cases')}>
            Back to Cases
          </button>
          <button className="case-flow-btn outline" onClick={nextStep}>
            Next step
          </button>
        </div>
      </header>

      <div className="case-flow-steps">
        {STEPS.map((item) => (
          <button
            key={item.key}
            className={`case-flow-step ${item.key === currentStep.key ? 'active' : ''}`}
            onClick={() => goToStep(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {status ? <div className="case-flow-status">{status}</div> : null}
      {transitionBlockers.length ? (
        <div className="case-flow-banner">
          Stage blocked: {transitionBlockers.length} requirement{transitionBlockers.length === 1 ? '' : 's'} pending.
          <button className="case-flow-btn small outline" onClick={() => setTransitionModalOpen(true)}>
            View details
          </button>
        </div>
      ) : null}

      <div className="case-flow-panel">
        {currentStep.key === 'intake' ? (
          <div>
            <div className="case-flow-step-header">
              <div>
                <h2>Intake</h2>
                <p className="case-flow-help">Capture scope, parties, and the initial trigger before any deep inspection.</p>
              </div>
              <button className="case-flow-info" onClick={toggleGuidance} type="button" aria-label="Toggle guidance">
                i
              </button>
            </div>
            {showGuidance ? (
              <div className="case-flow-guidance">
                <h4>Guidance</h4>
                <ul>
                  <li>Confirm the trigger source (alert, report, audit finding) before adding evidence.</li>
                  <li>Record all subjects in scope with role-based descriptors.</li>
                  <li>Keep summaries factual; avoid prohibited personal categories.</li>
                </ul>
              </div>
            ) : null}
            <div className="case-flow-grid">
              <div className="case-flow-card">
                <h3>Case context</h3>
                <p className="case-flow-help">Define scope and jurisdiction before deeper inspection.</p>
                <label className="case-flow-label">
                  Case title
                  <input
                    type="text"
                    value={caseMetaDraft.title}
                    onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, title: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Summary
                  <textarea
                    value={caseMetaDraft.summary}
                    onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, summary: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Jurisdiction
                  <select
                    value={caseMetaDraft.jurisdiction}
                    onChange={(e) =>
                      setCaseMetaDraft({ ...caseMetaDraft, jurisdiction: e.target.value, jurisdiction_other: '' })
                    }
                    disabled={isAnonymized}
                  >
                    <option value="">Select jurisdiction</option>
                    {JURISDICTION_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                {caseMetaDraft.jurisdiction === 'Other' ? (
                  <label className="case-flow-label">
                    Specify jurisdiction
                    <input
                      type="text"
                      value={caseMetaDraft.jurisdiction_other}
                      onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, jurisdiction_other: e.target.value })}
                      disabled={isAnonymized}
                    />
                  </label>
                ) : null}
                <label className="case-flow-label">
                  <input
                    type="checkbox"
                    checked={caseMetaDraft.vip_flag}
                    onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, vip_flag: e.target.checked })}
                    disabled={isAnonymized}
                  />
                  VIP / highly sensitive case
                </label>
                <label className="case-flow-label">
                  <input
                    type="checkbox"
                    checked={caseMetaDraft.urgent_dismissal}
                    onChange={(e) =>
                      setCaseMetaDraft({ ...caseMetaDraft, urgent_dismissal: e.target.checked })
                    }
                    disabled={isAnonymized}
                  />
                  Urgent dismissal case (NL guardrail)
                </label>
                <label className="case-flow-label">
                  <input
                    type="checkbox"
                    checked={caseMetaDraft.subject_suspended}
                    onChange={(e) =>
                      setCaseMetaDraft({ ...caseMetaDraft, subject_suspended: e.target.checked })
                    }
                    disabled={isAnonymized}
                  />
                  Subject suspended (required for NL urgent cases)
                </label>
                {needsSuspensionWarning ? (
                  <div className="case-flow-warning">
                    Netherlands urgent dismissal cases require suspension confirmation.
                  </div>
                ) : null}
                <label className="case-flow-label">
                  External report ID (optional)
                  <input
                    type="text"
                    value={caseMetaDraft.external_report_id}
                    onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, external_report_id: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Reporter channel ID (optional)
                  <input
                    type="text"
                    value={maskFieldValue(caseMetaDraft.reporter_channel_id)}
                    onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, reporter_channel_id: e.target.value })}
                    disabled={isAnonymized || !piiUnlocked}
                  />
                </label>
                <label className="case-flow-label">
                  Reporter key (optional)
                  <input
                    type="text"
                    value={maskFieldValue(caseMetaDraft.reporter_key)}
                    onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, reporter_key: e.target.value })}
                    disabled={isAnonymized || !piiUnlocked}
                  />
                </label>
                <button className="case-flow-btn outline" onClick={saveCaseDetails} disabled={isAnonymized}>
                  Save intake details
                </button>
                <div className="case-flow-divider" />
                <div className="case-flow-meta">Owner: {caseData.created_by || 'Unassigned'}</div>
                <div className="case-flow-meta">Created: {new Date(caseData.created_at).toLocaleString()}</div>
                {isAnonymized ? <div className="case-flow-warning">Case anonymized.</div> : null}
              </div>
              <div className="case-flow-card">
                <h3>Initial assessment (triage)</h3>
                <p className="case-flow-help">
                  Use plain-language impact and likelihood levels to clarify the business decision.
                </p>
                <label className="case-flow-label">
                  Business impact
                  <select
                    value={triageGate.impact}
                    onChange={(e) => {
                      const impact = Number(e.target.value)
                      setTriageGate({
                        ...triageGate,
                        impact,
                        risk_score: computeRiskScore(impact, triageGate.probability),
                      })
                    }}
                    disabled={isAnonymized}
                  >
                    {TRIAGE_IMPACT_LEVELS.map((option) => (
                      <option key={`impact-${option.value}`} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {triageImpactOption?.detail ? (
                    <span className="case-flow-muted">{triageImpactOption.detail}</span>
                  ) : null}
                </label>
                <label className="case-flow-label">
                  Likelihood
                  <select
                    value={triageGate.probability}
                    onChange={(e) => {
                      const probability = Number(e.target.value)
                      setTriageGate({
                        ...triageGate,
                        probability,
                        risk_score: computeRiskScore(triageGate.impact, probability),
                      })
                    }}
                    disabled={isAnonymized}
                  >
                    {TRIAGE_PROBABILITY_LEVELS.map((option) => (
                      <option key={`prob-${option.value}`} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {triageProbabilityOption?.detail ? (
                    <span className="case-flow-muted">{triageProbabilityOption.detail}</span>
                  ) : null}
                </label>
                <div className="case-flow-score-card">
                  <div>
                    <div className="case-flow-subtitle">Overall risk</div>
                    <div className="case-flow-muted">Calculated from impact and likelihood.</div>
                  </div>
                  <span className="case-flow-score-pill">{triageRiskOption?.label || 'TBD'}</span>
                </div>
                <label className="case-flow-label">
                  Trigger source
                  <input
                    list="triage-trigger-sources"
                    value={triageGate.trigger_source}
                    onChange={(e) => setTriageGate({ ...triageGate, trigger_source: e.target.value })}
                    placeholder="e.g., alert, hotline, audit finding"
                    disabled={isAnonymized}
                  />
                  <datalist id="triage-trigger-sources">
                    <option value="Automated alert" />
                    <option value="Employee report" />
                    <option value="Audit finding" />
                    <option value="HR escalation" />
                    <option value="External tip" />
                  </datalist>
                </label>
                <label className="case-flow-label">
                  Data sensitivity
                  <select
                    value={triageGate.data_sensitivity}
                    onChange={(e) => setTriageGate({ ...triageGate, data_sensitivity: e.target.value })}
                    disabled={isAnonymized}
                  >
                    <option value="">Select sensitivity</option>
                    {DATA_SENSITIVITY_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="case-flow-label">
                  Business impact summary
                  <textarea
                    value={triageGate.business_impact}
                    onChange={(e) => setTriageGate({ ...triageGate, business_impact: e.target.value })}
                    placeholder="Describe the potential business impact."
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Exposure summary
                  <textarea
                    value={triageGate.exposure_summary}
                    onChange={(e) => setTriageGate({ ...triageGate, exposure_summary: e.target.value })}
                    placeholder="Describe the data, systems, or processes exposed."
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Stakeholders impacted
                  <input
                    type="text"
                    value={triageGate.stakeholders}
                    onChange={(e) => setTriageGate({ ...triageGate, stakeholders: e.target.value })}
                    placeholder="e.g., Legal, HR, Comms, Finance"
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Confidence level
                  <select
                    value={triageGate.confidence_level}
                    onChange={(e) => setTriageGate({ ...triageGate, confidence_level: e.target.value })}
                    disabled={isAnonymized}
                  >
                    <option value="">Select confidence</option>
                    {TRIAGE_CONFIDENCE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="case-flow-label">
                  Recommended next actions
                  <textarea
                    value={triageGate.recommended_actions}
                    onChange={(e) => setTriageGate({ ...triageGate, recommended_actions: e.target.value })}
                    placeholder="Immediate actions or decision gates."
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Triage outcome
                  <select
                    value={triageGate.outcome}
                    onChange={(e) => setTriageGate({ ...triageGate, outcome: e.target.value })}
                    disabled={isAnonymized}
                  >
                    <option value="">Select outcome</option>
                    {TRIAGE_OUTCOME_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="case-flow-label">
                  Notes (optional)
                  <textarea
                    value={triageGate.notes}
                    onChange={(e) => setTriageGate({ ...triageGate, notes: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <button
                  className="case-flow-btn outline"
                  onClick={() => {
                    if (!triageGate.outcome) {
                      setStatus('Select a triage outcome before saving.')
                      return
                    }
                    saveGate('triage', {
                      impact: triageGate.impact,
                      probability: triageGate.probability,
                      risk_score: triageGate.risk_score,
                      outcome: triageGate.outcome,
                      notes: triageGate.notes || null,
                      trigger_source: triageGate.trigger_source || null,
                      business_impact: triageGate.business_impact || null,
                      exposure_summary: triageGate.exposure_summary || null,
                      data_sensitivity: triageGate.data_sensitivity || null,
                      stakeholders: triageGate.stakeholders || null,
                      confidence_level: triageGate.confidence_level || null,
                      recommended_actions: triageGate.recommended_actions || null,
                    })
                  }}
                  disabled={isAnonymized}
                >
                  Save triage assessment
                </button>
                <div className="case-flow-muted">
                  Triage uses business-friendly labels instead of numeric scores.
                </div>
              </div>
              <div className="case-flow-card">
                <h3>Subjects</h3>
                <p className="case-flow-help">Add everyone in scope (subject, witness, impacted stakeholder).</p>
                <label className="case-flow-label">
                  Subject type
                  <input
                    list="subject-types"
                    value={subjectDraft.subject_type}
                    onChange={(e) => setSubjectDraft({ ...subjectDraft, subject_type: e.target.value })}
                    placeholder="Employee"
                    disabled={isAnonymized}
                  />
                  <datalist id="subject-types">
                    {SUBJECT_TYPE_OPTIONS.map((option) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                </label>
                <label className="case-flow-label">
                  Display name
                  <input
                    type="text"
                    value={subjectDraft.display_name}
                    onChange={(e) => setSubjectDraft({ ...subjectDraft, display_name: e.target.value })}
                    placeholder="Jane Doe"
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Reference (optional)
                  <input
                    type="text"
                    value={subjectDraft.reference}
                    onChange={(e) => setSubjectDraft({ ...subjectDraft, reference: e.target.value })}
                    placeholder="Employee ID"
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Manager name (optional)
                  <input
                    type="text"
                    value={subjectDraft.manager_name}
                    onChange={(e) => setSubjectDraft({ ...subjectDraft, manager_name: e.target.value })}
                    placeholder="Manager name"
                    disabled={!canEditPII}
                  />
                </label>
                <button className="case-flow-btn outline" onClick={addSubject} disabled={!canEditPII}>
                  Add subject
                </button>
                <div className="case-flow-pill-list">
                  {caseData.subjects.map((subject, idx) => (
                    <span key={`${subject.subject_type}-${subject.display_name}-${idx}`} className="case-flow-pill">
                      {maskIndexed(subject.display_name, idx, 'Subject')} ({subject.subject_type})
                      {subject.manager_name ? ` · mgr ${maskText(subject.manager_name, 'Hidden')}` : ''}
                    </span>
                  ))}
                </div>
              </div>
              <div className="case-flow-card">
                <h3>Related cases</h3>
                <p className="case-flow-help">Link duplicates or related matters to keep investigations aligned.</p>
                <label className="case-flow-label">
                  Linked case ID
                  <input
                    type="text"
                    value={linkDraft.linked_case_id}
                    onChange={(e) => setLinkDraft({ ...linkDraft, linked_case_id: e.target.value })}
                    placeholder="CASE-0001"
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Relation
                  <select
                    value={linkDraft.relation_type}
                    onChange={(e) => setLinkDraft({ ...linkDraft, relation_type: e.target.value })}
                    disabled={isAnonymized}
                  >
                    {LINK_RELATION_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <button className="case-flow-btn outline" onClick={addLink} disabled={isAnonymized}>
                  Link case
                </button>
                {linkStatus ? <div className="case-flow-meta">{linkStatus}</div> : null}
                <div className="case-flow-link-list">
                  {links.length === 0 ? (
                    <div className="case-flow-muted">No linked cases yet.</div>
                  ) : (
                    links.map((link) => (
                      <div key={link.id} className="case-flow-link-item">
                        <div className="case-flow-link-meta">
                          <strong>{link.linked_case_id}</strong>
                          <span>{relationLabel(link.relation_type)}</span>
                          <span className="case-flow-muted">Linked {new Date(link.created_at).toLocaleDateString()}</span>
                        </div>
                        <div className="case-flow-inline">
                          <button
                            className="case-flow-btn outline small"
                            onClick={() => navigate(`/cases/${link.linked_case_id}/flow`)}
                          >
                            Open
                          </button>
                          <button
                            className="case-flow-btn outline small"
                            onClick={() => removeLink(link.id)}
                            disabled={isAnonymized}
                          >
                            Unlink
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
              <div className="case-flow-card">
                <h3>Serious cause (if known)</h3>
                <p className="case-flow-help">Enable early if the case already meets serious cause criteria.</p>
                <label className="case-flow-label">
                  <input
                    type="checkbox"
                    checked={seriousEnabledDraft}
                    onChange={(e) => setSeriousEnabledDraft(e.target.checked)}
                    disabled={isAnonymized}
                  />
                  Enable serious cause workflow
                </label>
                <label className="case-flow-label">
                  Incident occurred
                  <input
                    type="datetime-local"
                    value={seriousDraft.date_incident_occurred || toLocalInput(caseData.date_incident_occurred)}
                    onChange={(e) => setSeriousDraft({ ...seriousDraft, date_incident_occurred: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Investigation started
                  <input
                    type="datetime-local"
                    value={seriousDraft.date_investigation_started || toLocalInput(caseData.date_investigation_started)}
                    onChange={(e) => setSeriousDraft({ ...seriousDraft, date_investigation_started: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Decision maker (optional)
                  <input
                    type="text"
                    value={seriousDraft.decision_maker}
                    onChange={(e) => setSeriousDraft({ ...seriousDraft, decision_maker: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <button
                  className="case-flow-btn outline"
                  onClick={() => toggleSeriousCause(seriousEnabledDraft)}
                  disabled={isAnonymized}
                >
                  Save serious cause settings
                </button>
                <div className="case-flow-muted">You can refine deadlines later in the Decision step.</div>
              </div>
            </div>
          </div>
        ) : null}

        {currentStep.key === 'legitimacy' ? (
          <div>
            <div className="case-flow-step-header">
              <div>
                <h2>Legitimacy & Proportionality</h2>
                <p className="case-flow-help">Define legal basis, proportionality, and mandate before proceeding.</p>
              </div>
              <button className="case-flow-info" onClick={toggleGuidance} type="button" aria-label="Toggle guidance">
                i
              </button>
            </div>
            {showGuidance ? (
              <div className="case-flow-guidance">
                <h4>Guidance</h4>
                <ul>
                  <li>Legal basis must be specific enough to justify the scope of data reviewed.</li>
                  <li>Document less-intrusive steps you tried or ruled out.</li>
                  <li>Mandate owner and date should map to actual approval authority.</li>
                </ul>
              </div>
            ) : null}
            <div className="case-flow-card">
              <div className="case-flow-muted">Gate status: {caseData.gates.find((g) => g.gate_key === 'legitimacy')?.status || 'pending'}</div>
              <label className="case-flow-label">
                Legal basis
                <select
                  value={legitimacyGate.legal_basis}
                  onChange={(e) =>
                    setLegitimacyGate({ ...legitimacyGate, legal_basis: e.target.value, legal_basis_other: '' })
                  }
                  disabled={isAnonymized}
                >
                  <option value="">Select a basis</option>
                  {LEGAL_BASIS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              {legitimacyGate.legal_basis === 'Other' ? (
                <label className="case-flow-label">
                  Specify legal basis
                  <input
                    type="text"
                    value={legitimacyGate.legal_basis_other}
                    onChange={(e) => setLegitimacyGate({ ...legitimacyGate, legal_basis_other: e.target.value })}
                    placeholder="Describe the basis"
                    disabled={isAnonymized}
                  />
                </label>
              ) : null}
              <label className="case-flow-label">
                Trigger summary
                <textarea
                  value={legitimacyGate.trigger_summary}
                  onChange={(e) => setLegitimacyGate({ ...legitimacyGate, trigger_summary: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <label className="case-flow-label">
                <input
                  type="checkbox"
                  checked={legitimacyGate.proportionality_confirmed}
                  onChange={(e) =>
                    setLegitimacyGate({ ...legitimacyGate, proportionality_confirmed: e.target.checked })
                  }
                  disabled={isAnonymized}
                />
                Proportionality confirmed
              </label>
              <label className="case-flow-label">
                Less intrusive steps
                <input
                  type="text"
                  value={legitimacyGate.less_intrusive_steps}
                  onChange={(e) => setLegitimacyGate({ ...legitimacyGate, less_intrusive_steps: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <label className="case-flow-label">
                Mandate owner
                <input
                  type="text"
                  value={legitimacyGate.mandate_owner}
                  onChange={(e) => setLegitimacyGate({ ...legitimacyGate, mandate_owner: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <label className="case-flow-label">
                Mandate date
                <input
                  type="date"
                  value={legitimacyGate.mandate_date}
                  onChange={(e) => setLegitimacyGate({ ...legitimacyGate, mandate_date: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <div className="case-flow-inline">
                <button
                  className="case-flow-btn outline"
                  onClick={() => {
                    const basis =
                      legitimacyGate.legal_basis === 'Other'
                        ? legitimacyGate.legal_basis_other.trim()
                        : legitimacyGate.legal_basis
                    if (!basis || !legitimacyGate.trigger_summary.trim()) {
                      setStatus('Legitimacy gate needs legal basis and trigger summary.')
                      return
                    }
                    saveGate('legitimacy', {
                      legal_basis: basis,
                      trigger_summary: legitimacyGate.trigger_summary,
                      proportionality_confirmed: !!legitimacyGate.proportionality_confirmed,
                      less_intrusive_steps: legitimacyGate.less_intrusive_steps || null,
                      mandate_owner: legitimacyGate.mandate_owner || null,
                      mandate_date: legitimacyGate.mandate_date || null,
                    })
                  }}
                  disabled={isAnonymized}
                >
                  Save gate
                </button>
                <button className="case-flow-btn outline" onClick={() => generateDocument('INVESTIGATION_MANDATE')}>
                  Generate Mandate
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {currentStep.key === 'credentialing' ? (
          <div>
            <div className="case-flow-step-header">
              <div>
                <h2>Credentialing</h2>
                <p className="case-flow-help">Confirm investigator eligibility, licensing, and conflicts.</p>
              </div>
              <button className="case-flow-info" onClick={toggleGuidance} type="button" aria-label="Toggle guidance">
                i
              </button>
            </div>
            {showGuidance ? (
              <div className="case-flow-guidance">
                <h4>Guidance</h4>
                <ul>
                  <li>Licensed investigators are required for systematic investigations.</li>
                  <li>Document who authorized the assignment and when.</li>
                  <li>Flag conflicts early (reporting line, personal ties, prior involvement).</li>
                </ul>
              </div>
            ) : null}
            <div className="case-flow-card">
              <div className="case-flow-muted">Gate status: {caseData.gates.find((g) => g.gate_key === 'credentialing')?.status || 'pending'}</div>
              {!currentUser ? (
                <div className="case-flow-warning">
                  Investigator profile not loaded. Profile completion will be required once authentication is enabled.
                </div>
              ) : null}
              <label className="case-flow-label">
                Investigator name
                <input
                  type="text"
                  value={credentialingGate.investigator_name}
                  onChange={(e) => setCredentialingGate({ ...credentialingGate, investigator_name: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <button
                className="case-flow-btn outline"
                onClick={() => {
                  if (!currentUser) return
                  setCredentialingGate({ ...credentialingGate, investigator_name: currentUser })
                }}
                disabled={!currentUser || isAnonymized}
              >
                Use my profile
              </button>
              <label className="case-flow-label">
                Investigator role
                <input
                  list="investigator-roles"
                  value={credentialingGate.investigator_role}
                  onChange={(e) => setCredentialingGate({ ...credentialingGate, investigator_role: e.target.value })}
                  disabled={isAnonymized}
                />
                <datalist id="investigator-roles">
                  {INVESTIGATOR_ROLE_OPTIONS.map((option) => (
                    <option key={option} value={option} />
                  ))}
                </datalist>
              </label>
              <label className="case-flow-label">
                <input
                  type="checkbox"
                  checked={credentialingGate.licensed}
                  onChange={(e) => setCredentialingGate({ ...credentialingGate, licensed: e.target.checked })}
                  disabled={isAnonymized}
                />
                Licensed investigator
              </label>
              <label className="case-flow-label">
                License ID
                <input
                  type="text"
                  value={credentialingGate.license_id}
                  onChange={(e) => setCredentialingGate({ ...credentialingGate, license_id: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <label className="case-flow-label">
                <input
                  type="checkbox"
                  checked={credentialingGate.conflict_check_passed}
                  onChange={(e) =>
                    setCredentialingGate({ ...credentialingGate, conflict_check_passed: e.target.checked })
                  }
                  disabled={isAnonymized}
                />
                Conflict check passed
              </label>
              <label className="case-flow-label">
                Conflict override reason (if needed)
                <textarea
                  value={credentialingGate.conflict_override_reason}
                  onChange={(e) =>
                    setCredentialingGate({ ...credentialingGate, conflict_override_reason: e.target.value })
                  }
                  placeholder="Explain why an override is permitted."
                  disabled={isAnonymized}
                />
              </label>
              <label className="case-flow-label">
                Authorizer
                <input
                  type="text"
                  value={credentialingGate.authorizer}
                  onChange={(e) => setCredentialingGate({ ...credentialingGate, authorizer: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <label className="case-flow-label">
                Authorization date
                <input
                  type="date"
                  value={credentialingGate.authorization_date}
                  onChange={(e) =>
                    setCredentialingGate({ ...credentialingGate, authorization_date: e.target.value })
                  }
                  disabled={isAnonymized}
                />
              </label>
              <button
                className="case-flow-btn outline"
                onClick={() => {
                  if (!credentialingGate.investigator_name.trim() || !credentialingGate.investigator_role.trim()) {
                    setStatus('Credentialing gate needs investigator name and role.')
                    return
                  }
                  saveGate('credentialing', {
                    investigator_name: credentialingGate.investigator_name,
                    investigator_role: credentialingGate.investigator_role,
                    licensed: !!credentialingGate.licensed,
                    license_id: credentialingGate.license_id || null,
                    conflict_check_passed: !!credentialingGate.conflict_check_passed,
                    conflict_override_reason: credentialingGate.conflict_override_reason || null,
                    authorizer: credentialingGate.authorizer || null,
                    authorization_date: credentialingGate.authorization_date || null,
                  })
                }}
                disabled={isAnonymized}
              >
                Save gate
              </button>
            </div>
          </div>
        ) : null}

        {currentStep.key === 'investigation' ? (
          <div>
            <div className="case-flow-step-header">
              <div>
                <h2>Investigation</h2>
                <p className="case-flow-help">Capture actions, evidence, and logs as you build the case file.</p>
              </div>
              <button className="case-flow-info" onClick={toggleGuidance} type="button" aria-label="Toggle guidance">
                i
              </button>
            </div>
            {showGuidance ? (
              <div className="case-flow-guidance">
                <h4>Guidance</h4>
                <ul>
                  <li>Every investigative action should map to a task or evidence entry.</li>
                  <li>Use playbooks to avoid missing core steps.</li>
                  <li>Keep notes factual; avoid health, political, or union data.</li>
                </ul>
              </div>
            ) : null}
            <div className="case-flow-grid">
              <div className="case-flow-card">
                <h3>Impact analysis (PIA)</h3>
                <p className="case-flow-help">
                  Capture business impact to feed the final report (financial, reputational, people, operational).
                </p>
                <label className="case-flow-label">
                  Estimated loss (optional)
                  <input
                    type="number"
                    value={impactAnalysis.estimated_loss}
                    onChange={(e) => setImpactAnalysis({ ...impactAnalysis, estimated_loss: e.target.value })}
                    placeholder="e.g. 25000"
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Regulation breached (GDPR/SOX/etc.)
                  <input
                    type="text"
                    value={impactAnalysis.regulation_breached}
                    onChange={(e) => setImpactAnalysis({ ...impactAnalysis, regulation_breached: e.target.value })}
                    placeholder="GDPR, SOX, local labor law"
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Operational impact
                  <textarea
                    value={impactAnalysis.operational_impact}
                    onChange={(e) => setImpactAnalysis({ ...impactAnalysis, operational_impact: e.target.value })}
                    placeholder="Systems disrupted, response workload, etc."
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Financial impact
                  <textarea
                    value={impactAnalysis.financial_impact}
                    onChange={(e) => setImpactAnalysis({ ...impactAnalysis, financial_impact: e.target.value })}
                    placeholder="Loss drivers, cost categories, exposure."
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Reputational impact
                  <textarea
                    value={impactAnalysis.reputational_impact}
                    onChange={(e) => setImpactAnalysis({ ...impactAnalysis, reputational_impact: e.target.value })}
                    placeholder="Brand, customer trust, media exposure."
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  People impact
                  <textarea
                    value={impactAnalysis.people_impact}
                    onChange={(e) => setImpactAnalysis({ ...impactAnalysis, people_impact: e.target.value })}
                    placeholder="Team morale, leadership involvement, HR implications."
                    disabled={isAnonymized}
                  />
                </label>
                <button
                  className="case-flow-btn outline"
                  onClick={() => {
                    const lossValue = impactAnalysis.estimated_loss.trim()
                    const loss = lossValue ? Number(lossValue) : null
                    if (lossValue && Number.isNaN(loss)) {
                      setStatus('Estimated loss must be a number.')
                      return
                    }
                    saveGate('impact-analysis', {
                      estimated_loss: loss,
                      regulation_breached: impactAnalysis.regulation_breached || null,
                      operational_impact: impactAnalysis.operational_impact || null,
                      reputational_impact: impactAnalysis.reputational_impact || null,
                      people_impact: impactAnalysis.people_impact || null,
                      financial_impact: impactAnalysis.financial_impact || null,
                    })
                  }}
                  disabled={isAnonymized}
                >
                  Save impact analysis
                </button>
              </div>
              <div className="case-flow-card">
                <h3>Works Council airlock (DE/FR)</h3>
                <p className="case-flow-help">
                  If monitoring is required, evidence collection pauses until approval is documented.
                </p>
                {!isWorksCouncilJurisdiction ? (
                  <div className="case-flow-muted">Applicable for Germany/France monitoring cases.</div>
                ) : null}
                <label className="case-flow-label">
                  <input
                    type="checkbox"
                    checked={worksCouncilGate.monitoring}
                    onChange={(e) => setWorksCouncilGate({ ...worksCouncilGate, monitoring: e.target.checked })}
                    disabled={isAnonymized}
                  />
                  Monitoring requires Works Council approval
                </label>
                <label className="case-flow-label">
                  Approval document URI
                  <input
                    type="text"
                    value={worksCouncilGate.approval_document_uri}
                    onChange={(e) =>
                      setWorksCouncilGate({ ...worksCouncilGate, approval_document_uri: e.target.value })
                    }
                    placeholder="Link to approval document"
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Approval received at
                  <input
                    type="datetime-local"
                    value={worksCouncilGate.approval_received_at}
                    onChange={(e) =>
                      setWorksCouncilGate({ ...worksCouncilGate, approval_received_at: e.target.value })
                    }
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Notes
                  <textarea
                    value={worksCouncilGate.approval_notes}
                    onChange={(e) =>
                      setWorksCouncilGate({ ...worksCouncilGate, approval_notes: e.target.value })
                    }
                    disabled={isAnonymized}
                  />
                </label>
                <button
                  className="case-flow-btn outline"
                  onClick={() =>
                    saveGate('works-council', {
                      monitoring: !!worksCouncilGate.monitoring,
                      approval_document_uri: worksCouncilGate.approval_document_uri || null,
                      approval_received_at: worksCouncilGate.approval_received_at || null,
                      approval_notes: worksCouncilGate.approval_notes || null,
                    })
                  }
                  disabled={isAnonymized}
                >
                  Save Works Council status
                </button>
                {caseData.evidence_locked ? (
                  <div className="case-flow-warning">Evidence folder locked until approval is recorded.</div>
                ) : null}
              </div>
              <div className="case-flow-card">
                <h3>Tasks & Checklist</h3>
                <p className="case-flow-help">Track each investigative action and assignment.</p>
                <div className="case-flow-progress">
                  <div className="case-flow-progress-bar" style={{ width: `${taskProgress}%` }} />
                </div>
                <div className="case-flow-muted">
                  {taskTotal === 0 ? 'No tasks yet.' : `${taskCompleted} of ${taskTotal} tasks completed`}
                </div>
                <label className="case-flow-label">
                  Task
                  <input
                    type="text"
                    value={taskDraft.title}
                    onChange={(e) => setTaskDraft({ ...taskDraft, title: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Assignee
                  <input
                    type="text"
                    value={taskDraft.assignee}
                    onChange={(e) => setTaskDraft({ ...taskDraft, assignee: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <button className="case-flow-btn outline" onClick={addTask} disabled={isAnonymized}>
                  Add task
                </button>
                {caseData.tasks.length === 0 ? (
                  <div className="case-flow-muted">No tasks added.</div>
                ) : (
                  caseData.tasks.map((task) => (
                    <div key={task.task_id} className="case-flow-row">
                      <div>
                        <strong>{task.title}</strong>
                        <div className="case-flow-muted">
                          {task.assignee || 'Unassigned'}
                          {task.due_at ? ` · due ${new Date(task.due_at).toLocaleDateString()}` : ''}
                        </div>
                      </div>
                      <div className="case-flow-inline">
                        {task.task_type === 'retaliation_check' ? (
                          <span className="case-flow-tag">Retaliation</span>
                        ) : null}
                        <select
                          className="case-flow-select"
                          value={task.status}
                          onChange={(e) => updateTaskStatus(task.task_id, e.target.value)}
                          disabled={isAnonymized}
                        >
                          {TASK_STATUS_OPTIONS.map((option) => (
                            <option key={`${task.task_id}-${option}`} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  ))
                )}
                <div className="case-flow-divider" />
                <h4 className="case-flow-subtitle">Recommended tasks</h4>
                <div className="case-flow-muted">Add best-practice actions (you can still customize).</div>
                <div className="case-flow-inline">
                  {RECOMMENDED_TASKS.map((task) => (
                    <button
                      key={task}
                      className="case-flow-btn outline"
                      onClick={() => addRecommendedTask(task)}
                      disabled={isAnonymized}
                    >
                      Add: {task}
                    </button>
                  ))}
                </div>
                <button className="case-flow-btn outline" onClick={addAllRecommendedTasks} disabled={isAnonymized}>
                  Add all recommended
                </button>
              </div>
              <div className="case-flow-card">
                <h3>Evidence register</h3>
                <p className="case-flow-help">Log every piece of evidence with its system of origin.</p>
                {caseData.evidence_locked ? (
                  <div className="case-flow-warning">
                    Evidence folder locked pending Works Council approval.
                  </div>
                ) : null}
                <label className="case-flow-label">
                  Label
                  <input
                    type="text"
                    value={evidenceDraft.label}
                    onChange={(e) => setEvidenceDraft({ ...evidenceDraft, label: e.target.value })}
                    disabled={!canEditPII || !!caseData.evidence_locked}
                  />
                </label>
                <label className="case-flow-label">
                  Source
                  <input
                    list="evidence-sources"
                    value={evidenceDraft.source}
                    onChange={(e) => setEvidenceDraft({ ...evidenceDraft, source: e.target.value })}
                    disabled={!canEditPII || !!caseData.evidence_locked}
                  />
                  <datalist id="evidence-sources">
                    {EVIDENCE_SOURCE_OPTIONS.map((option) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                </label>
                <label className="case-flow-label">
                  Link (optional)
                  <input
                    type="text"
                    value={evidenceDraft.link}
                    onChange={(e) => setEvidenceDraft({ ...evidenceDraft, link: e.target.value })}
                    disabled={!canEditPII || !!caseData.evidence_locked}
                  />
                </label>
                <label className="case-flow-label">
                  Evidence hash (optional)
                  <input
                    type="text"
                    value={evidenceDraft.evidence_hash}
                    onChange={(e) => setEvidenceDraft({ ...evidenceDraft, evidence_hash: e.target.value })}
                    disabled={!canEditPII || !!caseData.evidence_locked}
                    placeholder="SHA-256 or other hash"
                  />
                </label>
                <button
                  className="case-flow-btn outline"
                  onClick={addEvidence}
                  disabled={!canEditPII || !!caseData.evidence_locked}
                >
                  Add evidence
                </button>
                <div className="case-flow-pill-list">
                  {caseData.evidence.map((evidence, idx) => (
                    <span key={evidence.evidence_id} className="case-flow-pill">
                      {maskIndexed(evidence.label, idx, 'Evidence')}
                      {evidence.evidence_hash ? ' · hash' : ''}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <div className="case-flow-grid">
              <div className="case-flow-card">
                <h3>Playbooks</h3>
                <p className="case-flow-help">Apply a playbook to auto-create tasks and evidence suggestions.</p>
                <div className="case-flow-inline">
                  {playbooks.map((playbook) => (
                    <button
                      key={playbook.key}
                      className="case-flow-btn outline"
                      onClick={() => applyPlaybook(playbook.key)}
                      disabled={isAnonymized}
                    >
                      {playbook.title}
                    </button>
                  ))}
                </div>
              </div>
              <div className="case-flow-card">
                <h3>Evidence suggestions</h3>
                <p className="case-flow-help">Convert suggestions into evidence entries or dismiss with rationale.</p>
                {suggestions.length === 0 ? (
                  <div className="case-flow-muted">No suggestions yet.</div>
                ) : (
                  suggestions.map((suggestion) => (
                    <div key={suggestion.suggestion_id} className="case-flow-row">
                      <div>
                        <strong>{suggestion.label}</strong>
                        <div className="case-flow-muted">{suggestion.source}</div>
                        <div className="case-flow-muted">{suggestion.playbook_key}</div>
                      </div>
                      {suggestion.status === 'open' ? (
                        <div className="case-flow-inline">
                          <button
                            className="case-flow-btn outline"
                            onClick={() => convertSuggestion(suggestion.suggestion_id)}
                            disabled={isAnonymized || !!caseData.evidence_locked}
                          >
                            Convert
                          </button>
                          <button
                            className="case-flow-btn outline"
                            onClick={() => dismissSuggestion(suggestion.suggestion_id)}
                            disabled={isAnonymized}
                          >
                            Dismiss
                          </button>
                        </div>
                      ) : (
                        <span className="case-flow-tag">{suggestion.status}</span>
                      )}
                    </div>
                  ))
                )}
              </div>
              <div className="case-flow-card">
                <h3>Reporter Q&amp;A</h3>
                <p className="case-flow-help">Secure two-way messages tied to the reporter key.</p>
                {!caseData.reporter_key ? (
                  <div className="case-flow-muted">No reporter key linked to this case.</div>
                ) : (
                  <>
                    {reporterMessages.length === 0 ? (
                      <div className="case-flow-muted">No messages yet.</div>
                    ) : (
                      reporterMessages.map((message) => (
                        <div key={message.id} className="case-flow-note">
                          <div className="case-flow-muted">
                            {message.sender} · {new Date(message.created_at).toLocaleString()}
                          </div>
                          <div>{maskText(message.body, 'Message hidden. Break glass to view.')}</div>
                        </div>
                      ))
                    )}
                    <label className="case-flow-label">
                      Reply to reporter
                      <textarea
                        value={reporterReply}
                        onChange={(e) => setReporterReply(e.target.value)}
                        disabled={!canEditPII}
                      />
                    </label>
                    <div className="case-flow-inline">
                      {REPORT_TEMPLATES.map((template, idx) => (
                        <button
                          key={`template-${idx}`}
                          className="case-flow-btn outline small"
                          onClick={() => setReporterReply(template)}
                          disabled={!canEditPII}
                        >
                          Use template {idx + 1}
                        </button>
                      ))}
                    </div>
                    <button className="case-flow-btn outline" onClick={sendReporterReply} disabled={!canEditPII}>
                      Send reply
                    </button>
                  </>
                )}
              </div>
            </div>
            <div className="case-flow-grid">
              <div className="case-flow-card">
                <h3>Silent legal hold</h3>
                <p className="case-flow-help">
                  Generate a confidential preservation instruction for a trusted IT contact.
                </p>
                <label className="case-flow-label">
                  IT contact name
                  <input
                    type="text"
                    value={legalHoldDraft.contact_name}
                    onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, contact_name: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  IT contact email
                  <input
                    type="email"
                    value={legalHoldDraft.contact_email}
                    onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, contact_email: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  IT contact role
                  <input
                    type="text"
                    value={legalHoldDraft.contact_role}
                    onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, contact_role: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Delivery channel
                  <select
                    value={legalHoldDraft.delivery_channel}
                    onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, delivery_channel: e.target.value })}
                    disabled={isAnonymized}
                  >
                    {LEGAL_HOLD_CHANNEL_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="case-flow-label">
                  Preservation scope
                  <textarea
                    value={legalHoldDraft.preservation_scope}
                    onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, preservation_scope: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Access code (optional)
                  <input
                    type="text"
                    value={legalHoldDraft.access_code}
                    onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, access_code: e.target.value })}
                    disabled={!canEditPII}
                    placeholder="Leave blank to auto-generate"
                  />
                </label>
                <label className="case-flow-label">
                  Override reason (only if contact is in scope)
                  <input
                    type="text"
                    value={legalHoldDraft.conflict_override_reason}
                    onChange={(e) =>
                      setLegalHoldDraft({ ...legalHoldDraft, conflict_override_reason: e.target.value })
                    }
                    disabled={!canEditPII}
                  />
                </label>
                <button className="case-flow-btn outline" onClick={createLegalHold} disabled={!canEditPII}>
                  Generate legal hold
                </button>
                {legalHoldStatus ? <div className="case-flow-meta">{legalHoldStatus}</div> : null}
                {legalHolds.length === 0 ? (
                  <div className="case-flow-muted">No legal holds yet.</div>
                ) : (
                  legalHolds.map((hold) => (
                    <div key={hold.id} className="case-flow-note">
                      <div className="case-flow-muted">
                        {hold.hold_id} · {new Date(hold.created_at).toLocaleString()}
                      </div>
                      <div>
                        <strong>{maskText(hold.contact_name, 'Hidden')}</strong>
                        {hold.contact_role ? ` · ${maskText(hold.contact_role, 'Hidden')}` : ''}
                      </div>
                      {hold.contact_email ? (
                        <div className="case-flow-muted">{maskText(hold.contact_email, 'Hidden')}</div>
                      ) : null}
                      {hold.preservation_scope ? (
                        <div className="case-flow-muted">Scope: {maskText(hold.preservation_scope, 'Hidden')}</div>
                      ) : null}
                      {hold.delivery_channel ? (
                        <div className="case-flow-muted">Channel: {hold.delivery_channel}</div>
                      ) : null}
                      {hold.access_code ? (
                        <div className="case-flow-tag">Access code: {maskText(hold.access_code, 'Hidden')}</div>
                      ) : null}
                      {hold.document_id ? (
                        <button
                          className="case-flow-btn outline small"
                          onClick={() =>
                            window.open(`${API_BASE}/cases/${caseData.case_id}/documents/${hold.document_id}/download`, '_blank')
                          }
                        >
                          Download instruction
                        </button>
                      ) : null}
                    </div>
                  ))
                )}
              </div>
              <div className="case-flow-card">
                <h3>External expert access (SOS)</h3>
                <p className="case-flow-help">
                  Grant 48-hour access to an external expert or partner firm with full audit logging.
                </p>
                <label className="case-flow-label">
                  Expert email
                  <input
                    type="email"
                    value={expertDraft.expert_email}
                    onChange={(e) => setExpertDraft({ ...expertDraft, expert_email: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Expert name
                  <input
                    type="text"
                    value={expertDraft.expert_name}
                    onChange={(e) => setExpertDraft({ ...expertDraft, expert_name: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Organization
                  <input
                    type="text"
                    value={expertDraft.organization}
                    onChange={(e) => setExpertDraft({ ...expertDraft, organization: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Reason / scope
                  <textarea
                    value={expertDraft.reason}
                    onChange={(e) => setExpertDraft({ ...expertDraft, reason: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <button className="case-flow-btn outline" onClick={grantExpertAccess} disabled={!canEditPII}>
                  Grant 48h access
                </button>
                {expertStatus ? <div className="case-flow-meta">{expertStatus}</div> : null}
                {expertAccess.length === 0 ? (
                  <div className="case-flow-muted">No external experts granted access yet.</div>
                ) : (
                  expertAccess.map((expert) => (
                    <div key={expert.access_id} className="case-flow-note">
                      <div className="case-flow-muted">
                        {maskText(expert.expert_email, 'Hidden')} · {expert.status}
                      </div>
                      {(expert.expert_name || expert.organization) ? (
                        <div>
                          {expert.expert_name ? maskText(expert.expert_name, 'External expert') : 'External expert'}
                          {expert.organization ? ` · ${maskText(expert.organization, 'Hidden')}` : ''}
                        </div>
                      ) : null}
                      <div className="case-flow-muted">
                        Expires {new Date(expert.expires_at).toLocaleString()}
                      </div>
                      {expert.reason ? <div className="case-flow-muted">Scope: {maskText(expert.reason, 'Hidden')}</div> : null}
                      {expert.status === 'active' ? (
                        <button
                          className="case-flow-btn outline small"
                          onClick={() => revokeExpertAccess(expert.access_id)}
                          disabled={isAnonymized}
                        >
                          Revoke access
                        </button>
                      ) : null}
                    </div>
                  ))
                )}
              </div>
            </div>
            <div className="case-flow-grid">
              <div className="case-flow-card">
                <h3>Investigation log</h3>
                <p className="case-flow-help">Append-only notes with automatic prohibited-data flagging.</p>
                <label className="case-flow-label">
                  Note type
                  <select
                    value={noteDraft.note_type}
                    onChange={(e) => setNoteDraft({ ...noteDraft, note_type: e.target.value })}
                    disabled={!canEditPII}
                  >
                    {NOTE_TYPE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="case-flow-label">
                  Note
                  <textarea
                    value={noteDraft.body}
                    onChange={(e) => setNoteDraft({ ...noteDraft, body: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <button className="case-flow-btn outline" onClick={addNote} disabled={!canEditPII}>
                  Add note
                </button>
                {caseData.notes.length === 0 ? (
                  <div className="case-flow-muted">No notes yet.</div>
                ) : (
                  caseData.notes.map((note) => (
                    <div key={note.id} className="case-flow-note">
                      <div className="case-flow-muted">
                        {note.note_type} · {new Date(note.created_at).toLocaleString()}
                      </div>
                      <div>{maskText(note.body, 'Note hidden. Break glass to view.')}</div>
                      {note.flags && (note.flags as { requires_review?: boolean }).requires_review ? (
                        <div className="case-flow-warning">Flagged for review</div>
                      ) : null}
                    </div>
                  ))
                )}
              </div>
              <div className="case-flow-card">
                <h3>Meetings & Minutes</h3>
                <p className="case-flow-help">Capture meeting notes, attendees, and summaries.</p>
                <label className="case-flow-label">
                  Meeting date/time
                  <input
                    type="datetime-local"
                    value={meetingDraft.meeting_date}
                    onChange={(e) => setMeetingDraft({ ...meetingDraft, meeting_date: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Attendees
                  <input
                    type="text"
                    value={meetingDraft.attendees}
                    onChange={(e) => setMeetingDraft({ ...meetingDraft, attendees: e.target.value })}
                    placeholder="Names or roles"
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Summary
                  <textarea
                    value={meetingDraft.summary}
                    onChange={(e) => setMeetingDraft({ ...meetingDraft, summary: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <label className="case-flow-label">
                  Minutes
                  <textarea
                    value={meetingDraft.minutes}
                    onChange={(e) => setMeetingDraft({ ...meetingDraft, minutes: e.target.value })}
                    disabled={!canEditPII}
                  />
                </label>
                <button className="case-flow-btn outline" onClick={addMeetingNote} disabled={!canEditPII}>
                  Add meeting minutes
                </button>
                <div className="case-flow-divider" />
                <h4 className="case-flow-subtitle">Meeting overview</h4>
                {caseData.notes.filter((note) => note.note_type === 'meeting').length === 0 ? (
                  <div className="case-flow-muted">No meetings recorded yet.</div>
                ) : (
                  caseData.notes
                    .filter((note) => note.note_type === 'meeting')
                    .map((note) => (
                      <div key={`meeting-${note.id}`} className="case-flow-note">
                        <div className="case-flow-muted">{new Date(note.created_at).toLocaleString()}</div>
                        <div>{maskText(note.body, 'Meeting note hidden. Break glass to view.')}</div>
                      </div>
                    ))
                )}
              </div>
              <div className="case-flow-card">
                <h3>Prohibited data flags</h3>
                <p className="case-flow-help">Resolve flagged keywords before finalizing reports.</p>
                {flags.length === 0 ? (
                  <div className="case-flow-muted">No flags detected.</div>
                ) : (
                  flags.map((flag) => (
                    <div key={flag.id} className="case-flow-row">
                      <div>
                        <div className="case-flow-muted">
                          {flag.flag_type} · {flag.status}
                        </div>
                        <div>{flag.terms.join(', ')}</div>
                      </div>
                      {flag.status === 'open' ? (
                        <button className="case-flow-btn outline" onClick={() => resolveFlag(flag.id)}>
                          Resolve
                        </button>
                      ) : (
                        <span className="case-flow-tag">Resolved</span>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ) : null}

        {currentStep.key === 'adversarial' ? (
          <div>
            <div className="case-flow-step-header">
              <div>
                <h2>Adversarial Debate</h2>
                <p className="case-flow-help">Document the right to be heard before recommending any sanction.</p>
              </div>
              <button className="case-flow-info" onClick={toggleGuidance} type="button" aria-label="Toggle guidance">
                i
              </button>
            </div>
            {showGuidance ? (
              <div className="case-flow-guidance">
                <h4>Guidance</h4>
                <ul>
                  <li>Provide written notice and record whether assistance was requested.</li>
                  <li>Summaries should reflect both allegations and the employee response.</li>
                </ul>
              </div>
            ) : null}
            <div className="case-flow-card">
              <div className="case-flow-muted">Gate status: {caseData.gates.find((g) => g.gate_key === 'adversarial')?.status || 'pending'}</div>
              <label className="case-flow-label">
                <input
                  type="checkbox"
                  checked={adversarialGate.invitation_sent}
                  onChange={(e) => setAdversarialGate({ ...adversarialGate, invitation_sent: e.target.checked })}
                  disabled={isAnonymized}
                />
                Invitation sent
              </label>
              <label className="case-flow-label">
                Invitation date
                <input
                  type="date"
                  value={adversarialGate.invitation_date}
                  onChange={(e) => setAdversarialGate({ ...adversarialGate, invitation_date: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <label className="case-flow-label">
                <input
                  type="checkbox"
                  checked={adversarialGate.rights_acknowledged}
                  onChange={(e) => setAdversarialGate({ ...adversarialGate, rights_acknowledged: e.target.checked })}
                  disabled={isAnonymized}
                />
                Rights acknowledged
              </label>
              <label className="case-flow-label">
                Representative present
                <input
                  type="text"
                  value={adversarialGate.representative_present}
                  onChange={(e) => setAdversarialGate({ ...adversarialGate, representative_present: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <label className="case-flow-label">
                Interview summary
                <textarea
                  value={adversarialGate.interview_summary}
                  onChange={(e) => setAdversarialGate({ ...adversarialGate, interview_summary: e.target.value })}
                  disabled={isAnonymized}
                />
              </label>
              <div className="case-flow-inline">
                <button
                  className="case-flow-btn outline"
                  onClick={() =>
                    saveGate('adversarial', {
                      invitation_sent: !!adversarialGate.invitation_sent,
                      invitation_date: adversarialGate.invitation_date || null,
                      rights_acknowledged: !!adversarialGate.rights_acknowledged,
                      representative_present: adversarialGate.representative_present || null,
                      interview_summary: adversarialGate.interview_summary,
                    })
                  }
                  disabled={isAnonymized}
                >
                  Save gate
                </button>
                <button className="case-flow-btn outline" onClick={() => generateDocument('INTERVIEW_INVITATION')}>
                  Generate Invitation
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {currentStep.key === 'decision' ? (
          <div>
            <div className="case-flow-step-header">
              <div>
                <h2>Decision & Outcome</h2>
                <p className="case-flow-help">Finalize the outcome, capture the decision summary, and trigger erasure if needed.</p>
              </div>
              <button className="case-flow-info" onClick={toggleGuidance} type="button" aria-label="Toggle guidance">
                i
              </button>
            </div>
            {showGuidance ? (
              <div className="case-flow-guidance">
                <h4>Guidance</h4>
                <ul>
                  <li>Record a concise decision rationale tied to verified facts.</li>
                  <li>If no sanction, initiate erasure within retention timelines.</li>
                  <li>For serious cause, use the clock below to enforce jurisdictional deadlines.</li>
                </ul>
              </div>
            ) : null}
            <div className="case-flow-grid">
              <div className="case-flow-card">
                <h3>Decision</h3>
                <label className="case-flow-label">
                  Outcome
                  <select value={decisionOutcome} onChange={(e) => setDecisionOutcome(e.target.value)}>
                    <option value="NO_SANCTION">No Sanction</option>
                    <option value="SANCTION">Sanction</option>
                    <option value="TERMINATION">Termination</option>
                    <option value="OTHER">Other</option>
                  </select>
                </label>
                <label className="case-flow-label">
                  Decision summary
                  <textarea value={decisionSummary} onChange={(e) => setDecisionSummary(e.target.value)} />
                </label>
                <div className="case-flow-inline">
                  <button className="case-flow-btn outline" onClick={draftDecisionSummary} disabled={isAnonymized}>
                    Draft summary from notes
                  </button>
                  <span className="case-flow-muted">Auto-generate a factual timeline from case notes.</span>
                </div>
                {hasRoleSeparationConflict ? (
                  <div className="case-flow-warning">
                    Role separation conflict: {roleSeparationConflicts.join('; ')}. Legal override required to proceed.
                  </div>
                ) : null}
                <label className="case-flow-label">
                  Role separation override reason (LEGAL)
                  <input
                    type="text"
                    value={decisionOverrideReason}
                    onChange={(e) => setDecisionOverrideReason(e.target.value)}
                    placeholder="Required only if decision maker/investigator conflict"
                  />
                </label>
                <button className="case-flow-btn outline" onClick={recordDecision}>
                  Record decision
                </button>
                <button className="case-flow-btn outline" onClick={() => generateDocument('DISMISSAL_REASONS_LETTER')}>
                  Generate Dismissal Letter
                </button>
                {decisionOutcome === 'NO_SANCTION' ? (
                  <div className="case-flow-card">
                    <h3>Erasure</h3>
                    <button className="case-flow-btn outline" onClick={approveErasure}>
                      Approve erasure
                    </button>
                    <button className="case-flow-btn outline" onClick={executeErasure}>
                      Execute erasure
                    </button>
                  </div>
                ) : null}
              </div>
              <div className="case-flow-card">
                <h3>Legal approval</h3>
                <div className="case-flow-muted">
                  Gate status: {caseData.gates.find((g) => g.gate_key === 'legal')?.status || 'pending'}
                </div>
                <label className="case-flow-label">
                  Approval date
                  <input
                    type="datetime-local"
                    value={legalGate.approved_at}
                    onChange={(e) => setLegalGate({ ...legalGate, approved_at: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Approval note
                  <textarea
                    value={legalGate.approval_note}
                    onChange={(e) => setLegalGate({ ...legalGate, approval_note: e.target.value })}
                    placeholder="Optional context for legal approval."
                    disabled={isAnonymized}
                  />
                </label>
                <button
                  className="case-flow-btn outline"
                  onClick={() =>
                    saveGate('legal', {
                      approved_at: legalGate.approved_at || null,
                      approval_note: legalGate.approval_note || null,
                    })
                  }
                  disabled={isAnonymized}
                >
                  Record legal approval
                </button>
                {caseData.gates.find((g) => g.gate_key === 'legal')?.completed_by ? (
                  <div className="case-flow-muted">
                    Approved by {caseData.gates.find((g) => g.gate_key === 'legal')?.completed_by}
                  </div>
                ) : null}
              </div>
              <div className="case-flow-card">
                <h3>Consistency check</h3>
                <p className="case-flow-help">
                  Compare this decision against historical outcomes for similar cases.
                </p>
                <button className="case-flow-btn outline" onClick={runConsistencyCheck}>
                  Run consistency check
                </button>
                {consistency ? (
                  <div className="case-flow-meta">
                    <div>Sample size: {consistency.sample_size}</div>
                    <div>Jurisdiction: {consistency.jurisdiction}</div>
                    {consistency.playbook_key ? <div>Playbook: {consistency.playbook_key}</div> : null}
                    <div className="case-flow-divider" />
                    {consistency.outcomes.length === 0 ? (
                      <div className="case-flow-muted">No comparable outcomes yet.</div>
                    ) : (
                      consistency.outcomes.map((row) => (
                        <div key={`${row.outcome}-${row.count}`} className="case-flow-row">
                          <span>{row.outcome}</span>
                          <span>{row.count} ({row.percent}%)</span>
                        </div>
                      ))
                    )}
                    <div className="case-flow-muted">{consistency.recommendation}</div>
                    {consistency.warning ? <div className="case-flow-warning">{consistency.warning}</div> : null}
                  </div>
                ) : (
                  <div className="case-flow-muted">No consistency check run yet.</div>
                )}
              </div>
              <div className="case-flow-card">
                <h3>Serious cause (jurisdiction rules)</h3>
                <p className="case-flow-help">Track statutory deadlines once facts are confirmed.</p>
                <label className="case-flow-label">
                  <input
                    type="checkbox"
                    checked={seriousEnabledDraft}
                    onChange={(e) => setSeriousEnabledDraft(e.target.checked)}
                    disabled={isAnonymized}
                  />
                  Enable serious cause workflow
                </label>
                <button
                  className="case-flow-btn outline"
                  onClick={() => toggleSeriousCause(seriousEnabledDraft)}
                  disabled={isAnonymized}
                >
                  Save serious cause settings
                </button>
                <label className="case-flow-label">
                  Incident occurred
                  <input
                    type="datetime-local"
                    value={seriousDraft.date_incident_occurred || toLocalInput(caseData.date_incident_occurred)}
                    onChange={(e) =>
                      setSeriousDraft({ ...seriousDraft, date_incident_occurred: e.target.value })
                    }
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Investigation started
                  <input
                    type="datetime-local"
                    value={seriousDraft.date_investigation_started || toLocalInput(caseData.date_investigation_started)}
                    onChange={(e) =>
                      setSeriousDraft({ ...seriousDraft, date_investigation_started: e.target.value })
                    }
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Decision maker (optional)
                  <input
                    type="text"
                    value={seriousDraft.decision_maker}
                    onChange={(e) => setSeriousDraft({ ...seriousDraft, decision_maker: e.target.value })}
                    disabled={isAnonymized}
                  />
                </label>
                {seriousEnabledDraft ? (
                  <>
                    <label className="case-flow-label">
                      Facts confirmed
                      <input
                        type="datetime-local"
                        value={seriousDraft.facts_confirmed_at || toLocalInput(caseData.serious_cause?.facts_confirmed_at)}
                        onChange={(e) =>
                          setSeriousDraft({ ...seriousDraft, facts_confirmed_at: e.target.value })
                        }
                        disabled={isAnonymized}
                      />
                    </label>
                    <button className="case-flow-btn outline" onClick={submitFindings} disabled={isAnonymized}>
                      Submit findings
                    </button>
                    <label className="case-flow-label">
                      Decision due
                      <input type="datetime-local" value={toLocalInput(caseData.serious_cause?.decision_due_at)} readOnly />
                    </label>
                    <label className="case-flow-label">
                      Dismissal due
                      <input type="datetime-local" value={toLocalInput(caseData.serious_cause?.dismissal_due_at)} readOnly />
                    </label>
                    <label className="case-flow-label">
                      Dismissal recorded
                      <input
                        type="datetime-local"
                        value={seriousDraft.dismissal_recorded_at}
                        onChange={(e) =>
                          setSeriousDraft({ ...seriousDraft, dismissal_recorded_at: e.target.value })
                        }
                        disabled={isAnonymized}
                      />
                    </label>
                    <button className="case-flow-btn outline" onClick={recordDismissal} disabled={isAnonymized}>
                      Record dismissal
                    </button>
                    <label className="case-flow-label">
                      Reasons sent
                      <input
                        type="datetime-local"
                        value={seriousDraft.reasons_sent_at}
                        onChange={(e) => setSeriousDraft({ ...seriousDraft, reasons_sent_at: e.target.value })}
                        disabled={isAnonymized}
                      />
                    </label>
                    <label className="case-flow-label">
                      Delivery method
                      <select
                        value={seriousDraft.reasons_delivery_method}
                        onChange={(e) =>
                          setSeriousDraft({ ...seriousDraft, reasons_delivery_method: e.target.value })
                        }
                        disabled={isAnonymized}
                      >
                        <option value="">Select method</option>
                        {DELIVERY_METHOD_OPTIONS.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="case-flow-label">
                      Proof URI (registered mail)
                      <input
                        type="text"
                        value={seriousDraft.reasons_delivery_proof_uri}
                        onChange={(e) =>
                          setSeriousDraft({ ...seriousDraft, reasons_delivery_proof_uri: e.target.value })
                        }
                        disabled={isAnonymized}
                      />
                    </label>
                    <button className="case-flow-btn outline" onClick={recordReasonsSent} disabled={isAnonymized}>
                      Record reasons sent
                    </button>
                    <label className="case-flow-label">
                      Missed deadline reason
                      <input
                        type="text"
                        value={seriousDraft.missed_reason}
                        onChange={(e) => setSeriousDraft({ ...seriousDraft, missed_reason: e.target.value })}
                        disabled={isAnonymized}
                      />
                    </label>
                    <button className="case-flow-btn outline" onClick={acknowledgeMissed} disabled={isAnonymized}>
                      Acknowledge missed deadline
                    </button>
                    <div className="case-flow-muted">Deadlines follow jurisdiction rules configured in tenant settings.</div>
                  </>
                ) : (
                  <div className="case-flow-muted">Enable serious cause to activate the clock and deadlines.</div>
                )}
              </div>
            </div>
          </div>
        ) : null}

        {currentStep.key === 'closure' ? (
          <div>
            <div className="case-flow-step-header">
              <div>
                <h2>Closure</h2>
                <p className="case-flow-help">Finalize documentation, export defensible artifacts, and apply data controls.</p>
              </div>
              <button className="case-flow-info" onClick={toggleGuidance} type="button" aria-label="Toggle guidance">
                i
              </button>
            </div>
            {showGuidance ? (
              <div className="case-flow-guidance">
                <h4>Guidance</h4>
                <ul>
                  <li>Export pack contains the audit trail and generated documents.</li>
                  <li>Anonymization clears sensitive data once retention obligations are met.</li>
                  <li>Update case status when legal/HR actions are completed.</li>
                </ul>
              </div>
            ) : null}
            <div className="case-flow-grid">
              <div className="case-flow-card">
                <h3>Reporting</h3>
                <p className="case-flow-help">
                  Generate a consolidated investigation report with triage, impact analysis, evidence, and decisions.
                </p>
                <label className="case-flow-label">
                  Document format
                  <select value={docFormat} onChange={(event) => setDocFormat(event.target.value)}>
                    <option value="txt">Text (.txt)</option>
                    <option value="pdf">PDF (.pdf)</option>
                    <option value="docx">DOCX (.docx)</option>
                  </select>
                </label>
                <div className="case-flow-muted">Readiness checklist</div>
                <div className="case-flow-pill-list">
                  <span className={`case-flow-pill ${reportSignals.triage ? 'good' : ''}`}>
                    Triage {reportSignals.triage ? '✓' : '•'}
                  </span>
                  <span className={`case-flow-pill ${reportSignals.impact ? 'good' : ''}`}>
                    Impact analysis {reportSignals.impact ? '✓' : '•'}
                  </span>
                  <span className={`case-flow-pill ${reportSignals.decision ? 'good' : ''}`}>
                    Decision {reportSignals.decision ? '✓' : '•'}
                  </span>
                  <span className={`case-flow-pill ${reportSignals.lessons ? 'good' : ''}`}>
                    Lessons learned {reportSignals.lessons ? '✓' : '•'}
                  </span>
                </div>
                <button className="case-flow-btn outline" onClick={() => generateDocument('INVESTIGATION_REPORT')}>
                  Generate investigation report
                </button>
              </div>
              <div className="case-flow-card">
                <h3>Sanity check</h3>
                <p className="case-flow-help">Scan the case file for missing mandatory items before closure.</p>
                <button className="case-flow-btn outline" onClick={loadSanityCheck}>
                  Run sanity check
                </button>
                {sanityCheck ? (
                  <>
                    <div className="case-flow-muted">
                      Score: {sanityCheck.score}% ({sanityCheck.completed}/{sanityCheck.total})
                    </div>
                    {sanityCheck.warnings.length > 0 ? (
                      <div className="case-flow-warning">
                        {sanityCheck.warnings.map((warn, idx) => (
                          <div key={`warn-${idx}`}>{warn}</div>
                        ))}
                      </div>
                    ) : null}
                    {sanityCheck.missing.length > 0 ? (
                      <div className="case-flow-meta">
                        <strong>Missing items</strong>
                        <ul className="case-flow-list">
                          {sanityCheck.missing.map((item, idx) => (
                            <li key={`missing-${idx}`}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <div className="case-flow-muted">All required items present.</div>
                    )}
                  </>
                ) : (
                  <div className="case-flow-muted">Run the check to see results.</div>
                )}
              </div>
              <div className="case-flow-card">
                <h3>Case status</h3>
                <label className="case-flow-label">
                  Status
                  <select value={caseData.status} onChange={(e) => updateStatus(e.target.value)}>
                    {STATUS_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <button className="case-flow-btn outline" onClick={() => generateDocument('ERASURE_CERTIFICATE')}>
                  Generate Erasure Certificate
                </button>
                <button className="case-flow-btn outline" onClick={exportPack}>
                  Export Pack
                </button>
              </div>
              <div className="case-flow-card">
                <h3>Data controls</h3>
                <p className="case-flow-help">
                  Anonymization clears subjects, evidence, notes, tasks, and gate data from this case.
                </p>
                <button className="case-flow-btn outline" onClick={anonymizeCase} disabled={isAnonymized}>
                  Anonymize case
                </button>
                {isAnonymized ? <div className="case-flow-warning">This case is anonymized.</div> : null}
              </div>
              <div className="case-flow-card">
                <h3>Root cause & actions</h3>
                <p className="case-flow-help">Capture lessons learned and remediation actions for the report.</p>
                <label className="case-flow-label">
                  Root cause
                  <textarea
                    value={lessonsDraft.root_cause}
                    onChange={(e) => setLessonsDraft({ ...lessonsDraft, root_cause: e.target.value })}
                    placeholder="e.g. Lack of training, policy gap, weak access controls."
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Action items
                  <textarea
                    value={lessonsDraft.action_items}
                    onChange={(e) => setLessonsDraft({ ...lessonsDraft, action_items: e.target.value })}
                    placeholder="e.g. Mandatory training, policy update, system hardening."
                    disabled={isAnonymized}
                  />
                </label>
                <button className="case-flow-btn outline" onClick={saveLessonsLearned} disabled={isAnonymized}>
                  Save lessons learned
                </button>
                {caseData.notes.find((note) => note.note_type === 'lessons_learned') ? (
                  <div className="case-flow-muted">Latest lessons learned captured.</div>
                ) : (
                  <div className="case-flow-muted">No lessons learned note yet.</div>
                )}
              </div>
              <div className="case-flow-card">
                <h3>DSAR redaction</h3>
                <p className="case-flow-help">
                  Document redactions before producing a DSAR export. Paste a JSON array or leave a note.
                </p>
                <label className="case-flow-label">
                  Redaction log (JSON or notes)
                  <textarea
                    value={redactionInput}
                    onChange={(e) => setRedactionInput(e.target.value)}
                    placeholder='e.g. [{"field":"witness_name","reason":"privacy"}]'
                    disabled={isAnonymized}
                  />
                </label>
                <div className="case-flow-inline">
                  <button className="case-flow-btn outline" onClick={suggestRedactions} disabled={isAnonymized}>
                    Suggest redactions
                  </button>
                  <span className="case-flow-muted">Uses regex heuristics to pre-fill PII candidates.</span>
                </div>
                <button className="case-flow-btn outline" onClick={exportRedactedPack} disabled={isAnonymized}>
                  Export redacted pack
                </button>
              </div>
              <div className="case-flow-card">
                <h3>Remediation export</h3>
                <p className="case-flow-help">
                  Capture the remediation statement for assessment intake. Available when outcome is not NO_SANCTION.
                </p>
                <label className="case-flow-label">
                  Remediation statement
                  <textarea
                    value={remediationInput}
                    onChange={(e) => setRemediationInput(e.target.value)}
                    placeholder="Summarize the proven issue and needed remediation."
                    disabled={isAnonymized}
                  />
                </label>
                <label className="case-flow-label">
                  Export format
                  <select
                    value={remediationFormat}
                    onChange={(e) => setRemediationFormat(e.target.value)}
                    disabled={isAnonymized}
                  >
                    <option value="json">JSON</option>
                    <option value="csv">CSV</option>
                  </select>
                </label>
                <button
                  className="case-flow-btn outline"
                  onClick={exportRemediation}
                  disabled={isAnonymized || remediationBlocked}
                >
                  Export remediation
                </button>
                {remediationBlocked ? (
                  <div className="case-flow-muted">Decision outcome required (non-NO_SANCTION).</div>
                ) : null}
                {caseData.remediation_exported_at ? (
                  <div className="case-flow-muted">
                    Last exported: {new Date(caseData.remediation_exported_at).toLocaleString()}
                  </div>
                ) : null}
              </div>
            </div>
            <div className="case-flow-card">
              <h3>Documents</h3>
              {documents.length === 0 ? (
                <div className="case-flow-muted">No documents yet.</div>
              ) : (
                documents.map((doc) => (
                  <div key={doc.id} className="case-flow-row">
                    <div>
                      <div className="case-flow-muted">
                        {doc.doc_type} · v{doc.version} · {doc.format}
                      </div>
                      <div>{doc.title}</div>
                    </div>
                    <button
                      className="case-flow-btn outline"
                      onClick={() =>
                        window.open(`${API_BASE}/cases/${caseData.case_id}/documents/${doc.id}/download`, '_blank')
                      }
                    >
                      Download
                    </button>
                  </div>
                ))
              )}
            </div>
            <div className="case-flow-card">
              <div className="case-flow-row">
                <h3>Audit timeline</h3>
                <button className="case-flow-btn outline small" onClick={() => goToStep('audit')}>
                  View audit log
                </button>
              </div>
              <div className="case-flow-muted">Audit log is available in the dedicated Audit step.</div>
            </div>
          </div>
        ) : null}
        {currentStep.key === 'audit' ? (
          <div>
            <div className="case-flow-step-header">
              <div>
                <h2>Audit log</h2>
                <p className="case-flow-help">Review all case actions with actor/date filters and field-level diffs.</p>
              </div>
              <button className="case-flow-info" onClick={toggleGuidance} type="button" aria-label="Toggle guidance">
                i
              </button>
            </div>
            {showGuidance ? (
              <div className="case-flow-guidance">
                <h4>Guidance</h4>
                <ul>
                  <li>Use actor filtering for targeted reviews (legal, HR, external counsel).</li>
                  <li>Date filters are local time; export the report for evidentiary packs.</li>
                  <li>Field-level diffs appear for case/task updates.</li>
                </ul>
              </div>
            ) : null}
            <div className="case-flow-grid">
              <div className="case-flow-card">
                <div className="case-flow-row">
                  <h3>Filters</h3>
                  <div className="case-flow-inline">
                    <button className="case-flow-btn outline small" onClick={() => loadAuditEvents()}>
                      Refresh
                    </button>
                    <button
                      className="case-flow-btn outline small"
                      onClick={() => {
                        setAuditActorFilter('')
                        setAuditFromFilter('')
                        setAuditToFilter('')
                        loadAuditEvents('')
                      }}
                    >
                      Clear
                    </button>
                  </div>
                </div>
                <div className="case-flow-audit-controls">
                  <label className="case-flow-label">
                    Actor
                    <input
                      type="text"
                      placeholder="e.g. legal_counsel"
                      value={auditActorFilter}
                      onChange={(event) => setAuditActorFilter(event.target.value)}
                      onBlur={() => loadAuditEvents()}
                    />
                  </label>
                  <label className="case-flow-label">
                    From
                    <input
                      type="date"
                      value={auditFromFilter}
                      onChange={(event) => setAuditFromFilter(event.target.value)}
                    />
                  </label>
                  <label className="case-flow-label">
                    To
                    <input
                      type="date"
                      value={auditToFilter}
                      onChange={(event) => setAuditToFilter(event.target.value)}
                    />
                  </label>
                </div>
              </div>
              <div className="case-flow-card">
                <div className="case-flow-row">
                  <h3>Audit timeline</h3>
                  <span className="case-flow-muted">{filteredAuditEvents.length} events</span>
                </div>
                {filteredAuditEvents.length === 0 ? (
                  <div className="case-flow-muted">No audit events yet.</div>
                ) : (
                  filteredAuditEvents.map((event, idx) => {
                    const changes = formatAuditChanges(event.details as Record<string, unknown>)
                    const context =
                      event.details && typeof event.details === 'object' && '_context' in event.details
                        ? (event.details as { _context?: { ip_address?: string; user_agent?: string } })._context
                        : undefined
                    return (
                      <div key={`${event.event_type}-${idx}`} className="case-flow-note">
                        <div className="case-flow-muted">
                          {event.event_type} · {new Date(event.created_at).toLocaleString()}
                        </div>
                        <div>{event.message}</div>
                        {event.actor ? <div className="case-flow-muted">Actor: {event.actor}</div> : null}
                        {context?.ip_address ? (
                          <div className="case-flow-muted">IP: {context.ip_address}</div>
                        ) : null}
                        {context?.user_agent ? (
                          <div className="case-flow-muted">Agent: {context.user_agent}</div>
                        ) : null}
                        {changes.length > 0 ? (
                          <div className="case-flow-audit-changes">
                            {changes.map((line) => (
                              <div key={line} className="case-flow-muted">
                                {line}
                              </div>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    )
                  })
                )}
              </div>
            </div>
          </div>
        ) : null}
      </div>
      <div className={`modal ${breakGlassOpen ? 'active' : ''}`}>
        <div className="modal-content">
          <div className="modal-header">
            <h3>Break Glass: Reveal PII</h3>
          </div>
          <div className="modal-body">
            <p className="case-flow-muted">
              This action is logged to the audit trail. Provide a justification to reveal PII for a limited window.
            </p>
            <label className="case-flow-label">
              Justification
              <textarea
                value={breakGlassReason}
                onChange={(event) => setBreakGlassReason(event.target.value)}
                placeholder="Reason for accessing sensitive identities"
              />
            </label>
            <label className="case-flow-label">
              Duration (minutes)
              <input
                type="number"
                min={15}
                max={480}
                value={breakGlassDuration}
                onChange={(event) => setBreakGlassDuration(Number(event.target.value))}
              />
            </label>
          </div>
          <div className="modal-footer">
            <button className="case-flow-btn outline" onClick={() => setBreakGlassOpen(false)}>
              Cancel
            </button>
            <button className="case-flow-btn" onClick={submitBreakGlass}>
              Unlock PII
            </button>
          </div>
        </div>
      </div>
      <div className={`modal ${showSuspensionModal ? 'active' : ''}`}>
        <div className="modal-content">
          <div className="modal-header">
            <h3>Suspension required (NL)</h3>
          </div>
          <div className="modal-body">
            <p>
              For Netherlands urgent dismissal cases, the subject should be suspended before proceeding.
              You can continue, but this may introduce legal risk.
            </p>
          </div>
          <div className="modal-footer">
            <button className="case-flow-btn outline" onClick={() => setShowSuspensionModal(false)}>
              Review
            </button>
            <button
              className="case-flow-btn"
              onClick={() => {
                setShowSuspensionModal(false)
                performSaveCaseDetails(true)
              }}
            >
              Continue & Save
            </button>
          </div>
        </div>
      </div>
      <div className={`modal ${transitionModalOpen ? 'active' : ''}`}>
        <div className="modal-content">
          <div className="modal-header">
            <h3>Stage blocked</h3>
          </div>
          <div className="modal-body">
            <p>Complete the following requirements before advancing:</p>
            <ul className="case-flow-blocker-list">
              {transitionBlockers.map((blocker) => (
                <li key={`${blocker.code}-${blocker.message}`}>{blocker.message}</li>
              ))}
            </ul>
          </div>
          <div className="modal-footer">
            <button className="case-flow-btn outline" onClick={() => setTransitionModalOpen(false)}>
              Close
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}

export default CaseFlow
