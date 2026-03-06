<template>
  <div class="w-full h-[600px] overflow-y-auto"> <!-- taller container with scroll -->
    <canvas id="countChart"></canvas>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Chart, registerables } from 'chart.js'
import API from '../api'

Chart.register(...registerables)

const chartInstance = ref(null)

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

    // Destroy old chart if exists
    if (chartInstance.value) {
      chartInstance.value.destroy()
    }

    // Create horizontal bar chart with thicker bars
    const ctx = document.getElementById('countChart').getContext('2d')
    chartInstance.value = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Detections',
          data,
          backgroundColor: 'rgba(220, 38, 38, 0.7)', // red tone
          borderColor: 'rgba(220, 38, 38, 1)',
          borderWidth: 1,
          barThickness: 24 // make bars thicker
        }]
      },
      options: {
        indexAxis: 'y', // horizontal bars
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { beginAtZero: true },
          y: {
            ticks: {
              autoSkip: false, // show all labels
              maxRotation: 0,
              minRotation: 0
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
