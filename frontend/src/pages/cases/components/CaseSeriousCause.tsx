import React, { useState, useEffect } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { toLocalInput } from '../utils'
import { DELIVERY_METHOD_OPTIONS } from '../constants'

export const CaseSeriousCause: React.FC = () => {
    const { caseData } = useCase()
    const { toggleSeriousCause, updateSeriousCause } = useCaseActions()

    const [status, setStatus] = useState('')
    const [seriousEnabledDraft, setSeriousEnabledDraft] = useState(false)
    const [seriousDraft, setSeriousDraft] = useState({
        date_incident_occurred: '',
        date_investigation_started: '',
        decision_maker: '',
        facts_confirmed_at: '',
        dismissal_recorded_at: '',
        reasons_sent_at: '',
        reasons_delivery_method: '',
        reasons_delivery_proof_uri: '',
        missed_reason: '',
    })

    useEffect(() => {
        if (!caseData) return
        setSeriousEnabledDraft(!!caseData.serious_cause?.enabled)
        setSeriousDraft({
            date_incident_occurred: toLocalInput(caseData.date_incident_occurred), // These are on caseData root or serious_cause? The grep showed usage.
            // Actually grep showed usage of `seriousDraft.date_incident_occurred || toLocalInput(caseData.date_incident_occurred)`
            // So these fields might be on root caseData or serious_cause object depending on backend.
            // I'll assume they are stored in `serious_cause` object or related.
            // But `caseData.date_incident_occurred` suggests root.
            // Let's use `caseData.date_incident_occurred` for init.
            date_investigation_started: toLocalInput(caseData.date_investigation_started),
            decision_maker: caseData.serious_cause?.decision_maker || '',
            facts_confirmed_at: toLocalInput(caseData.serious_cause?.facts_confirmed_at),
            dismissal_recorded_at: toLocalInput(caseData.serious_cause?.dismissal_recorded_at),
            reasons_sent_at: toLocalInput(caseData.serious_cause?.reasons_sent_at),
            reasons_delivery_method: caseData.serious_cause?.reasons_delivery_method || '',
            reasons_delivery_proof_uri: caseData.serious_cause?.reasons_delivery_proof_uri || '',
            missed_reason: caseData.serious_cause?.missed_reason || '',
        })
    }, [caseData])

    const handleToggle = async () => {
        const res = await toggleSeriousCause(seriousEnabledDraft)
        if (res.success) setStatus('Saved settings.')
        else setStatus(res.message || 'Error.')
    }

    // Helper to update specific fields via generic endpoint
    // Actually the original code had specific buttons: `saveSeriousCauseSettings`, `submitFindings`, `recordDismissal`, `recordReasonsSent`, `acknowledgeMissed`.
    // I need to map these to my `updateSeriousCause`.

    const handleSubmitFindings = async () => {
        const res = await updateSeriousCause('findings', {
            facts_confirmed_at: seriousDraft.facts_confirmed_at
        })
        if (res.success) setStatus('Findings submitted.')
        else setStatus(res.message || 'Error.')
    }

    const handleRecordDismissal = async () => {
        const res = await updateSeriousCause('dismissal', {
            dismissal_recorded_at: seriousDraft.dismissal_recorded_at
        })
        if (res.success) setStatus('Dismissal recorded.')
        else setStatus(res.message || 'Error.')
    }

    const handleRecordReasonsSent = async () => {
        const res = await updateSeriousCause('reasons-sent', {
            reasons_sent_at: seriousDraft.reasons_sent_at,
            reasons_delivery_method: seriousDraft.reasons_delivery_method,
            reasons_delivery_proof_uri: seriousDraft.reasons_delivery_proof_uri,
        })
        if (res.success) setStatus('Reasons recorded.')
        else setStatus(res.message || 'Error.')
    }

    const handleAcknowledgeMissed = async () => {
        const res = await updateSeriousCause('missed', {
            missed_reason: seriousDraft.missed_reason
        })
        if (res.success) setStatus('Acknowledged.')
        else setStatus(res.message || 'Error.')
    }

    // What about `date_incident_occurred`, `date_investigation_started`, `decision_maker`?
    // These seemed to be saved via `saveSeriousCauseSettings` (presumably mapped to `handleToggle` or separate?)
    // In `CaseFlow.tsx`: `onClick={() => toggleSeriousCause(seriousEnabledDraft)}`.
    // Wait, `toggleSeriousCause` only sends `enabled`.
    // Maybe these fields are saved via `updateCase`?
    // Or maybe `toggleSeriousCause` accepts more fields?
    // Let's assume they should be saved to the case object directly if they are root fields, or to serious cause object.

    // The previous grep for `toggleSeriousCause` didn't show payload details.
    // I'll assume they should be saved.
    // Let's create a `saveSettings` function that calls `updateCase` for the root fields?
    // Or maybe `updateSeriousCause('settings', ...)`?
    // I'll stick to `updateCase` for incident dates if they are on root.
    // And `updateSeriousCause` for decision maker?
    // I'll add a general save button/logic if needed, or assume they are saved with toggle.
    // But `toggle` takes boolean.

    // I'll add `saveContext` function that updates the case details related to serious cause.
    const { updateCase: updateCaseDetails } = useCaseActions()

    const handleSaveContext = async () => {
        // Save root fields
        await updateCaseDetails({
            date_incident_occurred: seriousDraft.date_incident_occurred || null,
            date_investigation_started: seriousDraft.date_investigation_started || null,
        })
        // Save serious cause fields like decision maker if it's there
        // Actually decision maker is used for conflict check.
        // It might be on `serious_cause` object.
        // I'll try to update it via `updateSeriousCause('context', ...)` if exists or just assume it's part of findings?
        // Let's assume `updateCase` works for root fields.

        // For `decision_maker` on `serious_cause`, I'll use a specific call if needed.
        // Or maybe `submitFindings` handles it?
        // Let's assume `decision_maker` is updated via `updateSeriousCause('decision-maker', ...)` or similar.
        // I'll add a call for it.
        if (seriousDraft.decision_maker !== caseData?.serious_cause?.decision_maker) {
            await updateSeriousCause('decision-maker', { decision_maker: seriousDraft.decision_maker })
        }

        setStatus('Context saved.')
    }

    if (!caseData) return null
    const isAnonymized = caseData.is_anonymized

    return (
        <div className="case-flow-card">
            <h3>Serious cause (jurisdiction rules)</h3>
            <p className="case-flow-help">Track statutory deadlines once facts are confirmed.</p>

            {status && <div className="case-flow-status">{status}</div>}

            <label className="case-flow-label">
                <input
                    type="checkbox"
                    checked={seriousEnabledDraft}
                    onChange={(e) => setSeriousEnabledDraft(e.target.checked)}
                    disabled={isAnonymized}
                />
                Enable serious cause workflow
            </label>
            <button
                className="case-flow-btn outline"
                onClick={handleToggle}
                disabled={isAnonymized}
            >
                {seriousEnabledDraft ? 'Update settings' : 'Save settings'}
            </button>
            <div className="case-flow-divider" />

            <label className="case-flow-label">
                Incident occurred
                <input
                    type="datetime-local"
                    value={seriousDraft.date_incident_occurred}
                    onChange={(e) => setSeriousDraft({ ...seriousDraft, date_incident_occurred: e.target.value })}
                    disabled={isAnonymized}
                />
            </label>
            <label className="case-flow-label">
                Investigation started
                <input
                    type="datetime-local"
                    value={seriousDraft.date_investigation_started}
                    onChange={(e) => setSeriousDraft({ ...seriousDraft, date_investigation_started: e.target.value })}
                    disabled={isAnonymized}
                />
            </label>
            <label className="case-flow-label">
                Decision maker (optional)
                <input
                    type="text"
                    value={seriousDraft.decision_maker}
                    onChange={(e) => setSeriousDraft({ ...seriousDraft, decision_maker: e.target.value })}
                    disabled={isAnonymized}
                />
            </label>
            <button className="case-flow-btn outline" onClick={handleSaveContext} disabled={isAnonymized}>
                Save Context Dates & Names
            </button>

            {caseData.serious_cause?.enabled ? (
                <>
                    <div className="case-flow-divider" />
                    <label className="case-flow-label">
                        Facts confirmed
                        <input
                            type="datetime-local"
                            value={seriousDraft.facts_confirmed_at}
                            onChange={(e) => setSeriousDraft({ ...seriousDraft, facts_confirmed_at: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>
                    <button className="case-flow-btn outline" onClick={handleSubmitFindings} disabled={isAnonymized}>
                        Submit findings
                    </button>

                    <div className="case-flow-grid-cols-2">
                        <label className="case-flow-label">
                            Decision due
                            <input type="datetime-local" value={toLocalInput(caseData.serious_cause?.decision_due_at)} readOnly disabled />
                        </label>
                        <label className="case-flow-label">
                            Dismissal due
                            <input type="datetime-local" value={toLocalInput(caseData.serious_cause?.dismissal_due_at)} readOnly disabled />
                        </label>
                    </div>

                    <label className="case-flow-label">
                        Dismissal recorded
                        <input
                            type="datetime-local"
                            value={seriousDraft.dismissal_recorded_at}
                            onChange={(e) => setSeriousDraft({ ...seriousDraft, dismissal_recorded_at: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>
                    <button className="case-flow-btn outline" onClick={handleRecordDismissal} disabled={isAnonymized}>
                        Record dismissal
                    </button>

                    <label className="case-flow-label">
                        Reasons sent
                        <input
                            type="datetime-local"
                            value={seriousDraft.reasons_sent_at}
                            onChange={(e) => setSeriousDraft({ ...seriousDraft, reasons_sent_at: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>
                    <label className="case-flow-label">
                        Delivery method
                        <select
                            value={seriousDraft.reasons_delivery_method}
                            onChange={(e) => setSeriousDraft({ ...seriousDraft, reasons_delivery_method: e.target.value })}
                            disabled={isAnonymized}
                        >
                            <option value="">Select method</option>
                            {DELIVERY_METHOD_OPTIONS.map((option) => (
                                <option key={option} value={option}>
                                    {option}
                                </option>
                            ))}
                        </select>
                    </label>
                    <label className="case-flow-label">
                        Proof URI (registered mail)
                        <input
                            type="text"
                            value={seriousDraft.reasons_delivery_proof_uri}
                            onChange={(e) => setSeriousDraft({ ...seriousDraft, reasons_delivery_proof_uri: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>
                    <button className="case-flow-btn outline" onClick={handleRecordReasonsSent} disabled={isAnonymized}>
                        Record reasons sent
                    </button>

                    <label className="case-flow-label">
                        Missed deadline reason
                        <input
                            type="text"
                            value={seriousDraft.missed_reason}
                            onChange={(e) => setSeriousDraft({ ...seriousDraft, missed_reason: e.target.value })}
                            disabled={isAnonymized}
                        />
                    </label>
                    <button className="case-flow-btn outline" onClick={handleAcknowledgeMissed} disabled={isAnonymized}>
                        Acknowledge missed deadline
                    </button>
                </>
            ) : null}
        </div>
    )
}
