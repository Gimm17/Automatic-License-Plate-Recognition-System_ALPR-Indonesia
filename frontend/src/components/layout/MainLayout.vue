<template>
  <!-- ========================================================
       MainLayout — Vigilant Light Design System
       Composes: Sidebar (fixed 256px) + TopNav (fixed 64px)
       + main content area with correct offsets
       ======================================================== -->
  <div class="layout-root">
    <!-- Fixed Sidebar -->
    <Sidebar @emergency="handleEmergency" />

    <!-- Main area (offset by sidebar) -->
    <div class="layout-main">
      <!-- Fixed TopNav -->
      <TopNav @notifications="handleNotifications" />

      <!-- Scrollable page content — slot for views that wrap MainLayout -->
      <main class="layout-content">
        <slot />
      </main>
    </div>

    <!-- Emergency Alert Toast -->
    <Transition name="slide-up">
      <div v-if="showEmergency" class="emergency-toast">
        <span class="material-symbols-outlined" style="font-size:18px">warning</span>
        <div>
          <p class="emergency-toast__title">Emergency Alert Aktif</p>
          <p class="emergency-toast__sub">Semua unit diberitahu</p>
        </div>
        <button class="emergency-toast__close" @click="showEmergency = false">
          <span class="material-symbols-outlined" style="font-size:16px">close</span>
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import TopNav from './TopNav.vue'

const showEmergency = ref(false)

function handleEmergency() {
  showEmergency.value = true
  setTimeout(() => { showEmergency.value = false }, 5000)
}

function handleNotifications() {
  // TODO: Show notifications panel
}
</script>

<style scoped>
/* ─── Layout root ────────────────────────────────────────────────────────────── */
.layout-root {
  display: flex;
  min-height: 100vh;
  background-color: var(--surface);
}

/* ─── Main area ──────────────────────────────────────────────────────────────── */
.layout-main {
  flex: 1;
  margin-left: var(--sidebar-width, 256px);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ─── Content canvas ─────────────────────────────────────────────────────────── */
.layout-content {
  flex: 1;
  margin-top: var(--topbar-height, 64px);
  padding: 32px;
  background-color: var(--surface);
  overflow-y: auto;
  min-height: calc(100vh - var(--topbar-height, 64px));
}

/* ─── Page transition ────────────────────────────────────────────────────────── */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to   { opacity: 0; transform: translateY(-4px); }

/* ─── Emergency Toast ────────────────────────────────────────────────────────── */
.emergency-toast {
  position: fixed;
  bottom: 24px;
  left: calc(var(--sidebar-width, 256px) + 24px);
  z-index: 100;

  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;

  background-color: var(--tertiary-fixed-dim);
  color: var(--on-tertiary-fixed);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(15, 31, 41, 0.15);
  font-weight: 600;
  max-width: 360px;
}

.emergency-toast__title {
  font-size: 13px;
  font-weight: 700;
}

.emergency-toast__sub {
  font-size: 11px;
  font-weight: 500;
  opacity: 0.8;
}

.emergency-toast__close {
  margin-left: auto;
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
  padding: 2px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}
.emergency-toast__close:hover { opacity: 1; }

/* ─── Toast transition ───────────────────────────────────────────────────────── */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.slide-up-enter-from { opacity: 0; transform: translateY(16px); }
.slide-up-leave-to   { opacity: 0; transform: translateY(8px); }
</style>
