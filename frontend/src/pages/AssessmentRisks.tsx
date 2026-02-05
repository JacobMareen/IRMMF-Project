import { useEffect, useMemo, useState } from 'react'
import './AssessmentRisks.css'
import { describeAssessmentError, getStoredAssessmentId } from '../utils/assessment'
import { apiFetchRoot, readApiError } from '../lib/api'

import { RiskHeatmap, type RiskPoint } from '../components/RiskHeatmap'
import { AssessmentNav } from '../components/AssessmentNav'
import { PageHeader } from '../components/PageHeader'

type RiskPayload = {
  risk_heatmap?: RiskPoint[]
  top_risks?: RiskPoint[]
}

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
    apiFetchRoot(`/responses/analysis/${assessmentId}`)
      .then(async (res) => {
        if (!res.ok) {
          const detail = await readApiError(res)
          throw new Error(describeAssessmentError(detail, 'Risk data unavailable.'))
        }
        return res.json()
      })
      .then((data) => {
        if (!data) throw new Error('No data')
        setPayload(data)
        setStatus('')
      })
      .catch((err) => setStatus(err instanceof Error ? err.message : 'Risk data unavailable. Check API status.'))
  }, [assessmentId])

  const heatmap = payload?.risk_heatmap || []
  const topRisks = payload?.top_risks || []


  return (
    <section className="rk-page">
      <PageHeader
        title="Risk Intelligence"
        subtitle={`Insider risk program view · Assessment ID: ${assessmentId || 'Not set'}`}
      />

      <div style={{ marginBottom: '20px' }}>
        <AssessmentNav assessmentId={assessmentId} />
      </div>

      {status ? <div className="rk-card">{status}</div> : null}

      {!status && (
        <>
          <section className="rk-grid">
            <div className="rk-card">
              <div className="rk-card-title">Risk Heatmap</div>
              <div className="rk-heatmap-container">
                <RiskHeatmap risks={heatmap} size={500} />
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
                  <span>Category</span>
                  <span>L</span>
                  <span>I</span>
                  <span>Level</span>
                  <span>Score</span>
                  <span>Treatment</span>
                </div>
                {heatmap.map((r, idx) => (
                  <div key={`${r.scenario || r.name}-${idx}`} className="rk-row">
                    <span>{r.scenario || r.name}</span>
                    <span className="rk-muted">{r.category || '—'}</span>
                    <span>{r.likelihood}</span>
                    <span>{r.impact}</span>
                    <span>{r.risk_level}</span>
                    <span>{r.risk_score}</span>
                    <span className="rk-muted">Not Started</span>
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
