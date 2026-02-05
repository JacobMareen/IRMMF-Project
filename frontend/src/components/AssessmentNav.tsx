import { NavLink, useLocation } from 'react-router-dom'
import './AssessmentNav.css'

type AssessmentNavProps = {
    assessmentId?: string
}

export const AssessmentNav = ({ assessmentId }: AssessmentNavProps) => {
    const location = useLocation()

    // Only disable if no assessment ID exists (except for Hub which is always open)
    const isDisabled = !assessmentId

    return (
        <nav className="an-nav">
            <NavLink to="/assessment" end className={({ isActive }) => `an-link ${isActive ? 'active' : ''}`}>
                Dashboard
            </NavLink>
            <NavLink
                to="/assessment/intake"
                className={({ isActive }) => `an-link ${isActive ? 'active' : ''} ${isDisabled ? 'disabled' : ''}`}
                onClick={(e) => isDisabled && e.preventDefault()}
            >
                Intake
            </NavLink>
            <NavLink
                to="/assessment/flow"
                className={({ isActive }) => `an-link ${isActive ? 'active' : ''} ${isDisabled ? 'disabled' : ''}`}
                onClick={(e) => isDisabled && e.preventDefault()}
            >
                Question Flow
            </NavLink>
            <NavLink
                to="/assessment/results"
                className={({ isActive }) => `an-link ${isActive ? 'active' : ''} ${isDisabled ? 'disabled' : ''}`}
                onClick={(e) => isDisabled && e.preventDefault()}
            >
                Results
            </NavLink>
            <NavLink
                to="/insider-risk-program/risks"
                className={({ isActive }) => `an-link ${isActive ? 'active' : ''} ${isDisabled ? 'disabled' : ''}`}
                onClick={(e) => isDisabled && e.preventDefault()}
            >
                Risks
            </NavLink>
        </nav >
    )
}
