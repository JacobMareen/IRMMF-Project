import { useEffect, useState } from 'react'
import { apiFetch, apiFetchRoot, readApiError } from '../lib/api'
import { describeAssessmentError } from '../utils/assessment'

export type ResumptionState = {
    completion_pct?: number
    reachable_path?: string[]
    responses?: Record<string, string>
    deferred_ids?: string[]
    flagged_ids?: string[]
}

export type RiskPoint = {
    id?: string
    scenario?: string
    name?: string
    likelihood?: number
    impact?: number
    risk_level?: string
}

type ResultsPayload = {
    risk_heatmap?: unknown[]
    top_risks?: unknown[]
}

type AssessmentData = {
    completionPct: number | null
    intakeAnswered: number | null
    intakeTotal: number | null
    topRisk: string
    heatmapCount: number | null
    riskHeatmap: RiskPoint[]
    resumeState: ResumptionState | null
    statusNote: string
    loading: boolean
    target_maturity?: Record<string, number>
}

export const useAssessmentData = (
    assessmentId: string,
    currentUser: string,
    onReset?: (note: string) => void
) => {
    const [data, setData] = useState<AssessmentData>({
        completionPct: null,
        intakeAnswered: null,
        intakeTotal: null,
        topRisk: '—',
        heatmapCount: null,
        riskHeatmap: [],
        resumeState: null,
        statusNote: '',
        loading: false,
        target_maturity: {},
    })

    // Helper to update specific fields
    const updateData = (fields: Partial<AssessmentData>) => {
        setData((prev) => ({ ...prev, ...fields }))
    }

    const triggerReset = (note: string) => {
        updateData({
            completionPct: null,
            intakeAnswered: null,
            intakeTotal: null,
            topRisk: '—',
            heatmapCount: null,
            riskHeatmap: [],
            resumeState: null,
            statusNote: note,
        })
        if (onReset) onReset(note)
    }

    useEffect(() => {
        if (!assessmentId) return
        const controller = new AbortController()
        updateData({ loading: true, statusNote: '' })

        Promise.allSettled([
            apiFetch(`/assessment/${assessmentId}/resume`, { signal: controller.signal }),
            apiFetch(`/intake/${assessmentId}`, { signal: controller.signal }),
            apiFetch(`/intake/start`, { signal: controller.signal }),
            apiFetchRoot(`/responses/analysis/${assessmentId}`, {
                signal: controller.signal,
            }),
        ])
            .then(async ([resumeResp, intakeResp, intakeStartResp, riskResp]) => {
                const nextState: Partial<AssessmentData> = { loading: false }

                if (resumeResp.status === 'fulfilled' && resumeResp.value.status === 404) {
                    triggerReset('Assessment not found. Creating a new one...')
                    return
                }

                let anyOk = false

                if (resumeResp.status === 'fulfilled' && resumeResp.value.ok) {
                    const state = (await resumeResp.value.json()) as ResumptionState & { target_maturity?: Record<string, number> }
                    nextState.completionPct = state.completion_pct ?? null
                    nextState.resumeState = state
                    nextState.target_maturity = state.target_maturity || {}
                    anyOk = true
                }

                if (intakeResp.status === 'fulfilled' && intakeResp.value.ok) {
                    const intakeRows = (await intakeResp.value.json()) as Array<{ value?: string | null }>
                    nextState.intakeAnswered = intakeRows.filter((row) => row.value != null && row.value !== '').length
                    anyOk = true
                } else {
                    const storedAnswered = localStorage.getItem(`intake_answered_${assessmentId}`)
                    nextState.intakeAnswered = storedAnswered ? Number(storedAnswered) : null
                }

                if (intakeStartResp.status === 'fulfilled' && intakeStartResp.value.ok) {
                    const intakeQs = (await intakeStartResp.value.json()) as unknown[]
                    nextState.intakeTotal = Array.isArray(intakeQs) ? intakeQs.length : null
                    anyOk = true
                } else {
                    const storedTotal = localStorage.getItem(`intake_total_${assessmentId}`)
                    nextState.intakeTotal = storedTotal ? Number(storedTotal) : null
                }

                if (riskResp.status === 'fulfilled' && riskResp.value.ok) {
                    const payload = (await riskResp.value.json()) as ResultsPayload
                    const heatmap = Array.isArray(payload.risk_heatmap) ? (payload.risk_heatmap as RiskPoint[]) : []
                    nextState.riskHeatmap = heatmap
                    nextState.heatmapCount = heatmap.length
                    const top = (Array.isArray(payload.top_risks) ? payload.top_risks : []) as RiskPoint[]
                    const label = top[0]?.scenario || top[0]?.name || '—'
                    nextState.topRisk = label
                    anyOk = true
                }

                if (!anyOk) {
                    let detail = ''
                    if (intakeStartResp.status === 'fulfilled' && !intakeStartResp.value.ok) {
                        detail = await readApiError(intakeStartResp.value)
                    } else if (resumeResp.status === 'fulfilled' && !resumeResp.value.ok) {
                        detail = await readApiError(resumeResp.value)
                    } else if (riskResp.status === 'fulfilled' && !riskResp.value.ok) {
                        detail = await readApiError(riskResp.value)
                    }
                    nextState.statusNote = describeAssessmentError(detail, 'Assessment data unavailable.')
                }

                updateData(nextState)
            })
            .catch(() => {
                const storedAnswered = localStorage.getItem(`intake_answered_${assessmentId}`)
                const storedTotal = localStorage.getItem(`intake_total_${assessmentId}`)
                updateData({
                    loading: false,
                    statusNote: 'Unable to reach the API. Ensure the backend is running, then refresh.',
                    intakeAnswered: storedAnswered ? Number(storedAnswered) : null,
                    intakeTotal: storedTotal ? Number(storedTotal) : null
                })
            })

        return () => controller.abort()
    }, [assessmentId])

    return {
        ...data,
        setStatusNote: (note: string) => updateData({ statusNote: note })
    }
}
