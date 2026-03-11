<template>
  <div class="flex flex-col h-full">
    <!-- Controls row: dropdown + optional product search -->
    <div class="flex items-center gap-2 mb-3 flex-wrap">
      <select v-model="mode"
              class="h-8 px-2 py-0.5 border border-gray-300 rounded text-sm bg-gray-100 text-gray-800 min-w-[180px]">
        <option value="brand">By Brand</option>
        <option value="top10sold">Top 10 Sold Products</option>
        <option value="top10least">Top 10 Least Sold Products</option>
        <option value="deadstock">Dead Stock (≥3 Months)</option>
        <option value="hourly">By Hour</option>
      </select>

      <!-- Product search — only visible when By Hour is selected -->
      <div v-if="mode === 'hourly'" class="relative flex-1 min-w-[180px]">
        <input
          ref="searchInput"
          v-model="productSearch"
          type="text"
          placeholder="Search brand or product…"
          class="w-full h-8 px-2 py-0.5 border border-gray-300 rounded text-sm bg-gray-100 text-gray-800"
          @focus="showDropdown = true"
          @blur="onSearchBlur"
        />
        <!-- Clear button -->
        <button v-if="selectedProduct"
                @click="clearProduct"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-600 text-xs font-bold">
          ✕
        </button>
        <!-- Selected product chip -->
        <span v-if="selectedProduct && !showDropdown"
              class="absolute left-2 top-1/2 -translate-y-1/2 bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded pointer-events-none max-w-[90%] truncate">
          {{ selectedProduct.product_brand }} — {{ selectedProduct.product_name }}
        </span>
        <!-- Dropdown results -->
        <ul v-if="showDropdown && filteredProducts.length"
            class="absolute z-50 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded shadow-lg max-h-52 overflow-y-auto text-sm">
          <li v-for="p in filteredProducts" :key="p.class_id"
              @mousedown.prevent="selectProduct(p)"
              class="px-3 py-1.5 hover:bg-red-50 cursor-pointer truncate">
            <span class="text-gray-500 text-xs">{{ p.product_brand }}</span>
            <span class="ml-1 text-gray-800">{{ p.product_name }}</span>
          </li>
        </ul>
        <p v-if="showDropdown && productSearch && !filteredProducts.length"
           class="absolute z-50 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded shadow text-sm px-3 py-2 text-gray-400">
          No matches found
        </p>
      </div>
    </div>

    <!-- Chart container -->
    <div class="relative flex-1 min-h-0">
      <canvas ref="chartCanvas" class="w-full h-full"></canvas>
      <div v-if="loading"
           class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-60">
        <span class="text-sm text-gray-400 animate-pulse">Loading…</span>
      </div>
      <div v-if="!loading && emptyData"
           class="absolute inset-0 flex items-center justify-center">
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
})

Chart.register(...registerables)

const chartCanvas    = ref(null)
const chartInstance  = ref(null)
const mode           = ref('brand')
const loading        = ref(false)
const emptyData      = ref(false)

// Product search (By Hour mode)
const searchInput    = ref(null)
const productSearch  = ref('')
const showDropdown   = ref(false)
const selectedProduct = ref(null)
const allProducts    = ref([])

let loadGen = 0

// ── Colour palette ────────────────────────────────────────────────────────────
const BRAND_COLORS = [
  '#dc2626','#ea580c','#d97706','#ca8a04','#65a30d',
  '#16a34a','#059669','#0891b2','#2563eb','#7c3aed',
  '#9333ea','#db2777','#e11d48','#f97316','#84cc16',
  '#06b6d4','#6366f1','#ec4899','#14b8a6','#f59e0b',
  '#10b981','#3b82f6','#8b5cf6','#ef4444','#22c55e',
]
const brandColor = (i) => BRAND_COLORS[i % BRAND_COLORS.length]

// ── Product search helpers ────────────────────────────────────────────────────
const filteredProducts = computed(() => {
  if (!productSearch.value.trim()) return allProducts.value.slice(0, 50)
  const q = productSearch.value.toLowerCase()
  return allProducts.value.filter(p =>
    p.product_brand.toLowerCase().includes(q) ||
    p.product_name.toLowerCase().includes(q)
  ).slice(0, 80)
})

function selectProduct(p) {
  selectedProduct.value = p
  productSearch.value   = ''
  showDropdown.value    = false
  loadChartData()
}

function clearProduct() {
  selectedProduct.value = null
  productSearch.value   = ''
  loadChartData()
}

function onSearchBlur() {
  setTimeout(() => { showDropdown.value = false }, 150)
}

async function fetchProducts() {
  try {
    const res = await API.get('/products')
    allProducts.value = res.data || []
  } catch (_) {}
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
  const d = new Date()
  d.setDate(d.getDate() - 90)
  return d.toISOString()
}

// ── Chart rendering ───────────────────────────────────────────────────────────
async function loadChartData() {
  const gen = ++loadGen
  loading.value   = true
  emptyData.value = false

  try {
    let events = []

    if (mode.value === 'deadstock') {
      // Always last 3 months regardless of filter selection
      const params = { start_date: threeMonthsAgoISO(), limit: 5000 }
      if (props.camera !== 'all') params.camera_id = props.camera
      const res = await API.get('/events', { params })
      if (gen !== loadGen) return
      events = Array.isArray(res.data) ? res.data : []
    } else {
      const params = { start_date: getStartDate(props.filter), limit: 5000 }
      if (props.filter === 'custom' && props.customTo) params.end_date = props.customTo
      if (props.camera !== 'all') params.camera_id = props.camera
      // For hourly with specific product, add product name filter
      if (mode.value === 'hourly' && selectedProduct.value) {
        params.product_name = selectedProduct.value.product_name
      }
      const res = await API.get('/events', { params })
      if (gen !== loadGen) return
      events = Array.isArray(res.data) ? res.data : []
    }

    if (!chartCanvas.value) return

    const existing = Chart.getChart(chartCanvas.value)
    if (existing) { existing.destroy(); chartInstance.value = null }

    await nextTick()
    if (gen !== loadGen || !chartCanvas.value) return

    const ctx = chartCanvas.value.getContext('2d')

    // ── By Brand (doughnut) ──────────────────────────────────────────────────
    if (mode.value === 'brand') {
      const brandCounts = {}
      events.forEach(ev => {
        const brand = ev.product_brand || 'Unknown'
        brandCounts[brand] = (brandCounts[brand] || 0) + 1
      })
      const sorted = Object.entries(brandCounts).sort((a, b) => b[1] - a[1])
      if (!sorted.length) { emptyData.value = true; loading.value = false; return }

      const labels = sorted.map(([b]) => b)
      const data   = sorted.map(([, c]) => c)
      const total  = data.reduce((s, v) => s + v, 0)
      const colors = labels.map((_, i) => brandColor(i))

      chartInstance.value = new Chart(ctx, {
        type: 'doughnut',
        data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 1 }] },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { position: 'right', labels: { font: { size: 11 }, boxWidth: 12 } },
            tooltip: {
              callbacks: {
                label: c => {
                  const pct = total ? ((c.raw / total) * 100).toFixed(1) : 0
                  return `${c.label}: ${c.raw} (${pct}%)`
                },
              },
            },
          },
        },
      })

    // ── Top 10 Sold Products (horizontal bar) ────────────────────────────────
    } else if (mode.value === 'top10sold') {
      const soldCounts = {}
      events.forEach(ev => {
        if (ev.event_type !== 'sold') return
        const key = `${ev.product_brand || 'Unknown'} — ${ev.product_name || 'Unnamed'}`
        soldCounts[key] = (soldCounts[key] || 0) + 1
      })
      const sorted = Object.entries(soldCounts).sort((a, b) => b[1] - a[1]).slice(0, 10)
      if (!sorted.length) { emptyData.value = true; loading.value = false; return }

      const labels = sorted.map(([l]) => l)
      const data   = sorted.map(([, c]) => c)
      const colors = labels.map((_, i) => brandColor(i))

      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Units Sold', data, backgroundColor: colors, borderWidth: 1 }] },
        options: {
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: { display: true, text: 'Top 10 Best-Selling Products', font: { size: 13 } },
            tooltip: { callbacks: { label: c => `${c.raw} sold` } },
          },
          scales: {
            x: { beginAtZero: true },
            y: { ticks: { font: { size: 10 }, autoSkip: false } },
          },
        },
      })

    // ── Top 10 Least Sold Products (horizontal bar) ──────────────────────────
    } else if (mode.value === 'top10least') {
      // Count sold events per product; show 10 with lowest sold count (incl. 0)
      const seenProducts = {}  // key → { brand, name, sold }
      events.forEach(ev => {
        const key = ev.product_name || 'Unnamed'
        if (!seenProducts[key]) seenProducts[key] = { brand: ev.product_brand || 'Unknown', sold: 0 }
        if (ev.event_type === 'sold') seenProducts[key].sold++
      })
      const sorted = Object.entries(seenProducts)
        .sort((a, b) => a[1].sold - b[1].sold)
        .slice(0, 10)
      if (!sorted.length) { emptyData.value = true; loading.value = false; return }

      const labels = sorted.map(([name, d]) => `${d.brand} — ${name}`)
      const data   = sorted.map(([, d]) => d.sold)
      const colors = labels.map((_, i) => brandColor(i))

      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Units Sold', data, backgroundColor: colors, borderWidth: 1 }] },
        options: {
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: { display: true, text: 'Top 10 Least Sold Products', font: { size: 13 } },
            tooltip: { callbacks: { label: c => `${c.raw} sold` } },
          },
          scales: {
            x: { beginAtZero: true },
            y: { ticks: { font: { size: 10 }, autoSkip: false } },
          },
        },
      })

    // ── Dead Stock ────────────────────────────────────────────────────────────
    } else if (mode.value === 'deadstock') {
      // Products seen in events but with ZERO sold events in last 3 months
      const seenMap = {}  // product_name → { brand, detected, lastSeen }
      const soldSet  = new Set()

      events.forEach(ev => {
        const key = ev.product_name || 'Unnamed'
        if (!seenMap[key]) seenMap[key] = { brand: ev.product_brand || 'Unknown', detected: 0, lastSeen: ev.ts }
        seenMap[key].detected++
        if (ev.ts > seenMap[key].lastSeen) seenMap[key].lastSeen = ev.ts
        if (ev.event_type === 'sold') soldSet.add(key)
      })

      const deadstock = Object.entries(seenMap)
        .filter(([name]) => !soldSet.has(name))
        .sort((a, b) => b[1].detected - a[1].detected)

      if (!deadstock.length) { emptyData.value = true; loading.value = false; return }

      const labels = deadstock.map(([name, d]) => `${d.brand} — ${name}`)
      const data   = deadstock.map(([, d]) => d.detected)
      const colors = labels.map(() => '#94a3b8')  // slate — "stale" colour

      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Detections (no sales)', data, backgroundColor: colors, borderWidth: 1 }] },
        options: {
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: {
              display: true,
              text: `Dead Stock — ${deadstock.length} product(s) not sold in 3 months`,
              font: { size: 13 },
            },
            tooltip: {
              callbacks: {
                label: c => `${c.raw} detections (0 sales in 3 months)`,
              },
            },
          },
          scales: {
            x: { beginAtZero: true },
            y: { ticks: { font: { size: 10 }, autoSkip: false } },
          },
        },
      })

    // ── By Hour ───────────────────────────────────────────────────────────────
    } else if (mode.value === 'hourly') {
      const hourlyCounts = new Array(24).fill(0)
      events.forEach(ev => {
        if (!ev.ts) return
        const wibHour = (new Date(ev.ts).getUTCHours() + 7) % 24
        hourlyCounts[wibHour]++
      })
      const maxCount = Math.max(...hourlyCounts, 1)
      const colors = hourlyCounts.map(c => {
        const intensity = c / maxCount
        return `rgba(220,38,38,${0.25 + intensity * 0.75})`
      })
      const titleText = selectedProduct.value
        ? `Sales by Hour — ${selectedProduct.value.product_brand} · ${selectedProduct.value.product_name}`
        : 'Detections by Hour of Day (WIB) — All Products'

      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`),
          datasets: [{
            label: 'Events',
            data: hourlyCounts,
            backgroundColor: colors,
            borderWidth: 1,
            borderColor: colors.map(c => c.replace(/[\d.]+\)$/, '1)')),
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: { display: true, text: titleText, font: { size: 12 } },
            tooltip: { callbacks: { label: c => `${c.raw} events` } },
          },
          scales: {
            x: { ticks: { font: { size: 10 } } },
            y: { beginAtZero: true },
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

onMounted(() => {
  fetchProducts()
  loadChartData()
})

watch(() => [props.camera, props.filter, props.customFrom, props.customTo], loadChartData)
watch(mode, () => {
  if (mode.value === 'hourly') {
    fetchProducts()
  }
  loadChartData()
})

onUnmounted(() => {
  const existing = chartCanvas.value ? Chart.getChart(chartCanvas.value) : null
  if (existing) existing.destroy()
})
</script>
