import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, apiJson } from '../lib/api'
import CaseWorkspace from '../components/CaseWorkspace'
import './Cases.css'

type CaseRecord = {
  case_id: string
  case_uuid: string
  title: string
  summary?: string | null
  jurisdiction: string
  vip_flag?: boolean
  status: string
  stage: string
  created_by?: string | null
  created_at: string
  is_anonymized: boolean
  serious_cause_enabled: boolean
  serious_cause?: {
    decision_due_at?: string | null
    dismissal_due_at?: string | null
  } | null
}

type SubjectDraft = {
  subject_type: string
  display_name: string
  reference: string
  manager_name: string
}

const SUBJECT_TYPE_OPTIONS = ['Employee', 'Contractor', 'Vendor', 'Third party', 'Unknown']
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

const Cases = () => {
  const navigate = useNavigate()
  const [cases, setCases] = useState<CaseRecord[]>([])
  const [status, setStatus] = useState('')
  const [newTitle, setNewTitle] = useState('')
  const [newSummary, setNewSummary] = useState('')
  const [newJurisdiction, setNewJurisdiction] = useState('Belgium')
  const [newVipFlag, setNewVipFlag] = useState(false)
  const [collapsedCases, setCollapsedCases] = useState<Record<string, boolean>>({})
  const [createOpen, setCreateOpen] = useState(false)
  const [createStep, setCreateStep] = useState(0)
  const [createdCaseId, setCreatedCaseId] = useState<string | null>(null)
  const [wizardStatus, setWizardStatus] = useState('')
  const [intakeDraft, setIntakeDraft] = useState({
    urgent_dismissal: false,
    subject_suspended: false,
    external_report_id: '',
    reporter_channel_id: '',
    reporter_key: '',
  })
  const [triageDraft, setTriageDraft] = useState({
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
  const [subjectDraft, setSubjectDraft] = useState<SubjectDraft>({
    subject_type: '',
    display_name: '',
    reference: '',
    manager_name: '',
  })
  const [subjectsAdded, setSubjectsAdded] = useState<SubjectDraft[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)
  const [breakGlassOpen, setBreakGlassOpen] = useState(false)
  const [breakGlassReason, setBreakGlassReason] = useState('')
  const [breakGlassDuration, setBreakGlassDuration] = useState(60)
  const [breakGlassExpiresAt, setBreakGlassExpiresAt] = useState<number | null>(null)

  const loadCases = () => {
    apiJson<CaseRecord[]>('/cases')
      .then((data) => setCases(data || []))
      .catch(() => setCases([]))
  }

  useEffect(() => {
    loadCases()
  }, [])

  const toggleCollapse = (caseId: string) => {
    setCollapsedCases((prev) => ({ ...prev, [caseId]: !prev[caseId] }))
  }

  const openFlow = (caseId: string) => {
    setSelectedCaseId(null)
    navigate(`/cases/${caseId}/flow/intake`)
  }

  const formatCountdown = (iso?: string | null) => {
    if (!iso) return null
    const diffMs = new Date(iso).getTime() - Date.now()
    const hours = Math.ceil(diffMs / 36e5)
    if (hours <= 0) return 'Overdue'
    if (hours < 24) return `${hours}h`
    const days = Math.ceil(hours / 24)
    return `${days}d`
  }

  const getBreakGlassExpiry = (caseId: string) => {
    const stored = localStorage.getItem(`break_glass_${caseId}`)
    if (!stored) return null
    try {
      const parsed = JSON.parse(stored) as { expiresAt?: number }
      if (parsed.expiresAt && parsed.expiresAt > Date.now()) {
        return parsed.expiresAt
      }
    } catch {
      // ignore malformed storage
    }
    localStorage.removeItem(`break_glass_${caseId}`)
    return null
  }

  const isPiiUnlocked = (caseId: string) => Boolean(getBreakGlassExpiry(caseId))

  const maskCaseText = (value: string | null | undefined, fallback: string, caseId: string) => {
    if (isPiiUnlocked(caseId)) return value || ''
    return fallback
  }

  const computeRiskScore = (impact: number, probability: number) =>
    Math.min(5, Math.max(1, Math.ceil((impact * probability) / 5)))

  const resetCreateWizard = () => {
    setCreateStep(0)
    setCreatedCaseId(null)
    setWizardStatus('')
    setNewTitle('')
    setNewSummary('')
    setNewJurisdiction('Belgium')
    setNewVipFlag(false)
    setIntakeDraft({
      urgent_dismissal: false,
      subject_suspended: false,
      external_report_id: '',
      reporter_channel_id: '',
      reporter_key: '',
    })
    setTriageDraft({
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
    setSubjectDraft({
      subject_type: '',
      display_name: '',
      reference: '',
      manager_name: '',
    })
    setSubjectsAdded([])
  }

  const openCreateWizard = () => {
    resetCreateWizard()
    setCreateOpen(true)
  }

  const closeCreateWizard = () => {
    setCreateOpen(false)
    resetCreateWizard()
  }

  const createCase = () => {
    if (!newTitle.trim()) {
      setWizardStatus('Provide a case title.')
      return
    }
    setWizardStatus('Creating case...')
    apiFetch('/cases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: newTitle.trim(),
        summary: newSummary.trim() || null,
        jurisdiction: newJurisdiction,
        vip_flag: newVipFlag,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!data?.case_id) throw new Error('No case id returned')
        setCreatedCaseId(data.case_id)
        setWizardStatus('Case created. Continue with intake details.')
        setCreateStep(1)
        loadCases()
      })
      .catch(() => setWizardStatus('Failed to create case.'))
  }

  const startIntakeStep = () => {
    if (createdCaseId) {
      setCreateStep(1)
      return
    }
    createCase()
  }

  const saveIntakeStep = () => {
    if (!createdCaseId) {
      setWizardStatus('Create the case before saving intake details.')
      return
    }
    setWizardStatus('Saving intake details...')
    apiFetch(`/cases/${createdCaseId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        urgent_dismissal: intakeDraft.urgent_dismissal,
        subject_suspended: intakeDraft.subject_suspended,
        external_report_id: intakeDraft.external_report_id || null,
        reporter_channel_id: intakeDraft.reporter_channel_id || null,
        reporter_key: intakeDraft.reporter_key || null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setWizardStatus('Intake details saved.')
        setCreateStep(2)
        loadCases()
      })
      .catch(() => setWizardStatus('Failed to save intake details.'))
  }

  const saveTriageStep = () => {
    if (!createdCaseId) {
      setWizardStatus('Create the case before saving triage.')
      return
    }
    if (!triageDraft.outcome) {
      setWizardStatus('Select a triage outcome before continuing.')
      return
    }
    setWizardStatus('Saving triage assessment...')
    apiFetch(`/cases/${createdCaseId}/gates/triage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        impact: triageDraft.impact,
        probability: triageDraft.probability,
        risk_score: triageDraft.risk_score,
        outcome: triageDraft.outcome,
        notes: triageDraft.notes || null,
        trigger_source: triageDraft.trigger_source || null,
        business_impact: triageDraft.business_impact || null,
        exposure_summary: triageDraft.exposure_summary || null,
        data_sensitivity: triageDraft.data_sensitivity || null,
        stakeholders: triageDraft.stakeholders || null,
        confidence_level: triageDraft.confidence_level || null,
        recommended_actions: triageDraft.recommended_actions || null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setWizardStatus('Triage assessment saved.')
        setCreateStep(3)
        loadCases()
      })
      .catch(() => setWizardStatus('Failed to save triage assessment.'))
  }

  const addSubject = () => {
    if (!createdCaseId) {
      setWizardStatus('Create the case before adding subjects.')
      return
    }
    if (!subjectDraft.subject_type || !subjectDraft.display_name) {
      setWizardStatus('Provide a subject type and display name.')
      return
    }
    setWizardStatus('Adding subject...')
    apiFetch(`/cases/${createdCaseId}/subjects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject_type: subjectDraft.subject_type,
        display_name: subjectDraft.display_name,
        reference: subjectDraft.reference || null,
        manager_name: subjectDraft.manager_name || null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setWizardStatus('Subject added.')
        setSubjectsAdded((prev) => [...prev, subjectDraft])
        setSubjectDraft({ subject_type: '', display_name: '', reference: '', manager_name: '' })
      })
      .catch(() => setWizardStatus('Failed to add subject.'))
  }

  const finishWizard = (openFlow: boolean) => {
    const caseId = createdCaseId
    closeCreateWizard()
    if (openFlow && caseId) {
      navigate(`/cases/${caseId}/flow/intake`)
    }
  }

  const updateStatus = (caseId: string, statusValue: string) => {
    apiFetch(`/cases/${caseId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: statusValue }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => loadCases())
      .catch(() => setStatus('Failed to update status.'))
  }

  const lockPII = () => {
    if (!selectedCaseId) return
    localStorage.removeItem(`break_glass_${selectedCaseId}`)
    setBreakGlassExpiresAt(null)
    setStatus('PII view locked.')
  }

  const submitBreakGlass = () => {
    if (!selectedCaseId) return
    const reason = breakGlassReason.trim()
    if (!reason) {
      setStatus('Break-glass reason is required.')
      return
    }
    const duration = Math.min(480, Math.max(15, Number(breakGlassDuration) || 60))
    apiFetch(`/cases/${selectedCaseId}/break-glass`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reason,
        scope: 'case_list',
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
        localStorage.setItem(`break_glass_${selectedCaseId}`, JSON.stringify({ expiresAt }))
        setBreakGlassExpiresAt(expiresAt)
        setBreakGlassReason('')
        setBreakGlassDuration(duration)
        setBreakGlassOpen(false)
        setStatus(`PII unlocked for ${duration} minutes.`)
      })
      .catch((err) => setStatus(err instanceof Error ? err.message : 'Failed to record break-glass action.'))
  }

  const closeCase = (item: CaseRecord) => {
    if (item.is_anonymized) {
      setStatus('Cannot close an anonymized case.')
      return
    }
    const confirmed = window.confirm('Close this case? You can reopen it until anonymized.')
    if (!confirmed) return
    updateStatus(item.case_id, 'CLOSED')
  }

  const reopenCase = (item: CaseRecord) => {
    if (item.is_anonymized) {
      setStatus('Cannot reopen an anonymized case.')
      return
    }
    const confirmed = window.confirm('Re-open this case?')
    if (!confirmed) return
    updateStatus(item.case_id, 'OPEN')
  }

  const selectedCase = cases.find((item) => item.case_id === selectedCaseId) || null
  const overlayOpen = createOpen || Boolean(selectedCaseId)
  const triageImpactOption = TRIAGE_IMPACT_LEVELS.find((option) => option.value === triageDraft.impact)
  const triageProbabilityOption = TRIAGE_PROBABILITY_LEVELS.find((option) => option.value === triageDraft.probability)
  const triageRiskOption = TRIAGE_RISK_LEVELS.find((option) => option.value === triageDraft.risk_score)
  const createSteps = ['Basics', 'Intake details', 'Triage', 'Subjects']
  const piiUnlockedSelected = selectedCaseId ? isPiiUnlocked(selectedCaseId) : false
  const breakGlassUntil =
    piiUnlockedSelected && breakGlassExpiresAt ? new Date(breakGlassExpiresAt).toLocaleTimeString() : ''

  useEffect(() => {
    if (selectedCaseId && !selectedCase) {
      setSelectedCaseId(null)
    }
  }, [selectedCaseId, selectedCase])

  useEffect(() => {
    if (!selectedCaseId) {
      setBreakGlassExpiresAt(null)
      setBreakGlassOpen(false)
      return
    }
    const expiry = getBreakGlassExpiry(selectedCaseId)
    setBreakGlassExpiresAt(expiry)
  }, [selectedCaseId])

  useEffect(() => {
    if (!breakGlassExpiresAt || !selectedCaseId) return
    const timer = window.setInterval(() => {
      if (Date.now() > breakGlassExpiresAt) {
        localStorage.removeItem(`break_glass_${selectedCaseId}`)
        setBreakGlassExpiresAt(null)
      }
    }, 30000)
    return () => window.clearInterval(timer)
  }, [breakGlassExpiresAt, selectedCaseId])

  useEffect(() => {
    document.body.classList.toggle('modal-open', overlayOpen)
    return () => {
      document.body.classList.remove('modal-open')
    }
  }, [overlayOpen])

  return (
    <>
      <CaseWorkspace
        className="cases-page"
        title="Cases"
        titleAs="h2"
        subtitle="Start or open an investigation. All case work happens in the flow."
        actions={
          <button className="cases-btn outline" onClick={() => navigate('/case-management/compliance')}>
            Compliance Overview
          </button>
        }
        leftTitle="Create a case"
        left={
          <>
            <div className="cases-muted">
              Launch a new investigation case with a clear scope, jurisdiction, and sensitivity flag.
            </div>
            <button className="cases-btn" onClick={openCreateWizard}>
              New case
            </button>
            {status ? <div className="cases-status">{status}</div> : null}
          </>
        }
        rightTitle="Active Cases"
        right={
          cases.length === 0 ? (
            <div className="cases-muted">No cases yet.</div>
          ) : (
            <div className="cases-list">
              {cases.map((item) => {
                const isCollapsed = collapsedCases[item.case_id] ?? true
                const hasJurisdiction = Boolean(item.jurisdiction)
                return (
                  <div key={item.case_id} className="cases-item">
                    <div className="cases-item-header">
                      <div>
                        <strong>{maskCaseText(item.title, 'Sensitive case', item.case_id)}</strong>
                        <div className="cases-meta">
                          {item.case_id} · {item.jurisdiction}
                          {item.vip_flag ? ' · VIP' : ''}
                        </div>
                        <div className="cases-meta">Immutable ID: {item.case_uuid}</div>
                      </div>
                      <div className="cases-actions">
                        <button className="cases-btn outline" onClick={() => setSelectedCaseId(item.case_id)}>
                          Details
                        </button>
                        <button className="cases-btn outline" onClick={() => toggleCollapse(item.case_id)}>
                          {isCollapsed ? 'Expand' : 'Minimize'}
                        </button>
                        <button className="cases-btn outline" onClick={() => openFlow(item.case_id)}>
                          Open Flow
                        </button>
                        {item.status === 'CLOSED' ? (
                          <button
                            className="cases-btn outline"
                            onClick={() => reopenCase(item)}
                            disabled={item.is_anonymized}
                          >
                            Re-open case
                          </button>
                        ) : (
                          <button
                            className="cases-btn outline"
                            onClick={() => closeCase(item)}
                            disabled={item.is_anonymized}
                          >
                            Close case
                          </button>
                        )}
                        <span className="cases-tag">{item.status}</span>
                        <span className={`cases-tag ${isPiiUnlocked(item.case_id) ? 'warning' : ''}`}>
                          PII {isPiiUnlocked(item.case_id) ? 'Unlocked' : 'Locked'}
                        </span>
                      </div>
                    </div>
                    {hasJurisdiction ? (
                      <div className="cases-banner">
                        Jurisdiction rules active: {item.jurisdiction}.
                      </div>
                    ) : null}
                    {isCollapsed ? null : (
                      <div className="cases-item-body">
                        <p>
                          {maskCaseText(
                            item.summary || 'No summary provided yet.',
                            'Summary hidden. Break glass to view.',
                            item.case_id
                          )}
                        </p>
                        <div className="cases-meta-row">
                          <span className="cases-meta">Stage: {item.stage}</span>
                          <span className="cases-meta">Owner: {item.created_by || 'Unassigned'}</span>
                          <span className="cases-meta">
                            Created: {new Date(item.created_at).toLocaleString()}
                          </span>
                        </div>
                        {item.serious_cause_enabled ? (
                          <div className="cases-meta-row">
                            <span className="cases-tag warning">Serious cause enabled</span>
                            {item.serious_cause?.decision_due_at ? (
                              <span className="cases-tag warning">
                                Decision due: {formatCountdown(item.serious_cause.decision_due_at)}
                              </span>
                            ) : null}
                            {item.serious_cause?.dismissal_due_at ? (
                              <span className="cases-tag warning">
                                Dismissal due: {formatCountdown(item.serious_cause.dismissal_due_at)}
                              </span>
                            ) : null}
                          </div>
                        ) : null}
                        {item.is_anonymized ? <div className="cases-warning">Case anonymized.</div> : null}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )
        }
      />

      <div
        className={`overlay ${createOpen ? 'active' : ''}`}
        onClick={(event) => {
          if (event.target === event.currentTarget) closeCreateWizard()
        }}
      >
        <div className="overlay-panel cases-overlay" onClick={(event) => event.stopPropagation()}>
          <div className="overlay-header">
            <div>
              <h3 className="overlay-title">New case · {createSteps[createStep]}</h3>
              <div className="overlay-subtitle">
                Step {createStep + 1} of {createSteps.length}
                {createdCaseId ? ` · ${createdCaseId}` : ''}
              </div>
            </div>
            <button className="overlay-close" onClick={closeCreateWizard} aria-label="Close">
              ×
            </button>
          </div>
          <div className="overlay-body">
            {createStep === 0 ? (
              <>
                <label>
                  Title
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(event) => setNewTitle(event.target.value)}
                    placeholder="Suspected data exfiltration"
                  />
                </label>
                <label>
                  Summary
                  <textarea
                    value={newSummary}
                    onChange={(event) => setNewSummary(event.target.value)}
                    placeholder="Trigger, scope, and justification"
                  />
                </label>
                <label>
                  Jurisdiction
                  <select value={newJurisdiction} onChange={(event) => setNewJurisdiction(event.target.value)}>
                    <option>Belgium</option>
                    <option>Netherlands</option>
                    <option>Luxembourg</option>
                    <option>Ireland</option>
                    <option>EU (non-Belgium)</option>
                    <option>UK</option>
                    <option>US</option>
                  </select>
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={newVipFlag}
                    onChange={(event) => setNewVipFlag(event.target.checked)}
                  />
                  VIP / highly sensitive
                </label>
              </>
            ) : null}
            {createStep === 1 ? (
              <>
                <div className="cases-help">Capture intake flags and external report metadata.</div>
                <label>
                  <input
                    type="checkbox"
                    checked={intakeDraft.urgent_dismissal}
                    onChange={(event) =>
                      setIntakeDraft((prev) => ({ ...prev, urgent_dismissal: event.target.checked }))
                    }
                  />
                  Urgent dismissal case (NL guardrail)
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={intakeDraft.subject_suspended}
                    onChange={(event) =>
                      setIntakeDraft((prev) => ({ ...prev, subject_suspended: event.target.checked }))
                    }
                  />
                  Subject suspended (required for NL urgent cases)
                </label>
                {intakeDraft.urgent_dismissal && !intakeDraft.subject_suspended ? (
                  <div className="cases-warning">Netherlands urgent dismissal cases require suspension confirmation.</div>
                ) : null}
                <label>
                  External report ID (optional)
                  <input
                    type="text"
                    value={intakeDraft.external_report_id}
                    onChange={(event) =>
                      setIntakeDraft((prev) => ({ ...prev, external_report_id: event.target.value }))
                    }
                  />
                </label>
                <label>
                  Reporter channel ID (optional)
                  <input
                    type="text"
                    value={intakeDraft.reporter_channel_id}
                    onChange={(event) =>
                      setIntakeDraft((prev) => ({ ...prev, reporter_channel_id: event.target.value }))
                    }
                  />
                </label>
                <label>
                  Reporter key (optional)
                  <input
                    type="text"
                    value={intakeDraft.reporter_key}
                    onChange={(event) => setIntakeDraft((prev) => ({ ...prev, reporter_key: event.target.value }))}
                  />
                </label>
              </>
            ) : null}
            {createStep === 2 ? (
              <>
                <div className="cases-help">Describe impact and likelihood using plain-language levels.</div>
                <label>
                  Business impact
                  <select
                    value={triageDraft.impact}
                    onChange={(event) => {
                      const impact = Number(event.target.value)
                      setTriageDraft((prev) => ({
                        ...prev,
                        impact,
                        risk_score: computeRiskScore(impact, prev.probability),
                      }))
                    }}
                  >
                    {TRIAGE_IMPACT_LEVELS.map((option) => (
                      <option key={`impact-${option.value}`} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {triageImpactOption?.detail ? <span className="cases-help">{triageImpactOption.detail}</span> : null}
                </label>
                <label>
                  Likelihood
                  <select
                    value={triageDraft.probability}
                    onChange={(event) => {
                      const probability = Number(event.target.value)
                      setTriageDraft((prev) => ({
                        ...prev,
                        probability,
                        risk_score: computeRiskScore(prev.impact, probability),
                      }))
                    }}
                  >
                    {TRIAGE_PROBABILITY_LEVELS.map((option) => (
                      <option key={`prob-${option.value}`} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {triageProbabilityOption?.detail ? (
                    <span className="cases-help">{triageProbabilityOption.detail}</span>
                  ) : null}
                </label>
                <div className="cases-score-card">
                  <div>
                    <div className="cases-section-title">Overall risk</div>
                    <div className="cases-help">Calculated from impact and likelihood.</div>
                  </div>
                  <span className="cases-score-pill">{triageRiskOption?.label || 'TBD'}</span>
                </div>
                <label>
                  Trigger source
                  <input
                    list="triage-trigger-sources"
                    value={triageDraft.trigger_source}
                    onChange={(event) => setTriageDraft((prev) => ({ ...prev, trigger_source: event.target.value }))}
                    placeholder="e.g., alert, hotline, audit finding"
                  />
                  <datalist id="triage-trigger-sources">
                    <option value="Automated alert" />
                    <option value="Employee report" />
                    <option value="Audit finding" />
                    <option value="HR escalation" />
                    <option value="External tip" />
                  </datalist>
                </label>
                <label>
                  Data sensitivity
                  <select
                    value={triageDraft.data_sensitivity}
                    onChange={(event) => setTriageDraft((prev) => ({ ...prev, data_sensitivity: event.target.value }))}
                  >
                    <option value="">Select sensitivity</option>
                    {DATA_SENSITIVITY_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Business impact summary
                  <textarea
                    value={triageDraft.business_impact}
                    onChange={(event) => setTriageDraft((prev) => ({ ...prev, business_impact: event.target.value }))}
                    placeholder="Describe the potential business impact."
                  />
                </label>
                <label>
                  Exposure summary
                  <textarea
                    value={triageDraft.exposure_summary}
                    onChange={(event) => setTriageDraft((prev) => ({ ...prev, exposure_summary: event.target.value }))}
                    placeholder="Describe the data, systems, or processes exposed."
                  />
                </label>
                <label>
                  Stakeholders impacted
                  <input
                    type="text"
                    value={triageDraft.stakeholders}
                    onChange={(event) => setTriageDraft((prev) => ({ ...prev, stakeholders: event.target.value }))}
                    placeholder="e.g., Legal, HR, Comms, Finance"
                  />
                </label>
                <label>
                  Confidence level
                  <select
                    value={triageDraft.confidence_level}
                    onChange={(event) => setTriageDraft((prev) => ({ ...prev, confidence_level: event.target.value }))}
                  >
                    <option value="">Select confidence</option>
                    {TRIAGE_CONFIDENCE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Recommended next actions
                  <textarea
                    value={triageDraft.recommended_actions}
                    onChange={(event) => setTriageDraft((prev) => ({ ...prev, recommended_actions: event.target.value }))}
                    placeholder="Immediate actions or decision gates."
                  />
                </label>
                <label>
                  Triage outcome
                  <select
                    value={triageDraft.outcome}
                    onChange={(event) => setTriageDraft((prev) => ({ ...prev, outcome: event.target.value }))}
                  >
                    <option value="">Select outcome</option>
                    {TRIAGE_OUTCOME_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Notes (optional)
                  <textarea
                    value={triageDraft.notes}
                    onChange={(event) => setTriageDraft((prev) => ({ ...prev, notes: event.target.value }))}
                  />
                </label>
              </>
            ) : null}
            {createStep === 3 ? (
              <>
                <div className="cases-help">Add the primary subjects in scope. You can add more later in the flow.</div>
                <label>
                  Subject type
                  <input
                    list="subject-types"
                    value={subjectDraft.subject_type}
                    onChange={(event) => setSubjectDraft((prev) => ({ ...prev, subject_type: event.target.value }))}
                    placeholder="Employee"
                  />
                  <datalist id="subject-types">
                    {SUBJECT_TYPE_OPTIONS.map((option) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                </label>
                <label>
                  Display name
                  <input
                    type="text"
                    value={subjectDraft.display_name}
                    onChange={(event) => setSubjectDraft((prev) => ({ ...prev, display_name: event.target.value }))}
                    placeholder="Jane Doe"
                  />
                </label>
                <label>
                  Reference (optional)
                  <input
                    type="text"
                    value={subjectDraft.reference}
                    onChange={(event) => setSubjectDraft((prev) => ({ ...prev, reference: event.target.value }))}
                    placeholder="Employee ID"
                  />
                </label>
                <label>
                  Manager name (optional)
                  <input
                    type="text"
                    value={subjectDraft.manager_name}
                    onChange={(event) => setSubjectDraft((prev) => ({ ...prev, manager_name: event.target.value }))}
                    placeholder="Manager name"
                  />
                </label>
                <button className="cases-btn outline" onClick={addSubject}>
                  Add subject
                </button>
                {subjectsAdded.length ? (
                  <div className="cases-pill-list">
                    {subjectsAdded.map((subject, index) => (
                      <span key={`${subject.display_name}-${index}`} className="cases-pill">
                        {subject.display_name} ({subject.subject_type})
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="cases-muted">No subjects added yet.</div>
                )}
              </>
            ) : null}
            {wizardStatus ? <div className="cases-status">{wizardStatus}</div> : null}
          </div>
          <div className="overlay-footer">
            {createStep > 0 ? (
              <button className="cases-btn outline" onClick={() => setCreateStep((prev) => Math.max(0, prev - 1))}>
                Back
              </button>
            ) : (
              <button className="cases-btn outline" onClick={closeCreateWizard}>
                Cancel
              </button>
            )}
            {createStep === 0 ? (
              <button className="cases-btn" onClick={startIntakeStep}>
                Start intake
              </button>
            ) : null}
            {createStep === 1 ? (
              <button className="cases-btn" onClick={saveIntakeStep}>
                Save & continue
              </button>
            ) : null}
            {createStep === 2 ? (
              <button className="cases-btn" onClick={saveTriageStep}>
                Save triage
              </button>
            ) : null}
            {createStep === 3 ? (
              <>
                <button className="cases-btn outline" onClick={() => finishWizard(false)}>
                  Finish
                </button>
                <button className="cases-btn" onClick={() => finishWizard(true)} disabled={!createdCaseId}>
                  Open case flow
                </button>
              </>
            ) : null}
          </div>
        </div>
      </div>

      <div
        className={`overlay ${selectedCase ? 'active' : ''}`}
        onClick={(event) => {
          if (event.target === event.currentTarget) setSelectedCaseId(null)
        }}
      >
        {selectedCase ? (
          <div className="overlay-panel wide" onClick={(event) => event.stopPropagation()}>
            <div className="overlay-header">
              <div>
                <h3 className="overlay-title">
                  {maskCaseText(selectedCase.title, 'Sensitive case', selectedCase.case_id)}
                </h3>
                <div className="overlay-subtitle">
                  {selectedCase.case_id} · {selectedCase.jurisdiction}
                </div>
              </div>
              <div className="cases-inline">
                <span className="cases-tag">{selectedCase.status}</span>
                <span className={`cases-tag ${piiUnlockedSelected ? 'warning' : ''}`}>
                  PII {piiUnlockedSelected ? 'Unlocked' : 'Locked'}
                </span>
                {breakGlassUntil ? <span className="cases-muted">until {breakGlassUntil}</span> : null}
                {piiUnlockedSelected ? (
                  <button className="cases-btn outline" onClick={lockPII}>
                    Lock PII
                  </button>
                ) : (
                  <button
                    className="cases-btn outline"
                    onClick={() => setBreakGlassOpen(true)}
                    disabled={selectedCase.is_anonymized}
                  >
                    Break Glass
                  </button>
                )}
                <button className="overlay-close" onClick={() => setSelectedCaseId(null)} aria-label="Close">
                  ×
                </button>
              </div>
            </div>
            <div className="overlay-body">
              <p className="cases-muted">
                {maskCaseText(
                  selectedCase.summary || 'No summary provided yet.',
                  'Summary hidden. Break glass to view.',
                  selectedCase.case_id
                )}
              </p>
              <div className="cases-meta-row">
                <span className="cases-meta">Stage: {selectedCase.stage}</span>
                <span className="cases-meta">Owner: {selectedCase.created_by || 'Unassigned'}</span>
                <span className="cases-meta">
                  Created: {new Date(selectedCase.created_at).toLocaleString()}
                </span>
              </div>
              <div className="cases-meta-row">
                <span className="cases-meta">Immutable ID: {selectedCase.case_uuid}</span>
                {selectedCase.vip_flag ? <span className="cases-tag warning">VIP</span> : null}
                {selectedCase.is_anonymized ? <span className="cases-tag warning">Anonymized</span> : null}
              </div>
              {selectedCase.serious_cause_enabled ? (
                <div className="cases-meta-row">
                  <span className="cases-tag warning">Serious cause enabled</span>
                  {selectedCase.serious_cause?.decision_due_at ? (
                    <span className="cases-tag warning">
                      Decision due: {formatCountdown(selectedCase.serious_cause.decision_due_at)}
                    </span>
                  ) : null}
                  {selectedCase.serious_cause?.dismissal_due_at ? (
                    <span className="cases-tag warning">
                      Dismissal due: {formatCountdown(selectedCase.serious_cause.dismissal_due_at)}
                    </span>
                  ) : null}
                </div>
              ) : null}
              <div className="cases-divider" />
              <div className="cases-inline-grid">
                <div className="cases-inline">
                  <div className="cases-section-title">Next actions</div>
                  <div className="cases-muted">Open the flow to continue work or jump to audit.</div>
                </div>
                <div className="cases-inline">
                  <button className="cases-btn outline" onClick={() => openFlow(selectedCase.case_id)}>
                    Open Flow
                  </button>
                  <button
                    className="cases-btn outline"
                    onClick={() => {
                      setSelectedCaseId(null)
                      navigate(`/cases/${selectedCase.case_id}/flow/audit`)
                    }}
                  >
                    Open Audit
                  </button>
                </div>
              </div>
            </div>
            <div className="overlay-footer">
              {selectedCase.status === 'CLOSED' ? (
                <button className="cases-btn outline" onClick={() => reopenCase(selectedCase)} disabled={selectedCase.is_anonymized}>
                  Re-open case
                </button>
              ) : (
                <button className="cases-btn outline" onClick={() => closeCase(selectedCase)} disabled={selectedCase.is_anonymized}>
                  Close case
                </button>
              )}
              <button className="cases-btn" onClick={() => setSelectedCaseId(null)}>
                Done
              </button>
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
            <p className="cases-muted">
              This action is logged. Provide a justification to reveal sensitive details for a limited time.
            </p>
            <label>
              Justification
              <textarea
                value={breakGlassReason}
                onChange={(event) => setBreakGlassReason(event.target.value)}
                placeholder="Reason for accessing sensitive identities"
              />
            </label>
            <label>
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
            <button className="cases-btn outline" onClick={() => setBreakGlassOpen(false)}>
              Cancel
            </button>
            <button className="cases-btn" onClick={submitBreakGlass}>
              Unlock PII
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

export default Cases
