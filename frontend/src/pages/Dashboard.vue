<template>
  <div class="dashboard bg-gray-50 min-h-screen px-10 py-5 text-gray-800">

    <!-- Header -->
    <header class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-red-600 tracking-wide">
        Birmas
      </h1>
      <button @click="logout"
              class="px-3 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-medium border border-red-700">
        Logout
      </button>
    </header>

    <!-- Camera Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-5 items-stretch">
      <!-- Selected Camera -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-200">
        <h2 class="text-lg font-semibold text-red-600 mb-2">Selected Camera</h2>
        <select v-model="selectedCam"
                class="w-40 mb-2 h-7 px-2 py-0.5 border border-gray-300 rounded text-sm leading-tight bg-gray-100 text-gray-800">
          <option v-for="cam in cameras" :key="cam.id" :value="cam.id">
            {{ cam.name }}
          </option>
        </select>
        <div class="relative aspect-video bg-black rounded-md overflow-hidden flex-1">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Grid Cameras -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-200">
        <h2 class="text-lg font-semibold text-red-600 mb-2">All Cameras</h2>
        <div class="grid grid-cols-3 gap-2 flex-1">
          <div v-for="cam in cameras" :key="cam.id"
               class="relative aspect-video rounded-md overflow-hidden cursor-pointer flex items-center justify-center border border-gray-300"
               :class="selectedCam === cam.id ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'"
               @click="selectedCam = cam.id">
            <span class="absolute bottom-2 left-2 text-xs font-medium px-2 py-0.5 rounded"
                  :class="selectedCam === cam.id ? 'bg-red-600 text-white' : 'bg-gray-400 text-white'">
              {{ cam.name }}
            </span>
            <!-- Static photo instead of live feed -->
            <img :src="cam.thumbnail" alt="Camera thumbnail" class="w-full h-full object-cover" />
            <!-- Online/Offline dot badge -->
            <span class="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full border border-white"
                  :class="cameraOnline(cam.id) ? 'bg-green-500 animate-pulse' : 'bg-red-500'">
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Bar (filtered by cam toggle, sits between cameras and content) -->
    <StatsBar :camera="showAllCams ? 'all' : selectedCam" />

    <!-- Unified Filter -->
    <div class="flex items-center gap-2 flex-wrap mb-3">
      <select v-model="activeFilter"
              class="w-40 h-7 px-2 py-0.5 border border-gray-300 rounded text-sm leading-tight bg-gray-100 text-gray-800">
        <option value="day">Last 1 Day</option>
        <option value="week">Last 1 Week</option>
        <option value="month">Last 1 Month</option>
        <option value="3months">Last 3 Months</option>
        <option value="year">Last 1 Year</option>
        <option value="custom">Custom Range</option>
      </select>
      <!-- Custom date range inputs -->
      <template v-if="activeFilter === 'custom'">
        <input type="date" v-model="customFrom"
               class="h-7 px-2 border border-gray-300 rounded text-sm bg-gray-100 text-gray-800" />
        <span class="text-sm text-gray-500">to</span>
        <input type="date" v-model="customTo"
               class="h-7 px-2 border border-gray-300 rounded text-sm bg-gray-100 text-gray-800" />
      </template>
      <button @click="showAllCams = !showAllCams"
              class="ml-auto px-3 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-medium border border-red-700">
        {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
      </button>
    </div>

    <!-- Bottom Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-3 items-stretch">
      <!-- Events Table -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-200">
        <h2 class="text-lg font-semibold text-red-600 mb-2">Recent Events</h2>
        <EventTable
          :filter="activeFilter"
          :camera="showAllCams ? 'all' : selectedCam"
          :customFrom="activeFilter === 'custom' ? customFromISO : null"
          :customTo="activeFilter === 'custom' ? customToISO : null"
        />
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-200">
        <h2 class="text-lg font-semibold text-red-600 mb-2">Product Count Statistics</h2>
        <CountChart
          :filter="activeFilter"
          :camera="showAllCams ? 'all' : selectedCam"
          :customFrom="activeFilter === 'custom' ? customFromISO : null"
          :customTo="activeFilter === 'custom' ? customToISO : null"
        />
      </div>
    </section>

    <!-- Toast notifications -->
    <ToastNotif :toasts="toasts" />

  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import LivePlayer from '../components/LivePlayer.vue'
import CountChart from '../components/CountChart.vue'
import EventTable from '../components/EventTable.vue'
import StatsBar from '../components/StatsBar.vue'
import ToastNotif from '../components/ToastNotif.vue'
import API from '../api'

const cameras = [
  { id: 'cam1', name: 'Tebet', thumbnail: '/images/tebet.jpg' },
  // Add more cameras later like:
  // { id: 'cam2', name: 'Kemang', thumbnail: '/images/kemang.jpg' },
  // { id: 'cam3', name: 'Senayan', thumbnail: '/images/senayan.jpg' },
]

const selectedCam = ref('cam1')
const activeFilter = ref('day')
const showAllCams = ref(false)
const customFrom = ref('')
const customTo = ref('')

// Convert local date string (YYYY-MM-DD) to ISO start/end of day
const customFromISO = computed(() =>
  customFrom.value ? new Date(customFrom.value + 'T00:00:00').toISOString() : null
)
const customToISO = computed(() =>
  customTo.value ? new Date(customTo.value + 'T23:59:59').toISOString() : null
)

const router = useRouter()
const logout = () => {
  localStorage.removeItem('auth_token')
  sessionStorage.removeItem('auth_token')
  router.push('/login')
}

// ── Camera online/offline status ──────────────────────────────────────────────
const cameraStatusMap = ref({})

async function fetchCameraStatus() {
  try {
    const res = await API.get('/camera-status')
    const map = {}
    for (const cam of res.data.cameras || []) {
      map[cam.id] = cam.online
    }
    cameraStatusMap.value = map
  } catch (_) {}
}

function cameraOnline(id) {
  return cameraStatusMap.value[id] === true
}

fetchCameraStatus()
const statusInterval = setInterval(fetchCameraStatus, 10000)

// ── Toast notifications via WebSocket ─────────────────────────────────────────
const STATUS_LABELS = { added: 'Detected', sold: 'Sold', restock: 'Restocked' }
const toasts = ref([])
let toastIdCounter = 0

const toastWs = new WebSocket(`ws://${window.location.host}/ws/events`)
toastWs.onmessage = (msg) => {
  const ev = JSON.parse(msg.data)
  const id = ++toastIdCounter
  const toast = {
    id,
    brand:       ev.product_brand || 'Unknown',
    product:     ev.product_name  || 'Unknown',
    event_type:  ev.event_type,
    statusLabel: STATUS_LABELS[ev.event_type] || ev.event_type || '—',
  }
  // Keep max 3 toasts
  toasts.value = [toast, ...toasts.value].slice(0, 3)
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 4000)
}

onUnmounted(() => {
  clearInterval(statusInterval)
  toastWs.close()
})
</script>
