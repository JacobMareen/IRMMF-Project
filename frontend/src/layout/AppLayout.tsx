import { useEffect, useMemo, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import './AppLayout.css'

const AppLayout = () => {
  const [logoSrc, setLogoSrc] = useState<string | null>(null)
  const [theme, setTheme] = useState<string>('dark')
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const navigate = useNavigate()

  useEffect(() => {
    const storedTheme = localStorage.getItem('theme') || 'dark'
    setTheme(storedTheme)
    document.documentElement.setAttribute('data-theme', storedTheme)
    setLogoSrc(localStorage.getItem('irmmf_logo_data'))

    const handleStorage = (event: StorageEvent) => {
      if (event.key === 'theme') {
        const next = event.newValue || 'dark'
        setTheme(next)
        document.documentElement.setAttribute('data-theme', next)
      }
      if (event.key === 'irmmf_logo_data') {
        setLogoSrc(event.newValue)
      }
      if (event.key === 'irmmf_user' && !event.newValue) {
        navigate('/login')
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  useEffect(() => {
    const updateModalState = () => {
      const hasModal = Boolean(document.querySelector('.modal.active'))
      document.body.classList.toggle('modal-open', hasModal)
    }
    updateModalState()
    const observer = new MutationObserver(updateModalState)
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class'],
    })
    return () => {
      observer.disconnect()
      document.body.classList.remove('modal-open')
    }
  }, [])

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light'
    setTheme(next)
    document.documentElement.setAttribute('data-theme', next)
    localStorage.setItem('theme', next)
  }

  const handleLogout = () => {
    localStorage.removeItem('irmmf_user')
    localStorage.removeItem('irmmf_token')
    localStorage.removeItem('irmmf_roles')
    localStorage.removeItem('irmmf_tenant')
    localStorage.removeItem('assessment_id')
    if (currentUser) {
      localStorage.removeItem(`assessment_id_${currentUser}`)
    }
    window.dispatchEvent(new Event('irmmf_user_change'))
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          {logoSrc ? <img className="brand-logo" src={logoSrc} alt="IRMMF logo" /> : null}
          <span className="brand-mark">IRMMF</span>
          <span className="brand-sub">Command Center</span>
        </div>
        <nav className="top-nav">
          <NavLink to="/" end className="top-link">
            Command Center
          </NavLink>
          <NavLink to="/assessment" className="top-link">
            Assessment Hub
          </NavLink>
          <NavLink to="/insider-risk-program" className="top-link">
            Insider Risk Program
          </NavLink>
          <NavLink to="/workforce" className="top-link">
            Workforce
          </NavLink>
          <NavLink to="/case-management" className="top-link">
            Case Management
          </NavLink>
          <NavLink to="/settings" className="top-link">
            Settings
          </NavLink>
          <button className="top-link theme-toggle" onClick={toggleTheme} title="Toggle Light/Dark Mode">
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          <button className="top-link theme-toggle" onClick={handleLogout}>
            Logout
          </button>
        </nav>
      </header>
      <div className="app-body">
        <aside className="side-nav">
          <NavLink to="/" end className="side-link">
            Command Center
          </NavLink>
          <NavLink to="/assessment" className="side-link">
            Assessment Hub
          </NavLink>
          <NavLink to="/insider-risk-program" className="side-link">
            Insider Risk Program
          </NavLink>
          <NavLink to="/workforce" className="side-link">
            Dynamic Workforce
          </NavLink>
          <NavLink to="/case-management" className="side-link">
            Case Management
          </NavLink>
          <NavLink to="/settings" className="side-link">
            Platform Settings
          </NavLink>
        </aside>
        <main className="app-content">
          <Outlet />
        </main>
      </div>
      <footer className="app-footer">© 2026 Belfort Advisory. All rights reserved.</footer>
    </div>
  )
}

export default AppLayout
