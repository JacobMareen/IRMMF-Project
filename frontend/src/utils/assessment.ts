export const getStoredAssessmentId = (userId?: string | null): string => {
  if (userId) {
    const byUser = localStorage.getItem(`assessment_id_${userId}`)
    if (byUser) return byUser
  }
  return localStorage.getItem('assessment_id') || ''
}

export const storeAssessmentId = (assessmentId: string, userId?: string | null) => {
  if (!assessmentId) return
  localStorage.setItem('assessment_id', assessmentId)
  if (userId) {
    localStorage.setItem(`assessment_id_${userId}`, assessmentId)
  }
}

export const clearStoredAssessmentId = (assessmentId?: string | null, userId?: string | null) => {
  if (assessmentId) {
    localStorage.removeItem(`role_lens_${assessmentId}`)
    localStorage.removeItem(`override_domains_${assessmentId}`)
    localStorage.removeItem(`intake_answered_${assessmentId}`)
    localStorage.removeItem(`intake_total_${assessmentId}`)
  }
  if (userId) {
    localStorage.removeItem(`assessment_id_${userId}`)
  }
  localStorage.removeItem('assessment_id')
}

export const describeAssessmentError = (detail: string | undefined | null, fallback: string) => {
  const message = (detail || '').trim()
  if (!message) return fallback
  const normalized = message.toLowerCase()
  if (normalized.includes('intake tables are empty')) {
    return 'Intake question bank is empty. Load the intake questions in the database and refresh the page.'
  }
  if (normalized.includes('assessment not found')) {
    return 'Assessment not found. Return to the Assessment Hub and start a new assessment.'
  }
  if (normalized.includes('no assessments found')) {
    return 'No assessments found for this user yet. Start a new assessment from the hub.'
  }
  if (
    normalized.includes('failed to fetch') ||
    normalized.includes('network') ||
    normalized.includes('connection') ||
    normalized.includes('connection refused')
  ) {
    return 'Unable to reach the API. Ensure the backend is running, then refresh.'
  }
  return `${fallback} ${message}`
}
