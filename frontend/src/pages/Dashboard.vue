<template>
  <div class="dashboard bg-gray-50 min-h-screen px-3 sm:px-5 lg:px-10 py-4 text-gray-800">

    <!-- Header -->
    <header class="flex items-center justify-between mb-4">
      <h1 class="text-xl sm:text-2xl font-bold text-red-600 tracking-wide">Birmas</h1>
      <div class="flex items-center gap-2">
        <!-- Idle warning -->
        <span v-if="idleWarning"
              class="text-xs text-amber-600 font-medium animate-pulse hidden sm:inline">
          Idle — logging out soon
        </span>
        <button @click="logout"
                class="px-3 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-medium">
          Logout
        </button>
      </div>
    </header>

    <!-- Camera Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-4 items-stretch">
      <!-- Selected Camera Player -->
      <div class="bg-white rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200">
        <div class="flex items-center gap-2 mb-2 flex-wrap">
          <h2 class="text-base sm:text-lg font-semibold text-red-600">Selected Camera</h2>
          <select v-model="selectedCam"
                  class="ml-auto w-36 h-7 px-2 py-0.5 border border-gray-300 rounded text-sm bg-gray-100 text-gray-800">
            <option v-for="cam in cameras" :key="cam.id" :value="cam.id">{{ cam.name }}</option>
          </select>
        </div>
        <div class="relative w-full rounded-md overflow-hidden bg-black" style="padding-top:56.25%">
          <div class="absolute inset-0">
            <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
          </div>
        </div>
      </div>

      <!-- All Cameras Grid -->
      <div class="bg-white rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200">
        <h2 class="text-base sm:text-lg font-semibold text-red-600 mb-2">All Cameras</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 flex-1">
          <div v-for="cam in cameras" :key="cam.id"
               class="relative rounded-md overflow-hidden cursor-pointer border border-gray-300"
               style="padding-top:56.25%"
               @click="selectedCam = cam.id">
            <img :src="cam.thumbnail" alt="Camera thumbnail"
                 class="absolute inset-0 w-full h-full object-cover" />
            <span class="absolute bottom-1 left-1 text-xs font-medium px-1.5 py-0.5 rounded"
                  :class="selectedCam === cam.id ? 'bg-red-600 text-white' : 'bg-gray-700 bg-opacity-70 text-white'">
              {{ cam.name }}
            </span>
            <span class="absolute top-1 right-1 w-2.5 h-2.5 rounded-full border border-white shadow"
                  :class="cameraOnline(cam.id) ? 'bg-green-500 animate-pulse' : 'bg-red-500'"></span>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Bar -->
    <StatsBar :camera="showAllCams ? 'all' : selectedCam" />

    <!-- Unified Filter Row -->
    <div class="flex items-center gap-2 flex-wrap mb-3 mt-3">
      <!-- Date range filter -->
      <select v-model="activeFilter"
              class="h-8 px-2 py-0.5 border border-gray-300 rounded text-sm bg-gray-100 text-gray-800">
        <option value="day">Last 1 Day</option>
        <option value="week">Last 1 Week</option>
        <option value="month">Last 1 Month</option>
        <option value="3months">Last 3 Months</option>
        <option value="year">Last 1 Year</option>
        <option value="custom">Custom Range</option>
      </select>
      <template v-if="activeFilter === 'custom'">
        <input type="date" v-model="customFrom"
               class="h-8 px-2 border border-gray-300 rounded text-sm bg-gray-100 text-gray-800" />
        <span class="text-sm text-gray-400">to</span>
        <input type="date" v-model="customTo"
               class="h-8 px-2 border border-gray-300 rounded text-sm bg-gray-100 text-gray-800" />
      </template>

      <!-- Cam toggle -->
      <div class="ml-auto flex items-center gap-2 select-none">
        <span class="text-sm font-medium" :class="!showAllCams ? 'text-red-600' : 'text-gray-400'">
          <span class="hidden sm:inline">Selected Cam</span>
          <span class="sm:hidden">Cam</span>
        </span>
        <button @click="showAllCams = !showAllCams" role="switch" :aria-checked="showAllCams"
                class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none"
                :class="showAllCams ? 'bg-red-600' : 'bg-gray-300'">
          <span class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                :class="showAllCams ? 'translate-x-6' : 'translate-x-1'"></span>
        </button>
        <span class="text-sm font-medium" :class="showAllCams ? 'text-red-600' : 'text-gray-400'">
          All
        </span>
      </div>
    </div>

    <!-- Table + Chart -->
    <section class="grid grid-cols-1 xl:grid-cols-2 gap-3 items-stretch">
      <!-- Events Table -->
      <div class="bg-white rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200 min-h-[400px]">
        <h2 class="text-base sm:text-lg font-semibold text-red-600 mb-2">Recent Events</h2>
        <EventTable
          :filter="activeFilter"
          :camera="showAllCams ? 'all' : selectedCam"
          :customFrom="activeFilter === 'custom' ? customFromISO : null"
          :customTo="activeFilter === 'custom' ? customToISO : null"
        />
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200 min-h-[400px]">
        <h2 class="text-base sm:text-lg font-semibold text-red-600 mb-2">Product Count Statistics</h2>
        <CountChart
          :filter="activeFilter"
          :camera="showAllCams ? 'all' : selectedCam"
          :customFrom="activeFilter === 'custom' ? customFromISO : null"
          :customTo="activeFilter === 'custom' ? customToISO : null"
        />
      </div>
    </section>

    <!-- Toast -->
    <ToastNotif :toasts="toasts" />
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import LivePlayer  from '../components/LivePlayer.vue'
import CountChart  from '../components/CountChart.vue'
import EventTable  from '../components/EventTable.vue'
import StatsBar    from '../components/StatsBar.vue'
import ToastNotif  from '../components/ToastNotif.vue'
import API from '../api'

const cameras = [
  { id: 'cam1', name: 'Tebet', thumbnail: '/images/tebet.jpg' },
]

const selectedCam  = ref('cam1')
const activeFilter = ref('day')
const showAllCams  = ref(false)
const customFrom   = ref('')
const customTo     = ref('')
const idleWarning  = ref(false)

const customFromISO = computed(() =>
  customFrom.value ? new Date(customFrom.value + 'T00:00:00').toISOString() : null
)
const customToISO = computed(() =>
  customTo.value ? new Date(customTo.value + 'T23:59:59').toISOString() : null
)

const router = useRouter()

function logout() {
  localStorage.removeItem('auth_token')
  sessionStorage.removeItem('auth_token')
  router.push('/login')
}

// ── Idle timeout ──────────────────────────────────────────────────────────────
const IDLE_LIMIT_MS   = 60 * 60 * 1000   // 1 hour
const IDLE_WARN_MS    = 55 * 60 * 1000   // warn 5 minutes before

let idleTimer    = null
let warnTimer    = null

function resetIdleTimer() {
  idleWarning.value = false
  clearTimeout(idleTimer)
  clearTimeout(warnTimer)
  warnTimer = setTimeout(() => { idleWarning.value = true }, IDLE_WARN_MS)
  idleTimer = setTimeout(() => {
    localStorage.removeItem('auth_token')
    sessionStorage.removeItem('auth_token')
    router.push('/login?timeout=1')
  }, IDLE_LIMIT_MS)
}

const ACTIVITY_EVENTS = ['mousemove', 'keydown', 'mousedown', 'scroll', 'touchstart', 'touchmove']
ACTIVITY_EVENTS.forEach(e => document.addEventListener(e, resetIdleTimer, { passive: true }))
resetIdleTimer()

// ── Camera online/offline ──────────────────────────────────────────────────────
const cameraStatusMap = ref({})

async function fetchCameraStatus() {
  try {
    const res = await API.get('/camera-status')
    const map = {}
    for (const cam of res.data.cameras || []) map[cam.id] = cam.online
    cameraStatusMap.value = map
  } catch (_) {}
}

function cameraOnline(id) { return cameraStatusMap.value[id] === true }

fetchCameraStatus()
const statusInterval = setInterval(fetchCameraStatus, 10000)

// ── Toast notifications via WebSocket ─────────────────────────────────────────
const STATUS_LABELS = { added: 'Detected', sold: 'Sold', restock: 'Restocked' }
const toasts = ref([])
let toastIdCounter = 0

const toastWs = new WebSocket(`ws://${window.location.host}/ws/events`)
toastWs.onmessage = (msg) => {
  const ev = JSON.parse(msg.data)
  const id  = ++toastIdCounter
  toasts.value = [
    { id, brand: ev.product_brand || 'Unknown', product: ev.product_name || 'Unknown',
      event_type: ev.event_type, statusLabel: STATUS_LABELS[ev.event_type] || ev.event_type || '—' },
    ...toasts.value,
  ].slice(0, 3)
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 4000)
}

onUnmounted(() => {
  clearInterval(statusInterval)
  clearTimeout(idleTimer)
  clearTimeout(warnTimer)
  ACTIVITY_EVENTS.forEach(e => document.removeEventListener(e, resetIdleTimer))
  toastWs.close()
})
</script>
