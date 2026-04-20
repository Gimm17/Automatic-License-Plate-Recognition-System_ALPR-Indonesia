/**
 * stores/stream.js
 * Pinia store — WebSocket live stream management.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useStreamStore = defineStore('stream', () => {
  // ─── State ─────────────────────────────────────────────────────────────────
  /** Map of camera_id → { ws, frameB64, detections, fps, frameCount, connected, error } */
  const streams  = ref({})

  // ─── Getters ───────────────────────────────────────────────────────────────
  const activeCount = computed(() =>
    Object.values(streams.value).filter(s => s.connected).length
  )

  function getStream(cameraId) {
    return streams.value[cameraId] || null
  }

  // ─── Actions ───────────────────────────────────────────────────────────────
  function connect(cameraId, sourceOverride = null) {
    // Don't double-connect
    if (streams.value[cameraId]?.connected) return

    const wsBase = import.meta.env.VITE_WS_BASE_URL ||
      `ws://${window.location.host}`
    const url = sourceOverride
      ? `${wsBase}/ws/stream/${cameraId}?source_override=${encodeURIComponent(sourceOverride)}`
      : `${wsBase}/ws/stream/${cameraId}`

    const ws = new WebSocket(url)

    streams.value[cameraId] = {
      ws,
      frameB64:   null,
      detections: [],
      fps:        0,
      frameCount: 0,
      connected:  false,
      error:      null,
    }

    ws.onopen = () => {
      if (streams.value[cameraId]) {
        streams.value[cameraId].connected = true
        streams.value[cameraId].error = null
      }
    }

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (!streams.value[cameraId]) return

      if (msg.type === 'frame') {
        streams.value[cameraId].frameB64   = msg.frame
        streams.value[cameraId].detections = msg.detections || []
        streams.value[cameraId].fps        = msg.fps_display || 0
        streams.value[cameraId].frameCount = msg.frame_count || 0
      } else if (msg.type === 'error') {
        streams.value[cameraId].error = msg.message
      }
    }

    ws.onerror = () => {
      if (streams.value[cameraId]) {
        streams.value[cameraId].error = 'WebSocket connection error'
        streams.value[cameraId].connected = false
      }
    }

    ws.onclose = () => {
      if (streams.value[cameraId]) {
        streams.value[cameraId].connected = false
      }
    }
  }

  function disconnect(cameraId) {
    const stream = streams.value[cameraId]
    if (stream?.ws) {
      stream.ws.close()
    }
    delete streams.value[cameraId]
  }

  function disconnectAll() {
    Object.keys(streams.value).forEach(id => disconnect(Number(id)))
  }

  return {
    streams, activeCount,
    getStream, connect, disconnect, disconnectAll,
  }
})
