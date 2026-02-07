import React from 'react'
import { useParams } from 'react-router-dom'

import { CaseProvider, useCase } from './cases/context/CaseContext'
import { CaseSidebar } from './cases/components/CaseSidebar'
import { CaseIntake } from './cases/components/CaseIntake'
import { CaseLegitimacy } from './cases/components/CaseLegitimacy'
import { CaseCredentialing } from './cases/components/CaseCredentialing'
import { CaseInvestigation } from './cases/components/CaseInvestigation'
import { CaseAdversarial } from './cases/components/CaseAdversarial'
import { CaseDecision } from './cases/components/CaseDecision'

const CaseFlowContent: React.FC = () => {
  const { caseData, loading, error, currentStep } = useCase()

  if (loading) return <div>Loading case...</div>
  if (error) return <div className="error-message">Error: {error}</div>
  if (!caseData) return <div>Case not found</div>

  const renderStep = () => {
    switch (currentStep.key) {
      case 'intake': return <CaseIntake />
      case 'legitimacy': return <CaseLegitimacy />
      case 'credentialing': return <CaseCredentialing />
      case 'investigation': return <CaseInvestigation />
      case 'adversarial': return <CaseAdversarial />
      case 'decision': return <CaseDecision />
      default: return <CaseIntake />
    }
  }

  return (
    <div className="case-flow-container">
      <CaseSidebar />
      <div className="case-flow-main">
        {renderStep()}
      </div>
    </div>
  )
}

const CaseFlow: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>()

  return (
    <>
      {caseId ? (
        <CaseProvider caseId={caseId}>
          <CaseFlowContent />
        </CaseProvider>
      ) : (
        <div>No case ID provided</div>
      )}
    </>
  )
}

export default CaseFlow
