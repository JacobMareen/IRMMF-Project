import { useEffect, useMemo, useState } from 'react'
import './DynamicWorkforce.css'
import { getStoredAssessmentId, storeAssessmentId } from '../utils/assessment'
import { apiFetch, apiJson } from '../lib/api'

type DwfOption = { a_id: string; answer_text: string; base_score: number }
type DwfQuestion = {
  q_id: string
  section?: string
  question_title?: string
  question_text: string
  options?: DwfOption[]
}

const DynamicWorkforce = () => {
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [assessmentId, setAssessmentId] = useState('')
  const [questions, setQuestions] = useState<DwfQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [status, setStatus] = useState('No assessment loaded.')
  const [analysis, setAnalysis] = useState<string>('Run analysis to view DWF scores.')

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    if (assessmentId) {
      registerAssessment(assessmentId)
    }
  }, [assessmentId])

  const registerAssessment = (aid: string) => {
    if (!aid) return
    apiFetch(`/dwf/assessment/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assessment_id: aid }),
    })
      .then(() => {
        setStatus(`Active assessment: ${aid}`)
        loadQuestions()
      })
      .catch(() => {
        setStatus('Failed to register assessment.')
      })
  }

  const loadQuestions = () => {
    apiJson<DwfQuestion[]>('/dwf/questions/all')
      .then((data: DwfQuestion[]) => {
        setQuestions(data || [])
      })
      .catch(() => {
        setQuestions([])
      })
  }

  const grouped = questions.reduce<Record<string, DwfQuestion[]>>((acc, q) => {
    const section = q.section || 'General'
    acc[section] = acc[section] || []
    acc[section].push(q)
    return acc
  }, {})

  const handleSubmit = (qid: string) => {
    if (!assessmentId) {
      setStatus('Register an assessment ID first.')
      return
    }
    const selected = answers[qid]
    if (!selected) return
    const q = questions.find((item) => item.q_id === qid)
    const opt = q?.options?.find((o) => o.a_id === selected)
    const score = opt?.base_score ?? 0
    apiFetch(`/dwf/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        assessment_id: assessmentId,
        q_id: qid,
        a_id: selected,
        score,
      }),
    })
      .then(() => {
        setStatus(`Saved response for ${qid}`)
      })
      .catch(() => {
        setStatus('Failed to save response.')
      })
  }

  const runAnalysis = () => {
    if (!assessmentId) return
    apiJson(`/dwf/assessment/${encodeURIComponent(assessmentId)}/analysis`)
      .then((data) => {
        if (!data) throw new Error('No analysis')
        setAnalysis(JSON.stringify(data, null, 2))
      })
      .catch(() => {
        setAnalysis('Failed to load analysis.')
      })
  }

  return (
    <section className="dwf-page">
      <div className="dwf-header">
        <div>
          <h1>Dynamic Workforce</h1>
          <p className="dwf-subtitle">Workforce risk module focused on culture, role impact, and resilience signals.</p>
        </div>
      </div>

      <div className="dwf-grid">
        <div className="dwf-card">
          <div className="dwf-title">Assessment Setup</div>
          <div className="dwf-row">
            <input
              className="dwf-input"
              type="text"
              placeholder="Assessment ID (IRMMF-...)"
              value={assessmentId}
              onChange={(event) => setAssessmentId(event.target.value)}
            />
            <button
              className="dwf-btn"
              onClick={() => {
                storeAssessmentId(assessmentId, currentUser)
                registerAssessment(assessmentId)
              }}
            >
              Register
            </button>
          </div>
          <div className="dwf-status">{status}</div>
          <div className="dwf-title spaced">Questions</div>
          {Object.keys(grouped).length === 0 ? (
            <div className="dwf-muted">No DWF questions loaded.</div>
          ) : (
            Object.entries(grouped).map(([section, items]) => (
              <div key={section} className="dwf-section">
                <div className="dwf-section-title">{section}</div>
                {items.map((q) => (
                  <div key={q.q_id} className="dwf-question">
                    <div className="dwf-question-title">{q.question_title || q.q_id}</div>
                    <div className="dwf-question-text">{q.question_text}</div>
                    <div className="dwf-actions">
                      <select
                        className="dwf-select"
                        value={answers[q.q_id] || ''}
                        onChange={(event) => setAnswers((prev) => ({ ...prev, [q.q_id]: event.target.value }))}
                      >
                        <option value="">Select...</option>
                        {(q.options || []).map((opt) => (
                          <option key={opt.a_id} value={opt.a_id}>
                            {opt.answer_text}
                          </option>
                        ))}
                      </select>
                      <button className="dwf-btn outline" onClick={() => handleSubmit(q.q_id)}>
                        Save
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ))
          )}
        </div>

        <div className="dwf-card">
          <div className="dwf-title">Analysis</div>
          <button className="dwf-btn" onClick={runAnalysis}>
            Run Analysis
          </button>
          <pre className="dwf-analysis">{analysis}</pre>
        </div>
      </div>
    </section>
  )
}

export default DynamicWorkforce
