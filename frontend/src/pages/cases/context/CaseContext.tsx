import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'
import { useParams } from 'react-router-dom'
import { apiFetch } from '../../../lib/api'
import type { CaseRecord, CaseFlag, CaseLink, CaseLegalHold, CaseExpertAccess, CaseReporterMessage, CaseAuditEvent, Playbook, CaseSuggestion, CaseDocument } from '../types'
import { STEPS } from '../constants'

interface CaseContextType {
    caseId: string | undefined
    caseData: CaseRecord | null
    loading: boolean
    error: string | null

    // Navigation
    currentStep: typeof STEPS[0]
    setCurrentStepKey: (key: string) => void
    steps: typeof STEPS

    // Auxiliary Data
    playbooks: Playbook[]
    suggestions: CaseSuggestion[]
    documents: CaseDocument[]
    flags: CaseFlag[]
    links: CaseLink[]
    legalHolds: CaseLegalHold[]
    expertAccess: CaseExpertAccess[]
    reporterMessages: CaseReporterMessage[]
    auditEvents: CaseAuditEvent[]

    // Draft/UI State that is global
    piiUnlocked: boolean

    // Actions
    refreshCase: () => Promise<void>
    refreshDocuments: () => Promise<void>
    refreshFlags: () => Promise<void>
    refreshLinks: () => Promise<void>
    refreshAudit: () => Promise<void>

    // Helpers
    hasRoleSeparationConflict: boolean
    isBelgiumCase: boolean

    // Setters for global UI constraints
    setPiiUnlocked: (unlocked: boolean) => void
}

const CaseContext = createContext<CaseContextType | undefined>(undefined)

export const useCase = () => {
    const context = useContext(CaseContext)
    if (!context) {
        throw new Error('useCase must be used within a CaseProvider')
    }
    return context
}

interface CaseProviderProps {
    children: ReactNode
    caseId?: string
}

export const CaseProvider: React.FC<CaseProviderProps> = ({ children, caseId: propCaseId }) => {
    const params = useParams()
    const caseId = propCaseId || params.caseId

    const [caseData, setCaseData] = useState<CaseRecord | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Navigation
    const [currentStepKey, setCurrentStepKey] = useState(STEPS[0].key)

    const [playbooks, setPlaybooks] = useState<Playbook[]>([])
    const [suggestions, setSuggestions] = useState<CaseSuggestion[]>([])
    const [documents, setDocuments] = useState<CaseDocument[]>([])
    const [flags, setFlags] = useState<CaseFlag[]>([])
    const [links, setLinks] = useState<CaseLink[]>([])
    const [legalHolds, setLegalHolds] = useState<CaseLegalHold[]>([])
    const [expertAccess, setExpertAccess] = useState<CaseExpertAccess[]>([])
    const [reporterMessages, setReporterMessages] = useState<CaseReporterMessage[]>([])
    const [auditEvents, setAuditEvents] = useState<CaseAuditEvent[]>([])

    const [piiUnlocked, setPiiUnlocked] = useState(false)

    const fetchCase = useCallback(async () => {
        if (!caseId) return
        try {
            const res = await apiFetch(`/cases/${caseId}`)
            if (res.ok) {
                const data = await res.json()
                setCaseData(data)
                setError(null)
            } else {
                setError('Failed to load case')
            }
        } catch (err) {
            setError('Network error')
        }
    }, [caseId])

    const fetchAuxiliary = useCallback(async () => {
        if (!caseId) return

        // Parallel fetch for non-critical data
        const endpoints = [
            { url: `/cases/playbooks`, setter: setPlaybooks, default: [] },
            { url: `/cases/${caseId}/suggestions`, setter: setSuggestions, default: [] },
            { url: `/cases/${caseId}/documents`, setter: setDocuments, default: [] },
            { url: `/cases/${caseId}/flags`, setter: setFlags, default: [] },
            { url: `/cases/${caseId}/links`, setter: setLinks, default: [] },
            { url: `/cases/${caseId}/legal-holds`, setter: setLegalHolds, default: [] },
            { url: `/cases/${caseId}/experts`, setter: setExpertAccess, default: [] },
            { url: `/cases/${caseId}/reporter-messages`, setter: setReporterMessages, default: [] },
            { url: `/audit?case_id=${caseId}`, setter: setAuditEvents, default: [] },
        ]

        await Promise.all(endpoints.map(ep =>
            apiFetch(ep.url)
                .then(res => res.ok ? res.json() : ep.default)
                .then(data => ep.setter(data || ep.default))
                .catch(() => ep.setter(ep.default))
        ))
    }, [caseId])

    const refreshCase = useCallback(async () => {
        await fetchCase()
    }, [fetchCase])

    const refreshDocuments = useCallback(async () => {
        if (!caseId) return
        apiFetch(`/cases/${caseId}/documents`)
            .then(res => res.json())
            .then(setDocuments)
            .catch(() => { })
    }, [caseId])

    const refreshFlags = useCallback(async () => {
        if (!caseId) return
        apiFetch(`/cases/${caseId}/flags`)
            .then(res => res.json())
            .then(setFlags)
            .catch(() => { })
    }, [caseId])

    const refreshLinks = useCallback(async () => {
        if (!caseId) return
        apiFetch(`/cases/${caseId}/links`)
            .then(res => res.json())
            .then(setLinks)
            .catch(() => { })
    }, [caseId])

    const refreshAudit = useCallback(async () => {
        if (!caseId) return
        apiFetch(`/audit?case_id=${caseId}`)
            .then(res => res.json())
            .then(setAuditEvents)
            .catch(() => { })
    }, [caseId])

    useEffect(() => {
        if (caseId) {
            setLoading(true)
            Promise.all([fetchCase(), fetchAuxiliary()])
                .finally(() => setLoading(false))
        }
    }, [caseId, fetchCase, fetchAuxiliary])

    // Computed properties
    const isBelgiumCase = (caseData?.jurisdiction || '').toLowerCase().includes('belgium')
    const hasRoleSeparationConflict = false

    const currentStep = STEPS.find(s => s.key === currentStepKey) || STEPS[0]

    const contextValue = React.useMemo(() => ({
        caseId,
        caseData,
        loading,
        error,
        currentStep,
        setCurrentStepKey,
        steps: STEPS,
        playbooks,
        suggestions,
        documents,
        flags,
        links,
        legalHolds,
        expertAccess,
        reporterMessages,
        auditEvents,
        piiUnlocked,
        refreshCase,
        refreshDocuments,
        refreshFlags,
        refreshLinks,
        refreshAudit,
        hasRoleSeparationConflict,
        isBelgiumCase,
        setPiiUnlocked
    }), [
        caseId, caseData, loading, error, currentStep,
        playbooks, suggestions, documents, flags, links,
        legalHolds, expertAccess, reporterMessages, auditEvents,
        piiUnlocked, refreshCase, refreshDocuments, refreshFlags,
        refreshLinks, refreshAudit, hasRoleSeparationConflict,
        isBelgiumCase
    ])

    return (
        <CaseContext.Provider value={contextValue}>
            {children}
        </CaseContext.Provider>
    )
}
