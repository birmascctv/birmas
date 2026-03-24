<template>
  <div class="flex-1 flex flex-col min-h-0">
    <!-- Export CSV button -->
    <div class="flex justify-end mb-2">
      <button @click="exportCSV"
              class="px-3 py-1 text-xs font-medium rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 shadow-sm">
        Export CSV
      </button>
    </div>

    <div class="overflow-x-auto" v-if="paginatedEvents && paginatedEvents.length">
    <table class="text-sm w-full border-collapse text-center min-w-[480px]">
      <thead>
        <tr>
          <th class="border border-gray-300 dark:border-gray-600 px-3 py-2 bg-slate-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200">Time</th>
          <th class="border border-gray-300 dark:border-gray-600 px-3 py-2 bg-slate-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200">Camera</th>
          <th class="border border-gray-300 dark:border-gray-600 px-3 py-2 bg-slate-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200">Brand</th>
          <th class="border border-gray-300 dark:border-gray-600 px-3 py-2 bg-slate-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200">Product</th>
          <th class="border border-gray-300 dark:border-gray-600 px-3 py-2 bg-slate-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200">Conf</th>
          <th class="border border-gray-300 dark:border-gray-600 px-3 py-2 bg-slate-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ev in paginatedEvents" :key="ev.id"
            :class="[rowClass(ev.event_type), newEventIds.has(ev.id) ? 'new-row' : '']">
          <td class="border border-gray-300 dark:border-gray-600 px-3 py-2 text-gray-700 dark:text-gray-200">
            {{
              ev.ts
                ? new Date(ev.ts).toISOString().replace('T', ' ').split('.')[0]
                : '—'
            }}
          </td>
          <td class="border border-gray-300 dark:border-gray-600 px-3 py-2 dark:text-gray-200">{{ ev.camera_id || '—' }}</td>
          <td class="border border-gray-300 dark:border-gray-600 px-3 py-2 dark:text-gray-200">{{ ev.product_brand || '—' }}</td>
          <td class="border border-gray-300 dark:border-gray-600 px-3 py-2 dark:text-gray-200">{{ ev.product_name || '—' }}</td>
          <td class="border border-gray-300 dark:border-gray-600 px-3 py-2 dark:text-gray-200">
            {{
              ev.confidence !== undefined && ev.confidence !== null
                ? (Number(ev.confidence) * 100).toFixed(1) + '%'
                : '—'
            }}
          </td>
          <td class="border border-gray-300 dark:border-gray-600 px-3 py-2">
            <span :class="statusClass(ev.event_type)"
                  class="px-2 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap">
              {{ statusLabel(ev.event_type) }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
    </div>

    <div v-else class="text-center text-gray-400 py-10">No data available</div>

    <!-- Pagination -->
    <div class="flex justify-center gap-2 mt-3 flex-wrap" v-if="totalPages > 1">
      <button @click="currentPage = Math.max(1, currentPage - 1)"
              class="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 disabled:opacity-40"
              :disabled="currentPage === 1">
        Prev
      </button>

      <template v-for="n in pagesToShow" :key="n">
        <span v-if="n === '...'" class="px-2 py-1 text-gray-400">...</span>
        <button v-else
                @click="currentPage = n"
                class="px-2 py-1 rounded border border-gray-300 dark:border-gray-600"
                :class="currentPage === n ? 'bg-red-600 text-white border-red-600' : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200'">
          {{ n }}
        </button>
      </template>

      <button @click="currentPage = Math.min(totalPages, currentPage + 1)"
              class="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 disabled:opacity-40"
              :disabled="currentPage === totalPages">
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import API from '../api'

const props = defineProps({
  camera:        { type: String,  default: 'cam1' },
  filter:        { type: String,  default: 'day' },
  customFrom:    { type: String,  default: null },
  customTo:      { type: String,  default: null },
  minConfidence: { type: Number,  default: 0 },
  filterStatus:  { type: String,  default: 'all' },
})

// Human-readable status labels
const STATUS_LABELS = { added: 'Detected', sold: 'Sold', restock: 'Restocked' }
const STATUS_CLASSES = {
  added:   'bg-red-100 text-red-700',
  sold:    'bg-green-100 text-green-700',
  restock: 'bg-blue-100 text-blue-700',
}
// Row colors: light mode uses soft tint (100-shade), dark mode uses low-opacity deep shade
const ROW_CLASSES = {
  added:   'bg-red-50   dark:bg-red-950/40',
  sold:    'bg-green-100 dark:bg-green-800/40',
  restock: 'bg-blue-100  dark:bg-blue-800/40',
}
function statusLabel(type) { return STATUS_LABELS[type] || type || '—' }
function statusClass(type) { return STATUS_CLASSES[type] || 'bg-gray-100 text-gray-600' }
function rowClass(type)    { return ROW_CLASSES[type]    || '' }

// Row limit per filter period
const LIMIT_MAP = { day: 50, week: 150, month: 500, '3months': 1000, year: 5000, custom: 2000 }

const events = ref([])
const currentPage = ref(1)
const pageSize = 10
const newEventIds = ref(new Set())

watch(() => [props.camera, props.filter, props.customFrom, props.customTo, props.minConfidence, props.filterStatus], () => {
  currentPage.value = 1
  loadEvents()
})

function getStartDate(filter) {
  if (filter === 'custom' && props.customFrom) return props.customFrom
  const now = new Date()
  const map = { day: 1, week: 7, month: 30, '3months': 90, year: 365 }
  now.setDate(now.getDate() - (map[filter] || 1))
  return now.toISOString()
}

async function loadEvents() {
  try {
    const params = { start_date: getStartDate(props.filter) }
    if (props.filter === 'custom' && props.customTo) params.end_date = props.customTo
    if (props.camera !== 'all') params.camera_id = props.camera
    params.limit = LIMIT_MAP[props.filter] || 50
    if (props.minConfidence > 0) params.min_confidence = props.minConfidence / 100
    if (props.filterStatus !== 'all') params.event_type = props.filterStatus
    const res = await API.get('/events', { params })
    events.value = res.data
  } catch (_) {}
}
loadEvents()

// WebSocket for live events — use wss:// on HTTPS to avoid mixed-content block
const wsProto = window.location.protocol === 'https:' ? 'wss' : 'ws'
const ws = new WebSocket(`${wsProto}://${window.location.host}/ws/events`)
ws.onmessage = (msg) => {
  const ev = JSON.parse(msg.data)
  if (props.camera !== 'all' && ev.camera_id !== props.camera) return
  const cutoff = new Date(getStartDate(props.filter)).getTime()
  if (ev.ts && new Date(ev.ts).getTime() < cutoff) return
  // Apply confidence and status filters to live events too
  if (props.minConfidence > 0 && (ev.confidence || 0) < props.minConfidence / 100) return
  if (props.filterStatus !== 'all' && ev.event_type !== props.filterStatus) return
  events.value.unshift(ev)
  // Track new event for flash animation
  newEventIds.value = new Set([...newEventIds.value, ev.id])
  setTimeout(() => {
    const updated = new Set(newEventIds.value)
    updated.delete(ev.id)
    newEventIds.value = updated
  }, 2000)
}
onUnmounted(() => ws.close())

// Export CSV
function exportCSV() {
  const header = ['Time', 'Camera', 'Brand', 'Product', 'Confidence', 'Status']
  const rows = events.value.map(ev => [
    ev.ts ? new Date(ev.ts).toISOString().replace('T', ' ').split('.')[0] : '',
    ev.camera_id || '',
    ev.product_brand || '',
    ev.product_name || '',
    ev.confidence !== undefined && ev.confidence !== null
      ? (Number(ev.confidence) * 100).toFixed(1) + '%' : '',
    STATUS_LABELS[ev.event_type] || ev.event_type || '',
  ])
  const csv = [header, ...rows].map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  const today = new Date().toISOString().split('T')[0]
  a.href = url
  a.download = `events_${props.filter}_${props.camera}_${today}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// Pagination
const totalPages = computed(() =>
  Math.ceil(events.value.length / pageSize)
)

const paginatedEvents = computed(() =>
  events.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize)
)

const pagesToShow = computed(() => {
  const total = totalPages.value
  const cur   = currentPage.value

  if (total <= 6) return Array.from({ length: total }, (_, i) => i + 1)

  const first3 = [1, 2, 3]
  const last3  = [total - 2, total - 1, total]
  const mid    = [cur - 1, cur].filter(p => p > 3 && p < total - 2)

  const allNums = [...new Set([...first3, ...mid, ...last3])].sort((a, b) => a - b)

  const result = []
  let prev = 0
  for (const p of allNums) {
    if (p > prev + 1) result.push('...')
    result.push(p)
    prev = p
  }
  return result
})
</script>

<style scoped>
.new-row {
  animation: flash-row 2s ease-out;
}
@keyframes flash-row {
  0%   { background-color: #fef08a; }
  100% { background-color: inherit; }
}
</style>
