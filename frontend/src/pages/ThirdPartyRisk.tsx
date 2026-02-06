import { useEffect, useMemo, useState } from 'react'
import './ThirdPartyRisk.css'
import { apiJson } from '../lib/api'
import { getStoredAssessmentId, storeAssessmentId } from '../utils/assessment'


type ThirdPartyAssessment = {
  id: string
  tenant_key: string
  assessment_id: string
  partner_name: string
  partner_type: string
  risk_tier: string
  status: string
  summary?: string | null
  responses?: Record<string, unknown> | null
  score?: number | null
  created_at: string
  updated_at: string
}

type ThirdPartyQuestionOption = {
  a_id: string
  label: string
  score: number
}

type ThirdPartyQuestion = {
  q_id: string
  category?: string | null
  question_text: string
  weight?: number | null
  options: ThirdPartyQuestionOption[]
}

type ThirdPartyComputed = {
  score?: number | null
  risk_band?: string | null
  answered?: number | null
  total?: number | null
  coverage?: number | null
}

type ThirdPartyResponseRow = {
  q_id: string
  category?: string | null
  question_text?: string | null
  answer_text?: string | null
  score?: number | null
}

type ThirdPartyForm = {
  partner_name: string
  partner_type: string
  risk_tier: string
  status: string
  summary: string
  score: string
}

const defaultForm: ThirdPartyForm = {
  partner_name: '',
  partner_type: 'Supplier',
  risk_tier: 'Tier-2',
  status: 'draft',
  summary: '',
  score: '',
}

const ThirdPartyRisk = () => {
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [assessmentId, setAssessmentId] = useState('')
  const [assessments, setAssessments] = useState<ThirdPartyAssessment[]>([])
  const [questions, setQuestions] = useState<ThirdPartyQuestion[]>([])
  const [selectedPartnerId, setSelectedPartnerId] = useState('')
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [detailOpen, setDetailOpen] = useState(false)
  const [detailId, setDetailId] = useState('')
  const [detailForm, setDetailForm] = useState<ThirdPartyForm>(defaultForm)
  const [form, setForm] = useState<ThirdPartyForm>(defaultForm)
  const [status, setStatus] = useState('Loading third-party assessments...')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isScoring, setIsScoring] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    loadAssessments()
    loadQuestions()
  }, [])

  useEffect(() => {
    if (!selectedPartnerId && assessments.length) {
      setSelectedPartnerId(assessments[0].id)
    }
  }, [assessments, selectedPartnerId])

  useEffect(() => {
    const selected = assessments.find((item) => item.id === selectedPartnerId)
    if (!selected) {
      setAnswers({})
      return
    }
    setAnswers(extractAnswers(selected))
  }, [assessments, selectedPartnerId])

  useEffect(() => {
    document.body.classList.toggle('modal-open', detailOpen)
    return () => {
      document.body.classList.remove('modal-open')
    }
  }, [detailOpen])

  const loadAssessments = () => {
    setIsLoading(true)
    apiJson<ThirdPartyAssessment[]>('/third-party/assessments')
      .then((data) => {
        const list = data || []
        setAssessments(list)
        setStatus(list.length ? `Loaded ${list.length} partner assessments.` : 'No third-party assessments yet.')
      })
      .catch((err) => {
        setAssessments([])
        setStatus(err instanceof Error ? err.message : 'Unable to load third-party assessments.')
      })
      .finally(() => {
        setIsLoading(false)
      })
  }

  const loadQuestions = () => {
    apiJson<ThirdPartyQuestion[]>('/third-party/questions/all')
      .then((data) => {
        setQuestions(data || [])
      })
      .catch(() => {
        setQuestions([])
      })
  }

  const extractAnswers = (assessment: ThirdPartyAssessment) => {
    const payload = assessment.responses
    if (!payload || typeof payload !== 'object') return {}
    const raw = (payload as { responses?: Array<Record<string, unknown>> }).responses
    if (!Array.isArray(raw)) return {}
    return raw.reduce<Record<string, string>>((acc, item) => {
      const qId = typeof item.q_id === 'string' ? item.q_id : ''
      const aId = typeof item.a_id === 'string' ? item.a_id : ''
      if (qId && aId) acc[qId] = aId
      return acc
    }, {})
  }

  const extractComputed = (assessment?: ThirdPartyAssessment | null): ThirdPartyComputed | null => {
    if (!assessment || !assessment.responses || typeof assessment.responses !== 'object') return null
    const computed = (assessment.responses as { computed?: ThirdPartyComputed }).computed
    if (!computed || typeof computed !== 'object') return null
    return computed
  }

  const extractResponseRows = (assessment?: ThirdPartyAssessment | null): ThirdPartyResponseRow[] => {
    if (!assessment || !assessment.responses || typeof assessment.responses !== 'object') return []
    const raw = (assessment.responses as { responses?: ThirdPartyResponseRow[] }).responses
    if (!Array.isArray(raw)) return []
    return raw.map((item) => ({
      q_id: item.q_id,
      category: item.category,
      question_text: item.question_text,
      answer_text: item.answer_text,
      score: typeof item.score === 'number' ? item.score : null,
    }))
  }

  const handleSaveContext = () => {
    if (!assessmentId.trim()) {
      setStatus('Enter an assessment ID before saving context.')
      return
    }
    storeAssessmentId(assessmentId.trim(), currentUser)
    setStatus(`Assessment context saved: ${assessmentId.trim()}`)
  }

  const handleCreate = () => {
    const trimmedAssessment = assessmentId.trim()
    const trimmedName = form.partner_name.trim()

    if (!trimmedAssessment) {
      setStatus('Set an assessment ID before creating a third-party assessment.')
      return
    }

    if (!trimmedName) {
      setStatus('Partner name is required.')
      return
    }

    const scoreValue = form.score.trim() ? Number(form.score) : undefined
    const payload = {
      partner_name: trimmedName,
      partner_type: form.partner_type || 'Supplier',
      risk_tier: form.risk_tier || 'Tier-2',
      status: form.status || 'draft',
      summary: form.summary.trim() || undefined,
      score: Number.isNaN(scoreValue) ? undefined : scoreValue,
    }

    setIsSubmitting(true)
    apiJson<ThirdPartyAssessment>(`/third-party/assessments?assessment_id=${encodeURIComponent(trimmedAssessment)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((created) => {
        setAssessments((prev) => [created, ...prev])
        setSelectedPartnerId(created.id)
        setForm(defaultForm)
        storeAssessmentId(trimmedAssessment, currentUser)
        setStatus(`Created assessment for ${created.partner_name}.`)
      })
      .catch((err) => {
        setStatus(err instanceof Error ? err.message : 'Unable to create assessment.')
      })
      .finally(() => {
        setIsSubmitting(false)
      })
  }

  const openDetail = (assessment: ThirdPartyAssessment) => {
    setDetailId(assessment.id)
    setDetailForm({
      partner_name: assessment.partner_name,
      partner_type: assessment.partner_type,
      risk_tier: assessment.risk_tier,
      status: assessment.status,
      summary: assessment.summary || '',
      score: typeof assessment.score === 'number' ? `${assessment.score}` : '',
    })
    setDetailOpen(true)
  }

  const handleDetailUpdate = () => {
    if (!detailId) return
    const name = detailForm.partner_name.trim()
    if (!name) {
      setStatus('Partner name is required.')
      return
    }
    const scoreValue = detailForm.score.trim() ? Number(detailForm.score) : null
    const payload = {
      partner_name: name,
      partner_type: detailForm.partner_type || 'Supplier',
      risk_tier: detailForm.risk_tier || 'Tier-2',
      status: detailForm.status || 'draft',
      summary: detailForm.summary.trim() ? detailForm.summary.trim() : null,
      score: Number.isNaN(scoreValue as number) ? null : scoreValue,
    }
    setIsUpdating(true)
    apiJson<ThirdPartyAssessment>(`/third-party/assessments/${detailId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((updated) => {
        setAssessments((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
        setStatus(`Updated ${updated.partner_name}.`)
        setDetailOpen(false)
      })
      .catch((err) => {
        setStatus(err instanceof Error ? err.message : 'Unable to update assessment.')
      })
      .finally(() => {
        setIsUpdating(false)
      })
  }

  const handleScore = () => {
    if (!selectedPartnerId) {
      setStatus('Select a partner assessment to score.')
      return
    }
    const responses = Object.entries(answers)
      .filter(([, aId]) => Boolean(aId))
      .map(([qId, aId]) => ({ q_id: qId, a_id: aId }))
    if (responses.length === 0) {
      setStatus('Answer at least one question before scoring.')
      return
    }
    setIsScoring(true)
    apiJson<ThirdPartyAssessment>(`/third-party/assessments/${selectedPartnerId}/responses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ responses }),
    })
      .then((updated) => {
        setAssessments((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
        setStatus(`Updated score for ${updated.partner_name}.`)
      })
      .catch((err) => {
        setStatus(err instanceof Error ? err.message : 'Unable to score assessment.')
      })
      .finally(() => {
        setIsScoring(false)
      })
  }

  const scored = assessments.filter((item) => typeof item.score === 'number')
  const avgScore = scored.length
    ? (scored.reduce((sum, item) => sum + (item.score || 0), 0) / scored.length).toFixed(2)
    : '--'
  const highRisk = assessments.filter((item) => (item.risk_tier || '').toLowerCase().includes('tier-1')).length
  const activeCount = assessments.filter((item) => !['closed', 'archived'].includes(item.status.toLowerCase())).length

  const formatDate = (value?: string) => {
    if (!value) return '--'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return '--'
    return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
  }

  const formatScore = (value?: number | null) => {
    if (typeof value !== 'number') return '--'
    return Math.round(value * 100) / 100
  }

  const selectedAssessment = assessments.find((item) => item.id === selectedPartnerId)
  const computed = extractComputed(selectedAssessment)
  const coveragePercent =
    typeof computed?.coverage === 'number' ? `${Math.round(computed.coverage * 100)}%` : '--'
  const detailAssessment = assessments.find((item) => item.id === detailId)
  const detailComputed = extractComputed(detailAssessment)
  const detailCoverage =
    typeof detailComputed?.coverage === 'number' ? `${Math.round(detailComputed.coverage * 100)}%` : '--'
  const detailResponses = extractResponseRows(detailAssessment)

  return (
    <section className="tpr-page">
      <div className="tpr-header">
        <div>
          <h1>Third-Party Risk</h1>
          <p className="tpr-subtitle">
            Track supplier exposure, partner readiness, and external dependencies across your assessment footprint.
          </p>
        </div>
        <div className="tpr-header-actions">
          <button className="tpr-btn secondary" onClick={loadAssessments} disabled={isLoading}>
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="tpr-grid">
        <div className="tpr-card">
          <div className="tpr-title">Portfolio Snapshot</div>
          <div className="tpr-metrics">
            <div className="tpr-metric">
              <span>Total partners</span>
              <strong>{assessments.length}</strong>
            </div>
            <div className="tpr-metric">
              <span>Active items</span>
              <strong>{activeCount}</strong>
            </div>
            <div className="tpr-metric">
              <span>Tier-1 partners</span>
              <strong>{highRisk}</strong>
            </div>
            <div className="tpr-metric">
              <span>Avg. score</span>
              <strong>{avgScore}</strong>
            </div>
          </div>
          <div className="tpr-status">{status}</div>
        </div>

        <div className="tpr-card">
          <div className="tpr-title">Create Assessment</div>
          <div className="tpr-form">
            <div className="tpr-field">
              <label>Assessment Context</label>
              <div className="tpr-row">
                <input
                  className="tpr-input"
                  type="text"
                  placeholder="Assessment ID"
                  value={assessmentId}
                  onChange={(event) => setAssessmentId(event.target.value)}
                />
                <button className="tpr-btn secondary" onClick={handleSaveContext}>
                  Save
                </button>
              </div>
              <div className="tpr-help">Links third-party assessments to the active IRMMF assessment.</div>
            </div>

            <label>
              Partner Name
              <input
                className="tpr-input"
                type="text"
                placeholder="Partner or supplier name"
                value={form.partner_name}
                onChange={(event) => setForm((prev) => ({ ...prev, partner_name: event.target.value }))}
              />
            </label>

            <div className="tpr-form-grid">
              <label>
                Partner Type
                <select
                  className="tpr-input"
                  value={form.partner_type}
                  onChange={(event) => setForm((prev) => ({ ...prev, partner_type: event.target.value }))}
                >
                  <option value="Supplier">Supplier</option>
                  <option value="Service Provider">Service Provider</option>
                  <option value="Strategic Partner">Strategic Partner</option>
                  <option value="Consultant">Consultant</option>
                  <option value="Other">Other</option>
                </select>
              </label>
              <label>
                Risk Tier
                <select
                  className="tpr-input"
                  value={form.risk_tier}
                  onChange={(event) => setForm((prev) => ({ ...prev, risk_tier: event.target.value }))}
                >
                  <option value="Tier-1">Tier-1 (Critical)</option>
                  <option value="Tier-2">Tier-2 (Material)</option>
                  <option value="Tier-3">Tier-3 (Low)</option>
                </select>
              </label>
              <label>
                Status
                <select
                  className="tpr-input"
                  value={form.status}
                  onChange={(event) => setForm((prev) => ({ ...prev, status: event.target.value }))}
                >
                  <option value="draft">Draft</option>
                  <option value="in_review">In Review</option>
                  <option value="active">Active</option>
                  <option value="closed">Closed</option>
                </select>
              </label>
              <label>
                Initial Score
                <input
                  className="tpr-input"
                  type="number"
                  step="0.1"
                  placeholder="0-4"
                  value={form.score}
                  onChange={(event) => setForm((prev) => ({ ...prev, score: event.target.value }))}
                />
              </label>
            </div>

            <label>
              Summary
              <textarea
                className="tpr-input"
                placeholder="Capture partner context, contracts, or control gaps."
                value={form.summary}
                onChange={(event) => setForm((prev) => ({ ...prev, summary: event.target.value }))}
              />
            </label>

            <div className="tpr-actions">
              <button className="tpr-btn" onClick={handleCreate} disabled={isSubmitting}>
                {isSubmitting ? 'Creating...' : 'Create Assessment'}
              </button>
              <button
                className="tpr-btn secondary"
                onClick={() => setForm(defaultForm)}
                disabled={isSubmitting}
              >
                Reset
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="tpr-card">
        <div className="tpr-title">Quick Questionnaire</div>
        {assessments.length === 0 ? (
          <div className="tpr-muted">Create a partner assessment to start scoring.</div>
        ) : (
          <div className="tpr-questionnaire">
            <div className="tpr-row tpr-row-tight">
              <label className="tpr-field">
                Partner
                <select
                  className="tpr-input"
                  value={selectedPartnerId}
                  onChange={(event) => setSelectedPartnerId(event.target.value)}
                >
                  {assessments.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.partner_name} · {item.risk_tier}
                    </option>
                  ))}
                </select>
              </label>
              <div className="tpr-score-summary">
                <div>
                  <span>Score</span>
                  <strong>{formatScore(selectedAssessment?.score)}</strong>
                </div>
                <div>
                  <span>Risk band</span>
                  <strong>{computed?.risk_band || '--'}</strong>
                </div>
                <div>
                  <span>Coverage</span>
                  <strong>{coveragePercent}</strong>
                </div>
              </div>
            </div>

            {questions.length === 0 ? (
              <div className="tpr-muted">Question bank unavailable.</div>
            ) : (
              <div className="tpr-question-list">
                {questions.map((question) => (
                  <div key={question.q_id} className="tpr-question">
                    <div className="tpr-question-header">
                      <div className="tpr-question-text">{question.question_text}</div>
                      {question.category ? <div className="tpr-question-tag">{question.category}</div> : null}
                    </div>
                    <select
                      className="tpr-input"
                      value={answers[question.q_id] || ''}
                      onChange={(event) =>
                        setAnswers((prev) => ({ ...prev, [question.q_id]: event.target.value }))
                      }
                    >
                      <option value="">Select...</option>
                      {question.options.map((opt) => (
                        <option key={opt.a_id} value={opt.a_id}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            )}

            <div className="tpr-actions">
              <button className="tpr-btn" onClick={handleScore} disabled={isScoring}>
                {isScoring ? 'Scoring...' : 'Calculate Score'}
              </button>
              <button className="tpr-btn secondary" onClick={() => setAnswers({})} disabled={isScoring}>
                Clear Answers
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="tpr-card">
        <div className="tpr-title">Assessments</div>
        {assessments.length === 0 ? (
          <div className="tpr-muted">No partner assessments yet. Create one to start tracking third-party exposure.</div>
        ) : (
          <div className="tpr-list">
            {assessments.map((item) => (
              <article key={item.id} className="tpr-item">
                <div className="tpr-item-header">
                  <div>
                    <div className="tpr-item-title">{item.partner_name}</div>
                    <div className="tpr-item-sub">
                      {item.partner_type} • {item.risk_tier} • Assessment Linked
                    </div>
                  </div>
                  <div className="tpr-item-actions">
                    <div className={`tpr-pill ${item.status.toLowerCase()}`}>{item.status}</div>
                    <button className="tpr-btn secondary" onClick={() => openDetail(item)}>
                      Details
                    </button>
                  </div>
                </div>
                <div className="tpr-item-meta">
                  <div>
                    <span>Score</span>
                    <strong>{formatScore(item.score)}</strong>
                  </div>
                  <div>
                    <span>Risk Band</span>
                    <strong>{extractComputed(item)?.risk_band || '--'}</strong>
                  </div>
                  <div>
                    <span>Updated</span>
                    <strong>{formatDate(item.updated_at)}</strong>
                  </div>
                </div>
                {item.summary ? <div className="tpr-item-summary">{item.summary}</div> : null}
              </article>
            ))}
          </div>
        )}
      </div>

      <div className={`overlay ${detailOpen ? 'active' : ''}`} onClick={() => setDetailOpen(false)}>
        <div className="overlay-panel wide tpr-overlay" onClick={(event) => event.stopPropagation()}>
          <div className="overlay-header">
            <div>
              <h3 className="overlay-title">Partner Detail</h3>
              <div className="overlay-subtitle">
                {detailAssessment ? `${detailAssessment.partner_name}` : 'Loading'}
              </div>
            </div>
            <button className="overlay-close" onClick={() => setDetailOpen(false)} aria-label="Close">
              ×
            </button>
          </div>
          <div className="overlay-body">
            {detailAssessment ? (
              <div className="tpr-detail-grid">
                <label>
                  Partner Name
                  <input
                    className="tpr-input"
                    type="text"
                    value={detailForm.partner_name}
                    onChange={(event) => setDetailForm((prev) => ({ ...prev, partner_name: event.target.value }))}
                  />
                </label>
                <label>
                  Partner Type
                  <select
                    className="tpr-input"
                    value={detailForm.partner_type}
                    onChange={(event) => setDetailForm((prev) => ({ ...prev, partner_type: event.target.value }))}
                  >
                    <option value="Supplier">Supplier</option>
                    <option value="Service Provider">Service Provider</option>
                    <option value="Strategic Partner">Strategic Partner</option>
                    <option value="Consultant">Consultant</option>
                    <option value="Other">Other</option>
                  </select>
                </label>
                <label>
                  Risk Tier
                  <select
                    className="tpr-input"
                    value={detailForm.risk_tier}
                    onChange={(event) => setDetailForm((prev) => ({ ...prev, risk_tier: event.target.value }))}
                  >
                    <option value="Tier-1">Tier-1 (Critical)</option>
                    <option value="Tier-2">Tier-2 (Material)</option>
                    <option value="Tier-3">Tier-3 (Low)</option>
                  </select>
                </label>
                <label>
                  Status
                  <select
                    className="tpr-input"
                    value={detailForm.status}
                    onChange={(event) => setDetailForm((prev) => ({ ...prev, status: event.target.value }))}
                  >
                    <option value="draft">Draft</option>
                    <option value="in_review">In Review</option>
                    <option value="active">Active</option>
                    <option value="closed">Closed</option>
                  </select>
                </label>
                <label>
                  Score
                  <input
                    className="tpr-input"
                    type="number"
                    step="0.1"
                    value={detailForm.score}
                    onChange={(event) => setDetailForm((prev) => ({ ...prev, score: event.target.value }))}
                  />
                </label>
                <label className="tpr-detail-span">
                  Summary
                  <textarea
                    className="tpr-input"
                    value={detailForm.summary}
                    onChange={(event) => setDetailForm((prev) => ({ ...prev, summary: event.target.value }))}
                  />
                </label>
                <div className="tpr-detail-metrics">
                  <div>
                    <span>Current Score</span>
                    <strong>{formatScore(detailAssessment.score)}</strong>
                  </div>
                  <div>
                    <span>Risk Band</span>
                    <strong>{detailComputed?.risk_band || '--'}</strong>
                  </div>
                  <div>
                    <span>Coverage</span>
                    <strong>{detailCoverage}</strong>
                  </div>
                </div>
              </div>
            ) : (
              <div className="tpr-muted">Loading partner detail...</div>
            )}

            <div className="tpr-response-section">
              <div className="tpr-response-title">Saved Responses</div>
              {detailResponses.length === 0 ? (
                <div className="tpr-muted">No responses saved yet.</div>
              ) : (
                <div className="tpr-response-grid">
                  {detailResponses.map((row) => (
                    <div key={`${row.q_id}-${row.answer_text || ''}`} className="tpr-response-row">
                      <div>
                        <div className="tpr-response-question">{row.question_text || row.q_id}</div>
                        <div className="tpr-response-meta">
                          {row.category ? `${row.category} · ` : ''}Answer: {row.answer_text || '--'}
                        </div>
                      </div>
                      <div className="tpr-response-score">{formatScore(row.score ?? null)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className="overlay-footer">
            <button className="tpr-btn secondary" onClick={() => setDetailOpen(false)} disabled={isUpdating}>
              Close
            </button>
            <button className="tpr-btn" onClick={handleDetailUpdate} disabled={isUpdating}>
              {isUpdating ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}

export default ThirdPartyRisk
