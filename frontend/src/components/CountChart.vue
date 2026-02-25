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
      // dynamic red shades for pie
      const min = Math.min(...counts)
      const max = Math.max(...counts)
      const colors = counts.map(val => {
        const ratio = (val - min) / (max - min || 1)
        // light red (#fecaca) → dark red (#b91c1c)
        return ratio === 0
          ? '#fecaca'
          : `hsl(0, 70%, ${70 - ratio*40}%)`
      })

      if (!chartInstance) {
        chartInstance = new Chart(chartRef.value, {
          type: chartType.value,
          data: {
            labels,
            datasets: [{
              label: 'Detections per Label',
              data: counts,
              backgroundColor: chartType.value === 'bar'
                ? 'rgba(220, 38, 38, 0.7)' // red for bar
                : colors
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false
          }
        })
      } else {
        chartInstance.config.type = chartType.value
        chartInstance.data.labels = labels
        chartInstance.data.datasets[0].data = counts
        chartInstance.data.datasets[0].backgroundColor =
          chartType.value === 'bar'
            ? 'rgba(220, 38, 38, 0.7)'
            : colors
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
