import { useEffect, useMemo, useState } from 'react'
import './Settings.css'
import { getStoredAssessmentId } from '../utils/assessment'
import { apiFetch, apiJson } from '../lib/api'

const BRAND_LOGO_KEY = 'irmmf_logo_data'
const DEFAULT_TENANT_KEY = 'default'

type TenantSettings = {
  tenant_key: string
  tenant_name: string
  environment_type: string
  company_name?: string | null
  default_jurisdiction: string
  investigation_mode: string
  retention_days: number
  keyword_flagging_enabled: boolean
  keyword_list: string[]
  weekend_days: number[]
  saturday_is_business_day: boolean
  deadline_cutoff_hour: number
  notifications_enabled: boolean
  serious_cause_notifications_enabled: boolean
  jurisdiction_rules: Record<string, unknown>
  updated_at: string
}

type UserRole = { role: string }
type UserEntry = {
  id: string
  email: string
  display_name?: string | null
  status: string
  roles: UserRole[]
  invited_at: string
  last_login_at?: string | null
}

const Settings = () => {
  const currentUser = useMemo(() => localStorage.getItem('irmmf_user') || '', [])
  const [logo, setLogo] = useState<string | null>(null)
  const [resetId, setResetId] = useState('')
  const [status, setStatus] = useState('')
  const [tenantSettings, setTenantSettings] = useState<TenantSettings | null>(null)
  const [tenantStatus, setTenantStatus] = useState('')
  const [keywordText, setKeywordText] = useState('')
  const [jurisdictionRulesText, setJurisdictionRulesText] = useState('')
  const [users, setUsers] = useState<UserEntry[]>([])
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteName, setInviteName] = useState('')
  const [inviteRole, setInviteRole] = useState('INVESTIGATOR')
  const [inviteStatus, setInviteStatus] = useState('')
  const [roleEdits, setRoleEdits] = useState<Record<string, string>>({})
  const [holidays, setHolidays] = useState<{ id: number; holiday_date: string; label?: string | null }[]>([])
  const [holidayDate, setHolidayDate] = useState('')
  const [holidayLabel, setHolidayLabel] = useState('')

  useEffect(() => {
    setLogo(localStorage.getItem(BRAND_LOGO_KEY))
    setResetId(getStoredAssessmentId(currentUser))
  }, [currentUser])

  useEffect(() => {
    apiJson<TenantSettings>(`/tenant/settings?tenant_key=${DEFAULT_TENANT_KEY}`)
      .then((data) => {
        setTenantSettings({
          ...data,
          weekend_days: data.weekend_days || [5, 6],
          saturday_is_business_day: data.saturday_is_business_day ?? false,
          deadline_cutoff_hour: data.deadline_cutoff_hour ?? 17,
          notifications_enabled: data.notifications_enabled ?? true,
          serious_cause_notifications_enabled: data.serious_cause_notifications_enabled ?? true,
          jurisdiction_rules: data.jurisdiction_rules || {},
        })
        setKeywordText((data.keyword_list || []).join(', '))
        setJurisdictionRulesText(JSON.stringify(data.jurisdiction_rules || {}, null, 2))
      })
      .catch(() => {
        setTenantStatus('Unable to load tenant settings. Check API status.')
      })
  }, [])

  useEffect(() => {
    apiJson<UserEntry[]>(`/users?tenant_key=${DEFAULT_TENANT_KEY}`)
      .then((data) => setUsers(data || []))
      .catch(() => {
        setInviteStatus('Unable to load users.')
      })
  }, [])

  useEffect(() => {
    apiJson(`/tenant/holidays?tenant_key=${DEFAULT_TENANT_KEY}`)
      .then((data) => setHolidays(data || []))
      .catch(() => {
        setTenantStatus('Unable to load holidays.')
      })
  }, [])

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
      const resp = await apiFetch(`/assessment/${encodeURIComponent(resetId.trim())}/reset`, {
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

  const saveTenantSettings = async () => {
    if (!tenantSettings) return
    setTenantStatus('Saving tenant settings...')
    const keywords = keywordText
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean)
    let rulesPayload: Record<string, unknown> = tenantSettings.jurisdiction_rules || {}
    if (jurisdictionRulesText.trim()) {
      try {
        rulesPayload = JSON.parse(jurisdictionRulesText)
      } catch {
        setTenantStatus('Jurisdiction rules JSON is invalid.')
        return
      }
    }
    const payload = {
      tenant_name: tenantSettings.tenant_name,
      environment_type: tenantSettings.environment_type,
      company_name: tenantSettings.company_name,
      default_jurisdiction: tenantSettings.default_jurisdiction,
      investigation_mode: tenantSettings.investigation_mode,
      retention_days: tenantSettings.retention_days,
      keyword_flagging_enabled: tenantSettings.keyword_flagging_enabled,
      keyword_list: keywords,
      weekend_days: tenantSettings.weekend_days,
      saturday_is_business_day: tenantSettings.saturday_is_business_day,
      deadline_cutoff_hour: tenantSettings.deadline_cutoff_hour,
      notifications_enabled: tenantSettings.notifications_enabled,
      serious_cause_notifications_enabled: tenantSettings.serious_cause_notifications_enabled,
      jurisdiction_rules: rulesPayload,
    }
    try {
      const resp = await apiFetch(`/tenant/settings?tenant_key=${DEFAULT_TENANT_KEY}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!resp.ok) throw new Error('Save failed')
      const updated = (await resp.json()) as TenantSettings
      setTenantSettings(updated)
      setKeywordText((updated.keyword_list || []).join(', '))
      setJurisdictionRulesText(JSON.stringify(updated.jurisdiction_rules || {}, null, 2))
      setTenantStatus('Tenant settings saved.')
    } catch {
      setTenantStatus('Unable to save tenant settings.')
    }
  }

  const refreshUsers = async () => {
    try {
      const resp = await apiFetch(`/users?tenant_key=${DEFAULT_TENANT_KEY}`)
      if (!resp.ok) throw new Error('Fetch failed')
      const data = (await resp.json()) as UserEntry[]
      setUsers(data || [])
    } catch {
      setInviteStatus('Unable to load users.')
    }
  }

  const updateUserRole = async (userId: string) => {
    const role = roleEdits[userId]
    if (!role) {
      setInviteStatus('Select a role to update.')
      return
    }
    setInviteStatus('Updating role...')
    try {
      const resp = await apiFetch(`/users/${userId}/roles?tenant_key=${DEFAULT_TENANT_KEY}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roles: [role] }),
      })
      if (!resp.ok) throw new Error('Role update failed')
      setInviteStatus('Role updated.')
      refreshUsers()
    } catch {
      setInviteStatus('Role update failed.')
    }
  }

  const inviteUser = async () => {
    if (!inviteEmail.trim()) {
      setInviteStatus('Enter an email to invite.')
      return
    }
    setInviteStatus('Inviting user...')
    try {
      const resp = await apiFetch(`/users/invite?tenant_key=${DEFAULT_TENANT_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: inviteEmail.trim(),
          display_name: inviteName.trim() || null,
          role: inviteRole,
        }),
      })
      if (!resp.ok) throw new Error('Invite failed')
      setInviteEmail('')
      setInviteName('')
      setInviteStatus('Invite sent.')
      refreshUsers()
    } catch {
      setInviteStatus('Invite failed. Check API status.')
    }
  }

  const addHoliday = async () => {
    if (!holidayDate) {
      setTenantStatus('Select a holiday date.')
      return
    }
    try {
      const resp = await apiFetch(`/tenant/holidays?tenant_key=${DEFAULT_TENANT_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ holiday_date: holidayDate, label: holidayLabel || null }),
      })
      if (!resp.ok) throw new Error('Holiday add failed')
      const created = await resp.json()
      setHolidays((prev) => [...prev, created].sort((a, b) => a.holiday_date.localeCompare(b.holiday_date)))
      setHolidayDate('')
      setHolidayLabel('')
      setTenantStatus('Holiday added.')
    } catch {
      setTenantStatus('Unable to add holiday.')
    }
  }

  const deleteHoliday = async (holidayId: number) => {
    try {
      const resp = await apiFetch(`/tenant/holidays/${holidayId}?tenant_key=${DEFAULT_TENANT_KEY}`, {
        method: 'DELETE',
      })
      if (!resp.ok) throw new Error('Delete failed')
      setHolidays((prev) => prev.filter((item) => item.id !== holidayId))
      setTenantStatus('Holiday removed.')
    } catch {
      setTenantStatus('Unable to remove holiday.')
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
          {tenantSettings ? (
            <>
              <label>
                Tenant name
                <input
                  type="text"
                  value={tenantSettings.tenant_name}
                  onChange={(event) =>
                    setTenantSettings((prev) =>
                      prev ? { ...prev, tenant_name: event.target.value } : prev
                    )
                  }
                  placeholder="Default Tenant"
                />
              </label>
              <label>
                Environment type
                <select
                  value={tenantSettings.environment_type}
                  onChange={(event) =>
                    setTenantSettings((prev) =>
                      prev ? { ...prev, environment_type: event.target.value } : prev
                    )
                  }
                >
                  <option>Production</option>
                  <option>Staging</option>
                  <option>Sandbox</option>
                </select>
              </label>
              <label>
                Company name
                <input
                  type="text"
                  value={tenantSettings.company_name || ''}
                  onChange={(event) =>
                    setTenantSettings((prev) =>
                      prev ? { ...prev, company_name: event.target.value } : prev
                    )
                  }
                  placeholder="Company name"
                />
              </label>
              <label>
                Default jurisdiction
                <select
                  value={tenantSettings.default_jurisdiction}
                  onChange={(event) =>
                    setTenantSettings((prev) =>
                      prev ? { ...prev, default_jurisdiction: event.target.value } : prev
                    )
                  }
                >
                  <option>Belgium</option>
                  <option>Netherlands</option>
                  <option>Luxembourg</option>
                  <option>Ireland</option>
                  <option>EU (non-Belgium)</option>
                  <option>UK</option>
                  <option>US</option>
                </select>
              </label>
              <label>
                Investigation mode
                <select
                  value={tenantSettings.investigation_mode}
                  onChange={(event) =>
                    setTenantSettings((prev) =>
                      prev ? { ...prev, investigation_mode: event.target.value } : prev
                    )
                  }
                >
                  <option value="standard">Standard</option>
                  <option value="occasional">Occasional</option>
                  <option value="systematic">Systematic</option>
                </select>
              </label>
              <label>
                Retention days
                <input
                  type="number"
                  min={0}
                  value={tenantSettings.retention_days}
                  onChange={(event) =>
                    setTenantSettings((prev) =>
                      prev ? { ...prev, retention_days: Number(event.target.value) } : prev
                    )
                  }
                />
              </label>
              <label>
                Keyword flagging
                <div className="toggle-row">
                  <span>{tenantSettings.keyword_flagging_enabled ? 'Enabled' : 'Disabled'}</span>
                  <input
                    type="checkbox"
                    checked={tenantSettings.keyword_flagging_enabled}
                    onChange={(event) =>
                      setTenantSettings((prev) =>
                        prev ? { ...prev, keyword_flagging_enabled: event.target.checked } : prev
                      )
                    }
                  />
                </div>
              </label>
              <label>
                Keyword list (comma separated)
                <textarea
                  value={keywordText}
                  onChange={(event) => setKeywordText(event.target.value)}
                  placeholder="union, illness, politics"
                />
              </label>
              <div className="settings-divider" />
              <h5>Notifications</h5>
              <label>
                In-app notifications
                <div className="toggle-row">
                  <span>{tenantSettings.notifications_enabled ? 'Enabled' : 'Disabled'}</span>
                  <input
                    type="checkbox"
                    checked={tenantSettings.notifications_enabled}
                    onChange={(event) =>
                      setTenantSettings((prev) =>
                        prev ? { ...prev, notifications_enabled: event.target.checked } : prev
                      )
                    }
                  />
                </div>
              </label>
              <label>
                Serious-cause milestones
                <div className="toggle-row">
                  <span>{tenantSettings.serious_cause_notifications_enabled ? 'Enabled' : 'Disabled'}</span>
                  <input
                    type="checkbox"
                    checked={tenantSettings.serious_cause_notifications_enabled}
                    onChange={(event) =>
                      setTenantSettings((prev) =>
                        prev ? { ...prev, serious_cause_notifications_enabled: event.target.checked } : prev
                      )
                    }
                  />
                </div>
              </label>
              <div className="settings-divider" />
              <h5>Business-day rules (Belgium)</h5>
              <label>
                Deadline cutoff hour (0-23)
                <input
                  type="number"
                  min={0}
                  max={23}
                  value={tenantSettings.deadline_cutoff_hour}
                  onChange={(event) =>
                    setTenantSettings((prev) =>
                      prev ? { ...prev, deadline_cutoff_hour: Number(event.target.value) } : prev
                    )
                  }
                />
              </label>
              <label>
                Saturday counts as business day
                <div className="toggle-row">
                  <span>{tenantSettings.saturday_is_business_day ? 'Enabled' : 'Disabled'}</span>
                  <input
                    type="checkbox"
                    checked={tenantSettings.saturday_is_business_day}
                    onChange={(event) =>
                      setTenantSettings((prev) =>
                        prev ? { ...prev, saturday_is_business_day: event.target.checked } : prev
                      )
                    }
                  />
                </div>
              </label>
              <div className="settings-inline">
                <span className="mini-note">Weekend days</span>
                <label className="settings-check">
                  <input
                    type="checkbox"
                    checked={(tenantSettings.weekend_days || []).includes(5)}
                    onChange={(event) => {
                      const current = new Set(tenantSettings.weekend_days || [])
                      if (event.target.checked) current.add(5)
                      else current.delete(5)
                      setTenantSettings((prev) =>
                        prev ? { ...prev, weekend_days: Array.from(current).sort() } : prev
                      )
                    }}
                  />
                  Saturday
                </label>
                <label className="settings-check">
                  <input
                    type="checkbox"
                    checked={(tenantSettings.weekend_days || []).includes(6)}
                    onChange={(event) => {
                      const current = new Set(tenantSettings.weekend_days || [])
                      if (event.target.checked) current.add(6)
                      else current.delete(6)
                      setTenantSettings((prev) =>
                        prev ? { ...prev, weekend_days: Array.from(current).sort() } : prev
                      )
                    }}
                  />
                  Sunday
                </label>
              </div>
              <div className="settings-divider" />
              <h5>Jurisdiction rules engine</h5>
              <div className="mini-note">
                Configure per-country guardrails (deadlines, delivery method, cooling-off windows). JSON only.
              </div>
              <textarea
                value={jurisdictionRulesText}
                onChange={(event) => setJurisdictionRulesText(event.target.value)}
                placeholder='{"BE":{"decision_deadline_days":3,"dismissal_deadline_days":3,"deadline_type":"working_days"}}'
                rows={10}
              />
              <div className="settings-divider" />
              <h5>Public holidays</h5>
              <div className="settings-inline">
                <input
                  type="date"
                  value={holidayDate}
                  onChange={(event) => setHolidayDate(event.target.value)}
                />
                <input
                  type="text"
                  placeholder="Holiday label"
                  value={holidayLabel}
                  onChange={(event) => setHolidayLabel(event.target.value)}
                />
                <button className="btn secondary" onClick={addHoliday}>
                  Add Holiday
                </button>
              </div>
              <div className="settings-list">
                {holidays.length === 0 ? (
                  <div className="mini-note">No holidays configured.</div>
                ) : (
                  holidays.map((holiday) => (
                    <div key={holiday.id} className="settings-row">
                      <div>
                        <strong>{holiday.holiday_date}</strong>
                        <div className="mini-note">{holiday.label || 'Holiday'}</div>
                      </div>
                      <button className="btn secondary" onClick={() => deleteHoliday(holiday.id)}>
                        Remove
                      </button>
                    </div>
                  ))
                )}
              </div>
              <div className="btn-row">
                <button className="btn secondary" onClick={saveTenantSettings}>
                  Save Tenant Settings
                </button>
              </div>
              {tenantStatus ? <div className="status-note">{tenantStatus}</div> : null}
              <div className="mini-note">
                Tenant context is derived from login (placeholder: {DEFAULT_TENANT_KEY}).
              </div>
            </>
          ) : (
            <div className="mini-note">{tenantStatus || 'Loading tenant settings...'}</div>
          )}
        </div>

        <div className="settings-card">
          <h4>Company & Users</h4>
          <label>
            Invite user (email)
            <input
              type="email"
              placeholder="user@company.com"
              value={inviteEmail}
              onChange={(event) => setInviteEmail(event.target.value)}
            />
          </label>
          <label>
            Display name
            <input
              type="text"
              placeholder="First Last"
              value={inviteName}
              onChange={(event) => setInviteName(event.target.value)}
            />
          </label>
          <label>
            Assign role
            <select value={inviteRole} onChange={(event) => setInviteRole(event.target.value)}>
              <option value="ADMIN">Admin</option>
              <option value="INVESTIGATOR">Investigator</option>
              <option value="LEGAL">Legal</option>
              <option value="LEGAL_COUNSEL">Legal Counsel</option>
              <option value="HR">HR</option>
              <option value="EXTERNAL_EXPERT">External Expert</option>
              <option value="AUDITOR">Auditor</option>
              <option value="BE_AUTHORIZED">BE Authorized</option>
              <option value="DPO_AUDITOR">DPO Auditor</option>
              <option value="VIEWER">Viewer</option>
            </select>
          </label>
          <div className="btn-row">
            <button className="btn secondary" onClick={inviteUser}>
              Invite User
            </button>
            <button className="btn secondary" onClick={refreshUsers}>
              Refresh List
            </button>
          </div>
          {inviteStatus ? <div className="status-note">{inviteStatus}</div> : null}
          <div className="mini-note">Tenant scope: {DEFAULT_TENANT_KEY}</div>
          <div className="mini-note">Users</div>
          <div className="settings-list">
            {users.length === 0 ? (
              <div className="mini-note">No users yet.</div>
            ) : (
              users.map((user) => (
                <div key={user.id} className="settings-row">
                  <div>
                    <strong>{user.display_name || user.email}</strong>
                    <div className="mini-note">{user.email}</div>
                  </div>
                  <div className="settings-row-actions">
                    <div className="mini-note">
                      {user.roles.map((role) => role.role).join(', ') || 'No role'} · {user.status}
                    </div>
                    <select
                      value={roleEdits[user.id] || user.roles[0]?.role || 'VIEWER'}
                      onChange={(event) =>
                        setRoleEdits((prev) => ({ ...prev, [user.id]: event.target.value }))
                      }
                    >
                      <option value="ADMIN">Admin</option>
                      <option value="INVESTIGATOR">Investigator</option>
                      <option value="LEGAL">Legal</option>
                      <option value="LEGAL_COUNSEL">Legal Counsel</option>
                      <option value="HR">HR</option>
                      <option value="EXTERNAL_EXPERT">External Expert</option>
                      <option value="AUDITOR">Auditor</option>
                      <option value="BE_AUTHORIZED">BE Authorized</option>
                      <option value="DPO_AUDITOR">DPO Auditor</option>
                      <option value="VIEWER">Viewer</option>
                    </select>
                    <button className="btn secondary" onClick={() => updateUserRole(user.id)}>
                      Update Role
                    </button>
                  </div>
                </div>
              ))
            )}
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
            <span>Case Management</span>
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
