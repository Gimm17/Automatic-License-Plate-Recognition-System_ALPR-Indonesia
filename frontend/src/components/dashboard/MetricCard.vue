<template>
  <!--
    MetricCard — Vigilant Light Design System
    Reusable stat card with label, value, trend, icon, and alert accent.
  -->
  <div class="metric-card" :class="{ 'metric-card--alert': alert }">
    <!-- Header: label + icon -->
    <div class="metric-card__header">
      <span class="metric-card__label">{{ label }}</span>
      <span
        class="metric-card__icon"
        :class="alert ? 'metric-card__icon--alert' : ''"
      >
        <span class="material-symbols-outlined">{{ icon }}</span>
      </span>
    </div>

    <!-- Value -->
    <div class="metric-card__body">
      <div class="metric-card__value">
        {{ formattedValue }}<span v-if="unit" class="metric-card__unit">{{ unit }}</span>
      </div>

      <!-- Trend row -->
      <div class="metric-card__trend" v-if="trend !== null">
        <span
          class="metric-card__trend-badge"
          :class="trendPositive ? 'metric-card__trend-badge--up' : 'metric-card__trend-badge--down'"
        >
          <span class="material-symbols-outlined" style="font-size:13px">
            {{ trendPositive ? 'trending_up' : 'trending_down' }}
          </span>
          {{ Math.abs(trend) }}{{ trendUnit }}
        </span>
        <span class="metric-card__trend-label">{{ trendLabel }}</span>
      </div>
      <div v-else class="metric-card__trend-label">{{ subLabel }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label:     { type: String, required: true },
  value:     { type: [Number, String], required: true },
  unit:      { type: String, default: '' },
  icon:      { type: String, default: 'bar_chart' },
  alert:     { type: Boolean, default: false },
  trend:     { type: Number, default: null },
  trendUnit: { type: String, default: '%' },
  trendLabel:{ type: String, default: 'vs kemarin' },
  subLabel:  { type: String, default: '' },
})

const trendPositive = computed(() => (props.trend ?? 0) >= 0)

const formattedValue = computed(() => {
  if (typeof props.value === 'number' && props.value >= 1000) {
    return props.value.toLocaleString('id-ID')
  }
  return props.value
})
</script>

<style scoped>
/* ─── Card shell ─────────────────────────────────────────────────────────────── */
.metric-card {
  background-color: var(--surface-container-lowest);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(15, 31, 41, 0.025);
  border: 1px solid rgba(195, 199, 203, 0.2);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 16px;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.metric-card:hover {
  box-shadow: 0 12px 32px rgba(15, 31, 41, 0.06);
  transform: translateY(-1px);
}

/* Alert variant — orange left accent bar */
.metric-card--alert {
  border: none;
  border-left: 4px solid var(--tertiary-fixed-dim);
  padding-left: 20px;
}

/* ─── Header ─────────────────────────────────────────────────────────────────── */
.metric-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.metric-card__label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--on-surface-variant);
}

.metric-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: 6px;
  background-color: var(--surface-container-low);
  color: var(--on-secondary-container);
  transition: background-color 0.2s;
}

.metric-card__icon--alert {
  background-color: var(--tertiary-fixed);
  color: var(--on-tertiary-container);
}

.metric-card__icon .material-symbols-outlined {
  font-size: 18px;
}

/* ─── Body ───────────────────────────────────────────────────────────────────── */
.metric-card__body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-card__value {
  font-size: 30px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.02em;
  line-height: 1;
}

.metric-card--alert .metric-card__value {
  color: var(--on-tertiary-container);
}

.metric-card__unit {
  font-size: 16px;
  font-weight: 500;
  color: var(--secondary);
  margin-left: 4px;
}

/* ─── Trend ──────────────────────────────────────────────────────────────────── */
.metric-card__trend {
  display: flex;
  align-items: center;
  gap: 6px;
}

.metric-card__trend-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  font-weight: 700;
}

.metric-card__trend-badge--up   { color: #16a34a; }
.metric-card__trend-badge--down { color: #dc2626; }

.metric-card__trend-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--secondary);
}
</style>
