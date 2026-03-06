<template>
  <div>
    <!-- Toggle buttons -->
    <div class="flex gap-2 mb-4">
      <button @click="mode = 'all'"
              :class="mode === 'all' ? 'bg-red-600 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'">
        All Products
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

    <!-- Chart container -->
    <div class="w-full h-[1000px] overflow-y-auto">
      <canvas id="countChart"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import API from '../api'

Chart.register(...registerables)

const chartInstance = ref(null)
const mode = ref('all') // default mode

async function loadChartData() {
  try {
    const res = await API.get('/events?camera_id=cam1')
    const events = Array.isArray(res.data) ? res.data : []

    let counts = {}

    if (mode.value === 'brand') {
      // Group by brand only
      events.forEach(ev => {
        const label = ev.product_brand || 'Unknown'
        counts[label] = (counts[label] || 0) + 1
      })
    } else {
      // Group by product_brand + product_name
      events.forEach(ev => {
        const label = ev.product_brand && ev.product_name
          ? `${ev.product_brand} - ${ev.product_name}`
          : 'Unknown'
        counts[label] = (counts[label] || 0) + 1
      })
    }

    // Sort by count descending
    let sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])

    if (mode.value === 'top20') {
      sorted = sorted.slice(0, 20)
    }

    const labels = sorted.map(([label]) => label)
    const data = sorted.map(([_, count]) => count)

    // Destroy old chart if exists
    if (chartInstance.value) {
      chartInstance.value.destroy()
    }

    const ctx = document.getElementById('countChart').getContext('2d')

    // Create gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 800, 0)
    gradient.addColorStop(0, 'rgba(255, 99, 132, 0.8)')
    gradient.addColorStop(1, 'rgba(220, 38, 38, 0.8)')

    chartInstance.value = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Detections',
          data,
          backgroundColor: gradient, // red gradient
          borderColor: 'rgba(220, 38, 38, 1)',
          borderWidth: 1,
          barThickness: 28
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { beginAtZero: true },
          y: {
            ticks: {
              font: { size: 12 },
              autoSkip: false
            }
          }
        }
      }
    })
  } catch (err) {
    console.error('Error loading chart data:', err)
  }
}

onMounted(loadChartData)
watch(mode, loadChartData)
</script>
