import React from 'react'
import { STEPS } from '../constants'
import { useCase } from '../context/CaseContext'

export const CaseSidebar: React.FC = () => {
    const { currentStep, setCurrentStepKey } = useCase()

    return (
        <div className="case-flow-sidebar">
            {STEPS.map((item) => (
                <button
                    key={item.key}
                    className={`case-flow-step ${currentStep.key === item.key ? 'active' : ''}`}
                    onClick={() => setCurrentStepKey(item.key)}
                >
                    {item.label}
                </button>
            ))}
        </div>
    )
}
