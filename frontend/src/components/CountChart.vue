<template><canvas id="chart"></canvas></template>
<script setup>
import { onMounted } from 'vue'
import { Chart } from 'chart.js'
onMounted(async () => {
  const r = await fetch('http://100.87.93.95:8000/events?camera_id=cam1')
  const data = await r.json()
  const labels = data.map(d => d.ts)
  const counts = data.map((_, i) => i) // placeholder
  new Chart(document.getElementById('chart'), { type: 'bar',
    data: { labels, datasets: [{ label: 'Detections', data: counts }] } })
})
</script>