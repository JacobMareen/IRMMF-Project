import React, { useState } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'

export const CaseEvidenceRegister: React.FC = () => {
    const { caseData, piiUnlocked } = useCase()
    const { addEvidence } = useCaseActions()

    const [status, setStatus] = useState('')
    const [evidenceDraft, setEvidenceDraft] = useState({ label: '', uri: '' })
    const [file, setFile] = useState<File | null>(null)

    // Derived state
    const canEditPII = piiUnlocked && !caseData?.is_anonymized && !caseData?.evidence_locked

    const handleAddEvidence = async () => {
        if (!evidenceDraft.label.trim()) {
            setStatus('Label required.')
            return
        }
        if (!file && !evidenceDraft.uri.trim()) {
            setStatus('File or URI required.')
            return
        }

        setStatus('Uploading...')
        const res = await addEvidence(evidenceDraft.label, file, evidenceDraft.uri) // Correct signature

        if (res.success) {
            setEvidenceDraft({ label: '', uri: '' })
            setFile(null)
            setStatus('Evidence item added.')
            // Reset file input manually if needed, but managing via state is hard for file inputs usually.
            // A key reset works best.
        } else {
            setStatus(res.message || 'Error adding evidence.')
        }
    }

    if (!caseData) return null

    return (
        <div className="case-flow-card">
            <h3>Evidence register</h3>
            <p className="case-flow-help">Log every piece of evidence with its system of origin.</p>

            {caseData.evidence_locked && (
                <div className="case-flow-warning">Evidence folder locked pending Works Council approval.</div>
            )}

            {status && <div className="case-flow-status">{status}</div>}

            <label className="case-flow-label">
                Label
                <input
                    type="text"
                    value={evidenceDraft.label}
                    onChange={(e) => setEvidenceDraft({ ...evidenceDraft, label: e.target.value })}
                    disabled={!canEditPII}
                />
            </label>

            <label className="case-flow-label">
                Upload file
                <input
                    key={file ? 'has-file' : 'no-file'} // simplistic reset
                    type="file"
                    onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                    disabled={!canEditPII}
                />
            </label>

            <div className="case-flow-muted">OR</div>

            <label className="case-flow-label">
                Link URI (e.g. Splunk query)
                <input
                    type="text"
                    value={evidenceDraft.uri}
                    onChange={(e) => setEvidenceDraft({ ...evidenceDraft, uri: e.target.value })}
                    placeholder="https://..."
                    disabled={!canEditPII}
                />
            </label>

            <button className="case-flow-btn outline" onClick={handleAddEvidence} disabled={!canEditPII}>
                Add evidence
            </button>

            {caseData.evidence.length === 0 ? (
                <div className="case-flow-muted">No evidence logged.</div>
            ) : (
                <div className="case-flow-list">
                    {caseData.evidence.map((item) => (
                        <div key={item.id} className="case-flow-list-item">
                            <div className="case-flow-list-content">
                                <strong>{item.label}</strong>
                                <div className="case-flow-muted">
                                    {item.filename ? `File: ${item.filename}` : `URI: ${item.location_uri}`}
                                </div>
                                <div className="case-flow-meta">
                                    Logged {new Date(item.created_at).toLocaleString()} by {item.created_by}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
