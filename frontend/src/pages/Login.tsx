import { useEffect, useState } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import './Login.css'
import { apiFetch } from '../lib/api'

const DEFAULT_TENANT_KEY = 'default'

const Login = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // State
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [tenantKey, setTenantKey] = useState('')
  const [status, setStatus] = useState('Enter your email to sign in.')

  useEffect(() => {
    // Check if already logged in
    const user = localStorage.getItem('irmmf_user')
    if (user) {
      navigate('/', { replace: true })
    }

    // Auto-fill from URL or params
    const emailParam = searchParams.get('email')
    if (emailParam) setUsername(emailParam)

    const tenantParam = searchParams.get('tenant')
    if (tenantParam) {
      setTenantKey(tenantParam)
    } else {
      // Fallback to stored tenant or default
      const storedTenant = localStorage.getItem('irmmf_tenant')
      setTenantKey(storedTenant || DEFAULT_TENANT_KEY)
    }

  }, [navigate, searchParams])

  useEffect(() => {
    const storedTheme = localStorage.getItem('theme') || 'dark'
    document.documentElement.setAttribute('data-theme', storedTheme)
  }, [])

  const handleLogin = async () => {
    const user = username.trim()
    const tKey = tenantKey.trim() || DEFAULT_TENANT_KEY

    if (!user) {
      setStatus('Enter an email address.')
      return
    }
    setStatus('Signing in...')
    try {
      const resp = await apiFetch(`/auth/login?tenant_key=${tKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: user,
          password: password.trim() || null,
        }),
      })
      if (!resp.ok) {
        setStatus('Login failed. Check your email or invite status.')
        return
      }
      const data = (await resp.json()) as {
        user?: { email?: string; roles?: { role: string }[] }
        token?: string
      }
      const storedUser = data?.user?.email || user
      localStorage.setItem('irmmf_user', storedUser)
      if (data?.token) {
        localStorage.setItem('irmmf_token', data.token)
      }
      const roles = data?.user?.roles?.map((role) => role.role).join(',') || ''
      if (roles) {
        localStorage.setItem('irmmf_roles', roles)
      }

      // Save the tenant key used for login
      localStorage.setItem('irmmf_tenant', tKey)

      window.dispatchEvent(new Event('irmmf_user_change'))
      try {
        const latestResp = await apiFetch(`/assessment/user/${storedUser}/latest`)
        if (latestResp.ok) {
          const latest = (await latestResp.json()) as { assessment_id?: string }
          if (latest.assessment_id) {
            localStorage.setItem(`assessment_id_${storedUser}`, latest.assessment_id)
            localStorage.setItem('assessment_id', latest.assessment_id)
          }
        } else if (latestResp.status === 404) {
          const createResp = await apiFetch(`/assessment/new`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: storedUser }),
          })
          if (createResp.ok) {
            const created = (await createResp.json()) as { assessment_id?: string }
            if (created.assessment_id) {
              localStorage.setItem(`assessment_id_${storedUser}`, created.assessment_id)
              localStorage.setItem('assessment_id', created.assessment_id)
            }
          }
        }
      } catch {
        setStatus('Signed in, but unable to resolve assessment ID. Check API status.')
      }
      navigate('/', { replace: true })
    } catch {
      setStatus('Login failed. Check API status.')
    }
  }

  return (
    <section className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1>IRMMF Command Center</h1>
          <p>Authentication required to access the platform.</p>
        </div>
        <div className="login-form">
          <label>
            Tenant Context
            <input
              type="text"
              placeholder="default"
              value={tenantKey}
              onChange={(event) => setTenantKey(event.target.value)}
            />
          </label>
          <label>
            Email
            <input
              type="text"
              placeholder="user@example.com"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              placeholder="Optional"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <button className="login-btn" onClick={handleLogin}>
            Sign In
          </button>

          <div className="login-status">{status}</div>

          <div className="login-link" style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
            <p style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Don't have a workspace?</p>
            <Link to="/register" style={{ color: 'var(--primary-color)', textDecoration: 'none', fontWeight: 600 }}>
              Create New Tenant
            </Link>
          </div>

        </div>
      </div>
    </section>
  )
}

export default Login
