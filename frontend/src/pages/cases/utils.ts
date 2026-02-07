
export const computeRiskScore = (triage: any): number => {
    let score = 0
    if (triage.risk_level === 'High') score += 50
    if (triage.risk_level === 'Medium') score += 30
    if (triage.risk_level === 'Low') score += 10

    // Add more logic as per requirement

    return score
}

export const maskFieldValue = (value: any) => {
    // Implement masking logic if needed, or just return value
    return value
}

// Helper for piiUnlocked which is passed down from top level usually
export const maskText = (value: string | undefined | null, fallback = 'Hidden', piiUnlocked = false) => {
    if (!value) return ''
    return piiUnlocked ? value : fallback
}

export const toLocalInput = (isoString?: string | null) => {
    if (!isoString) return ''
    // Assuming ISO string "YYYY-MM-DDTHH:mm:ss..."
    // input type="datetime-local" expects "YYYY-MM-DDTHH:mm"
    return isoString.slice(0, 16)
}

export const normalizeName = (name?: string | null) => name?.trim().toLowerCase() || ''
