import React, { useState } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { useCaseInvestigation } from '../hooks/useCaseInvestigation'
import { CaseWorksCouncil } from './CaseWorksCouncil'
import { CaseTasks } from './CaseTasks'
import { CaseEvidenceRegister } from './CaseEvidenceRegister'
import { CaseNotes } from './CaseNotes'
import { CaseExperts } from './CaseExperts'
import { CaseFlags } from './CaseFlags'
import { LEGAL_HOLD_CHANNEL_OPTIONS, REPORT_TEMPLATES } from '../constants'
import { maskText } from '../utils'

export const CaseInvestigation: React.FC = () => {
    const { caseData, piiUnlocked } = useCase()
    const { sendReporterReply, createLegalHold } = useCaseActions()
    const {
        playbooks, suggestions, legalHolds, reporterMessages,
        applyPlaybook, convertSuggestion, dismissSuggestion
    } = useCaseInvestigation()

    const [status, setStatus] = useState('')
    const [showGuidance, setShowGuidance] = useState(false)

    const [reporterReply, setReporterReply] = useState('')
    const [legalHoldDraft, setLegalHoldDraft] = useState({
        contact_name: '',
        contact_email: '',
        contact_role: '',
        delivery_channel: 'Email',
        preservation_scope: '',
        access_code: '',
        conflict_override_reason: '',
    })
    const [legalHoldStatus, setLegalHoldStatus] = useState('')

    const handleApplyPlaybook = async (key: string) => {
        setStatus(`Applying playbook...`)
        const res = await applyPlaybook(key)
        if (res.success) setStatus('Playbook applied.')
        else setStatus(res.message || 'Error.')
    }

    const handleConvertSuggestion = async (id: string) => {
        const res = await convertSuggestion(id)
        if (res.success) setStatus('Converted.')
        else setStatus(res.message || 'Error.')
    }

    const handleDismissSuggestion = async (id: string) => {
        const res = await dismissSuggestion(id)
        if (res.success) setStatus('Dismissed.')
        else setStatus(res.message || 'Error.')
    }

    const handleSendReply = async () => {
        if (!reporterReply.trim()) return
        setStatus('Sending...')
        const res = await sendReporterReply(reporterReply)
        if (res.success) {
            setStatus('Reply sent.')
            setReporterReply('')
        } else {
            setStatus(res.message || 'Error sending reply.')
        }
    }

    const handleCreateLegalHold = async () => {
        if (!legalHoldDraft.contact_name) {
            setLegalHoldStatus('Contact name required.')
            return
        }
        setLegalHoldStatus('Generating...')
        const res = await createLegalHold({
            contact_name: legalHoldDraft.contact_name,
            contact_email: legalHoldDraft.contact_email || null,
            contact_role: legalHoldDraft.contact_role || null,
            preservation_scope: legalHoldDraft.preservation_scope || null,
            delivery_channel: legalHoldDraft.delivery_channel,
            access_code: legalHoldDraft.access_code || null,
            conflict_override_reason: legalHoldDraft.conflict_override_reason || null,
        })
        if (res.success) {
            setLegalHoldStatus('Legal hold created.')
            setLegalHoldDraft({
                contact_name: '',
                contact_email: '',
                contact_role: '',
                delivery_channel: 'Email',
                preservation_scope: '',
                access_code: '',
                conflict_override_reason: '',
            })
        } else {
            setLegalHoldStatus(res.message || 'Error.')
        }
    }

    if (!caseData) return null
    const isAnonymized = caseData.is_anonymized
    const canEditPII = piiUnlocked && !isAnonymized

    return (
        <div>
            <div className="case-flow-step-header">
                <div>
                    <h2>Investigation</h2>
                    <p className="case-flow-help">Capture actions, evidence, and logs as you build the case file.</p>
                </div>
                <button className="case-flow-info" onClick={() => setShowGuidance(!showGuidance)} type="button">i</button>
            </div>

            {showGuidance && (
                <div className="case-flow-guidance">
                    <h4>Guidance</h4>
                    <ul>
                        <li>Every investigative action should map to a task or evidence entry.</li>
                        <li>Use playbooks to avoid missing core steps.</li>
                        <li>Keep notes factual; avoid health, political, or union data.</li>
                    </ul>
                </div>
            )}

            {status && <div className="case-flow-status">{status}</div>}

            <div className="case-flow-grid">
                <CaseWorksCouncil />
                <CaseTasks />
                <CaseEvidenceRegister />
            </div>

            <div className="case-flow-grid">
                {/* Playbooks */}
                <div className="case-flow-card">
                    <h3>Playbooks</h3>
                    <p className="case-flow-help">Apply a playbook to auto-create tasks and evidence suggestions.</p>
                    <div className="case-flow-inline">
                        {playbooks.map((playbook) => (
                            <button
                                key={playbook.key}
                                className="case-flow-btn outline"
                                onClick={() => handleApplyPlaybook(playbook.key)}
                                disabled={isAnonymized}
                            >
                                {playbook.title}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Suggestions */}
                <div className="case-flow-card">
                    <h3>Evidence suggestions</h3>
                    <p className="case-flow-help">Convert suggestions into evidence entries or dismiss with rationale.</p>
                    {suggestions.length === 0 ? (
                        <div className="case-flow-muted">No suggestions yet.</div>
                    ) : (
                        suggestions.map((suggestion) => (
                            <div key={suggestion.suggestion_id} className="case-flow-row">
                                <div>
                                    <strong>{suggestion.label}</strong>
                                    <div className="case-flow-muted">{suggestion.source}</div>
                                    <div className="case-flow-muted">{suggestion.playbook_key}</div>
                                </div>
                                {suggestion.status === 'open' ? (
                                    <div className="case-flow-inline">
                                        <button
                                            className="case-flow-btn outline"
                                            onClick={() => handleConvertSuggestion(suggestion.suggestion_id)}
                                            disabled={isAnonymized || !!caseData.evidence_locked}
                                        >
                                            Convert
                                        </button>
                                        <button
                                            className="case-flow-btn outline"
                                            onClick={() => handleDismissSuggestion(suggestion.suggestion_id)}
                                            disabled={isAnonymized}
                                        >
                                            Dismiss
                                        </button>
                                    </div>
                                ) : (
                                    <span className="case-flow-tag">{suggestion.status}</span>
                                )}
                            </div>
                        ))
                    )}
                </div>

                {/* Reporter Q&A */}
                <div className="case-flow-card">
                    <h3>Reporter Q&amp;A</h3>
                    <p className="case-flow-help">Secure two-way messages tied to the reporter key.</p>
                    {!caseData.reporter_key ? (
                        <div className="case-flow-muted">No reporter key linked to this case.</div>
                    ) : (
                        <>
                            {reporterMessages.length === 0 ? (
                                <div className="case-flow-muted">No messages yet.</div>
                            ) : (
                                reporterMessages.map((message) => (
                                    <div key={message.id} className="case-flow-note">
                                        <div className="case-flow-muted">
                                            {message.sender} · {new Date(message.created_at).toLocaleString()}
                                        </div>
                                        <div>{maskText(message.body, 'Message hidden. Break glass to view.', piiUnlocked)}</div>
                                    </div>
                                ))
                            )}
                            <label className="case-flow-label">
                                Reply to reporter
                                <textarea
                                    value={reporterReply}
                                    onChange={(e) => setReporterReply(e.target.value)}
                                    disabled={!canEditPII}
                                />
                            </label>
                            <div className="case-flow-inline">
                                {REPORT_TEMPLATES.map((template, idx) => (
                                    <button
                                        key={`template-${idx}`}
                                        className="case-flow-btn outline small"
                                        onClick={() => setReporterReply(template)}
                                        disabled={!canEditPII}
                                    >
                                        Use template {idx + 1}
                                    </button>
                                ))}
                            </div>
                            <button className="case-flow-btn outline" onClick={handleSendReply} disabled={!canEditPII}>
                                Send reply
                            </button>
                        </>
                    )}
                </div>
            </div>

            <div className="case-flow-grid">
                {/* Silent Legal Hold */}
                <div className="case-flow-card">
                    <h3>Silent legal hold</h3>
                    <p className="case-flow-help">
                        Generate a confidential preservation instruction for a trusted IT contact.
                    </p>
                    <label className="case-flow-label">
                        IT contact name
                        <input
                            type="text"
                            value={legalHoldDraft.contact_name}
                            onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, contact_name: e.target.value })}
                            disabled={!canEditPII}
                        />
                    </label>
                    <label className="case-flow-label">
                        IT contact email
                        <input
                            type="email"
                            value={legalHoldDraft.contact_email}
                            onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, contact_email: e.target.value })}
                            disabled={!canEditPII}
                        />
                    </label>
                    <label className="case-flow-label">
                        IT contact role
                        <input
                            type="text"
                            value={legalHoldDraft.contact_role}
                            onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, contact_role: e.target.value })}
                            disabled={!canEditPII}
                        />
                    </label>
                    <label className="case-flow-label">
                        Delivery channel
                        <select
                            value={legalHoldDraft.delivery_channel}
                            onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, delivery_channel: e.target.value })}
                            disabled={isAnonymized}
                        >
                            {LEGAL_HOLD_CHANNEL_OPTIONS.map((option) => (
                                <option key={option} value={option}>
                                    {option}
                                </option>
                            ))}
                        </select>
                    </label>
                    <label className="case-flow-label">
                        Preservation scope
                        <textarea
                            value={legalHoldDraft.preservation_scope}
                            onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, preservation_scope: e.target.value })}
                            disabled={!canEditPII}
                        />
                    </label>
                    <label className="case-flow-label">
                        Access code (optional)
                        <input
                            type="text"
                            value={legalHoldDraft.access_code}
                            onChange={(e) => setLegalHoldDraft({ ...legalHoldDraft, access_code: e.target.value })}
                            disabled={!canEditPII}
                            placeholder="Leave blank to auto-generate"
                        />
                    </label>
                    <label className="case-flow-label">
                        Override reason (only if contact is in scope)
                        <input
                            type="text"
                            value={legalHoldDraft.conflict_override_reason}
                            onChange={(e) =>
                                setLegalHoldDraft({ ...legalHoldDraft, conflict_override_reason: e.target.value })
                            }
                            disabled={!canEditPII}
                        />
                    </label>
                    <button className="case-flow-btn outline" onClick={handleCreateLegalHold} disabled={!canEditPII}>
                        Generate legal hold
                    </button>
                    {legalHoldStatus ? <div className="case-flow-meta">{legalHoldStatus}</div> : null}
                    {legalHolds.length === 0 ? (
                        <div className="case-flow-muted">No legal holds yet.</div>
                    ) : (
                        legalHolds.map((hold) => (
                            <div key={hold.id} className="case-flow-note">
                                <div className="case-flow-muted">
                                    {hold.hold_id} · {new Date(hold.created_at).toLocaleString()}
                                </div>
                                <div>
                                    <strong>{maskText(hold.contact_name, 'Hidden', piiUnlocked)}</strong>
                                    {hold.contact_role ? ` · ${maskText(hold.contact_role, 'Hidden', piiUnlocked)}` : ''}
                                </div>
                                {hold.contact_email ? (
                                    <div className="case-flow-muted">{maskText(hold.contact_email, 'Hidden', piiUnlocked)}</div>
                                ) : null}
                                {hold.preservation_scope ? (
                                    <div className="case-flow-muted">Scope: {maskText(hold.preservation_scope, 'Hidden', piiUnlocked)}</div>
                                ) : null}
                                {hold.delivery_channel ? (
                                    <div className="case-flow-muted">Channel: {hold.delivery_channel}</div>
                                ) : null}
                            </div>
                        ))
                    )}
                </div>

                <CaseExperts />
                <CaseNotes />
                <CaseFlags />
            </div>
        </div>
    )
}
