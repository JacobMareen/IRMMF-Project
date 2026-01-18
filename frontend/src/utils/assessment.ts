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
