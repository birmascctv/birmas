<template>
  <div class="flex flex-col h-full">
    <div class="flex items-center gap-2 mb-2 flex-wrap">
      <h2 class="text-base sm:text-lg font-semibold text-red-600">Customer Traffic</h2>
      <span class="ml-auto inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full"
            :class="storeActive ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                                 : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'">
        <span class="w-2 h-2 rounded-full" :class="storeActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'"></span>
        {{ storeActive ? 'Store Active' : 'No Recent Activity' }}
      </span>
    </div>
    <p class="text-xs text-gray-400 dark:text-gray-500 mb-2">
      {{ lastActivityLabel }}
    </p>

    <div class="relative" style="height:280px;min-height:220px;">
      <canvas ref="chartCanvas" style="width:100%;height:100%;"></canvas>
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800 bg-opacity-60 dark:bg-opacity-60">
        <span class="text-sm text-gray-400 animate-pulse">Loading…</span>
      </div>
      <div v-if="!loading && emptyData" class="absolute inset-0 flex items-center justify-center">
        <span class="text-sm text-gray-400">No people-detection data yet</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import API from '../api'

const props = defineProps({
  filter:     { type: String, default: 'day' },
  camera:     { type: String, default: 'all' },
  customFrom: { type: String, default: null },
  customTo:   { type: String, default: null },
  darkMode:   { type: Boolean, default: false },
})

Chart.register(...registerables)

const chartCanvas   = ref(null)
const loading       = ref(false)
const emptyData     = ref(false)
const storeActive   = ref(false)
const lastActivityTs = ref(null)
let statusTimer = null
let loadGen = 0

function textColor() { return props.darkMode ? '#ffffff' : '#374151' }
function gridColor() { return props.darkMode ? '#4b5563' : '#e5e7eb' }

function getStartDate(filter) {
  if (filter === 'custom' && props.customFrom) return props.customFrom
  if (filter === 'day') {
    // "Today" = start of today in WIB (Jakarta local time), not a rolling
    // 24-hour window — matches TimelineScrubber's day-boundary convention
    // (naive datetime string, compared directly against the naive-WIB
    // timestamps stored in the DB).
    const now = new Date()
    const wib = new Date(now.getTime() + (now.getTimezoneOffset() + 7 * 60) * 60000)
    const pad = n => String(n).padStart(2, '0')
    return `${wib.getFullYear()}-${pad(wib.getMonth() + 1)}-${pad(wib.getDate())}T00:00:00`
  }
  const now = new Date()
  const map = { week: 7, month: 30, '3months': 90, year: 365 }
  now.setDate(now.getDate() - (map[filter] || 7))
  return now.toISOString()
}

// Picks a "nice" axis step/max for large scales — e.g. max=340 -> step=100,
// max=3400, max=45 (small) falls back to the fixed 0-100/step-10 look.
// Uses a classic 1/2/5-times-power-of-ten stepping so gridlines land on
// round numbers no matter how big the counts get (hundreds, thousands...).
function niceStep(maxValue) {
  const rough = maxValue / 8  // aim for ~8 gridlines
  const pow10 = Math.pow(10, Math.floor(Math.log10(rough || 1)))
  const candidates = [1, 2, 5, 10]
  let step = pow10 * 10
  for (const c of candidates) {
    if (rough <= c * pow10) { step = c * pow10; break }
  }
  return step
}

const lastActivityLabel = ref('Checking store activity…')
function updateLastActivityLabel() {
  if (!lastActivityTs.value) { lastActivityLabel.value = 'No activity recorded yet'; return }
  const d = new Date(lastActivityTs.value)
  lastActivityLabel.value = `Last activity: ${d.toLocaleString('en-GB', { hour12: false })}`
}

async function fetchStoreStatus() {
  try {
    const res = await API.get('/store-status')
    storeActive.value = !!res.data.active
    lastActivityTs.value = res.data.last_activity
    updateLastActivityLabel()
  } catch (_) {}
}

async function loadChart() {
  const gen = ++loadGen
  loading.value = true; emptyData.value = false
  try {
    const params = { start_date: getStartDate(props.filter) }
    if (props.filter === 'custom' && props.customTo) params.end_date = props.customTo
    if (props.camera && props.camera !== 'all') params.camera_id = props.camera
    const res = await API.get('/people-events/hourly', { params })
    if (gen !== loadGen) return
    const { hours, in_counts, out_counts } = res.data

    if (!in_counts.some(v => v > 0) && !out_counts.some(v => v > 0)) {
      emptyData.value = true
    }

    if (!chartCanvas.value) return
    const existing = Chart.getChart(chartCanvas.value)
    if (existing) existing.destroy()
    await nextTick()
    if (gen !== loadGen || !chartCanvas.value) return

    const ctx = chartCanvas.value.getContext('2d')
    const tc  = textColor()
    const gc  = gridColor()

    // Switch bar -> line once any hourly count exceeds 100 (fixed 0-100 bar
    // scale no longer fits) — a line chart reads better than bars once the
    // range stretches into the hundreds, and lets the y-axis grow as wide
    // as the data needs instead of clipping/squashing at a fixed ceiling.
    const maxCount = Math.max(0, ...in_counts, ...out_counts)
    const useLine  = maxCount > 100

    let yMax, yStep
    if (useLine) {
      yStep = niceStep(maxCount)
      yMax  = Math.ceil((maxCount + 1) / yStep) * yStep
    } else {
      yMax  = 100
      yStep = 10
    }

    new Chart(ctx, {
      type: useLine ? 'line' : 'bar',
      data: {
        labels: hours,
        datasets: useLine
          ? [
              { label: 'In',  data: in_counts,  borderColor: '#2563eb', backgroundColor: '#2563eb', pointRadius: 2, tension: 0.25, fill: false },
              { label: 'Out', data: out_counts, borderColor: '#dc2626', backgroundColor: '#dc2626', pointRadius: 2, tension: 0.25, fill: false },
            ]
          : [
              { label: 'In',  data: in_counts,  backgroundColor: '#2563eb', borderWidth: 1 },
              { label: 'Out', data: out_counts, backgroundColor: '#dc2626', borderWidth: 1 },
            ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: tc } },
          tooltip: { callbacks: { label: c => `${c.dataset.label}: ${c.raw}` } },
        },
        scales: {
          x: { stacked: false, ticks: { color: tc, font: { size: 10 } }, grid: { color: gc } },
          y: {
            // Fixed 0-100/step-10 while counts stay small (per user
            // preference, keeps day-to-day scale consistent). Once any
            // hourly count tops 100, switch to an auto-growing "nice"
            // range/step (100s, 1000s, ...) so the line chart never clips.
            min: 0, max: yMax,
            ticks: { color: tc, stepSize: yStep, precision: 0 },
            grid: { color: gc },
            title: { display: true, text: 'People count', color: tc, font: { size: 11 } },
          },
        },
      },
    })
  } catch (err) {
    console.error('PeopleTrafficChart error:', err)
  } finally {
    if (gen === loadGen) loading.value = false
  }
}

onMounted(() => {
  loadChart()
  fetchStoreStatus()
  statusTimer = setInterval(fetchStoreStatus, 60_000)  // refresh status every minute
})
watch(() => [props.filter, props.customFrom, props.customTo, props.darkMode], loadChart)
onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer)
  const ex = chartCanvas.value ? Chart.getChart(chartCanvas.value) : null
  if (ex) ex.destroy()
})
</script>
