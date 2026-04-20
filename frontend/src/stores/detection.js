/**
 * stores/detection.js
 * Pinia store — detection history and upload processing.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/lib/api'

export const useDetectionStore = defineStore('detection', () => {
  // ─── State ─────────────────────────────────────────────────────────────────
  const detections   = ref([])
  const total        = ref(0)
  const page         = ref(1)
  const limit        = ref(20)
  const loading      = ref(false)
  const error        = ref(null)
  const filters      = ref({
    search:    '',
    status:    '',
    camera_id: null,
    date_from: '',
    date_to:   '',
  })

  // Latest upload result
  const uploadResult = ref(null)
  const uploading    = ref(false)

  // ─── Getters ───────────────────────────────────────────────────────────────
  const totalPages = computed(() => Math.ceil(total.value / limit.value))
  const hasResults = computed(() => detections.value.length > 0)

  // ─── Actions ───────────────────────────────────────────────────────────────
  async function fetchDetections(overridePage = null) {
    loading.value = true
    error.value   = null
    try {
      const params = {
        page:  overridePage ?? page.value,
        limit: limit.value,
        ...Object.fromEntries(
          Object.entries(filters.value).filter(([, v]) => v !== '' && v !== null)
        ),
      }
      const result = await api.get('/api/detections', { params })
      detections.value = result.items || []
      total.value      = result.total || 0
      page.value       = result.page  || 1
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function uploadFile(file, cameraId = null) {
    uploading.value  = true
    uploadResult.value = null
    error.value      = null
    try {
      const form = new FormData()
      form.append('file', file)
      if (cameraId) form.append('camera_id', cameraId)

      const result = await api.post('/api/detect', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      uploadResult.value = result
      return result
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      uploading.value = false
    }
  }

  function setFilter(key, value) {
    filters.value[key] = value
    page.value = 1
  }

  function resetFilters() {
    filters.value = { search: '', status: '', camera_id: null, date_from: '', date_to: '' }
    page.value = 1
  }

  function setPage(p) {
    page.value = p
    fetchDetections(p)
  }

  return {
    detections, total, page, limit, loading, error, filters,
    uploadResult, uploading,
    totalPages, hasResults,
    fetchDetections, uploadFile, setFilter, resetFilters, setPage,
  }
})
