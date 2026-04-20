<template>
  <!--
    CameraFeedCard — individual camera tile for the 2×2 / 1×1 grid.
    State: online (shows frame/placeholder), offline (signal lost).
    Supports WebSocket-driven base64 frames.
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

    <!-- ── ONLINE: live WebSocket frame ────────────────────────── -->
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
        <span class="placeholder-label">Menghubungkan…</span>
      </div>

      <!-- Detection bounding-box overlays -->
      <svg
        v-if="detections.length"
        class="feed-card__svg-overlay"
        viewBox="0 0 1 1"
        preserveAspectRatio="none"
      >
        <g v-for="(det, i) in detections" :key="i">
          <rect
            :x="det.bbox[0]"
            :y="det.bbox[1]"
            :width="det.bbox[2] - det.bbox[0]"
            :height="det.bbox[3] - det.bbox[1]"
            fill="rgba(255,183,134,0.08)"
            stroke="#ffb786"
            stroke-width="0.003"
          />
        </g>
      </svg>

      <!-- Hover detection highlight overlay -->
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
      <span class="feed-badge feed-badge--location">{{ camera.location }}</span>
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
import { computed } from 'vue'
import { useStreamStore } from '@/stores/stream'

const props = defineProps({
  camera:   { type: Object, required: true }, // { id, label, location, online }
  selected: { type: Boolean, default: false },
})
defineEmits(['select'])

const streamStore = useStreamStore()

// Pull live data from store (reactive)
const streamState = computed(() => streamStore.getStream(props.camera.id))
const frameB64    = computed(() => streamState.value?.frameB64 ?? null)
const detections  = computed(() => streamState.value?.detections ?? [])
const fps         = computed(() => streamState.value?.fps ?? 0)

const lastPlate = computed(() => {
  const dets = detections.value
  if (!dets.length) return null
  return dets[dets.length - 1]?.plate_text ?? null
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

/* ─── Online — image frame ───────────────────────────────────────────────────── */
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

.placeholder-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  font-weight: 600;
  letter-spacing: 0.04em;
}

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
