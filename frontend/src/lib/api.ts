export const API_ROOT = (() => {
  const fallback =
    location.hostname === '127.0.0.1' || location.hostname === 'localhost'
      ? 'http://127.0.0.1:8000'
      : 'http://0.0.0.0:8000'
  const fromEnv = import.meta.env.VITE_API_ROOT
  return (fromEnv || fallback).replace(/\/$/, '')
})()

export const API_BASE = (() => {
  const fallback = `${API_ROOT}/api/v1`
  const fromEnv = import.meta.env.VITE_API_BASE
  return (fromEnv || fallback).replace(/\/$/, '')
})()

const buildUrl = (base: string, path: string) => {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  if (!path.startsWith('/')) {
    return `${base}/${path}`
  }
  return `${base}${path}`
}

const withAuthHeaders = (headers?: HeadersInit) => {
  const merged = new Headers(headers)
  const token = localStorage.getItem('irmmf_token')
  const roles = localStorage.getItem('irmmf_roles')
  const tenant = localStorage.getItem('irmmf_tenant') || 'default'
  if (token && !merged.has('Authorization')) {
    merged.set('Authorization', `Bearer ${token}`)
  }
  if (roles && !merged.has('X-IRMMF-ROLES')) {
    merged.set('X-IRMMF-ROLES', roles)
  }
  if (!merged.has('X-IRMMF-KEY')) {
    merged.set('X-IRMMF-KEY', tenant)
  }
  return merged
}

export const apiFetch = (path: string, init: RequestInit = {}) => {
  const url = buildUrl(API_BASE, path)
  const headers = withAuthHeaders(init.headers)
  return fetch(url, { ...init, headers })
}

export const apiFetchRoot = (path: string, init: RequestInit = {}) => {
  const url = buildUrl(API_ROOT, path)
  const headers = withAuthHeaders(init.headers)
  return fetch(url, { ...init, headers })
}

const parseError = async (res: Response) => {
  const text = await res.text()
  if (!text) return `Request failed (${res.status})`
  try {
    const data = JSON.parse(text) as { detail?: string; message?: string }
    return data.detail || data.message || text
  } catch {
    return text
  }
}

export const apiJson = async <T>(path: string, init: RequestInit = {}) => {
  const res = await apiFetch(path, init)
  if (!res.ok) {
    throw new Error(await parseError(res))
  }
  const text = await res.text()
  return (text ? JSON.parse(text) : null) as T
}

export const apiJsonRoot = async <T>(path: string, init: RequestInit = {}) => {
  const res = await apiFetchRoot(path, init)
  if (!res.ok) {
    throw new Error(await parseError(res))
  }
  const text = await res.text()
  return (text ? JSON.parse(text) : null) as T
}

export const apiBlob = async (path: string, init: RequestInit = {}) => {
  const res = await apiFetch(path, init)
  if (!res.ok) {
    throw new Error(await parseError(res))
  }
  return res.blob()
}
