import { useEffect, useMemo, useState } from 'react'
import './Settings.css'
import { getStoredAssessmentId } from '../utils/assessment'

const BRAND_LOGO_KEY = 'irmmf_logo_data'
const API_BASE = 'http://127.0.0.1:8000/api/v1'

const Settings = () => {
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [logo, setLogo] = useState<string | null>(null)
  const [resetId, setResetId] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => {
    setLogo(localStorage.getItem(BRAND_LOGO_KEY))
    setResetId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  const handleLogoUpload = (file?: File | null) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file.')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      const value = typeof reader.result === 'string' ? reader.result : null
      if (!value) return
      localStorage.setItem(BRAND_LOGO_KEY, value)
      setLogo(value)
    }
    reader.readAsDataURL(file)
  }

  const clearLogo = () => {
    localStorage.removeItem(BRAND_LOGO_KEY)
    setLogo(null)
  }

  const resetAssessment = async () => {
    if (!resetId.trim()) {
      alert('Enter an assessment ID to reset.')
      return
    }
    const ok = confirm(
      'Remove all saved answers, intake data, evidence, and snapshots for this assessment? This cannot be undone.'
    )
    if (!ok) return
    try {
      const resp = await fetch(`${API_BASE}/assessment/${encodeURIComponent(resetId.trim())}/reset`, {
        method: 'POST',
      })
      if (!resp.ok) throw new Error('Reset failed')
      localStorage.removeItem(`intake_completed_${resetId}`)
      if (resetId === localStorage.getItem('assessment_id')) {
        localStorage.removeItem('assessment_id')
      }
      if (currentUser) {
        const userKey = `assessment_id_${currentUser}`
        if (resetId === localStorage.getItem(userKey)) {
          localStorage.removeItem(userKey)
        }
      }
      setStatus('Assessment data cleared.')
    } catch {
      setStatus('Reset failed. Check server logs.')
    }
  }

  return (
    <section className="settings-page">
      <div className="settings-title">Platform Settings</div>
      <div className="settings-grid">
        <div className="settings-card">
          <h4>Branding</h4>
          <p className="mini-note">Upload a logo that appears across the entire environment.</p>
          <div className="logo-row">
            {logo ? <img src={logo} alt="Logo preview" /> : null}
            <div className="mini-note">PNG, JPG, or SVG recommended.</div>
          </div>
          <input
            type="file"
            accept="image/*"
            onChange={(event) => handleLogoUpload(event.target.files?.[0])}
          />
          <div className="btn-row">
            <button className="btn secondary" onClick={clearLogo}>
              Use default
            </button>
          </div>
        </div>

        <div className="settings-card">
          <h4>User Profile</h4>
          <label>
            Contact email
            <input type="email" placeholder="you@company.com" />
          </label>
          <label>
            Change password
            <input type="password" placeholder="New password" />
          </label>
          <div className="btn-row">
            <button className="btn secondary">Update Profile</button>
          </div>
        </div>

        <div className="settings-card">
          <h4>Tenant / Environment</h4>
          <label>
            Tenant name
            <input type="text" placeholder="IRMMF Production" />
          </label>
          <label>
            Environment type
            <select>
              <option>Production</option>
              <option>Staging</option>
              <option>Sandbox</option>
            </select>
          </label>
          <div className="btn-row">
            <button className="btn secondary">Save Tenant</button>
          </div>
        </div>

        <div className="settings-card">
          <h4>Company & Users</h4>
          <label>
            Company name
            <input type="text" placeholder="Company name" />
          </label>
          <label>
            Add user (email)
            <input type="email" placeholder="user@company.com" />
          </label>
          <label>
            Assign role
            <select>
              <option>Admin</option>
              <option>Manager</option>
              <option>Reader</option>
            </select>
          </label>
          <div className="btn-row">
            <button className="btn secondary">Invite User</button>
          </div>
        </div>

        <div className="settings-card">
          <h4>Module Access</h4>
          <div className="toggle-row">
            <span>Assessment Hub</span>
            <input type="checkbox" defaultChecked />
          </div>
          <div className="toggle-row">
            <span>Dynamic Workforce</span>
            <input type="checkbox" defaultChecked />
          </div>
          <div className="toggle-row">
            <span>Future Modules</span>
            <input type="checkbox" />
          </div>
          <div className="btn-row">
            <button className="btn secondary">Apply Changes</button>
          </div>
        </div>

        <div className="settings-card">
          <h4>Security</h4>
          <div className="toggle-row">
            <span>Enable MFA (coming soon)</span>
            <input type="checkbox" disabled />
          </div>
          <div className="mini-note">MFA configuration will be enabled once authentication is integrated.</div>
        </div>

        <div className="settings-card">
          <h4>Assessment Reset</h4>
          <div className="mini-note">
            This permanently deletes answers, intake data, evidence, and snapshots for an assessment.
          </div>
          <label>
            Assessment ID
            <input
              type="text"
              value={resetId}
              onChange={(event) => setResetId(event.target.value)}
              placeholder="IRMMF-..."
            />
          </label>
          <div className="btn-row">
            <button className="btn secondary danger" onClick={resetAssessment}>
              Remove Data (Permanent)
            </button>
          </div>
          {status ? <div className="status-note">{status}</div> : null}
        </div>
      </div>
    </section>
  )
}

export default Settings
