import React, { useState, useEffect, useMemo } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'

export const CaseWorksCouncil: React.FC = () => {
    const { caseData } = useCase()
    const { saveGate } = useCaseActions()

    const [status, setStatus] = useState('')

    const [worksCouncilGate, setWorksCouncilGate] = useState({
        monitoring: false,
        approval_document_uri: '',
        approval_received_at: '',
        approval_notes: '',
    })

    useEffect(() => {
        if (!caseData) return
        const gate = caseData.gates.find(g => g.gate_key === 'works-council')
        if (gate?.data) {
            setWorksCouncilGate({
                monitoring: !!gate.data.monitoring,
                approval_document_uri: (gate.data.approval_document_uri as string) || '',
                approval_received_at: (gate.data.approval_received_at as string) || '',
                approval_notes: (gate.data.approval_notes as string) || '',
            })
        }
    }, [caseData])

    const isWorksCouncilJurisdiction = useMemo(() => {
        if (!caseData) return false
        const j = caseData.jurisdiction
        return j === 'Germany' || j === 'France' || (j === 'Other' && ['germany', 'france', 'de', 'fr'].includes((caseData.jurisdiction_other || '').toLowerCase()))
    }, [caseData])

    const handleSave = async () => {
        setStatus('Saving...')
        const res = await saveGate('works-council', {
            monitoring: !!worksCouncilGate.monitoring,
            approval_document_uri: worksCouncilGate.approval_document_uri || null,
            approval_received_at: worksCouncilGate.approval_received_at || null,
            approval_notes: worksCouncilGate.approval_notes || null,
        })

        if (res.success) {
            setStatus('Saved Works Council status.')
        } else {
            setStatus(res.message || 'Error saving.')
        }
    }

    if (!caseData) return null
    const isAnonymized = caseData.is_anonymized

    return (
        <div className="case-flow-card">
            <h3>Works Council airlock (DE/FR)</h3>
            <p className="case-flow-help">If monitoring is required, evidence collection pauses until approval is documented.</p>

            {!isWorksCouncilJurisdiction && (
                <div className="case-flow-muted">Applicable for Germany/France monitoring cases.</div>
            )}

            {status && <div className="case-flow-status">{status}</div>}

            <label className="case-flow-label">
                <input
                    type="checkbox"
                    checked={worksCouncilGate.monitoring}
                    onChange={(e) => setWorksCouncilGate({ ...worksCouncilGate, monitoring: e.target.checked })}
                    disabled={isAnonymized}
                />
                Monitoring requires Works Council approval
            </label>

            <label className="case-flow-label">
                Approval document URI
                <input
                    type="text"
                    value={worksCouncilGate.approval_document_uri}
                    onChange={(e) => setWorksCouncilGate({ ...worksCouncilGate, approval_document_uri: e.target.value })}
                    placeholder="Link to approval document"
                    disabled={isAnonymized}
                />
            </label>

            <label className="case-flow-label">
                Approval received at
                <input
                    type="datetime-local"
                    value={worksCouncilGate.approval_received_at}
                    onChange={(e) => setWorksCouncilGate({ ...worksCouncilGate, approval_received_at: e.target.value })}
                    disabled={isAnonymized}
                />
            </label>

            <label className="case-flow-label">
                Notes
                <textarea
                    value={worksCouncilGate.approval_notes}
                    onChange={(e) => setWorksCouncilGate({ ...worksCouncilGate, approval_notes: e.target.value })}
                    disabled={isAnonymized}
                />
            </label>

            <button className="case-flow-btn outline" onClick={handleSave} disabled={isAnonymized}>
                Save Works Council status
            </button>

            {caseData.evidence_locked && (
                <div className="case-flow-warning">Evidence folder locked until approval is recorded.</div>
            )}
        </div>
    )
}
