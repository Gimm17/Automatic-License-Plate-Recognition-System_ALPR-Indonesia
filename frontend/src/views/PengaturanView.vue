<template>
  <MainLayout>
    <div class="pengaturan-page">

      <!-- ══ HEADING ═══════════════════════════════════════════════════════════ -->
      <div class="peng-heading">
        <div>
          <h2 class="peng-heading__title">Pengaturan Kamera</h2>
          <p class="peng-heading__sub">Kelola status dan konfigurasi jaringan kamera ALPR.</p>
        </div>
        <div class="peng-heading__actions">
          <button class="btn-add-cam" @click="openCamForm(null)">
            <span class="material-symbols-outlined" style="font-size:16px">add</span>
            Tambah Kamera
          </button>
        </div>
      </div>

      <!-- ══ BENTO GRID ═════════════════════════════════════════════════════════ -->
      <div class="bento-grid">

        <!-- ── LEFT: Camera list (2 cols) ─────────────────────────────────── -->
        <div class="cam-section">

          <!-- Status header bar -->
          <div class="cam-status-bar">
            <span class="cam-status-bar__label">Kamera Aktif</span>
            <div class="cam-status-bar__badges">
              <span class="badge badge--ok">
                <span class="dot dot--ok"></span>
                {{ onlineCameras.length }} Online
              </span>
              <span class="badge badge--alert">
                <span class="dot dot--alert"></span>
                {{ offlineCameras.length }} Offline
              </span>
            </div>
          </div>

          <!-- Camera cards grid -->
          <div class="cam-grid">
            <div
              v-for="cam in cameras"
              :key="cam.id"
              class="cam-card"
              :class="{
                'cam-card--offline': cam.status === 'offline',
                'cam-card--active':  selectedCam?.id === cam.id,
              }"
              @click="selectedCam = cam"
            >
              <!-- Left accent bar -->
              <div
                class="cam-card__accent"
                :class="cam.status === 'online' ? 'accent--ok' : 'accent--alert'"
              ></div>

              <!-- Card header -->
              <div class="cam-card__header">
                <div>
                  <h3 class="cam-card__name" :class="{ 'muted': cam.status === 'offline' }">
                    {{ cam.name }}
                  </h3>
                  <p class="cam-card__id" :class="{ 'muted': cam.status === 'offline' }">
                    ID: {{ cam.cam_id }}
                  </p>
                </div>
                <button class="btn-more" @click.stop="openCamForm(cam)">
                  <span class="material-symbols-outlined" style="font-size:18px">more_vert</span>
                </button>
              </div>

              <!-- Preview thumbnail -->
              <div class="cam-card__preview">
                <template v-if="cam.status === 'online'">
                  <div class="cam-preview-placeholder">
                    <span class="material-symbols-outlined" style="font-size:32px;color:var(--on-surface-variant);opacity:.3">videocam</span>
                  </div>
                  <!-- LIVE badge -->
                  <div class="live-badge">
                    <span class="live-dot"></span>
                    LIVE
                  </div>
                </template>
                <template v-else>
                  <div class="cam-preview-offline">
                    <span class="material-symbols-outlined" style="font-size:32px;opacity:.3">videocam_off</span>
                    <span class="offline-text">Signal Lost</span>
                  </div>
                </template>
              </div>

              <!-- Cam info row -->
              <div class="cam-card__info">
                <div class="cam-info-item">
                  <span class="cam-info-item__label">Resolusi</span>
                  <span class="cam-info-item__val">
                    {{ cam.status === 'online' ? cam.resolution : '—' }}
                  </span>
                </div>
                <div class="cam-info-item cam-info-item--right">
                  <span class="cam-info-item__label">Status</span>
                  <span
                    class="cam-info-item__val cam-info-item__val--status"
                    :class="cam.status === 'online' ? 'status--ok' : 'status--alert'"
                  >
                    {{ cam.status === 'online' ? 'Online' : 'Offline' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── RIGHT: Add/Edit form panel ─────────────────────────────────── -->
        <div class="form-panel">
          <div class="form-panel__header">
            <h3 class="form-panel__title">
              {{ editCam ? 'Edit Kamera' : 'Tambah Kamera Baru' }}
            </h3>
            <p class="form-panel__sub">
              {{ editCam ? 'Perbarui konfigurasi kamera.' : 'Registrasi perangkat ALPR ke dalam sistem.' }}
            </p>
          </div>

          <form class="cam-form" @submit.prevent="saveCamForm">

            <div class="cam-form__field">
              <label class="cam-form__label">Nama Lokasi *</label>
              <input
                v-model="camForm.name"
                type="text"
                class="cam-form__input"
                placeholder="Cth: Gerbang Tol Bintaro"
              />
            </div>

            <div class="cam-form__field">
              <label class="cam-form__label">IP Address / RTSP Stream *</label>
              <input
                v-model="camForm.rtsp_url"
                type="text"
                class="cam-form__input cam-form__input--mono"
                placeholder="rtsp://admin:pass@192.168.1.100/stream"
              />
            </div>

            <div class="cam-form__row">
              <div class="cam-form__field">
                <label class="cam-form__label">Resolusi</label>
                <select v-model="camForm.resolution" class="cam-form__select">
                  <option>4K / 30fps</option>
                  <option>1080p / 60fps</option>
                  <option>1080p / 30fps</option>
                  <option>720p / 30fps</option>
                  <option>720p / 15fps</option>
                </select>
              </div>
              <div class="cam-form__field">
                <label class="cam-form__label">Wilayah</label>
                <select v-model="camForm.region" class="cam-form__select">
                  <option v-for="r in REGIONS" :key="r" :value="r">{{ r }}</option>
                </select>
              </div>
            </div>

            <div class="cam-form__field">
              <label class="cam-form__label">Zona Deteksi</label>
              <div class="detection-zone" @click="zoneClicked">
                <span class="material-symbols-outlined" style="font-size:16px;color:var(--on-surface-variant)">add_location</span>
                <span>{{ camForm.zone || 'Tentukan Area Mapping' }}</span>
              </div>
            </div>

            <div class="cam-form__field">
              <label class="cam-form__label">Confidence Threshold</label>
              <div class="threshold-wrap">
                <input
                  v-model.number="camForm.confidence_threshold"
                  type="range" min="0.5" max="1" step="0.01"
                  class="cam-form__range"
                />
                <span class="threshold-val">{{ (camForm.confidence_threshold * 100).toFixed(0) }}%</span>
              </div>
            </div>

            <!-- Toggle switches -->
            <div class="cam-form__switches">
              <div class="switch-row">
                <div>
                  <div class="switch-row__label">Aktifkan Kamera</div>
                  <div class="switch-row__sub">Kamera akan dihubungkan saat sistem aktif</div>
                </div>
                <button
                  type="button"
                  class="toggle"
                  :class="{ 'toggle--on': camForm.enabled }"
                  @click="camForm.enabled = !camForm.enabled"
                  :aria-pressed="camForm.enabled"
                >
                  <span class="toggle__knob"></span>
                </button>
              </div>

              <div class="switch-row">
                <div>
                  <div class="switch-row__label">Alert Watchlist</div>
                  <div class="switch-row__sub">Kirim notifikasi jika plat terdeteksi di watchlist</div>
                </div>
                <button
                  type="button"
                  class="toggle"
                  :class="{ 'toggle--on': camForm.watchlist_alert }"
                  @click="camForm.watchlist_alert = !camForm.watchlist_alert"
                  :aria-pressed="camForm.watchlist_alert"
                >
                  <span class="toggle__knob"></span>
                </button>
              </div>

              <div class="switch-row">
                <div>
                  <div class="switch-row__label">Rekam Otomatis</div>
                  <div class="switch-row__sub">Simpan frame saat deteksi plat berhasil</div>
                </div>
                <button
                  type="button"
                  class="toggle"
                  :class="{ 'toggle--on': camForm.auto_record }"
                  @click="camForm.auto_record = !camForm.auto_record"
                  :aria-pressed="camForm.auto_record"
                >
                  <span class="toggle__knob"></span>
                </button>
              </div>
            </div>

            <!-- Form actions -->
            <div class="cam-form__actions">
              <button
                v-if="editCam"
                type="button"
                class="btn-danger-sm"
                @click="confirmDeleteCam(editCam)"
              >
                <span class="material-symbols-outlined" style="font-size:14px">delete</span>
                Hapus
              </button>
              <button type="button" class="btn-cancel-sm" @click="resetCamForm">
                Batal
              </button>
              <button
                type="submit"
                class="btn-save-cam"
                :disabled="!camForm.name.trim() || !camForm.rtsp_url.trim()"
              >
                <span class="material-symbols-outlined" style="font-size:14px">save</span>
                {{ editCam ? 'Simpan' : 'Tambah Kamera' }}
              </button>
            </div>
          </form>
        </div>

      </div><!-- /bento-grid -->

      <!-- ══ GLOBAL SETTINGS SECTION ═══════════════════════════════════════════ -->
      <div class="global-settings">
        <h3 class="global-settings__title">Pengaturan Global Sistem</h3>

        <div class="settings-grid">

          <!-- Detection settings -->
          <div class="settings-card">
            <div class="settings-card__icon-wrap">
              <span class="material-symbols-outlined" style="font-size:20px;color:var(--primary)">tune</span>
            </div>
            <h4 class="settings-card__title">Parameter Deteksi</h4>

            <div class="settings-item">
              <label class="settings-label">Model YOLO</label>
              <select v-model="globalSettings.model" class="settings-select">
                <option value="yolov8n">YOLOv8n (Fast)</option>
                <option value="yolov8s">YOLOv8s (Balanced)</option>
                <option value="yolov8m">YOLOv8m (Accurate)</option>
              </select>
            </div>

            <div class="settings-item">
              <label class="settings-label">Min. Confidence Global</label>
              <div class="threshold-wrap">
                <input v-model.number="globalSettings.min_confidence" type="range" min="0.4" max="1" step="0.01" class="cam-form__range" />
                <span class="threshold-val">{{ (globalSettings.min_confidence * 100).toFixed(0) }}%</span>
              </div>
            </div>

            <div class="settings-item">
              <label class="settings-label">Frame Skip Rate</label>
              <select v-model="globalSettings.frame_skip" class="settings-select">
                <option :value="1">Setiap Frame (Max)</option>
                <option :value="2">1 dari 2 Frame</option>
                <option :value="3">1 dari 3 Frame</option>
                <option :value="5">1 dari 5 Frame</option>
              </select>
            </div>
          </div>

          <!-- OCR settings -->
          <div class="settings-card">
            <div class="settings-card__icon-wrap">
              <span class="material-symbols-outlined" style="font-size:20px;color:var(--primary)">font_download</span>
            </div>
            <h4 class="settings-card__title">Konfigurasi OCR</h4>

            <div class="settings-item">
              <label class="settings-label">Engine OCR</label>
              <select v-model="globalSettings.ocr_engine" class="settings-select">
                <option value="paddleocr">PaddleOCR (Rekomendasi)</option>
                <option value="tesseract">Tesseract</option>
                <option value="easyocr">EasyOCR</option>
              </select>
            </div>

            <div class="settings-item">
              <label class="settings-label">Validasi Format Plat</label>
              <div class="switch-row switch-row--inline">
                <span class="settings-label--sm">Wajib sesuai format Indonesia</span>
                <button
                  type="button"
                  class="toggle toggle--sm"
                  :class="{ 'toggle--on': globalSettings.validate_format }"
                  @click="globalSettings.validate_format = !globalSettings.validate_format"
                >
                  <span class="toggle__knob"></span>
                </button>
              </div>
            </div>

            <div class="settings-item">
              <label class="settings-label">Max Char OCR</label>
              <select v-model="globalSettings.max_chars" class="settings-select">
                <option :value="8">8 Karakter</option>
                <option :value="9">9 Karakter</option>
                <option :value="10">10 Karakter</option>
              </select>
            </div>
          </div>

          <!-- Notification settings -->
          <div class="settings-card">
            <div class="settings-card__icon-wrap">
              <span class="material-symbols-outlined" style="font-size:20px;color:var(--primary)">notifications</span>
            </div>
            <h4 class="settings-card__title">Notifikasi & Alert</h4>

            <div class="settings-item">
              <div class="switch-row switch-row--inline">
                <label class="settings-label">Email Alert</label>
                <button type="button" class="toggle toggle--sm"
                  :class="{ 'toggle--on': globalSettings.email_alert }"
                  @click="globalSettings.email_alert = !globalSettings.email_alert"
                ><span class="toggle__knob"></span></button>
              </div>
            </div>

            <div v-if="globalSettings.email_alert" class="settings-item">
              <label class="settings-label">Email Tujuan</label>
              <input v-model="globalSettings.email" type="email" class="cam-form__input" placeholder="admin@example.com" />
            </div>

            <div class="settings-item">
              <div class="switch-row switch-row--inline">
                <label class="settings-label">Webhook (POST)</label>
                <button type="button" class="toggle toggle--sm"
                  :class="{ 'toggle--on': globalSettings.webhook_enabled }"
                  @click="globalSettings.webhook_enabled = !globalSettings.webhook_enabled"
                ><span class="toggle__knob"></span></button>
              </div>
            </div>

            <div v-if="globalSettings.webhook_enabled" class="settings-item">
              <label class="settings-label">Webhook URL</label>
              <input v-model="globalSettings.webhook_url" type="url" class="cam-form__input cam-form__input--mono" placeholder="https://hooks.example.com/..." />
            </div>
          </div>

          <!-- Storage settings -->
          <div class="settings-card">
            <div class="settings-card__icon-wrap">
              <span class="material-symbols-outlined" style="font-size:20px;color:var(--primary)">storage</span>
            </div>
            <h4 class="settings-card__title">Penyimpanan</h4>

            <!-- Storage usage bar -->
            <div class="storage-usage">
              <div class="storage-usage__header">
                <span class="settings-label">Disk Usage</span>
                <span class="storage-usage__val">{{ storageUsed }} / {{ storageTotal }}</span>
              </div>
              <div class="storage-track">
                <div class="storage-fill" :style="{ width: storagePercent + '%' }"></div>
              </div>
              <span class="storage-pct">{{ storagePercent }}% terpakai</span>
            </div>

            <div class="settings-item">
              <label class="settings-label">Retensi Frame (hari)</label>
              <select v-model="globalSettings.retention_days" class="settings-select">
                <option :value="7">7 hari</option>
                <option :value="14">14 hari</option>
                <option :value="30">30 hari</option>
                <option :value="90">90 hari</option>
              </select>
            </div>

            <div class="settings-item">
              <div class="switch-row switch-row--inline">
                <label class="settings-label">Auto-purge Lama</label>
                <button type="button" class="toggle toggle--sm"
                  :class="{ 'toggle--on': globalSettings.auto_purge }"
                  @click="globalSettings.auto_purge = !globalSettings.auto_purge"
                ><span class="toggle__knob"></span></button>
              </div>
            </div>
          </div>
        </div>

        <!-- Save global settings -->
        <div class="global-actions">
          <button class="btn-global-reset" @click="resetGlobal">
            <span class="material-symbols-outlined" style="font-size:15px">restart_alt</span>
            Reset ke Default
          </button>
          <button class="btn-global-save" @click="saveGlobal">
            <span class="material-symbols-outlined" style="font-size:15px">save</span>
            Simpan Pengaturan
          </button>
        </div>
      </div>

    </div>

    <!-- ══ DELETE CAM CONFIRM MODAL ══════════════════════════════════════════= -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="deleteCamTarget" class="modal-overlay" @click.self="deleteCamTarget = null">
          <div class="modal-box">
            <h3 class="modal-box__title">Hapus Kamera?</h3>
            <p class="modal-box__text">
              Hapus <strong>{{ deleteCamTarget.name }}</strong> ({{ deleteCamTarget.cam_id }}) dari sistem ALPR?
              Semua konfigurasi akan hilang.
            </p>
            <div class="modal-box__actions">
              <button class="btn-cancel-sm" @click="deleteCamTarget = null">Batal</button>
              <button class="btn-delete" @click="deleteCamConfirmed">
                <span class="material-symbols-outlined" style="font-size:14px">delete</span>
                Hapus Kamera
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Toast notification -->
    <Teleport to="body">
      <Transition name="toast">
        <div v-if="toastMsg" class="toast">
          <span class="material-symbols-outlined" style="font-size:16px;font-variation-settings:'FILL' 1">check_circle</span>
          {{ toastMsg }}
        </div>
      </Transition>
    </Teleport>
  </MainLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'

// ─── Constants ────────────────────────────────────────────────────────────────
const REGIONS = ['DKI Jakarta', 'Jawa Barat', 'Jawa Tengah', 'Jawa Timur', 'Yogyakarta', 'Banten', 'Bali', 'Sumatera Utara']

// ─── Camera list ─────────────────────────────────────────────────────────────
const cameras = ref([
  { id: 1, cam_id: 'CAM-JKT-001', name: 'Gerbang Tol Utama',     status: 'online',  resolution: '1080p / 60fps', rtsp_url: 'rtsp://admin:pass@192.168.1.10/stream', region: 'DKI Jakarta', confidence_threshold: 0.85, enabled: true, watchlist_alert: true,  auto_record: true,  zone: 'Zona A' },
  { id: 2, cam_id: 'CAM-SMG-042', name: 'Simpang Lima',           status: 'online',  resolution: '720p / 30fps',  rtsp_url: 'rtsp://admin:pass@192.168.1.42/stream', region: 'Jawa Tengah',confidence_threshold: 0.80, enabled: true, watchlist_alert: true,  auto_record: false, zone: '' },
  { id: 3, cam_id: 'CAM-BDG-011', name: 'Pintu Keluar Selatan',   status: 'offline', resolution: '',              rtsp_url: 'rtsp://admin:pass@192.168.1.11/stream', region: 'Jawa Barat', confidence_threshold: 0.80, enabled: false, watchlist_alert: false, auto_record: false, zone: '' },
  { id: 4, cam_id: 'CAM-SBY-007', name: 'Terminal Juanda',        status: 'online',  resolution: '1080p / 30fps', rtsp_url: 'rtsp://admin:pass@192.168.1.7/stream',  region: 'Jawa Timur', confidence_threshold: 0.90, enabled: true, watchlist_alert: true,  auto_record: true,  zone: 'Zona B' },
])

const selectedCam = ref(cameras.value[0])

const onlineCameras  = computed(() => cameras.value.filter(c => c.status === 'online'))
const offlineCameras = computed(() => cameras.value.filter(c => c.status === 'offline'))

// ─── Camera form ──────────────────────────────────────────────────────────────
const editCam = ref(null)

const camFormDefault = () => ({
  name: '', rtsp_url: '', region: REGIONS[0],
  resolution: '1080p / 60fps', zone: '',
  confidence_threshold: 0.85,
  enabled: true, watchlist_alert: true, auto_record: false,
})

const camForm = ref(camFormDefault())

function openCamForm(cam) {
  editCam.value = cam
  camForm.value = cam ? { ...cam } : camFormDefault()
}

function resetCamForm() {
  editCam.value = null
  camForm.value  = camFormDefault()
}

function saveCamForm() {
  if (!camForm.value.name.trim() || !camForm.value.rtsp_url.trim()) return

  if (editCam.value) {
    const idx = cameras.value.findIndex(c => c.id === editCam.value.id)
    if (idx !== -1) cameras.value[idx] = { ...cameras.value[idx], ...camForm.value }
  } else {
    cameras.value.push({
      ...camForm.value,
      id: Date.now(),
      cam_id: `CAM-${Date.now().toString().slice(-6)}`,
      status: 'offline',
    })
  }
  resetCamForm()
  showToast('Kamera berhasil disimpan')
}

function zoneClicked() {
  camForm.value.zone = camForm.value.zone ? '' : 'Zona Kustom'
}

// ─── Delete camera ────────────────────────────────────────────────────────────
const deleteCamTarget = ref(null)
function confirmDeleteCam(cam) { deleteCamTarget.value = cam }
function deleteCamConfirmed() {
  cameras.value = cameras.value.filter(c => c.id !== deleteCamTarget.value.id)
  if (selectedCam.value?.id === deleteCamTarget.value.id) selectedCam.value = cameras.value[0] ?? null
  deleteCamTarget.value = null
  resetCamForm()
  showToast('Kamera berhasil dihapus')
}

// ─── Global settings ─────────────────────────────────────────────────────────
const globalSettings = ref({
  model:            'yolov8n',
  min_confidence:   0.80,
  frame_skip:       2,
  ocr_engine:       'paddleocr',
  validate_format:  true,
  max_chars:        9,
  email_alert:      false,
  email:            '',
  webhook_enabled:  false,
  webhook_url:      '',
  retention_days:   30,
  auto_purge:       true,
})

function resetGlobal() {
  globalSettings.value = {
    model: 'yolov8n', min_confidence: 0.80, frame_skip: 2,
    ocr_engine: 'paddleocr', validate_format: true, max_chars: 9,
    email_alert: false, email: '', webhook_enabled: false, webhook_url: '',
    retention_days: 30, auto_purge: true,
  }
  showToast('Pengaturan direset ke default')
}

function saveGlobal() { showToast('Pengaturan global disimpan') }

// ─── Storage (simulated) ──────────────────────────────────────────────────────
const storageUsed    = ref('34.8 GB')
const storageTotal   = ref('100 GB')
const storagePercent = ref(34.8)

// ─── Toast ────────────────────────────────────────────────────────────────────
const toastMsg = ref('')
let toastTimer = null
function showToast(msg) {
  toastMsg.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMsg.value = '' }, 3000)
}
</script>

<style scoped>
/* ─── Page ───────────────────────────────────────────────────────────────────── */
.pengaturan-page { display: flex; flex-direction: column; gap: 24px; }

/* ─── Heading ─────────────────────────────────────────────────────────────────── */
.peng-heading { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
.peng-heading__title { font-size: 26px; font-weight: 800; color: var(--primary); letter-spacing: -0.02em; }
.peng-heading__sub { font-size: 13px; color: var(--on-surface-variant); margin-top: 4px; }
.peng-heading__actions { display: flex; gap: 10px; }

.btn-add-cam {
  display: flex; align-items: center; gap: 6px; padding: 8px 18px;
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary); border: none; border-radius: 8px;
  font-size: 12px; font-weight: 700; cursor: pointer;
  transition: opacity .15s, transform .1s;
}
.btn-add-cam:hover  { opacity: .9; }
.btn-add-cam:active { transform: scale(.97); }

/* ─── Bento grid ─────────────────────────────────────────────────────────────── */
.bento-grid {
  display: grid; grid-template-columns: 2fr 1fr; gap: 20px;
}

@media (max-width: 900px) { .bento-grid { grid-template-columns: 1fr; } }

/* ─── Camera section ─────────────────────────────────────────────────────────── */
.cam-section { display: flex; flex-direction: column; gap: 14px; }

/* Status bar */
.cam-status-bar {
  display: flex; align-items: center; justify-content: space-between;
  background: var(--surface-container-low); padding: 12px 16px;
  border-radius: 8px; border: 1px solid rgba(195,199,203,.12);
}
.cam-status-bar__label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--primary); }
.cam-status-bar__badges { display: flex; gap: 8px; }

.badge {
  display: flex; align-items: center; gap: 5px; padding: 3px 10px;
  border-radius: 9999px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
}
.badge--ok    { background: rgba(22,163,74,.1);  color: #16a34a; }
.badge--alert { background: rgba(83,38,0,.1);    color: var(--on-tertiary-container); }

.dot { width: 7px; height: 7px; border-radius: 50%; }
.dot--ok    { background: #22c55e; box-shadow: 0 0 0 2px rgba(34,197,94,.25); }
.dot--alert { background: #f97316; }

/* Camera grid */
.cam-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }

/* Camera card */
.cam-card {
  background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.15); border-radius: 12px;
  padding: 16px; position: relative; overflow: hidden; cursor: pointer;
  box-shadow: 0 4px 12px rgba(15,31,41,.03);
  transition: box-shadow .15s, border-color .15s;
}
.cam-card:hover { box-shadow: 0 8px 24px rgba(15,31,41,.07); }
.cam-card--active { border-color: rgba(15,31,41,.25); box-shadow: 0 0 0 2px rgba(15,31,41,.08); }
.cam-card--offline { opacity: .7; }

/* Left accent bar */
.cam-card__accent { position: absolute; top: 0; left: 0; width: 3px; height: 100%; }
.accent--ok    { background: var(--secondary-container); }
.accent--alert { background: var(--tertiary-container); }

/* Card header */
.cam-card__header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; }
.cam-card__name { font-size: 14px; font-weight: 700; color: var(--primary); letter-spacing: -0.01em; }
.cam-card__id   { font-size: 10px; color: var(--on-surface-variant); font-weight: 500; margin-top: 2px; }
.muted { opacity: .6; }

.btn-more {
  background: none; border: none; cursor: pointer; color: var(--on-surface-variant);
  display: flex; align-items: center; padding: 2px; border-radius: 4px;
  transition: color .12s, background .12s;
}
.btn-more:hover { color: var(--primary); background: var(--surface-container-low); }

/* Preview */
.cam-card__preview {
  aspect-ratio: 16/9; border-radius: 8px; margin-bottom: 12px;
  overflow: hidden; position: relative; background: var(--surface-container-low);
}

.cam-preview-placeholder,
.cam-preview-offline {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 4px;
}

.offline-text { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--on-surface-variant); opacity: .5; }

/* LIVE badge */
.live-badge {
  position: absolute; bottom: 6px; left: 6px;
  display: flex; align-items: center; gap: 4px;
  backdrop-filter: blur(6px);
  background: rgba(245,250,250,.75);
  border: 1px solid rgba(195,199,203,.2);
  border-radius: 4px; padding: 3px 7px;
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--primary);
}

.live-dot {
  width: 5px; height: 5px; border-radius: 50%; background: #22c55e;
  box-shadow: 0 0 0 2px rgba(34,197,94,.3);
  animation: blink 1.2s infinite;
}

@keyframes blink { 0%,100%{ opacity:1; } 50%{ opacity:.3; } }

/* Cam info row */
.cam-card__info { display: flex; justify-content: space-between; }
.cam-info-item { display: flex; flex-direction: column; }
.cam-info-item--right { text-align: right; }
.cam-info-item__label { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--on-surface-variant); }
.cam-info-item__val   { font-size: 13px; font-weight: 600; color: var(--primary); margin-top: 2px; }
.cam-info-item__val--status { font-weight: 700; }
.status--ok    { color: #1a73e8; }
.status--alert { color: var(--on-tertiary-container); }

/* ─── Form panel ─────────────────────────────────────────────────────────────── */
.form-panel {
  background: var(--surface-container-low);
  border: 1px solid rgba(195,199,203,.12); border-radius: 12px; padding: 20px;
  display: flex; flex-direction: column;
}

.form-panel__header { margin-bottom: 20px; }
.form-panel__title  { font-size: 16px; font-weight: 700; color: var(--primary); }
.form-panel__sub    { font-size: 11px; color: var(--on-surface-variant); margin-top: 4px; }

/* Cam form */
.cam-form { display: flex; flex-direction: column; gap: 14px; flex: 1; }

.cam-form__field { display: flex; flex-direction: column; gap: 4px; }
.cam-form__row   { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.cam-form__label {
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--on-surface-variant);
}

.cam-form__input {
  width: 100%; padding: 8px 10px;
  background: var(--surface-container-lowest); border: none;
  border-bottom: 2px solid transparent; border-radius: 5px 5px 0 0;
  font-size: 12px; font-weight: 500; color: var(--primary); font-family: inherit;
  outline: none; transition: border-color .15s;
  box-sizing: border-box;
}
.cam-form__input:focus { border-bottom-color: var(--primary); }
.cam-form__input--mono { font-family: 'Courier New', monospace; font-size: 11px; }

.cam-form__select {
  width: 100%; padding: 8px 10px;
  background: var(--surface-container-lowest); border: none;
  border-bottom: 2px solid transparent; border-radius: 5px 5px 0 0;
  font-size: 12px; font-weight: 500; color: var(--primary); font-family: inherit;
  outline: none; appearance: none; cursor: pointer; transition: border-color .15s;
}
.cam-form__select:focus { border-bottom-color: var(--primary); }

.cam-form__range { width: 100%; accent-color: var(--primary); }

/* Threshold */
.threshold-wrap { display: flex; align-items: center; gap: 10px; }
.threshold-val { font-size: 12px; font-weight: 700; color: var(--primary); min-width: 36px; text-align: right; }

/* Detection zone */
.detection-zone {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  height: 60px; border: 1px solid rgba(195,199,203,.2); border-radius: 6px;
  background: var(--surface-container-lowest); font-size: 12px; font-weight: 500;
  color: var(--on-surface-variant); cursor: pointer; transition: background .12s;
}
.detection-zone:hover { background: var(--surface-variant); }

/* Switches */
.cam-form__switches { display: flex; flex-direction: column; gap: 10px; }

.switch-row {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 10px 12px; background: var(--surface-container-lowest);
  border-radius: 8px; border: 1px solid rgba(195,199,203,.15);
}

.switch-row--inline {
  background: none; border: none; padding: 0;
}

.switch-row__label { font-size: 12px; font-weight: 600; color: var(--primary); }
.switch-row__sub   { font-size: 10px; color: var(--on-surface-variant); margin-top: 2px; }
.settings-label--sm { font-size: 12px; color: var(--on-surface-variant); }

/* Toggle */
.toggle {
  width: 40px; height: 22px; border-radius: 9999px; border: none; cursor: pointer;
  background: var(--surface-container-high); position: relative;
  transition: background .2s; flex-shrink: 0; padding: 0;
}
.toggle--on { background: var(--primary); }

.toggle__knob {
  position: absolute; top: 3px; left: 3px;
  width: 16px; height: 16px; border-radius: 50%; background: white;
  box-shadow: 0 1px 4px rgba(0,0,0,.2); transition: transform .2s;
  display: block;
}
.toggle--on .toggle__knob { transform: translateX(18px); }

.toggle--sm { width: 34px; height: 19px; }
.toggle--sm .toggle__knob { width: 13px; height: 13px; }
.toggle--sm.toggle--on .toggle__knob { transform: translateX(15px); }

/* Form actions */
.cam-form__actions { display: flex; gap: 8px; margin-top: auto; padding-top: 6px; }

.btn-cancel-sm {
  padding: 8px 14px; background: var(--surface-container-highest);
  border: none; border-radius: 7px; font-size: 12px; font-weight: 700;
  color: var(--on-surface-variant); cursor: pointer; transition: background .12s;
}
.btn-cancel-sm:hover { background: var(--surface-variant); }

.btn-save-cam {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 5px;
  padding: 8px 14px;
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary); border: none; border-radius: 7px;
  font-size: 12px; font-weight: 700; cursor: pointer; transition: opacity .15s;
}
.btn-save-cam:hover:not(:disabled)  { opacity: .88; }
.btn-save-cam:disabled { opacity: .45; cursor: not-allowed; }

.btn-danger-sm {
  display: flex; align-items: center; gap: 4px; padding: 8px 12px;
  background: rgba(186,26,26,.1); color: #dc2626; border: none;
  border-radius: 7px; font-size: 12px; font-weight: 700; cursor: pointer; transition: background .12s;
}
.btn-danger-sm:hover { background: rgba(186,26,26,.18); }

/* ─── Global settings ─────────────────────────────────────────────────────────── */
.global-settings { display: flex; flex-direction: column; gap: 16px; }
.global-settings__title { font-size: 16px; font-weight: 700; color: var(--primary); }

.settings-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }

@media (max-width: 900px) { .settings-grid { grid-template-columns: 1fr; } }

/* Settings card */
.settings-card {
  background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.12); border-radius: 12px; padding: 20px;
  display: flex; flex-direction: column; gap: 14px;
  box-shadow: 0 4px 16px rgba(15,31,41,.03);
}

.settings-card__icon-wrap {
  width: 36px; height: 36px; border-radius: 8px;
  background: var(--surface-container-low); display: flex; align-items: center; justify-content: center;
}

.settings-card__title { font-size: 13px; font-weight: 700; color: var(--primary); margin: 0; }

.settings-item { display: flex; flex-direction: column; gap: 6px; }
.settings-label {
  font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--on-surface-variant);
}

.settings-select {
  padding: 8px 10px;
  background: var(--surface-container-low); border: none;
  border-bottom: 2px solid transparent; border-radius: 5px 5px 0 0;
  font-size: 12px; font-weight: 500; color: var(--primary);
  font-family: inherit; outline: none; appearance: none; cursor: pointer;
  transition: border-color .15s;
}
.settings-select:focus { border-bottom-color: var(--primary); }

/* Storage */
.storage-usage { display: flex; flex-direction: column; gap: 6px; }
.storage-usage__header { display: flex; justify-content: space-between; align-items: center; }
.storage-usage__val { font-size: 12px; font-weight: 700; color: var(--primary); }

.storage-track { height: 5px; background: var(--surface-container-high); border-radius: 9999px; overflow: hidden; }
.storage-fill  { height: 100%; background: linear-gradient(90deg, var(--primary), var(--primary-container)); border-radius: 9999px; }
.storage-pct   { font-size: 10px; color: var(--on-surface-variant); }

/* Global actions */
.global-actions { display: flex; gap: 10px; justify-content: flex-end; }

.btn-global-reset {
  display: flex; align-items: center; gap: 6px; padding: 9px 18px;
  background: var(--surface-container-high); border: none; border-radius: 8px;
  font-size: 12px; font-weight: 700; color: var(--on-surface-variant); cursor: pointer;
  transition: background .12s;
}
.btn-global-reset:hover { background: var(--surface-variant); }

.btn-global-save {
  display: flex; align-items: center; gap: 6px; padding: 9px 22px;
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary); border: none; border-radius: 8px;
  font-size: 12px; font-weight: 700; cursor: pointer; transition: opacity .15s;
}
.btn-global-save:hover { opacity: .9; }

/* ─── Delete modal ───────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(15,31,41,.3);
  backdrop-filter: blur(3px); z-index: 300;
  display: flex; align-items: center; justify-content: center; padding: 20px;
}

.modal-box {
  background: var(--surface-container-lowest); border-radius: 12px; padding: 24px;
  max-width: 360px; width: 100%;
  box-shadow: 0 20px 60px rgba(15,31,41,.15);
}
.modal-box__title  { font-size: 15px; font-weight: 700; color: var(--primary); margin-bottom: 8px; }
.modal-box__text   { font-size: 13px; color: var(--on-surface-variant); line-height: 1.6; margin-bottom: 20px; }
.modal-box__actions { display: flex; gap: 10px; justify-content: flex-end; }

.btn-delete {
  display: flex; align-items: center; gap: 5px; padding: 9px 16px;
  background: #dc2626; color: #fff; border: none; border-radius: 7px;
  font-size: 12px; font-weight: 700; cursor: pointer; transition: opacity .15s;
}
.btn-delete:hover { opacity: .88; }

/* Modal transition */
.modal-enter-active, .modal-leave-active { transition: opacity .2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-box { transform: scale(.95); }

/* ─── Toast ──────────────────────────────────────────────────────────────────── */
.toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 8px;
  background: var(--primary); color: var(--on-primary);
  padding: 12px 20px; border-radius: 8px;
  font-size: 12px; font-weight: 700;
  box-shadow: 0 8px 24px rgba(15,31,41,.2); z-index: 400;
  white-space: nowrap;
}

.toast-enter-active, .toast-leave-active { transition: all .2s ease; }
.toast-enter-from { opacity: 0; transform: translateX(-50%) translateY(10px); }
.toast-leave-to   { opacity: 0; transform: translateX(-50%) translateY(10px); }
</style>
