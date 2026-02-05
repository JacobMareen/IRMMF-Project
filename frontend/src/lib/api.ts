import { client, API_BASE, API_ROOT } from '../api/client'

export { API_BASE, API_ROOT }

export const apiFetch = (path: string, init: RequestInit = {}) => {
  return client.fetch(path, init)
}

export const apiFetchRoot = (path: string, init: RequestInit = {}) => {
  return client.fetch(path, init, true)
}

export const readApiError = async (res: Response) => {
  return (await client.readError(res)).message
}

export const apiJson = async <T>(path: string, init: RequestInit = {}) => {
  const res = await apiFetch(path, init)
  if (!res.ok) {
    throw new Error(await readApiError(res))
  }
  const text = await res.text()
  return (text ? JSON.parse(text) : null) as T
}

export const apiJsonRoot = async <T>(path: string, init: RequestInit = {}) => {
  const res = await apiFetchRoot(path, init)
  if (!res.ok) {
    throw new Error(await readApiError(res))
  }
  const text = await res.text()
  return (text ? JSON.parse(text) : null) as T
}

export const apiBlob = async (path: string, init: RequestInit = {}) => {
  const res = await apiFetch(path, init)
  if (!res.ok) {
    throw new Error(await readApiError(res))
  }
  return res.blob()
}
