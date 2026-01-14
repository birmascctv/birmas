<template>
  <canvas id="chart"></canvas>
</template>

<script setup>
import { onMounted } from 'vue'
import { Chart } from 'chart.js'
import API from './api.js'   // import your Axios instance

onMounted(async () => {
  try {
    const res = await API.get('/events', { params: { camera_id: 'cam1' } })
    const data = res.data

    // Group detections by label
    const countsByLabel = {}
    data.forEach(ev => {
      countsByLabel[ev.label] = (countsByLabel[ev.label] || 0) + 1
    })

    const labels = Object.keys(countsByLabel)
    const counts = Object.values(countsByLabel)

    new Chart(document.getElementById('chart'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Detections per Label',
          data: counts,
          backgroundColor: 'rgba(54, 162, 235, 0.6)'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        }
      }
    })
  } catch (err) {
    console.error("Error loading chart data:", err)
  }
})
</script>
