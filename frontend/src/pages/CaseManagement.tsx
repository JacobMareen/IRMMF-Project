import { NavLink, Outlet } from 'react-router-dom'
import './CaseManagement.css'

const CaseManagement = () => {
  return (
    <section className="case-mgmt-page">
      <div className="case-mgmt-header">
        <div>
          <h1>Case Management</h1>
          <p className="case-mgmt-subtitle">
            Compliance governance, investigation workflows, and operational notifications.
          </p>
        </div>
      </div>
      <div className="case-mgmt-tabs">
        <NavLink
          to="/case-management/compliance"
          className={({ isActive }) => `case-mgmt-tab${isActive ? ' active' : ''}`}
        >
          Compliance
        </NavLink>
        <NavLink
          to="/case-management/cases"
          className={({ isActive }) => `case-mgmt-tab${isActive ? ' active' : ''}`}
        >
          Cases
        </NavLink>
        <NavLink
          to="/case-management/notifications"
          className={({ isActive }) => `case-mgmt-tab${isActive ? ' active' : ''}`}
        >
          Notifications
        </NavLink>
      </div>
      <div className="case-mgmt-content">
        <Outlet />
      </div>
    </section>
  )
}

export default CaseManagement
