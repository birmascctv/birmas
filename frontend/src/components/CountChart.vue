<template>
  <div class="w-full h-64">
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
    // Ensure we always get an array
    const events = Array.isArray(res.data) ? res.data : []
    console.log('Chart events response:', res.data)

    // Count labels (product types)
    const counts = {}
    events.forEach(ev => {
      // Defensive parsing: make sure label exists
      const label = ev.label || 'Unknown'
      counts[label] = (counts[label] || 0) + 1
    })

    const labels = Object.keys(counts)
    const data = Object.values(counts)

    // Destroy old chart if exists
    if (chartInstance.value) {
      chartInstance.value.destroy()
    }

    // Create chart
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
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true }
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
