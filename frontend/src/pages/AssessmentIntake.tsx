import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, readApiError } from '../lib/api'
import './AssessmentIntake.css'
import { describeAssessmentError, getStoredAssessmentId } from '../utils/assessment'
import { AssessmentNav } from '../components/AssessmentNav'
import { PageHeader } from '../components/PageHeader'

type IntakeOption = { value: string; display_order?: number }
type IntakeQuestion = {
  intake_q_id: string
  section?: string
  question_text?: string
  guidance?: string
  input_type?: string
  options?: IntakeOption[]
}

type IntakeAnswerRow = { intake_q_id: string; value?: string | null }

const AssessmentIntake = () => {
  const navigate = useNavigate()
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [assessmentId, setAssessmentId] = useState<string>('')
  const [questions, setQuestions] = useState<IntakeQuestion[]>([])
  const [draft, setDraft] = useState<Record<string, string>>({})
  const [index, setIndex] = useState(0)
  const [status, setStatus] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [scrapeUrl, setScrapeUrl] = useState('')
  const [scrapeStatus, setScrapeStatus] = useState('')
  const [scrapeLoading, setScrapeLoading] = useState(false)
  const [scrapePreview, setScrapePreview] = useState<Record<string, unknown> | null>(null)
  const [scrapeSuggestions, setScrapeSuggestions] = useState<Record<string, string>>({})
  const [scrapeSelected, setScrapeSelected] = useState<Record<string, boolean>>({})

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    if (!assessmentId) {
      setLoading(false)
      return
    }
    const controller = new AbortController()
    setLoading(true)
    setStatus('')
    Promise.all([
      apiFetch(`/intake/start`, { signal: controller.signal }),
      apiFetch(`/intake/${assessmentId}`, { signal: controller.signal }),
    ])
      .then(async ([questionsResp, intakeResp]) => {
        if (!questionsResp.ok) {
          const detail = await readApiError(questionsResp)
          throw new Error(describeAssessmentError(detail, 'Unable to load intake questions.'))
        }
        const qs = (await questionsResp.json()) as IntakeQuestion[]
        setQuestions(qs)
        const answers = intakeResp.ok ? ((await intakeResp.json()) as IntakeAnswerRow[]) : []
        if (!intakeResp.ok) {
          const detail = await readApiError(intakeResp)
          setStatus(describeAssessmentError(detail, 'Intake answers unavailable. You can still complete intake.'))
        }
        const nextDraft: Record<string, string> = {}
        answers.forEach((row) => {
          if (row.value) nextDraft[row.intake_q_id] = row.value
        })
        setDraft(nextDraft)
        const firstUnanswered = qs.findIndex((q) => !nextDraft[q.intake_q_id])
        setIndex(firstUnanswered >= 0 ? firstUnanswered : 0)
        const answeredCount = Object.values(nextDraft).filter((val) => val != null && val !== '').length
        localStorage.setItem(`intake_total_${assessmentId}`, String(qs.length))
        localStorage.setItem(`intake_answered_${assessmentId}`, String(answeredCount))
      })
      .catch((err) => {
        const fallback = 'Unable to load intake. Check the API and question bank.'
        setStatus(err instanceof Error ? err.message : fallback)
      })
      .finally(() => setLoading(false))

    return () => controller.abort()
  }, [assessmentId])

  useEffect(() => {
    if (!assessmentId || !questions.length) return
    const answeredCount = Object.values(draft).filter((val) => val != null && val !== '').length
    localStorage.setItem(`intake_total_${assessmentId}`, String(questions.length))
    localStorage.setItem(`intake_answered_${assessmentId}`, String(answeredCount))
  }, [assessmentId, questions, draft])

  const question = questions[index]
  const progress = questions.length ? `${index + 1} / ${questions.length}` : '-- / --'
  const currentValue = question ? draft[question.intake_q_id] || '' : ''
  const options = question?.options || []
  const isMulti = (question?.input_type || '').toLowerCase().includes('multi')
  const isText = options.length === 0 || (question?.input_type || '').toLowerCase().includes('text')

  const setAnswer = (value: string) => {
    if (!question) return
    setDraft((prev) => ({ ...prev, [question.intake_q_id]: value }))
  }

  const handleMultiToggle = (value: string) => {
    if (!question) return
    const current = (draft[question.intake_q_id] || '').split(',').map((v) => v.trim()).filter(Boolean)
    const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]
    setDraft((prev) => ({ ...prev, [question.intake_q_id]: next.join(',') }))
  }

  const submitDraft = async (payload?: Record<string, string>) => {
    if (!assessmentId) return
    await apiFetch(`/intake/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assessment_id: assessmentId, answers: payload || draft }),
    })
  }

  const handleNext = async () => {
    if (!question) return
    try {
      await submitDraft()
      if (index < questions.length - 1) {
        setIndex(index + 1)
      } else {
        setStatus('Intake saved.')
      }
    } catch {
      setStatus('Failed to save intake.')
    }
  }

  const handleSingleSelect = async (value: string) => {
    if (!question) return
    const nextDraft = { ...draft, [question.intake_q_id]: value }
    setDraft(nextDraft)
    try {
      await submitDraft(nextDraft)
      if (index < questions.length - 1) {
        window.setTimeout(() => setIndex(index + 1), 100)
      } else {
        setStatus('Intake saved.')
      }
    } catch {
      setStatus('Failed to save intake.')
    }
  }

  const handleScrape = async () => {
    if (!assessmentId) return
    if (!scrapeUrl.trim()) {
      setScrapeStatus('Enter a website URL to analyze.')
      return
    }
    setScrapeLoading(true)
    setScrapeStatus('')
    try {
      const resp = await apiFetch(`/intake/scrape`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_url: scrapeUrl.trim(),
          assessment_id: assessmentId,
          persist: false,
        }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to scrape website.')
      }
      const data = (await resp.json()) as {
        suggested_intake?: Record<string, string>
        analysis?: Record<string, unknown>
      }
      setScrapePreview(data.analysis || null)
      if (data.suggested_intake) {
        setScrapeSuggestions(data.suggested_intake)
        const selections: Record<string, boolean> = {}
        Object.keys(data.suggested_intake).forEach((key) => {
          selections[key] = true
        })
        setScrapeSelected(selections)
      }
      setScrapeStatus('Review the suggested answers before applying.')
    } catch (err) {
      setScrapeStatus(err instanceof Error ? err.message : 'Failed to scrape website.')
    } finally {
      setScrapeLoading(false)
    }
  }

  const toggleScrapeSelection = (key: string) => {
    setScrapeSelected((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const applyScrapeSelections = async (persist: boolean) => {
    const picked: Record<string, string> = {}
    Object.entries(scrapeSuggestions).forEach(([key, value]) => {
      if (scrapeSelected[key]) {
        picked[key] = value
      }
    })
    if (!Object.keys(picked).length) {
      setScrapeStatus('Select at least one suggestion to apply.')
      return
    }
    const merged = { ...draft, ...picked }
    setDraft(merged)
    const firstUnanswered = questions.findIndex((q) => !merged[q.intake_q_id])
    if (firstUnanswered >= 0) {
      setIndex(firstUnanswered)
    }
    if (persist) {
      try {
        await submitDraft(merged)
        setScrapeStatus('Selected answers applied and saved.')
      } catch {
        setScrapeStatus('Applied locally, but failed to save.')
      }
      return
    }
    setScrapeStatus('Selected answers applied locally. Save to persist.')
  }

  if (loading) {
    return <div className="ai-card">Loading intake...</div>
  }

  if (!assessmentId) {
    return (
      <div className="ai-card">
        <h2>Assessment Required</h2>
        <p>Create an assessment first to begin intake.</p>
        <button className="ai-btn primary" onClick={() => navigate('/assessment')}>
          Back to Assessment Hub
        </button>
      </div>
    )
  }

  if (!question) {
    return (
      <div className="ai-card">
        <h2>No intake questions available</h2>
        <p>{status || 'Intake questions are not available yet. Load the question bank and refresh the page.'}</p>
      </div>
    )
  }

  return (
    <section className="ai-page">
      <PageHeader
        title="Intake"
        subtitle={`Assessment ID: ${assessmentId}`}
        actions={<div className="ai-progress">{progress}</div>}
      />

      <div style={{ marginBottom: '20px' }}>
        <AssessmentNav assessmentId={assessmentId} />
      </div>

      <div className="ai-card ai-scrape">
        <div className="ai-scrape-row">
          <div>
            <h2>Auto-fill from website</h2>
            <p className="ai-guidance">
              Paste the company’s public URL to infer intake details (industry, region, size).
            </p>
          </div>
        </div>
        <div className="ai-scrape-controls">
          <input
            className="ai-text ai-scrape-input"
            value={scrapeUrl}
            onChange={(event) => setScrapeUrl(event.target.value)}
            placeholder="https://company.com"
          />
          <button className="ai-btn primary" onClick={handleScrape} disabled={scrapeLoading}>
            {scrapeLoading ? 'Analyzing...' : 'Analyze & Fill'}
          </button>
        </div>
        {scrapePreview ? (
          <div className="ai-scrape-preview">
            {['industries', 'regions', 'regulations', 'company_scale'].map((key) => {
              const value = scrapePreview[key]
              if (!value || (Array.isArray(value) && value.length === 0)) return null
              const items = Array.isArray(value) ? value : [value]
              return (
                <div key={key} className="ai-scrape-meta">
                  <span className="ai-scrape-label">{key.replace('_', ' ')}</span>
                  <div className="ai-scrape-pill-row">
                    {items.map((item) => (
                      <span key={String(item)} className="ai-scrape-pill">
                        {String(item)}
                      </span>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        ) : null}
        {Object.keys(scrapeSuggestions).length ? (
          <div className="ai-scrape-suggestions">
            <div className="ai-scrape-suggestions-header">
              <span>Suggested intake answers</span>
              <span className="ai-scrape-hint">Select what you want to apply.</span>
            </div>
            <div className="ai-scrape-suggestion-list">
              {Object.entries(scrapeSuggestions).map(([key, value]) => (
                <label key={key} className="ai-scrape-suggestion">
                  <input
                    type="checkbox"
                    checked={!!scrapeSelected[key]}
                    onChange={() => toggleScrapeSelection(key)}
                  />
                  <span className="ai-scrape-key">{key.replace(/_/g, ' ')}</span>
                  <span className="ai-scrape-value">{value}</span>
                </label>
              ))}
            </div>
            <div className="ai-scrape-apply">
              <button className="ai-btn secondary" onClick={() => applyScrapeSelections(false)}>
                Apply Selection
              </button>
              <button className="ai-btn primary" onClick={() => applyScrapeSelections(true)}>
                Apply & Save
              </button>
            </div>
          </div>
        ) : null}
        {scrapeStatus ? <div className="ai-status">{scrapeStatus}</div> : null}
      </div>

      <div className="ai-card">
        <div className="ai-section">{question.section || 'Intake'}</div>
        <h2 className="ai-question">{question.question_text || question.intake_q_id}</h2>
        {question.guidance ? <div className="ai-guidance">{question.guidance}</div> : null}

        <div className="ai-inputs">
          {isText && (
            <input
              className="ai-text"
              value={currentValue}
              onChange={(event) => setAnswer(event.target.value)}
              placeholder="Enter response"
            />
          )}
          {!isText && !isMulti && (
            <div className="ai-option-list">
              {options.map((opt) => (
                <button
                  key={opt.value}
                  className={`ai-option ${currentValue === opt.value ? 'active' : ''}`}
                  onClick={() => handleSingleSelect(opt.value)}
                >
                  {opt.value}
                </button>
              ))}
            </div>
          )}
          {!isText && isMulti && (
            <div className="ai-option-list">
              {options.map((opt) => {
                const selected = currentValue.split(',').map((v) => v.trim()).includes(opt.value)
                return (
                  <button
                    key={opt.value}
                    className={`ai-option ${selected ? 'active' : ''}`}
                    onClick={() => handleMultiToggle(opt.value)}
                  >
                    {opt.value}
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <div className="ai-actions">
          <button className="ai-btn secondary" onClick={() => setIndex(Math.max(0, index - 1))}>
            Back
          </button>
          <button className="ai-btn primary" onClick={handleNext}>
            {index >= questions.length - 1 ? 'Finish Intake' : 'Save & Continue'}
          </button>
        </div>
        {status ? <div className="ai-status">{status}</div> : null}
      </div>
    </section>
  )
}

export default AssessmentIntake
