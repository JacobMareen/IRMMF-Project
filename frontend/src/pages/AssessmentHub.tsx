import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './AssessmentHub.css'
import { clearStoredAssessmentId, getStoredAssessmentId, storeAssessmentId } from '../utils/assessment'
import { apiFetch } from '../lib/api'




import { useAssessmentData } from '../hooks/useAssessmentData'
import { AssessmentNav } from '../components/AssessmentNav'
import { TargetMaturityModal } from '../components/TargetMaturityModal'
import { useToast } from '../context/ToastContext'
import FrameworkRadar from '../components/visuals/FrameworkRadar'
import DomainDetailOverlay from '../components/visuals/DomainDetailOverlay'
import { FrameworkGuide } from '../components/FrameworkGuide'
import { PageHeader } from '../components/PageHeader'

const AssessmentHub = () => {
  const { showToast } = useToast()
  const [assessmentId, setAssessmentId] = useState<string>('')
  const [roleLens, setRoleLens] = useState<string>('overall')
  const [overrideDomains, setOverrideDomains] = useState<Set<string>>(new Set())
  const [domains, setDomains] = useState<string[]>([])
  const [allQuestions, setAllQuestions] = useState<Array<{ q_id: string; domain: string }>>([])

  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const navigate = useNavigate()

  const handleReset = () => {
    clearStoredAssessmentId(assessmentId, currentUser)
    setAssessmentId('')
    showToast('Assessment reset initiated.', 'info')
  }

  const {
    completionPct,
    intakeAnswered,
    intakeTotal,
    topRisk,
    heatmapCount,
    resumeState,
    statusNote,
    setStatusNote,
    target_maturity
  } = useAssessmentData(assessmentId, currentUser, handleReset)

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    if (!currentUser || assessmentId) return
    const controller = new AbortController()
    const resolveAssessment = async () => {
      try {
        const latestResp = await apiFetch(`/assessment/user/${currentUser}/latest`, {
          signal: controller.signal,
        })
        if (latestResp.ok) {
          const latest = (await latestResp.json()) as { assessment_id?: string }
          if (latest.assessment_id) {
            setAssessmentId(latest.assessment_id)
            storeAssessmentId(latest.assessment_id, currentUser)
            return
          }
        }
        if (latestResp.status !== 404) return
        const createResp = await apiFetch(`/assessment/new`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: currentUser || null }),
          signal: controller.signal,
        })
        if (!createResp.ok) throw new Error('Create failed')
        const created = (await createResp.json()) as { assessment_id?: string }
        const id = created.assessment_id || ''
        if (id) {
          setAssessmentId(id)
          storeAssessmentId(id, currentUser)
        }
      } catch {
        // Handled by hook mostly, but this is init logic
      }
    }
    resolveAssessment()
    return () => controller.abort()
  }, [currentUser, assessmentId])

  useEffect(() => {
    if (!assessmentId) return
    apiFetch(`/questions/all?assessment_id=${assessmentId}`)
      .then((res) => {
        if (res.status === 404) {
          handleReset()
          return []
        }
        return res.ok ? res.json() : []
      })
      .then((data) => {
        const questions = (data || []) as Array<{ q_id: string; domain?: string }>
        setAllQuestions(questions.filter((q) => q.q_id && q.domain) as Array<{ q_id: string; domain: string }>)
        const unique = Array.from(new Set(questions.map((q) => q.domain).filter(Boolean))) as string[]
        setDomains(unique.sort())
      })
      .catch(() => setDomains([]))
  }, [assessmentId])

  useEffect(() => {
    if (!assessmentId) return
    const storedRole = localStorage.getItem(`role_lens_${assessmentId}`) || 'overall'
    setRoleLens(storedRole)
    const raw = localStorage.getItem(`override_domains_${assessmentId}`)
    if (raw) {
      try {
        const list = JSON.parse(raw)
        if (Array.isArray(list)) {
          setOverrideDomains(new Set(list))
        }
      } catch {
        setOverrideDomains(new Set())
      }
    } else {
      setOverrideDomains(new Set())
    }
  }, [assessmentId])

  const [activeDomain, setActiveDomain] = useState<any | null>(null)

  const domainCards = (() => {
    if (!allQuestions.length || !resumeState?.reachable_path) return []
    const responses = resumeState.responses || {}
    const deferred = new Set(resumeState.deferred_ids || [])
    const reachable = resumeState.reachable_path || []
    return domains.map((domain) => {
      const domainQs = allQuestions.filter((q) => q.domain === domain)
      const answeredCount = domainQs.filter((q) => responses[q.q_id] && !deferred.has(q.q_id)).length
      const reachableInDomain = reachable.filter((qid) => domainQs.find((dq) => dq.q_id === qid))
      const remaining = Math.max(domainQs.length - answeredCount, 0)
      let status = 'not_started'
      if (answeredCount > 0 && answeredCount < domainQs.length) status = 'ongoing'
      if (answeredCount >= domainQs.length && domainQs.length > 0) status = 'completed'
      return {
        domain,
        status,
        remaining,
        answered: answeredCount,
        total: domainQs.length,
        reachable: reachableInDomain,
      }
    })
  })()

  const handleStartDomain = (domain: string, reachable: string[]) => {
    if (!assessmentId) return
    if (reachable.length === 0) return
    localStorage.setItem('flow_start_domain', domain)
    navigate('/assessment/flow')
  }

  const [status, setStatus] = useState<string>('idle')
  const [showTargetModal, setShowTargetModal] = useState(false)

  // Handlers
  const handleStartDomainByName = (domainName: string) => {
    const card = domainCards.find(d => d.domain === domainName)
    if (card) {
      handleStartDomain(card.domain, card.reachable)
    }
  }

  const handleTargetSave = async (targets: Record<string, number>) => {
    if (!assessmentId) return
    try {
      await apiFetch(`/assessment/${assessmentId}/target-maturity`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_maturity: targets }),
      })
      showToast('Targets updated.', 'success')
      // Optimistically update or re-fetch could happen here
    } catch {
      showToast('Failed to update targets.', 'error')
    }
  }

  const persistOverrideDomains = (next: Set<string>) => {
    if (!assessmentId) return
    localStorage.setItem(`override_domains_${assessmentId}`, JSON.stringify([...next]))
  }

  const syncOverrideDepth = async (enabled: boolean) => {
    if (!assessmentId) return
    try {
      await apiFetch(`/assessment/${assessmentId}/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ override_depth: enabled }),
      })
      showToast(`Deep dive questions ${enabled ? 'enabled' : 'disabled'}.`, 'success')
    } catch {
      setStatusNote('Unable to update override depth. Check API status.')
      showToast('Failed to update override settings.', 'error')
    }
  }

  const toggleDomainOverride = (domain: string, enabled: boolean) => {
    const next = new Set(overrideDomains)
    if (enabled) next.add(domain)
    else next.delete(domain)
    setOverrideDomains(next)
    persistOverrideDomains(next)
    syncOverrideDepth(next.size > 0)
  }

  const handleRoleLensChange = (value: string) => {
    setRoleLens(value)
    if (assessmentId) {
      localStorage.setItem(`role_lens_${assessmentId}`, value)
    }
  }



  return (
    <section className="ah-page">
      <PageHeader
        title="Assessment Hub"
        subtitle="Assessment status, intake flow, and risk insights."
        statusNote={statusNote}
        actions={<FrameworkGuide />}
      />


      <AssessmentNav assessmentId={assessmentId} />

      {/* Rapid Benchmark Hero (Triage Mode) */}
      {intakeAnswered != null && intakeTotal != null && intakeAnswered < intakeTotal ? (
        <section className="ah-section">
          <div className="ah-hero-card">
            <div className="ah-hero-content">
              <h2>Step 1: Rapid Benchmark</h2>
              <p>Complete the {intakeTotal}-question triage to establish your preliminary risk profile and unlock the full framework.</p>
              <div className="ah-progress-storage">
                <div className="ah-progress-bar">
                  <div
                    className="ah-progress-fill"
                    style={{ width: `${(intakeAnswered / intakeTotal) * 100}%` }}
                  />
                </div>
                <span className="ah-progress-text">{intakeAnswered} / {intakeTotal} Answered</span>
              </div>
              <button
                className="ah-btn primary large"
                onClick={() => navigate('/assessment/intake')}
              >
                {intakeAnswered === 0 ? 'Start Rapid Benchmark' : 'Continue Triage'}
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {/* Framework Radar Section */}
      {assessmentId && domainCards.length > 0 && (intakeAnswered === intakeTotal) ? (
        <section className="ah-section">
          <div className="ah-section-title">Framework Coverage (Full Assessment)</div>
          <div style={{ display: 'flex', justifyContent: 'center', margin: '2rem 0' }}>
            <FrameworkRadar
              domains={domainCards}
              onDomainClick={setActiveDomain}
            />
          </div>

          <DomainDetailOverlay
            domainData={activeDomain}
            onClose={() => setActiveDomain(null)}
            onOpen={handleStartDomainByName}
            overrideEnabled={activeDomain ? overrideDomains.has(activeDomain.domain) : false}
            onToggleOverride={(enabled) => activeDomain && toggleDomainOverride(activeDomain.domain, enabled)}
          />
        </section>
      ) : null}

      {/* Standard Grid (Hidden during Triage for focus) */}
      {intakeAnswered === intakeTotal && (<>
        <section className="ah-grid">
          <div className="ah-card">
            <div className="ah-card-title">Assessment Status</div>
            <p>Resume where you left off or create a new assessment.</p>
            <div className="ah-status-row">
              <span>Current assessment</span>
              <strong>Active</strong>
            </div>
            <div className="ah-status-row">
              <span>Progress</span>
              <strong>{completionPct != null ? `${completionPct}%` : '--%'}</strong>
            </div>
            <div className="ah-actions" style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
              <button className="ah-btn secondary" onClick={() => setShowTargetModal(true)}>
                Set Targets
              </button>
            </div>
          </div>

          <div className="ah-card">
            <div className="ah-card-title">Rapid Benchmark</div>
            <p>Initial triage complete.</p>
            <div className="ah-status-row">
              <span>Status</span>
              <strong><span style={{ color: 'var(--success)' }}>✓ Complete</span></strong>
            </div>
            <div className="ah-status-row">
              <span>Next Step</span>
              <strong>Deep Dive</strong>
            </div>
          </div>

          <div className="ah-card">
            <div className="ah-card-title">Risk Snapshot</div>
            <p>Top risks and heatmap from the latest analysis run.</p>
            <div className="ah-status-row">
              <span>Top risk</span>
              <strong>{topRisk}</strong>
            </div>
            <div className="ah-status-row">
              <span>Heatmap coverage</span>
              <strong>{heatmapCount != null ? heatmapCount : '--'}</strong>
            </div>
          </div>
        </section>



        <section className="ah-section">
          <div className="ah-section-title">Results & Review</div>
          <div className="ah-review-grid">
            <div className="ah-card">
              <div className="ah-card-title">Results Dashboard</div>
              <p>Archetype, axis scores, and benchmarking will render here.</p>
              <button className="ah-btn secondary" onClick={() => navigate('/assessment/results')} disabled={!assessmentId}>
                Open Results
              </button>
            </div>
            <div className="ah-card">
              <div className="ah-card-title">Review Queue</div>
              <p>Flagged and deferred questions will be listed in this panel.</p>
              <button className="ah-btn secondary" onClick={() => navigate('/assessment/review')} disabled={!assessmentId}>
                Open Review
              </button>
            </div>
          </div>
        </section>
      </>)}

      {
        assessmentId ? (
          <section className="ah-controls ah-controls-bottom">
            <div className="ah-card">
              <div className="ah-card-title">Role Lens (view-only)</div>
              <p>Filters will map to role tags once metadata is available.</p>
              <select
                className="ah-select"
                value={roleLens}
                onChange={(event) => handleRoleLensChange(event.target.value)}
              >
                <option value="overall">Overall</option>
                <option value="ciso">CISO</option>
                <option value="ia">Internal Audit</option>
                <option value="hr">HR</option>
              </select>
            </div>
          </section>
        ) : null
      }
      {showTargetModal && (
        <TargetMaturityModal
          currentTargets={target_maturity || {}}
          onSave={handleTargetSave}
          onClose={() => setShowTargetModal(false)}
        />
      )}
    </section>
  )
}

export default AssessmentHub
