import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, readApiError } from '../lib/api'
import './AssessmentFlow.css'
import { clearStoredAssessmentId, describeAssessmentError, getStoredAssessmentId } from '../utils/assessment'
import { useToast } from '../context/ToastContext'
import { AssessmentNav } from '../components/AssessmentNav'
import { PageHeader } from '../components/PageHeader'

type AnswerOption = { a_id: string; answer_text: string; base_score: number; tags?: string }
type Question = {
  q_id: string
  domain: string
  question_title?: string
  question_text: string
  guidance?: string
  evidence_policy_id?: string | null
  options: AnswerOption[]
  is_multiselect?: boolean
}

type SidebarItem = {
  q_id: string
  domain: string
  title: string
  status: string
  reason?: string | null
}

type ResumptionState = {
  responses?: Record<string, string | string[]>
  deferred_ids?: string[]
  flagged_ids?: string[]
  reachable_path?: string[]
  sidebar_context?: SidebarItem[]
  next_best_qid?: string | null
  next_reason?: string | null
}

type EvidenceCheck = { id: string; label: string }
type EvidencePolicy = { label: string; description: string; checks: EvidenceCheck[]; required?: string[] }

const DEFAULT_EVIDENCE_CHECKS: EvidenceCheck[] = [
  { id: 'freshness', label: 'Updated in the last 12 months?' },
  { id: 'scope', label: 'Coverage is organization-wide?' },
  { id: 'independence', label: 'Independently reviewed?' },
  { id: 'sampling', label: 'Verified via sampling or testing?' },
  { id: 'traceability', label: 'Mapped to policy/standards?' },
  { id: 'ops_usage', label: 'Used in operational decisions?' },
]

const EVIDENCE_POLICIES: Record<string, EvidencePolicy> = {
  GOV_STD: {
    label: 'Governance standard',
    description: 'Governance evidence should be current, scoped, and reviewed.',
    checks: DEFAULT_EVIDENCE_CHECKS,
    required: ['freshness', 'scope'],
  },
  RISK_STD: {
    label: 'Risk/targeting standard',
    description: 'Risk evidence should show coverage and documented decisioning.',
    checks: DEFAULT_EVIDENCE_CHECKS.slice(0, 5),
    required: ['scope'],
  },
  OPS_STD: {
    label: 'Operational standard',
    description: 'Operational evidence should show live usage and oversight.',
    checks: DEFAULT_EVIDENCE_CHECKS,
    required: ['ops_usage'],
  },
  CULT_SOFT: {
    label: 'Culture soft',
    description: 'Soft-signal evidence is optional but increases confidence.',
    checks: DEFAULT_EVIDENCE_CHECKS.slice(0, 4),
  },
  LEG_STRICT: {
    label: 'Legal strict',
    description: 'Legal evidence requires defensible artifacts and traceability.',
    checks: DEFAULT_EVIDENCE_CHECKS,
    required: ['freshness', 'traceability'],
  },
  HUMAN_BIO: {
    label: 'Human bio-social',
    description: 'Human evidence should show scope and validated sampling.',
    checks: DEFAULT_EVIDENCE_CHECKS.slice(0, 5),
    required: ['scope', 'sampling'],
  },
  FRICTION_AI: {
    label: 'Friction/AI arbitrage',
    description: 'Evidence should show monitoring and traceable controls.',
    checks: DEFAULT_EVIDENCE_CHECKS,
    required: ['sampling', 'traceability'],
  },
  TECH_STRICT: {
    label: 'Technical strict',
    description: 'Technical evidence must show testing and traceability.',
    checks: DEFAULT_EVIDENCE_CHECKS,
    required: ['sampling', 'traceability'],
  },
}

const AssessmentFlow = () => {
  const navigate = useNavigate()
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [assessmentId, setAssessmentId] = useState('')
  const [questions, setQuestions] = useState<Question[]>([])
  const [baseReachable, setBaseReachable] = useState<string[]>([])
  const [reachable, setReachable] = useState<string[]>([])
  const [baseSidebar, setBaseSidebar] = useState<SidebarItem[]>([])
  const [sidebar, setSidebar] = useState<SidebarItem[]>([])
  const [responses, setResponses] = useState<Record<string, string | string[]>>({})
  const [deferredIds, setDeferredIds] = useState<Set<string>>(new Set())
  const [flaggedIds, setFlaggedIds] = useState<Set<string>>(new Set())
  const [currentIndex, setCurrentIndex] = useState(0)
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null)
  const [status, setStatus] = useState('Loading assessment...')
  const [requiresIntake, setRequiresIntake] = useState(false)
  const [overrideDomains, setOverrideDomains] = useState<Set<string>>(new Set())
  const [nextBestId, setNextBestId] = useState<string | null>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [autoAdvance, setAutoAdvance] = useState(true)
  const [pendingEvidence, setPendingEvidence] = useState<{
    q_id: string
    a_id: string
    score: number
    policy_id: string
  } | null>(null)
  const [evidenceChecks, setEvidenceChecks] = useState<Record<string, boolean>>({})
  const [hasEvidence, setHasEvidence] = useState(true)
  // const [logicToast, setLogicToast] = useState<string | null>(null) // REMOVED
  const [evidenceMissingRequired, setEvidenceMissingRequired] = useState<string[]>([])
  const currentQIdRef = useRef<string | null>(null)

  const { showToast } = useToast()

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    if (!assessmentId) return
    const raw = localStorage.getItem(`override_domains_${assessmentId}`)
    if (!raw) {
      setOverrideDomains(new Set())
      return
    }
    try {
      const list = JSON.parse(raw)
      if (Array.isArray(list)) setOverrideDomains(new Set(list))
    } catch {
      setOverrideDomains(new Set())
    }
  }, [assessmentId])

  useEffect(() => {
    if (!assessmentId) return
    const handler = (event: StorageEvent) => {
      if (event.key !== `override_domains_${assessmentId}`) return
      if (!event.newValue) {
        setOverrideDomains(new Set())
        return
      }
      try {
        const list = JSON.parse(event.newValue)
        if (Array.isArray(list)) setOverrideDomains(new Set(list))
      } catch {
        setOverrideDomains(new Set())
      }
    }
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [assessmentId])

  useEffect(() => {
    if (!assessmentId) {
      setStatus('No assessment selected.')
      return
    }
    const controller = new AbortController()
    setStatus('Loading assessment...')
    Promise.all([
      apiFetch(`/questions/all?assessment_id=${assessmentId}`, { signal: controller.signal }),
      apiFetch(`/assessment/${assessmentId}/resume`, { signal: controller.signal }),
      apiFetch(`/intake/${assessmentId}`, { signal: controller.signal }),
    ])
      .then(async ([qResp, rResp, intakeResp]) => {
        if (qResp.status === 404 || rResp.status === 404) {
          clearStoredAssessmentId(assessmentId, currentUser)
          setStatus('Assessment not found. Returning to the hub...')
          navigate('/assessment', { replace: true })
          return
        }
        if (!qResp.ok || !rResp.ok) {
          const detail = !qResp.ok ? await readApiError(qResp) : await readApiError(rResp)
          throw new Error(describeAssessmentError(detail, 'Assessment data unavailable.'))
        }
        const allQuestions = (await qResp.json()) as Question[]
        const state = (await rResp.json()) as ResumptionState
        setQuestions(allQuestions)
        applyState(state)

        const intakeRows = intakeResp.ok ? ((await intakeResp.json()) as Array<{ value?: string }>) : []
        const answered = intakeRows.filter((row) => row.value).length
        setRequiresIntake(answered === 0)
        setStatus('')
      })
      .catch((err) => {
        setStatus(err instanceof Error ? err.message : 'Failed to load assessment.')
      })

    return () => controller.abort()
  }, [assessmentId])

  useEffect(() => {
    const nextReachable = buildReachable(baseReachable, overrideDomains, questions)
    setReachable(nextReachable)
    const nextSidebar = buildSidebar(baseSidebar, overrideDomains, questions)
    setSidebar(nextSidebar)
  }, [baseReachable, baseSidebar, overrideDomains, questions])

  useEffect(() => {
    if (!reachable.length) return
    const preferred = nextBestId && reachable.includes(nextBestId) ? nextBestId : currentQIdRef.current
    const fallback = preferred && reachable.includes(preferred) ? preferred : reachable[0]
    const idx = reachable.indexOf(fallback)
    setCurrentIndex(idx >= 0 ? idx : 0)
  }, [reachable, nextBestId])

  useEffect(() => {
    const domain = localStorage.getItem('flow_start_domain')
    if (!domain || !reachable.length || !questions.length) return
    const responsesLocal = responses || {}
    const deferred = new Set(deferredIds)
    const next = reachable.find((qid) => {
      const q = questions.find((item) => item.q_id === qid)
      if (!q || q.domain !== domain) return false
      if (responsesLocal[qid] && !deferred.has(qid)) return false
      return true
    })
    const target = next || reachable.find((qid) => questions.find((item) => item.q_id === qid)?.domain === domain)
    if (target) {
      const idx = reachable.indexOf(target)
      if (idx >= 0) setCurrentIndex(idx)
    }
    localStorage.removeItem('flow_start_domain')
  }, [reachable, questions, responses, deferredIds])

  useEffect(() => {
    if (!expandedDomain) {
      const activeQ = questions.find((q) => q.q_id === reachable[0])
      if (activeQ) setExpandedDomain(activeQ.domain)
    }
  }, [expandedDomain, questions, reachable])

  const applyState = (state: ResumptionState) => {
    setResponses(state.responses || {})
    setDeferredIds(new Set(state.deferred_ids || []))
    setFlaggedIds(new Set(state.flagged_ids || []))
    setBaseReachable(state.reachable_path || [])
    setBaseSidebar(state.sidebar_context || [])
    setNextBestId(state.next_best_qid || null)
  }

  function buildReachable(base: string[], overrides: Set<string>, allQuestions: Question[]) {
    if (!base.length) return []
    if (!overrides.size) return base
    const baseSet = new Set(base)
    const extra = allQuestions
      .filter((q) => overrides.has(q.domain) && !baseSet.has(q.q_id))
      .sort((a, b) => a.domain.localeCompare(b.domain) || a.q_id.localeCompare(b.q_id))
    return base.concat(extra.map((q) => q.q_id))
  }

  function buildSidebar(base: SidebarItem[], overrides: Set<string>, allQuestions: Question[]) {
    if (!overrides.size) return base
    const baseIds = new Set(base.map((item) => item.q_id))
    const extra = allQuestions
      .filter((q) => overrides.has(q.domain) && !baseIds.has(q.q_id))
      .sort((a, b) => a.domain.localeCompare(b.domain) || a.q_id.localeCompare(b.q_id))
      .map((q) => ({
        q_id: q.q_id,
        domain: q.domain,
        title: q.question_title || q.question_text,
        status: 'override',
      }))
    return base.concat(extra)
  }

  function isOverrideQuestion(qId: string) {
    const q = questions.find((item) => item.q_id === qId)
    if (!q) return false
    return overrideDomains.has(q.domain) && !baseReachable.includes(qId)
  }

  const currentQId = reachable[currentIndex]
  const currentQuestion = questions.find((q) => q.q_id === currentQId)

  useEffect(() => {
    currentQIdRef.current = currentQId || null
  }, [currentQId])

  const isMultiSelectQuestion = (q: Question) => {
    return q.options.some((opt) => opt.tags === 'multiselect')
  }

  const getScoreForAnswer = (qId: string, aId: string) => {
    const q = questions.find((item) => item.q_id === qId)
    const opt = q?.options?.find((o) => o.a_id === aId)
    return opt ? opt.base_score : 0
  }

  const calculateMultiSelectScore = (_q: Question, selectedAIds: string[]) => {
    const count = selectedAIds.length
    if (count === 0) return 0
    if (count <= 2) return 1
    if (count <= 4) return 2
    if (count <= 6) return 3
    return 4
  }

  const submitAnswer = async (payload: {
    q_id: string
    a_id: string
    score: number
    is_deferred?: boolean
    is_flagged?: boolean
    evidence?: Record<string, unknown> | null
  }) => {
    if (!assessmentId) return
    const origin = isOverrideQuestion(payload.q_id) ? 'override' : 'adaptive'
    const q = questions.find((item) => item.q_id === payload.q_id)
    const res = await apiFetch(`/assessment/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        assessment_id: assessmentId,
        q_id: payload.q_id,
        a_id: payload.a_id,
        score: payload.score,
        pack_id: q?.domain || '',
        is_deferred: payload.is_deferred || false,
        is_flagged: payload.is_flagged || false,
        evidence: payload.evidence ?? null,
        origin,
      }),
    })
    if (!res.ok) throw new Error('Submit failed')
    const data = (await res.json()) as ResumptionState & { logic_reason?: string | null }
    applyState(data)
    if (autoAdvance && !flaggedIds.has(payload.q_id) && data.next_best_qid && data.reachable_path) {
      const nextReachable = buildReachable(data.reachable_path, overrideDomains, questions)
      setReachable(nextReachable)
      const idx = nextReachable.indexOf(data.next_best_qid)
      if (idx >= 0) {
        window.setTimeout(() => setCurrentIndex(idx), 300)
      }
    }
    if (data.logic_reason) {
      showToast(data.logic_reason, 'info', 4000)
    }
  }

  const handleAnswer = async (opt: AnswerOption) => {
    if (!currentQuestion) return

    // Multi-select handling: toggle selection
    if (isMultiSelectQuestion(currentQuestion)) {
      const currentSelection = responses[currentQuestion.q_id]
      const selectedIds = Array.isArray(currentSelection) ? currentSelection : []

      let newSelection: string[]
      if (selectedIds.includes(opt.a_id)) {
        // Deselect
        newSelection = selectedIds.filter((id) => id !== opt.a_id)
      } else {
        // Select
        newSelection = [...selectedIds, opt.a_id]
      }

      // Update local state immediately for UI responsiveness
      setResponses((prev) => ({ ...prev, [currentQuestion.q_id]: newSelection }))

      // Don't submit until user confirms or moves to next question
      return
    }

    // Single-select handling
    if (currentQuestion.evidence_policy_id) {
      setPendingEvidence({
        q_id: currentQuestion.q_id,
        a_id: opt.a_id,
        score: opt.base_score,
        policy_id: currentQuestion.evidence_policy_id,
      })
      setEvidenceChecks({})
      setHasEvidence(true)
      return
    }
    await submitAnswer({ q_id: currentQuestion.q_id, a_id: opt.a_id, score: opt.base_score })
  }

  const handleMultiSelectConfirm = async () => {
    if (!currentQuestion) return
    const currentSelection = responses[currentQuestion.q_id]
    if (!Array.isArray(currentSelection) || currentSelection.length === 0) return

    const score = calculateMultiSelectScore(currentQuestion, currentSelection)

    // For backend, send as comma-separated string
    const a_id = currentSelection.join(',')

    await submitAnswer({ q_id: currentQuestion.q_id, a_id, score })
  }

  const handleEvidenceSubmit = async () => {
    if (!pendingEvidence) return
    const policy = EVIDENCE_POLICIES[pendingEvidence.policy_id]
    const required = policy?.required || []
    const missingRequired = required.filter((key) => !evidenceChecks[key])
    setEvidenceMissingRequired(missingRequired)
    if (hasEvidence && missingRequired.length) {
      showToast('Complete required evidence checks before continuing.', 'warning')
      return
    }
    const evidencePayload = {
      policy_id: pendingEvidence.policy_id,
      has_evidence: hasEvidence,
      checks: evidenceChecks,
    }
    await submitAnswer({
      q_id: pendingEvidence.q_id,
      a_id: pendingEvidence.a_id,
      score: pendingEvidence.score,
      evidence: evidencePayload,
    })
    setPendingEvidence(null)
    setEvidenceMissingRequired([])
  }

  useEffect(() => {
    if (!pendingEvidence) return
    const policy = EVIDENCE_POLICIES[pendingEvidence.policy_id]
    const required = policy?.required || []
    const missingRequired = required.filter((key) => !evidenceChecks[key])
    setEvidenceMissingRequired(hasEvidence ? missingRequired : [])
  }, [pendingEvidence, evidenceChecks, hasEvidence])

  const handleDefer = async () => {
    if (!currentQuestion) return
    const existing = responses[currentQuestion.q_id]

    // Handle multi-select: convert array to comma-separated string
    let safeAnswer: string
    if (Array.isArray(existing)) {
      safeAnswer = existing.join(',')
    } else {
      safeAnswer = existing || currentQuestion.options?.[0]?.a_id
    }

    if (!safeAnswer) return

    // For multi-select, calculate score based on selection count
    let score: number
    if (isMultiSelectQuestion(currentQuestion) && Array.isArray(existing)) {
      score = calculateMultiSelectScore(currentQuestion, existing)
    } else {
      score = getScoreForAnswer(currentQuestion.q_id, safeAnswer)
    }

    await submitAnswer({
      q_id: currentQuestion.q_id,
      a_id: safeAnswer,
      score,
      is_deferred: true,
    })
  }

  const handleToggleReview = async (qId: string) => {
    const response = responses[qId]
    if (!response) return

    // Handle multi-select: convert array to comma-separated string
    const aId = Array.isArray(response) ? response.join(',') : response

    // Find the question to check if it's multi-select
    const q = questions.find((item) => item.q_id === qId)
    let score: number
    if (q && isMultiSelectQuestion(q) && Array.isArray(response)) {
      score = calculateMultiSelectScore(q, response)
    } else {
      score = getScoreForAnswer(qId, aId)
    }

    const isFlagged = flaggedIds.has(qId)
    await submitAnswer({
      q_id: qId,
      a_id: aId,
      score,
      is_flagged: !isFlagged,
    })
  }

  // Render helper to wrap content with PageHeader and Nav
  const renderLayout = (content: React.ReactNode) => (
    <section className="af-page">
      <PageHeader
        title="Question Flow"
        subtitle={`Assessment ID: ${assessmentId || 'Not set'}`}
      />
      <div style={{ marginBottom: '20px' }}>
        <AssessmentNav assessmentId={assessmentId} />
      </div>
      {content}
    </section>
  )

  if (!assessmentId) {
    return (
      <div className="af-card">
        <h2>Assessment Required</h2>
        <p>Create an assessment before entering the flow.</p>
        <button className="af-btn primary" onClick={() => navigate('/assessment')}>
          Back to Assessment Hub
        </button>
      </div>
    )
  }

  if (status) {
    return renderLayout(<div className="af-card">{status}</div>)
  }

  if (requiresIntake) {
    return renderLayout(
      <div className="af-card">
        <h2>Intake Required</h2>
        <p>Complete intake before the assessment flow unlocks.</p>
        <button className="af-btn primary" onClick={() => navigate('/assessment/intake')}>
          Start Intake
        </button>
      </div>
    )
  }

  if (!currentQuestion) {
    return renderLayout(<div className="af-card">No questions available.</div>)
  }

  const policy = pendingEvidence ? EVIDENCE_POLICIES[pendingEvidence.policy_id] : null

  const currentLabel = `${currentIndex + 1} / ${reachable.length || 0}`

  return renderLayout(
    <>
      <div className={`af-layout ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <aside className={`af-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <div className="af-sidebar-header">
            <div className="af-sidebar-title">Progress</div>
            <button className="af-collapse" onClick={() => setSidebarCollapsed((prev) => !prev)} title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
              {sidebarCollapsed ? '→' : '←'}
            </button>
          </div>

          {!sidebarCollapsed && (
            <div className="af-progress-summary">
              <div className="af-progress-stats">
                <div className="af-stat">
                  <span className="af-stat-value">{reachable.filter(id => responses[id] && !deferredIds.has(id)).length}</span>
                  <span className="af-stat-label">Answered</span>
                </div>
                <div className="af-stat">
                  <span className="af-stat-value">{reachable.filter(id => deferredIds.has(id)).length}</span>
                  <span className="af-stat-label">Deferred</span>
                </div>
                <div className="af-stat">
                  <span className="af-stat-value">{reachable.filter(id => flaggedIds.has(id)).length}</span>
                  <span className="af-stat-label">Flagged</span>
                </div>
              </div>
              <div className="af-progress-bar">
                <div
                  className="af-progress-fill"
                  style={{ width: `${reachable.length ? (reachable.filter(id => responses[id] && !deferredIds.has(id)).length / reachable.length * 100).toFixed(0) : 0}%` }}
                />
              </div>
              <div className="af-progress-text">
                {reachable.length ? ((reachable.filter(id => responses[id] && !deferredIds.has(id)).length / reachable.length) * 100).toFixed(0) : 0}% Complete
              </div>
            </div>
          )}

          {sidebar.length === 0 && <div className="af-empty">Sidebar unavailable.</div>}

          {!sidebarCollapsed && deferredIds.size > 0 && (
            <div className="af-quick-access">
              <div className="af-quick-title">Quick Access</div>
              <button
                className="af-quick-button deferred"
                onClick={() => {
                  const firstDeferred = reachable.find(id => deferredIds.has(id))
                  if (firstDeferred) {
                    setCurrentIndex(reachable.indexOf(firstDeferred))
                  }
                }}
              >
                <span>⚠</span>
                <span>Jump to Deferred ({deferredIds.size})</span>
              </button>
              {flaggedIds.size > 0 && (
                <button
                  className="af-quick-button flagged"
                  onClick={() => {
                    const firstFlagged = reachable.find(id => flaggedIds.has(id))
                    if (firstFlagged) {
                      setCurrentIndex(reachable.indexOf(firstFlagged))
                    }
                  }}
                >
                  <span>★</span>
                  <span>Jump to Flagged ({flaggedIds.size})</span>
                </button>
              )}
            </div>
          )}

          {[...new Set(sidebar.map((item) => item.domain))].map((domain) => {
            const items = sidebar.filter((item) => item.domain === domain && item.status !== 'hidden')
            if (items.length === 0) return null

            const domainAnswered = items.filter(item => responses[item.q_id] && !deferredIds.has(item.q_id)).length
            const domainTotal = items.length
            const domainPercent = domainTotal > 0 ? ((domainAnswered / domainTotal) * 100).toFixed(0) : 0
            const expanded = expandedDomain === domain

            return (
              <div key={domain} className="af-domain">
                <button className={`af-domain-header ${expanded ? 'active' : ''}`} onClick={() => setExpandedDomain(expanded ? null : domain)}>
                  <span className="af-domain-name">
                    <span>{domain}</span>
                    {!sidebarCollapsed && <span className="af-domain-count">({domainAnswered}/{domainTotal})</span>}
                  </span>
                  <span>{expanded ? '▾' : '▸'}</span>
                </button>
                {expanded && (
                  <div className="af-domain-list">
                    {items.map((item) => {
                      const isActive = item.q_id === currentQuestion.q_id
                      const isDone = responses[item.q_id] && !deferredIds.has(item.q_id)
                      const isDeferred = deferredIds.has(item.q_id)
                      const isFlagged = flaggedIds.has(item.q_id)
                      const isOverride = isOverrideQuestion(item.q_id)
                      const disabled = item.status === 'locked'
                      return (
                        <div key={item.q_id} className={`af-domain-item ${isActive ? 'active' : ''} ${disabled ? 'locked' : ''} ${isDone ? 'done' : ''} ${isDeferred ? 'deferred' : ''}`}>
                          <button
                            className="af-domain-link"
                            disabled={disabled}
                            onClick={() => setCurrentIndex(Math.max(0, reachable.indexOf(item.q_id)))}
                            title={disabled ? 'Locked - answer previous questions first' : item.title}
                          >
                            <span className="af-dot">{isDone ? '✓' : isDeferred ? '⚠' : '•'}</span>
                            <span className="af-question-title">{item.title}</span>
                          </button>
                          {isOverride && !sidebarCollapsed && <span className="af-override">override</span>}
                          {isDone && !sidebarCollapsed && (
                            <button
                              className={`af-flag ${isFlagged ? 'active' : ''}`}
                              onClick={() => handleToggleReview(item.q_id)}
                              title={isFlagged ? 'Remove flag' : 'Flag for review'}
                            >
                              {isFlagged ? '★' : '☆'}
                            </button>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </aside>

        <div className="af-question">
          <div className="af-meta">
            <span className="af-domain-label">{currentQuestion.domain}</span>
            <span className="af-id">
              {currentQuestion.q_id}
              {isOverrideQuestion(currentQuestion.q_id) ? ' · override' : ''}
            </span>
          </div>
          <label className="af-auto">
            <input
              type="checkbox"
              checked={autoAdvance}
              onChange={(event) => setAutoAdvance(event.target.checked)}
            />
            Auto-advance after answer
          </label>
          <div className="af-progress">{currentLabel}</div>
          <h2>{currentQuestion.question_text}</h2>
          {currentQuestion.guidance ? <div className="af-guidance">{currentQuestion.guidance}</div> : null}

          {isMultiSelectQuestion(currentQuestion) && (
            <div className="af-multiselect-note">
              Select all that apply (multiple selections allowed)
            </div>
          )}

          <div className="af-options">
            {isMultiSelectQuestion(currentQuestion) ? (
              // Multi-select: render checkboxes
              currentQuestion.options.map((opt) => {
                const currentSelection = responses[currentQuestion.q_id]
                const selectedIds = Array.isArray(currentSelection) ? currentSelection : []
                const isSelected = selectedIds.includes(opt.a_id)

                return (
                  <label
                    key={opt.a_id}
                    className={`af-option af-checkbox-option ${isSelected ? 'selected' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleAnswer(opt)}
                    />
                    <span>{opt.answer_text}</span>
                  </label>
                )
              })
            ) : (
              // Single-select: render buttons
              currentQuestion.options.map((opt) => (
                <button
                  key={opt.a_id}
                  className={`af-option ${responses[currentQuestion.q_id] === opt.a_id ? 'selected' : ''}`}
                  onClick={() => handleAnswer(opt)}
                >
                  {opt.answer_text}
                </button>
              ))
            )}
          </div>

          {isMultiSelectQuestion(currentQuestion) && (
            <div className="af-multiselect-actions">
              <button
                className="af-btn primary"
                onClick={handleMultiSelectConfirm}
                disabled={
                  !responses[currentQuestion.q_id] ||
                  (Array.isArray(responses[currentQuestion.q_id]) &&
                    (responses[currentQuestion.q_id] as string[]).length === 0)
                }
              >
                Confirm Selection
              </button>
            </div>
          )}

          {pendingEvidence && (
            <div className="af-evidence">
              <div className="af-evidence-title">Evidence Attestation</div>
              <div className="af-evidence-sub">{policy?.label || pendingEvidence.policy_id}</div>
              {policy?.description ? <div className="af-evidence-desc">{policy.description}</div> : null}
              <label className="af-toggle">
                <span>Do you have evidence?</span>
                <select value={hasEvidence ? 'yes' : 'no'} onChange={(event) => setHasEvidence(event.target.value === 'yes')}>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </label>
              {hasEvidence && (
                <div className="af-checks">
                  {(policy?.checks || DEFAULT_EVIDENCE_CHECKS).map((check) => (
                    <label key={check.id} className="af-check">
                      <input
                        type="checkbox"
                        checked={!!evidenceChecks[check.id]}
                        onChange={(event) =>
                          setEvidenceChecks((prev) => ({ ...prev, [check.id]: event.target.checked }))
                        }
                      />
                      <span>
                        {check.label}
                        {policy?.required?.includes(check.id) ? <strong className="af-required">Required</strong> : null}
                      </span>
                    </label>
                  ))}
                  {hasEvidence && evidenceMissingRequired.length ? (
                    <div className="af-required-note">
                      Required checks missing: {evidenceMissingRequired.join(', ')}.
                    </div>
                  ) : null}
                </div>
              )}
              <div className="af-evidence-actions">
                <button className="af-btn secondary" onClick={() => setPendingEvidence(null)}>
                  Cancel
                </button>
                <button className="af-btn primary" onClick={handleEvidenceSubmit}>
                  Confirm & Continue
                </button>
              </div>
            </div>
          )}

          <div className="af-actions">
            <button className="af-btn secondary" onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}>
              Previous
            </button>
            <button className="af-btn secondary" onClick={handleDefer}>
              Defer / Skip
            </button>
            <button className="af-btn secondary" onClick={() => setCurrentIndex(Math.min(reachable.length - 1, currentIndex + 1))}>
              Next
            </button>
            <button className="af-btn secondary" onClick={() => navigate('/assessment/results')}>
              View Results
            </button>
          </div>
        </div>
      </div>
    </>
  )
}

export default AssessmentFlow
