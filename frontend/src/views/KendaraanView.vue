<template>
  <MainLayout>
    <div class="kendaraan-page">

      <!-- ══ HEADING ═══════════════════════════════════════════════════════ -->
      <div class="k-heading">
        <div>
          <h2 class="k-heading__title">Database Kendaraan</h2>
          <p class="k-heading__sub">Manajemen whitelist, watchlist, dan daftar plat nomor terdaftar.</p>
        </div>

        <div class="k-heading__actions">
          <!-- Tab switcher -->
          <div class="tab-group">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="tab-btn"
              :class="{ 'tab-btn--active': activeTab === tab.key }"
              @click="setTab(tab.key)"
            >
              <span class="material-symbols-outlined" style="font-size:15px">{{ tab.icon }}</span>
              {{ tab.label }}
              <span class="tab-count" :class="tabCountClass(tab.key)">{{ tabCount(tab.key) }}</span>
            </button>
          </div>

          <!-- Add button -->
          <button class="btn-add" @click="openForm(null)">
            <span class="material-symbols-outlined" style="font-size:16px">add</span>
            Tambah Kendaraan
          </button>
        </div>
      </div>

      <!-- ══ STATS BAR ══════════════════════════════════════════════════════ -->
      <div class="stats-bar">
        <div class="stat-chip" v-for="s in statChips" :key="s.label">
          <span class="material-symbols-outlined stat-chip__icon" :style="{ color: s.color }">{{ s.icon }}</span>
          <div>
            <div class="stat-chip__val">{{ s.val }}</div>
            <div class="stat-chip__label">{{ s.label }}</div>
          </div>
        </div>
      </div>

      <!-- ══ SEARCH + FILTER ════════════════════════════════════════════════ -->
      <div class="k-filter">
        <div class="k-filter__search">
          <span class="material-symbols-outlined k-filter__search-icon">search</span>
          <input
            v-model="searchQuery"
            type="text"
            class="k-filter__input"
            placeholder="Cari plat nomor, pemilik, atau wilayah..."
          />
        </div>
        <div class="k-filter__right">
          <select v-model="filterRegion" class="k-filter__select">
            <option value="">Semua Wilayah</option>
            <option v-for="r in uniqueRegions" :key="r" :value="r">{{ r }}</option>
          </select>
          <button class="btn-reset-sm" @click="resetFilter">
            <span class="material-symbols-outlined" style="font-size:15px">restart_alt</span>
          </button>
        </div>
      </div>

      <!-- ══ TABLE ══════════════════════════════════════════════════════════ -->
      <div class="k-table-card">
        <table class="k-table">
          <thead>
            <tr>
              <th class="col-no">No</th>
              <th class="col-plat sortable" @click="toggleSort('plate')">
                Plat Nomor
                <span class="material-symbols-outlined sort-icon">{{ sortIcon('plate') }}</span>
              </th>
              <th class="col-owner">Pemilik</th>
              <th class="col-region">Wilayah</th>
              <th class="col-type">Tipe</th>
              <th class="col-status">Status</th>
              <th class="col-reg sortable" @click="toggleSort('registered_at')">
                Terdaftar
                <span class="material-symbols-outlined sort-icon">{{ sortIcon('registered_at') }}</span>
              </th>
              <th class="col-aksi">Aksi</th>
            </tr>
          </thead>

          <tbody>
            <!-- Skeleton -->
            <template v-if="loading">
              <tr v-for="i in 8" :key="`sk-${i}`" class="skel-row">
                <td v-for="j in 8" :key="j"><div class="skel" :class="`skel--${['xs','md','sm','sm','xs','xs','sm','xs'][j-1]}`"></div></td>
              </tr>
            </template>

            <!-- Empty -->
            <tr v-else-if="!pagedRows.length">
              <td colspan="8" class="empty-cell">
                <div class="empty-state">
                  <span class="material-symbols-outlined" style="font-size:30px;opacity:.2">directions_car</span>
                  <p>Tidak ada kendaraan ditemukan</p>
                </div>
              </td>
            </tr>

            <!-- Data rows -->
            <tr
              v-for="(row, idx) in pagedRows"
              :key="row.id"
              class="k-row"
              :class="{
                'k-row--alt':     idx % 2 === 1,
                'k-row--alert':   row.status === 'watchlist',
              }"
            >
              <td class="td-no">{{ (currentPage - 1) * perPage + idx + 1 }}</td>

              <!-- Plate -->
              <td>
                <div class="plate-pill" :class="{ 'plate-pill--alert': row.status === 'watchlist' }">
                  {{ row.plate }}
                </div>
              </td>

              <!-- Owner -->
              <td class="td-owner">
                <div class="owner-info">
                  <div class="owner-avatar" :style="{ background: avatarColor(row.owner) }">
                    {{ row.owner.charAt(0).toUpperCase() }}
                  </div>
                  <span>{{ row.owner }}</span>
                </div>
              </td>

              <!-- Region -->
              <td class="td-region">{{ row.region }}</td>

              <!-- Vehicle type -->
              <td>
                <span class="type-pill">{{ row.vehicle_type }}</span>
              </td>

              <!-- Status -->
              <td>
                <span class="status-pill" :class="statusPillClass(row.status)">
                  <span
                    v-if="row.status === 'watchlist'"
                    class="material-symbols-outlined"
                    style="font-size:10px;font-variation-settings:'FILL' 1"
                  >warning</span>
                  {{ statusLabel(row.status) }}
                </span>
              </td>

              <!-- Date -->
              <td class="td-date">{{ formatDate(row.registered_at) }}</td>

              <!-- Actions -->
              <td class="td-aksi">
                <div class="action-btns">
                  <button class="action-btn" title="Edit" @click="openForm(row)">
                    <span class="material-symbols-outlined" style="font-size:15px">edit</span>
                  </button>
                  <button
                    class="action-btn action-btn--flag"
                    :class="{ 'action-btn--flagged': row.status === 'watchlist' }"
                    :title="row.status === 'watchlist' ? 'Hapus Watchlist' : 'Tambah Watchlist'"
                    @click="toggleWatchlist(row)"
                  >
                    <span class="material-symbols-outlined" style="font-size:15px"
                      :style="{ fontVariationSettings: row.status === 'watchlist' ? `'FILL' 1` : `'FILL' 0` }"
                    >flag</span>
                  </button>
                  <button class="action-btn action-btn--del" title="Hapus" @click="confirmDelete(row)">
                    <span class="material-symbols-outlined" style="font-size:15px">delete</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="k-pagination">
          <span class="k-pagination__info">
            Menampilkan {{ paginationStart }}–{{ paginationEnd }} dari
            <strong>{{ filteredRows.length }}</strong> entri
          </span>
          <div class="k-pagination__controls">
            <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">
              <span class="material-symbols-outlined" style="font-size:15px">chevron_left</span>
            </button>
            <template v-for="p in visiblePages" :key="p">
              <span v-if="p === '...'" class="page-ellipsis">…</span>
              <button v-else class="page-btn" :class="{ 'page-btn--active': p === currentPage }" @click="currentPage = p">{{ p }}</button>
            </template>
            <button class="page-btn" :disabled="currentPage === totalPages" @click="currentPage++">
              <span class="material-symbols-outlined" style="font-size:15px">chevron_right</span>
            </button>
          </div>
        </div>
      </div>

      <!-- ══ ADD/EDIT MODAL (Teleport) ════════════════════════════════════ -->
      <Teleport to="body">
        <Transition name="modal">
          <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
            <div class="modal">
              <div class="modal__header">
                <h3 class="modal__title">{{ editTarget ? 'Edit Kendaraan' : 'Tambah Kendaraan Baru' }}</h3>
                <button class="modal__close" @click="showForm = false">
                  <span class="material-symbols-outlined">close</span>
                </button>
              </div>

              <div class="modal__body">
                <!-- Plate number -->
                <div class="form-field">
                  <label class="form-label">Plat Nomor *</label>
                  <input v-model="form.plate" class="form-input form-input--mono" placeholder="B 1234 XYZ" type="text" />
                </div>

                <!-- Owner -->
                <div class="form-field">
                  <label class="form-label">Nama Pemilik</label>
                  <input v-model="form.owner" class="form-input" placeholder="Nama lengkap pemilik kendaraan" type="text" />
                </div>

                <!-- Two columns -->
                <div class="form-row">
                  <div class="form-field">
                    <label class="form-label">Wilayah</label>
                    <select v-model="form.region" class="form-select">
                      <option v-for="r in REGIONS_LIST" :key="r" :value="r">{{ r }}</option>
                    </select>
                  </div>
                  <div class="form-field">
                    <label class="form-label">Tipe Kendaraan</label>
                    <select v-model="form.vehicle_type" class="form-select">
                      <option>Sedan</option>
                      <option>SUV</option>
                      <option>MPV</option>
                      <option>Pickup</option>
                      <option>Truk</option>
                      <option>Motor</option>
                      <option>Bus</option>
                    </select>
                  </div>
                </div>

                <!-- Status -->
                <div class="form-field">
                  <label class="form-label">Status</label>
                  <div class="status-radios">
                    <label
                      v-for="opt in statusOptions"
                      :key="opt.val"
                      class="radio-opt"
                      :class="{ 'radio-opt--active': form.status === opt.val, [`radio-opt--${opt.val}`]: true }"
                    >
                      <input type="radio" v-model="form.status" :value="opt.val" class="hidden" />
                      <span class="material-symbols-outlined" style="font-size:14px">{{ opt.icon }}</span>
                      {{ opt.label }}
                    </label>
                  </div>
                </div>

                <!-- Notes -->
                <div class="form-field">
                  <label class="form-label">Catatan</label>
                  <textarea v-model="form.notes" class="form-input form-input--textarea" placeholder="Catatan tambahan..." rows="2"></textarea>
                </div>
              </div>

              <div class="modal__footer">
                <button class="btn-cancel" @click="showForm = false">Batal</button>
                <button class="btn-save" @click="saveForm" :disabled="!form.plate.trim()">
                  <span class="material-symbols-outlined" style="font-size:15px">save</span>
                  {{ editTarget ? 'Simpan Perubahan' : 'Tambah Kendaraan' }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- ══ DELETE CONFIRM ════════════════════════════════════════════════ -->
      <Teleport to="body">
        <Transition name="modal">
          <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
            <div class="modal modal--sm">
              <div class="modal__header">
                <h3 class="modal__title">Hapus Kendaraan?</h3>
                <button class="modal__close" @click="deleteTarget = null">
                  <span class="material-symbols-outlined">close</span>
                </button>
              </div>
              <div class="modal__body">
                <p class="delete-confirm__text">
                  Apakah Anda yakin ingin menghapus kendaraan
                  <strong>{{ deleteTarget?.plate }}</strong> dari database?
                  Tindakan ini tidak dapat dibatalkan.
                </p>
              </div>
              <div class="modal__footer">
                <button class="btn-cancel" @click="deleteTarget = null">Batal</button>
                <button class="btn-delete" @click="deleteConfirmed">
                  <span class="material-symbols-outlined" style="font-size:15px">delete</span>
                  Hapus
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'
import { useVehicleStore } from '@/stores/vehicle'

const vehicleStore = useVehicleStore()

// ─── Constants ────────────────────────────────────────────────────────────────
const REGIONS_LIST = [
  'DKI Jakarta', 'Jawa Barat', 'Jawa Tengah', 'Jawa Timur',
  'Yogyakarta', 'Banten', 'Bali', 'Sumatera Utara', 'Sulawesi Selatan',
]

// ─── Dummy data (static fallback when backend offline) ────────────────────────
const OWNERS = ['Budi Santoso', 'Dewi Rahayu', 'Ahmad Fauzi', 'Siti Nurhaliza', 'Eko Prasetyo', 'Rina Wati', 'Hendra Gunawan', 'Maya Sari']
const PLATES = ['B 1234 ABC', 'D 5678 XYZ', 'L 9012 QRS', 'AB 3344 TT', 'F 8877 GG', 'N 4321 PP', 'B 5566 KK', 'T 7890 MN']

function makeDummy(n = 40) {
  const statuses = ['whitelist', 'whitelist', 'whitelist', 'watchlist', 'blacklist']
  const types    = ['Sedan', 'SUV', 'MPV', 'Pickup', 'Motor', 'Truk']
  return Array.from({ length: n }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - Math.floor(Math.random() * 180))
    return {
      id: i + 1,
      plate: PLATES[i % PLATES.length] + `-${i}`,
      owner: OWNERS[i % OWNERS.length],
      region: REGIONS_LIST[i % REGIONS_LIST.length],
      vehicle_type: types[i % types.length],
      status: statuses[i % statuses.length],
      registered_at: d.toISOString(),
      notes: '',
    }
  })
}

// Local state for offline-mode or optimistic edits
const localRows = ref([])
const loading   = computed(() => vehicleStore.loading)

// Merge: prefer API data, fallback to dummy
const allRows = computed(() =>
  vehicleStore.vehicles.length ? vehicleStore.vehicles : localRows.value
)

// ─── Tabs ─────────────────────────────────────────────────────────────────────
const tabs = [
  { key: '',           label: 'Semua',     icon: 'list' },
  { key: 'whitelist',  label: 'Whitelist', icon: 'verified' },
  { key: 'watchlist',  label: 'Watchlist', icon: 'flag' },
  { key: 'blacklist',  label: 'Blacklist', icon: 'block' },
]

const activeTab = ref('')

function setTab(key) { activeTab.value = key; currentPage.value = 1 }

function tabCount(key) {
  if (!key) return allRows.value.length
  return allRows.value.filter(r => r.status === key).length
}

function tabCountClass(key) {
  return { whitelist: 'count--ok', watchlist: 'count--alert', blacklist: 'count--error', '': 'count--neutral' }[key]
}

// ─── Stats bar ────────────────────────────────────────────────────────────────
const statChips = computed(() => [
  { label: 'Total Terdaftar', val: allRows.value.length, icon: 'database',  color: 'var(--primary)' },
  { label: 'Whitelist',       val: allRows.value.filter(r => r.status === 'whitelist').length, icon: 'verified', color: '#16a34a' },
  { label: 'Watchlist',       val: allRows.value.filter(r => r.status === 'watchlist').length, icon: 'flag',     color: 'var(--on-tertiary-container)' },
  { label: 'Blacklist',       val: allRows.value.filter(r => r.status === 'blacklist').length, icon: 'block',    color: '#dc2626' },
])

// ─── Filters & Sort ────────────────────────────────────────────────────────────
const searchQuery  = ref('')
const filterRegion = ref('')
const sortKey      = ref('registered_at')
const sortDir      = ref('desc')

function toggleSort(key) {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else { sortKey.value = key; sortDir.value = 'desc' }
}

function sortIcon(key) {
  if (sortKey.value !== key) return 'unfold_more'
  return sortDir.value === 'asc' ? 'arrow_upward' : 'arrow_downward'
}

function resetFilter() { searchQuery.value = ''; filterRegion.value = '' }

const uniqueRegions = computed(() => [...new Set(allRows.value.map(r => r.region))].sort())

const filteredRows = computed(() => {
  let rows = [...allRows.value]
  if (activeTab.value)   rows = rows.filter(r => r.status === activeTab.value)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    rows = rows.filter(r =>
      r.plate?.toLowerCase().includes(q) ||
      r.owner?.toLowerCase().includes(q) ||
      r.region?.toLowerCase().includes(q)
    )
  }
  if (filterRegion.value) rows = rows.filter(r => r.region === filterRegion.value)

  const dir = sortDir.value === 'asc' ? 1 : -1
  rows.sort((a, b) => {
    const va = a[sortKey.value] ?? ''
    const vb = b[sortKey.value] ?? ''
    return va < vb ? -dir : va > vb ? dir : 0
  })
  return rows
})

// ─── Pagination ───────────────────────────────────────────────────────────────
const perPage     = ref(15)
const currentPage = ref(1)
const totalPages  = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / perPage.value)))

watch(filteredRows, () => { if (currentPage.value > totalPages.value) currentPage.value = 1 })

const paginationStart = computed(() => filteredRows.value.length === 0 ? 0 : (currentPage.value - 1) * perPage.value + 1)
const paginationEnd   = computed(() => Math.min(currentPage.value * perPage.value, filteredRows.value.length))

const pagedRows = computed(() => {
  const s = (currentPage.value - 1) * perPage.value
  return filteredRows.value.slice(s, s + perPage.value)
})

const visiblePages = computed(() => {
  const total = totalPages.value, cur = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = [1]
  if (cur > 3)  pages.push('...')
  for (let p = Math.max(2, cur - 1); p <= Math.min(total - 1, cur + 1); p++) pages.push(p)
  if (cur < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

// ─── Modal (Add/Edit) ─────────────────────────────────────────────────────────
const showForm   = ref(false)
const editTarget = ref(null)

const formDefault = () => ({
  plate: '', owner: '', region: REGIONS_LIST[0],
  vehicle_type: 'Sedan', status: 'whitelist', notes: '',
})

const form = ref(formDefault())

const statusOptions = [
  { val: 'whitelist', label: 'Whitelist', icon: 'verified' },
  { val: 'watchlist', label: 'Watchlist', icon: 'flag' },
  { val: 'blacklist', label: 'Blacklist', icon: 'block' },
]

function openForm(row) {
  editTarget.value = row
  form.value = row ? { ...row } : formDefault()
  showForm.value = true
}

async function saveForm() {
  if (!form.value.plate.trim()) return
  try {
    if (editTarget.value) {
      await vehicleStore.updateVehicle(editTarget.value.id, form.value)
    } else {
      await vehicleStore.createVehicle(form.value)
    }
  } catch {
    // Backend offline — optimistic local update
    if (editTarget.value) {
      const idx = localRows.value.findIndex(r => r.id === editTarget.value.id)
      if (idx !== -1) localRows.value[idx] = { ...form.value }
    } else {
      localRows.value.unshift({ ...form.value, id: Date.now(), registered_at: new Date().toISOString() })
    }
  }
  showForm.value = false
}

// ─── Delete ───────────────────────────────────────────────────────────────────
const deleteTarget = ref(null)
function confirmDelete(row) { deleteTarget.value = row }
async function deleteConfirmed() {
  try {
    await vehicleStore.deleteVehicle(deleteTarget.value.id)
  } catch {
    localRows.value = localRows.value.filter(r => r.id !== deleteTarget.value.id)
  }
  deleteTarget.value = null
}

// ─── Watchlist toggle ─────────────────────────────────────────────────────────
async function toggleWatchlist(row) {
  const newStatus = row.status === 'watchlist' ? 'whitelist' : 'watchlist'
  try {
    await vehicleStore.flagVehicle(row.id, newStatus)
  } catch {
    row.status = newStatus  // optimistic
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(ts) {
  return new Date(ts).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
}

function statusLabel(s) {
  return { whitelist: 'Whitelist', watchlist: 'Watchlist', blacklist: 'Blacklist' }[s] ?? s
}

function statusPillClass(s) {
  return { whitelist: 'sp--ok', watchlist: 'sp--alert', blacklist: 'sp--error' }[s] ?? ''
}

const AVATAR_COLORS = ['#1e3a5f', '#c4440c', '#154c2b', '#7b2d8b', '#1a5c7a', '#8b6914']
function avatarColor(name) {
  const idx = (name?.charCodeAt(0) ?? 0) % AVATAR_COLORS.length
  return AVATAR_COLORS[idx]
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    await vehicleStore.fetchVehicles()
  } catch {
    // Backend offline — use dummy data locally
    localRows.value = makeDummy(40)
  }
  // If API returned nothing, seed dummy
  if (!vehicleStore.vehicles.length && !localRows.value.length) {
    localRows.value = makeDummy(40)
  }
})
</script>

<style scoped>
/* ─── Page ───────────────────────────────────────────────────────────────────── */
.kendaraan-page { display: flex; flex-direction: column; gap: 20px; }

/* ─── Heading ─────────────────────────────────────────────────────────────────── */
.k-heading { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
.k-heading__title { font-size: 26px; font-weight: 800; color: var(--primary); letter-spacing: -0.02em; }
.k-heading__sub { font-size: 13px; color: var(--on-surface-variant); margin-top: 4px; }
.k-heading__actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

/* ─── Tab group ───────────────────────────────────────────────────────────────── */
.tab-group { display: flex; background: var(--surface-container-low); border-radius: 8px; padding: 3px; border: 1px solid rgba(195,199,203,.15); gap: 2px; }

.tab-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 6px; border: none;
  background: none; font-size: 12px; font-weight: 600; cursor: pointer;
  color: var(--on-surface-variant); transition: background .12s, color .12s;
  white-space: nowrap;
}
.tab-btn:hover { background: var(--surface-container-high); color: var(--primary); }
.tab-btn--active { background: var(--surface-container-lowest); color: var(--primary); box-shadow: 0 1px 4px rgba(15,31,41,.06); }

.tab-count {
  font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 9999px;
}
.count--ok      { background: rgba(22,163,74,.12); color: #16a34a; }
.count--alert   { background: rgba(83,38,0,.12);   color: var(--on-tertiary-container); }
.count--error   { background: rgba(186,26,26,.1);  color: #dc2626; }
.count--neutral { background: var(--surface-container-high); color: var(--on-surface-variant); }

/* ─── Add button ──────────────────────────────────────────────────────────────── */
.btn-add {
  display: flex; align-items: center; gap: 6px; padding: 8px 18px;
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary); border: none; border-radius: 8px;
  font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap;
  transition: opacity .15s, transform .1s;
}
.btn-add:hover  { opacity: .9; }
.btn-add:active { transform: scale(.97); }

/* ─── Stats bar ───────────────────────────────────────────────────────────────── */
.stats-bar {
  display: flex; gap: 12px; flex-wrap: wrap;
  background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.12);
  border-radius: 12px; padding: 16px 20px;
  box-shadow: 0 4px 16px rgba(15,31,41,.03);
}

.stat-chip { display: flex; align-items: center; gap: 10px; flex: 1 1 120px; }

.stat-chip__icon { font-size: 22px !important; }

.stat-chip__val { font-size: 22px; font-weight: 800; color: var(--primary); letter-spacing: -0.02em; line-height: 1; }
.stat-chip__label { font-size: 10px; font-weight: 700; color: var(--on-surface-variant); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px; }

/* ─── Filter bar ─────────────────────────────────────────────────────────────── */
.k-filter { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.k-filter__search { position: relative; flex: 1; min-width: 240px; }

.k-filter__search-icon {
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  font-size: 18px; color: var(--on-surface-variant); pointer-events: none;
}

.k-filter__input {
  width: 100%; padding: 10px 12px 10px 40px;
  background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.2); border-radius: 8px;
  font-size: 13px; font-weight: 500; color: var(--primary);
  font-family: inherit; outline: none; transition: border-color .15s;
}
.k-filter__input:focus { border-color: rgba(15,31,41,.35); }

.k-filter__right { display: flex; align-items: center; gap: 8px; }

.k-filter__select {
  padding: 10px 14px; background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.2); border-radius: 8px;
  font-size: 13px; font-weight: 500; color: var(--primary);
  font-family: inherit; outline: none; cursor: pointer;
}

.btn-reset-sm {
  display: flex; align-items: center; padding: 9px;
  background: var(--surface-container-high); border: none;
  border-radius: 8px; color: var(--on-surface-variant); cursor: pointer;
  transition: background .12s, color .12s;
}
.btn-reset-sm:hover { background: var(--surface-variant); color: var(--primary); }

/* ─── Table card ────────────────────────────────────────────────────────────── */
.k-table-card {
  background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.12); border-radius: 12px;
  box-shadow: 0 8px 30px rgba(15,31,41,.04); overflow: hidden;
}

.k-table { width: 100%; border-collapse: collapse; font-size: 13px; }

/* THEAD */
.k-table thead tr { background: rgba(240,245,244,.5); }

.k-table th {
  padding: 13px 16px; font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--on-surface-variant); white-space: nowrap;
  user-select: none; text-align: left;
}

.k-table th.col-aksi { text-align: right; }

.sortable { cursor: pointer; }
.sortable:hover { color: var(--primary); }

.sort-icon { font-size: 14px !important; vertical-align: middle; margin-left: 2px; }

.col-no   { width: 44px; }
.col-plat { width: 150px; }
.col-owner{ width: 170px; }
.col-reg  { width: 120px; }
.col-aksi { width: 100px; }

/* TBODY */
.k-row {
  border-bottom: 1px solid rgba(195,199,203,.06);
  transition: background .1s;
}
.k-row:last-child { border-bottom: none; }
.k-row:hover { background: rgba(222,227,227,.3); }
.k-row--alt   { background: rgba(240,245,244,.2); }
.k-row--alert { background: rgba(255,220,198,.06); }

.k-row td { padding: 14px 16px; vertical-align: middle; }

.td-no   { color: var(--on-surface-variant); font-size: 12px; font-weight: 500; }
.td-region { color: var(--on-surface-variant); font-weight: 500; }
.td-date   { color: var(--on-surface-variant); font-size: 12px; font-weight: 500; }
.td-aksi   { text-align: right; }

/* Plate pill */
.plate-pill {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 4px 10px;
  background: var(--surface-container-lowest);
  border: 1px solid rgba(195,199,203,.3);
  border-radius: 4px; box-shadow: 0 1px 4px rgba(15,31,41,.04);
  font-family: 'Courier New', monospace; font-size: 13px;
  font-weight: 700; color: var(--primary); letter-spacing: 0.06em;
  white-space: nowrap;
}
.plate-pill--alert { border-color: rgba(255,183,134,.5); }

/* Owner info */
.owner-info { display: flex; align-items: center; gap: 8px; }

.owner-avatar {
  width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #fff; flex-shrink: 0;
}

/* Type pill */
.type-pill {
  padding: 3px 8px; background: var(--surface-container-low);
  border: 1px solid rgba(195,199,203,.2); border-radius: 4px;
  font-size: 11px; font-weight: 600; color: var(--on-surface-variant);
}

/* Status pill */
.status-pill {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 3px 9px; border-radius: 9999px;
  font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em;
}
.sp--ok    { background: rgba(22,163,74,.1);  color: #16a34a; }
.sp--alert { background: rgba(83,38,0,.12);   color: var(--on-tertiary-container); }
.sp--error { background: rgba(186,26,26,.1);  color: #dc2626; }

/* Action buttons */
.action-btns { display: flex; align-items: center; justify-content: flex-end; gap: 4px; opacity: 0; transition: opacity .12s; }
.k-row:hover .action-btns { opacity: 1; }

.action-btn {
  display: flex; align-items: center; padding: 5px;
  background: none; border: none; cursor: pointer;
  color: var(--on-surface-variant); border-radius: 5px;
  transition: background .12s, color .12s;
}
.action-btn:hover { background: var(--surface-container-low); color: var(--primary); }
.action-btn--flag:hover  { color: var(--on-tertiary-container); }
.action-btn--flagged     { color: var(--on-tertiary-container); }
.action-btn--del:hover   { color: #dc2626; }

/* Skeleton */
.skel-row td { padding: 18px 16px; }
@keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
.skel {
  height: 11px; border-radius: 4px;
  background: linear-gradient(90deg, var(--surface-container-low) 25%, var(--surface-container-high) 50%, var(--surface-container-low) 75%);
  background-size: 200% 100%; animation: shimmer 1.4s infinite;
}
.skel--xs { width: 24px; } .skel--sm { width: 80px; } .skel--md { width: 130px; }

/* Empty */
.empty-cell { padding: 0 !important; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 52px; color: var(--on-surface-variant); font-size: 13px; }

/* ─── Pagination ─────────────────────────────────────────────────────────────── */
.k-pagination {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 12px; padding: 12px 18px;
  border-top: 1px solid rgba(195,199,203,.1);
}
.k-pagination__info { font-size: 12px; color: var(--on-surface-variant); font-weight: 500; }
.k-pagination__info strong { color: var(--primary); font-weight: 700; }
.k-pagination__controls { display: flex; gap: 4px; }

.page-btn {
  width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
  border-radius: 6px; border: none; background: var(--surface-container-high);
  color: var(--primary); font-size: 12px; font-weight: 700; cursor: pointer;
  transition: background .12s;
}
.page-btn:hover:not(:disabled) { background: var(--surface-variant); }
.page-btn:disabled { opacity: .4; cursor: not-allowed; }
.page-btn--active  { background: var(--primary); color: var(--on-primary); }

.page-ellipsis { width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; color: var(--on-surface-variant); font-size: 13px; }

/* ─── Modal ──────────────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(15,31,41,.3);
  backdrop-filter: blur(3px); z-index: 300;
  display: flex; align-items: center; justify-content: center; padding: 20px;
}

.modal {
  background: var(--surface-container-lowest);
  border-radius: 14px; box-shadow: 0 20px 60px rgba(15,31,41,.15);
  width: 100%; max-width: 520px; overflow: hidden;
  display: flex; flex-direction: column;
}
.modal--sm { max-width: 380px; }

.modal__header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px; border-bottom: 1px solid rgba(195,199,203,.12); }
.modal__title  { font-size: 16px; font-weight: 700; color: var(--primary); }
.modal__close  { display: flex; align-items: center; background: none; border: none; cursor: pointer; color: var(--on-surface-variant); padding: 4px; border-radius: 50%; transition: background .12s, color .12s; }
.modal__close:hover { background: var(--surface-container-low); color: var(--primary); }

.modal__body { padding: 20px 24px; display: flex; flex-direction: column; gap: 16px; }

.modal__footer { padding: 16px 24px; border-top: 1px solid rgba(195,199,203,.12); display: flex; gap: 10px; justify-content: flex-end; }

/* Form fields */
.form-field { display: flex; flex-direction: column; gap: 4px; }
.form-row   { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }

.form-label {
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--on-surface-variant);
}

.form-input {
  width: 100%; padding: 9px 12px;
  background: var(--surface-container-low); border: none;
  border-bottom: 2px solid transparent; border-radius: 6px 6px 0 0;
  font-size: 13px; font-weight: 500; color: var(--primary); font-family: inherit;
  outline: none; transition: border-color .15s; resize: none;
}
.form-input:focus { border-bottom-color: var(--primary); }
.form-input--mono { font-family: 'Courier New', monospace; font-size: 14px; font-weight: 700; letter-spacing: 0.05em; }
.form-input--textarea { border-radius: 6px; border: 1px solid rgba(195,199,203,.2); }

.form-select {
  width: 100%; padding: 9px 12px;
  background: var(--surface-container-low); border: none;
  border-bottom: 2px solid transparent; border-radius: 6px 6px 0 0;
  font-size: 13px; font-weight: 500; color: var(--primary); font-family: inherit;
  outline: none; cursor: pointer; appearance: none; transition: border-color .15s;
}
.form-select:focus { border-bottom-color: var(--primary); }

/* Status radios */
.status-radios { display: flex; gap: 8px; }

.radio-opt {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 5px;
  padding: 8px 12px; border-radius: 7px; border: 1.5px solid rgba(195,199,203,.25);
  font-size: 11px; font-weight: 700; cursor: pointer;
  background: var(--surface-container-lowest); color: var(--on-surface-variant);
  transition: all .12s;
}

.radio-opt--active.radio-opt--whitelist { border-color: #16a34a; background: rgba(22,163,74,.08); color: #16a34a; }
.radio-opt--active.radio-opt--watchlist { border-color: var(--on-tertiary-container); background: rgba(83,38,0,.08); color: var(--on-tertiary-container); }
.radio-opt--active.radio-opt--blacklist { border-color: #dc2626; background: rgba(186,26,26,.08); color: #dc2626; }

/* Modal footer buttons */
.btn-cancel {
  padding: 9px 18px; background: var(--surface-container-high);
  border: none; border-radius: 7px; font-size: 12px; font-weight: 700;
  color: var(--on-surface-variant); cursor: pointer; transition: background .12s;
}
.btn-cancel:hover { background: var(--surface-variant); }

.btn-save {
  display: flex; align-items: center; gap: 5px; padding: 9px 18px;
  background: linear-gradient(135deg, var(--primary), var(--primary-container));
  color: var(--on-primary); border: none; border-radius: 7px;
  font-size: 12px; font-weight: 700; cursor: pointer; transition: opacity .15s;
}
.btn-save:hover:not(:disabled)  { opacity: .88; }
.btn-save:disabled { opacity: .45; cursor: not-allowed; }

.btn-delete {
  display: flex; align-items: center; gap: 5px; padding: 9px 18px;
  background: #dc2626; color: #fff; border: none; border-radius: 7px;
  font-size: 12px; font-weight: 700; cursor: pointer; transition: opacity .15s;
}
.btn-delete:hover { opacity: .88; }

.delete-confirm__text { font-size: 13px; color: var(--on-surface-variant); line-height: 1.6; }

/* Modal transition */
.modal-enter-active, .modal-leave-active { transition: opacity .2s; }
.modal-enter-active .modal, .modal-leave-active .modal { transition: transform .22s cubic-bezier(0.4,0,0.2,1); }
.modal-enter-from { opacity: 0; }
.modal-enter-from .modal { transform: scale(.95) translateY(10px); }
.modal-leave-to { opacity: 0; }
.modal-leave-to .modal { transform: scale(.95) translateY(10px); }

.hidden { display: none; }
</style>
