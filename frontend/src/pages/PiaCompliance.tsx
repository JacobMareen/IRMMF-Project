import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import './PiaCompliance.css'

type PiaKeyDate = {
  date: string
  requirement: string
}

type PiaBullet = {
  title: string
  detail: string
  tags?: string[] | null
}

type PiaSection = {
  key: string
  title: string
  summary: string
  bullets: PiaBullet[]
}

type PiaRoadmapPhase = {
  phase: string
  focus: string
  deliverables: string[]
}

type PiaOverview = {
  module_key: string
  title: string
  subtitle: string
  executive_summary: string
  key_dates: PiaKeyDate[]
  sections: PiaSection[]
  roadmap: PiaRoadmapPhase[]
}

type PiaWorkflowStep = {
  key: string
  title: string
  description: string
}

const PiaCompliance = () => {
  const navigate = useNavigate()
  const [overview, setOverview] = useState<PiaOverview | null>(null)
  const [workflow, setWorkflow] = useState<PiaWorkflowStep[]>([])
  const [status, setStatus] = useState('Loading compliance overview...')

  useEffect(() => {
    apiFetch(`/pia/overview`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data: PiaOverview | null) => {
        if (!data) throw new Error('No data')
        setOverview(data)
        setStatus('')
      })
      .catch(() => {
        setStatus('Unable to load compliance overview. Start the API to view module data.')
      })
  }, [])

  useEffect(() => {
    apiFetch(`/pia/workflow`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: PiaWorkflowStep[]) => {
        setWorkflow(data || [])
      })
      .catch(() => {
        setWorkflow([])
      })
  }, [])

  const hasWorkflow = workflow.length > 0

  return (
    <section className="pia-page">
      <div className="pia-hero">
        <div className="pia-card">
          <div className="pia-tag">PIA 2024</div>
          <h1>{overview?.title || 'Procedural Compliance Platform'}</h1>
          <p className="pia-subtitle">
            {overview?.subtitle || 'Investigation support for Belgian Private Investigations Act compliance.'}
          </p>
          <p className="pia-summary">{overview?.executive_summary || status}</p>
          <div className="pia-hero-actions">
            <button className="pia-btn outline" onClick={() => navigate('/case-management/cases')}>
              Investigation Cases
            </button>
          </div>
        </div>
        <div className="pia-card">
          <div className="pia-title">Key Dates</div>
          {overview?.key_dates?.length ? (
            <ul className="pia-date-list">
              {overview.key_dates.map((item) => (
                <li key={item.date}>
                  <strong>{item.date}</strong>
                  <span>{item.requirement}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="pia-muted">{status || 'No dates available.'}</div>
          )}
        </div>
      </div>

      <section className="pia-case-hub">
        <div className="pia-section-title">Case Management</div>
        <div className="pia-card">
          <p className="pia-summary">
            Cases are managed in the Case Management → Cases workspace. This compliance view focuses on policy,
            workflow guidance, and jurisdictional guardrails.
          </p>
          <div className="pia-hero-actions">
            <button className="pia-btn" onClick={() => navigate('/case-management/cases')}>
              Go to Cases
            </button>
            <button className="pia-btn outline" onClick={() => navigate('/case-management/notifications')}>
              View Notifications
            </button>
          </div>
        </div>
      </section>

      <section className="pia-workflow">
        <div className="pia-section-title">Compliance Workflow</div>
        {hasWorkflow ? (
          <div className="pia-workflow-grid">
            {workflow.map((step) => (
              <article key={step.key} className="pia-workflow-card">
                <div className="pia-workflow-title">{step.title}</div>
                <p className="pia-muted">{step.description}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="pia-muted">No workflow steps loaded.</div>
        )}
      </section>

      <section className="pia-sections">
        <div className="pia-section-title">Module Blueprint</div>
        {overview?.sections?.length ? (
          <div className="pia-section-grid">
            {overview.sections.map((section) => (
              <article key={section.key} className="pia-section-card">
                <div className="pia-section-header">
                  <h3>{section.title}</h3>
                  <p>{section.summary}</p>
                </div>
                <div className="pia-bullets">
                  {section.bullets.map((bullet) => (
                    <div key={`${section.key}-${bullet.title}`} className="pia-bullet">
                      <div className="pia-bullet-title">{bullet.title}</div>
                      <div className="pia-bullet-detail">{bullet.detail}</div>
                      {bullet.tags?.length ? (
                        <div className="pia-bullet-tags">
                          {bullet.tags.map((tag) => (
                            <span key={`${section.key}-${bullet.title}-${tag}`} className="pia-tag-pill">
                              {tag}
                            </span>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="pia-muted">No module sections loaded.</div>
        )}
      </section>

      <section className="pia-roadmap">
        <div className="pia-section-title">Delivery Roadmap</div>
        {overview?.roadmap?.length ? (
          <div className="pia-roadmap-grid">
            {overview.roadmap.map((phase) => (
              <article key={phase.phase} className="pia-roadmap-card">
                <div className="pia-roadmap-phase">{phase.phase}</div>
                <div className="pia-roadmap-focus">{phase.focus}</div>
                <ul>
                  {phase.deliverables.map((item) => (
                    <li key={`${phase.phase}-${item}`}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        ) : (
          <div className="pia-muted">No roadmap data loaded.</div>
        )}
      </section>
    </section>
  )
}

export default PiaCompliance
