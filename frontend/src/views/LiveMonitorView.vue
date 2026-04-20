<template>
  <MainLayout>
    <div class="monitor">

      <!-- ══════════════════════════════════════════════════════════
           LEFT — Video Grid Area
           ══════════════════════════════════════════════════════════ -->
      <div class="monitor__main">

        <!-- Page heading + grid controls -->
        <div class="monitor__heading">
          <div>
            <h2 class="monitor__title">Live Monitor</h2>
            <p class="monitor__sub">Real-time video feeds &amp; analytics.</p>
          </div>

          <div class="monitor__controls">
            <!-- Grid layout toggle -->
            <div class="grid-toggle">
              <button
                v-for="opt in gridOptions"
                :key="opt.value"
                class="grid-btn"
                :class="{ 'grid-btn--active': gridLayout === opt.value }"
                :title="opt.label"
                @click="gridLayout = opt.value"
              >
                <span class="material-symbols-outlined" style="font-size:16px">
                  {{ opt.icon }}
                </span>
                <span>{{ opt.label }}</span>
              </button>
            </div>

            <!-- Connect All / Disconnect All -->
            <button
              v-if="!allConnected"
              class="btn-connect"
              @click="connectAll"
            >
              <span class="material-symbols-outlined" style="font-size:16px">wifi</span>
              Connect All
            </button>
            <button
              v-else
              class="btn-disconnect"
              @click="disconnectAll"
            >
              <span class="material-symbols-outlined" style="font-size:16px">wifi_off</span>
              Disconnect
            </button>
          </div>
        </div>

        <!-- ── Camera Grid ─────────────────────────────────────────── -->
        <div
          class="camera-grid"
          :class="`camera-grid--${gridLayout}`"
        >
          <CameraFeedCard
            v-for="cam in cameras"
            :key="cam.id"
            :camera="cam"
            :selected="selectedCameraId === cam.id"
            @select="handleCameraSelect"
          />
        </div>

        <!-- ── Selected camera detail bar ────────────────────────────── -->
        <Transition name="slide-detail">
          <div v-if="selectedCamera" class="detail-bar">
            <div class="detail-bar__left">
              <span class="detail-bar__label">Kamera Aktif</span>
              <span class="detail-bar__name">{{ selectedCamera.label }} — {{ selectedCamera.location }}</span>
            </div>
            <div class="detail-bar__stats">
              <div class="detail-stat">
                <span class="detail-stat__val">{{ streamState?.fps ?? 0 }}</span>
                <span class="detail-stat__label">fps</span>
              </div>
              <div class="detail-stat">
                <span class="detail-stat__val">{{ streamState?.frameCount?.toLocaleString('id-ID') ?? 0 }}</span>
                <span class="detail-stat__label">frames</span>
              </div>
              <div class="detail-stat">
                <span
                  class="detail-stat__val"
                  :class="streamState?.connected ? 'val--live' : 'val--off'"
                >
                  {{ streamState?.connected ? 'LIVE' : 'IDLE' }}
                </span>
                <span class="detail-stat__label">status</span>
              </div>
            </div>
            <button class="detail-bar__fullscreen" @click="toggleFullscreen">
              <span class="material-symbols-outlined">fullscreen</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- ══════════════════════════════════════════════════════════
           RIGHT — Sidebar: Stats + Realtime Log
           ══════════════════════════════════════════════════════════ -->
      <aside class="monitor__sidebar">

        <!-- Mini stat card -->
        <div class="mini-stat-card">
          <div class="mini-stat-card__header">
            <span class="label-xs">Total Hari Ini</span>
            <span class="mini-stat-card__streams">
              <span class="live-pulse" style="width:6px;height:6px"></span>
              {{ activeStreamCount }} live
            </span>
          </div>
          <div class="mini-stat-card__value">
            {{ stats.todayTotal.toLocaleString('id-ID') }}
          </div>
          <div class="mini-stat-card__sub">
            <span class="mini-stat-card__label">Valid Reads:</span>
            <span class="mini-stat-card__pct">{{ stats.ocrAccuracy }}%</span>
          </div>
        </div>

        <!-- Realtime log — fills remaining height -->
        <RealtimeLog :entries="realtimeEntries" class="monitor__rtlog" />

      </aside>

    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'
import CameraFeedCard from '@/components/monitor/CameraFeedCard.vue'
import RealtimeLog from '@/components/monitor/RealtimeLog.vue'
import { useStreamStore } from '@/stores/stream'
import { useCameraStore } from '@/stores/camera'

const streamStore = useStreamStore()
const cameraStore = useCameraStore()

// ─── Grid layout ─────────────────────────────────────────────────────────────
const gridLayout = ref('2x2')
const gridOptions = [
  { value: '1x1', label: '1×1', icon: 'crop_square' },
  { value: '2x2', label: '2×2', icon: 'grid_view' },
  { value: '1+3', label: '1+3', icon: 'view_quilt' },
]

// ─── Cameras (dummy data until backend connected) ─────────────────────────────
const cameras = ref([
  { id: 1, label: 'CAM-01', location: 'Jakarta Utara',   online: true },
  { id: 2, label: 'CAM-02', location: 'Jakarta Selatan', online: true },
  { id: 3, label: 'CAM-03', location: 'Tol Dalam Kota',  online: true },
  { id: 4, label: 'CAM-04', location: 'Bekasi Barat',    online: false },
])

// ─── Selection ────────────────────────────────────────────────────────────────
const selectedCameraId = ref(1)
const selectedCamera = computed(() =>
  cameras.value.find(c => c.id === selectedCameraId.value) ?? null
)

const streamState = computed(() =>
  streamStore.getStream(selectedCameraId.value)
)

function handleCameraSelect(cam) {
  selectedCameraId.value = cam.id
}

// ─── Stream connect/disconnect ────────────────────────────────────────────────
const allConnected = computed(() =>
  cameras.value.filter(c => c.online).every(c => streamStore.getStream(c.id)?.connected)
)
const activeStreamCount = computed(() => streamStore.activeCount)

function connectAll() {
  cameras.value.filter(c => c.online).forEach(c => {
    streamStore.connect(c.id)
  })
}

function disconnectAll() {
  streamStore.disconnectAll()
}

// ─── Stats summary (dummy) ────────────────────────────────────────────────────
const stats = ref({ todayTotal: 12458, ocrAccuracy: 98.2 })

// ─── Realtime log — simulated new entries every ~2s ──────────────────────────
const realtimeEntries = ref([
  { id: 1, plate_text: 'B 1234 XYZ', status: 'valid',     camera_id: 1, camera_label: 'CAM-01', confidence: 0.99, detected_at: new Date(Date.now() - 5000).toISOString(),   crop_url: null },
  { id: 2, plate_text: 'D 4455 AA',  status: 'watchlist', camera_id: 2, camera_label: 'CAM-02', confidence: 0.97, detected_at: new Date(Date.now() - 40000).toISOString(),  crop_url: null },
  { id: 3, plate_text: 'F 8899 GHI', status: 'valid',     camera_id: 3, camera_label: 'CAM-03', confidence: 0.95, detected_at: new Date(Date.now() - 120000).toISOString(), crop_url: null },
  { id: 4, plate_text: null,          status: 'ocr_failed',camera_id: 1, camera_label: 'CAM-01', confidence: null, detected_at: new Date(Date.now() - 300000).toISOString(), crop_url: null },
])

const dummyPlates = ['B 1234 XYZ', 'L 5678 AB', 'AB 999 CD', 'F 0011 GG', 'N 4321 ZZ']
let logTimer = null
let nextId = 10

function addDummyEntry() {
  const isAlert = Math.random() < 0.12
  const isFail  = Math.random() < 0.06
  const camIdx  = Math.floor(Math.random() * 3)
  const cam     = cameras.value[camIdx]
  const entry = {
    id:           nextId++,
    plate_text:   isFail ? null : dummyPlates[Math.floor(Math.random() * dummyPlates.length)],
    status:       isFail ? 'ocr_failed' : isAlert ? 'watchlist' : 'valid',
    camera_id:    cam.id,
    camera_label: cam.label,
    confidence:   isFail ? null : 0.88 + Math.random() * 0.12,
    detected_at:  new Date().toISOString(),
    crop_url:     null,
  }
  realtimeEntries.value.unshift(entry)
  // Keep max 60 entries
  if (realtimeEntries.value.length > 60) {
    realtimeEntries.value.pop()
  }
}

// ─── Fullscreen toggle ────────────────────────────────────────────────────────
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.()
  } else {
    document.exitFullscreen?.()
  }
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(() => {
  logTimer = setInterval(addDummyEntry, 2200)
})

onUnmounted(() => {
  clearInterval(logTimer)
  streamStore.disconnectAll()
})
</script>

<style scoped>
/* ─── Monitor layout: left (flex-1) + right sidebar (fixed 320px) ────────────── */
.monitor {
  display: flex;
  gap: 24px;
  height: calc(100vh - var(--topbar-height, 64px) - 64px);
  min-height: 600px;
}

/* ─── Main left column ───────────────────────────────────────────────────────── */
.monitor__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

/* ─── Heading row ────────────────────────────────────────────────────────────── */
.monitor__heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-shrink: 0;
}

.monitor__title {
  font-size: 26px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.02em;
  line-height: 1;
}

.monitor__sub {
  font-size: 13px;
  color: var(--on-surface-variant);
  margin-top: 4px;
}

/* ─── Controls bar ───────────────────────────────────────────────────────────── */
.monitor__controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Grid toggle pills */
.grid-toggle {
  display: flex;
  gap: 2px;
  background-color: var(--surface-container-highest);
  border-radius: 4px;
  padding: 3px;
}

.grid-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border: none;
  background: transparent;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 700;
  color: var(--on-surface-variant);
  cursor: pointer;
  transition: background-color 0.12s, color 0.12s;
}

.grid-btn--active {
  background-color: var(--surface-container-lowest);
  color: var(--primary);
  box-shadow: 0 1px 4px rgba(15, 31, 41, 0.06);
}

/* Connect / Disconnect buttons */
.btn-connect,
.btn-disconnect {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}

.btn-connect {
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary);
}

.btn-disconnect {
  background-color: var(--surface-container-highest);
  color: var(--on-surface-variant);
}

.btn-connect:hover,
.btn-disconnect:hover { opacity: 0.88; }
.btn-connect:active,
.btn-disconnect:active { transform: scale(0.97); }

/* ─── Camera grid ────────────────────────────────────────────────────────────── */
.camera-grid {
  flex: 1;
  display: grid;
  gap: 12px;
  min-height: 0;
}

/* 2×2 layout */
.camera-grid--2x2 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows:    1fr 1fr;
}

/* 1×1 — first camera full width */
.camera-grid--1x1 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}
.camera-grid--1x1 > :not(:first-child) { display: none; }

/* 1+3 — big left + 3 small right column */
.camera-grid--1+3 {
  grid-template-columns: 2fr 1fr;
  grid-template-rows: 1fr 1fr;
}
.camera-grid--1\+3 > :first-child {
  grid-row: 1 / 3;
}

/* ─── Detail bar ─────────────────────────────────────────────────────────────── */
.detail-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 18px;
  background-color: var(--surface-container-lowest);
  border-radius: 8px;
  border: 1px solid rgba(195, 199, 203, 0.2);
  box-shadow: 0 4px 16px rgba(15, 31, 41, 0.03);
}

.detail-bar__left {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.detail-bar__label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--on-surface-variant);
}

.detail-bar__name {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  margin-top: 2px;
}

.detail-bar__stats {
  display: flex;
  gap: 20px;
}

.detail-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.detail-stat__val {
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}

.val--live { color: #16a34a; }
.val--off  { color: var(--on-surface-variant); }

.detail-stat__label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--on-surface-variant);
}

.detail-bar__fullscreen {
  display: flex;
  align-items: center;
  padding: 6px;
  border: none;
  background: var(--surface-container-low);
  border-radius: 6px;
  cursor: pointer;
  color: var(--on-surface-variant);
  transition: background-color 0.15s, color 0.15s;
}

.detail-bar__fullscreen:hover {
  background-color: var(--surface-container-highest);
  color: var(--primary);
}

/* Detail bar slide transition */
.slide-detail-enter-active,
.slide-detail-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.slide-detail-enter-from { opacity: 0; transform: translateY(8px); }
.slide-detail-leave-to   { opacity: 0; transform: translateY(4px); }

/* ─── Sidebar ────────────────────────────────────────────────────────────────── */
.monitor__sidebar {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

/* ─── Mini stat card ─────────────────────────────────────────────────────────── */
.mini-stat-card {
  background-color: var(--surface-container-lowest);
  border-radius: 10px;
  padding: 20px;
  border: 1px solid rgba(195, 199, 203, 0.2);
  box-shadow: 0 20px 40px rgba(15, 31, 41, 0.025);
  flex-shrink: 0;
}

.mini-stat-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.mini-stat-card__streams {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: var(--primary);
}

.mini-stat-card__value {
  font-size: 36px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.02em;
  margin: 6px 0;
  font-variant-numeric: tabular-nums;
}

.mini-stat-card__sub {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.mini-stat-card__label {
  color: var(--on-surface-variant);
  font-weight: 500;
}

.mini-stat-card__pct {
  font-weight: 700;
  color: var(--primary);
}

/* ─── Realtime log fills remaining sidebar height ────────────────────────────── */
.monitor__rtlog {
  flex: 1;
  min-height: 0;
}

/* ─── Label utility ──────────────────────────────────────────────────────────── */
.label-xs {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--on-surface-variant);
}
</style>
