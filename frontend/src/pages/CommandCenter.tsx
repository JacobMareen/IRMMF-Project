import { useEffect, useState } from 'react'
import './CommandCenter.css'

type ModuleEntry = {
  label: string
  description: string
}

const CommandCenter = () => {
  const [registryText, setRegistryText] = useState('Loading module metadata...')
  const [moduleCount, setModuleCount] = useState('4 active')

  useEffect(() => {
    const apiBase =
      location.hostname === '127.0.0.1' || location.hostname === 'localhost'
        ? 'http://127.0.0.1:8000'
        : 'http://0.0.0.0:8000'

    fetch(`${apiBase}/api/v1/modules`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!data) throw new Error('No data')
        const entries = Object.values(data) as ModuleEntry[]
        setRegistryText(entries.map((m) => `${m.label}: ${m.description}`).join(' • '))
        setModuleCount(`${entries.length} active`)
      })
      .catch(() => {
        setRegistryText('Registry unavailable (API offline).')
      })
  }, [])

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
          <h2>Executive Snapshot</h2>
          <div className="cc-row">
            <span>Assessments in progress</span>
            <strong>--</strong>
          </div>
          <div className="cc-row">
            <span>Top risk category</span>
            <strong>--</strong>
          </div>
          <div className="cc-row">
            <span>Benchmark cohort</span>
            <strong>--</strong>
          </div>
        </div>
      </div>

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
