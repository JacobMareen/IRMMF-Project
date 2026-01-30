import { useEffect, useMemo, useState } from 'react'
import './InsiderRiskProgram.css'
import { getStoredAssessmentId } from '../utils/assessment'
import { apiFetch, apiJson } from '../lib/api'

type Recommendation = {
  rec_id: string
  assessment_id?: string
  title: string
  category: string
  priority: string
  status?: string
  description: string
  rationale?: string
  implementation_steps?: {
    steps: Array<{
      step: number
      action: string
      owner: string
    }>
  }
  effort?: string
  timeline?: string
  subcategory?: string
  assigned_to?: string
  due_date?: string
  custom_notes?: string
  triggered_by?: {
    axes?: string[]
    risks?: string[]
  }
}

type PolicySection = {
  title: string
  intent?: string
  bullets?: string[]
  owner?: string
  artifacts?: string[]
}

type InsiderRiskPolicy = {
  status: string
  version: string
  owner: string
  approval: string
  scope: string
  last_reviewed?: string
  next_review?: string
  principles: string[]
  sections: PolicySection[]
  is_template?: boolean
}

type ControlStatus = 'planned' | 'in_progress' | 'implemented' | 'monitored'

type Control = {
  control_id: string
  title?: string
  domain: string
  objective?: string
  status: ControlStatus
  owner?: string
  frequency?: string
  evidence?: string
  last_reviewed?: string
  next_review?: string
  linked_actions?: string[]
  linked_rec_ids?: string[]
  linked_categories?: string[]
}

const DEFAULT_POLICY: InsiderRiskPolicy = {
  status: 'Draft',
  version: 'v0.9',
  owner: 'IR Program Lead',
  approval: 'Pending GC + HR approval',
  scope: 'Employees, contractors, and trusted third parties with access to sensitive data or systems.',
  last_reviewed: '2026-01-15',
  next_review: '2026-04-15',
  principles: [
    'Lawful, fair, and transparent handling of insider risk signals.',
    'Least intrusive monitoring with strict access controls and audit trails.',
    'Clear escalation paths with legal, HR, and privacy oversight.',
    'Documented decision-making and proportional response.',
  ],
  sections: [
    {
      title: 'Governance & Accountability',
      intent: 'Define program ownership, decision rights, and reporting cadence.',
      bullets: [
        'IR Steering Group chaired by Legal/HR with Security and Privacy representation.',
        'Case approvals required for elevated monitoring or investigative steps.',
        'Quarterly program review with KPI reporting to leadership.',
      ],
      owner: 'Legal + HR',
      artifacts: ['RACI matrix', 'Approval workflow', 'Quarterly KPI pack'],
    },
    {
      title: 'Detection & Monitoring',
      intent: 'Establish what is monitored, how signals are reviewed, and how privacy is protected.',
      bullets: [
        'Signals limited to approved telemetry and contextualized with business need.',
        'Alert triage within 5 business days with documented rationale.',
        'Sensitive access requires justification and audit log retention.',
      ],
      owner: 'Security Operations',
      artifacts: ['Monitoring charter', 'Signal catalog', 'Triage checklist'],
    },
    {
      title: 'Investigation & Response',
      intent: 'Standardize case intake, evidence handling, and response actions.',
      bullets: [
        'Intake requires scope, jurisdiction, and legal basis.',
        'Evidence register maintained with chain-of-custody tracking.',
        'Escalations follow predefined decision gates and HR/legal review.',
      ],
      owner: 'Investigations Lead',
      artifacts: ['Case workflow', 'Evidence register', 'Decision log'],
    },
    {
      title: 'Privacy, Ethics, and Data Retention',
      intent: 'Protect employee rights and ensure proportionality and retention controls.',
      bullets: [
        'Data minimization applied to all case artifacts and exports.',
        'Retention periods enforced with erasure workflows and approvals.',
        'Ethics review required for high-impact monitoring changes.',
      ],
      owner: 'Privacy Office',
      artifacts: ['Retention schedule', 'Erasure certificate', 'Ethics checklist'],
    },
  ],
}

const CONTROL_DOMAINS = ['Governance', 'Prevention', 'Detection', 'Response', 'Recovery']

const DEFAULT_CONTROLS: Control[] = [
  {
    control_id: 'IR-CTRL-001',
    title: 'Insider Risk Policy Adoption',
    domain: 'Governance',
    objective: 'Ensure the policy is approved, communicated, and enforced.',
    status: 'in_progress',
    owner: 'Legal + HR',
    frequency: 'Annual review',
    evidence: 'Signed policy, awareness notice',
    last_reviewed: '2026-01-10',
    next_review: '2026-07-10',
    linked_actions: ['Finalize policy approval workflow', 'Publish employee notice'],
  },
  {
    control_id: 'IR-CTRL-002',
    title: 'Privileged Access Reviews',
    domain: 'Prevention',
    objective: 'Reduce unnecessary access to sensitive systems.',
    status: 'implemented',
    owner: 'IT Security',
    frequency: 'Quarterly',
    evidence: 'Access review logs, remediation tickets',
    last_reviewed: '2026-01-05',
    next_review: '2026-04-05',
    linked_actions: ['Quarterly access recertification', 'Privileged role clean-up'],
  },
  {
    control_id: 'IR-CTRL-003',
    title: 'Insider Signal Triage',
    domain: 'Detection',
    objective: 'Review and disposition alerts within defined SLAs.',
    status: 'planned',
    owner: 'Security Operations',
    frequency: 'Weekly',
    evidence: 'Triage queue exports, SLA report',
    last_reviewed: '2025-12-20',
    next_review: '2026-02-20',
    linked_actions: ['Define triage SLAs', 'Configure signal thresholds'],
  },
  {
    control_id: 'IR-CTRL-004',
    title: 'Case Intake & Gatekeeping',
    domain: 'Response',
    objective: 'Ensure cases meet legal and policy requirements before escalation.',
    status: 'monitored',
    owner: 'Investigations Lead',
    frequency: 'Per case',
    evidence: 'Gate approvals, case intake logs',
    last_reviewed: '2026-01-18',
    next_review: '2026-03-18',
    linked_actions: ['Standardize gate checklist', 'Improve intake templates'],
  },
  {
    control_id: 'IR-CTRL-005',
    title: 'Evidence Handling & Chain of Custody',
    domain: 'Response',
    objective: 'Maintain integrity of evidence through secure collection and logging.',
    status: 'implemented',
    owner: 'Investigations Lead',
    frequency: 'Per case',
    evidence: 'Evidence register snapshots, hash logs',
    last_reviewed: '2026-01-12',
    next_review: '2026-04-12',
    linked_actions: ['Enable evidence hashing', 'Train investigators on logging'],
  },
  {
    control_id: 'IR-CTRL-006',
    title: 'Program Training & Awareness',
    domain: 'Governance',
    objective: 'Ensure staff understand insider risk expectations and reporting paths.',
    status: 'in_progress',
    owner: 'HR + Compliance',
    frequency: 'Annual',
    evidence: 'Training completion report',
    last_reviewed: '2025-11-30',
    next_review: '2026-02-28',
    linked_actions: ['Refresh training modules', 'Launch awareness campaign'],
  },
  {
    control_id: 'IR-CTRL-007',
    title: 'Retention & Erasure Controls',
    domain: 'Recovery',
    objective: 'Apply retention limits and erasure workflows to case data.',
    status: 'planned',
    owner: 'Privacy Office',
    frequency: 'Quarterly',
    evidence: 'Erasure approvals, audit logs',
    last_reviewed: '2026-01-02',
    next_review: '2026-04-02',
    linked_actions: ['Configure retention schedules', 'Automate erasure reporting'],
  },
  {
    control_id: 'IR-CTRL-008',
    title: 'Post-Incident Lessons Learned',
    domain: 'Recovery',
    objective: 'Capture findings and feed improvements back into the program.',
    status: 'planned',
    owner: 'IR Program Lead',
    frequency: 'Per major case',
    evidence: 'Lessons learned register',
    last_reviewed: '2025-12-15',
    next_review: '2026-03-15',
    linked_actions: ['Create remediation tracking', 'Review policy updates'],
  },
]

const CONTROL_STATUS_OPTIONS: ControlStatus[] = ['planned', 'in_progress', 'implemented', 'monitored']

const InsiderRiskProgram = () => {
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [assessmentId, setAssessmentId] = useState<string>('')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [actionsLoading, setActionsLoading] = useState(true)
  const [policy, setPolicy] = useState<InsiderRiskPolicy>(DEFAULT_POLICY)
  const [policyLoading, setPolicyLoading] = useState(true)
  const [policySaving, setPolicySaving] = useState(false)
  const [policyTemplate, setPolicyTemplate] = useState(true)
  const [policyDraft, setPolicyDraft] = useState<InsiderRiskPolicy | null>(null)
  const [policyError, setPolicyError] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    assessment: '',
    priority: '',
    status: '',
    category: '',
  })
  const [categories, setCategories] = useState<string[]>([])
  const [modalRec, setModalRec] = useState<Recommendation | null>(null)
  const [modalFields, setModalFields] = useState({
    status: 'pending',
    priority: 'Medium',
    assigned_to: '',
    due_date: '',
    custom_notes: '',
  })
  const [controls, setControls] = useState<Control[]>(DEFAULT_CONTROLS)
  const [controlsLoading, setControlsLoading] = useState(true)
  const [controlsSeeded, setControlsSeeded] = useState(false)
  const [controlsError, setControlsError] = useState<string | null>(null)
  const [controlFilters, setControlFilters] = useState({ domain: '', status: '' })
  const [controlDraft, setControlDraft] = useState<Control | null>(null)
  const [controlMode, setControlMode] = useState<'create' | 'edit'>('edit')

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    loadLibraryCategories()
  }, [])

  useEffect(() => {
    loadPolicy()
    loadControls()
  }, [])

  useEffect(() => {
    loadRecommendations()
  }, [filters.assessment])

  const loadLibraryCategories = async () => {
    try {
      const data = await apiJson<Recommendation[]>('/recommendations/library')
      const unique = Array.from(new Set(data.map((rec) => rec.category).filter(Boolean)))
      setCategories(unique)
    } catch {
      setCategories([])
    }
  }

  const normalizePolicy = (incoming?: Partial<InsiderRiskPolicy>) => {
    const merged = { ...DEFAULT_POLICY, ...(incoming || {}) }
    merged.principles = Array.isArray(incoming?.principles) ? incoming!.principles : DEFAULT_POLICY.principles
    merged.sections = Array.isArray(incoming?.sections) ? incoming!.sections : DEFAULT_POLICY.sections
    return merged
  }

  const normalizeControl = (control: Control): Control => ({
    ...control,
    linked_actions: control.linked_actions ?? [],
    linked_rec_ids: control.linked_rec_ids ?? [],
    linked_categories: control.linked_categories ?? [],
  })

  const normalizeDate = (value?: string) => (value ? value : null)

  const loadPolicy = async () => {
    setPolicyLoading(true)
    setPolicyError(null)
    try {
      const data = await apiJson<InsiderRiskPolicy>('/insider-program/policy')
      setPolicy(normalizePolicy(data))
      setPolicyTemplate(Boolean(data.is_template))
    } catch {
      setPolicy(normalizePolicy())
      setPolicyTemplate(true)
      setPolicyError('Policy template loaded locally.')
    } finally {
      setPolicyLoading(false)
    }
  }

  const savePolicy = async (nextPolicy: InsiderRiskPolicy) => {
    setPolicySaving(true)
    setPolicyError(null)
    try {
      const { is_template: _isTemplate, ...policyBody } = nextPolicy
      const payload = {
        ...policyBody,
        last_reviewed: normalizeDate(nextPolicy.last_reviewed),
        next_review: normalizeDate(nextPolicy.next_review),
        principles: nextPolicy.principles || [],
        sections: nextPolicy.sections || [],
      }
      const saved = await apiJson<InsiderRiskPolicy>('/insider-program/policy', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      setPolicy(normalizePolicy(saved))
      setPolicyTemplate(Boolean(saved.is_template))
      setPolicyDraft(null)
    } catch {
      setPolicyError('Failed to save policy.')
    } finally {
      setPolicySaving(false)
    }
  }

  const loadRecommendations = async () => {
    setActionsLoading(true)
    const targetAssessment = filters.assessment || assessmentId
    try {
      let data: Recommendation[] = []
      if (!targetAssessment) {
        data = await apiJson<Recommendation[]>('/recommendations/library')
        data = data.map((rec) => ({ ...rec, status: 'pending' }))
      } else {
        data = await apiJson<Recommendation[]>(`/assessment/${targetAssessment}/recommendations`)
      }
      setRecommendations(data)
    } catch {
      setRecommendations([])
    } finally {
      setActionsLoading(false)
    }
  }

  const seedControls = async () => {
    if (controlsSeeded) {
      return DEFAULT_CONTROLS.map(normalizeControl)
    }
    setControlsSeeded(true)
    try {
      const results = await Promise.allSettled(
        DEFAULT_CONTROLS.map((control) =>
          apiJson<Control>('/insider-program/controls', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              ...control,
              last_reviewed: normalizeDate(control.last_reviewed),
              next_review: normalizeDate(control.next_review),
              linked_actions: control.linked_actions ?? [],
              linked_rec_ids: control.linked_rec_ids ?? [],
              linked_categories: control.linked_categories ?? [],
            }),
          }),
        ),
      )
      const created = results
        .filter((result): result is PromiseFulfilledResult<Control> => result.status === 'fulfilled')
        .map((result) => normalizeControl(result.value))
      return created.length ? created : DEFAULT_CONTROLS.map(normalizeControl)
    } catch {
      return DEFAULT_CONTROLS.map(normalizeControl)
    }
  }

  const loadControls = async () => {
    setControlsLoading(true)
    setControlsError(null)
    try {
      const data = await apiJson<Control[]>('/insider-program/controls')
      if (!data.length) {
        const seeded = await seedControls()
        setControls(seeded)
      } else {
        setControls(data.map(normalizeControl))
      }
    } catch {
      setControlsError('Control register unavailable.')
      setControls(DEFAULT_CONTROLS.map(normalizeControl))
    } finally {
      setControlsLoading(false)
    }
  }

  const applyFilters = () => {
    setFilters({ ...filters })
  }

  const filtered = recommendations.filter((rec) => {
    if (filters.priority && rec.priority !== filters.priority) return false
    if (filters.status && rec.status !== filters.status) return false
    if (filters.category && rec.category !== filters.category) return false
    return true
  })

  const stats = {
    total: filtered.length,
    critical: filtered.filter((r) => r.priority === 'Critical').length,
    inProgress: filtered.filter((r) => r.status === 'in_progress').length,
    completed: filtered.filter((r) => r.status === 'completed').length,
  }

  const controlDomains = useMemo(() => {
    const merged = new Set<string>(CONTROL_DOMAINS)
    controls.forEach((control) => merged.add(control.domain))
    return Array.from(merged).sort()
  }, [controls])

  const filteredControls = useMemo(() => {
    return controls.filter((control) => {
      if (controlFilters.domain && control.domain !== controlFilters.domain) return false
      if (controlFilters.status && control.status !== controlFilters.status) return false
      return true
    })
  }, [controls, controlFilters])

  const controlStats = useMemo(() => {
    const totals = {
      total: controls.length,
      planned: 0,
      in_progress: 0,
      implemented: 0,
      monitored: 0,
    }
    controls.forEach((control) => {
      if (control.status === 'planned') totals.planned += 1
      if (control.status === 'in_progress') totals.in_progress += 1
      if (control.status === 'implemented') totals.implemented += 1
      if (control.status === 'monitored') totals.monitored += 1
    })
    return totals
  }, [controls])

  const controlCoverage =
    controlStats.total > 0
      ? Math.round(((controlStats.implemented + controlStats.monitored) / controlStats.total) * 100)
      : 0

  const controlsReviewDue = useMemo(() => {
    const windowDays = 30
    const now = Date.now()
    const cutoff = now + windowDays * 24 * 60 * 60 * 1000
    return controls.filter((control) => {
      const next = new Date(control.next_review).getTime()
      return Number.isFinite(next) && next <= cutoff
    }).length
  }, [controls])

  const recommendationById = useMemo(
    () => new Map(recommendations.map((rec) => [rec.rec_id, rec])),
    [recommendations],
  )

  const formatDate = (value?: string) => {
    if (!value) return '--'
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return '--'
    return parsed.toLocaleDateString()
  }

  const buildLinkedActions = (control: Control) => {
    const linked = new Set<string>()
    control.linked_rec_ids?.forEach((recId) => {
      const rec = recommendationById.get(recId)
      if (rec?.title) {
        linked.add(rec.title)
      } else {
        linked.add(`Rec ID: ${recId}`)
      }
    })
    control.linked_categories?.forEach((category) => {
      const matches = recommendations.filter((rec) => rec.category === category)
      if (!matches.length) {
        linked.add(`Category: ${category}`)
        return
      }
      matches.forEach((rec) => {
        if (rec.title) linked.add(rec.title)
      })
    })
    control.linked_actions?.forEach((action) => linked.add(action))
    return Array.from(linked)
  }

  const openModal = (rec: Recommendation) => {
    setModalRec(rec)
    setModalFields({
      status: rec.status || 'pending',
      priority: rec.priority,
      assigned_to: rec.assigned_to || '',
      due_date: rec.due_date ? rec.due_date.split('T')[0] : '',
      custom_notes: rec.custom_notes || '',
    })
  }

  const saveUpdate = async () => {
    if (!modalRec || !modalRec.assessment_id) return
    try {
      const resp = await apiFetch(`/assessment/${modalRec.assessment_id}/recommendations/${modalRec.rec_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...modalFields, user_id: currentUser || 'current_user' }),
      })
      if (!resp.ok) throw new Error('Update failed')
      setModalRec(null)
      loadRecommendations()
    } catch {
      alert('Failed to update program action.')
    }
  }

  const openControlEdit = (control: Control) => {
    setControlMode('edit')
    setControlDraft(normalizeControl(control))
  }

  const updateControlDraft = (patch: Partial<Control>) => {
    setControlDraft((prev) => (prev ? { ...prev, ...patch } : prev))
  }

  const updatePolicyDraft = (patch: Partial<InsiderRiskPolicy>) => {
    setPolicyDraft((prev) => (prev ? { ...prev, ...patch } : prev))
  }

  const openControlCreate = () => {
    const nextId = `IR-CTRL-${String(controls.length + 1).padStart(3, '0')}`
    setControlMode('create')
    setControlDraft({
      control_id: nextId,
      title: '',
      domain: controlDomains[0] || 'Governance',
      objective: '',
      status: 'planned',
      owner: '',
      frequency: 'Quarterly',
      evidence: '',
      last_reviewed: '',
      next_review: '',
      linked_actions: [],
      linked_rec_ids: [],
      linked_categories: [],
    })
  }

  const openPolicyEdit = () => {
    setPolicyDraft(JSON.parse(JSON.stringify(policy)))
  }

  const saveControl = async () => {
    if (!controlDraft) return
    try {
      const payload = {
        ...controlDraft,
        last_reviewed: normalizeDate(controlDraft.last_reviewed),
        next_review: normalizeDate(controlDraft.next_review),
        linked_actions: controlDraft.linked_actions ?? [],
        linked_rec_ids: controlDraft.linked_rec_ids ?? [],
        linked_categories: controlDraft.linked_categories ?? [],
      }
      let saved: Control
      if (controlMode === 'create') {
        saved = await apiJson<Control>('/insider-program/controls', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      } else {
        saved = await apiJson<Control>(`/insider-program/controls/${controlDraft.control_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      }
      setControls((prev) => {
        const normalized = normalizeControl(saved)
        if (controlMode === 'create') {
          return [normalized, ...prev]
        }
        return prev.map((control) =>
          control.control_id === normalized.control_id ? normalized : control,
        )
      })
      setControlsError(null)
      setControlDraft(null)
    } catch {
      setControlsError('Failed to save control.')
    }
  }

  return (
    <div className="recommendations-page">
      <header className="rec-header">
        <h1>🧭 Insider Risk Program</h1>
        <p className="rec-subtitle">
          Program governance, action ownership, and timelines tied to your assessment findings.
        </p>
      </header>

      <section className="irp-section">
        <div className="irp-section-header">
          <div>
            <h2>Insider Risk Policy</h2>
            <p>Formal policy and governance rules that drive the program and its controls.</p>
          </div>
          <div className="irp-section-actions">
            <button className="btn btn-secondary btn-sm" type="button" onClick={openPolicyEdit}>
              Edit Policy
            </button>
            <button
              className="btn btn-primary btn-sm"
              type="button"
              onClick={() => savePolicy(policy)}
              disabled={policySaving}
            >
              {policySaving ? 'Saving...' : 'Save Policy'}
            </button>
            <button className="btn btn-secondary btn-sm" type="button">
              Export Policy
            </button>
          </div>
        </div>

        <div className="irp-policy-grid">
          <div className="irp-card">
            <div className="irp-card-title">Policy Summary</div>
            <p className="irp-muted">{policy.scope || '--'}</p>
            <div className="irp-kv">
              <div>
                <div className="kv-label">Status</div>
                <div className="kv-value">{policyLoading ? '--' : policy.status || '--'}</div>
              </div>
              <div>
                <div className="kv-label">Owner</div>
                <div className="kv-value">{policyLoading ? '--' : policy.owner || '--'}</div>
              </div>
              <div>
                <div className="kv-label">Last Review</div>
                <div className="kv-value">{formatDate(policy.last_reviewed)}</div>
              </div>
              <div>
                <div className="kv-label">Next Review</div>
                <div className="kv-value">{formatDate(policy.next_review)}</div>
              </div>
            </div>
            <div className="irp-meta">
              <span className="badge">Version {policy.version || '--'}</span>
              <span className="badge">{policy.approval || 'Approval pending'}</span>
              <span className="badge">{policyTemplate ? 'Template' : 'Stored'}</span>
            </div>
            {policyError ? <div className="irp-muted irp-status-note">{policyError}</div> : null}
          </div>

          <div className="irp-card">
            <div className="irp-card-title">Core Principles</div>
            <ul className="irp-list">
              {policy.principles.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="irp-policy-sections">
          {policy.sections.map((section) => (
            <div key={section.title} className="irp-card">
              <div className="irp-card-title">{section.title}</div>
              {section.intent ? <p className="irp-muted">{section.intent}</p> : null}
              <ul className="irp-list">
                {(section.bullets || []).map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
              <div className="irp-subgrid">
                <div>
                  <div className="detail-label">Owner</div>
                  <div className="detail-value">{section.owner || '--'}</div>
                </div>
                <div>
                  <div className="detail-label">Artifacts</div>
                  <div className="detail-value">
                    {(section.artifacts || []).length ? (
                      section.artifacts!.map((artifact) => (
                        <span key={artifact} className="irp-chip">
                          {artifact}
                        </span>
                      ))
                    ) : (
                      <span className="irp-muted">None</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="irp-section">
        <div className="irp-section-header">
          <div>
            <h2>Control Register</h2>
            <p>Manage controls derived from policy requirements and assessment-driven actions.</p>
          </div>
          <div className="irp-section-actions">
            <button className="btn btn-primary btn-sm" onClick={openControlCreate}>
              Register Control
            </button>
          </div>
        </div>

        <div className="stats-grid irp-control-stats">
          <div className="stat-card">
            <div className="stat-label">Control Coverage</div>
            <div className="stat-value">{controlsLoading ? '--' : `${controlCoverage}%`}</div>
            <div className="stat-sub">Implemented + Monitored</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Planned</div>
            <div className="stat-value">{controlsLoading ? '--' : controlStats.planned}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">In Progress</div>
            <div className="stat-value progress">{controlsLoading ? '--' : controlStats.in_progress}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Review Due (30d)</div>
            <div className="stat-value critical">{controlsLoading ? '--' : controlsReviewDue}</div>
          </div>
        </div>

        {controlsError ? <div className="irp-muted irp-status-note">{controlsError}</div> : null}

        <div className="filters control-filters">
          <div className="filter-row">
            <div className="filter-group">
              <label>Domain</label>
              <select
                value={controlFilters.domain}
                onChange={(event) => setControlFilters({ ...controlFilters, domain: event.target.value })}
              >
                <option value="">All Domains</option>
                {controlDomains.map((domain) => (
                  <option key={domain} value={domain}>
                    {domain}
                  </option>
                ))}
              </select>
            </div>
            <div className="filter-group">
              <label>Status</label>
              <select
                value={controlFilters.status}
                onChange={(event) =>
                  setControlFilters({ ...controlFilters, status: event.target.value })
                }
              >
                <option value="">All Statuses</option>
                {CONTROL_STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>
                    {status.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <div className="filter-group align-end">
              <label>&nbsp;</label>
              <button
                className="btn btn-secondary"
                onClick={() => setControlFilters({ domain: '', status: '' })}
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {controlsLoading ? (
          <div className="rec-loading">
            <div className="spinner" />
            <p>Loading control register...</p>
          </div>
        ) : filteredControls.length === 0 ? (
          <div className="empty-state">
            <h3>No Controls Found</h3>
            <p>Register a new control or clear your filters.</p>
          </div>
        ) : (
          <div className="control-grid">
            {filteredControls.map((control) => {
              const statusClass = control.status.replace('_', '-')
              const domainClass = control.domain.toLowerCase().replace(/\s+/g, '-')
              const linkedActions = buildLinkedActions(control)
              return (
                <div key={control.control_id} className={`control-card domain-${domainClass}`}>
                  <div className="control-header">
                    <div>
                      <div className="control-id">{control.control_id}</div>
                      <h3 className="control-title">{control.title || 'New Control'}</h3>
                    </div>
                    <div className="control-tags">
                      <span className="badge">{control.domain}</span>
                      <span className={`badge badge-status ${statusClass}`}>
                        {control.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <p className="control-objective">
                    {control.objective || 'Objective to be defined.'}
                  </p>
                  <div className="control-meta-grid">
                    <div>
                      <div className="detail-label">Owner</div>
                      <div className="detail-value">{control.owner || 'Unassigned'}</div>
                    </div>
                    <div>
                      <div className="detail-label">Frequency</div>
                      <div className="detail-value">{control.frequency || '--'}</div>
                    </div>
                    <div>
                      <div className="detail-label">Last Review</div>
                      <div className="detail-value">{formatDate(control.last_reviewed)}</div>
                    </div>
                    <div>
                      <div className="detail-label">Next Review</div>
                      <div className="detail-value">{formatDate(control.next_review)}</div>
                    </div>
                    <div>
                      <div className="detail-label">Evidence</div>
                      <div className="detail-value">{control.evidence || 'Not provided'}</div>
                    </div>
                  </div>
                  <div className="control-links">
                    <div className="detail-label">Linked actions</div>
                    <div className="control-link-tags">
                      {linkedActions.length ? (
                        linkedActions.slice(0, 4).map((action) => (
                          <span key={action} className="trigger-tag">
                            {action}
                          </span>
                        ))
                      ) : (
                        <span className="irp-muted">No linked actions yet.</span>
                      )}
                    </div>
                  </div>
                  <div className="control-actions">
                    <button className="btn btn-secondary btn-sm" onClick={() => openControlEdit(control)}>
                      Update Control
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>

      <section className="irp-section">
        <div className="irp-section-header">
          <div>
            <h2>Program Actions</h2>
            <p>Assessment-driven recommendations tracked as accountable program actions.</p>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Actions</div>
            <div className="stat-value">{actionsLoading ? '--' : stats.total}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Critical Priority</div>
            <div className="stat-value critical">{actionsLoading ? '--' : stats.critical}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">In Progress</div>
            <div className="stat-value progress">{actionsLoading ? '--' : stats.inProgress}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Completed</div>
            <div className="stat-value completed">{actionsLoading ? '--' : stats.completed}</div>
          </div>
        </div>

        <div className="filters">
          <div className="filter-row">
            <div className="filter-group">
              <label>Assessment</label>
              <select
                value={filters.assessment}
                onChange={(event) => setFilters({ ...filters, assessment: event.target.value })}
              >
                <option value="">All Assessments</option>
                {assessmentId ? <option value={assessmentId}>Current Assessment</option> : null}
              </select>
            </div>
            <div className="filter-group">
              <label>Priority</label>
              <select
                value={filters.priority}
                onChange={(event) => setFilters({ ...filters, priority: event.target.value })}
              >
                <option value="">All Priorities</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
            <div className="filter-group">
              <label>Status</label>
              <select
                value={filters.status}
                onChange={(event) => setFilters({ ...filters, status: event.target.value })}
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div className="filter-group">
              <label>Category</label>
              <select
                value={filters.category}
                onChange={(event) => setFilters({ ...filters, category: event.target.value })}
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
            <div className="filter-group align-end">
              <label>&nbsp;</label>
              <button className="btn btn-primary" onClick={applyFilters}>
                Apply Filters
              </button>
            </div>
          </div>
        </div>

        {actionsLoading ? (
          <div className="rec-loading">
            <div className="spinner" />
            <p>Loading program actions...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <h3>No Program Actions Found</h3>
            <p>Try adjusting your filters or complete an assessment to generate recommendations.</p>
          </div>
        ) : (
          <div className="recommendations-grid">
            {filtered.map((rec) => {
              const priorityClass = rec.priority.toLowerCase()
              const statusClass = rec.status ? rec.status.replace('_', '-') : 'pending'
              const triggeredBy = [
                ...(rec.triggered_by?.axes || []).map((a) => `Axis: ${a}`),
                ...(rec.triggered_by?.risks || []).map((r) => `Risk: ${r}`),
              ]
              const hasSteps = rec.implementation_steps?.steps?.length
              return (
                <div key={rec.rec_id} className={`rec-card priority-${priorityClass}`}>
                  <div className="rec-header-row">
                    <div>
                      <h3 className="rec-title">{rec.title}</h3>
                      <div className="rec-meta">
                        <span className={`badge badge-${priorityClass}`}>{rec.priority}</span>
                        {rec.status ? (
                          <span className={`badge badge-status ${statusClass}`}>
                            {rec.status.replace('_', ' ').toUpperCase()}
                          </span>
                        ) : null}
                        <span className="badge">{rec.category}</span>
                        {rec.effort ? <span className="badge">{rec.effort} Effort</span> : null}
                      </div>
                    </div>
                  </div>
                  <p className="rec-description">{rec.description}</p>
                  {rec.rationale ? (
                    <div className="rec-rationale">
                      <strong>Why this matters:</strong>
                      <p>{rec.rationale}</p>
                    </div>
                  ) : null}
                  {triggeredBy.length > 0 ? (
                    <div className="triggered-by">
                      <strong>Triggered by:</strong>
                      {triggeredBy.map((tag) => (
                        <span key={tag} className="trigger-tag">
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <div className="rec-details">
                    {rec.timeline ? (
                      <div className="detail-item">
                        <div className="detail-label">Timeline</div>
                        <div className="detail-value">{rec.timeline}</div>
                      </div>
                    ) : null}
                    {rec.subcategory ? (
                      <div className="detail-item">
                        <div className="detail-label">Subcategory</div>
                        <div className="detail-value">{rec.subcategory}</div>
                      </div>
                    ) : null}
                    {rec.assigned_to ? (
                      <div className="detail-item">
                        <div className="detail-label">Assigned To</div>
                        <div className="detail-value">{rec.assigned_to}</div>
                      </div>
                    ) : null}
                    {rec.due_date ? (
                      <div className="detail-item">
                        <div className="detail-label">Due Date</div>
                        <div className="detail-value">{new Date(rec.due_date).toLocaleDateString()}</div>
                      </div>
                    ) : null}
                  </div>
                  {hasSteps ? (
                    <details className="rec-steps">
                      <summary>View Implementation Steps</summary>
                      <div className="implementation-steps">
                        {rec.implementation_steps?.steps.map((step) => (
                          <div key={step.step} className="step">
                            <div className="step-number">{step.step}</div>
                            <div className="step-content">
                              <div className="step-action">{step.action}</div>
                              <div className="step-owner">Owner: {step.owner}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </details>
                  ) : null}
                  {rec.assessment_id ? (
                    <div className="rec-actions">
                      <button className="btn btn-primary btn-sm" onClick={() => openModal(rec)}>
                        Update Status
                      </button>
                    </div>
                  ) : null}
                </div>
              )
            })}
          </div>
        )}
      </section>

      {modalRec ? (
        <div className="modal active" onClick={(event) => event.target === event.currentTarget && setModalRec(null)}>
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">Update Program Action</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setModalRec(null)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Status</label>
                <select
                  value={modalFields.status}
                  onChange={(event) => setModalFields({ ...modalFields, status: event.target.value })}
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>
              <div className="form-group">
                <label>Priority</label>
                <select
                  value={modalFields.priority}
                  onChange={(event) => setModalFields({ ...modalFields, priority: event.target.value })}
                >
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
              <div className="form-group">
                <label>Assigned To</label>
                <input
                  type="text"
                  value={modalFields.assigned_to}
                  onChange={(event) => setModalFields({ ...modalFields, assigned_to: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Due Date</label>
                <input
                  type="date"
                  value={modalFields.due_date}
                  onChange={(event) => setModalFields({ ...modalFields, due_date: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={modalFields.custom_notes}
                  onChange={(event) => setModalFields({ ...modalFields, custom_notes: event.target.value })}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setModalRec(null)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={saveUpdate}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      ) : null}
      {controlDraft ? (
        <div className="modal active" onClick={(event) => event.target === event.currentTarget && setControlDraft(null)}>
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">
                {controlMode === 'create' ? 'Register Control' : 'Update Control'}
              </h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setControlDraft(null)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Control ID</label>
                <input
                  type="text"
                  value={controlDraft.control_id || ''}
                  onChange={(event) => updateControlDraft({ control_id: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  value={controlDraft.title || ''}
                  onChange={(event) => updateControlDraft({ title: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Domain</label>
                <select
                  value={controlDraft.domain}
                  onChange={(event) => updateControlDraft({ domain: event.target.value })}
                >
                  {controlDomains.map((domain) => (
                    <option key={domain} value={domain}>
                      {domain}
                    </option>
                  ))}
                  {!controlDomains.includes(controlDraft.domain) ? (
                    <option value={controlDraft.domain}>{controlDraft.domain}</option>
                  ) : null}
                </select>
              </div>
              <div className="form-group">
                <label>Status</label>
                <select
                  value={controlDraft.status}
                  onChange={(event) =>
                    updateControlDraft({ status: event.target.value as ControlStatus })
                  }
                >
                  {CONTROL_STATUS_OPTIONS.map((status) => (
                    <option key={status} value={status}>
                      {status.replace('_', ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Owner</label>
                <input
                  type="text"
                  value={controlDraft.owner || ''}
                  onChange={(event) => updateControlDraft({ owner: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Frequency</label>
                <input
                  type="text"
                  value={controlDraft.frequency || ''}
                  onChange={(event) => updateControlDraft({ frequency: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Objective</label>
                <textarea
                  value={controlDraft.objective || ''}
                  onChange={(event) => updateControlDraft({ objective: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Evidence</label>
                <textarea
                  value={controlDraft.evidence || ''}
                  onChange={(event) => updateControlDraft({ evidence: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Last Review</label>
                <input
                  type="date"
                  value={controlDraft.last_reviewed || ''}
                  onChange={(event) => updateControlDraft({ last_reviewed: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Next Review</label>
                <input
                  type="date"
                  value={controlDraft.next_review || ''}
                  onChange={(event) => updateControlDraft({ next_review: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Linked Actions (one per line)</label>
                <textarea
                  value={(controlDraft.linked_actions || []).join('\n')}
                  onChange={(event) =>
                    updateControlDraft({
                      linked_actions: event.target.value
                        .split('\n')
                        .map((item) => item.trim())
                        .filter(Boolean),
                    })
                  }
                />
              </div>
              <div className="form-group">
                <label>Linked Recommendation IDs (one per line)</label>
                <textarea
                  value={(controlDraft.linked_rec_ids || []).join('\n')}
                  onChange={(event) =>
                    updateControlDraft({
                      linked_rec_ids: event.target.value
                        .split('\n')
                        .map((item) => item.trim())
                        .filter(Boolean),
                    })
                  }
                />
              </div>
              <div className="form-group">
                <label>Linked Categories (one per line)</label>
                <textarea
                  value={(controlDraft.linked_categories || []).join('\n')}
                  onChange={(event) =>
                    updateControlDraft({
                      linked_categories: event.target.value
                        .split('\n')
                        .map((item) => item.trim())
                        .filter(Boolean),
                    })
                  }
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setControlDraft(null)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={saveControl}>
                Save Control
              </button>
            </div>
          </div>
        </div>
      ) : null}
      {policyDraft ? (
        <div className="modal active" onClick={(event) => event.target === event.currentTarget && setPolicyDraft(null)}>
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">Edit Policy</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setPolicyDraft(null)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Status</label>
                <input
                  type="text"
                  value={policyDraft.status || ''}
                  onChange={(event) => updatePolicyDraft({ status: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Version</label>
                <input
                  type="text"
                  value={policyDraft.version || ''}
                  onChange={(event) => updatePolicyDraft({ version: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Owner</label>
                <input
                  type="text"
                  value={policyDraft.owner || ''}
                  onChange={(event) => updatePolicyDraft({ owner: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Approval</label>
                <input
                  type="text"
                  value={policyDraft.approval || ''}
                  onChange={(event) => updatePolicyDraft({ approval: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Scope</label>
                <textarea
                  value={policyDraft.scope || ''}
                  onChange={(event) => updatePolicyDraft({ scope: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Last Review</label>
                <input
                  type="date"
                  value={policyDraft.last_reviewed || ''}
                  onChange={(event) => updatePolicyDraft({ last_reviewed: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Next Review</label>
                <input
                  type="date"
                  value={policyDraft.next_review || ''}
                  onChange={(event) => updatePolicyDraft({ next_review: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Core Principles (one per line)</label>
                <textarea
                  value={(policyDraft.principles || []).join('\n')}
                  onChange={(event) =>
                    updatePolicyDraft({
                      principles: event.target.value
                        .split('\n')
                        .map((item) => item.trim())
                        .filter(Boolean),
                    })
                  }
                />
              </div>
              <div className="irp-muted">
                Policy sections are managed in the template for now; ask to extend if you want full section editing.
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setPolicyDraft(null)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={() => policyDraft && savePolicy(policyDraft)}
                disabled={policySaving}
              >
                {policySaving ? 'Saving...' : 'Save Policy'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default InsiderRiskProgram
