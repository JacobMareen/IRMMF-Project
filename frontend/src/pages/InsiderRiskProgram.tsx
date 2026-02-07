
import { ProgramProvider } from './insider-risk/context/ProgramContext'
import { type InsiderRiskProgramView } from './insider-risk/types'

import PolicyManager from './insider-risk/components/PolicyManager'
import ControlRegister from './insider-risk/components/ControlRegister'
import ActionPlan from './insider-risk/components/ActionPlan'

const InsiderRiskContent = ({ view }: { view: InsiderRiskProgramView }) => {
  const showPolicy = view === 'overview' || view === 'policy'
  const showControls = view === 'overview' || view === 'controls'
  const showActions = view === 'overview' || view === 'actions'

  return (
    <div className="recommendations-page">
      {showPolicy && <PolicyManager />}
      {showControls && <ControlRegister />}
      {showActions && <ActionPlan />}
    </div>
  )
}

const InsiderRiskProgram = ({ view = 'overview' }: { view?: InsiderRiskProgramView }) => {
  return (
    <ProgramProvider>
      <InsiderRiskContent view={view} />
    </ProgramProvider>
  )
}

export default InsiderRiskProgram
