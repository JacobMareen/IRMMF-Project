import { useEffect, useMemo, useState } from 'react'
import './AssessmentRisks.css'
import { getStoredAssessmentId } from '../utils/assessment'

type RiskEntry = {
  scenario?: string
  name?: string
  category?: string
  likelihood?: number
  impact?: number
  risk_level?: string
  risk_score?: number
}

type RiskPayload = {
  risk_heatmap?: RiskEntry[]
  top_risks?: RiskEntry[]
}

const API_BASE = 'http://127.0.0.1:8000'

const AssessmentRisks = () => {
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [assessmentId, setAssessmentId] = useState('')
  const [payload, setPayload] = useState<RiskPayload | null>(null)
  const [status, setStatus] = useState('Loading risks...')

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    if (!assessmentId) {
      setStatus('No assessment selected.')
      return
    }
    setStatus('Loading risks...')
    fetch(`${API_BASE}/responses/analysis/${assessmentId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!data) throw new Error('No data')
        setPayload(data)
        setStatus('')
      })
      .catch(() => setStatus('Risk data unavailable. Check API status.'))
  }, [assessmentId])

  const heatmap = payload?.risk_heatmap || []
  const topRisks = payload?.top_risks || []
  const dotRadius = 8

  return (
    <section className="rk-page">
      <div className="rk-header">
        <div>
          <h1>Risk Overview</h1>
          <p className="rk-subtitle">
            Assessment ID: <strong>{assessmentId || 'Not set'}</strong>
          </p>
        </div>
      </div>

      {status ? <div className="rk-card">{status}</div> : null}

      {!status && (
        <>
          <section className="rk-grid">
            <div className="rk-card">
              <div className="rk-card-title">Risk Heatmap</div>
              <div className="rk-heatmap">
                <div className="rk-axis-labels">
                  <span>7</span>
                  <span>6</span>
                  <span>5</span>
                  <span>4</span>
                  <span>3</span>
                  <span>2</span>
                  <span>1</span>
                </div>
                <div className="rk-heatmap-grid">
                  {heatmap.map((r, idx) => {
                    const likelihood = Math.min(7, Math.max(1, Number(r.likelihood || 1)))
                    const impact = Math.min(7, Math.max(1, Number(r.impact || 1)))
                    const x = (likelihood - 1) / 6
                    const y = (impact - 1) / 6
                    const left = `clamp(${dotRadius}px, ${x * 100}%, calc(100% - ${dotRadius}px))`
                    const top = `clamp(${dotRadius}px, ${(1 - y) * 100}%, calc(100% - ${dotRadius}px))`
                    return (
                      <div
                        key={`${r.scenario || r.name}-${idx}`}
                        className={`rk-dot level-${(r.risk_level || 'green').toLowerCase()}`}
                        style={{ left, top }}
                        title={`${r.scenario || r.name} (L${likelihood} × I${impact})`}
                      />
                    )
                  })}
                </div>
                <div className="rk-axis-spacer" />
                <div className="rk-axis-bottom">
                  <span>1</span>
                  <span>2</span>
                  <span>3</span>
                  <span>4</span>
                  <span>5</span>
                  <span>6</span>
                  <span>7</span>
                </div>
              </div>
            </div>

            <div className="rk-card">
              <div className="rk-card-title">Top Risks</div>
              {topRisks.length === 0 ? (
                <div className="rk-muted">No top risks available.</div>
              ) : (
                topRisks.map((r, idx) => (
                  <div key={`${r.scenario || r.name}-${idx}`} className="rk-risk">
                    <strong>{r.scenario || r.name}</strong>
                    <div className="rk-subtext">
                      L{r.likelihood} × I{r.impact} · {r.risk_level}
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="rk-card">
            <div className="rk-card-title">Risk Table</div>
            {heatmap.length === 0 ? (
              <div className="rk-muted">No risk data available.</div>
            ) : (
              <div className="rk-table">
                <div className="rk-row rk-header-row">
                  <span>Risk</span>
                  <span>L</span>
                  <span>I</span>
                  <span>Level</span>
                  <span>Score</span>
                </div>
                {heatmap.map((r, idx) => (
                  <div key={`${r.scenario || r.name}-${idx}`} className="rk-row">
                    <span>{r.scenario || r.name}</span>
                    <span>{r.likelihood}</span>
                    <span>{r.impact}</span>
                    <span>{r.risk_level}</span>
                    <span>{r.risk_score}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </section>
  )
}

export default AssessmentRisks
