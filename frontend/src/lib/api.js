/**
 * src/lib/api.js
 * Axios instance pre-configured for the FastAPI backend.
 * All responses are unwrapped to their `data` payload automatically.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
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
    const msg =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      'Network error'
    return Promise.reject(new Error(msg))
  }
)

export default api
