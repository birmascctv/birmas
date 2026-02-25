<template>
  <div class="flex-1">
    <canvas v-if="hasData" ref="chartRef"></canvas>
    <div v-else class="text-center text-slate-400 py-10">
      No data available
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from 'chart.js'
import API from '@/api.js'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const props = defineProps({
  range: String,
  camera: String
})

const chartRef = ref(null)
let chartInstance = null
const hasData = ref(false)

const loadData = async () => {
  try {
    const params = props.camera === 'all' ? {} : { camera_id: props.camera }
    const res = await API.get('/events', { params })
    let data = res.data

    const now = Date.now()
    if (props.range === 'day') {
      const cutoff = now - 24*60*60*1000
      data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
    } else if (props.range === 'week') {
      const cutoff = now - 7*24*60*60*1000
      data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
    } else if (props.range === 'month') {
      const cutoff = now - 30*24*60*60*1000
      data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
    } else if (props.range === '3months') {
      const cutoff = now - 90*24*60*60*1000
      data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
    } else if (props.range === 'year') {
      const cutoff = now - 365*24*60*60*1000
      data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
    }

    const countsByLabel = {}
    data.forEach(ev => {
      countsByLabel[ev.label] = (countsByLabel[ev.label] || 0) + 1
    })

    const labels = Object.keys(countsByLabel)
    const counts = Object.values(countsByLabel)

    hasData.value = labels.length > 0

    if (chartInstance) chartInstance.destroy()
    if (chartRef.value && hasData.value) {
      chartInstance = new Chart(chartRef.value, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Detections per Label',
            data: counts,
            backgroundColor: 'rgba(79, 70, 229, 0.7)' // Indigo
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false },
            tooltip: { bodyFont: { size: 12 }, titleFont: { size: 14 } }
          },
          scales: {
            x: { ticks: { font: { size: 12 } } },
            y: { ticks: { font: { size: 12 } } }
          }
        }
      })
    }
  } catch (err) {
    console.error("Error loading chart data:", err)
    hasData.value = false
  }
}

onMounted(loadData)
watch(() => [props.range, props.camera], loadData)
</script>
