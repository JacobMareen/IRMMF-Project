import { NavLink, Outlet } from 'react-router-dom'
import './InsiderRiskProgramLayout.css'
import './InsiderRiskProgram.css'

const InsiderRiskProgramLayout = () => {
  return (
    <section className="irp-shell">
      <div className="irp-shell-header">
        <div>
          <h1>Insider Risk Program</h1>
          <p className="irp-shell-subtitle">
            Policy governance, control assurance, risk intelligence, and action delivery.
          </p>
        </div>
      </div>
      <div className="irp-shell-tabs">
        <NavLink
          to="/insider-risk-program/policy"
          className={({ isActive }) => `irp-shell-tab${isActive ? ' active' : ''}`}
        >
          Policy
        </NavLink>
        <NavLink
          to="/insider-risk-program/controls"
          className={({ isActive }) => `irp-shell-tab${isActive ? ' active' : ''}`}
        >
          Controls
        </NavLink>
        <NavLink
          to="/insider-risk-program/risks"
          className={({ isActive }) => `irp-shell-tab${isActive ? ' active' : ''}`}
        >
          Risks
        </NavLink>
        <NavLink
          to="/insider-risk-program/roadmap"
          className={({ isActive }) => `irp-shell-tab${isActive ? ' active' : ''}`}
        >
          Roadmap
        </NavLink>
        <NavLink
          to="/insider-risk-program/actions"
          className={({ isActive }) => `irp-shell-tab${isActive ? ' active' : ''}`}
        >
          Actions
        </NavLink>
        <NavLink
          to="/insider-risk-program/resources"
          className={({ isActive }) => `irp-shell-tab${isActive ? ' active' : ''}`}
        >
          Resources
        </NavLink>
      </div>
      <div className="irp-shell-content">
        <Outlet />
      </div>
    </section>
  )
}

export default InsiderRiskProgramLayout
