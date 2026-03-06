<template>
  <div class="w-full h-[800px] overflow-y-auto">
    <canvas id="countChart"></canvas>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Chart, registerables } from 'chart.js'
import API from '../api'

Chart.register(...registerables)

const chartInstance = ref(null)

// Simple color palette generator
function getColor(index) {
  const colors = [
    'rgba(220, 38, 38, 0.7)',   // red
    'rgba(37, 99, 235, 0.7)',   // blue
    'rgba(34, 197, 94, 0.7)',   // green
    'rgba(234, 179, 8, 0.7)',   // yellow
    'rgba(168, 85, 247, 0.7)',  // purple
    'rgba(251, 113, 133, 0.7)', // pink
    'rgba(14, 165, 233, 0.7)'   // cyan
  ]
  return colors[index % colors.length]
}

async function loadChartData() {
  try {
    const res = await API.get('/events?camera_id=cam1')
    const events = Array.isArray(res.data) ? res.data : []
    console.log('Chart events response:', res.data)

    // Count products by brand + name
    const counts = {}
    events.forEach(ev => {
      const label = ev.product_brand && ev.product_name
        ? `${ev.product_brand} - ${ev.product_name}`
        : 'Unknown'
      counts[label] = (counts[label] || 0) + 1
    })

    // Sort by count descending
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1])
    const labels = sorted.map(([label]) => label)
    const data = sorted.map(([_, count]) => count)

    // Assign colors per label
    const backgroundColors = labels.map((_, i) => getColor(i))
    const borderColors = labels.map((_, i) => getColor(i).replace('0.7', '1'))

    // Destroy old chart if exists
    if (chartInstance.value) {
      chartInstance.value.destroy()
    }

    // Create horizontal bar chart
    const ctx = document.getElementById('countChart').getContext('2d')
    chartInstance.value = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Detections',
          data,
          backgroundColor: backgroundColors,
          borderColor: borderColors,
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

onMounted(() => {
  loadChartData()
})
</script>
