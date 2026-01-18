import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Login.css'

const TEST_USER = 'test'
const TEST_PASS = 'test123'
const API_BASE = 'http://127.0.0.1:8000/api/v1'

const Login = () => {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('Use credentials: test / test123')

  useEffect(() => {
    const user = localStorage.getItem('irmmf_user')
    if (user) {
      navigate('/', { replace: true })
    }
  }, [navigate])

  useEffect(() => {
    const storedTheme = localStorage.getItem('theme') || 'dark'
    document.documentElement.setAttribute('data-theme', storedTheme)
  }, [])

  const handleLogin = async () => {
    const user = username.trim()
    const pass = password.trim()
    if (user === TEST_USER && pass === TEST_PASS) {
      localStorage.setItem('irmmf_user', user)
      window.dispatchEvent(new Event('irmmf_user_change'))
      try {
        const latestResp = await fetch(`${API_BASE}/assessment/user/${user}/latest`)
        if (latestResp.ok) {
          const latest = (await latestResp.json()) as { assessment_id?: string }
          if (latest.assessment_id) {
            localStorage.setItem(`assessment_id_${user}`, latest.assessment_id)
            localStorage.setItem('assessment_id', latest.assessment_id)
          }
        } else if (latestResp.status === 404) {
          const createResp = await fetch(`${API_BASE}/assessment/new`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user }),
          })
          if (createResp.ok) {
            const created = (await createResp.json()) as { assessment_id?: string }
            if (created.assessment_id) {
              localStorage.setItem(`assessment_id_${user}`, created.assessment_id)
              localStorage.setItem('assessment_id', created.assessment_id)
            }
          }
        }
      } catch {
        setStatus('Signed in, but unable to resolve assessment ID. Check API status.')
      }
      navigate('/', { replace: true })
      return
    }
    setStatus('Invalid credentials. Use test / test123.')
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
            Username
            <input
              type="text"
              placeholder="test"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              placeholder="test123"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <button className="login-btn" onClick={handleLogin}>
            Sign In
          </button>
          <div className="login-status">{status}</div>
        </div>
      </div>
    </section>
  )
}

export default Login
