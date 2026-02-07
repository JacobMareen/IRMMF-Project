import { useCallback } from 'react'
import { apiFetch } from '../../../lib/api'
import { useCase } from '../context/CaseContext'


export const useCaseActions = () => {
    const { caseId, refreshCase } = useCase()

    const saveGate = useCallback(
        async (gateKey: string, payload: Record<string, unknown>) => {
            if (!caseId) return { success: false, message: 'No case ID' }
            try {
                const res = await apiFetch(`/cases/${caseId}/gates/${gateKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
                if (!res.ok) {
                    const text = await res.text()
                    let message = text || 'Unable to save gate.'
                    try {
                        const data = JSON.parse(text)
                        if (data?.detail) message = data.detail
                    } catch {
                        // keep raw text
                    }
                    throw new Error(message)
                }
                await refreshCase()
                return { success: true }
            } catch (err) {
                return { success: false, message: err instanceof Error ? err.message : 'Unknown error' }
            }
        },
        [caseId, refreshCase]
    )

    const updateCase = useCallback(
        async (payload: Record<string, unknown>) => {
            if (!caseId) return { success: false, message: 'No case ID' }
            try {
                const res = await apiFetch(`/cases/${caseId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
                if (!res.ok) throw new Error('Failed to update case.')
                await refreshCase()
                return { success: true }
            } catch (err) {
                return { success: false, message: err instanceof Error ? err.message : 'Unknown error' }
            }
        },
        [caseId, refreshCase]
    )

    const addSubject = useCallback(async (payload: any) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/subjects`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            if (!res.ok) throw new Error('Failed to add subject')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const createTask = useCallback(async (title: string, assignee?: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title.trim(), assignee: assignee?.trim() || null }),
            })
            if (!res.ok) throw new Error('Failed to add task.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const updateTaskStatus = useCallback(async (taskId: number, status: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/tasks/${taskId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status }),
            })
            if (!res.ok) throw new Error('Failed to update task.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const addEvidence = useCallback(async (label: string, file: File | null, uri: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const formData = new FormData()
            formData.append('label', label)
            if (file) formData.append('file', file)
            if (uri) formData.append('location_uri', uri)
            const res = await apiFetch(`/cases/${caseId}/evidence`, { method: 'POST', body: formData })
            if (!res.ok) throw new Error('Failed to upload evidence.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const sendReporterReply = useCallback(async (message: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/reporter-qa`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message }),
            })
            if (!res.ok) throw new Error('Failed to send reply.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const createLegalHold = useCallback(async (payload: any) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/legal-hold`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            if (!res.ok) throw new Error('Failed to create legal hold.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const addNote = useCallback(async (body: string, noteType: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ body, note_type: noteType }),
            })
            if (!res.ok) throw new Error('Failed to add note.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const grantExpertAccess = useCallback(async (payload: any) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/expert-access`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            if (!res.ok) throw new Error('Failed to grant access.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const revokeExpertAccess = useCallback(async (accessId: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/expert-access/${accessId}`, { method: 'DELETE' })
            if (!res.ok) throw new Error('Failed to revoke access.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const resolveFlag = useCallback(async (flagId: number) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/flags/${flagId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'resolved' }),
            })
            if (!res.ok) throw new Error('Failed to resolve flag.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const generateDocument = useCallback(async (docType: string, format: string = 'PDF') => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/documents/${docType}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format }),
            })
            if (!res.ok) throw new Error('Failed to generate document.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const recordDecision = useCallback(async (outcome: string, summary: string, overrideReason?: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/decision`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ outcome, summary, role_separation_override: overrideReason }),
            })
            if (!res.ok) throw new Error('Failed to record decision.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const draftDecisionSummary = useCallback(async () => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/draft-decision`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to draft decision.')
            const data = await res.json()
            return { success: true, summary: data.summary }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId])

    const approveErasure = useCallback(async () => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/erasure/approve`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to approve erasure.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const executeErasure = useCallback(async () => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/erasure/execute`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to execute erasure.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const toggleSeriousCause = useCallback(async (enabled: boolean) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/serious-cause/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled }),
            })
            if (!res.ok) throw new Error('Failed to toggle serious cause.')
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const updateSeriousCause = useCallback(async (endpoint: string, payload: any) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/serious-cause/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            if (!res.ok) throw new Error(`Failed to update serious cause ${endpoint}.`)
            await refreshCase()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId, refreshCase])

    const runConsistencyCheck = useCallback(async () => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/consistency-check`, { method: 'POST' })
            if (!res.ok) throw new Error('Failed to run consistency check.')
            const data = await res.json()
            return { success: true, data }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }, [caseId])

    return {
        saveGate, updateCase, addSubject, createTask, updateTaskStatus,
        addEvidence, sendReporterReply, createLegalHold, addNote,
        grantExpertAccess, revokeExpertAccess, resolveFlag,
        generateDocument, recordDecision, draftDecisionSummary,
        approveErasure, executeErasure,
        toggleSeriousCause, updateSeriousCause, runConsistencyCheck
    }
}
