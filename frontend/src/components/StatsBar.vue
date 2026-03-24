<template>
  <div class="grid grid-cols-3 gap-2 sm:gap-3 mb-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-red-200 dark:border-red-900 p-2 sm:p-4 flex flex-col items-start">
      <span class="text-xs font-semibold text-red-600 uppercase tracking-wide mb-1 leading-tight">Detected</span>
      <span class="text-2xl sm:text-3xl font-bold text-red-700 dark:text-red-400">{{ counts.added }}</span>
      <span class="text-xs text-gray-400 mt-0.5">{{ periodLabel }}</span>
    </div>
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-green-200 dark:border-green-900 p-2 sm:p-4 flex flex-col items-start">
      <span class="text-xs font-semibold text-green-600 uppercase tracking-wide mb-1 leading-tight">Sold</span>
      <span class="text-2xl sm:text-3xl font-bold text-green-700 dark:text-green-400">{{ counts.sold }}</span>
      <span class="text-xs text-gray-400 mt-0.5">{{ periodLabel }}</span>
    </div>
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-blue-200 dark:border-blue-900 p-2 sm:p-4 flex flex-col items-start">
      <span class="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1 leading-tight">Restocked</span>
      <span class="text-2xl sm:text-3xl font-bold text-blue-700 dark:text-blue-400">{{ counts.restock }}</span>
      <span class="text-xs text-gray-400 mt-0.5">{{ periodLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import API from '../api'

const props = defineProps({
  camera:     { type: String, default: 'cam1' },
  filter:     { type: String, default: 'day' },
  customFrom: { type: String, default: null },
  customTo:   { type: String, default: null },
})

const counts = ref({ added: 0, sold: 0, restock: 0 })

const PERIOD_LABELS = {
  day: 'Last 1 Day', week: 'Last 1 Week', month: 'Last 1 Month',
  '3months': 'Last 3 Months', year: 'Last 1 Year', custom: 'Custom Range',
}
const periodLabel = computed(() => PERIOD_LABELS[props.filter] || 'Last 1 Day')

function getStartDate(filter) {
  if (filter === 'custom' && props.customFrom) return props.customFrom
  const now = new Date()
  const map = { day: 1, week: 7, month: 30, '3months': 90, year: 365 }
  now.setDate(now.getDate() - (map[filter] || 1))
  return now.toISOString()
}

async function loadStats() {
  try {
    const params = { start_date: getStartDate(props.filter), limit: 5000 }
    if (props.filter === 'custom' && props.customTo) params.end_date = props.customTo
    if (props.camera !== 'all') params.camera_id = props.camera
    const res = await API.get('/events', { params })
    const totals = { added: 0, sold: 0, restock: 0 }
    for (const ev of res.data) {
      if (ev.event_type in totals) totals[ev.event_type]++
    }
    counts.value = totals
  } catch (_) {}
}

loadStats()
watch(() => [props.camera, props.filter, props.customFrom, props.customTo], loadStats)

// WebSocket for live increments — use wss:// on HTTPS to avoid mixed-content block
const wsProto = window.location.protocol === 'https:' ? 'wss' : 'ws'
const ws = new WebSocket(`${wsProto}://${window.location.host}/ws/events`)
ws.onmessage = (msg) => {
  const ev = JSON.parse(msg.data)
  if (props.camera !== 'all' && ev.camera_id !== props.camera) return
  const cutoff = new Date(getStartDate(props.filter)).getTime()
  if (ev.ts && new Date(ev.ts).getTime() < cutoff) return
  if (ev.event_type in counts.value) counts.value[ev.event_type]++
}
onUnmounted(() => ws.close())
</script>
