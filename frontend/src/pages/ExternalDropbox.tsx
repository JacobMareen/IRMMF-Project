import { useState } from 'react'
import { API_ROOT } from '../lib/api'
import './ExternalDropbox.css'

const ExternalDropbox = () => {
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState('')
  const [ticketId, setTicketId] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = () => {
    if (!message.trim()) {
      setStatus('Please describe your concern or tip before submitting.')
      return
    }
    setLoading(true)
    setStatus('Submitting...')
    fetch(`${API_ROOT}/api/external/dropbox`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject: subject.trim() || null,
        message: message.trim(),
        reporter_name: name.trim() || null,
        reporter_email: email.trim() || null,
        source: 'dropbox',
      }),
    })
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then((data: { ticket_id?: string }) => {
        setTicketId(data.ticket_id || '')
        setStatus('Submission received. Your report has been logged.')
        setSubject('')
        setMessage('')
        setName('')
        setEmail('')
      })
      .catch(async (err) => {
        if (err?.text) {
          const text = await err.text()
          setStatus(text || 'Unable to submit. Please try again later.')
        } else {
          setStatus('Unable to submit. Please try again later.')
        }
      })
      .finally(() => setLoading(false))
  }

  return (
    <main className="external-dropbox">
      <div className="external-dropbox-shell">
        <header>
          <h1>Secure Dropbox</h1>
          <p>Submit a confidential tip or concern. This inbox is reviewed by investigators.</p>
        </header>
        <section className="external-dropbox-card">
          {status ? <div className="external-dropbox-status">{status}</div> : null}
          {ticketId ? (
            <div className="external-dropbox-ticket">
              Reference ID: <strong>{ticketId}</strong>
            </div>
          ) : null}
          <div className="external-dropbox-grid">
            <label>
              Subject (optional)
              <input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Short summary"
                disabled={loading}
              />
            </label>
            <label>
              Your name (optional)
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Anonymous"
                disabled={loading}
              />
            </label>
            <label>
              Email (optional)
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                disabled={loading}
              />
            </label>
          </div>
          <label>
            Message
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Describe the concern, who is involved, and any relevant dates."
              disabled={loading}
            />
          </label>
          <button className="external-dropbox-btn" onClick={submit} disabled={loading}>
            {loading ? 'Submitting...' : 'Submit securely'}
          </button>
          <div className="external-dropbox-muted">
            Attachments are not enabled in this MVP. If you need to provide files, mention it in your message.
          </div>
        </section>
      </div>
    </main>
  )
}

export default ExternalDropbox
