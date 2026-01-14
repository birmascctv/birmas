<template>
  <canvas ref="chartRef"></canvas>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Chart } from 'chart.js'
import API from '@/api.js'

const chartRef = ref(null)

onMounted(async () => {
  try {
    const res = await API.get('/events', { params: { camera_id: 'cam1' } })
    const data = res.data

    const countsByLabel = {}
    data.forEach(ev => {
      countsByLabel[ev.label] = (countsByLabel[ev.label] || 0) + 1
    })

    const labels = Object.keys(countsByLabel)
    const counts = Object.values(countsByLabel)

    if (chartRef.value) {
      new Chart(chartRef.value, {
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
    } else {
      console.error("Chart canvas not found")
    }
  } catch (err) {
    console.error("Error loading chart data:", err)
  }
})
</script>
