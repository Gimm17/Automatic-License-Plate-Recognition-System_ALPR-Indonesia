<template>
  <MainLayout>
    <div class="dashboard">

      <!-- ══════════════════════════════════════════════════════════
           ROW 1 — Metric Cards (4 columns)
           ══════════════════════════════════════════════════════════ -->
      <section class="dashboard__metrics">
        <MetricCard
          label="Deteksi Hari Ini"
          :value="stats.total_detections ?? stats.todayTotal"
          icon="directions_car"
          :trend="12"
          trend-label="vs kemarin"
        />
        <MetricCard
          label="Akurasi OCR"
          :value="stats.ocr_accuracy_pct ?? stats.ocrAccuracy"
          unit="%"
          icon="center_focus_strong"
          :trend="0.2"
          trend-label="avg"
        />
        <MetricCard
          label="Avg Confidence"
          :value="stats.avg_confidence_pct ?? stats.avgConfidence"
          unit="%"
          icon="speed"
          :trend="null"
          sub-label="YOLO Mean"
        />
        <MetricCard
          label="Alert Aktif"
          :value="stats.watchlist_hits ?? stats.activeAlerts"
          icon="warning"
          :alert="true"
          :trend="null"
          sub-label="Membutuhkan Perhatian"
        />
      </section>

      <!-- ══════════════════════════════════════════════════════════
           ROW 2 — Live Feed + Recent Detections
           ══════════════════════════════════════════════════════════ -->
      <section class="dashboard__live-row">

        <!-- Live Feed Panel (2/3 width) -->
        <div class="dashboard__live-panel">
          <!-- Panel header -->
          <div class="live-panel__header">
            <div class="live-panel__title-group">
              <span class="live-pulse" v-if="selectedCam"></span>
              <h2 class="live-panel__title">
                {{ selectedCam ? selectedCam.name : 'Belum ada kamera aktif' }}
              </h2>
            </div>
            <div class="live-panel__meta">
              <!-- Camera selector dropdown -->
              <select
                v-if="activeCameras.length > 1"
                v-model="selectedCamId"
                class="cam-selector"
              >
                <option
                  v-for="cam in activeCameras"
                  :key="cam.id"
                  :value="cam.id"
                >{{ cam.name }}</option>
              </select>
              <RouterLink to="/live" class="live-panel__goto">
                <span class="material-symbols-outlined" style="font-size:15px">open_in_new</span>
                Full Monitor
              </RouterLink>
            </div>
          </div>

          <!-- Feed canvas -->
          <div class="live-panel__feed">
            <!-- HLS Video player -->
            <video
              v-if="selectedCam"
              ref="dashVideoEl"
              class="live-panel__video"
              muted
              playsinline
              autoplay
            />

            <!-- Loading overlay -->
            <div v-if="selectedCam && !dashVideoLoaded && !dashVideoError" class="live-panel__placeholder">
              <span class="material-symbols-outlined" style="font-size:48px;color:rgba(255,255,255,0.15)">videocam</span>
              <p style="color:rgba(255,255,255,0.4);font-size:12px;margin-top:8px">Memuat stream…</p>
            </div>

            <!-- Error state -->
            <div v-if="dashVideoError" class="live-panel__placeholder">
              <span class="material-symbols-outlined" style="font-size:36px;color:rgba(255,255,255,0.15)">signal_disconnected</span>
              <p style="color:rgba(255,255,255,0.4);font-size:12px;margin-top:8px">Stream tidak dapat dimuat</p>
            </div>

            <!-- No cameras state -->
            <div v-if="!selectedCam" class="live-panel__placeholder">
              <span class="material-symbols-outlined" style="font-size:48px;color:rgba(255,255,255,0.15)">videocam</span>
              <p style="color:rgba(255,255,255,0.4);font-size:12px;margin-top:8px">
                Tambahkan kamera di
                <RouterLink to="/pengaturan" style="color:rgba(255,255,255,0.6);text-decoration:underline">Pengaturan</RouterLink>
              </p>
            </div>

            <!-- Bottom metadata badges -->
            <div class="live-panel__meta-badges">
              <span class="meta-badge glass">{{ cameraItems.length }} Kamera Terdaftar</span>
              <span class="meta-badge glass">{{ cameraItems.filter(c=>c.is_active).length }} Aktif</span>
            </div>
          </div>
        </div>

        <!-- Detection Log (1/3 width) -->
        <div class="dashboard__log-panel">
          <DetectionLog
            :items="logItems"
            :loading="detectionStore.loading"
            @refresh="handleRefresh"
            @select="handleDetectionSelect"
          />
        </div>
      </section>

      <!-- ══════════════════════════════════════════════════════════
           ROW 3 — Chart + Breakdown
           ══════════════════════════════════════════════════════════ -->
      <section class="dashboard__analytics-row">
        <!-- 7-day trend chart (2/3) -->
        <div class="dashboard__chart">
          <DetectionChart :data="chartItems" />
        </div>

        <!-- Source + region breakdown (1/3) -->
        <div class="dashboard__breakdown">
          <SourceBreakdown :source-data="sourceItems" :region-data="regionItems" />
        </div>
      </section>

      <!-- ══════════════════════════════════════════════════════════
           ROW 4 — Camera Status Cards
           ══════════════════════════════════════════════════════════ -->
      <section class="dashboard__cameras">
        <div class="dashboard__cameras-header">
          <h3 class="dashboard__section-title">Status Kamera</h3>
          <RouterLink to="/pengaturan" class="dashboard__section-link">
            Kelola Kamera
            <span class="material-symbols-outlined" style="font-size:14px">arrow_forward</span>
          </RouterLink>
        </div>

        <div class="camera-grid">
          <div
            v-for="cam in cameraItems"
            :key="cam.id"
            class="camera-card"
            :class="{ 'camera-card--offline': !cam.online && !cam.is_active }"
          >
            <div class="camera-card__status-dot"
              :class="(cam.online || cam.is_active) ? 'dot--online' : 'dot--offline'"
            ></div>
            <div class="camera-card__info">
              <p class="camera-card__name">{{ cam.name || cam.location_name }}</p>
              <p class="camera-card__location">{{ cam.location || cam.cam_id || 'ID tidak diketahui' }}</p>
            </div>
            <div class="camera-card__stat">
              <span class="camera-card__count">{{ (cam.detections_today ?? 0).toLocaleString('id-ID') }}</span>
              <span class="camera-card__count-label">hari ini</span>
            </div>
          </div>
        </div>
      </section>

    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import Hls from 'hls.js'
import MainLayout from '@/components/layout/MainLayout.vue'
import MetricCard from '@/components/dashboard/MetricCard.vue'
import DetectionLog from '@/components/dashboard/DetectionLog.vue'
import DetectionChart from '@/components/dashboard/DetectionChart.vue'
import SourceBreakdown from '@/components/dashboard/SourceBreakdown.vue'
import { useStatsStore }     from '@/stores/stats'
import { useCameraStore }    from '@/stores/camera'
import { useDetectionStore } from '@/stores/detection'

const statsStore     = useStatsStore()
const cameraStore    = useCameraStore()
const detectionStore = useDetectionStore()

// ─── Metric cards ───────────────────────────────────────────────────────────────────────
const EMPTY_STATS = { total_detections: 0, ocr_accuracy_pct: 0, avg_confidence_pct: 0, watchlist_hits: 0 }
const stats = computed(() => statsStore.summary || EMPTY_STATS)

// ─── Detection log / chart / breakdown ───────────────────────────────────────────────────────
const logItems    = computed(() => detectionStore.detections)
const chartItems  = computed(() => statsStore.chartData || [])
const sourceItems = computed(() => statsStore.sourceData || [])
const regionItems = computed(() => statsStore.regionData || [])
const cameraItems = computed(() => cameraStore.cameras)

// ─── Camera selector + HLS player ──────────────────────────────────────────────────────────
const activeCameras  = computed(() => cameraStore.cameras.filter(c => c.is_active))
const selectedCamId  = ref(null)
const selectedCam    = computed(() => activeCameras.value.find(c => c.id === selectedCamId.value) || null)
const dashVideoEl    = ref(null)
const dashVideoLoaded = ref(false)
const dashVideoError  = ref(false)

let dashHls = null

function destroyDashHls() {
  if (dashHls) { dashHls.destroy(); dashHls = null }
}

function initDashHls() {
  destroyDashHls()
  if (!selectedCam.value || !dashVideoEl.value) return

  const url = selectedCam.value.rtsp_url
  if (!url) return

  dashVideoLoaded.value = false
  dashVideoError.value  = false

  if (Hls.isSupported()) {
    dashHls = new Hls({
      enableWorker: true,
      manifestLoadingMaxRetry: 8,
      manifestLoadingRetryDelay: 2000,
    })
    dashHls.loadSource(url)
    dashHls.attachMedia(dashVideoEl.value)
    dashHls.on(Hls.Events.MANIFEST_PARSED, () => {
      dashVideoEl.value?.play().catch(() => {})
      dashVideoLoaded.value = true
    })
    dashHls.on(Hls.Events.ERROR, (_, data) => {
      if (data.fatal) { dashVideoError.value = true }
    })
  } else if (dashVideoEl.value.canPlayType('application/vnd.apple.mpegurl')) {
    dashVideoEl.value.src = url
    dashVideoEl.value.play().catch(() => {})
    dashVideoLoaded.value = true
  } else {
    dashVideoError.value = true
  }
}

// Auto-select first camera when cameras load
watch(activeCameras, (cams) => {
  if (cams.length && !selectedCamId.value) {
    selectedCamId.value = cams[0].id
  }
}, { immediate: true })

// Re-init HLS when selected camera changes
watch(selectedCam, () => {
  dashVideoLoaded.value = false
  dashVideoError.value  = false
  setTimeout(initDashHls, 150)
})

// ─── Handlers ──────────────────────────────────────────────────────────────────────────────
function handleRefresh() { detectionStore.fetchDetections() }
function handleDetectionSelect() { /* TODO: open global detail drawer */ }

// ─── Lifecycle ──────────────────────────────────────────────────────────────────────────────
onMounted(async () => {
  statsStore.startAutoRefresh(30_000)
  await cameraStore.fetchCameras()
  detectionStore.fetchDetections()
})

onUnmounted(() => {
  statsStore.stopAutoRefresh()
  destroyDashHls()
})
</script>

<style scoped>
/* ─── Dashboard container ────────────────────────────────────────────────────── */
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ─── ROW 1 — Metric cards ───────────────────────────────────────────────────── */
.dashboard__metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

/* ─── ROW 2 — Live + log row ─────────────────────────────────────────────────── */
.dashboard__live-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  align-items: stretch;
}

/* ─── Live panel ─────────────────────────────────────────────────────────────── */
.dashboard__live-panel {
  background-color: var(--surface-container-low);
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.live-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background-color: var(--surface-container-lowest);
  border-radius: 10px 10px 0 0;
}

.live-panel__title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.live-panel__title {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -0.01em;
}

.live-panel__meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.live-panel__goto {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--on-surface-variant);
  text-decoration: none;
  transition: color 0.15s;
}
.live-panel__goto:hover { color: var(--primary); }

/* ─── Feed area ─────────────────────────────────────────────────────────────────────────────── */
.live-panel__feed {
  flex: 1;
  background-color: #0b151c;
  min-height: 360px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.live-panel__video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ─── Camera selector ──────────────────────────────────────────────────────────────────────────── */
.cam-selector {
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  background: var(--surface-container);
  border: 1px solid rgba(195,199,203,0.3);
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  outline: none;
  transition: border-color 0.15s;
}
.cam-selector:hover { border-color: var(--primary); }

.live-panel__placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  user-select: none;
}

/* ─── Annotation overlay ─────────────────────────────────────────────────────── */
.live-panel__annotation {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.annotation-box {
  position: absolute;
  top: 38%;
  left: 30%;
  border: 2px solid var(--tertiary-fixed-dim);
  width: 130px;
  height: 90px;
  border-radius: 4px;
  background-color: rgba(255, 183, 134, 0.08);
}

.annotation-chip {
  position: absolute;
  top: -34px;
  left: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border-radius: 4px;
  white-space: nowrap;
}

.annotation-chip__plate {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: 0.04em;
}

.annotation-chip__conf {
  font-size: 11px;
  font-weight: 700;
  color: #16a34a;
}

/* ─── Meta badges ────────────────────────────────────────────────────────────── */
.live-panel__meta-badges {
  position: absolute;
  bottom: 14px;
  left: 14px;
  display: flex;
  gap: 8px;
}

.meta-badge {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  font-weight: 700;
  color: var(--primary);
  padding: 4px 10px;
  border-radius: 4px;
}

/* ─── Log panel ──────────────────────────────────────────────────────────────── */
.dashboard__log-panel {
  display: flex;
  flex-direction: column;
  min-height: 440px;
}

/* ─── ROW 3 — Analytics ──────────────────────────────────────────────────────── */
.dashboard__analytics-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

/* ─── ROW 4 — Cameras ────────────────────────────────────────────────────────── */
.dashboard__cameras {}

.dashboard__cameras-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.dashboard__section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -0.01em;
}

.dashboard__section-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--on-surface-variant);
  text-decoration: none;
  transition: color 0.15s;
}
.dashboard__section-link:hover { color: var(--primary); }

/* ─── Camera grid ────────────────────────────────────────────────────────────── */
.camera-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.camera-card {
  background-color: var(--surface-container-lowest);
  border-radius: 8px;
  padding: 16px 18px;
  box-shadow: 0 4px 16px rgba(15, 31, 41, 0.03);
  border: 1px solid rgba(195, 199, 203, 0.2);
  display: flex;
  align-items: center;
  gap: 12px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.camera-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(15, 31, 41, 0.06);
}

.camera-card--offline { opacity: 0.55; }

.camera-card__status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot--online  { background-color: #16a34a; box-shadow: 0 0 0 3px rgba(22,163,74,0.15); }
.dot--offline { background-color: var(--outline); }

.camera-card__info { flex: 1; min-width: 0; }

.camera-card__name {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.camera-card__location {
  font-size: 11px;
  color: var(--on-surface-variant);
  margin-top: 2px;
}

.camera-card__stat {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
}

.camera-card__count {
  font-size: 16px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}

.camera-card__count-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--on-surface-variant);
}

/* ─── Responsive ─────────────────────────────────────────────────────────────── */
@media (max-width: 1280px) {
  .dashboard__metrics  { grid-template-columns: repeat(2, 1fr); }
  .camera-grid         { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 900px) {
  .dashboard__live-row,
  .dashboard__analytics-row { grid-template-columns: 1fr; }
  .dashboard__metrics        { grid-template-columns: repeat(2, 1fr); }
  .camera-grid               { grid-template-columns: 1fr 1fr; }
}
</style>
