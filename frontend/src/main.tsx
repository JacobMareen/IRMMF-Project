import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

const originalFetch = window.fetch.bind(window)
window.fetch = (input, init = {}) => {
  const url = typeof input === 'string' ? input : input.url
  const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined))
  if (url.includes('/api/v1/')) {
    const token = localStorage.getItem('irmmf_token')
    const roles = localStorage.getItem('irmmf_roles')
    const tenant = localStorage.getItem('irmmf_tenant') || 'default'
    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    if (roles && !headers.has('X-IRMMF-ROLES')) {
      headers.set('X-IRMMF-ROLES', roles)
    }
    if (!headers.has('X-IRMMF-KEY')) {
      headers.set('X-IRMMF-KEY', tenant)
    }
  }
  return originalFetch(input, { ...init, headers })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
