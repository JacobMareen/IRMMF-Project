import { useEffect, useMemo, useState } from 'react'
import './AssessmentRisks.css'
import { describeAssessmentError, getStoredAssessmentId } from '../utils/assessment'
import { apiFetchRoot, readApiError } from '../lib/api'
import { getDomainMeta } from '../utils/domainMetadata'

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
  const axisToDomains: Record<string, string[]> = {
    Governance: ['Strategy & Governance'],
    Execution: ['Threat Model & Operations', 'Performance & Resilience'],
    Technical: ['Technical Controls'],
    'Technical Orchestration': ['Technical Controls'],
    Legal: ['Legal, Privacy & Ethics'],
    'Legal & Privacy': ['Legal, Privacy & Ethics'],
    Human: ['Human-Centric Culture'],
    'Human Sentiment': ['Human-Centric Culture'],
    Visibility: ['Technical Controls', 'Behavioral Analytics & Detection'],
    Resilience: ['Performance & Resilience', 'Investigation & Response'],
    Friction: ['Human-Centric Culture', 'Technical Controls'],
    'Control Lag': ['Performance & Resilience', 'Threat Model & Operations'],
    'Control Lag Management': ['Performance & Resilience', 'Threat Model & Operations'],
  }

  const getRiskFocusDomains = (risk: RiskPoint) => {
    const gaps = risk.key_gaps || []
    const domainSet = new Set<string>()
    gaps.forEach((gap) => {
      const axis = gap.split(':')[0]?.trim()
      if (!axis) return
      const mapped = axisToDomains[axis] || []
      mapped.forEach((d) => domainSet.add(d))
    })
    return Array.from(domainSet)
  }

  const focusDomains = useMemo(() => {
    const counts = new Map<string, number>()
    topRisks.forEach((risk) => {
      getRiskFocusDomains(risk).forEach((domain) => {
        counts.set(domain, (counts.get(domain) || 0) + 1)
      })
    })
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([domain, count]) => {
        const meta = getDomainMeta(domain)
        return {
          domain,
          count,
          label: meta.label,
          icon: meta.icon,
          capabilities: meta.capabilities || [],
        }
      })
  }, [topRisks])


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
                      {r.category || 'General'} · L{r.likelihood} × I{r.impact} · {r.risk_level}
                    </div>
                    {r.description ? <div className="rk-risk-desc">{r.description}</div> : null}
                    {r.key_gaps && r.key_gaps.length ? (
                      <div className="rk-risk-tags">
                        {r.key_gaps.map((gap) => (
                          <span key={gap} className="rk-gap-tag">{gap}</span>
                        ))}
                      </div>
                    ) : null}
                    {getRiskFocusDomains(r).length ? (
                      <div className="rk-risk-focus">
                        {getRiskFocusDomains(r).map((domain) => {
                          const meta = getDomainMeta(domain)
                          return (
                            <span key={domain} className="rk-risk-focus-tag">
                              {meta.icon} {meta.label}
                            </span>
                          )
                        })}
                      </div>
                    ) : null}
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="rk-card">
            <div className="rk-card-title">Risk Focus Areas</div>
            <div className="rk-muted">
              Focus domains inferred from top risk key gaps (prioritize these for mitigation uplift).
            </div>
            {focusDomains.length ? (
              <div className="rk-focus-grid">
                {focusDomains.map((domain) => (
                  <div key={domain.domain} className="rk-focus-card">
                    <div className="rk-focus-header">
                      <div className="rk-focus-title">
                        <span className="rk-focus-icon">{domain.icon}</span>
                        <span>{domain.label}</span>
                      </div>
                      <span className="rk-focus-count">Top risks: {domain.count}</span>
                    </div>
                    {domain.capabilities.length ? (
                      <div className="rk-focus-tags">
                        {domain.capabilities.slice(0, 4).map((cap) => (
                          <span key={cap} className="rk-focus-tag">{cap}</span>
                        ))}
                      </div>
                    ) : (
                      <div className="rk-muted">No capability tags listed.</div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="rk-muted">No focus areas identified yet.</div>
            )}
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
                  <span>Key Gaps</span>
                </div>
                {heatmap.map((r, idx) => (
                  <div key={`${r.scenario || r.name}-${idx}`} className="rk-row">
                    <span>{r.scenario || r.name}</span>
                    <span className="rk-muted">{r.category || '—'}</span>
                    <span>{r.likelihood}</span>
                    <span>{r.impact}</span>
                    <span>{r.risk_level}</span>
                    <span>{r.risk_score}</span>
                    <span>
                      {r.key_gaps && r.key_gaps.length ? (
                        <div className="rk-gap-tags">
                          {r.key_gaps.map((gap) => (
                            <span key={gap} className="rk-gap-tag">{gap}</span>
                          ))}
                        </div>
                      ) : (
                        <span className="rk-muted">—</span>
                      )}
                    </span>
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
