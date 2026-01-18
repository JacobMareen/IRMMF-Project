import { useEffect, useMemo, useState } from 'react'
import './Recommendations.css'
import { getStoredAssessmentId } from '../utils/assessment'

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

const API_BASE = 'http://127.0.0.1:8000'

const Recommendations = () => {
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [assessmentId, setAssessmentId] = useState<string>('')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
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

  useEffect(() => {
    setAssessmentId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    loadLibraryCategories()
  }, [])

  useEffect(() => {
    loadRecommendations()
  }, [filters.assessment])

  const loadLibraryCategories = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/recommendations/library`)
      if (!resp.ok) return
      const data = (await resp.json()) as Recommendation[]
      const unique = Array.from(new Set(data.map((rec) => rec.category).filter(Boolean)))
      setCategories(unique)
    } catch {
      setCategories([])
    }
  }

  const loadRecommendations = async () => {
    setLoading(true)
    const targetAssessment = filters.assessment || assessmentId
    try {
      let data: Recommendation[] = []
      if (!targetAssessment) {
        const resp = await fetch(`${API_BASE}/api/v1/recommendations/library`)
        data = resp.ok ? await resp.json() : []
        data = data.map((rec) => ({ ...rec, status: 'pending' }))
      } else {
        const resp = await fetch(`${API_BASE}/api/v1/assessment/${targetAssessment}/recommendations`)
        data = resp.ok ? await resp.json() : []
      }
      setRecommendations(data)
    } catch {
      setRecommendations([])
    } finally {
      setLoading(false)
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
      const resp = await fetch(
        `${API_BASE}/api/v1/assessment/${modalRec.assessment_id}/recommendations/${modalRec.rec_id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...modalFields, user_id: currentUser || 'current_user' }),
        }
      )
      if (!resp.ok) throw new Error('Update failed')
      setModalRec(null)
      loadRecommendations()
    } catch {
      alert('Failed to update recommendation.')
    }
  }

  if (loading) {
    return (
      <div className="rec-loading">
        <div className="spinner" />
        <p>Loading recommendations...</p>
      </div>
    )
  }

  return (
    <div className="recommendations-page">
      <header className="rec-header">
        <h1>📋 Recommendations</h1>
        <p className="rec-subtitle">Actionable recommendations based on your assessment findings.</p>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Recommendations</div>
          <div className="stat-value">{stats.total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Critical Priority</div>
          <div className="stat-value critical">{stats.critical}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">In Progress</div>
          <div className="stat-value progress">{stats.inProgress}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Completed</div>
          <div className="stat-value completed">{stats.completed}</div>
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

      {filtered.length === 0 ? (
        <div className="empty-state">
          <h3>No Recommendations Found</h3>
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

      {modalRec ? (
        <div className="modal active" onClick={(event) => event.target === event.currentTarget && setModalRec(null)}>
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">Update Recommendation</h3>
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
    </div>
  )
}

export default Recommendations
