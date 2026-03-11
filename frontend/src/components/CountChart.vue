<template>
  <div>
    <!-- Toggle buttons -->
    <div class="flex gap-2 mb-3 flex-wrap">
      <button @click="mode = 'products'"
              :class="mode === 'products' ? 'bg-red-600 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'">
        All Products
      </button>
      <button @click="mode = 'doughnut'"
              :class="mode === 'doughnut' ? 'bg-red-600 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'">
        Brand Share
      </button>
      <button @click="mode = 'top20'"
              :class="mode === 'top20' ? 'bg-red-600 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'">
        Top 20 Products
      </button>
      <button @click="mode = 'brand'"
              :class="mode === 'brand' ? 'bg-red-600 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'">
        Group by Brand
      </button>
      <button @click="mode = 'hourly'"
              :class="mode === 'hourly' ? 'bg-red-600 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'">
        By Hour
      </button>
    </div>

    <!-- Chart container -->
    <div class="w-full h-[460px]">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import API from '../api'

const props = defineProps({
  camera:     { type: String, default: 'cam1' },
  filter:     { type: String, default: 'day' },
  customFrom: { type: String, default: null },
  customTo:   { type: String, default: null },
})

Chart.register(...registerables)

const chartCanvas = ref(null)
const chartInstance = ref(null)
const mode = ref('products')
let loadGen = 0  // generation counter — cancels stale async loadChartData calls

// Brand colour palette — consistent per brand across all chart types
const BRAND_COLORS = [
  '#dc2626','#ea580c','#d97706','#ca8a04','#65a30d',
  '#16a34a','#059669','#0891b2','#2563eb','#7c3aed',
  '#9333ea','#db2777','#e11d48','#f97316','#84cc16',
  '#06b6d4','#6366f1','#ec4899','#14b8a6','#f59e0b',
  '#10b981','#3b82f6','#8b5cf6','#ef4444','#22c55e',
]

function brandColor(index) {
  return BRAND_COLORS[index % BRAND_COLORS.length]
}

function getStartDate(filter) {
  if (filter === 'custom' && props.customFrom) return props.customFrom
  const now = new Date()
  const map = { day: 1, week: 7, month: 30, '3months': 90, year: 365 }
  now.setDate(now.getDate() - (map[filter] || 1))
  return now.toISOString()
}

async function loadChartData() {
  const gen = ++loadGen  // stamp this call; if a newer call starts, this one aborts after await
  try {
    const params = { start_date: getStartDate(props.filter) }
    if (props.filter === 'custom' && props.customTo) params.end_date = props.customTo
    if (props.camera !== 'all') params.camera_id = props.camera
    const res = await API.get('/events', { params })

    if (gen !== loadGen) return  // stale — a newer call is already running, discard

    const events = Array.isArray(res.data) ? res.data : []

    if (!chartCanvas.value) return  // component unmounted during await

    const existing = Chart.getChart(chartCanvas.value)
    if (existing) existing.destroy()
    chartInstance.value = null

    const ctx = chartCanvas.value.getContext('2d')

    if (mode.value === 'products') {
      // Top 20 products doughnut — segment size = total detections, tooltip shows sold count
      const totalCounts = {}
      const soldCounts  = {}
      events.forEach(ev => {
        const key = ev.product_name || 'Unknown'
        totalCounts[key] = (totalCounts[key] || 0) + 1
        if (ev.event_type === 'sold') soldCounts[key] = (soldCounts[key] || 0) + 1
      })
      const sorted = Object.entries(totalCounts).sort((a, b) => b[1] - a[1]).slice(0, 20)
      const labels = sorted.map(([p]) => p)
      const data   = sorted.map(([, c]) => c)
      const sold   = labels.map(p => soldCounts[p] || 0)
      const colors = labels.map((_, i) => brandColor(i))

      chartInstance.value = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels,
          datasets: [{ data, backgroundColor: colors, borderWidth: 1 }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'right', labels: { font: { size: 11 } } },
            tooltip: {
              callbacks: {
                label: c => {
                  const totalAll = data.reduce((s, v) => s + v, 0)
                  const pct = totalAll ? ((c.raw / totalAll) * 100).toFixed(1) : 0
                  return [`Total: ${c.raw} (${pct}%)`, `Sold: ${sold[c.dataIndex]}`]
                },
              },
            },
          },
        },
      })

    } else if (mode.value === 'doughnut') {
      const brandCounts = {}
      events.forEach(ev => {
        const brand = ev.product_brand || 'Unknown'
        brandCounts[brand] = (brandCounts[brand] || 0) + 1
      })
      const sorted = Object.entries(brandCounts).sort((a, b) => b[1] - a[1])
      const labels = sorted.map(([b]) => b)
      const data   = sorted.map(([, c]) => c)
      const colors = labels.map((_, i) => brandColor(i))

      chartInstance.value = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels,
          datasets: [{ data, backgroundColor: colors, borderWidth: 1 }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'right', labels: { font: { size: 11 } } },
            tooltip: {
              callbacks: {
                label: c => {
                  const total = data.reduce((s, v) => s + v, 0)
                  const pct = total ? ((c.raw / total) * 100).toFixed(1) : 0
                  return `${c.label}: ${c.raw} (${pct}%)`
                },
              },
            },
          },
        },
      })

    } else if (mode.value === 'hourly') {
      // Group by WIB hour (UTC+7)
      const hourlyCounts = new Array(24).fill(0)
      events.forEach(ev => {
        if (!ev.ts) return
        const wibHour = (new Date(ev.ts).getUTCHours() + 7) % 24
        hourlyCounts[wibHour]++
      })
      const maxCount = Math.max(...hourlyCounts, 1)
      // Colour intensity: lighter = fewer, darker = more
      const colors = hourlyCounts.map(c => {
        const intensity = c / maxCount
        const r = Math.round(220 - intensity * 80)
        const g = Math.round(38 - intensity * 20)
        const b = Math.round(38 - intensity * 20)
        return `rgba(${r},${g},${b},${0.3 + intensity * 0.7})`
      })

      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`),
          datasets: [{
            label: 'Detections',
            data: hourlyCounts,
            backgroundColor: colors,
            borderWidth: 1,
            borderColor: colors.map(c => c.replace(/[\d.]+\)$/, '1)')),
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: {
              display: true,
              text: 'Detections by Hour of Day (WIB)',
              font: { size: 13 },
            },
            tooltip: {
              callbacks: {
                label: c => `${c.raw} detections`,
              },
            },
          },
          scales: {
            x: { ticks: { font: { size: 10 } } },
            y: { beginAtZero: true },
          },
        },
      })

    } else {
      // 'top20' or 'brand' — horizontal bar chart
      let counts = {}
      if (mode.value === 'brand') {
        events.forEach(ev => {
          const brand = ev.product_brand || 'Unknown'
          counts[brand] = (counts[brand] || 0) + 1
        })
      } else {
        events.forEach(ev => {
          const brand   = ev.product_brand || 'Unknown'
          const product = ev.product_name  || 'Unnamed'
          counts[`${brand} — ${product}`] = (counts[`${brand} — ${product}`] || 0) + 1
        })
      }

      let sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])
      if (mode.value === 'top20') sorted = sorted.slice(0, 20)

      const labels = sorted.map(([l]) => l)
      const data   = sorted.map(([, c]) => c)
      const colors = labels.map((_, i) => brandColor(i))

      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Detections',
            data,
            backgroundColor: colors,
            borderWidth: 1,
          }],
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: c => `${c.raw} detections`,
              },
            },
          },
          scales: {
            x: { beginAtZero: true },
            y: { ticks: { font: { size: 11 }, autoSkip: false } },
          },
        },
      })
    }
  } catch (err) {
    console.error('CountChart error:', err)
  }
}

onMounted(loadChartData)
watch(() => [props.camera, props.filter, props.customFrom, props.customTo], loadChartData)
watch(mode, loadChartData)

onUnmounted(() => {
  const existing = Chart.getChart(chartCanvas.value)
  if (existing) existing.destroy()
})
</script>
