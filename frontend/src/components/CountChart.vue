<template>
  <div>
    <!-- Toggle buttons -->
    <div class="flex gap-2 mb-4">
      <button @click="mode = 'all'"
              :class="mode === 'all' ? 'bg-red-600 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'">
        All Products (Treemap)
      </button>
      <button @click="mode = 'top20'"
              :class="mode === 'top20' ? 'bg-red-600 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'">
        Top 20 Products
      </button>
      <button @click="mode = 'brand'"
              :class="mode === 'brand' ? 'bg-red-600 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'">
        Group by Brand
      </button>
    </div>

    <!-- Breadcrumb trail -->
    <div v-if="mode === 'all'" class="mb-2 text-sm">
      <span class="cursor-pointer text-blue-600" @click="resetTreemap">All Products</span>
      <span v-if="drilledBrand"> > {{ drilledBrand }}</span>
    </div>

    <!-- Chart container -->
    <div class="w-full h-[600px]">
      <canvas id="countChart"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import { TreemapController, TreemapElement } from 'chartjs-chart-treemap' // ✅ explicit import
import API from '../api'

// Register Chart.js core + treemap plugin
Chart.register(...registerables, TreemapController, TreemapElement)

const chartInstance = ref(null)
const mode = ref('all')
const drilledBrand = ref(null)
let allData = []

async function loadChartData() {
  try {
    const res = await API.get('/events?camera_id=cam1')
    const events = Array.isArray(res.data) ? res.data : []

    let counts = {}
    if (mode.value === 'brand') {
      events.forEach(ev => {
        const label = ev.product_brand || 'Unknown'
        counts[label] = (counts[label] || 0) + 1
      })
    } else {
      events.forEach(ev => {
        const label = ev.product_brand && ev.product_name
          ? `${ev.product_brand} - ${ev.product_name}`
          : 'Unknown'
        counts[label] = (counts[label] || 0) + 1
      })
    }

    let sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])
    if (mode.value === 'top20') sorted = sorted.slice(0, 20)

    const labels = sorted.map(([label]) => label)

    if (chartInstance.value) chartInstance.value.destroy()
    const ctx = document.getElementById('countChart').getContext('2d')

    if (mode.value === 'all') {
      allData = sorted
      drilledBrand.value = null

      chartInstance.value = new Chart(ctx, {
        type: 'treemap',
        data: {
          datasets: [{
            tree: sorted.map(([label, count]) => {
              const brand = label.split(' - ')[0] || label
              return { label, brand, value: count }
            }),
            key: 'value',
            groups: ['brand'],
            backgroundColor(ctx) {
              const i = ctx.index
              const step = i / labels.length
              const r = 220 + Math.round(35 * step)
              const g = 38 + Math.round(61 * step)
              const b = 38 + Math.round(94 * step)
              return `rgba(${r}, ${g}, ${b}, 0.9)`
            },
            labels: {
              display: true,
              formatter(ctx) {
                const total = sorted.reduce((sum, [, c]) => sum + c, 0)
                const pct = ((ctx.raw.value / total) * 100).toFixed(1)
                return `${ctx.raw.label}\n${ctx.raw.value} (${pct}%)`
              }
            }
          }]
        },
        options: {
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: ctx => {
                  const total = sorted.reduce((sum, [, c]) => sum + c, 0)
                  const pct = ((ctx.raw.value / total) * 100).toFixed(1)
                  return `${ctx.raw.label}: ${ctx.raw.value} (${pct}%)`
                }
              }
            }
          },
          onClick(evt, elements) {
            if (!elements.length) return
            const node = elements[0].raw
            drilledBrand.value = node.brand
            drillDownTreemap(ctx, node.brand)
          }
        }
      })
    } else {
      chartInstance.value = new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Detections',
            data: sorted.map(([_, count]) => count),
            backgroundColor: labels.map((_, i) => {
              const step = i / labels.length
              const r = 220 + Math.round(35 * step)
              const g = 38 + Math.round(61 * step)
              const b = 38 + Math.round(94 * step)
              return `rgba(${r}, ${g}, ${b}, 0.9)`
            }),
            borderWidth: 1,
            categoryPercentage: 1.0,
            barPercentage: 1.0
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: ctx => `${ctx.label}: ${ctx.raw} detections`
              }
            }
          },
          scales: {
            x: { beginAtZero: true },
            y: { ticks: { font: { size: 12 }, autoSkip: false } }
          }
        }
      })
    }
  } catch (err) {
    console.error('Error loading chart data:', err)
  }
}

function drillDownTreemap(ctx, brand) {
  const brandProducts = allData.filter(([label]) => label.startsWith(brand))
  chartInstance.value.destroy()
  chartInstance.value = new Chart(ctx, {
    type: 'treemap',
    data: {
      datasets: [{
        tree: brandProducts.map(([label, count]) => ({ label, value: count })),
        key: 'value',
        groups: ['label'],
        backgroundColor(ctx) {
          const i = ctx.index
          const step = i / brandProducts.length
          const r = 220 + Math.round(35 * step)
          const g = 38 + Math.round(61 * step)
          const b = 38 + Math.round(94 * step)
          return `rgba(${r}, ${g}, ${b}, 0.9)`
        },
        labels: {
          display: true,
          formatter(ctx) {
            const total = brandProducts.reduce((sum, [, c]) => sum + c, 0)
            const pct = ((ctx.raw.value / total) * 100).toFixed(1)
            return `${ctx.raw.label}\n${ctx.raw.value} (${pct}%)`
          }
        }
      }]
    },
    options: {
      plugins: {
        tooltip: {
          callbacks: {
            label: ctx => {
              const total = brandProducts.reduce((sum, [, c]) => sum + c, 0)
              const pct = ((ctx.raw.value / total) * 100).toFixed(1)
              return `${ctx.raw.label}: ${ctx.raw.value} (${pct}%)`
            }
          }
        }
      }
    }
  })
}

function resetTreemap() {
  loadChartData()
}

onMounted(loadChartData)
watch(mode, loadChartData)
</script>
