/**
 * stores/vehicle.js
 * Pinia store — vehicle database.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/lib/api'

export const useVehicleStore = defineStore('vehicle', () => {
  // ─── State ─────────────────────────────────────────────────────────────────
  const vehicles    = ref([])
  const total       = ref(0)
  const page        = ref(1)
  const limit       = ref(20)
  const loading     = ref(false)
  const error       = ref(null)
  const search      = ref('')
  const statusFilter = ref('')

  // ─── Getters ───────────────────────────────────────────────────────────────
  const watchlistCount = computed(() =>
    vehicles.value.filter(v => v.status === 'watchlist').length
  )
  const totalPages = computed(() => Math.ceil(total.value / limit.value))

  // ─── Actions ───────────────────────────────────────────────────────────────
  async function fetchVehicles(overridePage = null) {
    loading.value = true
    error.value   = null
    try {
      const params = { page: overridePage ?? page.value, limit: limit.value }
      if (search.value)       params.search = search.value
      if (statusFilter.value) params.status = statusFilter.value

      const result = await api.get('/api/vehicles', { params })
      vehicles.value = result.items || []
      total.value    = result.total || 0
      page.value     = result.page  || 1
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function lookupPlate(plate) {
    return await api.get(`/api/vehicles/lookup/${encodeURIComponent(plate)}`)
  }

  async function createVehicle(payload) {
    const v = await api.post('/api/vehicles', payload)
    vehicles.value.unshift(v)
    total.value++
    return v
  }

  async function updateVehicle(id, payload) {
    const updated = await api.put(`/api/vehicles/${id}`, payload)
    const idx = vehicles.value.findIndex(v => v.id === id)
    if (idx !== -1) vehicles.value[idx] = updated
    return updated
  }

  async function deleteVehicle(id) {
    await api.delete(`/api/vehicles/${id}`)
    vehicles.value = vehicles.value.filter(v => v.id !== id)
    total.value--
  }

  async function flagVehicle(id, status = 'watchlist', notes = '') {
    const params = { status }
    if (notes) params.notes = notes
    const updated = await api.post(`/api/vehicles/${id}/flag`, null, { params })
    const idx = vehicles.value.findIndex(v => v.id === id)
    if (idx !== -1) vehicles.value[idx] = updated
    return updated
  }

  function setPage(p) {
    page.value = p
    fetchVehicles(p)
  }

  return {
    vehicles, total, page, limit, loading, error, search, statusFilter,
    watchlistCount, totalPages,
    fetchVehicles, lookupPlate, createVehicle, updateVehicle,
    deleteVehicle, flagVehicle, setPage,
  }
})
