import React, { useState } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { useCaseInvestigation } from '../hooks/useCaseInvestigation'

export const CaseFlags: React.FC = () => {
    const { caseData } = useCase()
    const { resolveFlag } = useCaseActions()
    const { flags, refreshInvestigationData } = useCaseInvestigation()

    const [status, setStatus] = useState('')

    const handleResolve = async (id: number) => {
        setStatus('Resolving...')
        const res = await resolveFlag(id)
        if (res.success) {
            setStatus('Resolved.')
            refreshInvestigationData()
        } else {
            setStatus(res.message || 'Error.')
        }
    }

    if (!caseData) return null

    return (
        <div className="case-flow-card">
            <h3>Prohibited data flags</h3>
            <p className="case-flow-help">Resolve flagged keywords before finalizing reports.</p>
            {status && <div className="case-flow-status">{status}</div>}

            {flags.length === 0 ? (
                <div className="case-flow-muted">No flags detected.</div>
            ) : (
                flags.map((flag) => (
                    <div key={flag.id} className="case-flow-row">
                        <div>
                            <div className="case-flow-muted">
                                {flag.flag_type} · {flag.status}
                            </div>
                            <div>{flag.terms.join(', ')}</div>
                        </div>
                        {flag.status === 'open' ? (
                            <button className="case-flow-btn outline" onClick={() => handleResolve(flag.id)}>
                                Resolve
                            </button>
                        ) : (
                            <span className="case-flow-tag">Resolved</span>
                        )}
                    </div>
                ))
            )}
        </div>
    )
}
