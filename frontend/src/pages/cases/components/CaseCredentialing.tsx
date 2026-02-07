import React, { useState, useEffect, useMemo } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { INVESTIGATOR_ROLE_OPTIONS } from '../constants'

export const CaseCredentialing: React.FC = () => {
    const { caseData } = useCase()
    const { saveGate } = useCaseActions()

    const [status, setStatus] = useState('')
    const [showGuidance, setShowGuidance] = useState(false)
    const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])

    const [credentialingGate, setCredentialingGate] = useState({
        investigator_name: '',
        investigator_role: '',
        licensed: false,
        license_id: '',
        conflict_check_passed: false,
        conflict_override_reason: '',
        authorizer: '',
        authorization_date: '',
    })

    useEffect(() => {
        if (!caseData) return
        const gate = caseData.gates.find(g => g.gate_key === 'credentialing')
        if (gate?.data) {
            setCredentialingGate({
                investigator_name: (gate.data.investigator_name as string) || '',
                investigator_role: (gate.data.investigator_role as string) || '',
                licensed: !!gate.data.licensed,
                license_id: (gate.data.license_id as string) || '',
                conflict_check_passed: !!gate.data.conflict_check_passed,
                conflict_override_reason: (gate.data.conflict_override_reason as string) || '',
                authorizer: (gate.data.authorizer as string) || '',
                authorization_date: (gate.data.authorization_date as string) || '',
            })
        }
    }, [caseData])

    // Auto-fill currentUser if empty
    useEffect(() => {
        if (currentUser && !credentialingGate.investigator_name && !caseData?.gates.find(g => g.gate_key === 'credentialing')?.data?.investigator_name) {
            setCredentialingGate(prev => ({ ...prev, investigator_name: currentUser }))
        }
    }, [currentUser, credentialingGate.investigator_name, caseData])

    const handleSave = async () => {
        if (!credentialingGate.investigator_name.trim() || !credentialingGate.investigator_role.trim()) {
            setStatus('Credentialing gate needs investigator name and role.')
            return
        }
        setStatus('Saving...')
        const res = await saveGate('credentialing', {
            investigator_name: credentialingGate.investigator_name,
            investigator_role: credentialingGate.investigator_role,
            licensed: !!credentialingGate.licensed,
            license_id: credentialingGate.license_id || null,
            conflict_check_passed: !!credentialingGate.conflict_check_passed,
            conflict_override_reason: credentialingGate.conflict_override_reason || null,
            authorizer: credentialingGate.authorizer || null,
            authorization_date: credentialingGate.authorization_date || null,
        })

        if (res.success) {
            setStatus('Saved.')
        } else {
            setStatus(res.message || 'Error saving.')
        }
    }

    if (!caseData) return null
    const isAnonymized = caseData.is_anonymized

    return (
        <div>
            <div className="case-flow-step-header">
                <div>
                    <h2>Credentialing</h2>
                    <p className="case-flow-help">Confirm investigator eligibility, licensing, and conflicts.</p>
                </div>
                <button className="case-flow-info" onClick={() => setShowGuidance(!showGuidance)} type="button">i</button>
            </div>

            {showGuidance && (
                <div className="case-flow-guidance">
                    <h4>Guidance</h4>
                    <ul>
                        <li>Licensed investigators are required for systematic investigations.</li>
                        <li>Document who authorized the assignment and when.</li>
                        <li>Flag conflicts early (reporting line, personal ties, prior involvement).</li>
                    </ul>
                </div>
            )}

            {status && <div className="case-flow-status">{status}</div>}

            <div className="case-flow-card">
                <div className="case-flow-muted">Gate status: {caseData.gates.find((g) => g.gate_key === 'credentialing')?.status || 'pending'}</div>

                {!currentUser && (
                    <div className="case-flow-warning">
                        Investigator profile not loaded. Profile completion will be required once authentication is enabled.
                    </div>
                )}

                <label className="case-flow-label">
                    Investigator name
                    <input
                        type="text"
                        value={credentialingGate.investigator_name}
                        onChange={(e) => setCredentialingGate({ ...credentialingGate, investigator_name: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <button
                    className="case-flow-btn outline"
                    onClick={() => {
                        if (!currentUser) return
                        setCredentialingGate({ ...credentialingGate, investigator_name: currentUser })
                    }}
                    disabled={!currentUser || isAnonymized}
                >
                    Use my profile
                </button>

                <label className="case-flow-label">
                    Investigator role
                    <input
                        list="investigator-roles"
                        value={credentialingGate.investigator_role}
                        onChange={(e) => setCredentialingGate({ ...credentialingGate, investigator_role: e.target.value })}
                        disabled={isAnonymized}
                    />
                    <datalist id="investigator-roles">
                        {INVESTIGATOR_ROLE_OPTIONS.map((option) => (
                            <option key={option} value={option} />
                        ))}
                    </datalist>
                </label>

                <label className="case-flow-label">
                    <input
                        type="checkbox"
                        checked={credentialingGate.licensed}
                        onChange={(e) => setCredentialingGate({ ...credentialingGate, licensed: e.target.checked })}
                        disabled={isAnonymized}
                    />
                    Licensed investigator
                </label>

                <label className="case-flow-label">
                    License ID
                    <input
                        type="text"
                        value={credentialingGate.license_id}
                        onChange={(e) => setCredentialingGate({ ...credentialingGate, license_id: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <label className="case-flow-label">
                    <input
                        type="checkbox"
                        checked={credentialingGate.conflict_check_passed}
                        onChange={(e) =>
                            setCredentialingGate({ ...credentialingGate, conflict_check_passed: e.target.checked })
                        }
                        disabled={isAnonymized}
                    />
                    Conflict check passed
                </label>

                <label className="case-flow-label">
                    Conflict override reason (if needed)
                    <textarea
                        value={credentialingGate.conflict_override_reason}
                        onChange={(e) =>
                            setCredentialingGate({ ...credentialingGate, conflict_override_reason: e.target.value })
                        }
                        placeholder="Explain why an override is permitted."
                        disabled={isAnonymized}
                    />
                </label>

                <label className="case-flow-label">
                    Authorizer
                    <input
                        type="text"
                        value={credentialingGate.authorizer}
                        onChange={(e) => setCredentialingGate({ ...credentialingGate, authorizer: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <label className="case-flow-label">
                    Authorization date
                    <input
                        type="date"
                        value={credentialingGate.authorization_date}
                        onChange={(e) =>
                            setCredentialingGate({ ...credentialingGate, authorization_date: e.target.value })
                        }
                        disabled={isAnonymized}
                    />
                </label>

                <button className="case-flow-btn outline" onClick={handleSave} disabled={isAnonymized}>
                    Save gate
                </button>
            </div>
        </div>
    )
}
