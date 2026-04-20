/**
 * stores/stats.js
 * Pinia store — dashboard statistics with auto-refresh.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/lib/api'

export const useStatsStore = defineStore('stats', () => {
  // ─── State ─────────────────────────────────────────────────────────────────
  const summary       = ref(null)
  const chartData     = ref([])
  const regionData    = ref([])
  const cameraData    = ref([])
  const alertsData    = ref(null)
  const loading       = ref(false)
  const error         = ref(null)
  let   _refreshTimer = null

  // ─── Actions ───────────────────────────────────────────────────────────────
  async function fetchSummary(days = 1) {
    try {
      summary.value = await api.get('/api/stats', { params: { days } })
    } catch (e) {
      error.value = e.message
    }
  }

  async function fetchChart(days = 7) {
    try {
      chartData.value = await api.get('/api/stats/chart', { params: { days } })
    } catch (e) {
      console.warn('Chart data fetch failed', e.message)
    }
  }

  async function fetchRegion(days = 7) {
    try {
      regionData.value = await api.get('/api/stats/by-region', { params: { days, top_n: 10 } })
    } catch (e) {
      console.warn('Region data fetch failed', e.message)
    }
  }

  async function fetchCameraStats(days = 1) {
    try {
      cameraData.value = await api.get('/api/stats/by-camera', { params: { days } })
    } catch (e) {
      console.warn('Camera stats fetch failed', e.message)
    }
  }

  async function fetchAlerts(hours = 24) {
    try {
      alertsData.value = await api.get('/api/stats/alerts', { params: { hours } })
    } catch (e) {
      console.warn('Alerts fetch failed', e.message)
    }
  }

  async function fetchAll() {
    loading.value = true
    error.value   = null
    await Promise.allSettled([
      fetchSummary(1),
      fetchChart(7),
      fetchRegion(7),
      fetchCameraStats(1),
      fetchAlerts(24),
    ])
    loading.value = false
  }

  /** Start polling every N seconds. Call stopRefresh() on unmount. */
  function startAutoRefresh(intervalMs = 30_000) {
    fetchAll()
    _refreshTimer = setInterval(fetchAll, intervalMs)
  }

  function stopAutoRefresh() {
    if (_refreshTimer) {
      clearInterval(_refreshTimer)
      _refreshTimer = null
    }
  }

  return {
    summary, chartData, regionData, cameraData, alertsData,
    loading, error,
    fetchSummary, fetchChart, fetchRegion, fetchCameraStats,
    fetchAlerts, fetchAll, startAutoRefresh, stopAutoRefresh,
  }
})
