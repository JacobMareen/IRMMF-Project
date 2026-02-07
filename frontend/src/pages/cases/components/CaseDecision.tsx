import React, { useState, useEffect, useMemo } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { CaseSeriousCause } from './CaseSeriousCause'
import { normalizeName } from '../utils'

// Types for Consistency Check (could be in types.ts)
interface ConsistencyResult {
    sample_size: number
    jurisdiction: string
    playbook_key?: string
    outcomes: { outcome: string; count: number; percent: number }[]
    recommendation: string
    warning?: string
}

export const CaseDecision: React.FC = () => {
    const { caseData, piiUnlocked } = useCase()
    const {
        saveGate, recordDecision, draftDecisionSummary,
        runConsistencyCheck, approveErasure, executeErasure
    } = useCaseActions()

    // Local state
    const [status, setStatus] = useState('')
    const [showGuidance, setShowGuidance] = useState(false)

    const [legalGate, setLegalGate] = useState({
        approved_at: '',
        approval_note: '',
    })

    const [decisionDraft, setDecisionDraft] = useState({
        outcome: '',
        summary: '',
        overrideReason: '',
    })

    const [consistency, setConsistency] = useState<ConsistencyResult | null>(null)

    // Load initial state
    useEffect(() => {
        if (!caseData) return

        // Legal gate
        const lGate = caseData.gates.find(g => g.gate_key === 'legal')
        if (lGate?.data) {
            setLegalGate({
                approved_at: (lGate.data.approved_at as string) || '',
                approval_note: (lGate.data.approval_note as string) || '',
            })
        }

        // Decision outcome
        if (caseData.outcome) {
            setDecisionDraft(prev => ({
                ...prev,
                outcome: caseData.outcome?.outcome || '',
                summary: caseData.outcome?.summary || '',
                overrideReason: caseData.outcome?.role_separation_override || '',
            }))
        }
    }, [caseData])

    // Role separation logic
    const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
    const roleSeparationConflicts = useMemo(() => {
        if (!caseData) return []
        const conflicts: string[] = []

        // Credentialing gate for investigator
        const credGate = caseData.gates.find(g => g.gate_key === 'credentialing')
        const investigatorName = credGate?.data?.investigator_name as string || ''

        // Serious cause decision maker (if applicable)
        const decisionMakerName = caseData.serious_cause?.decision_maker || ''

        if (normalizeName(decisionMakerName) && normalizeName(decisionMakerName) === normalizeName(investigatorName)) {
            conflicts.push('Decision maker matches investigator')
        }

        if (normalizeName(investigatorName) && normalizeName(investigatorName) === normalizeName(currentUser)) {
            conflicts.push('Investigator cannot record the decision')
        }

        return conflicts
    }, [caseData, currentUser])

    const handleSaveLegal = async () => {
        setStatus('Saving legal...')
        const res = await saveGate('legal', {
            approved_at: legalGate.approved_at || null,
            approval_note: legalGate.approval_note || null,
        })
        if (res.success) setStatus('Legal gate saved.')
        else setStatus(res.message || 'Error.')
    }

    const handleRunConsistency = async () => {
        setStatus('Running consistency check...')
        const res = await runConsistencyCheck()
        if (res.success && res.data) {
            setConsistency(res.data)
            setStatus('Consistency check complete.')
        } else {
            setStatus(res.message || 'Error.')
        }
    }

    const handleDraftSummary = async () => {
        setStatus('Drafting summary...')
        const res = await draftDecisionSummary()
        if (res.success && res.summary) {
            setDecisionDraft(prev => ({ ...prev, summary: res.summary }))
            setStatus('Drafted.')
        } else {
            setStatus(res.message || 'Error.')
        }
    }

    const handleRecordDecision = async () => {
        if (!decisionDraft.outcome) {
            setStatus('Outcome required.')
            return
        }
        setStatus('Recording decision...')
        const res = await recordDecision(
            decisionDraft.outcome,
            decisionDraft.summary,
            decisionDraft.overrideReason
        )
        if (res.success) setStatus('Decision recorded.')
        else setStatus(res.message || 'Error.')
    }

    const handleApproveErasure = async () => {
        const res = await approveErasure()
        if (res.success) setStatus('Erasure approved.')
        else setStatus(res.message || 'Error.')
    }

    const handleExecuteErasure = async () => {
        const res = await executeErasure()
        if (res.success) setStatus('Erasure executed.')
        else setStatus(res.message || 'Error.')
    }

    if (!caseData) return null
    const isAnonymized = caseData.is_anonymized

    return (
        <div>
            <div className="case-flow-step-header">
                <div>
                    <h2>Decision & Closure</h2>
                    <p className="case-flow-help">Formalize the outcome and ensure data minimization.</p>
                </div>
                <button className="case-flow-info" onClick={() => setShowGuidance(!showGuidance)} type="button">i</button>
            </div>

            {showGuidance && (
                <div className="case-flow-guidance">
                    <h4>Guidance</h4>
                    <ul>
                        <li>Sanctions must be proportionate and consistent with precedent.</li>
                        <li>Legal approval is mandatory for termination.</li>
                        <li>Ensure role separation: Investigator ≠ Decision Maker.</li>
                    </ul>
                </div>
            )}

            {status && <div className="case-flow-status">{status}</div>}

            <div className="case-flow-grid">
                {/* Legal Approval */}
                <div className="case-flow-card">
                    <h3>Legal approval</h3>
                    <p className="case-flow-help">Required for High impact cases or termination.</p>
                    <label className="case-flow-label">
                        Approved at
                        <input
                            type="datetime-local"
                            value={legalGate.approved_at}
                            onChange={(e) => setLegalGate({ ...legalGate, approved_at: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>
                    <label className="case-flow-label">
                        Approval note
                        <textarea
                            value={legalGate.approval_note}
                            onChange={(e) => setLegalGate({ ...legalGate, approval_note: e.target.value })}
                            placeholder="Optional context for legal approval."
                            disabled={isAnonymized}
                        />
                    </label>
                    <button className="case-flow-btn outline" onClick={handleSaveLegal} disabled={isAnonymized}>
                        Record legal approval
                    </button>
                    {caseData.gates.find((g) => g.gate_key === 'legal')?.completed_by && (
                        <div className="case-flow-muted">
                            Approved by {caseData.gates.find((g) => g.gate_key === 'legal')?.completed_by}
                        </div>
                    )}
                </div>

                {/* Consistency Check */}
                <div className="case-flow-card">
                    <h3>Consistency check</h3>
                    <p className="case-flow-help">Compare this decision against historical outcomes.</p>
                    <button className="case-flow-btn outline" onClick={handleRunConsistency}>
                        Run consistency check
                    </button>
                    {consistency ? (
                        <div className="case-flow-meta">
                            <div>Sample size: {consistency.sample_size}</div>
                            <div>Jurisdiction: {consistency.jurisdiction}</div>
                            {consistency.playbook_key && <div>Playbook: {consistency.playbook_key}</div>}
                            <div className="case-flow-divider" />
                            {consistency.outcomes.length === 0 ? (
                                <div className="case-flow-muted">No comparable outcomes.</div>
                            ) : (
                                consistency.outcomes.map((row) => (
                                    <div key={`${row.outcome}-${row.count}`} className="case-flow-row">
                                        <span>{row.outcome}</span>
                                        <span>{row.count} ({row.percent}%)</span>
                                    </div>
                                ))
                            )}
                            <div className="case-flow-muted">{consistency.recommendation}</div>
                            {consistency.warning && <div className="case-flow-warning">{consistency.warning}</div>}
                        </div>
                    ) : (
                        <div className="case-flow-muted">No consistency check run yet.</div>
                    )}
                </div>

                {/* Serious Cause */}
                <CaseSeriousCause />
            </div>

            <div className="case-flow-card full-width">
                <h3>Final Decision</h3>

                {roleSeparationConflicts.length > 0 && (
                    <div className="case-flow-warning">
                        <strong>Role Separation Conflicts:</strong>
                        <ul>
                            {roleSeparationConflicts.map((c, i) => <li key={i}>{c}</li>)}
                        </ul>
                        <label className="case-flow-label">
                            Override reason (required to proceed)
                            <input
                                type="text"
                                value={decisionDraft.overrideReason}
                                onChange={(e) => setDecisionDraft({ ...decisionDraft, overrideReason: e.target.value })}
                                disabled={isAnonymized}
                            />
                        </label>
                    </div>
                )}

                <label className="case-flow-label">
                    Outcome
                    <select
                        value={decisionDraft.outcome}
                        onChange={(e) => setDecisionDraft({ ...decisionDraft, outcome: e.target.value })}
                        disabled={isAnonymized || !!caseData.outcome}
                    >
                        <option value="">Select Outcome</option>
                        <option value="NO_SANCTION">No Sanction / Unsubstantiated</option>
                        <option value="WARNING">Written Warning</option>
                        <option value="PIP">Performance Improvement Plan</option>
                        <option value="TERMINATION">Termination</option>
                    </select>
                </label>

                <label className="case-flow-label">
                    Executive Summary
                    <textarea
                        value={decisionDraft.summary}
                        onChange={(e) => setDecisionDraft({ ...decisionDraft, summary: e.target.value })}
                        disabled={isAnonymized}
                        rows={5}
                    />
                </label>

                <div className="case-flow-inline">
                    <button className="case-flow-btn outline" onClick={handleDraftSummary} disabled={isAnonymized}>
                        Auto-draft Summary
                    </button>
                    <button
                        className="case-flow-btn outline"
                        onClick={handleRecordDecision}
                        disabled={isAnonymized || !!caseData.outcome || (roleSeparationConflicts.length > 0 && !decisionDraft.overrideReason)}
                    >
                        Record Decision
                    </button>
                </div>

                {caseData.outcome && (
                    <div className="case-flow-success">
                        Decision recorded by {caseData.outcome.decision_maker} on {new Date(caseData.outcome.decision_date).toLocaleDateString()}
                    </div>
                )}
            </div>

            {/* Erasure / Closure */}
            {(caseData.outcome?.outcome === 'NO_SANCTION' || caseData.status === 'closed') && (
                <div className="case-flow-card full-width">
                    <h3>Case Erasure (GDPR)</h3>
                    <p className="case-flow-help">If unsubstantiated, data must be erased/anonymized immediately.</p>

                    <div className="case-flow-inline">
                        {caseData.erasure_approved_at ? (
                            <div className="case-flow-meta">Erasure approved at {new Date(caseData.erasure_approved_at).toLocaleString()}</div>
                        ) : (
                            <button className="case-flow-btn outline" onClick={handleApproveErasure} disabled={isAnonymized}>
                                Approve Erasure
                            </button>
                        )}

                        <button
                            className="case-flow-btn outline"
                            onClick={handleExecuteErasure}
                            disabled={isAnonymized || !caseData.erasure_approved_at}
                        >
                            Execute Erasure / Anonymization
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
