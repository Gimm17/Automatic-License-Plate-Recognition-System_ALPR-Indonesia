<template>
  <!--
    DetectionChart — 7-day line chart using Chart.js
    Shows daily total, valid, and watchlist detections.
  -->
  <div class="chart-card">
    <!-- Header -->
    <div class="chart-card__header">
      <div>
        <h3 class="chart-card__title">Tren Deteksi</h3>
        <p class="chart-card__sub">7 hari terakhir</p>
      </div>
      <div class="chart-card__legend">
        <span class="legend-dot legend-dot--total"></span><span class="legend-label">Total</span>
        <span class="legend-dot legend-dot--valid"></span><span class="legend-label">Valid</span>
        <span class="legend-dot legend-dot--alert"></span><span class="legend-label">Watchlist</span>
      </div>
    </div>

    <!-- Chart canvas -->
    <div class="chart-card__canvas-wrap">
      <Line
        v-if="chartData.datasets.length"
        :data="chartData"
        :options="chartOptions"
        class="chart-canvas"
      />
      <div v-else class="chart-card__empty">
        <span class="material-symbols-outlined" style="font-size:28px;opacity:.25">
          bar_chart
        </span>
        <p>Memuat data chart…</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale, LinearScale,
  PointElement, LineElement,
  Filler, Tooltip, Legend
)

const props = defineProps({
  data: { type: Array, default: () => [] }, // [{ date, total, valid, watchlist }]
})

const chartData = computed(() => {
  if (!props.data.length) return { labels: [], datasets: [] }

  const labels  = props.data.map(d => {
    const dt = new Date(d.date)
    return dt.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
  })

  return {
    labels,
    datasets: [
      {
        label:           'Total',
        data:            props.data.map(d => d.total),
        borderColor:     '#0f1f29',
        backgroundColor: 'rgba(15,31,41,0.06)',
        borderWidth:     2,
        pointRadius:     3,
        pointHoverRadius: 5,
        tension:         0.4,
        fill:            true,
      },
      {
        label:           'Valid',
        data:            props.data.map(d => d.valid),
        borderColor:     '#16a34a',
        backgroundColor: 'rgba(22,163,74,0.04)',
        borderWidth:     2,
        pointRadius:     2,
        pointHoverRadius: 4,
        tension:         0.4,
        fill:            false,
      },
      {
        label:           'Watchlist',
        data:            props.data.map(d => d.watchlist),
        borderColor:     '#ffb786',
        backgroundColor: 'rgba(255,183,134,0.08)',
        borderWidth:     2,
        pointRadius:     3,
        pointHoverRadius: 5,
        tension:         0.4,
        fill:            false,
      },
    ],
  }
})

const chartOptions = {
  responsive:          true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#ffffff',
      titleColor:      '#0f1f29',
      bodyColor:       '#43474b',
      borderColor:     'rgba(195,199,203,0.3)',
      borderWidth:     1,
      padding:         12,
      boxPadding:      4,
      usePointStyle:   true,
    },
  },
  scales: {
    x: {
      grid: { display: false },
      border: { display: false },
      ticks: {
        font:  { size: 11, family: 'Inter' },
        color: '#74777c',
      },
    },
    y: {
      grid: {
        color: 'rgba(195,199,203,0.15)',
        drawBorder: false,
      },
      border: { display: false, dash: [4, 4] },
      ticks: {
        font:    { size: 11, family: 'Inter' },
        color:   '#74777c',
        padding: 8,
      },
    },
  },
}
</script>

<style scoped>
/* ─── Card ───────────────────────────────────────────────────────────────────── */
.chart-card {
  background-color: var(--surface-container-lowest);
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(15, 31, 41, 0.025);
  border: 1px solid rgba(195, 199, 203, 0.2);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ─── Header ─────────────────────────────────────────────────────────────────── */
.chart-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.chart-card__title {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -0.01em;
}

.chart-card__sub {
  font-size: 11px;
  color: var(--on-surface-variant);
  margin-top: 2px;
}

/* ─── Legend ─────────────────────────────────────────────────────────────────── */
.chart-card__legend {
  display: flex;
  align-items: center;
  gap: 12px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.legend-dot--total  { background-color: #0f1f29; }
.legend-dot--valid  { background-color: #16a34a; }
.legend-dot--alert  { background-color: #ffb786; }

.legend-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--on-surface-variant);
}

/* ─── Canvas ─────────────────────────────────────────────────────────────────── */
.chart-card__canvas-wrap {
  position: relative;
  height: 180px;
}

.chart-canvas {
  width: 100% !important;
  height: 100% !important;
}

.chart-card__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  color: var(--on-surface-variant);
  font-size: 12px;
}
</style>
