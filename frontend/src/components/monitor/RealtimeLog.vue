<template>
  <!--
    RealtimeLog — Scrolling live detection feed for the monitor sidebar.
    New entries slide in from the top with animation.
  -->
  <div class="rtlog">
    <!-- Header -->
    <div class="rtlog__header">
      <h3 class="rtlog__title">Realtime Logs</h3>
      <span class="live-pulse" title="Live"></span>
    </div>

    <!-- Entries list -->
    <div class="rtlog__list" ref="listRef">
      <TransitionGroup name="log-item" tag="div" class="rtlog__inner">
        <div
          v-for="entry in entries"
          :key="entry.id"
          class="rtlog__entry"
          :class="{
            'rtlog__entry--alert':     entry.status === 'watchlist',
            'rtlog__entry--unreadable': entry.status === 'ocr_failed',
          }"
        >
          <!-- Left accent bar for watchlist -->
          <div v-if="entry.status === 'watchlist'" class="entry-accent"></div>

          <!-- Thumbnail -->
          <div class="entry-thumb">
            <img
              v-if="entry.crop_url"
              :src="entry.crop_url"
              :alt="entry.plate_text"
              loading="lazy"
            />
            <span v-else class="material-symbols-outlined thumb-fallback">image</span>
          </div>

          <!-- Info -->
          <div class="entry-info">
            <div class="entry-top">
              <span
                class="entry-plate"
                :class="{ 'entry-plate--muted': entry.status === 'ocr_failed' }"
              >
                {{ entry.plate_text || 'Unreadable' }}
              </span>
              <span
                class="entry-badge"
                :class="relTimeBadgeClass(entry.status)"
              >
                {{ entry.status === 'watchlist' ? 'FLAGGED' : relTime(entry.detected_at) }}
              </span>
            </div>

            <!-- Tags row: camera + confidence / status tag -->
            <div class="entry-tags">
              <span class="tag tag--cam">{{ entry.camera_label || `CAM-${entry.camera_id}` }}</span>
              <span
                class="tag"
                :class="confTagClass(entry)"
              >
                {{ confTagLabel(entry) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Empty placeholder -->
        <div v-if="!entries.length" key="empty" class="rtlog__empty">
          <span class="material-symbols-outlined" style="font-size:24px;opacity:.25">
            history
          </span>
          <p>Menunggu deteksi…</p>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  entries: { type: Array, default: () => [] }, // max ~50 items, newest first
})

const listRef = ref(null)

// Auto-scroll to top when new entry arrives
watch(() => props.entries.length, async () => {
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = 0
})

function relTime(ts) {
  if (!ts) return '—'
  const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 1000)
  if (diff < 10)  return 'Just now'
  if (diff < 60)  return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

function relTimeBadgeClass(status) {
  if (status === 'watchlist') return 'badge--alert'
  return 'badge--time'
}

function confTagClass(entry) {
  if (entry.status === 'watchlist')  return 'tag--watchlist'
  if (entry.status === 'ocr_failed') return 'tag--lowvis'
  return 'tag--conf'
}

function confTagLabel(entry) {
  if (entry.status === 'watchlist')  return 'WANTED'
  if (entry.status === 'ocr_failed') return 'LOW VIS'
  if (entry.confidence)              return `CONF ${Math.round(entry.confidence * 100)}%`
  return 'VALID'
}
</script>

<style scoped>
/* ─── Shell ──────────────────────────────────────────────────────────────────── */
.rtlog {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  border-radius: 10px;
  background-color: var(--surface-container-lowest);
  box-shadow: 0 20px 40px rgba(15, 31, 41, 0.03);
  border: 1px solid rgba(195, 199, 203, 0.2);
}

/* ─── Header ─────────────────────────────────────────────────────────────────── */
.rtlog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background-color: var(--surface-container-low);
  border-bottom: 1px solid rgba(195, 199, 203, 0.15);
  flex-shrink: 0;
}

.rtlog__title {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -0.01em;
}

/* ─── List ───────────────────────────────────────────────────────────────────── */
.rtlog__list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.rtlog__inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ─── Empty ──────────────────────────────────────────────────────────────────── */
.rtlog__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 16px;
  color: var(--on-surface-variant);
  font-size: 12px;
}

/* ─── Entry ──────────────────────────────────────────────────────────────────── */
.rtlog__entry {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  background-color: var(--surface-container-low);
  border: 1px solid rgba(195, 199, 203, 0.2);
  overflow: hidden;
  transition: background-color 0.15s ease;
}

.rtlog__entry:hover {
  background-color: var(--surface-container);
}

.rtlog__entry--alert {
  border-color: rgba(255, 183, 134, 0.5);
}

.rtlog__entry--unreadable {
  opacity: 0.65;
}

/* Alert left accent bar */
.entry-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: var(--tertiary-fixed-dim);
}

/* ─── Thumbnail ──────────────────────────────────────────────────────────────── */
.entry-thumb {
  width: 48px;
  height: 36px;
  border-radius: 4px;
  border: 1px solid rgba(195, 199, 203, 0.3);
  background-color: var(--surface-container-highest);
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.entry-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-fallback {
  font-size: 18px;
  color: var(--on-surface-variant);
  opacity: 0.4;
}

/* ─── Info ───────────────────────────────────────────────────────────────────── */
.entry-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.entry-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px;
}

.entry-plate {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: 0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entry-plate--muted {
  color: var(--on-surface-variant);
  font-style: italic;
  font-weight: 500;
}

.entry-badge {
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}

.badge--time  { color: var(--on-surface-variant); }
.badge--alert { color: var(--on-tertiary-container); }

/* ─── Tags ───────────────────────────────────────────────────────────────────── */
.entry-tags {
  display: flex;
  gap: 5px;
}

.tag {
  padding: 1px 6px;
  border-radius: 2px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.tag--cam       { background-color: var(--surface-container-highest); color: var(--on-surface-variant); }
.tag--conf      { background-color: var(--secondary-container);       color: var(--on-secondary-container); }
.tag--watchlist { background-color: rgba(83,38,0,0.1);               color: var(--on-tertiary-container); }
.tag--lowvis    { background-color: var(--surface-variant);           color: var(--on-surface-variant); }

/* ─── Transition: new log item slides in from top ────────────────────────────── */
.log-item-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.log-item-leave-active {
  transition: all 0.2s ease;
  position: absolute;
  width: calc(100% - 24px);
}
.log-item-enter-from {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
}
.log-item-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
.log-item-move {
  transition: transform 0.3s ease;
}
</style>
