/**
 * stores/camera.js
 * Pinia store — camera list and stream status.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/lib/api'

export const useCameraStore = defineStore('camera', () => {
  // ─── State ─────────────────────────────────────────────────────────────────
  const cameras       = ref([])
  const loading       = ref(false)
  const error         = ref(null)
  const streamStatus  = ref({}) // camera_id → { streaming: bool }
  const selectedId    = ref(null)

  // ─── Getters ───────────────────────────────────────────────────────────────
  const activeCameras   = computed(() => cameras.value.filter(c => c.is_active))
  const selectedCamera  = computed(() => cameras.value.find(c => c.id === selectedId.value))
  const totalCameras    = computed(() => cameras.value.length)

  // ─── Actions ───────────────────────────────────────────────────────────────
  async function fetchCameras() {
    loading.value = true
    error.value   = null
    try {
      const result = await api.get('/api/cameras', { params: { limit: 100 } })
      cameras.value = (result.items || []).map(normalizeCamera)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function createCamera(payload) {
    const camera = await api.post('/api/cameras', payload)
    const norm = normalizeCamera(camera)
    cameras.value.unshift(norm)
    return norm
  }

  async function updateCamera(id, payload) {
    const updated = await api.put(`/api/cameras/${id}`, payload)
    const norm = normalizeCamera(updated)
    const idx = cameras.value.findIndex(c => c.id === id)
    if (idx !== -1) cameras.value[idx] = norm
    return norm
  }

  async function deleteCamera(id) {
    await api.delete(`/api/cameras/${id}`)
    cameras.value = cameras.value.filter(c => c.id !== id)
  }

  async function testConnection(id) {
    return await api.post(`/api/cameras/${id}/test`)
  }

  async function fetchStreamStatus() {
    try {
      const result = await api.get('/api/stream/status')
      const map = {}
      ;(result.cameras || []).forEach(c => { map[c.camera_id] = c })
      streamStatus.value = map
    } catch (e) {
      // Silently fail
    }
  }

  function selectCamera(id) {
    selectedId.value = id
  }

  // ─── Helpers ───────────────────────────────────────────────────────────────
  /**
   * Add a normalized .status field so all views can use cam.status === 'online'.
   * Backend only has is_active (bool) — we derive status from it.
   * Also rewrite Kemenhub HLS URLs through local Vite proxy to bypass CORS.
   */
  function normalizeCamera(cam) {
    let rtsp_url = cam.rtsp_url || null

    // Rewrite Kemenhub stream URLs through local proxy (dev only)
    if (rtsp_url && rtsp_url.includes('mitradarat-vidstream.dephub.go.id')) {
      // Convert: https://mitradarat-vidstream.dephub.go.id/stream/XYZ/index.m3u8
      // To:      /stream-proxy/stream/XYZ/index.m3u8
      rtsp_url = rtsp_url.replace(
        'https://mitradarat-vidstream.dephub.go.id',
        '/stream-proxy'
      )
    }

    return {
      ...cam,
      rtsp_url,
      status: cam.is_active ? 'online' : 'offline',
    }
  }

  return {
    cameras, loading, error, streamStatus, selectedId,
    activeCameras, selectedCamera, totalCameras,
    fetchCameras, createCamera, updateCamera, deleteCamera,
    testConnection, fetchStreamStatus, selectCamera,
  }
})
