<template>
  <!--
    SourceBreakdown — Doughnut chart for detection source type.
    Also shows top-5 regions bar mini list.
  -->
  <div class="breakdown-card">
    <!-- Header -->
    <div class="breakdown-card__header">
      <h3 class="breakdown-card__title">Sumber & Wilayah</h3>
      <span class="label-xs">{{ periodLabel }}</span>
    </div>

    <!-- Source doughnut -->
    <div class="breakdown-section">
      <p class="breakdown-section__label">Sumber Deteksi</p>
      <div class="doughnut-wrap">
        <Doughnut
          v-if="sourceChartData.datasets[0].data.some(v => v > 0)"
          :data="sourceChartData"
          :options="doughnutOptions"
          class="doughnut-canvas"
        />
        <div v-else class="breakdown-empty">—</div>

        <!-- Center label -->
        <div class="doughnut-center">
          <span class="doughnut-center__value">{{ totalDetections.toLocaleString('id-ID') }}</span>
          <span class="doughnut-center__label">Total</span>
        </div>
      </div>

      <!-- Source legend pills -->
      <div class="source-pills">
        <div v-for="(item, i) in sourceItems" :key="i" class="source-pill">
          <span class="source-pill__dot" :style="{ background: sourceColors[i] }"></span>
          <span class="source-pill__name">{{ item.label }}</span>
          <span class="source-pill__count">{{ item.count.toLocaleString('id-ID') }}</span>
        </div>
      </div>
    </div>

    <!-- Divider -->
    <div class="breakdown-divider"></div>

    <!-- Top regions -->
    <div class="breakdown-section">
      <p class="breakdown-section__label">Top Wilayah</p>
      <div class="region-list">
        <div
          v-for="(r, i) in topRegions"
          :key="r.region_code"
          class="region-item"
        >
          <span class="region-item__rank">{{ i + 1 }}</span>
          <div class="region-item__info">
            <span class="region-item__code">{{ r.region_code }}</span>
            <span class="region-item__name">{{ r.region }}</span>
          </div>
          <div class="region-item__bar-wrap">
            <div
              class="region-item__bar"
              :style="{ width: barWidth(r.count) + '%' }"
            ></div>
          </div>
          <span class="region-item__count">{{ r.count.toLocaleString('id-ID') }}</span>
        </div>
        <div v-if="!topRegions.length" class="breakdown-empty">Tidak ada data</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Chart as ChartJS, ArcElement, Tooltip } from 'chart.js'
import { Doughnut } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip)

const props = defineProps({
  sourceData: { type: Array, default: () => [] },  // [{ source, count }]
  regionData: { type: Array, default: () => [] },  // [{ region_code, region, count }]
  days:       { type: Number, default: 7 },
})

const periodLabel = computed(() => `${props.days} hari terakhir`)

const sourceColors = ['#0f1f29', '#16a34a', '#ffb786', '#74777c']
const sourceLabelMap = {
  upload:      'Upload',
  stream:      'Live Stream',
  video_batch: 'Video Batch',
}

const sourceItems = computed(() => {
  const known = ['upload', 'stream', 'video_batch']
  return known.map(key => {
    const found = props.sourceData.find(d => d.source === key)
    return { label: sourceLabelMap[key] ?? key, count: found?.count ?? 0 }
  })
})

const totalDetections = computed(() =>
  sourceItems.value.reduce((sum, s) => sum + s.count, 0)
)

const sourceChartData = computed(() => ({
  labels:   sourceItems.value.map(s => s.label),
  datasets: [{
    data:            sourceItems.value.map(s => s.count),
    backgroundColor: sourceColors,
    borderWidth:     0,
    hoverOffset:     4,
  }],
}))

const doughnutOptions = {
  responsive:          true,
  maintainAspectRatio: false,
  cutout:              '72%',
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#ffffff',
      titleColor:      '#0f1f29',
      bodyColor:       '#43474b',
      borderColor:     'rgba(195,199,203,0.3)',
      borderWidth:     1,
      padding:         10,
    },
  },
}

const topRegions = computed(() =>
  [...props.regionData].sort((a, b) => b.count - a.count).slice(0, 5)
)

const maxCount = computed(() =>
  topRegions.value.reduce((m, r) => Math.max(m, r.count), 1)
)

function barWidth(count) {
  return Math.round((count / maxCount.value) * 100)
}
</script>

<style scoped>
/* ─── Card ───────────────────────────────────────────────────────────────────── */
.breakdown-card {
  background-color: var(--surface-container-lowest);
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(15, 31, 41, 0.025);
  border: 1px solid rgba(195, 199, 203, 0.2);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ─── Header ─────────────────────────────────────────────────────────────────── */
.breakdown-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.breakdown-card__title {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -0.01em;
}

.label-xs {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--on-surface-variant);
}

/* ─── Section ────────────────────────────────────────────────────────────────── */
.breakdown-section { display: flex; flex-direction: column; gap: 12px; }

.breakdown-section__label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--on-surface-variant);
}

/* ─── Doughnut ───────────────────────────────────────────────────────────────── */
.doughnut-wrap {
  position: relative;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.doughnut-canvas {
  width: 120px !important;
  height: 120px !important;
}

.doughnut-center {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
}

.doughnut-center__value {
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.02em;
}

.doughnut-center__label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--on-surface-variant);
}

/* ─── Source pills ───────────────────────────────────────────────────────────── */
.source-pills { display: flex; flex-direction: column; gap: 6px; }

.source-pill {
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-pill__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.source-pill__name {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
  color: var(--on-surface-variant);
}

.source-pill__count {
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}

/* ─── Divider ────────────────────────────────────────────────────────────────── */
.breakdown-divider {
  height: 1px;
  background-color: rgba(195, 199, 203, 0.18);
}

/* ─── Region list ────────────────────────────────────────────────────────────── */
.region-list { display: flex; flex-direction: column; gap: 8px; }

.region-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.region-item__rank {
  font-size: 10px;
  font-weight: 800;
  color: var(--on-surface-variant);
  width: 14px;
  text-align: center;
}

.region-item__info {
  display: flex;
  flex-direction: column;
  width: 60px;
  flex-shrink: 0;
}

.region-item__code {
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  font-variant-numeric: tabular-nums;
}

.region-item__name {
  font-size: 10px;
  color: var(--on-surface-variant);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.region-item__bar-wrap {
  flex: 1;
  height: 5px;
  background-color: var(--surface-container-high);
  border-radius: 9999px;
  overflow: hidden;
}

.region-item__bar {
  height: 100%;
  background-color: var(--primary);
  border-radius: 9999px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.region-item__count {
  font-size: 11px;
  font-weight: 700;
  color: var(--on-surface-variant);
  font-variant-numeric: tabular-nums;
  min-width: 36px;
  text-align: right;
}

.breakdown-empty {
  font-size: 12px;
  color: var(--on-surface-variant);
  padding: 8px 0;
  text-align: center;
}
</style>
