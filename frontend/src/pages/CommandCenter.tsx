import { useEffect, useState } from 'react'
import { apiJson } from '../lib/api'
import './CommandCenter.css'
import { CaseStatusChart } from '../components/charts/CaseStatusChart'
import { GateThroughputChart } from '../components/charts/GateThroughputChart'

type ModuleEntry = {
  label: string
  description: string
}

type DashboardData = {
  total_cases: number
  status_counts: Record<string, number>
  stage_counts: Record<string, number>
  serious_cause_enabled: number
  avg_days_open: number
  avg_days_in_stage: number
  gate_completion: Record<string, { completed: number; total_cases: number; rate: number }>
  recent_case_count: number
  recent_window_days: number
  alert_threshold_cases: number
  alerts: { alert_key: string; severity: string; message: string; created_at: string }[]
  serious_cause_cases: {
    case_id: string
    title: string
    decision_due_at?: string | null
    dismissal_due_at?: string | null
    facts_confirmed_at?: string | null
  }[]
}

const CommandCenter = () => {
  const [registryText, setRegistryText] = useState('Loading module metadata...')
  const [moduleCount, setModuleCount] = useState('4 active')
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)

  useEffect(() => {
    apiJson<Record<string, ModuleEntry>>('/modules')
      .then((data) => {
        const entries = Object.values(data || {}) as ModuleEntry[]
        setRegistryText(entries.map((m) => `${m.label}: ${m.description}`).join(' • '))
        setModuleCount(`${entries.length} active`)
      })
      .catch(() => {
        setRegistryText('Registry unavailable (API offline).')
      })

    apiJson<DashboardData>('/dashboard')
      .then((data) => {
        setDashboard(data)

      })
      .catch(() => {
        console.error('Dashboard unavailable')
      })
  }, [])

  const alerts = dashboard?.alerts ?? []
  const seriousCauseCases = dashboard?.serious_cause_cases ?? []

  const formatCountdown = (iso?: string | null) => {
    if (!iso) return '--'
    const diffMs = new Date(iso).getTime() - Date.now()
    const hours = Math.ceil(diffMs / 36e5)
    if (hours <= 0) return 'Overdue'
    if (hours < 24) return `${hours}h`
    const days = Math.ceil(hours / 24)
    return `${days}d`
  }

  return (
    <section className="cc-page">
      <div className="cc-hero">
        <div className="cc-card">
          <h2>Welcome</h2>
          <p>
            Launch assessments, explore specialist modules, and gather
            executive-level signals. This page will evolve into a live dashboard
            as we add reporting and benchmarks.
          </p>
          <div className="cc-meta-grid">
            <div className="cc-meta-tile">
              <strong>Modules</strong>
              <span>{moduleCount}</span>
            </div>
            <div className="cc-meta-tile">
              <strong>Latest update</strong>
              <span>Model v6.1</span>
            </div>
            <div className="cc-meta-tile">
              <strong>Status</strong>
              <span>Local dev</span>
            </div>
          </div>
        </div>
        <div className="cc-card">
          <h2>Case Operations</h2>
          <div className="cc-charts-row">
            <div className="cc-chart-container">
              <h3>Case Status</h3>
              {dashboard ? (
                <CaseStatusChart
                  open={dashboard.status_counts?.OPEN ?? 0}
                  onHold={dashboard.status_counts?.ON_HOLD ?? 0}
                  closed={dashboard.total_cases - (dashboard.status_counts?.OPEN ?? 0) - (dashboard.status_counts?.ON_HOLD ?? 0)}
                />
              ) : (
                <div className="cc-loading-chart">Loading...</div>
              )}
            </div>
            <div className="cc-chart-container">
              <h3>Gate Throughput</h3>
              {dashboard ? (
                <GateThroughputChart
                  legitimacy={dashboard.gate_completion?.legitimacy?.rate ?? 0}
                  credentialing={dashboard.gate_completion?.credentialing?.rate ?? 0}
                  adversarial={dashboard.gate_completion?.adversarial?.rate ?? 0}
                />
              ) : (
                <div className="cc-loading-chart">Loading...</div>
              )}
            </div>
          </div>

          <div className="cc-metrics-grid">
            <div className="cc-metric-tile">
              <span>Avg days open</span>
              <strong>{dashboard ? dashboard.avg_days_open : '--'}</strong>
            </div>
            <div className="cc-metric-tile">
              <span>In investigation</span>
              <strong>{dashboard ? dashboard.stage_counts?.INVESTIGATION ?? 0 : '--'}</strong>
            </div>
          </div>
        </div>
      </div>

      {alerts.length ? (
        <section className="cc-alerts">
          {alerts.map((alert) => (
            <div key={alert.alert_key} className={`cc-alert ${alert.severity}`}>
              <strong>Alert:</strong> {alert.message}
            </div>
          ))}
        </section>
      ) : null}

      <section className="cc-alerts-grid">
        <div className="cc-card">
          <h2>Serious Cause Countdown</h2>
          {seriousCauseCases.length === 0 ? (
            <p className="cc-muted">No active serious-cause clocks.</p>
          ) : (
            <div className="cc-list">
              {seriousCauseCases.map((item) => (
                <div key={item.case_id} className="cc-row">
                  <div>
                    <strong>{item.case_id}</strong>
                    <div className="cc-muted">{item.title}</div>
                  </div>
                  <div className="cc-countdown">
                    <span>Decision: {formatCountdown(item.decision_due_at)}</span>
                    <span>Dismissal: {formatCountdown(item.dismissal_due_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="cc-card">
          <h2>HR Exemption Drift</h2>
          <p className="cc-muted">
            Rolling {dashboard?.recent_window_days ?? 30} day case volume vs. threshold.
          </p>
          <div className="cc-row">
            <span>Cases opened (window)</span>
            <strong>{dashboard ? dashboard.recent_case_count : '--'}</strong>
          </div>
          <div className="cc-row">
            <span>Threshold</span>
            <strong>{dashboard ? dashboard.alert_threshold_cases : '--'}</strong>
          </div>
        </div>
      </section>

      <section className="cc-modules">
        <div className="cc-section-title">Modules</div>
        <div className="cc-module-grid">
          <div className="cc-module-card">
            <div className="cc-tag">Assessment</div>
            <h3>IRMMF Assessment</h3>
            <p>Adaptive maturity and resilience assessment with evidence confidence and risk outputs.</p>
            <div className="cc-actions">
              <a className="cc-btn primary" href="/assessment">
                Open Assessment Hub
              </a>
              <a className="cc-btn secondary" href="/assessment">
                Assessment Dashboard
              </a>
            </div>
          </div>

          <div className="cc-module-card">
            <div className="cc-tag">DWF</div>
            <h3>Dynamic Workforce</h3>
            <p>Workforce risk module focused on culture, role impact, and resilience signals.</p>
            <div className="cc-actions">
              <a className="cc-btn primary" href="/workforce">
                Open DWF
              </a>
              <a className="cc-btn secondary" href="/workforce">
                View Results
              </a>
            </div>
          </div>

          <div className="cc-module-card">
            <div className="cc-tag">Case Mgmt</div>
            <h3>Case Management</h3>
            <p>Compliance governance, investigation workflows, and case operations in one workspace.</p>
            <div className="cc-actions">
              <a className="cc-btn primary" href="/case-management/compliance">
                Compliance Overview
              </a>
              <a className="cc-btn secondary" href="/case-management/cases">
                Open Cases
              </a>
            </div>
          </div>

          <div className="cc-module-card">
            <div className="cc-tag">Investigations</div>
            <h3>Cases</h3>
            <p>Core case object, lifecycle status, evidence register, and task checklists.</p>
            <div className="cc-actions">
              <a className="cc-btn primary" href="/case-management/cases">
                View Case List
              </a>
              <a className="cc-btn secondary" href="/case-management/notifications">
                Notifications
              </a>
            </div>
          </div>

          <div className="cc-module-card">
            <div className="cc-tag">Settings</div>
            <h3>Platform Settings</h3>
            <p>Manage environment-wide configuration, branding, access, and integrations.</p>
            <div className="cc-actions">
              <a className="cc-btn primary" href="/settings">
                Open Settings
              </a>
            </div>
          </div>

          <div className="cc-module-card">
            <div className="cc-tag">Upcoming</div>
            <h3>Future Module</h3>
            <p>Reserved for new capabilities (vendor risk, regulatory readiness, executive reporting).</p>
            <div className="cc-actions">
              <a className="cc-btn secondary" href="/">
                Define Scope
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="cc-registry">
        <strong>Module Registry:</strong>
        <span>{registryText}</span>
      </section>

    </section>
  )
}

export default CommandCenter
