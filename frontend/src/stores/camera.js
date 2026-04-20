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
      cameras.value = result.items || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function createCamera(payload) {
    const camera = await api.post('/api/cameras', payload)
    cameras.value.unshift(camera)
    return camera
  }

  async function updateCamera(id, payload) {
    const updated = await api.put(`/api/cameras/${id}`, payload)
    const idx = cameras.value.findIndex(c => c.id === id)
    if (idx !== -1) cameras.value[idx] = updated
    return updated
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

  return {
    cameras, loading, error, streamStatus, selectedId,
    activeCameras, selectedCamera, totalCameras,
    fetchCameras, createCamera, updateCamera, deleteCamera,
    testConnection, fetchStreamStatus, selectCamera,
  }
})
