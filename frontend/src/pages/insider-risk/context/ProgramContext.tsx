import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react'

import { apiJson } from '../../../lib/api'
import { getStoredAssessmentId } from '../../../utils/assessment'
import {
    type InsiderRiskPolicy,
    type Control,
    type Recommendation
} from '../types'
import { DEFAULT_POLICY, DEFAULT_CONTROLS } from '../constants'

interface ProgramContextType {
    // Policy State
    policy: InsiderRiskPolicy
    policyLoading: boolean
    policySaving: boolean
    policyTemplate: boolean
    policyDraft: InsiderRiskPolicy | null
    policyError: string | null
    setPolicyDraft: (policy: InsiderRiskPolicy | null) => void
    updatePolicyDraft: (patch: Partial<InsiderRiskPolicy>) => void
    savePolicy: (policy: InsiderRiskPolicy) => Promise<void>

    // Control State
    controls: Control[]
    controlsLoading: boolean
    controlsError: string | null
    controlDraft: Control | null
    setControlDraft: (control: Control | null) => void
    updateControlDraft: (patch: Partial<Control>) => void
    saveControl: (mode: 'create' | 'edit') => Promise<void>
    refreshControls: () => Promise<void>

    // Recommendation State
    recommendations: Recommendation[]
    actionsLoading: boolean
    refreshRecommendations: () => Promise<void>
    categories: string[]

    // Filters
    filters: {
        assessment: string
        priority: string
        status: string
        category: string
    }
    setFilters: (filters: { assessment: string; priority: string; status: string; category: string }) => void
    controlFilters: {
        domain: string
        status: string
    }
    setControlFilters: (filters: { domain: string; status: string }) => void

    // Meta
    assessmentId: string
    currentUser: string
}

const ProgramContext = createContext<ProgramContextType | undefined>(undefined)

export const useProgram = () => {
    const context = useContext(ProgramContext)
    if (!context) {
        throw new Error('useProgram must be used within a ProgramProvider')
    }
    return context
}

export const ProgramProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
    const [assessmentId, setAssessmentId] = useState<string>('')

    // Policy State
    const [policy, setPolicy] = useState<InsiderRiskPolicy>(DEFAULT_POLICY)
    const [policyLoading, setPolicyLoading] = useState(true)
    const [policySaving, setPolicySaving] = useState(false)
    const [policyTemplate, setPolicyTemplate] = useState(true)
    const [policyDraft, setPolicyDraft] = useState<InsiderRiskPolicy | null>(null)
    const [policyError, setPolicyError] = useState<string | null>(null)

    // Control State
    const [controls, setControls] = useState<Control[]>(DEFAULT_CONTROLS)
    const [controlsLoading, setControlsLoading] = useState(true)
    const [controlsSeeded, setControlsSeeded] = useState(false)
    const [controlsError, setControlsError] = useState<string | null>(null)
    const [controlDraft, setControlDraft] = useState<Control | null>(null)

    // Action State
    const [recommendations, setRecommendations] = useState<Recommendation[]>([])
    const [actionsLoading, setActionsLoading] = useState(true)
    const [categories, setCategories] = useState<string[]>([])

    // Filters
    const [filters, setFilters] = useState({
        assessment: '',
        priority: '',
        status: '',
        category: '',
    })
    const [controlFilters, setControlFilters] = useState({ domain: '', status: '' })

    useEffect(() => {
        setAssessmentId(getStoredAssessmentId(currentUser))
    }, [currentUser])

    // --- Helpers ---

    const normalizeDate = (value?: string) => (value ? value : null)

    const normalizePolicy = useCallback((incoming?: Partial<InsiderRiskPolicy>) => {
        const merged = { ...DEFAULT_POLICY, ...(incoming || {}) }
        merged.principles = Array.isArray(incoming?.principles) ? incoming!.principles : DEFAULT_POLICY.principles
        merged.sections = Array.isArray(incoming?.sections) ? incoming!.sections : DEFAULT_POLICY.sections
        return merged
    }, [])

    const normalizeControl = useCallback((control: Control): Control => ({
        ...control,
        linked_actions: control.linked_actions ?? [],
        linked_rec_ids: control.linked_rec_ids ?? [],
        linked_categories: control.linked_categories ?? [],
    }), [])

    // --- Loaders ---

    const loadPolicy = useCallback(async () => {
        setPolicyLoading(true)
        setPolicyError(null)
        try {
            const data = await apiJson<InsiderRiskPolicy>('/insider-program/policy')
            setPolicy(normalizePolicy(data))
            setPolicyTemplate(Boolean(data.is_template))
        } catch {
            setPolicy(normalizePolicy())
            setPolicyTemplate(true)
            setPolicyError('Policy template loaded locally.')
        } finally {
            setPolicyLoading(false)
        }
    }, [normalizePolicy])

    const seedControls = useCallback(async () => {
        if (controlsSeeded) {
            return DEFAULT_CONTROLS.map(normalizeControl)
        }
        setControlsSeeded(true)
        try {
            const results = await Promise.allSettled(
                DEFAULT_CONTROLS.map((control) =>
                    apiJson<Control>('/insider-program/controls', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            ...control,
                            last_reviewed: normalizeDate(control.last_reviewed),
                            next_review: normalizeDate(control.next_review),
                            linked_actions: control.linked_actions ?? [],
                            linked_rec_ids: control.linked_rec_ids ?? [],
                            linked_categories: control.linked_categories ?? [],
                        }),
                    }),
                ),
            )
            const created = results
                .filter((result): result is PromiseFulfilledResult<Control> => result.status === 'fulfilled')
                .map((result) => normalizeControl(result.value))
            return created.length ? created : DEFAULT_CONTROLS.map(normalizeControl)
        } catch {
            return DEFAULT_CONTROLS.map(normalizeControl)
        }
    }, [controlsSeeded, normalizeControl])

    const loadControls = useCallback(async () => {
        setControlsLoading(true)
        setControlsError(null)
        try {
            const data = await apiJson<Control[]>('/insider-program/controls')
            if (!data.length) {
                const seeded = await seedControls()
                setControls(seeded)
            } else {
                setControls(data.map(normalizeControl))
            }
        } catch {
            setControlsError('Control register unavailable.')
            setControls(DEFAULT_CONTROLS.map(normalizeControl))
        } finally {
            setControlsLoading(false)
        }
    }, [normalizeControl, seedControls])

    const loadLibraryCategories = useCallback(async () => {
        try {
            const data = await apiJson<Recommendation[]>('/recommendations/library')
            const unique = Array.from(new Set(data.map((rec) => rec.category).filter(Boolean)))
            setCategories(unique)
        } catch {
            setCategories([])
        }
    }, [])

    const loadRecommendations = useCallback(async () => {
        setActionsLoading(true)
        const targetAssessment = filters.assessment || assessmentId
        try {
            let data: Recommendation[] = []
            if (!targetAssessment) {
                data = await apiJson<Recommendation[]>('/recommendations/library')
                data = data.map((rec) => ({ ...rec, status: 'pending' }))
            } else {
                data = await apiJson<Recommendation[]>(`/assessment/${targetAssessment}/recommendations`)
            }
            setRecommendations(data)
        } catch {
            setRecommendations([])
        } finally {
            setActionsLoading(false)
        }
    }, [assessmentId, filters.assessment])

    // --- Initial Load ---

    useEffect(() => {
        loadLibraryCategories()
        loadPolicy()
        loadControls()
    }, [loadLibraryCategories, loadPolicy, loadControls])

    useEffect(() => {
        loadRecommendations()
    }, [loadRecommendations])

    // --- Actions ---

    const savePolicy = async (nextPolicy: InsiderRiskPolicy) => {
        setPolicySaving(true)
        setPolicyError(null)
        try {
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { is_template: _isTemplate, ...policyBody } = nextPolicy
            const payload = {
                ...policyBody,
                last_reviewed: normalizeDate(nextPolicy.last_reviewed),
                next_review: normalizeDate(nextPolicy.next_review),
                principles: nextPolicy.principles || [],
                sections: nextPolicy.sections || [],
            }
            const saved = await apiJson<InsiderRiskPolicy>('/insider-program/policy', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            setPolicy(normalizePolicy(saved))
            setPolicyTemplate(Boolean(saved.is_template))
            setPolicyDraft(null)
        } catch {
            setPolicyError('Failed to save policy.')
        } finally {
            setPolicySaving(false)
        }
    }

    const updatePolicyDraft = (patch: Partial<InsiderRiskPolicy>) => {
        setPolicyDraft((prev) => (prev ? { ...prev, ...patch } : prev))
    }

    const updateControlDraft = (patch: Partial<Control>) => {
        setControlDraft((prev) => (prev ? { ...prev, ...patch } : prev))
    }

    const saveControl = async (mode: 'create' | 'edit') => {
        if (!controlDraft) return
        try {
            const payload = {
                ...controlDraft,
                last_reviewed: normalizeDate(controlDraft.last_reviewed),
                next_review: normalizeDate(controlDraft.next_review),
                linked_actions: controlDraft.linked_actions ?? [],
                linked_rec_ids: controlDraft.linked_rec_ids ?? [],
                linked_categories: controlDraft.linked_categories ?? [],
            }
            let saved: Control
            if (mode === 'create') {
                saved = await apiJson<Control>('/insider-program/controls', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
            } else {
                saved = await apiJson<Control>(`/insider-program/controls/${controlDraft.control_id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
            }
            setControls((prev) => {
                const normalized = normalizeControl(saved)
                if (mode === 'create') {
                    return [normalized, ...prev]
                }
                return prev.map((control) =>
                    control.control_id === normalized.control_id ? normalized : control,
                )
            })
            setControlsError(null)
            setControlDraft(null)
        } catch {
            setControlsError('Failed to save control.')
        }
    }

    const value = useMemo(() => ({
        policy,
        policyLoading,
        policySaving,
        policyTemplate,
        policyDraft,
        policyError,
        setPolicyDraft,
        updatePolicyDraft,
        savePolicy,
        controls,
        controlsLoading,
        controlsError,
        controlDraft,
        setControlDraft,
        updateControlDraft,
        saveControl,
        refreshControls: loadControls,
        recommendations,
        actionsLoading,
        refreshRecommendations: loadRecommendations,
        categories,
        filters,
        setFilters,
        controlFilters,
        setControlFilters,
        assessmentId,
        currentUser
    }), [
        policy, policyLoading, policySaving, policyTemplate, policyDraft, policyError,
        controls, controlsLoading, controlsError, controlDraft,
        recommendations, actionsLoading, categories,
        filters, controlFilters, assessmentId, currentUser,
        loadControls, loadRecommendations
    ])

    return <ProgramContext.Provider value={value}>{children}</ProgramContext.Provider>
}
