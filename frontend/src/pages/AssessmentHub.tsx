import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './AssessmentHub.css'
import { getStoredAssessmentId, storeAssessmentId } from '../utils/assessment'

type ResumptionState = {
  completion_pct?: number
  reachable_path?: string[]
  responses?: Record<string, string>
  deferred_ids?: string[]
  flagged_ids?: string[]
}

type RiskEntry = {
  scenario?: string
  name?: string
  likelihood?: number
  impact?: number
}

const API_BASE = 'http://127.0.0.1:8000/api/v1'

const AssessmentHub = () => {
  const [assessmentId, setAssessmentId] = useState<string>('')
  const [completionPct, setCompletionPct] = useState<number | null>(null)
  const [intakeAnswered, setIntakeAnswered] = useState<number | null>(null)
  const [intakeTotal, setIntakeTotal] = useState<number | null>(null)
  const [topRisk, setTopRisk] = useState<string>('—')
  const [heatmapCount, setHeatmapCount] = useState<number | null>(null)
  const [statusNote, setStatusNote] = useState<string>('')
  const [domains, setDomains] = useState<string[]>([])
  const [allQuestions, setAllQuestions] = useState<Array<{ q_id: string; domain: string }>>([])
  const [resumeState, setResumeState] = useState<ResumptionState | null>(null)
  const [roleLens, setRoleLens] = useState<string>('overall')
  const [overrideDomains, setOverrideDomains] = useState<Set<string>>(new Set())

  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const navigate = useNavigate()

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    if (!currentUser || assessmentId) return
    const controller = new AbortController()
    const resolveAssessment = async () => {
      try {
        const latestResp = await fetch(`${API_BASE}/assessment/user/${currentUser}/latest`, {
          signal: controller.signal,
        })
        if (latestResp.ok) {
          const latest = (await latestResp.json()) as { assessment_id?: string }
          if (latest.assessment_id) {
            setAssessmentId(latest.assessment_id)
            storeAssessmentId(latest.assessment_id, currentUser)
            return
          }
        }
        if (latestResp.status !== 404) return
        const createResp = await fetch(`${API_BASE}/assessment/new`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: currentUser || null }),
          signal: controller.signal,
        })
        if (!createResp.ok) throw new Error('Create failed')
        const created = (await createResp.json()) as { assessment_id?: string }
        const id = created.assessment_id || ''
        if (id) {
          setAssessmentId(id)
          storeAssessmentId(id, currentUser)
        }
      } catch {
        if (!controller.signal.aborted) {
          setStatusNote('Unable to resolve assessment ID. Check API status.')
        }
      }
    }
    resolveAssessment()
    return () => controller.abort()
  }, [currentUser, assessmentId])

  useEffect(() => {
    if (!assessmentId) return
    fetch(`${API_BASE}/questions/all?assessment_id=${assessmentId}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        const questions = (data || []) as Array<{ q_id: string; domain?: string }>
        setAllQuestions(questions.filter((q) => q.q_id && q.domain) as Array<{ q_id: string; domain: string }>)
        const unique = Array.from(new Set(questions.map((q) => q.domain).filter(Boolean))) as string[]
        setDomains(unique.sort())
      })
      .catch(() => setDomains([]))
  }, [assessmentId])

  useEffect(() => {
    if (!assessmentId) return
    const storedRole = localStorage.getItem(`role_lens_${assessmentId}`) || 'overall'
    setRoleLens(storedRole)
    const raw = localStorage.getItem(`override_domains_${assessmentId}`)
    if (raw) {
      try {
        const list = JSON.parse(raw)
        if (Array.isArray(list)) {
          setOverrideDomains(new Set(list))
        }
      } catch {
        setOverrideDomains(new Set())
      }
    } else {
      setOverrideDomains(new Set())
    }
  }, [assessmentId])

  useEffect(() => {
    if (!assessmentId) return
    const controller = new AbortController()
    setStatusNote('')

    Promise.allSettled([
      fetch(`${API_BASE}/assessment/${assessmentId}/resume`, { signal: controller.signal }),
      fetch(`${API_BASE}/intake/${assessmentId}`, { signal: controller.signal }),
      fetch(`${API_BASE}/intake/start`, { signal: controller.signal }),
      fetch(`${API_BASE.replace('/api/v1', '')}/responses/analysis/${assessmentId}`, {
        signal: controller.signal,
      }),
    ])
      .then(async ([resumeResp, intakeResp, intakeStartResp, riskResp]) => {
        let anyOk = false

        if (resumeResp.status === 'fulfilled' && resumeResp.value.ok) {
          const state = (await resumeResp.value.json()) as ResumptionState
          setCompletionPct(state.completion_pct ?? null)
          setResumeState(state)
          anyOk = true
        }

        if (intakeResp.status === 'fulfilled' && intakeResp.value.ok) {
          const intakeRows = (await intakeResp.value.json()) as Array<{ value?: string | null }>
          setIntakeAnswered(intakeRows.filter((row) => row.value != null && row.value !== '').length)
          anyOk = true
        } else {
          const storedAnswered = localStorage.getItem(`intake_answered_${assessmentId}`)
          setIntakeAnswered(storedAnswered ? Number(storedAnswered) : null)
        }

        if (intakeStartResp.status === 'fulfilled' && intakeStartResp.value.ok) {
          const intakeQs = (await intakeStartResp.value.json()) as unknown[]
          setIntakeTotal(Array.isArray(intakeQs) ? intakeQs.length : null)
          anyOk = true
        } else {
          const storedTotal = localStorage.getItem(`intake_total_${assessmentId}`)
          setIntakeTotal(storedTotal ? Number(storedTotal) : null)
        }

        if (riskResp.status === 'fulfilled' && riskResp.value.ok) {
          const data = await riskResp.value.json()
          const heatmap = Array.isArray(data.risk_heatmap) ? data.risk_heatmap : []
          setHeatmapCount(heatmap.length)
          const top = (Array.isArray(data.top_risks) ? data.top_risks : []) as RiskEntry[]
          const label = top[0]?.scenario || top[0]?.name || '—'
          setTopRisk(label)
          anyOk = true
        }

        if (!anyOk) {
          setStatusNote('API offline. Start the backend to load assessment data.')
        }
      })
      .catch(() => {
        setStatusNote('API offline. Start the backend to load assessment data.')
        const storedAnswered = localStorage.getItem(`intake_answered_${assessmentId}`)
        const storedTotal = localStorage.getItem(`intake_total_${assessmentId}`)
        setIntakeAnswered(storedAnswered ? Number(storedAnswered) : null)
        setIntakeTotal(storedTotal ? Number(storedTotal) : null)
      })

    return () => controller.abort()
  }, [assessmentId])

  const domainCards = (() => {
    if (!allQuestions.length || !resumeState?.reachable_path) return []
    const responses = resumeState.responses || {}
    const deferred = new Set(resumeState.deferred_ids || [])
    const reachable = resumeState.reachable_path || []
    return domains.map((domain) => {
      const domainQs = allQuestions.filter((q) => q.domain === domain)
      const answeredCount = domainQs.filter((q) => responses[q.q_id] && !deferred.has(q.q_id)).length
      const reachableInDomain = reachable.filter((qid) => domainQs.find((dq) => dq.q_id === qid))
      const remaining = Math.max(domainQs.length - answeredCount, 0)
      let status = 'not_started'
      if (answeredCount > 0 && answeredCount < domainQs.length) status = 'ongoing'
      if (answeredCount >= domainQs.length && domainQs.length > 0) status = 'completed'
      return {
        domain,
        status,
        remaining,
        reachable: reachableInDomain,
      }
    })
  })()

  const handleStartDomain = (domain: string, reachable: string[]) => {
    if (!assessmentId) return
    if (reachable.length === 0) return
    localStorage.setItem('flow_start_domain', domain)
    navigate('/assessment/flow')
  }

  const persistOverrideDomains = (next: Set<string>) => {
    if (!assessmentId) return
    localStorage.setItem(`override_domains_${assessmentId}`, JSON.stringify([...next]))
  }

  const syncOverrideDepth = async (enabled: boolean) => {
    if (!assessmentId) return
    try {
      await fetch(`${API_BASE}/assessment/${assessmentId}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ override_depth: enabled }),
      })
    } catch {
      setStatusNote('Unable to update override depth. Check API status.')
    }
  }

  const toggleDomainOverride = (domain: string, enabled: boolean) => {
    const next = new Set(overrideDomains)
    if (enabled) next.add(domain)
    else next.delete(domain)
    setOverrideDomains(next)
    persistOverrideDomains(next)
    syncOverrideDepth(next.size > 0)
  }

  const handleRoleLensChange = (value: string) => {
    setRoleLens(value)
    if (assessmentId) {
      localStorage.setItem(`role_lens_${assessmentId}`, value)
    }
  }

  const intakeStatus =
    intakeAnswered != null && intakeTotal != null
      ? `${intakeAnswered} / ${intakeTotal}`
      : '-- / --'

  return (
    <section className="ah-page">
      <div className="ah-header">
        <div>
          <h1>Assessment Hub</h1>
          <p className="ah-subtitle">Assessment status, intake flow, and risk insights.</p>
          {statusNote ? <div className="ah-status-note">{statusNote}</div> : null}
        </div>
        <div className="ah-actions">
          <button className="ah-btn secondary" onClick={() => navigate('/assessment/intake')} disabled={!assessmentId}>
            Start Intake
          </button>
          <button className="ah-btn secondary" onClick={() => navigate('/assessment/results')} disabled={!assessmentId}>
            View Results
          </button>
          <button className="ah-btn secondary" onClick={() => navigate('/assessment/flow')} disabled={!assessmentId}>
            Assessment Flow
          </button>
          <button className="ah-btn secondary" onClick={() => navigate('/assessment/risks')} disabled={!assessmentId}>
            Risks
          </button>
        </div>
      </div>

      <section className="ah-grid">
        <div className="ah-card">
          <div className="ah-card-title">Assessment Status</div>
          <p>Resume where you left off or create a new assessment.</p>
          <div className="ah-status-row">
            <span>Current assessment</span>
            <strong>{assessmentId ? assessmentId : 'Not set'}</strong>
          </div>
          <div className="ah-status-row">
            <span>Progress</span>
            <strong>{completionPct != null ? `${completionPct}%` : '--%'}</strong>
          </div>
        </div>

        <div className="ah-card">
          <div className="ah-card-title">Intake Progress</div>
          <p>Complete intake to unlock kick-start and routing.</p>
          <div className="ah-status-row">
            <span>Answered</span>
            <strong>{intakeStatus}</strong>
          </div>
          <div className="ah-status-row">
            <span>Status</span>
            <strong>{intakeAnswered && intakeAnswered > 0 ? 'In progress' : 'Pending'}</strong>
          </div>
        </div>

        <div className="ah-card">
          <div className="ah-card-title">Risk Snapshot</div>
          <p>Top risks and heatmap from the latest analysis run.</p>
          <div className="ah-status-row">
            <span>Top risk</span>
            <strong>{topRisk}</strong>
          </div>
          <div className="ah-status-row">
            <span>Heatmap coverage</span>
            <strong>{heatmapCount != null ? heatmapCount : '--'}</strong>
          </div>
        </div>
      </section>

      <section className="ah-section">
        <div className="ah-section-title">Risk Heatmap</div>
        <div className="ah-heatmap">
          <div className="ah-axis-labels">
            <span>7</span>
            <span>6</span>
            <span>5</span>
            <span>4</span>
            <span>3</span>
            <span>2</span>
            <span>1</span>
          </div>
          <div className="ah-heatmap-grid" />
          <div className="ah-axis-spacer" />
          <div className="ah-axis-bottom">
            <span>1</span>
            <span>2</span>
            <span>3</span>
            <span>4</span>
            <span>5</span>
            <span>6</span>
            <span>7</span>
          </div>
        </div>
      </section>

      <section className="ah-section">
        <div className="ah-section-title">Results & Review</div>
        <div className="ah-review-grid">
          <div className="ah-card">
            <div className="ah-card-title">Results Dashboard</div>
            <p>Archetype, axis scores, and benchmarking will render here.</p>
            <button className="ah-btn secondary" onClick={() => navigate('/assessment/results')} disabled={!assessmentId}>
              Open Results
            </button>
          </div>
          <div className="ah-card">
            <div className="ah-card-title">Review Queue</div>
            <p>Flagged and deferred questions will be listed in this panel.</p>
            <button className="ah-btn secondary" onClick={() => navigate('/assessment/review')} disabled={!assessmentId}>
              Open Review
            </button>
          </div>
        </div>
      </section>

      {assessmentId && domainCards.length > 0 ? (
        <section className="ah-section">
          <div className="ah-section-title">Domain Progress</div>
          <div className="ah-domain-grid">
            {domainCards.map((card) => (
              <div key={card.domain} className={`ah-domain-card ${card.status}`}>
                <div className="ah-domain-title">{card.domain}</div>
                <div className="ah-domain-meta">
                  {card.status === 'completed' ? 'Path complete' : `~${card.remaining} potential remaining`}
                </div>
                <button
                  className="ah-btn secondary"
                  onClick={() => handleStartDomain(card.domain, card.reachable)}
                  disabled={card.reachable.length === 0}
                >
                  Open Domain
                </button>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {assessmentId ? (
        <section className="ah-controls ah-controls-bottom">
          <div className="ah-card">
            <div className="ah-card-title">Role Lens (view-only)</div>
            <p>Filters will map to role tags once metadata is available.</p>
            <select
              className="ah-select"
              value={roleLens}
              onChange={(event) => handleRoleLensChange(event.target.value)}
            >
              <option value="overall">Overall</option>
              <option value="ciso">CISO</option>
              <option value="ia">Internal Audit</option>
              <option value="hr">HR</option>
            </select>
          </div>
          <div className="ah-card">
            <div className="ah-card-title">Explore Deeper Questions</div>
            <p>Select domains to include deeper items. Overrides are excluded from benchmarks.</p>
            <label className="ah-toggle">
              <input
                type="checkbox"
                checked={overrideDomains.size > 0}
                onChange={(event) => {
                  if (!event.target.checked) {
                    const cleared = new Set<string>()
                    setOverrideDomains(cleared)
                    persistOverrideDomains(cleared)
                    syncOverrideDepth(false)
                  }
                }}
              />
              Enable
            </label>
            <details className="ah-domain-picker">
              <summary>Domains</summary>
              <div className="ah-domain-list">
                {domains.map((domain) => (
                  <label key={domain}>
                    <input
                      type="checkbox"
                      checked={overrideDomains.has(domain)}
                      onChange={(event) => toggleDomainOverride(domain, event.target.checked)}
                    />
                    {domain}
                  </label>
                ))}
              </div>
            </details>
          </div>
        </section>
      ) : null}
    </section>
  )
}

export default AssessmentHub
