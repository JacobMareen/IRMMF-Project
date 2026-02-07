import React, { useMemo } from 'react'
import { useProgram } from '../context/ProgramContext'
import { type Control, type ControlStatus } from '../types'
import { CONTROL_STATUS_OPTIONS } from '../constants'

const ControlRegister: React.FC = () => {
    const {
        controls,
        controlsLoading,
        controlsError,
        controlDraft,
        setControlDraft,
        updateControlDraft,
        saveControl,
        controlFilters,
        setControlFilters,
        recommendations
    } = useProgram()

    const controlDomains = useMemo(() => {
        const merged = new Set<string>(['Governance', 'Prevention', 'Detection', 'Response', 'Recovery'])
        controls.forEach((control: Control) => merged.add(control.domain))
        return Array.from(merged).sort()
    }, [controls])

    const filteredControls = useMemo(() => {
        return controls.filter((control: Control) => {
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
        controls.forEach((control: Control) => {
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
        return controls.filter((control: Control) => {
            const next = new Date(control.next_review || '').getTime()
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

    const openControlCreate = () => {
        const nextId = `IR-CTRL-${String(controls.length + 1).padStart(3, '0')}`
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

    const openControlEdit = (control: Control) => {
        // Simple distinct logic: if control exists in list, it's edit mode
        setControlDraft(JSON.parse(JSON.stringify(control)))
    }

    const handleSave = () => {
        if (!controlDraft) return
        const isNew = !controls.find(c => c.control_id === controlDraft.control_id)
        saveControl(isNew ? 'create' : 'edit')
    }

    return (
        <>
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
                                {CONTROL_STATUS_OPTIONS.map((status: string) => (
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

            {controlDraft && (
                <div className="modal active" onClick={(event) => event.target === event.currentTarget && setControlDraft(null)}>
                    <div className="modal-content">
                        <div className="modal-header">
                            <h3 className="modal-title">
                                {controls.find(c => c.control_id === controlDraft.control_id) ? 'Update Control' : 'Register Control'}
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
                                    {CONTROL_STATUS_OPTIONS.map((status: string) => (
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
                            <button className="btn btn-primary" onClick={handleSave}>
                                Save Control
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}

export default ControlRegister
