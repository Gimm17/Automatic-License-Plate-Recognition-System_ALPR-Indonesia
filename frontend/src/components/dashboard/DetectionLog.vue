<template>
  <!--
    DetectionLog — Recent detections sidebar list
    Used in Dashboard right column, following design reference Item 1/2/3 pattern.
  -->
  <div class="detection-log">
    <!-- Header -->
    <div class="detection-log__header">
      <h3 class="detection-log__title">Deteksi Terbaru</h3>
      <button class="detection-log__refresh" @click="$emit('refresh')" title="Refresh">
        <span class="material-symbols-outlined" :class="{ 'spin': loading }">refresh</span>
      </button>
    </div>

    <!-- List -->
    <div class="detection-log__list">
      <!-- Empty state -->
      <div v-if="!items.length && !loading" class="detection-log__empty">
        <span class="material-symbols-outlined" style="font-size:32px;opacity:.3">
          search_off
        </span>
        <p>Belum ada deteksi</p>
      </div>

      <!-- Skeleton loading -->
      <template v-if="loading">
        <div v-for="i in 5" :key="i" class="detection-log__skeleton">
          <div class="skeleton-thumb"></div>
          <div class="skeleton-lines">
            <div class="skeleton-line skeleton-line--wide"></div>
            <div class="skeleton-line skeleton-line--short"></div>
          </div>
        </div>
      </template>

      <!-- Real items -->
      <template v-else>
        <div
          v-for="item in items"
          :key="item.id"
          class="detection-log__item"
          :class="{
            'detection-log__item--alert': item.status === 'watchlist',
            'detection-log__item--invalid': item.status === 'ocr_failed' || item.status === 'invalid',
          }"
          @click="$emit('select', item)"
        >
          <!-- Plate thumbnail -->
          <div class="detection-log__thumb">
            <img
              v-if="item.crop_url"
              :src="item.crop_url"
              :alt="item.plate_text"
              loading="lazy"
            />
            <span v-else class="material-symbols-outlined thumb-icon">
              directions_car
            </span>
          </div>

          <!-- Plate info -->
          <div class="detection-log__info">
            <div class="detection-log__plate">{{ item.plate_text || '—' }}</div>
            <div class="detection-log__time">{{ formatTime(item.detected_at) }}</div>
          </div>

          <!-- Status icon -->
          <span class="detection-log__status">
            <span
              class="material-symbols-outlined status-icon"
              :class="statusClass(item.status)"
            >
              {{ statusIcon(item.status) }}
            </span>
          </span>
        </div>
      </template>
    </div>

    <!-- Footer: view all link -->
    <div class="detection-log__footer">
      <RouterLink to="/riwayat" class="detection-log__viewall">
        Lihat semua
        <span class="material-symbols-outlined" style="font-size:14px">arrow_forward</span>
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items:   { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})
defineEmits(['refresh', 'select'])

function formatTime(ts) {
  if (!ts) return '—'
  const d = new Date(ts)
  return d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function statusIcon(status) {
  const map = {
    valid:      'check_circle',
    watchlist:  'warning',
    invalid:    'cancel',
    ocr_failed: 'help',
  }
  return map[status] ?? 'radio_button_unchecked'
}

function statusClass(status) {
  const map = {
    valid:      'status-icon--valid',
    watchlist:  'status-icon--alert',
    invalid:    'status-icon--error',
    ocr_failed: 'status-icon--muted',
  }
  return map[status] ?? ''
}
</script>

<style scoped>
/* ─── Shell ──────────────────────────────────────────────────────────────────── */
.detection-log {
  background-color: var(--surface-container-lowest);
  border-radius: 10px;
  border: 1px solid rgba(195, 199, 203, 0.2);
  box-shadow: 0 20px 40px rgba(15, 31, 41, 0.025);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ─── Header ─────────────────────────────────────────────────────────────────── */
.detection-log__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(195, 199, 203, 0.12);
}

.detection-log__title {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -0.01em;
}

.detection-log__refresh {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--on-surface-variant);
  padding: 4px;
  border-radius: 50%;
  transition: background-color 0.15s, color 0.15s;
}
.detection-log__refresh:hover {
  background-color: var(--surface-container-high);
  color: var(--primary);
}
.detection-log__refresh .material-symbols-outlined { font-size: 18px; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 0.7s linear infinite; }

/* ─── List ───────────────────────────────────────────────────────────────────── */
.detection-log__list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* ─── Empty ──────────────────────────────────────────────────────────────────── */
.detection-log__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 20px;
  color: var(--on-surface-variant);
  font-size: 12px;
}

/* ─── Item ───────────────────────────────────────────────────────────────────── */
.detection-log__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.12s ease;
}
.detection-log__item:hover {
  background-color: var(--surface-container-low);
}

/* Alert variant */
.detection-log__item--alert {
  border-left: 3px solid var(--tertiary-fixed-dim);
  padding-left: 9px;
}
.detection-log__item--invalid {
  opacity: 0.7;
}

/* ─── Thumbnail ──────────────────────────────────────────────────────────────── */
.detection-log__thumb {
  width: 48px;
  height: 32px;
  border-radius: 4px;
  background-color: var(--surface-container-high);
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.detection-log__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumb-icon {
  font-size: 18px;
  color: var(--on-surface-variant);
  opacity: 0.5;
}

/* ─── Info ───────────────────────────────────────────────────────────────────── */
.detection-log__info {
  flex: 1;
  min-width: 0;
}
.detection-log__plate {
  font-family: 'Courier New', 'Courier', monospace;
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: 0.03em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.detection-log__time {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--on-surface-variant);
  margin-top: 2px;
}

/* ─── Status icons ───────────────────────────────────────────────────────────── */
.status-icon {
  font-size: 18px;
}
.status-icon--valid  { color: #16a34a; }
.status-icon--alert  { color: var(--tertiary-fixed-dim); }
.status-icon--error  { color: #dc2626; }
.status-icon--muted  { color: var(--on-surface-variant); }

/* ─── Skeleton ───────────────────────────────────────────────────────────────── */
.detection-log__skeleton {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.skeleton-thumb,
.skeleton-line {
  background: linear-gradient(90deg,
    var(--surface-container-low) 25%,
    var(--surface-container-high) 50%,
    var(--surface-container-low) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  border-radius: 4px;
}
.skeleton-thumb { width: 48px; height: 32px; flex-shrink: 0; }
.skeleton-lines { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.skeleton-line       { height: 10px; }
.skeleton-line--wide  { width: 70%; }
.skeleton-line--short { width: 40%; }

/* ─── Footer ─────────────────────────────────────────────────────────────────── */
.detection-log__footer {
  padding: 12px 20px;
  border-top: 1px solid rgba(195, 199, 203, 0.12);
}
.detection-log__viewall {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--on-surface-variant);
  text-decoration: none;
  transition: color 0.15s;
}
.detection-log__viewall:hover { color: var(--primary); }
</style>
