import React from 'react'

import { useProgram } from '../context/ProgramContext'

const PolicyManager: React.FC = () => {
    const {
        policy,
        policyLoading,
        policySaving,
        policyTemplate,
        policyDraft,
        policyError,
        setPolicyDraft,
        updatePolicyDraft,
        savePolicy
    } = useProgram()

    const formatDate = (value?: string) => {
        if (!value) return '--'
        const parsed = new Date(value)
        if (Number.isNaN(parsed.getTime())) return '--'
        return parsed.toLocaleDateString()
    }

    const openPolicyEdit = () => {
        setPolicyDraft(JSON.parse(JSON.stringify(policy)))
    }

    return (
        <>
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
                    </div>
                </div>

                <div className="irp-policy-grid">
                    <div className="irp-card">
                        <div className="irp-card-title">Policy Summary</div>
                        <p className="irp-muted">{policy.scope || 'No scope defined.'}</p>
                        <div className="irp-kv">
                            <div>
                                <div className="kv-label">Status</div>
                                <div className="kv-value">{policyLoading ? '--' : policy.status || 'Draft'}</div>
                            </div>
                            <div>
                                <div className="kv-label">Owner</div>
                                <div className="kv-value">{policyLoading ? '--' : policy.owner || 'Unassigned'}</div>
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
                            <span className="badge">Version {policy.version || '0.1'}</span>
                            <span className="badge">{policy.approval || 'Pending Approval'}</span>
                            <span className="badge">{policyTemplate ? 'Template' : 'Stored'}</span>
                        </div>
                        {policyError ? <div className="irp-muted irp-status-note">{policyError}</div> : null}
                    </div>

                    <div className="irp-card">
                        <div className="irp-card-title">Core Principles</div>
                        {policy.principles && policy.principles.length > 0 ? (
                            <ul className="irp-list">
                                {policy.principles.map((item, i) => (
                                    <li key={i}>{item}</li>
                                ))}
                            </ul>
                        ) : (
                            <p className="irp-muted">No principles defined.</p>
                        )}
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

            {policyDraft && (
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
            )}
        </>
    )
}

export default PolicyManager
