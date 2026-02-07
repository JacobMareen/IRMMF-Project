import React, { useState, useEffect, useMemo } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { JURISDICTION_OPTIONS, TRIAGE_IMPACT_LEVELS, TRIAGE_PROBABILITY_LEVELS, TRIAGE_RISK_LEVELS, DATA_SENSITIVITY_OPTIONS, TRIAGE_CONFIDENCE_OPTIONS, TRIAGE_OUTCOME_OPTIONS } from '../constants'
import { computeRiskScore, maskFieldValue } from '../utils'

export const CaseIntake: React.FC = () => {
    const { caseData, piiUnlocked } = useCase()
    const { updateCase, saveGate } = useCaseActions()

    const [status, setStatus] = useState('')
    const [showGuidance, setShowGuidance] = useState(false)

    // Case Meta Draft
    const [caseMetaDraft, setCaseMetaDraft] = useState({
        title: '',
        summary: '',
        jurisdiction: '',
        jurisdiction_other: '',
        vip_flag: false,
        urgent_dismissal: false,
        subject_suspended: false,
        external_report_id: '',
        reporter_channel_id: '',
        reporter_key: '',
    })

    const [suspensionOverride, setSuspensionOverride] = useState(false)
    const [showSuspensionModal, setShowSuspensionModal] = useState(false)

    // Triage Gate Draft
    const [triageGate, setTriageGate] = useState({
        impact: 3,
        probability: 3,
        risk_score: 3,
        outcome: '',
        notes: '',
        trigger_source: '',
        business_impact: '',
        exposure_summary: '',
        data_sensitivity: '',
        stakeholders: '',
        confidence_level: '',
        recommended_actions: '',
    })

    // Initialize state from caseData
    useEffect(() => {
        if (!caseData) return

        const matchJurisdiction = JURISDICTION_OPTIONS.includes(caseData.jurisdiction)
        setCaseMetaDraft({
            title: caseData.title,
            summary: caseData.summary || '',
            jurisdiction: matchJurisdiction ? caseData.jurisdiction : 'Other',
            jurisdiction_other: matchJurisdiction ? '' : caseData.jurisdiction,
            vip_flag: !!caseData.vip_flag,
            urgent_dismissal: !!caseData.urgent_dismissal,
            subject_suspended: !!caseData.subject_suspended,
            external_report_id: caseData.external_report_id || '',
            reporter_channel_id: caseData.reporter_channel_id || '',
            reporter_key: caseData.reporter_key || '',
        })

        setSuspensionOverride(false)

        const triage = caseData.gates.find(g => g.gate_key === 'triage')
        if (triage?.data) {
            setTriageGate({
                impact: Number(triage.data.impact || 3),
                probability: Number(triage.data.probability || 3),
                risk_score: Number(triage.data.risk_score || 3),
                outcome: (triage.data.outcome as string) || '',
                notes: (triage.data.notes as string) || '',
                trigger_source: (triage.data.trigger_source as string) || '',
                business_impact: (triage.data.business_impact as string) || '',
                exposure_summary: (triage.data.exposure_summary as string) || '',
                data_sensitivity: (triage.data.data_sensitivity as string) || '',
                stakeholders: (triage.data.stakeholders as string) || '',
                confidence_level: (triage.data.confidence_level as string) || '',
                recommended_actions: (triage.data.recommended_actions as string) || '',
            })
        }
    }, [caseData])

    const isNetherlandsDraft = useMemo(() => {
        const base = (caseMetaDraft.jurisdiction || '').trim().toLowerCase()
        const other = (caseMetaDraft.jurisdiction_other || '').trim().toLowerCase()
        if (base === 'netherlands') return true
        return base === 'other' ? other.includes('netherlands') || other === 'nl' : base.includes('netherlands')
    }, [caseMetaDraft.jurisdiction, caseMetaDraft.jurisdiction_other])

    const needsSuspensionWarning = isNetherlandsDraft && caseMetaDraft.urgent_dismissal && !caseMetaDraft.subject_suspended
    const isAnonymized = caseData?.is_anonymized

    const triageImpactOption = TRIAGE_IMPACT_LEVELS.find(o => o.value === triageGate.impact)
    const triageProbabilityOption = TRIAGE_PROBABILITY_LEVELS.find(o => o.value === triageGate.probability)
    const triageRiskOption = TRIAGE_RISK_LEVELS.find(o => o.value === triageGate.risk_score)

    const handleSaveDetails = async (force = false) => {
        if (!caseMetaDraft.title.trim()) {
            setStatus('Title required')
            return
        }

        const jurisdictionValue = caseMetaDraft.jurisdiction === 'Other'
            ? caseMetaDraft.jurisdiction_other.trim()
            : caseMetaDraft.jurisdiction

        if (!jurisdictionValue) {
            setStatus('Jurisdiction required')
            return
        }

        if (needsSuspensionWarning && !force && !suspensionOverride) {
            setShowSuspensionModal(true)
            return
        }

        setStatus('Saving...')
        const res = await updateCase({
            title: caseMetaDraft.title.trim(),
            summary: caseMetaDraft.summary.trim() || null,
            jurisdiction: jurisdictionValue,
            vip_flag: caseMetaDraft.vip_flag,
            urgent_dismissal: caseMetaDraft.urgent_dismissal,
            subject_suspended: caseMetaDraft.subject_suspended,
            external_report_id: caseMetaDraft.external_report_id.trim() || null,
            reporter_channel_id: caseMetaDraft.reporter_channel_id.trim() || null,
            reporter_key: caseMetaDraft.reporter_key.trim() || null,
        })

        if (res.success) {
            setStatus('Saved details.')
            if (needsSuspensionWarning) setSuspensionOverride(true)
        } else {
            setStatus(res.message || 'Error saving.')
        }
    }

    const handleSaveTriage = async () => {
        if (!triageGate.outcome) {
            setStatus('Triage outcome required')
            return
        }
        setStatus('Saving triage...')
        const res = await saveGate('triage', triageGate)
        if (res.success) {
            setStatus('Saved triage.')
        } else {
            setStatus(res.message || 'Error saving triage.')
        }
    }

    if (!caseData) return null

    return (
        <div>
            {status && <div className="case-flow-status">{status}</div>}

            {/* Suspension Modal */}
            {showSuspensionModal && (
                <div className="case-flow-modal-overlay">
                    <div className="case-flow-modal">
                        <h3>Warning: Suspension Required</h3>
                        <p>For urgent dismissal cases in the Netherlands, the subject must be suspended immediately. Proceed anyway?</p>
                        <div className="case-flow-actions">
                            <button className="case-flow-btn outline" onClick={() => setShowSuspensionModal(false)}>Cancel</button>
                            <button className="case-flow-btn warning" onClick={() => {
                                setShowSuspensionModal(false)
                                handleSaveDetails(true)
                            }}>Proceed without suspension</button>
                        </div>
                    </div>
                </div>
            )}

            <div className="case-flow-step-header">
                <div>
                    <h2>Intake</h2>
                    <p className="case-flow-help">Capture scope, parties, and the initial trigger before any deep inspection.</p>
                </div>
                <button className="case-flow-info" onClick={() => setShowGuidance(!showGuidance)} type="button">i</button>
            </div>

            {showGuidance && (
                <div className="case-flow-guidance">
                    <h4>Guidance</h4>
                    <ul>
                        <li>Confirm the trigger source (alert, report, audit finding) before adding evidence.</li>
                        <li>Record all subjects in scope with role-based descriptors.</li>
                        <li>Keep summaries factual; avoid prohibited personal categories.</li>
                    </ul>
                </div>
            )}

            <div className="case-flow-grid">
                <div className="case-flow-card">
                    <h3>Case context</h3>
                    <p className="case-flow-help">Define scope and jurisdiction before deeper inspection.</p>
                    <label className="case-flow-label">
                        Case title
                        <input
                            type="text"
                            value={caseMetaDraft.title}
                            onChange={e => setCaseMetaDraft({ ...caseMetaDraft, title: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>
                    <label className="case-flow-label">
                        Summary
                        <textarea
                            value={caseMetaDraft.summary}
                            onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, summary: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>
                    <label className="case-flow-label">
                        Jurisdiction
                        <select
                            value={caseMetaDraft.jurisdiction}
                            onChange={(e) =>
                                setCaseMetaDraft({ ...caseMetaDraft, jurisdiction: e.target.value, jurisdiction_other: '' })
                            }
                            disabled={isAnonymized}
                        >
                            <option value="">Select jurisdiction</option>
                            {JURISDICTION_OPTIONS.map((option) => (
                                <option key={option} value={option}>
                                    {option}
                                </option>
                            ))}
                        </select>
                    </label>
                    {caseMetaDraft.jurisdiction === 'Other' && (
                        <label className="case-flow-label">
                            Specify jurisdiction
                            <input
                                type="text"
                                value={caseMetaDraft.jurisdiction_other}
                                onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, jurisdiction_other: e.target.value })}
                                disabled={isAnonymized}
                            />
                        </label>
                    )}

                    <label className="case-flow-label">
                        <input
                            type="checkbox"
                            checked={caseMetaDraft.vip_flag}
                            onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, vip_flag: e.target.checked })}
                            disabled={isAnonymized}
                        />
                        VIP / highly sensitive case
                    </label>

                    <label className="case-flow-label">
                        <input
                            type="checkbox"
                            checked={caseMetaDraft.urgent_dismissal}
                            onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, urgent_dismissal: e.target.checked })}
                            disabled={isAnonymized}
                        />
                        Urgent dismissal case (NL guardrail)
                    </label>

                    <label className="case-flow-label">
                        <input
                            type="checkbox"
                            checked={caseMetaDraft.subject_suspended}
                            onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, subject_suspended: e.target.checked })}
                            disabled={isAnonymized}
                        />
                        Subject suspended (required for NL urgent cases)
                    </label>

                    {needsSuspensionWarning && (
                        <div className="case-flow-warning">Netherlands urgent dismissal cases require suspension confirmation.</div>
                    )}

                    <label className="case-flow-label">
                        External report ID (optional)
                        <input
                            type="text"
                            value={caseMetaDraft.external_report_id}
                            onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, external_report_id: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>

                    <label className="case-flow-label">
                        Reporter channel ID (optional)
                        <input
                            type="text"
                            value={maskFieldValue(caseMetaDraft.reporter_channel_id, piiUnlocked)}
                            onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, reporter_channel_id: e.target.value })}
                            disabled={isAnonymized || !piiUnlocked}
                        />
                    </label>

                    <label className="case-flow-label">
                        Reporter key (optional)
                        <input
                            type="text"
                            value={maskFieldValue(caseMetaDraft.reporter_key, piiUnlocked)}
                            onChange={(e) => setCaseMetaDraft({ ...caseMetaDraft, reporter_key: e.target.value })}
                            disabled={isAnonymized || !piiUnlocked}
                            placeholder={!piiUnlocked ? 'Break glass to edit' : ''}
                        />
                    </label>

                    <button className="case-flow-btn outline" onClick={() => handleSaveDetails(false)} disabled={isAnonymized}>
                        Save intake details
                    </button>

                    <div className="case-flow-divider" />
                    <div className="case-flow-meta">Owner: {caseData.created_by || 'Unassigned'}</div>
                    <div className="case-flow-meta">Created: {new Date(caseData.created_at).toLocaleString()}</div>
                    {isAnonymized && <div className="case-flow-warning">Case anonymized.</div>}
                </div>

                {/* Triage Card */}
                <div className="case-flow-card">
                    <h3>Initial assessment (triage)</h3>
                    <p className="case-flow-help">Use plain-language impact and likelihood levels to clarify the business decision.</p>
                    <label className="case-flow-label">
                        Business impact
                        <select
                            value={triageGate.impact}
                            onChange={(e) => {
                                const impact = Number(e.target.value)
                                setTriageGate({
                                    ...triageGate,
                                    impact,
                                    risk_score: computeRiskScore(impact, triageGate.probability),
                                })
                            }}
                            disabled={isAnonymized}
                        >
                            {TRIAGE_IMPACT_LEVELS.map((option) => (
                                <option key={option.value} value={option.value}>{option.label}</option>
                            ))}
                        </select>
                        {triageImpactOption?.detail && <span className="case-flow-muted">{triageImpactOption.detail}</span>}
                    </label>

                    <label className="case-flow-label">
                        Likelihood
                        <select
                            value={triageGate.probability}
                            onChange={(e) => {
                                const probability = Number(e.target.value)
                                setTriageGate({
                                    ...triageGate,
                                    probability,
                                    risk_score: computeRiskScore(triageGate.impact, probability),
                                })
                            }}
                            disabled={isAnonymized}
                        >
                            {TRIAGE_PROBABILITY_LEVELS.map((option) => (
                                <option key={option.value} value={option.value}>{option.label}</option>
                            ))}
                        </select>
                        {triageProbabilityOption?.detail && <span className="case-flow-muted">{triageProbabilityOption.detail}</span>}
                    </label>

                    <div className="case-flow-score-card">
                        <div>
                            <div className="case-flow-subtitle">Overall risk</div>
                            <div className="case-flow-muted">Calculated from impact and likelihood.</div>
                        </div>
                        <span className="case-flow-score-pill">{triageRiskOption?.label || 'TBD'}</span>
                    </div>

                    <label className="case-flow-label">
                        Trigger source
                        <input
                            list="triage-trigger-sources"
                            value={triageGate.trigger_source}
                            onChange={(e) => setTriageGate({ ...triageGate, trigger_source: e.target.value })}
                            placeholder="e.g., alert, hotline, audit finding"
                            disabled={isAnonymized}
                        />
                        <datalist id="triage-trigger-sources">
                            <option value="Automated alert" />
                            <option value="Employee report" />
                            <option value="Audit finding" />
                            <option value="HR escalation" />
                            <option value="External tip" />
                        </datalist>
                    </label>

                    <label className="case-flow-label">
                        Data sensitivity
                        <select
                            value={triageGate.data_sensitivity}
                            onChange={(e) => setTriageGate({ ...triageGate, data_sensitivity: e.target.value })}
                            disabled={isAnonymized}
                        >
                            <option value="">Select sensitivity</option>
                            {DATA_SENSITIVITY_OPTIONS.map((option) => (
                                <option key={option} value={option}>{option}</option>
                            ))}
                        </select>
                    </label>

                    <label className="case-flow-label">
                        Business impact summary
                        <textarea
                            value={triageGate.business_impact}
                            onChange={(e) => setTriageGate({ ...triageGate, business_impact: e.target.value })}
                            placeholder="Describe the potential business impact."
                            disabled={isAnonymized}
                        />
                    </label>

                    <label className="case-flow-label">
                        Exposure summary
                        <textarea
                            value={triageGate.exposure_summary}
                            onChange={(e) => setTriageGate({ ...triageGate, exposure_summary: e.target.value })}
                            placeholder="Describe the data, systems, or processes exposed."
                            disabled={isAnonymized}
                        />
                    </label>

                    <label className="case-flow-label">
                        Stakeholders impacted
                        <input
                            type="text"
                            value={triageGate.stakeholders}
                            onChange={(e) => setTriageGate({ ...triageGate, stakeholders: e.target.value })}
                            placeholder="e.g., Legal, HR, Comms, Finance"
                            disabled={isAnonymized}
                        />
                    </label>

                    <label className="case-flow-label">
                        Confidence level
                        <select
                            value={triageGate.confidence_level}
                            onChange={(e) => setTriageGate({ ...triageGate, confidence_level: e.target.value })}
                            disabled={isAnonymized}
                        >
                            <option value="">Select confidence</option>
                            {TRIAGE_CONFIDENCE_OPTIONS.map((option) => (
                                <option key={option} value={option}>{option}</option>
                            ))}
                        </select>
                    </label>

                    <label className="case-flow-label">
                        Recommended next actions
                        <textarea
                            value={triageGate.recommended_actions}
                            onChange={(e) => setTriageGate({ ...triageGate, recommended_actions: e.target.value })}
                            placeholder="Immediate actions or decision gates."
                            disabled={isAnonymized}
                        />
                    </label>

                    <label className="case-flow-label">
                        Triage outcome
                        <select
                            value={triageGate.outcome}
                            onChange={(e) => setTriageGate({ ...triageGate, outcome: e.target.value })}
                            disabled={isAnonymized}
                        >
                            <option value="">Select outcome</option>
                            {TRIAGE_OUTCOME_OPTIONS.map((option) => (
                                <option key={option.value} value={option.value}>{option.label}</option>
                            ))}
                        </select>
                    </label>

                    <label className="case-flow-label">
                        Notes (optional)
                        <textarea
                            value={triageGate.notes}
                            onChange={(e) => setTriageGate({ ...triageGate, notes: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>

                    <button className="case-flow-btn outline" onClick={handleSaveTriage} disabled={isAnonymized}>
                        Save triage
                    </button>
                </div>
            </div>
        </div>
    )
}
