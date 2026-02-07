import { useState, useCallback, useEffect } from 'react'
import { apiFetch } from '../../../lib/api'
import { useCase } from '../context/CaseContext'
import type { Playbook, CaseSuggestion, CaseLegalHold, CaseReporterMessage, CaseExpertAccess, CaseFlag } from '../types'

export const useCaseInvestigation = () => {
    const { caseId, refreshCase } = useCase()

    const [playbooks, setPlaybooks] = useState<Playbook[]>([])
    const [suggestions, setSuggestions] = useState<CaseSuggestion[]>([])
    const [legalHolds, setLegalHolds] = useState<CaseLegalHold[]>([])
    const [reporterMessages, setReporterMessages] = useState<CaseReporterMessage[]>([])
    const [expertAccess, setExpertAccess] = useState<CaseExpertAccess[]>([])
    const [flags, setFlags] = useState<CaseFlag[]>([])
    const [loading, setLoading] = useState(false)
    const [error] = useState<string | null>(null)

    const loadPlaybooks = useCallback(async () => {
        try {
            const res = await apiFetch(`/cases/playbooks`)
            const data = res.ok ? await res.json() : []
            setPlaybooks(data || [])
        } catch {
            setPlaybooks([])
        }
    }, [])

    const loadSuggestions = useCallback(async () => {
        if (!caseId) return
        try {
            const res = await apiFetch(`/cases/${caseId}/suggestions`)
            const data = res.ok ? await res.json() : []
            setSuggestions(data || [])
        } catch {
            setSuggestions([])
        }
    }, [caseId])

    const loadLegalHolds = useCallback(async () => {
        if (!caseId) return
        try {
            const res = await apiFetch(`/cases/${caseId}/legal-holds`)
            const data = res.ok ? await res.json() : []
            setLegalHolds(data || [])
        } catch {
            setLegalHolds([])
        }
    }, [caseId])

    const loadReporterMessages = useCallback(async () => {
        if (!caseId) return
        try {
            const res = await apiFetch(`/cases/${caseId}/reporter-messages`)
            const data = res.ok ? await res.json() : []
            setReporterMessages(data || [])
        } catch {
            setReporterMessages([])
        }
    }, [caseId])

    const loadExpertAccess = useCallback(async () => {
        if (!caseId) return
        try {
            const res = await apiFetch(`/cases/${caseId}/experts`)
            const data = res.ok ? await res.json() : []
            setExpertAccess(data || [])
        } catch {
            setExpertAccess([])
        }
    }, [caseId])

    const loadFlags = useCallback(async () => {
        if (!caseId) return
        try {
            const res = await apiFetch(`/cases/${caseId}/flags`)
            const data = res.ok ? await res.json() : []
            setFlags(data || [])
        } catch {
            setFlags([])
        }
    }, [caseId])

    const refreshInvestigationData = useCallback(async () => {
        setLoading(true)
        await Promise.all([
            loadPlaybooks(),
            loadSuggestions(),
            loadLegalHolds(),
            loadReporterMessages(),
            loadExpertAccess(),
            loadFlags()
        ])
        setLoading(false)
    }, [loadPlaybooks, loadSuggestions, loadLegalHolds, loadReporterMessages, loadExpertAccess, loadFlags])

    // Initial load
    useEffect(() => {
        if (caseId) refreshInvestigationData()
    }, [caseId, refreshInvestigationData])

    const applyPlaybook = async (playbookKey: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/apply-playbook`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ playbook_key: playbookKey }),
            })
            if (!res.ok) throw new Error('Playbook failed.')
            await refreshCase()
            await loadSuggestions()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }

    const convertSuggestion = async (suggestionId: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/suggestions/${suggestionId}/convert`, { method: 'POST' })
            if (!res.ok) throw new Error('Convert failed.')
            await refreshCase()
            await loadSuggestions()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }

    const dismissSuggestion = async (suggestionId: string) => {
        if (!caseId) return { success: false, message: 'No case ID' }
        try {
            const res = await apiFetch(`/cases/${caseId}/suggestions/${suggestionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'dismissed' }),
            })
            if (!res.ok) throw new Error('Dismiss failed.')
            await loadSuggestions()
            return { success: true }
        } catch (err) {
            return { success: false, message: err instanceof Error ? err.message : 'Error' }
        }
    }

    return {
        playbooks,
        suggestions,
        legalHolds,
        reporterMessages,
        expertAccess,
        flags,
        loading,
        error,
        refreshInvestigationData,
        applyPlaybook,
        convertSuggestion,
        dismissSuggestion
    }
}
