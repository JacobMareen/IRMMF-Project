import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import CaseWorkspace from '../components/CaseWorkspace'
import './PiaCompliance.css'

type PiaKeyDate = {
  date: string
  requirement: string
}

type PiaBullet = {
  title: string
  detail: string
  tags?: string[] | null
}

type PiaSection = {
  key: string
  title: string
  summary: string
  bullets: PiaBullet[]
}

type PiaRoadmapPhase = {
  phase: string
  focus: string
  deliverables: string[]
}

type PiaOverview = {
  module_key: string
  title: string
  subtitle: string
  executive_summary: string
  key_dates: PiaKeyDate[]
  sections: PiaSection[]
  roadmap: PiaRoadmapPhase[]
}

type PiaWorkflowStep = {
  key: string
  title: string
  description: string
}

type PiaEvidencePlaceholder = {
  evidence_id: string
  label: string
  source: string
  notes?: string | null
  status: string
  created_at: string
}

type PiaCase = {
  case_id: string
  case_uuid: string
  title: string
  summary?: string | null
  jurisdiction: string
  status: string
  current_step: string
  evidence: PiaEvidencePlaceholder[]
  step_data: Record<string, { data: Record<string, string | boolean | null>; updated_at: string }>
  created_by?: string | null
  company_id?: string | null
  is_anonymized: boolean
  anonymized_at?: string | null
  created_at: string
  updated_at: string
}

type PiaAuditEvent = {
  event_type: string
  actor?: string | null
  message: string
  details?: Record<string, string | number | boolean | null>
  created_at: string
}

const PiaCompliance = () => {
  const navigate = useNavigate()
  const [overview, setOverview] = useState<PiaOverview | null>(null)
  const [workflow, setWorkflow] = useState<PiaWorkflowStep[]>([])
  const [cases, setCases] = useState<PiaCase[]>([])
  const [status, setStatus] = useState('Loading compliance overview...')
  const [caseStatus, setCaseStatus] = useState('')
  const [newTitle, setNewTitle] = useState('')
  const [newSummary, setNewSummary] = useState('')
  const [newJurisdiction, setNewJurisdiction] = useState('Belgium')
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [evidenceDraft, setEvidenceDraft] = useState<Record<string, { label: string; source: string }>>({})
  const [stepDrafts, setStepDrafts] = useState<Record<string, Record<string, Record<string, string | boolean>>>>({})
  const [auditLog, setAuditLog] = useState<Record<string, PiaAuditEvent[]>>({})
  const [auditOpen, setAuditOpen] = useState<Record<string, boolean>>({})

  const workflowIndex = useMemo(() => {
    const map: Record<string, number> = {}
    workflow.forEach((step, idx) => {
      map[step.key] = idx
    })
    return map
  }, [workflow])

  useEffect(() => {
    apiFetch(`/pia/overview`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data: PiaOverview | null) => {
        if (!data) throw new Error('No data')
        setOverview(data)
        setStatus('')
      })
      .catch(() => {
        setStatus('Unable to load compliance overview. Start the API to view module data.')
      })
  }, [])

  useEffect(() => {
    apiFetch(`/pia/workflow`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: PiaWorkflowStep[]) => {
        setWorkflow(data || [])
      })
      .catch(() => {
        setWorkflow([])
      })
  }, [])

  const loadCases = () => {
    apiFetch(`/pia/cases`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: PiaCase[]) => {
        setCases(data || [])
      })
      .catch(() => {
        setCases([])
      })
  }

  useEffect(() => {
    loadCases()
  }, [])

  const createCase = () => {
    if (!newTitle.trim()) {
      setCaseStatus('Provide a case title to create a case.')
      return
    }
    setCaseStatus('Creating case...')
    apiFetch(`/pia/cases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: newTitle.trim(),
        summary: newSummary.trim() || null,
        jurisdiction: newJurisdiction,
        user_id: currentUser || null,
        company_id: null,
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setNewTitle('')
        setNewSummary('')
        setCaseStatus('Case created.')
        loadCases()
      })
      .catch(() => {
        setCaseStatus('Failed to create case.')
      })
  }

  const advanceCase = (caseId: string) => {
    setCaseStatus(`Advancing ${caseId}...`)
    apiFetch(`/pia/cases/${caseId}/advance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setCaseStatus(`Advanced ${caseId}.`)
        loadCases()
      })
      .catch(() => {
        setCaseStatus('Failed to advance case.')
      })
  }

  const addEvidence = (caseId: string) => {
    const draft = evidenceDraft[caseId] || { label: '', source: '' }
    if (!draft.label.trim() || !draft.source.trim()) {
      setCaseStatus('Provide a label and source for the evidence placeholder.')
      return
    }
    setCaseStatus(`Adding evidence to ${caseId}...`)
    apiFetch(`/pia/cases/${caseId}/evidence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        label: draft.label.trim(),
        source: draft.source.trim(),
      }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setEvidenceDraft((prev) => ({ ...prev, [caseId]: { label: '', source: '' } }))
        setCaseStatus(`Evidence placeholder added to ${caseId}.`)
        loadCases()
      })
      .catch(() => {
        setCaseStatus('Failed to add evidence.')
      })
  }

  const anonymizeCase = (caseId: string) => {
    const confirmed = window.confirm(
      'This will permanently remove sensitive data from the case. Continue?'
    )
    if (!confirmed) return
    setCaseStatus(`Anonymizing ${caseId}...`)
    apiFetch(`/pia/cases/${caseId}/anonymize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ actor: currentUser || null, reason: 'User-triggered anonymization' }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setCaseStatus(`Anonymized ${caseId}.`)
        loadCases()
      })
      .catch(() => {
        setCaseStatus('Failed to anonymize case.')
      })
  }

  const saveStep = (caseItem: PiaCase, stepKey: string) => {
    const caseId = caseItem.case_id
    const draft = stepDrafts[caseId]?.[stepKey] || {}
    const stored = caseItem.step_data?.[stepKey]?.data || {}
    const payload = { ...stored, ...draft }
    setCaseStatus(`Saving ${stepKey} for ${caseId}...`)
    apiFetch(`/pia/cases/${caseId}/steps/${stepKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setCaseStatus(`Saved ${stepKey} for ${caseId}.`)
        loadCases()
      })
      .catch(() => {
        setCaseStatus('Failed to save step data.')
      })
  }

  const toggleAudit = (caseId: string) => {
    const isOpen = auditOpen[caseId]
    if (isOpen) {
      setAuditOpen((prev) => ({ ...prev, [caseId]: false }))
      return
    }
    apiFetch(`/pia/cases/${caseId}/audit`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: PiaAuditEvent[]) => {
        setAuditLog((prev) => ({ ...prev, [caseId]: data || [] }))
        setAuditOpen((prev) => ({ ...prev, [caseId]: true }))
      })
      .catch(() => {
        setAuditLog((prev) => ({ ...prev, [caseId]: [] }))
        setAuditOpen((prev) => ({ ...prev, [caseId]: true }))
      })
  }

  const exportSummary = (caseId: string) => {
    apiFetch(`/pia/cases/${caseId}/summary`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!data) throw new Error('No data')
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `pia-summary-${caseId}.json`
        document.body.appendChild(link)
        link.click()
        link.remove()
        URL.revokeObjectURL(url)
      })
      .catch(() => {
        setCaseStatus('Failed to export summary.')
      })
  }

  const updateStepDraft = (caseId: string, stepKey: string, field: string, value: string | boolean) => {
    setStepDrafts((prev) => ({
      ...prev,
      [caseId]: {
        ...(prev[caseId] || {}),
        [stepKey]: {
          ...(prev[caseId]?.[stepKey] || {}),
          [field]: value,
        },
      },
    }))
  }

  const getStepValue = (
    caseItem: PiaCase,
    stepKey: string,
    field: string,
    fallback: string | boolean = ''
  ) => {
    const draft = stepDrafts[caseItem.case_id]?.[stepKey]?.[field]
    if (draft !== undefined) return draft
    const stored = caseItem.step_data?.[stepKey]?.data?.[field]
    if (stored !== undefined) return stored as string | boolean
    return fallback
  }

  const renderStepForm = (caseItem: PiaCase) => {
    if (caseItem.is_anonymized) {
      return <div className="pia-muted">Case anonymized. Step data cleared.</div>
    }
    const stepKey = caseItem.current_step
    if (stepKey === 'legitimacy') {
      return (
        <div className="pia-step-form">
          <label className="pia-label">
            Legal basis
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'legal_basis', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'legal_basis', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Trigger summary
            <textarea
              className="pia-textarea"
              value={getStepValue(caseItem, stepKey, 'trigger_summary', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'trigger_summary', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Proportionality confirmed
            <select
              className="pia-select"
              value={String(getStepValue(caseItem, stepKey, 'proportionality_confirmed', false))}
              onChange={(event) =>
                updateStepDraft(caseItem.case_id, stepKey, 'proportionality_confirmed', event.target.value === 'true')
              }
            >
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </label>
          <label className="pia-label">
            Less intrusive steps tried
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'less_intrusive_steps', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'less_intrusive_steps', event.target.value)}
            />
          </label>
          <div className="pia-form-row">
            <label className="pia-label">
              Mandate owner
              <input
                className="pia-input"
                value={getStepValue(caseItem, stepKey, 'mandate_owner', '') as string}
                onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'mandate_owner', event.target.value)}
              />
            </label>
            <label className="pia-label">
              Mandate date
              <input
                className="pia-input"
                type="date"
                value={getStepValue(caseItem, stepKey, 'mandate_date', '') as string}
                onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'mandate_date', event.target.value)}
              />
            </label>
          </div>
        </div>
      )
    }
    if (stepKey === 'authorization') {
      return (
        <div className="pia-step-form">
          <label className="pia-label">
            Investigator name
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'investigator_name', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'investigator_name', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Investigator role
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'investigator_role', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'investigator_role', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Licensed
            <select
              className="pia-select"
              value={String(getStepValue(caseItem, stepKey, 'licensed', false))}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'licensed', event.target.value === 'true')}
            >
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </label>
          <label className="pia-label">
            License ID
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'license_id', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'license_id', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Conflict check passed
            <select
              className="pia-select"
              value={String(getStepValue(caseItem, stepKey, 'conflict_check_passed', false))}
              onChange={(event) =>
                updateStepDraft(caseItem.case_id, stepKey, 'conflict_check_passed', event.target.value === 'true')
              }
            >
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </label>
          <div className="pia-form-row">
            <label className="pia-label">
              Authorizer
              <input
                className="pia-input"
                value={getStepValue(caseItem, stepKey, 'authorizer', '') as string}
                onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'authorizer', event.target.value)}
              />
            </label>
            <label className="pia-label">
              Authorization date
              <input
                className="pia-input"
                type="date"
                value={getStepValue(caseItem, stepKey, 'authorization_date', '') as string}
                onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'authorization_date', event.target.value)}
              />
            </label>
          </div>
        </div>
      )
    }
    if (stepKey === 'evidence') {
      return (
        <div className="pia-step-form">
          <label className="pia-label">
            Collection scope
            <textarea
              className="pia-textarea"
              value={getStepValue(caseItem, stepKey, 'collection_scope', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'collection_scope', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Chain of custody owner
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'chain_of_custody_owner', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'chain_of_custody_owner', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Relevance tagging method
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'relevance_tagging_method', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'relevance_tagging_method', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Minimization notes
            <textarea
              className="pia-textarea"
              value={getStepValue(caseItem, stepKey, 'minimization_notes', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'minimization_notes', event.target.value)}
            />
          </label>
        </div>
      )
    }
    if (stepKey === 'interview') {
      return (
        <div className="pia-step-form">
          <label className="pia-label">
            Invitation sent
            <select
              className="pia-select"
              value={String(getStepValue(caseItem, stepKey, 'invitation_sent', false))}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'invitation_sent', event.target.value === 'true')}
            >
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </label>
          <label className="pia-label">
            Invitation date
            <input
              className="pia-input"
              type="date"
              value={getStepValue(caseItem, stepKey, 'invitation_date', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'invitation_date', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Rights acknowledged
            <select
              className="pia-select"
              value={String(getStepValue(caseItem, stepKey, 'rights_acknowledged', false))}
              onChange={(event) =>
                updateStepDraft(caseItem.case_id, stepKey, 'rights_acknowledged', event.target.value === 'true')
              }
            >
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </label>
          <label className="pia-label">
            Representative present
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'representative_present', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'representative_present', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Interview summary
            <textarea
              className="pia-textarea"
              value={getStepValue(caseItem, stepKey, 'interview_summary', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'interview_summary', event.target.value)}
            />
          </label>
        </div>
      )
    }
    if (stepKey === 'outcome') {
      return (
        <div className="pia-step-form">
          <label className="pia-label">
            Decision
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'decision', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'decision', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Sanction
            <input
              className="pia-input"
              value={getStepValue(caseItem, stepKey, 'sanction', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'sanction', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Erasure deadline
            <input
              className="pia-input"
              type="date"
              value={getStepValue(caseItem, stepKey, 'erasure_deadline', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'erasure_deadline', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Retention rationale
            <textarea
              className="pia-textarea"
              value={getStepValue(caseItem, stepKey, 'retention_rationale', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'retention_rationale', event.target.value)}
            />
          </label>
          <label className="pia-label">
            Outcome notes
            <textarea
              className="pia-textarea"
              value={getStepValue(caseItem, stepKey, 'outcome_notes', '') as string}
              onChange={(event) => updateStepDraft(caseItem.case_id, stepKey, 'outcome_notes', event.target.value)}
            />
          </label>
        </div>
      )
    }
    return null
  }

  return (
    <section className="pia-page">
      <div className="pia-hero">
        <div className="pia-card">
          <div className="pia-tag">PIA 2024</div>
          <h1>{overview?.title || 'Procedural Compliance Platform'}</h1>
          <p className="pia-subtitle">
            {overview?.subtitle || 'Investigation support for Belgian Private Investigations Act compliance.'}
          </p>
          <p className="pia-summary">{overview?.executive_summary || status}</p>
          <div className="pia-hero-actions">
            <button className="pia-btn outline" onClick={() => navigate('/case-management/cases')}>
              Investigation Cases
            </button>
          </div>
        </div>
        <div className="pia-card">
          <div className="pia-title">Key Dates</div>
          {overview?.key_dates?.length ? (
            <ul className="pia-date-list">
              {overview.key_dates.map((item) => (
                <li key={item.date}>
                  <strong>{item.date}</strong>
                  <span>{item.requirement}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="pia-muted">{status || 'No dates available.'}</div>
          )}
        </div>
      </div>

      <CaseWorkspace
        className="pia-case-workspace"
        title="Case Workspace"
        titleAs="h2"
        leftTitle="Create Case"
        rightTitle="Active Cases"
        left={
          <>
            <label className="pia-label">
              Title
              <input
                className="pia-input"
                type="text"
                value={newTitle}
                onChange={(event) => setNewTitle(event.target.value)}
                placeholder="Investigation mandate for suspected data exfiltration"
              />
            </label>
            <label className="pia-label">
              Summary
              <textarea
                className="pia-textarea"
                value={newSummary}
                onChange={(event) => setNewSummary(event.target.value)}
                placeholder="Capture the trigger, scope, and initial rationale."
              />
            </label>
            <label className="pia-label">
              Jurisdiction
              <select
                className="pia-select"
                value={newJurisdiction}
                onChange={(event) => setNewJurisdiction(event.target.value)}
              >
                <option>Belgium</option>
                <option>Netherlands</option>
                <option>Luxembourg</option>
                <option>Ireland</option>
                <option>EU (non-Belgium)</option>
                <option>UK</option>
                <option>US</option>
              </select>
            </label>
            <button className="pia-btn" onClick={createCase}>
              Create Case
            </button>
            {caseStatus ? <div className="pia-status">{caseStatus}</div> : null}
          </>
        }
        right={
          cases.length === 0 ? (
            <div className="pia-muted">No cases yet. Create the first compliance workflow case.</div>
          ) : (
            <div className="pia-case-list">
              {cases.map((item) => {
                const currentIndex = workflowIndex[item.current_step] ?? 0
                const atEnd = currentIndex >= workflow.length - 1
                const isClosed = item.status === 'closed'
                const isAnonymized = item.is_anonymized
                return (
                  <div key={item.case_id} className="pia-case-item">
                    <div className="pia-case-header">
                      <div>
                        <strong>{item.title}</strong>
                        <div className="pia-case-meta">
                          {item.case_id} · {item.jurisdiction}
                        </div>
                        <div className="pia-case-meta">
                          Immutable ID: {item.case_uuid}
                        </div>
                        <div className="pia-case-meta">
                          Owner: {item.created_by || 'Unassigned'} · Company: {item.company_id || 'Unassigned'}
                        </div>
                        {item.is_anonymized ? (
                          <div className="pia-case-meta">
                            Anonymized: {item.anonymized_at ? new Date(item.anonymized_at).toLocaleString() : 'Yes'}
                          </div>
                        ) : null}
                      </div>
                      <span className={`pia-case-status ${item.status}`}>{item.status}</span>
                    </div>
                    <p className="pia-case-summary">{item.summary || 'No summary captured.'}</p>
                    <div className="pia-step-track">
                      {workflow.map((step, index) => {
                        const state = index < currentIndex ? 'done' : index === currentIndex ? 'active' : 'pending'
                        return (
                          <div key={`${item.case_id}-${step.key}`} className={`pia-step ${state}`}>
                            <span>{step.title}</span>
                          </div>
                        )
                      })}
                    </div>
                    <div className="pia-case-actions">
                      <button
                        className="pia-btn outline"
                        onClick={() => advanceCase(item.case_id)}
                        disabled={isClosed || isAnonymized}
                      >
                        {isClosed ? 'Closed' : atEnd ? 'Close Case' : 'Advance Step'}
                      </button>
                      <div className="pia-form-shell">
                        <div className="pia-form-title">Current Step: {item.current_step}</div>
                        {renderStepForm(item)}
                        <button
                          className="pia-btn"
                          onClick={() => saveStep(item, item.current_step)}
                          disabled={isAnonymized}
                        >
                          Save Step Data
                        </button>
                      </div>
                      <div className="pia-evidence-inputs">
                        <input
                          className="pia-input"
                          type="text"
                          placeholder="Evidence label"
                          value={evidenceDraft[item.case_id]?.label || ''}
                          onChange={(event) =>
                            setEvidenceDraft((prev) => ({
                              ...prev,
                              [item.case_id]: {
                                label: event.target.value,
                                source: prev[item.case_id]?.source || '',
                              },
                            }))
                          }
                          disabled={isAnonymized}
                        />
                        <input
                          className="pia-input"
                          type="text"
                          placeholder="Source system"
                          value={evidenceDraft[item.case_id]?.source || ''}
                          onChange={(event) =>
                            setEvidenceDraft((prev) => ({
                              ...prev,
                              [item.case_id]: {
                                label: prev[item.case_id]?.label || '',
                                source: event.target.value,
                              },
                            }))
                          }
                          disabled={isAnonymized}
                        />
                        <button className="pia-btn" onClick={() => addEvidence(item.case_id)} disabled={isAnonymized}>
                          Add Evidence Placeholder
                        </button>
                      </div>
                    </div>
                    <div className="pia-audit-controls">
                      <button className="pia-btn outline" onClick={() => toggleAudit(item.case_id)}>
                        {auditOpen[item.case_id] ? 'Hide Audit Log' : 'View Audit Log'}
                      </button>
                      <button className="pia-btn" onClick={() => exportSummary(item.case_id)}>
                        Export Case Summary
                      </button>
                      <button className="pia-btn outline" onClick={() => anonymizeCase(item.case_id)} disabled={isAnonymized}>
                        {isAnonymized ? 'Anonymized' : 'Anonymize Case'}
                      </button>
                    </div>
                    {auditOpen[item.case_id] ? (
                      <div className="pia-audit-list">
                        {(auditLog[item.case_id] || []).length === 0 ? (
                          <div className="pia-muted">No audit events yet.</div>
                        ) : (
                          (auditLog[item.case_id] || []).map((event, idx) => (
                            <div key={`${item.case_id}-audit-${idx}`} className="pia-audit-item">
                              <div>
                                <strong>{event.event_type.replace('_', ' ')}</strong>
                                <span className="pia-audit-time">{new Date(event.created_at).toLocaleString()}</span>
                              </div>
                              <p>{event.message}</p>
                              {event.actor ? <span className="pia-audit-actor">Actor: {event.actor}</span> : null}
                            </div>
                          ))
                        )}
                      </div>
                    ) : null}
                    {item.evidence?.length ? (
                      <div className="pia-evidence-list">
                        {item.evidence.map((ev) => (
                          <div key={`${item.case_id}-${ev.evidence_id}`} className="pia-evidence-item">
                            <strong>{ev.label}</strong>
                            <span>{ev.source}</span>
                            <span className="pia-evidence-status">{ev.status}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="pia-muted">No evidence placeholders yet.</div>
                    )}
                  </div>
                )
              })}
            </div>
          )
        }
      />

      <section className="pia-sections">
        <div className="pia-section-title">Module Blueprint</div>
        {overview?.sections?.length ? (
          <div className="pia-section-grid">
            {overview.sections.map((section) => (
              <article key={section.key} className="pia-section-card">
                <div className="pia-section-header">
                  <h3>{section.title}</h3>
                  <p>{section.summary}</p>
                </div>
                <div className="pia-bullets">
                  {section.bullets.map((bullet) => (
                    <div key={`${section.key}-${bullet.title}`} className="pia-bullet">
                      <div className="pia-bullet-title">{bullet.title}</div>
                      <div className="pia-bullet-detail">{bullet.detail}</div>
                      {bullet.tags?.length ? (
                        <div className="pia-bullet-tags">
                          {bullet.tags.map((tag) => (
                            <span key={`${section.key}-${bullet.title}-${tag}`} className="pia-tag-pill">
                              {tag}
                            </span>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="pia-muted">No module sections loaded.</div>
        )}
      </section>

      <section className="pia-roadmap">
        <div className="pia-section-title">Roadmap</div>
        {overview?.roadmap?.length ? (
          <div className="pia-roadmap-grid">
            {overview.roadmap.map((phase) => (
              <div key={phase.phase} className="pia-roadmap-card">
                <div className="pia-roadmap-phase">{phase.phase}</div>
                <div className="pia-roadmap-focus">{phase.focus}</div>
                <ul>
                  {phase.deliverables.map((item) => (
                    <li key={`${phase.phase}-${item}`}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        ) : (
          <div className="pia-muted">No roadmap data loaded.</div>
        )}
      </section>
    </section>
  )
}

export default PiaCompliance
