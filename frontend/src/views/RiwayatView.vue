<template>
  <MainLayout>
    <div class="riwayat">

      <!-- ══════════════════════════════════════════════════════════
           HEADING ROW
           ══════════════════════════════════════════════════════════ -->
      <div class="riwayat__heading">
        <div>
          <h2 class="riwayat__title">Riwayat Deteksi</h2>
          <p class="riwayat__sub">
            Log komprehensif kendaraan yang teridentifikasi di seluruh jaringan kamera.
          </p>
        </div>

        <!-- Mini stat cards + export -->
        <div class="riwayat__header-right">
          <div class="riwayat__mini-stats">
            <div class="mini-stat">
              <span class="mini-stat__label">Total Hari Ini</span>
              <span class="mini-stat__value">{{ totalToday.toLocaleString('id-ID') }}</span>
            </div>
            <div class="mini-stat mini-stat--alert">
              <span class="mini-stat__label">Flagged</span>
              <span class="mini-stat__value mini-stat__value--alert">{{ totalFlagged }}</span>
            </div>
          </div>

          <!-- Export buttons -->
          <div class="export-group">
            <button class="btn-export" @click="exportCSV" title="Export CSV">
              <span class="material-symbols-outlined" style="font-size:16px">table_view</span>
              CSV
            </button>
            <button class="btn-export" @click="exportJSON" title="Export JSON">
              <span class="material-symbols-outlined" style="font-size:16px">data_object</span>
              JSON
            </button>
          </div>
        </div>
      </div>

      <!-- ══════════════════════════════════════════════════════════
           FILTER BAR
           ══════════════════════════════════════════════════════════ -->
      <section class="filter-bar">
        <!-- Search -->
        <div class="filter-field filter-field--grow">
          <span class="material-symbols-outlined filter-field__icon">search</span>
          <input
            v-model="filters.search"
            class="filter-input"
            type="text"
            placeholder="Cari Plat Nomor..."
            @input="debouncedFilter"
          />
        </div>

        <!-- Date range -->
        <div class="filter-field">
          <span class="material-symbols-outlined filter-field__icon">calendar_today</span>
          <select v-model="filters.dateRange" class="filter-select" @change="applyFilters">
            <option value="today">Hari Ini</option>
            <option value="7d">7 Hari Terakhir</option>
            <option value="30d">30 Hari Terakhir</option>
            <option value="all">Semua</option>
          </select>
          <span class="material-symbols-outlined filter-field__chevron">expand_more</span>
        </div>

        <!-- Camera filter -->
        <div class="filter-field">
          <span class="material-symbols-outlined filter-field__icon">videocam</span>
          <select v-model="filters.camera" class="filter-select" @change="applyFilters">
            <option value="">Semua Kamera ({{ cameras.length }})</option>
            <option v-for="c in cameras" :key="c.id" :value="c.id">
              {{ c.label }}
            </option>
          </select>
          <span class="material-symbols-outlined filter-field__chevron">expand_more</span>
        </div>

        <!-- Status filter -->
        <div class="filter-field">
          <span class="material-symbols-outlined filter-field__icon">filter_list</span>
          <select v-model="filters.status" class="filter-select" @change="applyFilters">
            <option value="">Semua Status</option>
            <option value="valid">Authorized</option>
            <option value="watchlist">Flagged</option>
            <option value="invalid">Unregistered</option>
            <option value="ocr_failed">OCR Failed</option>
          </select>
          <span class="material-symbols-outlined filter-field__chevron">expand_more</span>
        </div>

        <!-- Reset -->
        <button class="btn-reset" @click="resetFilters">
          <span class="material-symbols-outlined" style="font-size:16px">restart_alt</span>
          Reset
        </button>
      </section>

      <!-- ══════════════════════════════════════════════════════════
           DATA TABLE
           ══════════════════════════════════════════════════════════ -->
      <div class="table-card">
        <div class="table-wrap">
          <table class="riwayat-table">
            <thead>
              <tr>
                <th class="col-no">No</th>
                <th class="col-plat sortable" @click="toggleSort('plate_text')">
                  Plat
                  <span class="material-symbols-outlined sort-icon">
                    {{ sortIcon('plate_text') }}
                  </span>
                </th>
                <th class="col-waktu sortable" @click="toggleSort('detected_at')">
                  Waktu
                  <span class="material-symbols-outlined sort-icon">
                    {{ sortIcon('detected_at') }}
                  </span>
                </th>
                <th class="col-kamera">Kamera</th>
                <th class="col-wilayah">Wilayah</th>
                <th class="col-conf sortable" @click="toggleSort('confidence')">
                  Confidence
                  <span class="material-symbols-outlined sort-icon">
                    {{ sortIcon('confidence') }}
                  </span>
                </th>
                <th class="col-status">Status</th>
                <th class="col-aksi">Aksi</th>
              </tr>
            </thead>

            <tbody>
              <!-- Skeleton rows while loading -->
              <template v-if="loading">
                <tr v-for="i in perPage" :key="`sk-${i}`" class="skeleton-row">
                  <td><div class="skel skel--xs"></div></td>
                  <td><div class="skel skel--md"></div></td>
                  <td><div class="skel skel--sm"></div></td>
                  <td><div class="skel skel--md"></div></td>
                  <td><div class="skel skel--sm"></div></td>
                  <td><div class="skel skel--sm"></div></td>
                  <td><div class="skel skel--xs"></div></td>
                  <td></td>
                </tr>
              </template>

              <!-- Empty state -->
              <tr v-else-if="!pagedRows.length">
                <td colspan="8" class="empty-cell">
                  <div class="empty-state">
                    <span class="material-symbols-outlined" style="font-size:32px;opacity:.25">
                      search_off
                    </span>
                    <p>Tidak ada hasil yang sesuai filter</p>
                  </div>
                </td>
              </tr>

              <!-- Rows -->
              <tr
                v-for="(row, idx) in pagedRows"
                :key="row.id"
                class="data-row"
                :class="{
                  'data-row--alt':      idx % 2 === 1,
                  'data-row--alert':    row.status === 'watchlist',
                  'data-row--muted':    row.status === 'ocr_failed',
                }"
                @click="openDetail(row)"
              >
                <!-- No -->
                <td class="td-no">{{ (currentPage - 1) * perPage + idx + 1 }}</td>

                <!-- Plate badge -->
                <td class="td-plat">
                  <div
                    class="plate-badge"
                    :class="{ 'plate-badge--alert': row.status === 'watchlist' }"
                  >
                    {{ row.plate_text || '—' }}
                  </div>
                </td>

                <!-- Waktu -->
                <td class="td-waktu">
                  <div class="time-group">
                    <span class="time-group__time">{{ formatTime(row.detected_at) }}</span>
                    <span class="time-group__date">{{ formatDate(row.detected_at) }}</span>
                  </div>
                </td>

                <!-- Kamera -->
                <td class="td-kamera">
                  <span class="material-symbols-outlined cam-icon">videocam</span>
                  {{ row.camera_label }}
                </td>

                <!-- Wilayah -->
                <td class="td-wilayah">{{ row.region || '—' }}</td>

                <!-- Confidence -->
                <td class="td-conf">
                  <div class="conf-wrap">
                    <div class="conf-bar">
                      <div
                        class="conf-bar__fill"
                        :style="{ width: confPct(row.confidence) + '%' }"
                        :class="confBarClass(row.confidence)"
                      ></div>
                    </div>
                    <span
                      class="conf-val"
                      :class="confBarClass(row.confidence)"
                    >
                      {{ row.confidence != null ? (row.confidence * 100).toFixed(1) + '%' : '—' }}
                    </span>
                  </div>
                </td>

                <!-- Status badge -->
                <td class="td-status">
                  <span class="status-badge" :class="statusBadgeClass(row.status)">
                    <span
                      v-if="row.status === 'watchlist'"
                      class="material-symbols-outlined"
                      style="font-size:11px;font-variation-settings:'FILL' 1"
                    >warning</span>
                    {{ statusLabel(row.status) }}
                  </span>
                </td>

                <!-- Aksi -->
                <td class="td-aksi">
                  <button
                    class="btn-detail"
                    @click.stop="openDetail(row)"
                    title="Lihat Detail"
                  >
                    <span class="material-symbols-outlined" style="font-size:18px">open_in_new</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- ── Pagination footer ────────────────────────────────────── -->
        <div class="pagination">
          <span class="pagination__info">
            Menampilkan {{ paginationStart }}–{{ paginationEnd }} dari
            <strong>{{ filteredRows.length.toLocaleString('id-ID') }}</strong> entri
          </span>

          <div class="pagination__controls">
            <!-- Prev -->
            <button
              class="page-btn"
              :disabled="currentPage === 1"
              @click="currentPage--"
            >
              <span class="material-symbols-outlined" style="font-size:16px">chevron_left</span>
            </button>

            <!-- Page numbers -->
            <template v-for="p in visiblePages" :key="p">
              <span v-if="p === '...'" class="page-ellipsis">…</span>
              <button
                v-else
                class="page-btn"
                :class="{ 'page-btn--active': p === currentPage }"
                @click="currentPage = p"
              >{{ p }}</button>
            </template>

            <!-- Next -->
            <button
              class="page-btn"
              :disabled="currentPage === totalPages"
              @click="currentPage++"
            >
              <span class="material-symbols-outlined" style="font-size:16px">chevron_right</span>
            </button>
          </div>

          <!-- Per-page selector -->
          <div class="perpage-group">
            <label class="perpage-label">Baris:</label>
            <select v-model.number="perPage" class="perpage-select" @change="currentPage = 1">
              <option :value="10">10</option>
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
        </div>
      </div>

    </div>

    <!-- ══════════════════════════════════════════════════════════
         DETAIL DRAWER (slide-in from right)
         ══════════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <Transition name="drawer">
        <div
          v-if="detailRow"
          class="drawer-overlay"
          @click.self="detailRow = null"
        >
          <div class="drawer">
            <!-- Drawer header -->
            <div class="drawer__header">
              <h3 class="drawer__title">Detail Deteksi</h3>
              <button class="drawer__close" @click="detailRow = null">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>

            <!-- Plate preview -->
            <div class="drawer__plate-preview">
              <div class="plate-badge plate-badge--lg" :class="{ 'plate-badge--alert': detailRow.status === 'watchlist' }">
                {{ detailRow.plate_text || '—' }}
              </div>
              <span class="status-badge" :class="statusBadgeClass(detailRow.status)">
                {{ statusLabel(detailRow.status) }}
              </span>
            </div>

            <!-- Detail rows -->
            <div class="drawer__body">
              <div class="detail-item">
                <span class="detail-item__label">Waktu Deteksi</span>
                <span class="detail-item__val">
                  {{ formatTime(detailRow.detected_at) }}
                  <span class="detail-item__sub">{{ formatDate(detailRow.detected_at) }}</span>
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-item__label">Kamera</span>
                <span class="detail-item__val">{{ detailRow.camera_label }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-item__label">Wilayah</span>
                <span class="detail-item__val">{{ detailRow.region || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-item__label">Sumber</span>
                <span class="detail-item__val">{{ detailRow.source || 'stream' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-item__label">Confidence OCR</span>
                <span class="detail-item__val">
                  {{ detailRow.confidence != null ? (detailRow.confidence * 100).toFixed(2) + '%' : '—' }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-item__label">Kode Wilayah</span>
                <span class="detail-item__val drawer__mono">{{ detailRow.region_code || '—' }}</span>
              </div>
            </div>

            <!-- Actions -->
            <div class="drawer__footer">
              <button class="btn-drawer-action btn-drawer-action--primary">
                <span class="material-symbols-outlined" style="font-size:16px">flag</span>
                Tandai Watchlist
              </button>
              <button class="btn-drawer-action">
                <span class="material-symbols-outlined" style="font-size:16px">download</span>
                Export
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </MainLayout>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'

// ─── Dummy data generator ─────────────────────────────────────────────────────
const STATUSES   = ['valid', 'valid', 'valid', 'valid', 'watchlist', 'invalid', 'ocr_failed']
const CAMERAS    = [
  { id: 1, label: 'Cam-01-Sudirman' },
  { id: 2, label: 'Cam-02-Thamrin' },
  { id: 3, label: 'Cam-05-GatotSubroto' },
  { id: 4, label: 'Cam-12-Pahlawan' },
]
const REGIONS = ['Jakarta Pusat', 'Jakarta Selatan', 'Jakarta Utara', 'Surabaya', 'Bandung', 'Yogyakarta', 'Bogor', 'Depok']
const REGION_CODES = ['B', 'D', 'L', 'AB', 'F', 'T', 'Z', 'N']
const PLATES = ['B 1234 RFS', 'D 5678 EFG', 'L 9012 HIJ', 'B 3344 KKL', 'F 8877 GG', 'AB 1111 ZZ', 'N 4321 AB', 'T 9876 XY', 'D 1212 PP', 'B 5555 QRS']

function makeDummyData(n = 200) {
  const rows = []
  const base = new Date()
  for (let i = 0; i < n; i++) {
    const status  = STATUSES[Math.floor(Math.random() * STATUSES.length)]
    const cam     = CAMERAS[Math.floor(Math.random() * CAMERAS.length)]
    const regIdx  = Math.floor(Math.random() * REGIONS.length)
    const ts      = new Date(base.getTime() - i * 3700 - Math.random() * 1800000)
    rows.push({
      id:           i + 1,
      plate_text:   status === 'ocr_failed' ? null : PLATES[Math.floor(Math.random() * PLATES.length)],
      detected_at:  ts.toISOString(),
      camera_id:    cam.id,
      camera_label: cam.label,
      region:       REGIONS[regIdx],
      region_code:  REGION_CODES[regIdx],
      confidence:   status === 'ocr_failed' ? null : 0.82 + Math.random() * 0.18,
      status,
      source:       Math.random() > 0.4 ? 'stream' : 'upload',
    })
  }
  return rows
}

const allRows = ref(makeDummyData(200))
const cameras = ref(CAMERAS)
const loading = ref(false)

// ─── Stats ────────────────────────────────────────────────────────────────────
const totalToday   = computed(() => allRows.value.length)
const totalFlagged = computed(() => allRows.value.filter(r => r.status === 'watchlist').length)

// ─── Filters ──────────────────────────────────────────────────────────────────
const filters = ref({
  search:    '',
  dateRange: 'today',
  camera:    '',
  status:    '',
})

const sortKey = ref('detected_at')
const sortDir = ref('desc')  // 'asc' | 'desc'

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'desc'
  }
}

function sortIcon(key) {
  if (sortKey.value !== key) return 'unfold_more'
  return sortDir.value === 'asc' ? 'arrow_upward' : 'arrow_downward'
}

// ─── Computed filtered + sorted rows ─────────────────────────────────────────
const filteredRows = computed(() => {
  let rows = [...allRows.value]

  // search
  if (filters.value.search) {
    const q = filters.value.search.toUpperCase().replace(/\s/g, '')
    rows = rows.filter(r => r.plate_text?.replace(/\s/g, '').includes(q))
  }

  // date range (simplified — all dummy data is "today" anyway)
  // camera
  if (filters.value.camera) {
    const camId = Number(filters.value.camera)
    rows = rows.filter(r => r.camera_id === camId)
  }

  // status
  if (filters.value.status) {
    rows = rows.filter(r => r.status === filters.value.status)
  }

  // sort
  const dir = sortDir.value === 'asc' ? 1 : -1
  rows.sort((a, b) => {
    const va = a[sortKey.value] ?? ''
    const vb = b[sortKey.value] ?? ''
    if (va < vb) return -dir
    if (va > vb) return  dir
    return 0
  })

  return rows
})

// ─── Debounce search ──────────────────────────────────────────────────────────
let searchTimer = null
function debouncedFilter() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { currentPage.value = 1 }, 250)
}

function applyFilters() { currentPage.value = 1 }

function resetFilters() {
  filters.value = { search: '', dateRange: 'today', camera: '', status: '' }
  currentPage.value = 1
}

// ─── Pagination ───────────────────────────────────────────────────────────────
const perPage     = ref(25)
const currentPage = ref(1)

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / perPage.value)))

watch(filteredRows, () => {
  if (currentPage.value > totalPages.value) currentPage.value = 1
})

const paginationStart = computed(() =>
  filteredRows.value.length === 0 ? 0 : (currentPage.value - 1) * perPage.value + 1
)
const paginationEnd = computed(() =>
  Math.min(currentPage.value * perPage.value, filteredRows.value.length)
)

const pagedRows = computed(() => {
  const s = (currentPage.value - 1) * perPage.value
  return filteredRows.value.slice(s, s + perPage.value)
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur   = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = [1]
  if (cur > 3)  pages.push('...')
  for (let p = Math.max(2, cur - 1); p <= Math.min(total - 1, cur + 1); p++) pages.push(p)
  if (cur < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

// ─── Detail drawer ────────────────────────────────────────────────────────────
const detailRow = ref(null)
function openDetail(row) { detailRow.value = row }

// ─── Formatters ───────────────────────────────────────────────────────────────
function formatTime(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatDate(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
}

function confPct(val) {
  return val != null ? Math.round(val * 100) : 0
}

function confBarClass(val) {
  if (val == null)  return 'conf--na'
  if (val >= 0.95)  return 'conf--high'
  if (val >= 0.85)  return 'conf--mid'
  return 'conf--low'
}

function statusLabel(status) {
  return { valid: 'Authorized', watchlist: 'Flagged', invalid: 'Unregistered', ocr_failed: 'OCR Failed' }[status] ?? status
}

function statusBadgeClass(status) {
  return {
    valid:      'badge--authorized',
    watchlist:  'badge--flagged',
    invalid:    'badge--unreg',
    ocr_failed: 'badge--fail',
  }[status] ?? ''
}

// ─── Export ───────────────────────────────────────────────────────────────────
function exportCSV() {
  const cols = ['id', 'plate_text', 'detected_at', 'camera_label', 'region', 'confidence', 'status']
  const header = cols.join(',')
  const rows = filteredRows.value.map(r =>
    cols.map(c => JSON.stringify(r[c] ?? '')).join(',')
  )
  download([header, ...rows].join('\n'), 'riwayat_deteksi.csv', 'text/csv')
}

function exportJSON() {
  download(JSON.stringify(filteredRows.value, null, 2), 'riwayat_deteksi.json', 'application/json')
}

function download(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
/* ─── Page wrapper ───────────────────────────────────────────────────────────── */
.riwayat {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ─── Heading ─────────────────────────────────────────────────────────────────── */
.riwayat__heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.riwayat__title {
  font-size: 26px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.02em;
  line-height: 1;
}

.riwayat__sub {
  font-size: 13px;
  color: var(--on-surface-variant);
  margin-top: 4px;
}

.riwayat__header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* ─── Mini stat cards ─────────────────────────────────────────────────────────── */
.riwayat__mini-stats {
  display: flex;
  gap: 12px;
}

.mini-stat {
  background-color: var(--surface-container-low);
  border: 1px solid rgba(195, 199, 203, 0.2);
  border-radius: 8px;
  padding: 12px 18px;
  display: flex;
  flex-direction: column;
  min-width: 110px;
  box-shadow: 0 4px 16px rgba(15, 31, 41, 0.03);
}

.mini-stat__label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--on-surface-variant);
  margin-bottom: 4px;
}

.mini-stat__value {
  font-size: 22px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.mini-stat__value--alert { color: var(--on-tertiary-container); }

/* ─── Export group ─────────────────────────────────────────────────────────────── */
.export-group {
  display: flex;
  gap: 6px;
}

.btn-export {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 14px;
  border: 1px solid rgba(195, 199, 203, 0.3);
  border-radius: 6px;
  background-color: var(--surface-container-lowest);
  color: var(--on-surface-variant);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.12s, color 0.12s, border-color 0.12s;
}

.btn-export:hover {
  background-color: var(--surface-container-high);
  color: var(--primary);
  border-color: rgba(195, 199, 203, 0.5);
}

/* ─── Filter bar ─────────────────────────────────────────────────────────────── */
.filter-bar {
  background-color: var(--surface-container-low);
  border: 1px solid rgba(195, 199, 203, 0.12);
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  box-shadow: 0 4px 20px rgba(15, 31, 41, 0.03);
  backdrop-filter: blur(8px);
}

.filter-field {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 160px;
}

.filter-field--grow { flex: 1; min-width: 200px; }

.filter-field__icon {
  position: absolute;
  left: 12px;
  font-size: 18px;
  color: var(--on-surface-variant);
  pointer-events: none;
  z-index: 1;
}

.filter-field__chevron {
  position: absolute;
  right: 10px;
  font-size: 18px;
  color: var(--on-surface-variant);
  pointer-events: none;
}

.filter-input,
.filter-select {
  width: 100%;
  background-color: var(--surface-container-lowest);
  border: none;
  border-bottom: 2px solid transparent;
  border-radius: 8px;
  padding: 10px 12px 10px 40px;
  font-size: 13px;
  font-weight: 500;
  color: var(--primary);
  font-family: inherit;
  outline: none;
  appearance: none;
  box-shadow: 0 2px 8px rgba(15, 31, 41, 0.04);
  transition: border-color 0.15s;
}

.filter-select { padding-right: 36px; cursor: pointer; }

.filter-input:focus,
.filter-select:focus {
  border-bottom-color: var(--primary);
}

.btn-reset {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background-color: var(--surface-container-highest);
  border: none;
  border-radius: 8px;
  color: var(--primary);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.12s;
  white-space: nowrap;
}

.btn-reset:hover { background-color: var(--surface-variant); }

/* ─── Table card ─────────────────────────────────────────────────────────────── */
.table-card {
  background-color: var(--surface-container-lowest);
  border-radius: 12px;
  border: 1px solid rgba(195, 199, 203, 0.12);
  box-shadow: 0 8px 30px rgba(15, 31, 41, 0.04);
  overflow: hidden;
}

.table-wrap { overflow-x: auto; }

/* ─── Table ──────────────────────────────────────────────────────────────────── */
.riwayat-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

/* THEAD */
.riwayat-table thead tr {
  background-color: rgba(240, 245, 244, 0.5);
}

.riwayat-table th {
  padding: 14px 18px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--on-surface-variant);
  white-space: nowrap;
  user-select: none;
  text-align: left;
}

.riwayat-table th.col-aksi { text-align: right; }

.sortable {
  cursor: pointer;
  display: table-cell;
}

.sortable:hover { color: var(--primary); }

.sort-icon {
  font-size: 14px !important;
  vertical-align: middle;
  margin-left: 2px;
}

/* Width hints */
.col-no     { width: 48px; }
.col-plat   { width: 160px; }
.col-waktu  { width: 130px; }
.col-conf   { width: 140px; }
.col-status { width: 120px; }
.col-aksi   { width: 56px; }

/* TBODY rows */
.data-row {
  border-bottom: 1px solid rgba(195, 199, 203, 0.06);
  cursor: pointer;
  transition: background-color 0.1s ease;
}
.data-row:last-child { border-bottom: none; }
.data-row:hover { background-color: rgba(222, 227, 227, 0.35); }

.data-row--alt   { background-color: rgba(240, 245, 244, 0.2); }
.data-row--alert { background-color: rgba(255, 220, 198, 0.08); }
.data-row--muted { opacity: 0.6; }

.data-row td {
  padding: 16px 18px;
  vertical-align: middle;
}

/* Cells */
.td-no { color: var(--on-surface-variant); font-weight: 500; font-size: 12px; }
.td-kamera { display: flex; align-items: center; gap: 6px; font-weight: 600; color: var(--primary); }
.td-wilayah { font-weight: 500; color: var(--on-surface-variant); }
.td-aksi { text-align: right; }

/* ─── Plate badge ────────────────────────────────────────────────────────────── */
.plate-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px 10px;
  background-color: var(--surface-container-lowest);
  border: 1px solid rgba(195, 199, 203, 0.3);
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(15, 31, 41, 0.04);
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.plate-badge--alert {
  border-color: rgba(255, 183, 134, 0.5);
}

.plate-badge--lg {
  font-size: 20px;
  padding: 8px 16px;
  letter-spacing: 0.1em;
}

/* ─── Time group ─────────────────────────────────────────────────────────────── */
.time-group { display: flex; flex-direction: column; }
.time-group__time { font-weight: 700; color: var(--primary); }
.time-group__date { font-size: 10px; color: var(--on-surface-variant); margin-top: 2px; }

/* ─── Camera icon ────────────────────────────────────────────────────────────── */
.cam-icon { font-size: 16px !important; color: var(--on-surface-variant); }

/* ─── Confidence bar ─────────────────────────────────────────────────────────── */
.conf-wrap { display: flex; align-items: center; gap: 8px; }

.conf-bar {
  width: 60px;
  height: 5px;
  background-color: var(--surface-container-high);
  border-radius: 9999px;
  overflow: hidden;
  flex-shrink: 0;
}

.conf-bar__fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 0.4s ease;
}

.conf-val { font-size: 11px; font-weight: 700; }

.conf--high .conf-bar__fill { background-color: #16a34a; }
.conf--mid  .conf-bar__fill { background-color: var(--primary); }
.conf--low  .conf-bar__fill { background-color: #dc2626; }
.conf--na   .conf-bar__fill { background-color: var(--outline); }

.conf--high.conf-val { color: #16a34a; }
.conf--mid.conf-val  { color: var(--primary); }
.conf--low.conf-val  { color: #dc2626; }
.conf--na.conf-val   { color: var(--on-surface-variant); }

/* ─── Status badge pills ─────────────────────────────────────────────────────── */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.badge--authorized { background-color: var(--secondary-container); color: var(--on-secondary-container); }
.badge--flagged    { background-color: rgba(83,38,0,0.12); color: var(--on-tertiary-container); }
.badge--unreg      { background-color: var(--surface-container-high); color: var(--on-surface); }
.badge--fail       { background-color: var(--error-container); color: var(--on-error-container); }

/* ─── Aksi button ────────────────────────────────────────────────────────────── */
.btn-detail {
  display: inline-flex;
  align-items: center;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--on-surface-variant);
  padding: 4px;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.12s, color 0.12s, background-color 0.12s;
}
.data-row:hover .btn-detail {
  opacity: 1;
}
.btn-detail:hover { color: var(--primary); background-color: var(--surface-container-low); }

/* ─── Skeleton ───────────────────────────────────────────────────────────────── */
.skeleton-row td { padding: 20px 18px; }

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skel {
  height: 12px;
  border-radius: 4px;
  background: linear-gradient(90deg,
    var(--surface-container-low) 25%,
    var(--surface-container-high) 50%,
    var(--surface-container-low) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.skel--xs  { width: 24px; }
.skel--sm  { width: 80px; }
.skel--md  { width: 130px; }

/* ─── Empty state ────────────────────────────────────────────────────────────── */
.empty-cell { padding: 0 !important; }
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 56px;
  color: var(--on-surface-variant);
  font-size: 13px;
}

/* ─── Pagination ─────────────────────────────────────────────────────────────── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 14px 20px;
  border-top: 1px solid rgba(195, 199, 203, 0.1);
  background-color: var(--surface-container-lowest);
}

.pagination__info {
  font-size: 12px;
  font-weight: 500;
  color: var(--on-surface-variant);
}
.pagination__info strong { color: var(--primary); font-weight: 700; }

.pagination__controls {
  display: flex;
  gap: 4px;
}

.page-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: none;
  background-color: var(--surface-container-high);
  color: var(--primary);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.12s, color 0.12s;
}

.page-btn:hover:not(:disabled) { background-color: var(--surface-variant); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-btn--active  { background-color: var(--primary); color: var(--on-primary); }

.page-ellipsis {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--on-surface-variant);
  font-size: 14px;
}

.perpage-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.perpage-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.perpage-select {
  background-color: var(--surface-container-low);
  border: 1px solid rgba(195, 199, 203, 0.25);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  cursor: pointer;
  font-family: inherit;
  outline: none;
}

/* ─── Detail Drawer ──────────────────────────────────────────────────────────── */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 31, 41, 0.3);
  z-index: 200;
  display: flex;
  justify-content: flex-end;
  backdrop-filter: blur(2px);
}

.drawer {
  width: 360px;
  background-color: var(--surface-container-lowest);
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: -8px 0 40px rgba(15, 31, 41, 0.12);
  overflow: hidden;
}

.drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(195, 199, 203, 0.15);
  flex-shrink: 0;
}

.drawer__title {
  font-size: 15px;
  font-weight: 700;
  color: var(--primary);
}

.drawer__close {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--on-surface-variant);
  padding: 4px;
  border-radius: 50%;
  transition: background-color 0.12s, color 0.12s;
}
.drawer__close:hover { background-color: var(--surface-container-low); color: var(--primary); }

.drawer__plate-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 28px 24px;
  background-color: var(--surface-container-low);
  border-bottom: 1px solid rgba(195, 199, 203, 0.15);
  flex-shrink: 0;
}

.drawer__body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid rgba(195, 199, 203, 0.08);
  gap: 12px;
}
.detail-item:last-child { border-bottom: none; }

.detail-item__label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--on-surface-variant);
  flex-shrink: 0;
  padding-top: 2px;
}

.detail-item__val {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-item__sub {
  font-size: 11px;
  color: var(--on-surface-variant);
  font-weight: 400;
}

.drawer__mono {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  letter-spacing: 0.04em;
}

.drawer__footer {
  display: flex;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid rgba(195, 199, 203, 0.15);
  flex-shrink: 0;
}

.btn-drawer-action {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(195, 199, 203, 0.25);
  background-color: var(--surface-container-low);
  color: var(--on-surface-variant);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.12s, color 0.12s;
}

.btn-drawer-action:hover { background-color: var(--surface-container-high); color: var(--primary); }

.btn-drawer-action--primary {
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary);
  border: none;
}
.btn-drawer-action--primary:hover { opacity: 0.88; color: var(--on-primary); }

/* ─── Drawer transition ──────────────────────────────────────────────────────── */
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.22s ease;
}
.drawer-enter-active .drawer,
.drawer-leave-active .drawer {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.drawer-enter-from    { opacity: 0; }
.drawer-enter-from .drawer { transform: translateX(100%); }
.drawer-leave-to      { opacity: 0; }
.drawer-leave-to .drawer  { transform: translateX(100%); }
</style>
