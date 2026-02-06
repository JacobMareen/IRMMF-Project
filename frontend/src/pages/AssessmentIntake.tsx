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
