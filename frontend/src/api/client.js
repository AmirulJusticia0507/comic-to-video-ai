import { useAuthStore } from '../stores/auth'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export async function api(path, { method = 'GET', body, headers = {} } = {}) {
  const auth = useAuthStore()
  const isFormData = body instanceof FormData
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      ...(body !== undefined && !isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
      ...headers,
    },
    body: body !== undefined ? (isFormData ? body : JSON.stringify(body)) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message = typeof data.detail === 'string' ? data.detail : `request failed (${res.status})`
    const error = new Error(message)
    error.status = res.status
    throw error
  }
  return data
}
