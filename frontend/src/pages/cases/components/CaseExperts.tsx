import React, { useState } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { useCaseInvestigation } from '../hooks/useCaseInvestigation'
import { maskText } from '../utils'

export const CaseExperts: React.FC = () => {
    const { caseData, piiUnlocked } = useCase()
    const { grantExpertAccess, revokeExpertAccess } = useCaseActions()
    const { expertAccess, refreshInvestigationData } = useCaseInvestigation()

    const [status, setStatus] = useState('')
    const [expertDraft, setExpertDraft] = useState({
        expert_email: '',
        expert_name: '',
        organization: '',
        reason: '',
    })

    const handleGrantAccess = async () => {
        if (!expertDraft.expert_email) {
            setStatus('Email required.')
            return
        }
        setStatus('Granting access...')
        const res = await grantExpertAccess({
            expert_email: expertDraft.expert_email,
            expert_name: expertDraft.expert_name || null,
            organization: expertDraft.organization || null,
            reason: expertDraft.reason || null,
        })

        if (res.success) {
            setExpertDraft({ expert_email: '', expert_name: '', organization: '', reason: '' })
            setStatus('Access granted.')
            refreshInvestigationData() // Reload list
        } else {
            setStatus(res.message || 'Error granting access.')
        }
    }

    const handleRevokeAccess = async (accessId: string) => {
        setStatus('Revoking...')
        const res = await revokeExpertAccess(accessId)
        if (res.success) {
            setStatus('Access revoked.')
            refreshInvestigationData()
        } else {
            setStatus(res.message || 'Error revoking access.')
        }
    }

    if (!caseData) return null
    const canEditPII = piiUnlocked && !caseData.is_anonymized

    return (
        <div className="case-flow-card">
            <h3>External expert access (SOS)</h3>
            <p className="case-flow-help">Grant 48-hour access to an external expert or partner firm with full audit logging.</p>

            {status && <div className="case-flow-status">{status}</div>}

            <label className="case-flow-label">
                Expert email
                <input
                    type="email"
                    value={expertDraft.expert_email}
                    onChange={(e) => setExpertDraft({ ...expertDraft, expert_email: e.target.value })}
                    disabled={!canEditPII}
                />
            </label>
            <label className="case-flow-label">
                Expert name
                <input
                    type="text"
                    value={expertDraft.expert_name}
                    onChange={(e) => setExpertDraft({ ...expertDraft, expert_name: e.target.value })}
                    disabled={!canEditPII}
                />
            </label>
            <label className="case-flow-label">
                Organization
                <input
                    type="text"
                    value={expertDraft.organization}
                    onChange={(e) => setExpertDraft({ ...expertDraft, organization: e.target.value })}
                    disabled={!canEditPII}
                />
            </label>
            <label className="case-flow-label">
                Reason / scope
                <textarea
                    value={expertDraft.reason}
                    onChange={(e) => setExpertDraft({ ...expertDraft, reason: e.target.value })}
                    disabled={!canEditPII}
                />
            </label>
            <button className="case-flow-btn outline" onClick={handleGrantAccess} disabled={!canEditPII}>
                Grant 48h access
            </button>

            {expertAccess.length === 0 ? (
                <div className="case-flow-muted">No external experts granted access yet.</div>
            ) : (
                expertAccess.map((expert) => (
                    <div key={expert.access_id} className="case-flow-note">
                        <div className="case-flow-muted">
                            {maskText(expert.expert_email, 'Hidden', piiUnlocked)} · {expert.status}
                        </div>
                        {(expert.expert_name || expert.organization) && (
                            <div>
                                {expert.expert_name ? maskText(expert.expert_name, 'External expert', piiUnlocked) : 'External expert'}
                                {expert.organization ? ` · ${maskText(expert.organization, 'Hidden', piiUnlocked)}` : ''}
                            </div>
                        )}
                        <div className="case-flow-muted">
                            Expires {new Date(expert.expires_at).toLocaleString()}
                        </div>
                        {expert.reason && <div className="case-flow-muted">Scope: {maskText(expert.reason, 'Hidden', piiUnlocked)}</div>}
                        {expert.status === 'active' && (
                            <button
                                className="case-flow-btn outline small"
                                onClick={() => handleRevokeAccess(expert.access_id)}
                                disabled={caseData.is_anonymized}
                            >
                                Revoke access
                            </button>
                        )}
                    </div>
                ))
            )}
        </div>
    )
}
