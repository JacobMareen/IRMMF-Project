import { useEffect, useMemo, useRef, useState } from 'react'
import Chart from 'chart.js/auto'
import './AssessmentResults.css'
import { describeAssessmentError, getStoredAssessmentId } from '../utils/assessment'
import { apiFetchRoot, API_BASE, readApiError } from '../lib/api'

type AxisScore = { axis?: string; code?: string; score?: number }
type Recommendation = {
  title: string
  priority?: string
  timeline?: string
  rationale?: string
}
type ArchetypeDetails = {
  rationale?: string[]
}
type MaturityScores = {
  baseline?: { trust_index?: number; friction_score?: number }
  expanded?: { trust_index?: number; friction_score?: number }
}
type CapApplied = {
  type?: string
  axis?: string
  cap_to?: number
  reason?: string
}
type ResultsPayload = {
  archetype?: string
  archetype_details?: ArchetypeDetails
  summary?: {
    trust_index?: number
    friction_score?: number
    evidence_confidence_avg?: number
  }
  axes?: AxisScore[]
  expanded_axes?: AxisScore[]
  declared_vector?: AxisScore[]
  verified_vector?: AxisScore[]
  gap_vector?: AxisScore[]
  recommendations?: Recommendation[]
  maturity_scores?: MaturityScores
  maturity_explanation?: string
  caps_applied?: CapApplied[]
  risk_heatmap?: unknown[]
}

const AssessmentResults = () => {
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [assessmentId, setAssessmentId] = useState('')
  const [payload, setPayload] = useState<ResultsPayload | null>(null)
  const [status, setStatus] = useState('Loading results...')
  const [showExpanded, setShowExpanded] = useState(false)
  const [showOverlay, setShowOverlay] = useState(false)
  const [radarExpanded, setRadarExpanded] = useState(false)
  const [theme, setTheme] = useState(document.documentElement.getAttribute('data-theme') || 'dark')
  const [benchmarkFilters, setBenchmarkFilters] = useState(() => ({
    sector: localStorage.getItem('benchmark_filter_sector') || 'all',
    size: localStorage.getItem('benchmark_filter_size') || 'all',
    region: localStorage.getItem('benchmark_filter_region') || 'all',
  }))
  const radarCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const radarChartRef = useRef<Chart | null>(null)

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    if (!assessmentId) {
      setStatus('No assessment selected.')
      return
    }
    setStatus('Loading results...')
    apiFetchRoot(`/responses/analysis/${assessmentId}`)
      .then(async (res) => {
        if (!res.ok) {
          const detail = await readApiError(res)
          throw new Error(describeAssessmentError(detail, 'Results unavailable.'))
        }
        return res.json()
      })
      .then((data) => {
        if (!data) throw new Error('No data')
        setPayload(data)
        setStatus('')
      })
      .catch((err) => {
        setStatus(err instanceof Error ? err.message : 'Results unavailable. Check API status.')
      })
  }, [assessmentId])

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setTheme(document.documentElement.getAttribute('data-theme') || 'dark')
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    localStorage.setItem('benchmark_filter_sector', benchmarkFilters.sector)
    localStorage.setItem('benchmark_filter_size', benchmarkFilters.size)
    localStorage.setItem('benchmark_filter_region', benchmarkFilters.region)
  }, [benchmarkFilters])

  const axes = payload?.axes || []
  const expandedAxes = payload?.expanded_axes || []
  const summary = payload?.summary || {}
  const recommendations = payload?.recommendations || []
  const rationale = payload?.archetype_details?.rationale || []
  const strengthPockets = axes.filter((axis) => (axis.score ?? 0) >= 75).slice(0, 4)
  const maturityScores = payload?.maturity_scores
  const gapVector = payload?.gap_vector || []
  const capsApplied = payload?.caps_applied || []
  const axesToShow = showExpanded && expandedAxes.length ? expandedAxes : axes
  const benchmarkRows = useMemo(() => {
    if (!axes.length) return []
    const base =
      2.4 +
      (benchmarkFilters.sector === 'financial' ? 0.2 : 0) +
      (benchmarkFilters.size === 'enterprise' ? 0.15 : 0) +
      (benchmarkFilters.region === 'eu' ? 0.1 : 0)
    return axes.map((axis) => {
      const client = Number(axis.score || 0)
      const benchmark = Math.min(100, Math.max(0, (base / 4) * 100 + (client % 7)))
      const delta = Math.round((client - benchmark) * 10) / 10
      return {
        axis: axis.axis || axis.code || 'Axis',
        client: Math.round(client * 10) / 10,
        benchmark: Math.round(benchmark * 10) / 10,
        delta,
      }
    })
  }, [axes, benchmarkFilters])

  useEffect(() => {
    if (!payload?.axes?.length || !radarCanvasRef.current) return
    const labels = payload.axes.map((axis) => axis.axis || axis.code || 'Axis')
    const declaredValues = (payload.declared_vector || []).map((axis) => axis.score ?? 0)
    const verifiedValues = (payload.verified_vector || []).map((axis) => axis.score ?? 0)
    const axisValues = payload.axes.map((axis) => axis.score ?? 0)
    const isLight = theme === 'light'
    const gridColor = isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)'
    const pointLabelColor = isLight ? '#666' : '#b0c4de'
    const datasets = [
      {
        label: 'Declared',
        data: declaredValues.length ? declaredValues : axisValues,
        backgroundColor: 'rgba(232, 179, 115, 0.15)',
        borderColor: '#e8b373',
        pointBackgroundColor: '#011E3D',
        borderWidth: 2,
      },
      {
        label: 'Verified',
        data: verifiedValues.length ? verifiedValues : axisValues,
        backgroundColor: 'rgba(91, 192, 222, 0.15)',
        borderColor: '#5bc0de',
        pointBackgroundColor: '#5bc0de',
        borderWidth: 2,
      },
    ]
    if (showOverlay && payload.expanded_axes?.length) {
      datasets.push({
        label: 'Expanded (override)',
        data: payload.expanded_axes.map((axis) => axis.score ?? 0),
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderColor: '#10b981',
        pointBackgroundColor: '#10b981',
        borderWidth: 2,
      })
    }
    if (radarChartRef.current) {
      radarChartRef.current.destroy()
    }
    radarChartRef.current = new Chart(radarCanvasRef.current, {
      type: 'radar',
      data: { labels, datasets },
      options: {
        maintainAspectRatio: false,
        scales: {
          r: {
            min: 0,
            max: 100,
            ticks: { display: false, backdropColor: 'transparent' },
            grid: { color: gridColor },
            pointLabels: {
              font: { size: 12, family: "'Montserrat', sans-serif" },
              color: pointLabelColor,
            },
          },
        },
      },
    })
    return () => {
      if (radarChartRef.current) {
        radarChartRef.current.destroy()
        radarChartRef.current = null
      }
    }
  }, [payload, showOverlay, theme])

  const handleExport = (type: 'csv' | 'json') => {
    if (!assessmentId) return
    window.open(`${API_BASE}/assessment/${assessmentId}/export/${type}`, '_blank')
  }

  return (
    <section className="ar-page">
      <div className="ar-header">
        <div>
          <h1>Results Dashboard</h1>
          <p className="ar-subtitle">
            Assessment ID: <strong>{assessmentId || 'Not set'}</strong>
          </p>
        </div>
        <div className="ar-header-actions">
          <button className="ar-btn ar-btn-outline" onClick={() => handleExport('csv')}>
            📥 Report (.csv)
          </button>
          <button className="ar-btn ar-btn-muted" onClick={() => handleExport('json')}>
            💾 Backup (.json)
          </button>
        </div>
      </div>

      {status ? <div className="ar-card">{status}</div> : null}

      {!status && (
        <>
          <section className="ar-grid">
            <div className="ar-card">
              <div className="ar-card-title">Archetype</div>
              <div className="ar-metric">{payload?.archetype || '—'}</div>
            </div>
            <div className="ar-card">
              <div className="ar-card-title">Trust Index</div>
              <div className="ar-metric">{summary.trust_index ?? '—'}</div>
            </div>
            <div className="ar-card">
              <div className="ar-card-title">Friction Score</div>
              <div className="ar-metric">{summary.friction_score ?? '—'}</div>
            </div>
            <div className="ar-card">
              <div className="ar-card-title">Evidence Confidence</div>
              <div className="ar-metric">{summary.evidence_confidence_avg ?? '—'}</div>
            </div>
          </section>

          <section className="ar-panel-grid">
            <div className="ar-card">
              <div className="ar-card-title">Archetype Rationale</div>
              {rationale.length ? (
                <div className="ar-list">
                  {rationale.map((line) => (
                    <div key={line} className="ar-list-item">
                      {line}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="ar-muted">No rationale available.</div>
              )}
            </div>
            <div className="ar-card">
              <div className="ar-card-title">Top Actions</div>
              {recommendations.length ? (
                <div className="ar-list">
                  {recommendations.map((rec) => (
                    <div key={rec.title} className="ar-list-item ar-accent">
                      <div className="ar-list-title">{rec.title}</div>
                      <div className="ar-list-sub">{rec.rationale || 'Action pending.'}</div>
                      <div className="ar-list-meta">
                        {rec.priority ? `Priority: ${rec.priority}` : 'Priority: —'}
                        {rec.timeline ? ` · ${rec.timeline}` : ''}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="ar-muted">Program actions pending.</div>
              )}
            </div>
          </section>

          <section className="ar-card ar-section">
            <div className="ar-card-title">Strength Pockets</div>
            {strengthPockets.length ? (
              <div className="ar-list">
                {strengthPockets.map((axis) => (
                  <div key={axis.code || axis.axis} className="ar-list-item ar-success">
                    <div className="ar-list-title">{axis.axis || axis.code}</div>
                    <div className="ar-list-sub">Strong maturity detected. Consider scaling.</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="ar-muted">No strength pockets detected yet.</div>
            )}
          </section>

          <section className="ar-card ar-section">
            <div className="ar-card-title">Maturity Scores</div>
            {payload?.maturity_explanation ? (
              <div className="ar-muted">{payload.maturity_explanation}</div>
            ) : null}
            <div className="ar-maturity-grid">
              <div className="ar-maturity-card">
                <div className="ar-maturity-label">Baseline (adaptive only)</div>
                <div className="ar-maturity-value">{maturityScores?.baseline?.trust_index ?? '—'}</div>
                <div className="ar-maturity-sub">
                  Friction {maturityScores?.baseline?.friction_score ?? '—'}
                </div>
              </div>
              <div className="ar-maturity-card">
                <div className="ar-maturity-label">Expanded (incl. overrides)</div>
                <div className="ar-maturity-value">{maturityScores?.expanded?.trust_index ?? '—'}</div>
                <div className="ar-maturity-sub">
                  Friction {maturityScores?.expanded?.friction_score ?? '—'}
                </div>
              </div>
            </div>
          </section>

          <section className="ar-radar-grid">
            <div className={`ar-card ar-radar-card ${radarExpanded ? 'expanded' : ''}`}>
              <div className="ar-card-header">
                <div>
                  <div className="ar-card-title">Maturity Radar</div>
                  <div className="ar-muted">Declared vs verified profiles.</div>
                </div>
                <div className="ar-radar-controls">
                  <label className="ar-toggle">
                    <input
                      type="checkbox"
                      checked={showOverlay}
                      onChange={(event) => setShowOverlay(event.target.checked)}
                    />
                    Show expanded overlay
                  </label>
                  <button className="ar-btn ar-btn-muted" onClick={() => setRadarExpanded((prev) => !prev)}>
                    {radarExpanded ? 'Collapse' : 'Expand'}
                  </button>
                </div>
              </div>
              <div className="ar-radar-canvas">
                <canvas ref={radarCanvasRef} />
              </div>
              <div className={`ar-radar-explainer ${radarExpanded ? 'visible' : ''}`}>
                Baseline = adaptive path. Expanded overlay = baseline + override answers.
              </div>
            </div>

            <div className="ar-axis-details">
              {axes.length ? (
                axes.map((axis) => (
                  <div key={axis.code || axis.axis} className="ar-axis-card">
                    <div className="ar-axis-header">
                      <strong>{axis.axis || axis.code}</strong>
                      <span>{axis.score ?? 0}%</span>
                    </div>
                    <div className="ar-axis-bar">
                      <div
                        className="ar-axis-fill"
                        style={{ width: `${Math.min(100, Math.max(0, axis.score ?? 0))}%` }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <div className="ar-card ar-muted">Insufficient data.</div>
              )}
            </div>
          </section>

          <section className="ar-section">
            <div className="ar-section-title">Axis Scores</div>
            {expandedAxes.length ? (
              <label className="ar-toggle">
                <input
                  type="checkbox"
                  checked={showExpanded}
                  onChange={(event) => setShowExpanded(event.target.checked)}
                />
                Show expanded overlay
              </label>
            ) : null}
            <div className="ar-table">
              <div className="ar-row ar-header-row">
                <span>Axis</span>
                <span>Score</span>
              </div>
              {axesToShow.length ? (
                axesToShow.map((axis) => (
                  <div key={axis.code || axis.axis} className="ar-row">
                    <span>{axis.axis || axis.code}</span>
                    <span>{axis.score ?? 0}</span>
                  </div>
                ))
              ) : (
                <div className="ar-row">
                  <span>No axis data.</span>
                  <span>—</span>
                </div>
              )}
            </div>
          </section>

          <section className="ar-card ar-section">
            <div className="ar-card-title">Benchmarking</div>
            <div className="ar-muted">Per-axis comparison placeholders.</div>
            <div className="ar-benchmark-filters">
              <select
                value={benchmarkFilters.sector}
                onChange={(event) => setBenchmarkFilters({ ...benchmarkFilters, sector: event.target.value })}
              >
                <option value="all">Sector: All</option>
                <option value="technology">Sector: Technology</option>
                <option value="healthcare">Sector: Healthcare</option>
                <option value="financial">Sector: Financial Services</option>
                <option value="manufacturing">Sector: Manufacturing</option>
              </select>
              <select
                value={benchmarkFilters.size}
                onChange={(event) => setBenchmarkFilters({ ...benchmarkFilters, size: event.target.value })}
              >
                <option value="all">Size: All</option>
                <option value="sme">SME (&lt;250)</option>
                <option value="mid">Mid-Market (250-4999)</option>
                <option value="enterprise">Enterprise (5000+)</option>
              </select>
              <select
                value={benchmarkFilters.region}
                onChange={(event) => setBenchmarkFilters({ ...benchmarkFilters, region: event.target.value })}
              >
                <option value="all">Region: All</option>
                <option value="eu">EU</option>
                <option value="na">North America</option>
                <option value="apac">APAC</option>
              </select>
            </div>
            <div className="ar-benchmark-table">
              {benchmarkRows.length ? (
                <table>
                  <thead>
                    <tr>
                      <th>Axis</th>
                      <th>Client</th>
                      <th>Benchmark</th>
                      <th>Δ</th>
                    </tr>
                  </thead>
                  <tbody>
                    {benchmarkRows.map((row) => (
                      <tr key={row.axis}>
                        <td>{row.axis}</td>
                        <td>{row.client}</td>
                        <td>{row.benchmark}</td>
                        <td>{row.delta}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="ar-muted">No benchmark data available yet.</div>
              )}
            </div>
          </section>

          <section className="ar-panel-grid">
            <div className="ar-card">
              <div className="ar-card-title">Declared vs Verified</div>
              {gapVector.length ? (
                <div className="ar-list">
                  {gapVector.map((axis) => (
                    <div key={axis.code || axis.axis} className="ar-list-item">
                      <div className="ar-list-title">{axis.axis || axis.code}</div>
                      <div className="ar-list-sub">Gap: {axis.score ?? 0}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="ar-muted">No gap data available.</div>
              )}
            </div>
            <div className="ar-card">
              <div className="ar-card-title">Circuit Breakers</div>
              {capsApplied.length ? (
                <div className="ar-list">
                  {capsApplied.map((cap, idx) => (
                    <div key={`${cap.type}-${idx}`} className="ar-list-item">
                      <div className="ar-list-title">
                        {cap.type || 'Cap'} · {cap.axis || '—'}
                      </div>
                      <div className="ar-list-sub">
                        Capped to {cap.cap_to ?? '—'} · {cap.reason || 'No reason provided.'}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="ar-muted">No caps applied.</div>
              )}
            </div>
          </section>
        </>
      )}
    </section>
  )
}

export default AssessmentResults
