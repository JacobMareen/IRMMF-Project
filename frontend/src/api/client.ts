export const API_ROOT = (() => {
  const fallback =
    location.hostname === '127.0.0.1' || location.hostname === 'localhost'
      ? 'http://localhost:8000'
      : 'http://0.0.0.0:8000'
  const fromEnv = import.meta.env.VITE_API_ROOT
  console.log('[IRMMF] API_ROOT:', (fromEnv || fallback).replace(/\/$/, ''))
  return (fromEnv || fallback).replace(/\/$/, '')
})()

export const API_BASE = (() => {
  const fallback = `${API_ROOT}/api/v1`
  const fromEnv = import.meta.env.VITE_API_BASE
  return (fromEnv || fallback).replace(/\/$/, '')
})()

type RequestOptions = RequestInit & {
  authenticated?: boolean
}

class ApiClient {
  private clearAuth(): void {
    const currentUser = localStorage.getItem('irmmf_user') || ''
    localStorage.removeItem('irmmf_user')
    localStorage.removeItem('irmmf_token')
    localStorage.removeItem('irmmf_roles')
    localStorage.removeItem('irmmf_tenant')
    localStorage.removeItem('assessment_id')
    if (currentUser) {
      localStorage.removeItem(`assessment_id_${currentUser}`)
    }
  }

  private getAuthHeaders(): Headers {
    const headers = new Headers()
    const token = localStorage.getItem('irmmf_token')
    const roles = localStorage.getItem('irmmf_roles')
    const tenant = localStorage.getItem('irmmf_tenant') || 'default'

    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    if (roles) {
      headers.set('X-IRMMF-ROLES', roles)
    }
    headers.set('X-IRMMF-KEY', tenant)

    return headers
  }

  private buildUrl(path: string, root = false): string {
    const base = root ? API_ROOT : API_BASE
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path
    }
    const cleanPath = path.startsWith('/') ? path.substring(1) : path
    return `${base}/${cleanPath}`
  }

  async fetch(path: string, options: RequestOptions = {}, root = false): Promise<Response> {
    const url = this.buildUrl(path, root)
    const headers = new Headers(options.headers)

    if (options.authenticated !== false) {
      const authHeaders = this.getAuthHeaders()
      authHeaders.forEach((val, key) => {
        if (!headers.has(key)) {
          headers.set(key, val)
        }
      })
    }

    const config = {
      ...options,
      headers
    }

    // Antigravity Fix: Prevent browser caching of API responses
    if (!headers.has('Cache-Control')) {
      headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
    }
    if (!headers.has('Pragma')) {
      headers.set('Pragma', 'no-cache')
    }
    if (!headers.has('Expires')) {
      headers.set('Expires', '0')
    }

    const res = await fetch(url, config)
    if (res.status === 401 && options.authenticated !== false) {
      this.clearAuth()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.assign('/login')
      }
    }
    return res
  }

  async get<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const res = await this.fetch(path, { ...options, method: 'GET' })
    if (!res.ok) throw await this.readError(res)
    const text = await res.text()
    return (text ? JSON.parse(text) : null) as T
  }

  async post<T>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
    const headers = new Headers(options.headers)
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }

    const res = await this.fetch(path, {
      ...options,
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    })

    if (!res.ok) throw await this.readError(res)
    const text = await res.text()
    return (text ? JSON.parse(text) : null) as T
  }

  async put<T>(path: string, body: unknown, options: RequestOptions = {}): Promise<T> {
    const headers = new Headers(options.headers)
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }

    const res = await this.fetch(path, {
      ...options,
      method: 'PUT',
      headers,
      body: JSON.stringify(body)
    })

    if (!res.ok) throw await this.readError(res)
    const text = await res.text()
    return (text ? JSON.parse(text) : null) as T
  }

  async delete<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const res = await this.fetch(path, { ...options, method: 'DELETE' })
    if (!res.ok) throw await this.readError(res)
    const text = await res.text()
    return (text ? JSON.parse(text) : null) as T
  }

  async readError(res: Response): Promise<Error> {
    const text = await res.text()
    if (!text) return new Error(`Request failed (${res.status})`)
    try {
      const data = JSON.parse(text) as { detail?: string; message?: string }
      return new Error(data.detail || data.message || text)
    } catch {
      return new Error(text)
    }
  }
}

export const client = new ApiClient()
