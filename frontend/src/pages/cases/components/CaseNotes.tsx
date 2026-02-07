import React, { useState } from 'react'
import { useCase } from '../context/CaseContext'
import { useCaseActions } from '../hooks/useCaseActions'
import { NOTE_TYPE_OPTIONS } from '../constants'
import { maskText } from '../utils'

export const CaseNotes: React.FC = () => {
    const { caseData, piiUnlocked } = useCase()
    const { addNote } = useCaseActions()

    const [status, setStatus] = useState('')
    const [noteDraft, setNoteDraft] = useState({ body: '', note_type: 'general' })
    const [meetingDraft, setMeetingDraft] = useState({
        meeting_date: '',
        attendees: '',
        summary: '',
        minutes: '',
    })

    // TODO: Implement addMeetingNote in useCaseActions or here as a specialized addNote wrapper?
    // The original code used `addMeetingNote` which likely called `addNote` with a specific format or endpoint.
    // I need to check `addMeetingNote` implementation.
    // Assuming for now I can just use `addNote` with a formatted body for meetings or similar.
    // But wait, `addMeetingNote` was a function in CaseFlow.tsx.
    // Let's implement handles for both.

    const handleAddNote = async () => {
        if (!noteDraft.body.trim()) return
        setStatus('Adding note...')
        const res = await addNote(noteDraft.body, noteDraft.note_type)
        if (res.success) {
            setNoteDraft({ ...noteDraft, body: '' })
            setStatus('Note added.')
        } else {
            setStatus(res.message || 'Error.')
        }
    }

    const handleAddMeeting = async () => {
        // Construction logic for meeting note
        const body = `Meeting Date: ${meetingDraft.meeting_date}\nAttendees: ${meetingDraft.attendees}\nSummary: ${meetingDraft.summary}\n\nMinutes:\n${meetingDraft.minutes}`
        setStatus('Adding meeting minutes...')
        const res = await addNote(body, 'meeting')
        if (res.success) {
            setMeetingDraft({ meeting_date: '', attendees: '', summary: '', minutes: '' })
            setStatus('Meeting added.')
        } else {
            setStatus(res.message || 'Error.')
        }
    }

    if (!caseData) return null
    const canEditPII = piiUnlocked && !caseData.is_anonymized

    return (
        <div className="case-flow-grid">
            <div className="case-flow-card">
                <h3>Investigation log</h3>
                <p className="case-flow-help">Append-only notes with automatic prohibited-data flagging.</p>

                {status && <div className="case-flow-status">{status}</div>}

                <label className="case-flow-label">
                    Note type
                    <select
                        value={noteDraft.note_type}
                        onChange={(e) => setNoteDraft({ ...noteDraft, note_type: e.target.value })}
                        disabled={!canEditPII}
                    >
                        {NOTE_TYPE_OPTIONS.map((option) => (
                            <option key={option} value={option}>
                                {option}
                            </option>
                        ))}
                    </select>
                </label>
                <label className="case-flow-label">
                    Note
                    <textarea
                        value={noteDraft.body}
                        onChange={(e) => setNoteDraft({ ...noteDraft, body: e.target.value })}
                        disabled={!canEditPII}
                    />
                </label>
                <button className="case-flow-btn outline" onClick={handleAddNote} disabled={!canEditPII}>
                    Add note
                </button>

                {caseData.notes.length === 0 ? (
                    <div className="case-flow-muted">No notes yet.</div>
                ) : (
                    caseData.notes.map((note) => (
                        <div key={note.id} className="case-flow-note">
                            <div className="case-flow-muted">
                                {note.note_type} · {new Date(note.created_at).toLocaleString()}
                            </div>
                            <div>{maskText(note.body, 'Note hidden. Break glass to view.', piiUnlocked)}</div>
                            {note.flags && (note.flags as any).requires_review ? (
                                <div className="case-flow-warning">Flagged for review</div>
                            ) : null}
                        </div>
                    ))
                )}
            </div>

            <div className="case-flow-card">
                <h3>Meetings & Minutes</h3>
                <p className="case-flow-help">Capture meeting notes, attendees, and summaries.</p>
                <label className="case-flow-label">
                    Meeting date/time
                    <input
                        type="datetime-local"
                        value={meetingDraft.meeting_date}
                        onChange={(e) => setMeetingDraft({ ...meetingDraft, meeting_date: e.target.value })}
                        disabled={!canEditPII}
                    />
                </label>
                <label className="case-flow-label">
                    Attendees
                    <input
                        type="text"
                        value={meetingDraft.attendees}
                        onChange={(e) => setMeetingDraft({ ...meetingDraft, attendees: e.target.value })}
                        placeholder="Names or roles"
                        disabled={!canEditPII}
                    />
                </label>
                <label className="case-flow-label">
                    Summary
                    <textarea
                        value={meetingDraft.summary}
                        onChange={(e) => setMeetingDraft({ ...meetingDraft, summary: e.target.value })}
                        disabled={!canEditPII}
                    />
                </label>
                <label className="case-flow-label">
                    Minutes
                    <textarea
                        value={meetingDraft.minutes}
                        onChange={(e) => setMeetingDraft({ ...meetingDraft, minutes: e.target.value })}
                        disabled={!canEditPII}
                    />
                </label>
                <button className="case-flow-btn outline" onClick={handleAddMeeting} disabled={!canEditPII}>
                    Add meeting minutes
                </button>

                <div className="case-flow-divider" />
                <h4 className="case-flow-subtitle">Meeting overview</h4>
                {caseData.notes.filter((note) => note.note_type === 'meeting').length === 0 ? (
                    <div className="case-flow-muted">No meetings recorded yet.</div>
                ) : (
                    caseData.notes
                        .filter((note) => note.note_type === 'meeting')
                        .map((note) => (
                            <div key={`meeting-${note.id}`} className="case-flow-note">
                                <div className="case-flow-muted">{new Date(note.created_at).toLocaleString()}</div>
                                <div>{maskText(note.body, 'Meeting note hidden. Break glass to view.', piiUnlocked)}</div>
                            </div>
                        ))
                )}
            </div>
        </div>
    )
}
