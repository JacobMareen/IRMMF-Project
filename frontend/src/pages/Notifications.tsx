import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Notifications.css'
import { apiFetch, apiJson } from '../lib/api'

type NotificationItem = {
  id: number
  case_id: string
  tenant_key: string
  notification_type: string
  severity: string
  message: string
  recipient_role?: string | null
  status: string
  due_at?: string | null
  sent_at?: string | null
  acknowledged_at?: string | null
  acknowledged_by?: string | null
  created_at: string
}

const Notifications = () => {
  const [items, setItems] = useState<NotificationItem[]>([])
  const [status, setStatus] = useState('')
  const navigate = useNavigate()

  const loadNotifications = () => {
    apiJson<NotificationItem[]>('/notifications')
      .then((data) => setItems(data || []))
      .catch(() => setItems([]))
  }

  useEffect(() => {
    loadNotifications()
  }, [])

  const acknowledge = (id: number) => {
    apiFetch(`/notifications/${id}/ack`, { method: 'POST' })
      .then((res) => (res.ok ? res.json() : null))
      .then(() => {
        setStatus('Notification acknowledged.')
        loadNotifications()
      })
      .catch(() => setStatus('Unable to acknowledge notification.'))
  }

  const formatDate = (value?: string | null) => (value ? new Date(value).toLocaleString() : '--')

  return (
    <section className="notifications-page">
      <div className="notifications-header">
        <div>
          <h1>Notifications</h1>
          <p className="notifications-subtitle">Serious-cause milestones and compliance alerts.</p>
        </div>
        <button className="notifications-btn outline" onClick={loadNotifications}>
          Refresh
        </button>
      </div>
      {status ? <div className="notifications-status">{status}</div> : null}
      <div className="notifications-list">
        {items.length === 0 ? (
          <div className="notifications-muted">No notifications yet.</div>
        ) : (
          items.map((item) => (
            <div key={item.id} className={`notifications-item ${item.severity}`}>
              <div className="notifications-meta">
                <span className="notifications-tag">{item.notification_type}</span>
                <span className="notifications-tag">{item.status}</span>
                {item.recipient_role ? <span className="notifications-tag">{item.recipient_role}</span> : null}
              </div>
              <div className="notifications-message">{item.message}</div>
              <div className="notifications-details">
                <span>Case: {item.case_id}</span>
                <span>Due: {formatDate(item.due_at)}</span>
                <span>Sent: {formatDate(item.sent_at)}</span>
                <span>Created: {formatDate(item.created_at)}</span>
              </div>
              <div className="notifications-actions">
                <button className="notifications-btn" onClick={() => navigate(`/cases/${item.case_id}/flow/intake`)}>
                  Open Case
                </button>
                {item.status !== 'acknowledged' ? (
                  <button className="notifications-btn outline" onClick={() => acknowledge(item.id)}>
                    Acknowledge
                  </button>
                ) : (
                  <span className="notifications-muted">
                    Acknowledged by {item.acknowledged_by || 'user'} ({formatDate(item.acknowledged_at)})
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  )
}

export default Notifications
