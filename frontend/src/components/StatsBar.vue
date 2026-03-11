<template>
  <div class="grid grid-cols-3 gap-3 mb-5">
    <!-- Detected Today -->
    <div class="bg-white rounded-lg shadow-sm border border-red-200 p-4 flex flex-col items-start">
      <span class="text-xs font-semibold text-red-600 uppercase tracking-wide mb-1">Detected Today</span>
      <span class="text-3xl font-bold text-red-700">{{ counts.added }}</span>
    </div>
    <!-- Sold Today -->
    <div class="bg-white rounded-lg shadow-sm border border-green-200 p-4 flex flex-col items-start">
      <span class="text-xs font-semibold text-green-600 uppercase tracking-wide mb-1">Sold Today</span>
      <span class="text-3xl font-bold text-green-700">{{ counts.sold }}</span>
    </div>
    <!-- Restocked Today -->
    <div class="bg-white rounded-lg shadow-sm border border-blue-200 p-4 flex flex-col items-start">
      <span class="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">Restocked Today</span>
      <span class="text-3xl font-bold text-blue-700">{{ counts.restock }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import API from '../api'

const props = defineProps({
  camera: { type: String, default: 'cam1' }
})

const counts = ref({ added: 0, sold: 0, restock: 0 })

function todayStartWIB() {
  // WIB = UTC+7
  const now = new Date()
  const wibOffsetMs = 7 * 60 * 60 * 1000
  const wibNow = new Date(now.getTime() + wibOffsetMs)
  // Start of today in WIB
  const y = wibNow.getUTCFullYear()
  const m = String(wibNow.getUTCMonth() + 1).padStart(2, '0')
  const d = String(wibNow.getUTCDate()).padStart(2, '0')
  // Return as UTC ISO that corresponds to 00:00 WIB
  return new Date(`${y}-${m}-${d}T00:00:00+07:00`).toISOString()
}

async function loadStats() {
  const params = { start_date: todayStartWIB(), limit: 5000 }
  if (props.camera !== 'all') params.camera_id = props.camera
  const res = await API.get('/events', { params })
  const totals = { added: 0, sold: 0, restock: 0 }
  for (const ev of res.data) {
    if (ev.event_type in totals) totals[ev.event_type]++
  }
  counts.value = totals
}

loadStats()
watch(() => props.camera, loadStats)

// WebSocket for live increments
const ws = new WebSocket(`ws://${window.location.host}/ws/events`)
ws.onmessage = (msg) => {
  const ev = JSON.parse(msg.data)
  if (props.camera !== 'all' && ev.camera_id !== props.camera) return
  // Only count if today in WIB
  if (ev.ts && new Date(ev.ts) >= new Date(todayStartWIB())) {
    if (ev.event_type in counts.value) counts.value[ev.event_type]++
  }
}
onUnmounted(() => ws.close())
</script>
