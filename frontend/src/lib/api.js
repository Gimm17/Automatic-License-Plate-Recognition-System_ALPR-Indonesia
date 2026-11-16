/**
 * src/lib/api.js
 * Axios instance pre-configured for the FastAPI backend.
 * All responses are unwrapped to their `data` payload automatically.
 */

import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
export const API_KEY = import.meta.env.VITE_API_KEY || ''

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  config.headers = config.headers || {}
  if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  if (API_KEY) {
    config.headers['X-API-Key'] = API_KEY
  }
  return config
})

// ─── Response interceptor — unwrap standard envelope ──────────────────────────
api.interceptors.response.use(
  (response) => {
    // Our API always returns { success, data, message }
    if (response.data && typeof response.data.success !== 'undefined') {
      if (!response.data.success) {
        return Promise.reject(new Error(response.data.message || 'API error'))
      }
      return response.data.data
    }
    return response.data
  },
  (error) => {
    const responseData = error.response?.data
    let msg = error.message || 'Network error'

    if (responseData) {
      // FastAPI 422 validation error: detail is an array of {loc, msg, type}
      if (Array.isArray(responseData.detail)) {
        msg = responseData.detail
          .map(d => {
            const field = d.loc?.filter(l => l !== 'body').join('.') || ''
            return field ? `${field}: ${d.msg}` : d.msg
          })
          .join(', ')
      } else if (typeof responseData.detail === 'string') {
        msg = responseData.detail
      } else if (typeof responseData.message === 'string') {
        msg = responseData.message
      }
    }

    const err = new Error(msg)
    err.status = error.response?.status
    err.detail = responseData?.detail
    return Promise.reject(err)
  }
)

export function getApiKey() {
  return API_KEY
}

export function toApiAssetUrl(path) {
  if (!path) return null
  if (/^https?:\/\//i.test(path) || path.startsWith('data:')) return path
  const base = API_BASE_URL.replace(/\/$/, '')
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${base}${normalized}`
}

export default api
