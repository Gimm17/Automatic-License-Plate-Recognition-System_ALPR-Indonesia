<template>
  <MainLayout>
    <div class="upload-page">

      <!-- ══ PAGE HEADER ══════════════════════════════════════════════════ -->
      <div class="upload-page__heading">
        <div>
          <h2 class="upload-page__title">Data Ingestion Node</h2>
          <p class="upload-page__sub">
            Upload gambar atau video statis untuk ekstraksi plat nomor presisi tinggi.
          </p>
        </div>

        <!-- Session ID badge -->
        <div class="session-badge" v-if="sessionId">
          <span class="material-symbols-outlined" style="font-size:14px">tag</span>
          Session: <strong>{{ sessionId }}</strong>
        </div>
      </div>

      <!-- ══ DROP ZONE ════════════════════════════════════════════════════ -->
      <div
        class="drop-zone"
        :class="{
          'drop-zone--over':     isDragging,
          'drop-zone--has-file': fileQueue.length > 0,
        }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <!-- Hidden file input -->
        <input
          ref="fileInputRef"
          type="file"
          multiple
          accept="image/jpeg,image/png,image/bmp,image/webp,video/mp4,video/x-msvideo,video/quicktime"
          class="hidden"
          @change="handleFileInput"
        />

        <div class="drop-zone__icon-wrap" :class="{ 'scale-up': isDragging }">
          <span class="material-symbols-outlined drop-zone__icon">cloud_upload</span>
        </div>

        <h3 class="drop-zone__title">
          {{ isDragging ? 'Lepas file di sini…' : 'Drag & Drop Imagery' }}
        </h3>
        <p class="drop-zone__desc">
          Mendukung JPG, PNG, BMP, WebP (gambar) dan MP4, AVI, MOV (video).
          Multi-vehicle akan di-segmentasi otomatis.
        </p>

        <button class="btn-browse" @click.stop="triggerFileInput">
          <span class="material-symbols-outlined" style="font-size:15px">folder_open</span>
          Browse Local Files
        </button>

        <!-- Format chips -->
        <div class="drop-zone__chips">
          <span class="chip" v-for="fmt in ['JPG','PNG','BMP','WebP','MP4','AVI','MOV']" :key="fmt">
            {{ fmt }}
          </span>
        </div>
      </div>

      <!-- ══ FILE QUEUE ════════════════════════════════════════════════════ -->
      <TransitionGroup
        v-if="fileQueue.length"
        name="queue"
        tag="div"
        class="file-queue"
      >
        <div
          v-for="item in fileQueue"
          :key="item.id"
          class="queue-item"
          :class="{
            'queue-item--done':    item.status === 'done',
            'queue-item--error':   item.status === 'error',
            'queue-item--active':  item.status === 'processing',
          }"
          @click="selectItem(item)"
        >
          <!-- Thumb -->
          <div class="queue-item__thumb">
            <img v-if="item.previewUrl" :src="item.previewUrl" alt="preview" />
            <span v-else class="material-symbols-outlined" style="font-size:20px;color:var(--on-surface-variant)">movie</span>
          </div>

          <!-- Info -->
          <div class="queue-item__info">
            <span class="queue-item__name">{{ item.name }}</span>
            <span class="queue-item__meta">
              {{ item.type === 'video' ? 'Video' : 'Gambar' }} · {{ formatBytes(item.size) }}
            </span>
            <span v-if="item.status === 'error' && item.errorMessage" class="queue-item__error">
              {{ item.errorMessage }}
            </span>

            <!-- Progress bar (visible while processing) -->
            <div v-if="item.status === 'processing'" class="queue-item__bar">
              <div class="queue-item__bar-fill" :style="{ width: item.progress + '%' }"></div>
            </div>
          </div>

          <!-- Status icon -->
          <div class="queue-item__status">
            <span
              v-if="item.status === 'done'"
              class="material-symbols-outlined status-icon status-icon--done"
              style="font-variation-settings:'FILL' 1"
            >check_circle</span>
            <span
              v-else-if="item.status === 'error'"
              class="material-symbols-outlined status-icon status-icon--error"
              style="font-variation-settings:'FILL' 1"
            >error</span>
            <button
              v-if="item.status === 'error'"
              class="status-retry"
              title="Coba proses ulang"
              @click.stop="processItem(item)"
            >
              <span class="material-symbols-outlined" style="font-size:16px">refresh</span>
            </button>
            <span
              v-else-if="item.status === 'processing'"
              class="spinner"
            ></span>
            <span
              v-else
              class="material-symbols-outlined status-icon"
            >schedule</span>
          </div>

          <!-- Remove btn (pending/error only) -->
          <button
            v-if="item.status === 'pending' || item.status === 'error'"
            class="queue-item__remove"
            @click.stop="removeItem(item.id)"
          >
            <span class="material-symbols-outlined" style="font-size:16px">close</span>
          </button>
        </div>
      </TransitionGroup>

      <!-- Process All button -->
      <div v-if="processableItems.length" class="process-bar">
        <span class="process-bar__info">
          {{ processableItems.length }} file perlu proses
        </span>
        <button class="btn-process" @click="processAll">
          <span class="material-symbols-outlined" style="font-size:16px">play_arrow</span>
          Proses Semua
        </button>
      </div>

      <!-- ══ ACTIVE ANALYSIS SESSION ════════════════════════════════════════ -->
      <div v-if="activeItem" class="analysis-section">

        <!-- Section header -->
        <div class="section-header">
          <h3 class="section-header__title">Active Analysis Session</h3>
          <div class="section-header__divider"></div>
          <span class="session-chip">ID: {{ sessionId }}</span>
        </div>

        <!-- Two-column bento grid -->
        <div class="analysis-grid">

          <!-- ── Annotated Image Viewer (col-span 2) ─────────────────── -->
          <div class="viewer-card">
            <!-- Top action bar -->
            <div class="viewer-card__topbar">
              <div class="viewer-card__badge">
                <span class="material-symbols-outlined" style="font-size:14px">center_focus_strong</span>
                Auto-Focus Mode
              </div>
              <button class="viewer-card__fs" @click="toggleFullscreen">
                <span class="material-symbols-outlined" style="font-size:14px">
                  {{ isFullscreen ? 'fullscreen_exit' : 'fullscreen' }}
                </span>
              </button>
            </div>

            <!-- Image container with BBox overlays -->
            <div class="viewer-card__canvas" ref="imageCanvasRef">
              <img
                v-if="activeItem.displayUrl"
                :src="activeItem.displayUrl"
                alt="Source Vehicle"
                class="viewer-card__img"
                ref="imageRef"
              />

              <!-- Placeholder if no image (video) -->
              <div v-else class="viewer-card__placeholder">
                <span class="material-symbols-outlined" style="font-size:48px;opacity:.2">movie</span>
                <p style="opacity:.4;font-size:12px;margin-top:8px">
                  Memuat preview video…
                </p>
              </div>

              <!-- BBox annotations from backend bbox_norm -->
              <template v-if="activeItem.result">
                <div
                  v-for="(box, bi) in activeItem.result.boxes"
                  :key="bi"
                  class="bbox"
                  :style="{
                    left:   box.x + '%',
                    top:    box.y + '%',
                    width:  box.w + '%',
                    height: box.h + '%',
                  }"
                >
                  <!-- Corner handles -->
                  <div class="bbox__corner bbox__corner--tl"></div>
                  <div class="bbox__corner bbox__corner--tr"></div>
                  <div class="bbox__corner bbox__corner--bl"></div>
                  <div class="bbox__corner bbox__corner--br"></div>

                  <!-- Hover tooltip -->
                  <div class="bbox__label">{{ box.plate }}</div>
                </div>
              </template>

              <!-- Processing overlay -->
              <div v-if="activeItem.status === 'processing'" class="viewer-card__overlay">
                <div class="processing-pulse">
                  <span class="material-symbols-outlined" style="font-size:32px;color:var(--primary)">radar</span>
                  <p>Analyzing…</p>
                  <div class="processing-bar">
                    <div class="processing-bar__fill" :style="{ width: activeItem.progress + '%' }"></div>
                  </div>
                  <span class="processing-pct">{{ activeItem.progress }}%</span>
                </div>
              </div>
            </div>

            <!-- File name footer -->
            <div class="viewer-card__footer">
              <span class="material-symbols-outlined" style="font-size:14px;color:var(--on-surface-variant)">image</span>
              <span class="viewer-card__fname">{{ activeItem.name }}</span>
              <span class="viewer-card__fsize">{{ formatBytes(activeItem.size) }}</span>
            </div>
          </div>

          <!-- ── Extraction Data Panel ────────────────────────────────── -->
          <div class="extraction-panel">

            <!-- Header -->
            <div class="extraction-panel__header">
              <h4 class="extraction-panel__title">Extraction Data</h4>
              <span
                v-if="activeItem.result"
                class="status-chip"
                :class="statusChipClass(activeItem.result.status)"
              >
                <span
                  v-if="activeItem.result.status === 'watchlist'"
                  class="material-symbols-outlined"
                  style="font-size:11px;font-variation-settings:'FILL' 1"
                >flag</span>
                {{ statusLabel(activeItem.result.status) }}
              </span>
            </div>

            <!-- No result yet -->
            <div v-if="!activeItem.result && activeItem.status !== 'processing'" class="extraction-panel__empty">
              <span class="material-symbols-outlined" style="font-size:28px;opacity:.2">analytics</span>
              <p>Belum ada hasil. Proses file terlebih dahulu.</p>
            </div>

            <!-- Processing -->
            <div v-else-if="activeItem.status === 'processing'" class="extraction-panel__loading">
              <div v-for="i in 4" :key="i" class="skel-line"></div>
            </div>

            <!-- Result -->
            <template v-else-if="activeItem.result">
              <!-- Primary plate display -->
              <div class="plate-display">
                <p class="plate-display__label">Detected Plate Sequence</p>
                <div class="plate-display__box"
                  :class="{ 'plate-display__box--alert': activeItem.result.status === 'watchlist' }"
                >
                  <span class="plate-display__text">{{ activeItem.result.plate }}</span>
                </div>

                <!-- Confidence meter -->
                <div class="conf-header">
                  <span class="conf-label">Algorithm Confidence</span>
                  <span class="conf-value" :class="confClass(activeItem.result.confidence)">
                    {{ (activeItem.result.confidence * 100).toFixed(1) }}%
                  </span>
                </div>
                <div class="conf-track">
                  <div
                    class="conf-fill"
                    :style="{ width: (activeItem.result.confidence * 100) + '%' }"
                    :class="confClass(activeItem.result.confidence)"
                  ></div>
                </div>
              </div>

              <!-- Metadata list -->
              <div class="meta-list">
                <!-- Video batch summary -->
                <template v-if="activeItem.result.is_video">
                  <div class="meta-item">
                    <span class="meta-item__label">Mode Deteksi</span>
                    <span class="meta-item__val" style="color:var(--tertiary)">🎬 Video Batch</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-item__label">Total Plat Terdeteksi</span>
                    <span class="meta-item__val">{{ activeItem.result.total_found }}</span>
                  </div>
                  <div class="meta-item">
                    <span class="meta-item__label">Frame Diproses</span>
                    <span class="meta-item__val">{{ activeItem.result.frames_processed }}</span>
                  </div>
                  <div class="meta-item" v-if="activeItem.result.unique_plates.length">
                    <span class="meta-item__label">Plat Unik Ditemukan</span>
                    <span class="meta-item__val meta-item__val--mono">{{ activeItem.result.unique_plates.join(', ') }}</span>
                  </div>
                </template>
                <div class="meta-item">
                  <span class="meta-item__label">Region Code Mapping</span>
                  <span class="meta-item__val">{{ activeItem.result.region }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-item__label">Vehicle Classification</span>
                  <span class="meta-item__val">{{ activeItem.result.vehicle_type }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-item__label">Capture Timestamp</span>
                  <span class="meta-item__val meta-item__val--mono">{{ activeItem.result.timestamp }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-item__label">Source File</span>
                  <span class="meta-item__val meta-item__val--mono">{{ activeItem.name }}</span>
                </div>
                <div class="meta-item" v-if="sessionId">
                  <span class="meta-item__label">Session ID</span>
                  <span class="meta-item__val meta-item__val--mono">{{ sessionId }}</span>
                </div>
              </div>

              <!-- Action buttons -->
              <div class="extraction-panel__actions">
                <button class="btn-commit" @click="$router.push('/riwayat')" title="Lihat hasil di Riwayat Deteksi">
                  <span class="material-symbols-outlined" style="font-size:15px">check</span>
                  Lihat Riwayat
                </button>
                <button class="btn-edit" @click="$router.push('/riwayat')" title="Lihat & edit di halaman Riwayat">
                  <span class="material-symbols-outlined" style="font-size:15px">edit</span>
                </button>
                <button class="btn-edit" @click="$router.push('/kendaraan')" title="Kelola watchlist di halaman Kendaraan">
                  <span class="material-symbols-outlined" style="font-size:15px">flag</span>
                </button>
              </div>
            </template>
          </div>
        </div>

        <!-- ── Batch Results List ──────────────────────────────────────── -->
        <div class="batch-results" v-if="doneItems.length > 1">
          <div class="section-header" style="margin-bottom:12px">
            <h3 class="section-header__title" style="font-size:14px">Batch Results</h3>
            <div class="section-header__divider"></div>
            <span class="session-chip">{{ doneItems.length }} selesai</span>
          </div>

          <div class="results-grid">
            <div
              v-for="item in doneItems"
              :key="item.id"
              class="result-thumb"
              :class="{ 'result-thumb--active': activeItem?.id === item.id }"
              @click="selectItem(item)"
            >
              <img v-if="item.displayUrl" :src="item.displayUrl" alt="thumb" class="result-thumb__img" />
              <div class="result-thumb__overlay">
                <span class="result-thumb__plate">{{ item.result?.plate || '—' }}</span>
                <span
                  class="status-dot"
                  :class="{
                    'status-dot--ok':    item.result?.status === 'valid',
                    'status-dot--alert': item.result?.status === 'watchlist',
                    'status-dot--muted': item.result?.status === 'invalid',
                  }"
                ></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty analysis placeholder -->
      <div v-else-if="!fileQueue.length" class="empty-hint">
        <span class="material-symbols-outlined" style="font-size:36px;opacity:.15">analytics</span>
        <p>Unggah file untuk memulai sesi analisis</p>
      </div>

    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'
import { useDetectionStore } from '@/stores/detection'
import { useStatsStore } from '@/stores/stats'
import { toApiAssetUrl } from '@/lib/api'

const detectionStore = useDetectionStore()
const statsStore = useStatsStore()

// ── Refs ──────────────────────────────────────────────────────────────────────
const fileInputRef   = ref(null)
const imageCanvasRef = ref(null)
const imageRef       = ref(null)
const isDragging     = ref(false)
const isFullscreen   = ref(false)
const fileQueue      = ref([])
const activeItemId   = ref(null)
const sessionId      = ref(null)

// ── Computed ──────────────────────────────────────────────────────────────────
const activeItem = computed(() =>
  fileQueue.value.find(f => f.id === activeItemId.value) ?? null
)

const doneItems = computed(() =>
  fileQueue.value.filter(f => f.status === 'done')
)

const processableItems = computed(() =>
  fileQueue.value.filter(f => f.status === 'pending' || f.status === 'error')
)

// ── File handling ──────────────────────────────────────────────────────────────
function triggerFileInput() { fileInputRef.value?.click() }

function handleDrop(e) {
  isDragging.value = false
  addFiles([...e.dataTransfer.files])
}

function handleFileInput(e) {
  addFiles([...e.target.files])
  e.target.value = ''
}

function addFiles(files) {
  const newItems = files.map(file => {
    const isVideo = file.type.startsWith('video/')
    const id = Math.random().toString(36).slice(2)
    const item = {
      id,
      file,
      name:       file.name,
      size:       file.size,
      type:       isVideo ? 'video' : 'image',
      status:     'pending',   // pending | processing | done | error
      progress:   0,
      previewUrl: null,
      displayUrl: null,
      result:     null,
      response:   null,
      errorMessage: null,
    }

    // Generate preview for images
    if (!isVideo) {
      const reader = new FileReader()
      reader.onload = e => {
        item.previewUrl = e.target.result
        item.displayUrl = e.target.result
      }
      reader.readAsDataURL(file)
    } else {
      // Generate video thumbnail from first frame
      const videoEl = document.createElement('video')
      videoEl.preload = 'metadata'
      videoEl.muted = true
      videoEl.playsInline = true
      const objUrl = URL.createObjectURL(file)
      videoEl.src = objUrl
      videoEl.onloadeddata = () => {
        videoEl.currentTime = 0.5
      }
      videoEl.onseeked = () => {
        try {
          const canvas = document.createElement('canvas')
          canvas.width = videoEl.videoWidth
          canvas.height = videoEl.videoHeight
          canvas.getContext('2d').drawImage(videoEl, 0, 0)
          item.previewUrl = canvas.toDataURL('image/jpeg', 0.7)
          item.displayUrl = item.previewUrl
        } catch (_) { /* cross-origin or codec issue */ }
        URL.revokeObjectURL(objUrl)
      }
      videoEl.onerror = () => URL.revokeObjectURL(objUrl)
    }

    return item
  })

  fileQueue.value.push(...newItems)

  // Generate session ID first time
  if (!sessionId.value) {
    sessionId.value = 'REQ-' + Math.floor(Math.random() * 9000 + 1000)
  }

  // Auto-select first item that isn't done yet
  if (!activeItemId.value && newItems.length) {
    activeItemId.value = newItems[0].id
  }
}

function removeItem(id) {
  fileQueue.value = fileQueue.value.filter(f => f.id !== id)
  if (activeItemId.value === id) activeItemId.value = null
}

function selectItem(item) { activeItemId.value = item.id }

// API-backed upload processing.
async function processAll() {
  for (const item of processableItems.value) {
    await processItem(item)
  }
}

async function processItem(item) {
  item.status   = 'processing'
  item.progress = 0
  item.errorMessage = null
  item.result = null
  item.response = null
  activeItemId.value = item.id

  const progressTimer = startProgress(item)
  try {
    const result = await detectionStore.uploadFile(item.file)
    clearInterval(progressTimer)
    item.progress = 100
    item.response = result
    item.result = mapUploadResult(result)
    item.displayUrl = toApiAssetUrl(result.annotated_image_url) || item.previewUrl
    item.status = 'done'
    await Promise.allSettled([
      detectionStore.fetchDetections?.(1),
      statsStore.fetchAll?.(),
    ])
  } catch (err) {
    clearInterval(progressTimer)
    item.progress = 100
    item.status = 'error'
    item.errorMessage = err.message || 'Upload gagal'
  }
}

function startProgress(item) {
  return setInterval(() => {
    if (item.progress < 90) {
      item.progress += Math.max(3, Math.round((90 - item.progress) * 0.18))
    }
  }, 160)
}

// Map backend upload response into the local viewer state.
function mapUploadResult(result) {
  const detections = result?.detections || []
  const first = detections[0] || null
  return {
    plate: first?.plate_text || 'Tidak terdeteksi',
    status: first?.status || (detections.length ? 'invalid' : 'ocr_failed'),
    confidence: first?.confidence ?? 0,
    region: first?.region || '-',
    vehicle_type: first?.vehicle_type || '-',
    timestamp: new Date().toISOString().replace('T', ' ').slice(0, 23),
    total_found: result?.total_found ?? detections.length,
    unique_plates: result?.unique_plates ?? [],
    frames_processed: result?.frames_processed ?? 0,
    is_video: !!(result?.frames_processed),
    boxes: detections
      .filter(d => Array.isArray(d.bbox_norm) && d.bbox_norm.length === 4)
      .map(d => {
        const [x1, y1, x2, y2] = d.bbox_norm
        return {
          plate: d.plate_text || 'UNKNOWN',
          x: x1 * 100,
          y: y1 * 100,
          w: Math.max(0, (x2 - x1) * 100),
          h: Math.max(0, (y2 - y1) * 100),
        }
      }),
  }
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  if (isFullscreen.value) {
    imageCanvasRef.value?.requestFullscreen?.()
  } else {
    document.exitFullscreen?.()
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024)       return bytes + ' B'
  if (bytes < 1048576)    return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function confClass(val) {
  if (val >= 0.95) return 'conf--high'
  if (val >= 0.85) return 'conf--mid'
  return 'conf--low'
}

function statusLabel(status) {
  return { valid: 'Authorized', watchlist: 'Flagged', invalid: 'Unregistered', ocr_failed: 'OCR Failed' }[status] ?? status
}

function statusChipClass(status) {
  return {
    valid:      'chip--ok',
    watchlist:  'chip--alert',
    invalid:    'chip--muted',
    ocr_failed: 'chip--error',
  }[status] ?? ''
}
</script>

<style scoped>
/* ─── Page ───────────────────────────────────────────────────────────────────── */
.upload-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ─── Heading ──────────────────────────────────────────────────────────────── */
.upload-page__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.upload-page__title {
  font-size: 26px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.02em;
}

.upload-page__sub {
  font-size: 13px;
  color: var(--on-surface-variant);
  margin-top: 4px;
}

.session-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: var(--on-surface-variant);
  background: var(--surface-container-low);
  border: 1px solid rgba(195,199,203,.2);
  padding: 6px 12px;
  border-radius: 6px;
  letter-spacing: 0.04em;
}

/* ─── Drop zone ──────────────────────────────────────────────────────────────── */
.drop-zone {
  position: relative;
  overflow: hidden;
  background-color: var(--surface-container-lowest);
  border-radius: 16px;
  border: 2px dashed rgba(195,199,203,.35);
  padding: 56px 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  cursor: pointer;
  transition: border-color .2s ease, background-color .2s ease;
}

.drop-zone:hover,
.drop-zone--over {
  border-color: rgba(15,31,41,.35);
  background-color: var(--surface-container-low);
}

.drop-zone--has-file { padding: 32px 40px; }

/* Icon */
.drop-zone__icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--surface-container-low);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .25s ease;
}

.drop-zone--over .drop-zone__icon-wrap,
.scale-up { transform: scale(1.1); }

.drop-zone__icon {
  font-size: 32px;
  color: var(--primary);
  font-variation-settings: 'wght' 300;
}

.drop-zone__title {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -0.01em;
}

.drop-zone__desc {
  font-size: 13px;
  color: var(--on-surface-variant);
  text-align: center;
  max-width: 420px;
  line-height: 1.5;
}

/* Browse button */
.btn-browse {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary);
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(15,31,41,.12);
  transition: opacity .15s, transform .1s;
  margin-top: 4px;
}

.btn-browse:hover  { opacity: .9; }
.btn-browse:active { transform: scale(.97); }

/* Format chips */
.drop-zone__chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
}

.chip {
  padding: 3px 8px;
  background: var(--surface-container-low);
  border: 1px solid rgba(195,199,203,.25);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  color: var(--on-surface-variant);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

/* ─── File Queue ─────────────────────────────────────────────────────────────── */
.file-queue {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.15);
  border-radius: 10px;
  cursor: pointer;
  transition: background-color .12s, border-color .12s;
  position: relative;
}

.queue-item:hover { background: var(--surface-container-low); }

.queue-item--active  { border-color: rgba(15,31,41,.2); }
.queue-item--done    { border-left: 3px solid #16a34a; }
.queue-item--error   { border-left: 3px solid #dc2626; }

/* Thumb */
.queue-item__thumb {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  overflow: hidden;
  background: var(--surface-container-low);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.queue-item__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Info */
.queue-item__info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.queue-item__name {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-item__meta {
  font-size: 11px;
  color: var(--on-surface-variant);
}

.queue-item__error {
  font-size: 11px;
  color: #dc2626;
  line-height: 1.35;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Progress bar */
.queue-item__bar {
  height: 3px;
  background: var(--surface-container-high);
  border-radius: 9999px;
  overflow: hidden;
  margin-top: 2px;
}

.queue-item__bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--primary-container));
  border-radius: 9999px;
  transition: width .2s ease;
}

/* Status icons */
.queue-item__status {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-icon { font-size: 20px; }
.status-icon--done  { color: #16a34a; }
.status-icon--error { color: #dc2626; }

.status-retry {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: var(--surface-container-high);
  color: var(--primary);
  cursor: pointer;
}

.status-retry:hover { background: var(--surface-variant); }

/* Spinner */
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(15,31,41,.15);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin .7s linear infinite;
  display: block;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Remove button */
.queue-item__remove {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--on-surface-variant);
  opacity: 0;
  padding: 4px;
  border-radius: 4px;
  transition: color .12s, opacity .12s;
}

.queue-item:hover .queue-item__remove { opacity: 1; }
.queue-item__remove:hover { color: #dc2626; }

/* Queue animation */
.queue-enter-active,
.queue-leave-active { transition: all .2s ease; }

.queue-enter-from { opacity: 0; transform: translateY(-8px); }
.queue-leave-to   { opacity: 0; transform: translateX(-16px); }

/* ─── Process bar ─────────────────────────────────────────────────────────────── */
.process-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: var(--surface-container-low);
  border: 1px solid rgba(195,199,203,.15);
  border-radius: 10px;
}

.process-bar__info {
  font-size: 12px;
  font-weight: 600;
  color: var(--on-surface-variant);
}

.btn-process {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary);
  border: none;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 0.02em;
  transition: opacity .15s, transform .1s;
}

.btn-process:hover  { opacity: .9; }
.btn-process:active { transform: scale(.97); }

/* ─── Analysis section ────────────────────────────────────────────────────────── */
.analysis-section { display: flex; flex-direction: column; gap: 16px; }

/* Section header */
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header__title {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  white-space: nowrap;
}

.section-header__divider {
  flex: 1;
  height: 1px;
  background: rgba(195,199,203,.2);
}

.session-chip {
  font-size: 10px;
  font-weight: 700;
  color: var(--on-surface-variant);
  background: var(--surface-container-low);
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
}

/* ─── Bento grid ────────────────────────────────────────────────────────────── */
.analysis-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

@media (max-width: 900px) {
  .analysis-grid { grid-template-columns: 1fr; }
}

/* ─── Annotated image viewer ────────────────────────────────────────────────── */
.viewer-card {
  background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.12);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 30px rgba(15,31,41,.04);
  display: flex;
  flex-direction: column;
  position: relative;
  min-height: 380px;
}

/* Top bar (floating) */
.viewer-card__topbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  pointer-events: none;
}

.viewer-card__badge {
  display: flex;
  align-items: center;
  gap: 5px;
  backdrop-filter: blur(8px);
  background: rgba(245,250,250,.75);
  border: 1px solid rgba(195,199,203,.25);
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 10px;
  font-weight: 700;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  pointer-events: auto;
  box-shadow: 0 4px 16px rgba(15,31,41,.06);
}

.viewer-card__fs {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(245,250,250,.75);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(195,199,203,.25);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--primary);
  box-shadow: 0 4px 16px rgba(15,31,41,.06);
  pointer-events: auto;
  transition: background .12s;
}

.viewer-card__fs:hover { background: rgba(222,227,227,.9); }

/* Canvas */
.viewer-card__canvas {
  flex: 1;
  position: relative;
  background: var(--surface-container-low);
  overflow: hidden;
  min-height: 320px;
}

.viewer-card__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.viewer-card__placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* BBox */
.bbox {
  position: absolute;
  border: 2.5px solid var(--tertiary-fixed-dim);
  background: rgba(255,183,134,.12);
  border-radius: 2px;
  cursor: crosshair;
}

.bbox__corner {
  position: absolute;
  width: 8px;
  height: 8px;
  background: white;
  border: 1.5px solid var(--primary);
}

.bbox__corner--tl { top: -4px; left: -4px; }
.bbox__corner--tr { top: -4px; right: -4px; }
.bbox__corner--bl { bottom: -4px; left: -4px; }
.bbox__corner--br { bottom: -4px; right: -4px; }

.bbox__label {
  position: absolute;
  top: -26px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  background: var(--primary);
  color: var(--on-primary);
  font-size: 9px;
  font-weight: 700;
  padding: 3px 7px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0;
  transition: opacity .15s;
  pointer-events: none;
}

.bbox:hover .bbox__label { opacity: 1; }

/* Processing overlay */
.viewer-card__overlay {
  position: absolute;
  inset: 0;
  background: rgba(245,250,250,.8);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.processing-pulse {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

@keyframes pulse { 0%,100%{ opacity:1; } 50%{ opacity:.5; } }

.processing-pulse span { animation: pulse 1.2s infinite; }

.processing-pulse p {
  font-size: 12px;
  font-weight: 600;
  color: var(--on-surface-variant);
}

.processing-bar {
  width: 140px;
  height: 4px;
  background: var(--surface-container-high);
  border-radius: 9999px;
  overflow: hidden;
}

.processing-bar__fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--primary-container));
  border-radius: 9999px;
  transition: width .2s ease;
}

.processing-pct {
  font-size: 11px;
  font-weight: 700;
  color: var(--primary);
}

/* Footer */
.viewer-card__footer {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-top: 1px solid rgba(195,199,203,.1);
  background: var(--surface-container-lowest);
}

.viewer-card__fname {
  font-size: 11px;
  font-weight: 600;
  color: var(--primary);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.viewer-card__fsize {
  font-size: 10px;
  color: var(--on-surface-variant);
  flex-shrink: 0;
}

/* ─── Extraction panel ──────────────────────────────────────────────────────── */
.extraction-panel {
  background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.12);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 8px 30px rgba(15,31,41,.04);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.extraction-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.extraction-panel__title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--on-surface-variant);
}

/* Status chip */
.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  border-radius: 9999px;
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.chip--ok    { background: var(--secondary-container); color: var(--on-secondary-container); }
.chip--alert { background: rgba(83,38,0,.12);          color: var(--on-tertiary-container); }
.chip--muted { background: var(--surface-container-high); color: var(--on-surface); }
.chip--error { background: var(--error-container);     color: var(--on-error-container); }

/* Empty state */
.extraction-panel__empty,
.extraction-panel__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 32px 0;
  color: var(--on-surface-variant);
  font-size: 12px;
  text-align: center;
}

/* Skeleton lines */
.skel-line {
  width: 100%;
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(90deg,
    var(--surface-container-low) 25%,
    var(--surface-container-high) 50%,
    var(--surface-container-low) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* Plate display */
.plate-display { display: flex; flex-direction: column; gap: 8px; }

.plate-display__label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--on-surface-variant);
}

.plate-display__box {
  width: 100%;
  border: 2px solid var(--primary);
  background: var(--surface-container-low);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.plate-display__box--alert { border-color: var(--on-tertiary-container); }

.plate-display__text {
  font-size: 26px;
  font-weight: 900;
  color: var(--primary);
  letter-spacing: -0.01em;
  font-family: 'Courier New', monospace;
}

/* Confidence */
.conf-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.conf-label { font-size: 11px; color: var(--on-surface-variant); font-weight: 500; }
.conf-value { font-size: 12px; font-weight: 700; }

.conf--high { color: #16a34a; }
.conf--mid  { color: var(--primary); }
.conf--low  { color: #dc2626; }

.conf-track {
  height: 5px;
  background: var(--surface-container-low);
  border-radius: 9999px;
  overflow: hidden;
}

.conf-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width .5s ease;
}

.conf-fill.conf--high { background: #16a34a; }
.conf-fill.conf--mid  { background: var(--primary); }
.conf-fill.conf--low  { background: #dc2626; }

/* Metadata list */
.meta-list { display: flex; flex-direction: column; gap: 2px; }

.meta-item {
  display: flex;
  flex-direction: column;
  padding: 9px 0;
  border-bottom: 1px solid rgba(195,199,203,.08);
}

.meta-item:last-child { border-bottom: none; }

.meta-item__label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--on-surface-variant);
  margin-bottom: 2px;
}

.meta-item__val {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
}

.meta-item__val--mono {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

/* Action buttons */
.extraction-panel__actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
}

.btn-commit {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 10px 14px;
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary);
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity .15s, transform .1s;
}

.btn-commit:hover  { opacity: .88; }
.btn-commit:active { transform: scale(.97); }

.btn-edit {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-container-low);
  border: 1px solid rgba(195,199,203,.2);
  border-radius: 8px;
  color: var(--on-surface-variant);
  cursor: pointer;
  transition: background .12s, color .12s;
}

.btn-edit:hover { background: var(--surface-container-high); color: var(--primary); }
.btn-edit:disabled {
  opacity: .55;
  cursor: not-allowed;
}
.btn-edit:disabled:hover {
  background: var(--surface-container-low);
  color: var(--on-surface-variant);
}


/* ─── Batch results thumbnails ──────────────────────────────────────────────── */
.batch-results { display: flex; flex-direction: column; gap: 12px; }

.results-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.result-thumb {
  width: 88px;
  height: 66px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  position: relative;
  border: 2px solid transparent;
  transition: border-color .15s, transform .12s;
  flex-shrink: 0;
}

.result-thumb:hover { transform: scale(1.04); }

.result-thumb--active {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(15,31,41,.15);
}

.result-thumb__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.result-thumb__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(15,31,41,.7) 0%, transparent 60%);
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 4px 6px;
}

.result-thumb__plate {
  font-size: 9px;
  font-weight: 800;
  color: white;
  font-family: 'Courier New', monospace;
  letter-spacing: 0.04em;
  line-height: 1;
}

/* Status dot */
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot--ok    { background: #22c55e; }
.status-dot--alert { background: #f97316; }
.status-dot--muted { background: #9ca3af; }

/* ─── Empty hint ─────────────────────────────────────────────────────────────── */
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 40px;
  color: var(--on-surface-variant);
  font-size: 13px;
}

.hidden { display: none; }
</style>
