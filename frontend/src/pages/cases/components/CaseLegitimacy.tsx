import React, { useState, useEffect } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { LEGAL_BASIS_OPTIONS } from '../constants'

export const CaseLegitimacy: React.FC = () => {
    const { caseData } = useCase()
    const { saveGate } = useCaseActions()

    const [status, setStatus] = useState('')
    const [showGuidance, setShowGuidance] = useState(false)

    const [legitimacyGate, setLegitimacyGate] = useState({
        legal_basis: '',
        legal_basis_other: '',
        trigger_summary: '',
        proportionality_confirmed: false,
        less_intrusive_steps: '',
        mandate_owner: '',
        mandate_date: '',
    })

    useEffect(() => {
        if (!caseData) return
        const gate = caseData.gates.find(g => g.gate_key === 'legitimacy')
        if (gate?.data) {
            const legalBasisValue = (gate.data.legal_basis as string) || ''
            const match = LEGAL_BASIS_OPTIONS.some(o => o.value === legalBasisValue)
            setLegitimacyGate({
                legal_basis: legalBasisValue ? (match ? legalBasisValue : 'Other') : '',
                legal_basis_other: match ? '' : legalBasisValue,
                trigger_summary: (gate.data.trigger_summary as string) || '',
                proportionality_confirmed: !!gate.data.proportionality_confirmed,
                less_intrusive_steps: (gate.data.less_intrusive_steps as string) || '',
                mandate_owner: (gate.data.mandate_owner as string) || '',
                mandate_date: (gate.data.mandate_date as string) || '',
            })
        }
    }, [caseData])

    const handleSave = async () => {
        setStatus('Saving...')
        const payload = {
            legal_basis: legitimacyGate.legal_basis === 'Other' ? legitimacyGate.legal_basis_other : legitimacyGate.legal_basis,
            trigger_summary: legitimacyGate.trigger_summary,
            proportionality_confirmed: legitimacyGate.proportionality_confirmed,
            less_intrusive_steps: legitimacyGate.less_intrusive_steps,
            mandate_owner: legitimacyGate.mandate_owner,
            mandate_date: legitimacyGate.mandate_date,
        }

        const res = await saveGate('legitimacy', payload)
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
                    <h2>Legitimacy & Proportionality</h2>
                    <p className="case-flow-help">Define legal basis, proportionality, and mandate before proceeding.</p>
                </div>
                <button className="case-flow-info" onClick={() => setShowGuidance(!showGuidance)} type="button">i</button>
            </div>

            {showGuidance && (
                <div className="case-flow-guidance">
                    <h4>Guidance</h4>
                    <ul>
                        <li>Legal basis must be specific enough to justify the scope of data reviewed.</li>
                        <li>Document less-intrusive steps you tried or ruled out.</li>
                        <li>Mandate owner and date should map to actual approval authority.</li>
                    </ul>
                </div>
            )}

            {status && <div className="case-flow-status">{status}</div>}

            <div className="case-flow-card">
                <div className="case-flow-muted">Gate status: {caseData.gates.find((g) => g.gate_key === 'legitimacy')?.status || 'pending'}</div>

                <label className="case-flow-label">
                    Legal basis
                    <select
                        value={legitimacyGate.legal_basis}
                        onChange={(e) =>
                            setLegitimacyGate({ ...legitimacyGate, legal_basis: e.target.value, legal_basis_other: '' })
                        }
                        disabled={isAnonymized}
                    >
                        <option value="">Select a basis</option>
                        {LEGAL_BASIS_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                    </select>
                </label>

                {legitimacyGate.legal_basis === 'Other' && (
                    <label className="case-flow-label">
                        Specify legal basis
                        <input
                            type="text"
                            value={legitimacyGate.legal_basis_other}
                            onChange={(e) => setLegitimacyGate({ ...legitimacyGate, legal_basis_other: e.target.value })}
                            placeholder="Describe the basis"
                            disabled={isAnonymized}
                        />
                    </label>
                )}

                <label className="case-flow-label">
                    Trigger summary
                    <textarea
                        value={legitimacyGate.trigger_summary}
                        onChange={(e) => setLegitimacyGate({ ...legitimacyGate, trigger_summary: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <label className="case-flow-label">
                    <input
                        type="checkbox"
                        checked={legitimacyGate.proportionality_confirmed}
                        onChange={(e) =>
                            setLegitimacyGate({ ...legitimacyGate, proportionality_confirmed: e.target.checked })
                        }
                        disabled={isAnonymized}
                    />
                    Proportionality confirmed
                </label>

                <label className="case-flow-label">
                    Less intrusive steps
                    <input
                        type="text"
                        value={legitimacyGate.less_intrusive_steps}
                        onChange={(e) => setLegitimacyGate({ ...legitimacyGate, less_intrusive_steps: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <label className="case-flow-label">
                    Mandate owner
                    <input
                        type="text"
                        value={legitimacyGate.mandate_owner}
                        onChange={(e) => setLegitimacyGate({ ...legitimacyGate, mandate_owner: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <label className="case-flow-label">
                    Mandate date
                    <input
                        type="date"
                        value={legitimacyGate.mandate_date}
                        onChange={(e) => setLegitimacyGate({ ...legitimacyGate, mandate_date: e.target.value })}
                        disabled={isAnonymized}
                    />
                </label>

                <button className="case-flow-btn outline" onClick={handleSave} disabled={isAnonymized}>
                    Save Gate
                </button>
            </div>
        </div>
    )
}
