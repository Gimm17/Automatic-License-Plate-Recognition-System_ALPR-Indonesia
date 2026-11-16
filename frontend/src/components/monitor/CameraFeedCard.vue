<template>
  <!--
    CameraFeedCard — individual camera tile for the 2×2 / 1×1 grid.
    
    Two display modes:
    ① HLS/HTTPS stream → <video> tag (native browser playback, no backend needed)
    ② RTSP stream      → WebSocket base64 frames from backend
    ③ Offline          → Signal Lost state
  -->
  <div
    class="feed-card"
    :class="{
      'feed-card--selected': selected,
      'feed-card--offline':  !camera.online,
    }"
    @click="$emit('select', camera)"
  >
    <!-- ── OFFLINE state ────────────────────────────────────────── -->
    <div v-if="!camera.online" class="feed-card__offline">
      <span class="material-symbols-outlined offline-icon">videocam_off</span>
      <span class="offline-label">Signal Lost</span>
    </div>

    <!-- ── ONLINE: auto-detect HLS vs WebSocket ──────────────────── -->
    <template v-else>

      <!-- MODE 1: HLS/HTTPS via hls.js ────────────────────────── -->
      <template v-if="isHlsStream">
        <!-- Always render <video> so ref="videoEl" is available for hls.js -->
        <video
          ref="videoEl"
          class="feed-card__video"
          muted
          playsinline
          @loadeddata="videoLoaded = true"
        />

        <!-- Loading overlay (shown until first frame) -->
        <div v-if="!videoLoaded && !videoError" class="feed-card__overlay-state">
          <span class="material-symbols-outlined" style="font-size:36px;opacity:.2">
            videocam
          </span>
          <span class="placeholder-label">Memuat stream…</span>
        </div>

        <!-- Error overlay -->
        <div v-if="videoError" class="feed-card__overlay-state feed-card__overlay-state--error">
          <span class="material-symbols-outlined" style="font-size:28px;opacity:.5">
            signal_disconnected
          </span>
          <span class="placeholder-label">Stream tidak dapat dimuat</span>
        </div>
      </template>

      <!-- MODE 2: WebSocket base64 frames (RTSP via backend) ─────── -->
      <template v-else>
        <!-- Base64 frame from WebSocket stream -->
        <img
          v-if="frameB64"
          :src="`data:image/jpeg;base64,${frameB64}`"
          class="feed-card__img"
          alt="Live camera feed"
        />
        <!-- Placeholder when connected but no frame yet -->
        <div v-else class="feed-card__placeholder">
          <span class="material-symbols-outlined" style="font-size:36px;opacity:.2">
            videocam
          </span>
          <span class="placeholder-label">{{ wsError || 'Menghubungkan…' }}</span>
        </div>
      </template>

      <!-- Detection bounding-box overlays (WebSocket mode only) ─────── -->
      <svg
        v-if="overlayBoxes.length"
        class="feed-card__svg-overlay"
        viewBox="0 0 1 1"
        preserveAspectRatio="none"
      >
        <g v-for="(box, i) in overlayBoxes" :key="i">
          <rect
            :x="box.x"
            :y="box.y"
            :width="box.w"
            :height="box.h"
            fill="rgba(255,183,134,0.08)"
            stroke="#ffb786"
            stroke-width="0.003"
          />
        </g>
      </svg>

      <!-- Hover overlay -->
      <div class="feed-card__hover-overlay">
        <div class="hover-crosshair"></div>
      </div>
    </template>

    <!-- ── Top-left: camera ID + location badge ─────────────────── -->
    <div class="feed-card__badges">
      <span class="feed-badge feed-badge--cam">
        <span
          class="feed-badge__dot"
          :class="camera.online ? 'dot--live' : 'dot--off'"
        ></span>
        {{ camera.label }}
      </span>
      <span v-if="camera.location" class="feed-badge feed-badge--location">{{ camera.location }}</span>
      <!-- HLS badge -->
      <span v-if="isHlsStream && camera.online" class="feed-badge feed-badge--hls">HLS</span>
    </div>

    <!-- ── Bottom: FPS + last plate (when online + streaming) ─────── -->
    <div v-if="camera.online && (lastPlate || fps)" class="feed-card__footer">
      <span v-if="lastPlate" class="feed-footer-chip glass">
        <span class="material-symbols-outlined" style="font-size:11px">tag</span>
        {{ lastPlate }}
      </span>
      <span v-if="fps" class="feed-footer-chip glass fps-chip">
        {{ fps }} fps
      </span>
    </div>

    <!-- ── Selected ring indicator ───────────────────────────────── -->
    <div v-if="selected" class="feed-card__selected-ring"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import Hls from 'hls.js'
import { useStreamStore } from '@/stores/stream'
import api from '@/lib/api'

const props = defineProps({
  camera:   { type: Object, required: true }, // { id, label, location, online, rtsp_url }
  selected: { type: Boolean, default: false },
})
defineEmits(['select'])

const streamStore = useStreamStore()

// ─── Stream URL resolution ────────────────────────────────────────────────────
const streamUrl   = ref(null)
const videoEl     = ref(null)
const videoLoaded = ref(false)
const videoError  = ref(false)

// Detect if the stream URL is HLS/HTTPS (browser-playable) vs RTSP (needs WebSocket)
const isHlsStream = computed(() => {
  const url = streamUrl.value || props.camera.rtsp_url || ''
  if (!url) return false
  // RTSP = needs WebSocket backend
  if (url.startsWith('rtsp://') || url.startsWith('rtsps://')) return false
  // Everything else: HLS, local proxy, HTTP/HTTPS
  return true
})

// Fetch/resolve the actual stream URL
async function resolveStreamUrl() {
  if (props.camera.rtsp_url) {
    streamUrl.value = props.camera.rtsp_url
    return
  }
  try {
    const data = await api.get(`/api/cameras/${props.camera.id}`)
    streamUrl.value = data?.data?.rtsp_url || data?.rtsp_url || null
  } catch {
    streamUrl.value = null
  }
}

// ─── HLS.js integration ───────────────────────────────────────────────────────
let hlsInstance = null

function destroyHls() {
  if (hlsInstance) {
    hlsInstance.destroy()
    hlsInstance = null
  }
}

function initHls() {
  destroyHls()
  const url = streamUrl.value
  if (!url || !videoEl.value) return

  videoLoaded.value = false
  videoError.value  = false

  if (Hls.isSupported()) {
    hlsInstance = new Hls({
      enableWorker: true,
      lowLatencyMode: true,
      backBufferLength: 10,
      // Retry settings for live streams that may be temporarily offline
      manifestLoadingMaxRetry: 8,
      manifestLoadingRetryDelay: 2000,
      levelLoadingMaxRetry: 8,
      levelLoadingRetryDelay: 2000,
      fragLoadingMaxRetry: 6,
    })
    hlsInstance.loadSource(url)
    hlsInstance.attachMedia(videoEl.value)

    hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
      videoEl.value?.play().catch(() => {})
      videoLoaded.value = true
      videoError.value  = false
    })

    hlsInstance.on(Hls.Events.ERROR, (event, data) => {
      console.warn('[HLS] error', data.type, data.details)
      if (data.fatal) {
        videoError.value = true
        if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          // Network error: try to recover automatically
          hlsInstance?.startLoad()
        } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
          hlsInstance?.recoverMediaError()
        } else {
          destroyHls()
        }
      }
    })
  } else if (videoEl.value.canPlayType('application/vnd.apple.mpegurl')) {
    // Safari native HLS
    videoEl.value.src = url
    videoEl.value.addEventListener('loadeddata', () => { videoLoaded.value = true }, { once: true })
    videoEl.value.addEventListener('error', () => { videoError.value = true }, { once: true })
    videoEl.value.play().catch(() => {})
  } else {
    videoError.value = true
  }
}

function onVideoError() {
  videoError.value = true
  videoLoaded.value = false
}

// ─── WebSocket stream state (RTSP mode) ──────────────────────────────────────
const streamState = computed(() => streamStore.getStream(props.camera.id))
const frameB64    = computed(() => streamState.value?.frameB64 ?? null)
const detections  = computed(() => streamState.value?.detections ?? [])
const fps         = computed(() => streamState.value?.fps ?? 0)
const wsError     = computed(() => streamState.value?.error ?? null)
const overlayBoxes = computed(() =>
  detections.value
    .filter(det => Array.isArray(det.bbox_norm) && det.bbox_norm.length === 4)
    .map(det => {
      const [x1, y1, x2, y2] = det.bbox_norm
      return {
        x: x1,
        y: y1,
        w: Math.max(0, x2 - x1),
        h: Math.max(0, y2 - y1),
      }
    })
)

const lastPlate = computed(() => {
  const dets = detections.value
  if (!dets.length) return null
  return dets[dets.length - 1]?.plate_text ?? null
})

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  if (props.camera.online) {
    await resolveStreamUrl()
    if (isHlsStream.value) {
      // Wait for DOM to render <video> element
      setTimeout(initHls, 100)
      // Also connect WebSocket for live detection (YOLO/OCR on backend)
      // Backend reads the HLS URL via OpenCV and runs detection pipeline
      streamStore.connect(props.camera.id)
    }
  }
})

onUnmounted(() => {
  destroyHls()
  // Disconnect WS detection for HLS streams too
  if (isHlsStream.value) {
    streamStore.disconnect(props.camera.id)
  }
})

// Re-init when camera changes or comes online
watch(streamUrl, () => {
  if (isHlsStream.value && props.camera.online) {
    setTimeout(initHls, 100)
  }
})

watch(() => props.camera.online, async (isOnline) => {
  if (isOnline) {
    videoLoaded.value = false
    videoError.value  = false
    await resolveStreamUrl()
    if (isHlsStream.value) {
      setTimeout(initHls, 100)
      streamStore.connect(props.camera.id)
    }
  } else {
    destroyHls()
    if (isHlsStream.value) {
      streamStore.disconnect(props.camera.id)
    }
  }
})
</script>

<style scoped>
/* ─── Card Shell ─────────────────────────────────────────────────────────────── */
.feed-card {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--surface-container-low);
  box-shadow: 0 20px 40px rgba(15, 31, 41, 0.025);
  cursor: pointer;
  transition: box-shadow 0.2s ease, transform 0.15s ease;
  aspect-ratio: 16/9;
}

.feed-card:hover {
  box-shadow: 0 12px 32px rgba(15, 31, 41, 0.08);
}

.feed-card--selected {
  box-shadow: 0 0 0 2px var(--primary), 0 12px 32px rgba(15, 31, 41, 0.12);
}

/* ─── Offline state ──────────────────────────────────────────────────────────── */
.feed-card__offline {
  position: absolute;
  inset: 0;
  background-color: var(--surface-container-highest);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--on-surface-variant);
}

.offline-icon {
  font-size: 36px;
  opacity: 0.4;
}

.offline-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.6;
}

/* ─── HLS Video player ───────────────────────────────────────────────────────── */
.feed-card__video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: #000;
}

/* ─── Online — image frame (WebSocket mode) ──────────────────────────────────── */
.feed-card__img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ─── Placeholder ────────────────────────────────────────────────────────────── */
.feed-card__placeholder {
  position: absolute;
  inset: 0;
  background-color: #0b151c;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.feed-card__placeholder--error { background-color: #150a0a; }

.placeholder-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  font-weight: 600;
  letter-spacing: 0.04em;
}

.placeholder-url {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.15);
  font-family: monospace;
  max-width: 90%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ─── Overlay state (loading / error on top of video element) ───────────────── */
.feed-card__overlay-state {
  position: absolute;
  inset: 0;
  z-index: 5;
  background-color: #0b151c;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.3);
  pointer-events: none;
}

.feed-card__overlay-state--error { background-color: #150a0a; }

/* ─── SVG bbox overlay ───────────────────────────────────────────────────────── */
.feed-card__svg-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

/* ─── Hover crosshair overlay ────────────────────────────────────────────────── */
.feed-card__hover-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(15, 31, 41, 0.06);
  opacity: 0;
  transition: opacity 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.feed-card:hover .feed-card__hover-overlay {
  opacity: 1;
}

.hover-crosshair {
  width: 100px;
  height: 60px;
  border: 2px solid var(--tertiary-fixed-dim);
  border-radius: 2px;
}

/* ─── Top badges ─────────────────────────────────────────────────────────────── */
.feed-card__badges {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  gap: 6px;
  z-index: 10;
}

.feed-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(195, 199, 203, 0.25);
  color: var(--primary);
}

.feed-badge--location {
  color: var(--on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.feed-badge--hls {
  background: rgba(22, 163, 74, 0.8);
  color: #fff;
  border-color: rgba(22, 163, 74, 0.4);
}

.feed-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot--live {
  background-color: #ffb786;
  animation: blink 1.8s ease-in-out infinite;
}

.dot--off { background-color: var(--outline); }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

/* ─── Bottom footer ──────────────────────────────────────────────────────────── */
.feed-card__footer {
  position: absolute;
  bottom: 10px;
  left: 10px;
  display: flex;
  gap: 6px;
  z-index: 10;
}

.feed-footer-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 700;
  color: var(--primary);
  font-family: 'Courier New', monospace;
}

.fps-chip {
  color: var(--on-surface-variant);
}

/* ─── Selected ring ──────────────────────────────────────────────────────────── */
.feed-card__selected-ring {
  position: absolute;
  inset: 0;
  border: 2px solid var(--primary);
  border-radius: 8px;
  pointer-events: none;
}
</style>
