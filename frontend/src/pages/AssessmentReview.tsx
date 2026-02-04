import { useEffect, useMemo, useState } from 'react'
import './AssessmentReview.css'
import { describeAssessmentError, getStoredAssessmentId } from '../utils/assessment'
import { apiFetch, apiFetchRoot, readApiError } from '../lib/api'

type AnswerOption = { a_id: string; answer_text: string; base_score: number }
type Question = {
  q_id: string
  domain: string
  question_title?: string
  question_text: string
  options: AnswerOption[]
}

type ReviewRow = {
  q_id: string
  question?: string
  question_title?: string
  answer?: string
  a_id?: string
  score?: number
  domain?: string
  tier?: string
  evidence_confidence?: number
  is_deferred?: boolean
  is_flagged?: boolean
}

type IntakeAnswer = {
  intake_q_id: string
  value: string
}

const AssessmentReview = () => {
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [assessmentId, setAssessmentId] = useState('')
  const [rows, setRows] = useState<ReviewRow[]>([])
  const [questions, setQuestions] = useState<Question[]>([])
  const [intakeAnswers, setIntakeAnswers] = useState<IntakeAnswer[]>([])
  const [status, setStatus] = useState('Loading review table...')

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    if (!assessmentId) return
    apiFetch(`/questions/all?assessment_id=${assessmentId}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setQuestions(data))
      .catch(() => setQuestions([]))
  }, [assessmentId])

  const loadReview = () => {
    if (!assessmentId) {
      setStatus('No assessment selected.')
      return
    }
    setStatus('Loading review table...')
    Promise.all([
    apiFetchRoot(`/responses/table/${assessmentId}`),
    apiFetch(`/intake/${assessmentId}`),
    ])
      .then(async ([reviewResp, intakeResp]) => {
        if (!reviewResp.ok) {
          const detail = await readApiError(reviewResp)
          throw new Error(describeAssessmentError(detail, 'Review table unavailable.'))
        }
        const reviewData = await reviewResp.json()
        const intakeData = intakeResp.ok ? await intakeResp.json() : []
        setRows(reviewData)
        setIntakeAnswers(Array.isArray(intakeData) ? intakeData : [])
        if (!intakeResp.ok) {
          const detail = await readApiError(intakeResp)
          setStatus(describeAssessmentError(detail, 'Intake answers unavailable. Review table loaded.'))
        } else {
          setStatus('')
        }
      })
      .catch((err) => setStatus(err instanceof Error ? err.message : 'Review table unavailable. Check API status.'))
  }

  useEffect(() => {
    loadReview()
  }, [assessmentId])

  const getScoreForAnswer = (qId: string, aId: string) => {
    const q = questions.find((item) => item.q_id === qId)
    const opt = q?.options?.find((o) => o.a_id === aId)
    return opt ? opt.base_score : 0
  }

  const updateReviewAnswer = async (qId: string, aId: string, isFlagged?: boolean) => {
    const q = questions.find((item) => item.q_id === qId)
    if (!q || !assessmentId) return
    const score = getScoreForAnswer(qId, aId)
    await apiFetch(`/assessment/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        assessment_id: assessmentId,
        q_id: qId,
        a_id: aId,
        score,
        pack_id: q.domain,
        is_flagged: isFlagged || false,
        is_deferred: false,
      }),
    })
  }

  const exportCsv = () => {
    if (!rows.length) {
      alert('No review data to export.')
      return
    }
    const headers = ['q_id', 'question', 'answer', 'evidence_confidence', 'is_deferred', 'is_flagged', 'domain']
    const lines = [
      headers.join(','),
      ...rows.map((row) =>
        headers
          .map((key) => {
            const value = row[key as keyof ReviewRow]
            return `"${value == null ? '' : String(value).replace(/\"/g, '""')}"`
          })
          .join(',')
      ),
    ]
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `review-${assessmentId || 'export'}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  const groupedRows = useMemo(() => {
    return rows.reduce<Record<string, ReviewRow[]>>((acc, row) => {
      const key = row.domain || 'Unassigned'
      if (!acc[key]) acc[key] = []
      acc[key].push(row)
      return acc
    }, {})
  }, [rows])

  return (
    <section className="rv-page">
      <div className="rv-header">
        <div>
          <h1>Review Queue</h1>
          <p className="rv-subtitle">
            Assessment ID: <strong>{assessmentId || 'Not set'}</strong>
          </p>
        </div>
        <button className="rv-btn" onClick={exportCsv}>
          Export CSV
        </button>
      </div>

      {status ? <div className="rv-card">{status}</div> : null}

      {!status && intakeAnswers.length > 0 ? (
        <div className="rv-card">
          <div className="rv-card-title">Intake Answers</div>
          <div className="rv-table">
            <div className="rv-row rv-row-2 rv-header-row">
              <span>Question</span>
              <span>Answer</span>
            </div>
            {intakeAnswers.map((row) => (
              <div key={row.intake_q_id} className="rv-row rv-row-2">
                <span>{row.intake_q_id}</span>
                <span>{row.value}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {!status &&
        (Object.keys(groupedRows).length ? (
          Object.keys(groupedRows)
            .sort()
            .map((domain) => (
              <details key={domain} className="rv-card" open>
                <summary className="rv-summary">
                  {domain} ({groupedRows[domain].length})
                </summary>
                <div className="rv-table">
                  <div className="rv-row rv-header-row">
                    <span>Question</span>
                    <span>Answer</span>
                    <span>Evidence</span>
                    <span>Flags</span>
                  </div>
                  {groupedRows[domain].map((row) => {
                    const q = questions.find((item) => item.q_id === row.q_id)
                    const options = q?.options || []
                    return (
                      <div key={row.q_id} className="rv-row">
                        <span>{row.question_title || row.question || row.q_id}</span>
                        <span>
                          {options.length ? (
                            <select
                              value={row.a_id}
                              onChange={async (event) => {
                                await updateReviewAnswer(row.q_id, event.target.value, row.is_flagged)
                                loadReview()
                              }}
                            >
                              {options.map((opt) => (
                                <option key={opt.a_id} value={opt.a_id}>
                                  {opt.answer_text}
                                </option>
                              ))}
                            </select>
                          ) : (
                            row.answer || '—'
                          )}
                        </span>
                        <span>
                          {row.evidence_confidence != null
                            ? `${Math.round(row.evidence_confidence * 100)}%`
                            : '—'}
                        </span>
                        <span>
                          {row.is_flagged ? 'Review ' : ''}
                          {row.is_deferred ? 'Deferred' : ''}
                          {!row.is_flagged && !row.is_deferred ? '—' : ''}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </details>
            ))
        ) : (
          <div className="rv-card rv-muted">No responses yet.</div>
        ))}
    </section>
  )
}

export default AssessmentReview
