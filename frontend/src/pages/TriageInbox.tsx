import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import './TriageInbox.css'

type TriageTicket = {
  id: number
  ticket_id: string
  tenant_key: string
  subject?: string | null
  message: string
  reporter_name?: string | null
  reporter_email?: string | null
  source: string
  status: string
  triage_notes?: string | null
  linked_case_id?: string | null
  created_at: string
  updated_at: string
}

const STATUS_FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'new', label: 'New' },
  { value: 'triaged', label: 'Triaged' },
  { value: 'closed', label: 'Closed' },
]

const TriageInbox = () => {
  const [tickets, setTickets] = useState<TriageTicket[]>([])
  const [status, setStatus] = useState('')
  const [filter, setFilter] = useState('new')
  const [busyId, setBusyId] = useState<string | null>(null)
  const navigate = useNavigate()

  const [tenantKey, setTenantKey] = useState<string>('')

  useEffect(() => {
    try {
      const userStr = localStorage.getItem('irmmf_user')
      if (userStr) {
        const user = JSON.parse(userStr)
        if (user.tenant_key) {
          setTenantKey(user.tenant_key)
        }
      }
    } catch (e) {
      console.error('Failed to parse user', e)
    }
  }, [])

  const publicUrl = useMemo(() => {
    const baseUrl = `${location.origin}/external/dropbox`
    return tenantKey ? `${baseUrl}?tenant_key=${tenantKey}` : baseUrl
  }, [tenantKey])

  const loadTickets = () => {
    setStatus('Loading inbox...')
    const params = new URLSearchParams()
    if (filter !== 'all') {
      params.set('status', filter)
    }
    const path = params.toString() ? `/triage/inbox?${params.toString()}` : '/triage/inbox'
    apiFetch(path)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: TriageTicket[]) => {
        setTickets(data || [])
        setStatus('')
      })
      .catch(() => setStatus('Unable to load triage inbox. Check API status.'))
  }

  useEffect(() => {
    loadTickets()
  }, [filter])

  const convertTicket = (ticketId: string) => {
    setBusyId(ticketId)
    setStatus('Creating case...')
    apiFetch(`/triage/inbox/${ticketId}/convert`, { method: 'POST' })
      .then(async (res) => {
        if (!res.ok) throw new Error('Unable to create case')
        const data = await res.json()
        return data as { case_id?: string }
      })
      .then((data) => {
        setStatus('Case created.')
        loadTickets()
        if (data?.case_id) {
          navigate(`/cases/${data.case_id}/flow`)
        }
      })
      .catch(() => setStatus('Unable to create case.'))
      .finally(() => setBusyId(null))
  }

  const updateTicketStatus = (ticketId: string, nextStatus: string) => {
    setBusyId(ticketId)
    apiFetch(`/triage/inbox/${ticketId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: nextStatus }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Update failed')
        return res.json()
      })
      .then(() => {
        setStatus('Triage status updated.')
        loadTickets()
      })
      .catch(() => setStatus('Unable to update triage status.'))
      .finally(() => setBusyId(null))
  }

  const copyPublicUrl = async () => {
    try {
      await navigator.clipboard.writeText(publicUrl)
      setStatus('Public inbox URL copied.')
    } catch {
      setStatus('Copy failed. You can manually share the URL.')
    }
  }

  return (
    <section className="triage-page">
      <div className="triage-header">
        <div>
          <h2>Triage Inbox</h2>
          <p className="triage-subtitle">
            Secure, unlinked submissions waiting for review and conversion into cases.
          </p>
        </div>
        <div className="triage-actions">
          <div className="triage-url">
            <span>Public inbox URL</span>
            <strong>{publicUrl}</strong>
            <button className="triage-btn ghost" onClick={copyPublicUrl}>
              Copy
            </button>
          </div>
        </div>
      </div>

      <div className="triage-toolbar">
        <div className="triage-filter">
          <span>Status</span>
          <div className="triage-pills">
            {STATUS_FILTERS.map((option) => (
              <button
                key={option.value}
                className={`triage-pill${filter === option.value ? ' active' : ''}`}
                onClick={() => setFilter(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        {status ? <div className="triage-status">{status}</div> : null}
      </div>

      <div className="triage-grid">
        {tickets.length === 0 ? (
          <div className="triage-card empty">No inbox items match this filter.</div>
        ) : (
          tickets.map((ticket) => (
            <div key={ticket.ticket_id} className="triage-card">
              <div className="triage-card-header">
                <div>
                  <div className="triage-ticket">{ticket.ticket_id}</div>
                  <h3>{ticket.subject || 'General inquiry'}</h3>
                  <div className="triage-meta">
                    {new Date(ticket.created_at).toLocaleString()} · {ticket.source}
                  </div>
                </div>
                <span className={`triage-tag ${ticket.status}`}>{ticket.status}</span>
              </div>
              <p className="triage-message">{ticket.message}</p>
              {(ticket.reporter_name || ticket.reporter_email) && (
                <div className="triage-reporter">
                  {ticket.reporter_name || 'Reporter'}
                  {ticket.reporter_email ? ` · ${ticket.reporter_email}` : ''}
                </div>
              )}
              <div className="triage-card-actions">
                {ticket.linked_case_id ? (
                  <button
                    className="triage-btn"
                    onClick={() => navigate(`/cases/${ticket.linked_case_id}/flow`)}
                  >
                    Open case {ticket.linked_case_id}
                  </button>
                ) : (
                  <button
                    className="triage-btn"
                    disabled={busyId === ticket.ticket_id}
                    onClick={() => convertTicket(ticket.ticket_id)}
                  >
                    Create case
                  </button>
                )}
                {ticket.status !== 'closed' ? (
                  <button
                    className="triage-btn ghost"
                    disabled={busyId === ticket.ticket_id}
                    onClick={() => updateTicketStatus(ticket.ticket_id, 'closed')}
                  >
                    Close
                  </button>
                ) : (
                  <button
                    className="triage-btn ghost"
                    disabled={busyId === ticket.ticket_id}
                    onClick={() => updateTicketStatus(ticket.ticket_id, 'new')}
                  >
                    Reopen
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  )
}

export default TriageInbox
