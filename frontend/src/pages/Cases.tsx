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

const Cases = () => {
  const navigate = useNavigate()
  const [cases, setCases] = useState<CaseRecord[]>([])
  const [status, setStatus] = useState('')
  const [newTitle, setNewTitle] = useState('')
  const [newSummary, setNewSummary] = useState('')
  const [newJurisdiction, setNewJurisdiction] = useState('Belgium')
  const [newVipFlag, setNewVipFlag] = useState(false)
  const [collapsedCases, setCollapsedCases] = useState<Record<string, boolean>>({})

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

  const createCase = () => {
    if (!newTitle.trim()) {
      setStatus('Provide a case title.')
      return
    }
    setStatus('Creating case...')
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
      .then(() => {
        setNewTitle('')
        setNewSummary('')
        setNewVipFlag(false)
        setStatus('Case created.')
        loadCases()
      })
      .catch(() => setStatus('Failed to create case.'))
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

  return (
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
      leftTitle="Create Case"
      left={
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
          <button className="cases-btn" onClick={createCase}>
            Create Case
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
              const isCollapsed = !!collapsedCases[item.case_id]
              const hasJurisdiction = Boolean(item.jurisdiction)
              return (
                <div key={item.case_id} className="cases-item">
                  <div className="cases-item-header">
                    <div>
                      <strong>{item.title}</strong>
                      <div className="cases-meta">
                        {item.case_id} · {item.jurisdiction}
                        {item.vip_flag ? ' · VIP' : ''}
                      </div>
                      <div className="cases-meta">Immutable ID: {item.case_uuid}</div>
                    </div>
                    <div className="cases-actions">
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
                    </div>
                  </div>
                  {hasJurisdiction ? (
                    <div className="cases-banner">
                      Jurisdiction rules active: {item.jurisdiction}.
                    </div>
                  ) : null}
                  {isCollapsed ? null : (
                    <div className="cases-item-body">
                      <p>{item.summary || 'No summary provided yet.'}</p>
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
  )
}

export default Cases
