<template>
  <div class="flex-1">
    <div class="flex gap-2 mb-2">
      <button @click="chartType = 'bar'"
              :class="chartType==='bar'
                ? 'bg-amber-600 text-white px-3 py-1 rounded'
                : 'bg-stone-200 px-3 py-1 rounded'">
        Bar
      </button>
      <button @click="chartType = 'pie'"
              :class="chartType==='pie'
                ? 'bg-amber-600 text-white px-3 py-1 rounded'
                : 'bg-stone-200 px-3 py-1 rounded'">
        Pie
      </button>
    </div>

    <!-- Chart canvas -->
    <div class="flex items-center justify-center">
      <canvas v-if="hasData"
              ref="chartRef"
              :class="chartType === 'pie' ? 'scale-90' : 'w-full h-full'"></canvas>
      <div v-else class="text-center text-slate-400 py-10">No data available</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import {
  Chart,
  BarController,
  PieController,
  BarElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from 'chart.js'
import API from '@/api.js'

Chart.register(BarController, PieController, BarElement, ArcElement, CategoryScale, LinearScale, Tooltip, Legend)

const props = defineProps({ range: String, camera: String })

const chartRef = ref(null)
let chartInstance = null
const hasData = ref(false)
const events = ref([])
const chartType = ref('bar')

const loadData = async () => {
  try {
    const params = props.camera === 'all' ? {} : { camera_id: props.camera }
    const res = await API.get('/events', { params })
    events.value = res.data

    const now = Date.now()
    let filtered = events.value.filter(ev => {
      const ts = new Date(ev.ts).getTime()
      if (props.range === 'day') return ts >= now - 24*60*60*1000
      if (props.range === 'week') return ts >= now - 7*24*60*60*1000
      if (props.range === 'month') return ts >= now - 30*24*60*60*1000
      if (props.range === '3months') return ts >= now - 90*24*60*60*1000
      if (props.range === 'year') return ts >= now - 365*24*60*60*1000
      return true
    })

    const countsByLabel = {}
    filtered.forEach(ev => {
      countsByLabel[ev.label] = (countsByLabel[ev.label] || 0) + 1
    })

    const labels = Object.keys(countsByLabel)
    const counts = Object.values(countsByLabel)

    hasData.value = labels.length > 0

    if (chartRef.value && hasData.value) {
      if (!chartInstance) {
        chartInstance = new Chart(chartRef.value, {
          type: chartType.value,
          data: {
            labels,
            datasets: [{
              label: 'Detections per Label',
              data: counts,
              backgroundColor: chartType.value === 'bar'
                ? 'rgba(202, 138, 4, 0.7)' // amber for bar
                : ['#fbbf24','#f59e0b','#d97706','#b45309'] // pie slices
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false
          }
        })
      } else {
        // ✅ Update instead of destroy/recreate
        chartInstance.config.type = chartType.value
        chartInstance.data.labels = labels
        chartInstance.data.datasets[0].data = counts
        chartInstance.data.datasets[0].backgroundColor =
          chartType.value === 'bar'
            ? 'rgba(202, 138, 4, 0.7)'
            : ['#fbbf24','#f59e0b','#d97706','#b45309']
        chartInstance.update()
      }
    }
  } catch (err) {
    console.error("Error loading chart data:", err)
    hasData.value = false
  }
}

onMounted(loadData)
watch(() => [props.range, props.camera, chartType.value], loadData)
</script>
