<template>
  <!-- ========================================================
       TopNav — Vigilant Light Design System
       Fixed 64px topbar, right-offset by sidebar width
       ======================================================== -->
  <header class="topnav">
    <!-- Page title / breadcrumb -->
    <div class="topnav-left">
      <h2 class="topnav-title">{{ pageTitle }}</h2>
    </div>

    <!-- Actions right side -->
    <div class="topnav-right">
      <!-- Notification + Settings icons -->
      <div class="topnav-icons">
        <button
          class="icon-btn"
          :class="{ 'icon-btn--alert': alertCount > 0 }"
          title="Notifikasi"
          @click="$emit('notifications')"
        >
          <span class="material-symbols-outlined">notifications</span>
          <span v-if="alertCount > 0" class="alert-dot">{{ alertCount }}</span>
        </button>

        <RouterLink to="/pengaturan" class="icon-btn" title="Pengaturan">
          <span class="material-symbols-outlined">settings</span>
        </RouterLink>
      </div>

      <!-- Live Monitor CTA -->
      <RouterLink to="/live" class="btn-live">
        <span class="material-symbols-outlined" style="font-size:16px">videocam</span>
        Live Monitor
      </RouterLink>

      <!-- User avatar placeholder -->
      <div class="avatar" title="Operator">
        <span class="material-symbols-outlined" style="font-size:18px;color:var(--on-primary)">person</span>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useStatsStore } from '@/stores/stats'

defineEmits(['notifications'])

const route      = useRoute()
const statsStore = useStatsStore()

// Map route names → display titles
const titleMap = {
  'dashboard':    'Dashboard',
  'live-monitor': 'Live Monitor',
  'riwayat':      'Riwayat Deteksi',
  'kendaraan':    'Database Kendaraan',
  'upload':       'Upload & Deteksi',
  'pengaturan':   'Pengaturan Kamera',
}

const pageTitle = computed(() =>
  titleMap[route.name] || 'ALPR Indonesia'
)

const alertCount = computed(() =>
  statsStore.summary?.watchlist_hits || 0
)
</script>

<style scoped>
/* ─── TopNav shell ───────────────────────────────────────────────────────────── */
.topnav {
  position: fixed;
  top: 0;
  left: var(--sidebar-width, 256px);
  right: 0;
  height: var(--topbar-height, 64px);
  z-index: 40;

  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;

  background-color: var(--surface);
  /* No shadow — let background tone do the work (Vigilant Light principle) */
  border-bottom: 1px solid rgba(195, 199, 203, 0.15);
}

/* ─── Left ───────────────────────────────────────────────────────────────────── */
.topnav-left {
  display: flex;
  align-items: center;
}

.topnav-title {
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.02em;
}

/* ─── Right ──────────────────────────────────────────────────────────────────── */
.topnav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.topnav-icons {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ─── Icon buttons ───────────────────────────────────────────────────────────── */
.icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  color: #455a64;
  text-decoration: none;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.icon-btn:hover {
  background-color: var(--surface-container-highest);
  color: var(--primary);
}

.icon-btn:active {
  opacity: 0.7;
}

.icon-btn--alert {
  color: var(--on-tertiary-container);
}

/* Alert dot */
.alert-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 16px;
  height: 16px;
  background-color: var(--tertiary-fixed-dim);
  color: var(--on-tertiary-fixed);
  font-size: 9px;
  font-weight: 800;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* ─── Live Monitor button ────────────────────────────────────────────────────── */
.btn-live {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-container) 100%);
  color: var(--on-primary);
  font-size: 13px;
  font-weight: 600;
  border-radius: 6px;
  text-decoration: none;
  transition: opacity 0.15s ease, transform 0.1s ease;
  white-space: nowrap;
}

.btn-live:hover  { opacity: 0.9; }
.btn-live:active { transform: scale(0.97); opacity: 0.85; }

/* ─── Avatar ─────────────────────────────────────────────────────────────────── */
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-container), var(--primary));
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 1.5px solid rgba(195, 199, 203, 0.3);
  flex-shrink: 0;
  transition: box-shadow 0.15s ease;
}

.avatar:hover {
  box-shadow: 0 0 0 3px rgba(15, 31, 41, 0.08);
}
</style>
