<template>
  <!-- ========================================================
       Sidebar — Vigilant Light Design System
       Fixed 256px left column, bg surface-container-low
       ======================================================== -->
  <nav class="sidebar">
    <!-- Brand -->
    <div class="sidebar-brand">
      <h1 class="brand-title">ALPR Curator</h1>
      <p class="brand-sub">Technical Operations</p>
    </div>

    <!-- Nav links -->
    <div class="sidebar-nav">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-link"
        :class="{ 'nav-link--active': isActive(item) }"
        :title="item.label"
      >
        <span class="material-symbols-outlined nav-link__icon">{{ item.icon }}</span>
        <span class="nav-link__label">{{ item.label }}</span>
      </RouterLink>
    </div>

    <!-- Footer actions -->
    <div class="sidebar-footer">
      <!-- Active stream count badge -->
      <div v-if="streamCount > 0" class="stream-badge">
        <span class="live-pulse"></span>
        <span class="stream-badge__text">{{ streamCount }} Live</span>
      </div>

      <!-- Emergency alert button -->
      <button class="btn-emergency" @click="$emit('emergency')">
        <span class="material-symbols-outlined" style="font-size:16px">warning</span>
        Emergency Alert
      </button>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useStreamStore } from '@/stores/stream'

defineEmits(['emergency'])

const route       = useRoute()
const streamStore = useStreamStore()

const streamCount = computed(() => streamStore.activeCount)

const navItems = [
  { to: '/dashboard',  icon: 'dashboard',      label: 'Dashboard'  },
  { to: '/live',       icon: 'videocam',        label: 'Live Monitor' },
  { to: '/riwayat',    icon: 'history',         label: 'Riwayat'    },
  { to: '/kendaraan',  icon: 'directions_car',  label: 'Kendaraan'  },
  { to: '/upload',     icon: 'upload_file',     label: 'Upload'     },
  { to: '/pengaturan', icon: 'settings',        label: 'Pengaturan' },
]

function isActive(item) {
  return route.path === item.to || route.path.startsWith(item.to + '/')
}
</script>

<style scoped>
/* ─── Sidebar shell ──────────────────────────────────────────────────────────── */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: var(--sidebar-width, 256px);
  height: 100vh;
  z-index: 50;

  display: flex;
  flex-direction: column;
  padding: 24px 16px;

  background-color: var(--surface-container-low);
  box-shadow: 4px 0 24px rgba(15, 31, 41, 0.04);
  overflow-y: auto;
}

/* ─── Brand ──────────────────────────────────────────────────────────────────── */
.sidebar-brand {
  margin-bottom: 32px;
  padding: 0 8px;
}

.brand-title {
  font-size: 17px;
  font-weight: 900;
  color: var(--primary);
  letter-spacing: -0.01em;
}

.brand-sub {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--on-surface-variant);
  margin-top: 2px;
}

/* ─── Nav links ──────────────────────────────────────────────────────────────── */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 16px;
  border-radius: 6px;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  color: #607d8b;
  transition: color 0.15s ease, transform 0.15s ease, background-color 0.15s ease;
  user-select: none;
}

.nav-link:hover:not(.nav-link--active) {
  color: var(--primary);
  transform: translateX(4px);
}

.nav-link:active {
  transform: scale(0.97);
}

/* Active state */
.nav-link--active {
  background-color: var(--surface-container-lowest);
  color: var(--primary);
  box-shadow: 0 2px 8px rgba(15, 31, 41, 0.06);
}

.nav-link__icon {
  font-size: 20px;
  flex-shrink: 0;
  transition: color 0.15s ease;
}

.nav-link__label {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

/* ─── Footer ─────────────────────────────────────────────────────────────────── */
.sidebar-footer {
  padding-top: 16px;
  border-top: 1px solid rgba(195, 199, 203, 0.2);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stream-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: var(--surface-container);
  border-radius: 6px;
}

.stream-badge__text {
  font-size: 11px;
  font-weight: 700;
  color: var(--primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.btn-emergency {
  width: 100%;
  padding: 11px 16px;
  background-color: var(--tertiary-fixed-dim);
  color: var(--on-tertiary-fixed);
  font-size: 13px;
  font-weight: 700;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: opacity 0.15s ease, transform 0.1s ease;
}

.btn-emergency:hover { opacity: 0.9; }
.btn-emergency:active { transform: scale(0.97); }
</style>
