/**
 * src/router/index.js
 * Vue Router — all application routes.
 */

import { createRouter, createWebHistory } from 'vue-router'

// Lazy-loaded views for code-splitting
const DashboardView      = () => import('@/views/DashboardView.vue')
const LiveMonitorView    = () => import('@/views/LiveMonitorView.vue')
const RiwayatView        = () => import('@/views/RiwayatView.vue')
const KendaraanView      = () => import('@/views/KendaraanView.vue')
const UploadView         = () => import('@/views/UploadView.vue')
const PengaturanView     = () => import('@/views/PengaturanView.vue')
const NotFoundView       = () => import('@/views/NotFoundView.vue')

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { title: 'Dashboard — ALPR Indonesia' },
  },
  {
    path: '/live',
    name: 'live-monitor',
    component: LiveMonitorView,
    meta: { title: 'Live Monitor — ALPR Indonesia' },
  },
  {
    path: '/riwayat',
    name: 'riwayat',
    component: RiwayatView,
    meta: { title: 'Riwayat Deteksi — ALPR Indonesia' },
  },
  {
    path: '/kendaraan',
    name: 'kendaraan',
    component: KendaraanView,
    meta: { title: 'Database Kendaraan — ALPR Indonesia' },
  },
  {
    path: '/upload',
    name: 'upload',
    component: UploadView,
    meta: { title: 'Upload Deteksi — ALPR Indonesia' },
  },
  {
    path: '/pengaturan',
    name: 'pengaturan',
    component: PengaturanView,
    meta: { title: 'Pengaturan Kamera — ALPR Indonesia' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFoundView,
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// Update document title on navigation
router.afterEach((to) => {
  document.title = to.meta.title || 'ALPR Indonesia'
})

export default router
