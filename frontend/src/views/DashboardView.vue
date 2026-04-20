<template>
  <MainLayout>
    <div class="dashboard">

      <!-- ══════════════════════════════════════════════════════════
           ROW 1 — Metric Cards (4 columns)
           ══════════════════════════════════════════════════════════ -->
      <section class="dashboard__metrics">
        <MetricCard
          label="Deteksi Hari Ini"
          :value="stats.todayTotal"
          icon="directions_car"
          :trend="12"
          trend-label="vs kemarin"
        />
        <MetricCard
          label="Akurasi OCR"
          :value="stats.ocrAccuracy"
          unit="%"
          icon="center_focus_strong"
          :trend="0.2"
          trend-label="avg"
        />
        <MetricCard
          label="Avg Latency"
          :value="stats.avgLatency"
          unit="ms"
          icon="speed"
          :trend="null"
          sub-label="Optimal Range"
        />
        <MetricCard
          label="Alert Aktif"
          :value="stats.activeAlerts"
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
              <span class="live-pulse"></span>
              <h2 class="live-panel__title">Pintu Masuk Utama – Cam 01</h2>
            </div>
            <div class="live-panel__meta">
              <span class="live-panel__badge">1080p / 30fps</span>
              <RouterLink to="/live" class="live-panel__goto">
                <span class="material-symbols-outlined" style="font-size:15px">open_in_new</span>
                Full Monitor
              </RouterLink>
            </div>
          </div>

          <!-- Feed canvas -->
          <div class="live-panel__feed">
            <!-- Placeholder video frame -->
            <div class="live-panel__placeholder">
              <span class="material-symbols-outlined" style="font-size:48px;color:rgba(255,255,255,0.15)">
                videocam
              </span>
              <p style="color:rgba(255,255,255,0.4);font-size:12px;margin-top:8px">
                Hubungkan kamera untuk memulai live feed
              </p>
            </div>

            <!-- AI annotation overlay (demo) -->
            <div class="live-panel__annotation" v-if="demoAnnotation.show">
              <div class="annotation-box">
                <div class="annotation-chip glass">
                  <span class="annotation-chip__plate">{{ demoAnnotation.plate }}</span>
                  <span class="annotation-chip__conf">{{ demoAnnotation.conf }}%</span>
                </div>
              </div>
            </div>

            <!-- Bottom metadata badges -->
            <div class="live-panel__meta-badges">
              <span class="meta-badge glass">CONF: HIGH</span>
              <span class="meta-badge glass">TYPE: {{ demoAnnotation.type }}</span>
              <span class="meta-badge glass">REG: {{ demoAnnotation.region }}</span>
            </div>
          </div>
        </div>

        <!-- Detection Log (1/3 width) -->
        <div class="dashboard__log-panel">
          <DetectionLog
            :items="dummyDetections"
            :loading="false"
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
          <DetectionChart :data="dummyChartData" />
        </div>

        <!-- Source + region breakdown (1/3) -->
        <div class="dashboard__breakdown">
          <SourceBreakdown :source-data="dummySourceData" :region-data="dummyRegionData" />
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
            v-for="cam in dummyCameras"
            :key="cam.id"
            class="camera-card"
            :class="{ 'camera-card--offline': !cam.online }"
          >
            <div class="camera-card__status-dot"
              :class="cam.online ? 'dot--online' : 'dot--offline'"
            ></div>
            <div class="camera-card__info">
              <p class="camera-card__name">{{ cam.name }}</p>
              <p class="camera-card__location">{{ cam.location }}</p>
            </div>
            <div class="camera-card__stat">
              <span class="camera-card__count">{{ cam.detections_today.toLocaleString('id-ID') }}</span>
              <span class="camera-card__count-label">hari ini</span>
            </div>
          </div>
        </div>
      </section>

    </div>
  </MainLayout>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'
import MetricCard from '@/components/dashboard/MetricCard.vue'
import DetectionLog from '@/components/dashboard/DetectionLog.vue'
import DetectionChart from '@/components/dashboard/DetectionChart.vue'
import SourceBreakdown from '@/components/dashboard/SourceBreakdown.vue'

// ─── Summary stats (dummy) ───────────────────────────────────────────────────
const stats = reactive({
  todayTotal:   14289,
  ocrAccuracy:  98.4,
  avgLatency:   124,
  activeAlerts: 3,
})

// ─── Demo live annotation ────────────────────────────────────────────────────
const demoAnnotation = reactive({
  show:   true,
  plate:  'B 1234 XYZ',
  conf:   99,
  type:   'SUV',
  region: 'DKI Jakarta',
})

// ─── Dummy detection log ─────────────────────────────────────────────────────
const dummyDetections = [
  { id: 1, plate_text: 'B 1234 XYZ', status: 'valid',     detected_at: new Date(Date.now() - 1*60000).toISOString(), crop_url: null },
  { id: 2, plate_text: 'D 8888 AA',  status: 'watchlist', detected_at: new Date(Date.now() - 2*60000).toISOString(), crop_url: null },
  { id: 3, plate_text: 'F 5678 BCD', status: 'valid',     detected_at: new Date(Date.now() - 4*60000).toISOString(), crop_url: null },
  { id: 4, plate_text: 'AB 123 CD',  status: 'valid',     detected_at: new Date(Date.now() - 6*60000).toISOString(), crop_url: null },
  { id: 5, plate_text: '???',        status: 'ocr_failed', detected_at: new Date(Date.now() - 8*60000).toISOString(), crop_url: null },
  { id: 6, plate_text: 'L 9999 XY',  status: 'watchlist', detected_at: new Date(Date.now() - 10*60000).toISOString(), crop_url: null },
  { id: 7, plate_text: 'N 0001 A',   status: 'valid',     detected_at: new Date(Date.now() - 12*60000).toISOString(), crop_url: null },
  { id: 8, plate_text: 'T 4567 NN',  status: 'valid',     detected_at: new Date(Date.now() - 14*60000).toISOString(), crop_url: null },
]

// ─── Dummy chart data (7 days) ───────────────────────────────────────────────
const dummyChartData = (() => {
  const days = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const total     = Math.floor(Math.random() * 3000) + 11000
    const watchlist = Math.floor(Math.random() * 30) + 5
    days.push({
      date:      d.toISOString().slice(0, 10),
      total,
      valid:     total - watchlist - Math.floor(Math.random() * 50),
      watchlist,
    })
  }
  return days
})()

// ─── Dummy source data ───────────────────────────────────────────────────────
const dummySourceData = [
  { source: 'stream',      count: 9821 },
  { source: 'upload',      count: 3102 },
  { source: 'video_batch', count: 1366 },
]

// ─── Dummy region data ───────────────────────────────────────────────────────
const dummyRegionData = [
  { region_code: 'B',  region: 'DKI Jakarta',    count: 4210 },
  { region_code: 'D',  region: 'Bandung',         count: 2841 },
  { region_code: 'L',  region: 'Surabaya',        count: 2103 },
  { region_code: 'AB', region: 'Yogyakarta',      count: 1562 },
  { region_code: 'F',  region: 'Bogor',           count: 987  },
]

// ─── Dummy camera status ─────────────────────────────────────────────────────
const dummyCameras = [
  { id: 1, name: 'Pintu Masuk Utama', location: 'Gate A',  online: true,  detections_today: 5823 },
  { id: 2, name: 'Pintu Keluar',      location: 'Gate B',  online: true,  detections_today: 4511 },
  { id: 3, name: 'Parkir Basement',   location: 'B1',      online: false, detections_today: 0    },
  { id: 4, name: 'Area Tamu',         location: 'Lobby',   online: true,  detections_today: 3955 },
]

// ─── Handlers ────────────────────────────────────────────────────────────────
function handleRefresh() {
  // TODO: call detection store fetchDetections()
}

function handleDetectionSelect(item) {
  // TODO: open detail drawer
}

// ─── Animate demo annotation plate periodically ───────────────────────────────
const plates = ['B 1234 XYZ', 'D 8888 AA', 'F 5678 BCD', 'L 9999 XY', 'AB 123 CD']
let plateTimer = null
onMounted(() => {
  plateTimer = setInterval(() => {
    demoAnnotation.plate = plates[Math.floor(Math.random() * plates.length)]
    demoAnnotation.conf  = Math.floor(Math.random() * 5) + 95
  }, 2500)
})
onUnmounted(() => {
  clearInterval(plateTimer)
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

.live-panel__badge {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: var(--on-surface-variant);
  background-color: var(--surface-container);
  padding: 3px 8px;
  border-radius: 4px;
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

/* ─── Feed area ──────────────────────────────────────────────────────────────── */
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
