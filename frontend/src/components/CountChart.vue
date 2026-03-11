<template>
  <div class="flex flex-col h-full">
    <!-- Controls row -->
    <div class="flex items-center gap-2 mb-3 flex-wrap">
      <select v-model="mode"
              class="h-8 px-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 min-w-[185px]">
        <option value="brand">By Brand</option>
        <option value="top10sold">Top 10 Sold Products</option>
        <option value="top10least">Top 10 Least Sold Products</option>
        <option value="deadstock">Dead Stock (≥3 Months)</option>
        <option value="hourly">By Hour</option>
      </select>

      <!-- Product search (By Hour only) -->
      <div v-if="mode === 'hourly'" class="relative flex-1 min-w-[180px]">
        <input ref="searchInput" v-model="productSearch" type="text"
               placeholder="Search brand or product…"
               class="w-full h-8 px-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 pr-6"
               @focus="showDropdown = true" @blur="onSearchBlur" />
        <button v-if="selectedProduct" @click="clearProduct"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-600 text-xs font-bold">✕</button>
        <span v-if="selectedProduct && !showDropdown"
              class="absolute left-2 top-1/2 -translate-y-1/2 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 text-xs px-2 py-0.5 rounded pointer-events-none max-w-[90%] truncate">
          {{ selectedProduct.product_brand }} — {{ selectedProduct.product_name }}
        </span>
        <ul v-if="showDropdown && filteredProducts.length"
            class="absolute z-50 left-0 right-0 top-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded shadow-lg max-h-52 overflow-y-auto text-sm">
          <li v-for="p in filteredProducts" :key="p.class_id"
              @mousedown.prevent="selectProduct(p)"
              class="px-3 py-1.5 hover:bg-red-50 dark:hover:bg-gray-700 cursor-pointer truncate">
            <span class="text-gray-500 dark:text-gray-400 text-xs">{{ p.product_brand }}</span>
            <span class="ml-1 text-gray-800 dark:text-gray-100">{{ p.product_name }}</span>
          </li>
        </ul>
        <p v-if="showDropdown && productSearch && !filteredProducts.length"
           class="absolute z-50 left-0 right-0 top-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded shadow text-sm px-3 py-2 text-gray-400">
          No matches found
        </p>
      </div>
    </div>

    <!-- Chart canvas with fixed height so Chart.js always gets a non-zero size -->
    <div class="relative" style="height:360px;min-height:280px;">
      <canvas ref="chartCanvas" style="width:100%;height:100%;"></canvas>
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800 bg-opacity-60 dark:bg-opacity-60">
        <span class="text-sm text-gray-400 animate-pulse">Loading…</span>
      </div>
      <div v-if="!loading && emptyData" class="absolute inset-0 flex items-center justify-center">
        <span class="text-sm text-gray-400">No data for this period</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import API from '../api'

const props = defineProps({
  camera:     { type: String, default: 'cam1' },
  filter:     { type: String, default: 'day' },
  customFrom: { type: String, default: null },
  customTo:   { type: String, default: null },
  darkMode:   { type: Boolean, default: false },
})

Chart.register(...registerables)

const chartCanvas    = ref(null)
const chartInstance  = ref(null)
const mode           = ref('brand')
const loading        = ref(false)
const emptyData      = ref(false)

const searchInput     = ref(null)
const productSearch   = ref('')
const showDropdown    = ref(false)
const selectedProduct = ref(null)
const allProducts     = ref([])
let loadGen = 0

// ── Colours ───────────────────────────────────────────────────────────────────
const BRAND_COLORS = [
  '#dc2626','#ea580c','#d97706','#ca8a04','#65a30d',
  '#16a34a','#059669','#0891b2','#2563eb','#7c3aed',
  '#9333ea','#db2777','#e11d48','#f97316','#84cc16',
  '#06b6d4','#6366f1','#ec4899','#14b8a6','#f59e0b',
  '#10b981','#3b82f6','#8b5cf6','#ef4444','#22c55e',
]
const brandColor = (i) => BRAND_COLORS[i % BRAND_COLORS.length]

// Chart.js theme colours driven by darkMode prop
function textColor()   { return props.darkMode ? '#ffffff' : '#374151' }
function gridColor()   { return props.darkMode ? '#4b5563' : '#e5e7eb' }
function canvasBg()    { return props.darkMode ? '#1f2937' : '#ffffff' }

// Integer-only tick config for Y (or X for horizontal charts)
const integerTicks = { stepSize: 1, precision: 0 }

// ── Product search ─────────────────────────────────────────────────────────────
const filteredProducts = computed(() => {
  const q = productSearch.value.trim().toLowerCase()
  if (!q) return allProducts.value.slice(0, 50)
  return allProducts.value.filter(p =>
    p.product_brand.toLowerCase().includes(q) || p.product_name.toLowerCase().includes(q)
  ).slice(0, 80)
})

function selectProduct(p) {
  selectedProduct.value = p; productSearch.value = ''; showDropdown.value = false; loadChartData()
}
function clearProduct() {
  selectedProduct.value = null; productSearch.value = ''; loadChartData()
}
function onSearchBlur() { setTimeout(() => { showDropdown.value = false }, 150) }

async function fetchProducts() {
  try { const res = await API.get('/products'); allProducts.value = res.data || [] } catch (_) {}
}

// ── Date helpers ──────────────────────────────────────────────────────────────
function getStartDate(filter) {
  if (filter === 'custom' && props.customFrom) return props.customFrom
  const now = new Date()
  const map = { day: 1, week: 7, month: 30, '3months': 90, year: 365 }
  now.setDate(now.getDate() - (map[filter] || 1))
  return now.toISOString()
}
function threeMonthsAgoISO() {
  const d = new Date(); d.setDate(d.getDate() - 90); return d.toISOString()
}

// ── Chart rendering ───────────────────────────────────────────────────────────
async function loadChartData() {
  const gen = ++loadGen
  loading.value = true; emptyData.value = false

  try {
    let events = []
    if (mode.value === 'deadstock') {
      const params = { start_date: threeMonthsAgoISO(), limit: 5000 }
      if (props.camera !== 'all') params.camera_id = props.camera
      const res = await API.get('/events', { params })
      if (gen !== loadGen) return
      events = res.data || []
    } else {
      const params = { start_date: getStartDate(props.filter), limit: 5000 }
      if (props.filter === 'custom' && props.customTo) params.end_date = props.customTo
      if (props.camera !== 'all') params.camera_id = props.camera
      if (mode.value === 'hourly' && selectedProduct.value)
        params.product_name = selectedProduct.value.product_name
      const res = await API.get('/events', { params })
      if (gen !== loadGen) return
      events = res.data || []
    }

    if (!chartCanvas.value) return
    const existing = Chart.getChart(chartCanvas.value)
    if (existing) { existing.destroy(); chartInstance.value = null }
    await nextTick()
    if (gen !== loadGen || !chartCanvas.value) return

    const ctx  = chartCanvas.value.getContext('2d')
    const tc   = textColor()
    const gc   = gridColor()

    // Common base options for bar charts
    function barOpts(title, xLabel, isHoriz = true) {
      return {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: title, color: tc, font: { size: 13 } },
          tooltip: { callbacks: { label: c => `${c.raw} ${xLabel}` } },
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: { color: tc, ...(isHoriz ? integerTicks : { font: { size: 10 } }) },
            grid: { color: gc },
            title: isHoriz ? { display: true, text: xLabel, color: tc, font: { size: 11 } } : undefined,
          },
          y: {
            ticks: {
              color: tc,
              ...(isHoriz ? { font: { size: 10 }, autoSkip: false } : integerTicks),
            },
            grid: { color: gc },
            title: !isHoriz ? { display: true, text: xLabel, color: tc, font: { size: 11 } } : undefined,
          },
        },
      }
    }

    // ── By Brand (doughnut) ───────────────────────────────────────────────────
    if (mode.value === 'brand') {
      const brandCounts = {}
      events.forEach(ev => {
        const b = ev.product_brand || 'Unknown'
        brandCounts[b] = (brandCounts[b] || 0) + 1
      })
      const sorted = Object.entries(brandCounts).sort((a, b) => b[1] - a[1])
      if (!sorted.length) { emptyData.value = true; return }
      const labels = sorted.map(([b]) => b)
      const data   = sorted.map(([, c]) => c)
      const total  = data.reduce((s, v) => s + v, 0)
      chartInstance.value = new Chart(ctx, {
        type: 'doughnut',
        data: { labels, datasets: [{ data, backgroundColor: labels.map((_, i) => brandColor(i)), borderWidth: 1 }] },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { position: 'right', labels: { color: tc, font: { size: 11 }, boxWidth: 12 } },
            title: { display: true, text: 'Detections by Brand', color: tc, font: { size: 13 } },
            tooltip: { callbacks: { label: c => `${c.label}: ${c.raw} (${total ? ((c.raw/total)*100).toFixed(1) : 0}%)` } },
          },
        },
      })

    // ── Top 10 Sold ───────────────────────────────────────────────────────────
    } else if (mode.value === 'top10sold') {
      const soldCounts = {}
      events.forEach(ev => {
        if (ev.event_type !== 'sold') return
        const k = `${ev.product_brand || 'Unknown'} — ${ev.product_name || 'Unnamed'}`
        soldCounts[k] = (soldCounts[k] || 0) + 1
      })
      const sorted = Object.entries(soldCounts).sort((a, b) => b[1] - a[1]).slice(0, 10)
      if (!sorted.length) { emptyData.value = true; return }
      const labels = sorted.map(([l]) => l)
      const data   = sorted.map(([, c]) => c)
      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Total Sold', data, backgroundColor: labels.map((_, i) => brandColor(i)), borderWidth: 1 }] },
        options: { ...barOpts('Top 10 Best-Selling Products', 'Total Sold', true), indexAxis: 'y' },
      })

    // ── Top 10 Least Sold ─────────────────────────────────────────────────────
    } else if (mode.value === 'top10least') {
      const seenProducts = {}
      events.forEach(ev => {
        const k = `${ev.product_brand || 'Unknown'} — ${ev.product_name || 'Unnamed'}`
        if (!seenProducts[k]) seenProducts[k] = { sold: 0 }
        if (ev.event_type === 'sold') seenProducts[k].sold++
      })
      const sorted = Object.entries(seenProducts).sort((a, b) => a[1].sold - b[1].sold).slice(0, 10)
      if (!sorted.length) { emptyData.value = true; return }
      const labels = sorted.map(([k]) => k)
      const data   = sorted.map(([, d]) => d.sold)
      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Total Sold', data, backgroundColor: labels.map((_, i) => brandColor(i)), borderWidth: 1 }] },
        options: { ...barOpts('Top 10 Least Sold Products', 'Total Sold', true), indexAxis: 'y' },
      })

    // ── Dead Stock ────────────────────────────────────────────────────────────
    } else if (mode.value === 'deadstock') {
      const seenMap = {}; const soldSet = new Set()
      events.forEach(ev => {
        const k = `${ev.product_brand || 'Unknown'} — ${ev.product_name || 'Unnamed'}`
        if (!seenMap[k]) seenMap[k] = { detected: 0 }
        seenMap[k].detected++
        if (ev.event_type === 'sold') soldSet.add(k)
      })
      const deadstock = Object.entries(seenMap).filter(([k]) => !soldSet.has(k))
        .sort((a, b) => b[1].detected - a[1].detected)
      if (!deadstock.length) { emptyData.value = true; return }
      const labels = deadstock.map(([k]) => k)
      const data   = deadstock.map(([, d]) => d.detected)
      const opts   = barOpts(`Dead Stock — ${deadstock.length} product(s) not sold in 3 months`, 'Total Detections', true)
      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Total Detections', data, backgroundColor: '#94a3b8', borderWidth: 1 }] },
        options: { ...opts, indexAxis: 'y' },
      })

    // ── By Hour ────────────────────────────────────────────────────────────────
    } else if (mode.value === 'hourly') {
      const hourlyCounts = new Array(24).fill(0)
      events.forEach(ev => {
        if (!ev.ts) return
        const wibHour = (new Date(ev.ts).getUTCHours() + 7) % 24
        hourlyCounts[wibHour]++
      })
      const maxCount = Math.max(...hourlyCounts, 1)
      const colors   = hourlyCounts.map(c => `rgba(220,38,38,${0.25 + (c / maxCount) * 0.75})`)
      const titleText = selectedProduct.value
        ? `By Hour — ${selectedProduct.value.product_brand} · ${selectedProduct.value.product_name}`
        : 'Events by Hour of Day (WIB)'

      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`),
          datasets: [{ label: 'Event Count', data: hourlyCounts, backgroundColor: colors, borderWidth: 1 }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: { display: true, text: titleText, color: tc, font: { size: 12 } },
            tooltip: { callbacks: { label: c => `${c.raw} events` } },
          },
          scales: {
            x: { ticks: { color: tc, font: { size: 10 } }, grid: { color: gc },
                 title: { display: true, text: 'Hour (WIB)', color: tc, font: { size: 11 } } },
            y: { beginAtZero: true, ticks: { color: tc, ...integerTicks }, grid: { color: gc },
                 title: { display: true, text: 'Event Count', color: tc, font: { size: 11 } } },
          },
        },
      })
    }
  } catch (err) {
    console.error('CountChart error:', err)
  } finally {
    if (gen === loadGen) loading.value = false
  }
}

onMounted(() => { fetchProducts(); loadChartData() })
watch(() => [props.camera, props.filter, props.customFrom, props.customTo, props.darkMode], loadChartData)
watch(mode, () => { if (mode.value === 'hourly') fetchProducts(); loadChartData() })
onUnmounted(() => {
  const ex = chartCanvas.value ? Chart.getChart(chartCanvas.value) : null
  if (ex) ex.destroy()
})
</script>
