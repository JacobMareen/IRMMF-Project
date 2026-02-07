import React, { useState, useEffect } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'

export const CaseAdversarial: React.FC = () => {
    const { caseData } = useCase()
    const { saveGate, generateDocument } = useCaseActions()

    const [status, setStatus] = useState('')
    const [showGuidance, setShowGuidance] = useState(false)

    const [adversarialGate, setAdversarialGate] = useState({
        invitation_sent: false,
        invitation_date: '',
        rights_acknowledged: false,
        representative_present: '',
        interview_summary: '',
    })

    useEffect(() => {
        if (!caseData) return
        const gate = caseData.gates.find(g => g.gate_key === 'adversarial')
        if (gate?.data) {
            setAdversarialGate({
                invitation_sent: !!gate.data.invitation_sent,
                invitation_date: (gate.data.invitation_date as string) || '',
                rights_acknowledged: !!gate.data.rights_acknowledged,
                representative_present: (gate.data.representative_present as string) || '',
                interview_summary: (gate.data.interview_summary as string) || '',
            })
        }
    }, [caseData])

    const handleSave = async () => {
        setStatus('Saving...')
        const res = await saveGate('adversarial', {
            invitation_sent: !!adversarialGate.invitation_sent,
            invitation_date: adversarialGate.invitation_date || null,
            rights_acknowledged: !!adversarialGate.rights_acknowledged,
            representative_present: adversarialGate.representative_present || null,
            interview_summary: adversarialGate.interview_summary,
        })

        if (res.success) {
            setStatus('Saved.')
        } else {
            setStatus(res.message || 'Error saving.')
        }
    }

    const handleGenerateInvitation = async () => {
        setStatus('Generating invitation...')
        const res = await generateDocument('INTERVIEW_INVITATION')
        if (res.success) setStatus('Invitation generated.')
        else setStatus(res.message || 'Error generating.')
    }

    if (!caseData) return null
    const isAnonymized = caseData.is_anonymized

    return (
        <div>
            <div className="case-flow-step-header">
                <div>
                    <h2>Adversarial Debate</h2>
                    <p className="case-flow-help">Document the right to be heard before recommending any sanction.</p>
                </div>
                <button className="case-flow-info" onClick={() => setShowGuidance(!showGuidance)} type="button">i</button>
            </div>

            {showGuidance && (
                <div className="case-flow-guidance">
                    <h4>Guidance</h4>
                    <ul>
                        <li>Provide written notice and record whether assistance was requested.</li>
                        <li>Summaries should reflect both allegations and the employee response.</li>
                    </ul>
                </div>
            )}

            {status && <div className="case-flow-status">{status}</div>}

            <div className="case-flow-card">
                <div className="case-flow-muted">
                    Gate status: {caseData.gates.find((g) => g.gate_key === 'adversarial')?.status || 'pending'}
                </div>

                <label className="case-flow-label">
                    <input
                        type="checkbox"
                        checked={adversarialGate.invitation_sent}
                        onChange={(e) => setAdversarialGate({ ...adversarialGate, invitation_sent: e.target.checked })}
                        disabled={isAnonymized}
                    />
                    Invitation sent
                </label>

                <label className="case-flow-label">
                    Invitation date
                    <input
                        type="date"
                        value={adversarialGate.invitation_date}
                        onChange={(e) => setAdversarialGate({ ...adversarialGate, invitation_date: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <label className="case-flow-label">
                    <input
                        type="checkbox"
                        checked={adversarialGate.rights_acknowledged}
                        onChange={(e) => setAdversarialGate({ ...adversarialGate, rights_acknowledged: e.target.checked })}
                        disabled={isAnonymized}
                    />
                    Rights acknowledged
                </label>

                <label className="case-flow-label">
                    Representative present
                    <input
                        type="text"
                        value={adversarialGate.representative_present}
                        onChange={(e) => setAdversarialGate({ ...adversarialGate, representative_present: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <label className="case-flow-label">
                    Interview summary
                    <textarea
                        value={adversarialGate.interview_summary}
                        onChange={(e) => setAdversarialGate({ ...adversarialGate, interview_summary: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <div className="case-flow-inline">
                    <button
                        className="case-flow-btn outline"
                        onClick={handleSave}
                        disabled={isAnonymized}
                    >
                        Save gate
                    </button>
                    <button className="case-flow-btn outline" onClick={handleGenerateInvitation} disabled={isAnonymized}>
                        Generate Invitation
                    </button>
                </div>
            </div>
        </div>
    )
}
