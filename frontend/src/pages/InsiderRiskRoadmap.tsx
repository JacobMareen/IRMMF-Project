import { useEffect, useState } from 'react'
import './InsiderRiskRoadmap.css'
import { apiJson } from '../lib/api'

type RoadmapItem = {
  id?: string
  phase: string
  title: string
  description?: string | null
  owner?: string | null
  target_window?: string | null
  status?: string | null
}

const DEFAULT_ITEMS: RoadmapItem[] = [
  {
    phase: 'Now',
    title: 'Policy approval + control onboarding',
    description: 'Finalize policy approvals, seed control register, and align owners.',
    owner: 'IR Program Lead',
    target_window: '30 days',
    status: 'planned',
  },
  {
    phase: 'Next',
    title: 'Risk telemetry + alert tuning',
    description: 'Define signal sources, thresholds, and triage SLAs.',
    owner: 'Security Operations',
    target_window: '60 days',
    status: 'planned',
  },
  {
    phase: 'Later',
    title: 'Response readiness & training',
    description: 'Run tabletop exercises and update training materials.',
    owner: 'HR + Legal',
    target_window: '90 days',
    status: 'planned',
  },
]

const InsiderRiskRoadmap = () => {
  const [items, setItems] = useState<RoadmapItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [draft, setDraft] = useState<RoadmapItem | null>(null)
  const [mode, setMode] = useState<'create' | 'edit'>('create')
  const [seeded, setSeeded] = useState(false)

  const seedRoadmap = async () => {
    if (seeded) return DEFAULT_ITEMS
    setSeeded(true)
    try {
      const results = await Promise.allSettled(
        DEFAULT_ITEMS.map((item) =>
          apiJson<RoadmapItem>('/insider-program/roadmap', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(item),
          }),
        ),
      )
      const created = results
        .filter((result): result is PromiseFulfilledResult<RoadmapItem> => result.status === 'fulfilled')
        .map((result) => result.value)
      return created.length ? created : DEFAULT_ITEMS
    } catch {
      return DEFAULT_ITEMS
    }
  }

  const loadRoadmap = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiJson<RoadmapItem[]>('/insider-program/roadmap')
      if (!data.length) {
        const seededItems = await seedRoadmap()
        setItems(seededItems)
      } else {
        setItems(data)
      }
    } catch {
      setItems(DEFAULT_ITEMS)
      setError('Roadmap unavailable. Using defaults.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRoadmap()
  }, [])

  const openCreate = () => {
    setMode('create')
    setDraft({
      phase: 'Now',
      title: '',
      description: '',
      owner: '',
      target_window: '',
      status: 'planned',
    })
  }

  const openEdit = (item: RoadmapItem) => {
    setMode('edit')
    setDraft({ ...item })
  }

  const saveDraft = async () => {
    if (!draft) return
    try {
      if (mode === 'create') {
        const created = await apiJson<RoadmapItem>('/insider-program/roadmap', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(draft),
        })
        setItems((prev) => [created, ...prev])
      } else if (draft.id) {
        const updated = await apiJson<RoadmapItem>(`/insider-program/roadmap/${draft.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(draft),
        })
        setItems((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
      }
      setDraft(null)
      setError(null)
    } catch {
      setError('Failed to save roadmap item.')
    }
  }

  const deleteItem = async (item: RoadmapItem) => {
    if (!item.id) {
      setItems((prev) => prev.filter((row) => row !== item))
      return
    }
    try {
      await apiJson(`/insider-program/roadmap/${item.id}`, { method: 'DELETE' })
      setItems((prev) => prev.filter((row) => row.id !== item.id))
    } catch {
      setError('Failed to delete roadmap item.')
    }
  }

  return (
    <section className="irp-roadmap">
      <div className="irp-roadmap-header">
        <div>
          <h2>Program Roadmap</h2>
          <p>Sequenced milestones that operationalize the insider risk program.</p>
          {error ? <div className="irp-roadmap-note">{error}</div> : null}
        </div>
        <button className="btn btn-primary btn-sm" type="button" onClick={openCreate}>
          Add Milestone
        </button>
      </div>

      {loading ? (
        <div className="irp-roadmap-note">Loading roadmap...</div>
      ) : (
        <div className="irp-roadmap-grid">
          {items.map((item, idx) => (
            <div key={item.id || `${item.title}-${idx}`} className="irp-roadmap-card">
              <div className="irp-roadmap-phase">{item.phase}</div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              <div className="irp-roadmap-meta">
                <span>Owner: {item.owner || 'TBD'}</span>
                <span>Target: {item.target_window || 'TBD'}</span>
                <span>Status: {item.status || 'planned'}</span>
              </div>
              <div className="irp-roadmap-actions">
                <button className="btn btn-secondary btn-sm" onClick={() => openEdit(item)}>
                  Edit
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => deleteItem(item)}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {draft ? (
        <div className="modal active" onClick={(event) => event.target === event.currentTarget && setDraft(null)}>
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">
                {mode === 'create' ? 'Add Milestone' : 'Edit Milestone'}
              </h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setDraft(null)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Phase</label>
                <select
                  value={draft.phase}
                  onChange={(event) => setDraft({ ...draft, phase: event.target.value })}
                >
                  <option value="Now">Now</option>
                  <option value="Next">Next</option>
                  <option value="Later">Later</option>
                </select>
              </div>
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  value={draft.title}
                  onChange={(event) => setDraft({ ...draft, title: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={draft.description || ''}
                  onChange={(event) => setDraft({ ...draft, description: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Owner</label>
                <input
                  type="text"
                  value={draft.owner || ''}
                  onChange={(event) => setDraft({ ...draft, owner: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Target Window</label>
                <input
                  type="text"
                  value={draft.target_window || ''}
                  onChange={(event) => setDraft({ ...draft, target_window: event.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select
                  value={draft.status || 'planned'}
                  onChange={(event) => setDraft({ ...draft, status: event.target.value })}
                >
                  <option value="planned">Planned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setDraft(null)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={saveDraft}>
                Save Milestone
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}

export default InsiderRiskRoadmap
