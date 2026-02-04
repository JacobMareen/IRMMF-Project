import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { API_ROOT } from '../lib/api'
import './ExternalInbox.css'

type ExternalMessage = {
  id: number
  sender: string
  body: string
  created_at: string
}

type ExternalInboxResponse = {
  case_id: string
  external_report_id?: string | null
  messages: ExternalMessage[]
}

const ExternalInbox = () => {
  const [searchParams] = useSearchParams()
  const caseId = useMemo(() => (searchParams.get('case_id') || '').trim(), [searchParams])
  const token = useMemo(() => (searchParams.get('token') || '').trim(), [searchParams])
  const [data, setData] = useState<ExternalInboxResponse | null>(null)
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)

  const load = () => {
    if (!caseId || !token) {
      setStatus('Missing case ID or access token.')
      return
    }
    setLoading(true)
    fetch(`${API_ROOT}/api/external/inbox?case_id=${encodeURIComponent(caseId)}&token=${encodeURIComponent(token)}`)
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then((payload: ExternalInboxResponse) => {
        setData(payload)
        setStatus('')
      })
      .catch(async (err) => {
        if (err?.text) {
          const text = await err.text()
          setStatus(text || 'Unable to load inbox.')
        } else {
          setStatus('Unable to load inbox.')
        }
      })
      .finally(() => setLoading(false))
  }

  const sendMessage = () => {
    if (!caseId || !token) {
      setStatus('Missing case ID or access token.')
      return
    }
    if (!message.trim()) {
      setStatus('Enter a message before sending.')
      return
    }
    setLoading(true)
    fetch(`${API_ROOT}/api/external/inbox?case_id=${encodeURIComponent(caseId)}&token=${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body: message.trim() }),
    })
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then(() => {
        setMessage('')
        load()
      })
      .catch(async (err) => {
        if (err?.text) {
          const text = await err.text()
          setStatus(text || 'Unable to send message.')
        } else {
          setStatus('Unable to send message.')
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (caseId && token) {
      load()
    } else if (!caseId && !token) {
      setStatus('Enter a case ID and token in the URL to access the inbox.')
    }
  }, [caseId, token])

  return (
    <main className="external-inbox">
      <div className="external-inbox-shell">
        <header>
          <h1>Secure Inbox</h1>
          <p>Confidential two-way message thread for investigation communications.</p>
        </header>
        <section className="external-inbox-card">
          <div className="external-inbox-row">
            <div>
              <div className="external-inbox-label">Case</div>
              <div className="external-inbox-value">{caseId || '—'}</div>
            </div>
            <button className="external-inbox-btn outline" onClick={load} disabled={loading}>
              Refresh
            </button>
          </div>
          {status ? <div className="external-inbox-status">{status}</div> : null}
          {!data ? (
            <div className="external-inbox-muted">Load the inbox to see messages.</div>
          ) : (
            <>
              {data.external_report_id ? (
                <div className="external-inbox-muted">Report ref: {data.external_report_id}</div>
              ) : null}
              <div className="external-inbox-thread">
                {data.messages.length === 0 ? (
                  <div className="external-inbox-muted">No messages yet.</div>
                ) : (
                  data.messages.map((msg) => (
                    <div key={msg.id} className={`external-inbox-message ${msg.sender}`}>
                      <div className="external-inbox-meta">
                        {msg.sender} · {new Date(msg.created_at).toLocaleString()}
                      </div>
                      <div>{msg.body}</div>
                    </div>
                  ))
                )}
              </div>
              <div className="external-inbox-compose">
                <label>
                  Your message
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Type your message here..."
                    disabled={loading}
                  />
                </label>
                <button className="external-inbox-btn" onClick={sendMessage} disabled={loading}>
                  Send message
                </button>
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  )
}

export default ExternalInbox
