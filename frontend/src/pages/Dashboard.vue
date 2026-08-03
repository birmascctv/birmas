<template>
  <div class="dashboard bg-gray-50 dark:bg-gray-900 min-h-screen px-3 sm:px-5 lg:px-10 py-4 text-gray-800 dark:text-gray-100 transition-colors">

    <!-- Header -->
    <header class="flex items-center justify-between mb-4 gap-2 flex-wrap">
      <h1 class="text-xl sm:text-2xl font-bold text-red-600 tracking-wide">Birmas</h1>
      <div class="flex items-center gap-2 sm:gap-3">
        <span v-if="idleWarning" class="text-xs text-amber-500 font-medium animate-pulse hidden sm:inline">
          Idle — logging out soon
        </span>

        <!-- Dark / Light mode toggle -->
        <div class="flex items-center gap-1.5 select-none">
          <!-- Sun icon -->
          <svg class="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm0 15a5 5 0 100-10 5 5 0 000 10zm7.07-12.07a1 1 0 010 1.41l-.71.71a1 1 0 11-1.41-1.41l.71-.71a1 1 0 011.41 0zM21 11h1a1 1 0 110 2h-1a1 1 0 110-2zm-2.93 7.07a1 1 0 01-1.41 0l-.71-.71a1 1 0 011.41-1.41l.71.71a1 1 0 010 1.41zM12 20a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zm-7.07-2.93a1 1 0 010-1.41l.71-.71a1 1 0 111.41 1.41l-.71.71a1 1 0 01-1.41 0zM3 11h1a1 1 0 110 2H3a1 1 0 110-2zm1.93-7.07a1 1 0 011.41 0l.71.71a1 1 0 01-1.41 1.41l-.71-.71a1 1 0 010-1.41z"/>
          </svg>
          <button @click="toggleDark()" role="switch" :aria-checked="dark"
                  class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none"
                  :class="dark ? 'bg-indigo-600' : 'bg-gray-300'">
            <span class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                  :class="dark ? 'translate-x-6' : 'translate-x-1'"></span>
          </button>
          <!-- Moon icon -->
          <svg class="w-4 h-4 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z"/>
          </svg>
        </div>

        <button @click="logout"
                class="px-3 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-medium">
          Logout
        </button>
      </div>
    </header>

    <!-- Camera Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-4 items-stretch">
      <!-- Selected Camera Player -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200 dark:border-gray-700">
        <div class="flex items-center gap-2 mb-2 flex-wrap">
          <h2 class="text-base sm:text-lg font-semibold text-red-600">Selected Camera</h2>
          <select v-model="selectedCam"
                  class="ml-auto w-36 h-7 px-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100">
            <option v-for="cam in cameras" :key="cam.id" :value="cam.id">{{ cam.name }}</option>
          </select>
        </div>
        <div class="relative w-full rounded-md overflow-hidden bg-black" style="padding-top:56.25%">
          <div class="absolute inset-0">
            <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
          </div>
        </div>
      </div>

      <!-- All Cameras 3-column grid (prepared for future cameras) -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200 dark:border-gray-700">
        <h2 class="text-base sm:text-lg font-semibold text-red-600 mb-2">All Cameras</h2>
        <div class="grid grid-cols-3 gap-2">
          <div v-for="cam in cameras" :key="cam.id"
               class="relative aspect-video rounded-md overflow-hidden cursor-pointer border-2"
               :class="selectedCam === cam.id ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'"
               @click="selectedCam = cam.id">
            <img :src="cam.thumbnail" alt="Camera thumbnail"
                 class="w-full h-full object-cover" />
            <span class="absolute bottom-0.5 left-0.5 text-xs font-medium px-1 py-0.5 rounded leading-tight"
                  :class="selectedCam === cam.id ? 'bg-red-600 text-white' : 'bg-black bg-opacity-60 text-white'">
              {{ cam.name }}
            </span>
            <span class="absolute top-0.5 right-0.5 w-2 h-2 rounded-full border border-white shadow"
                  :class="cameraOnline(cam.id) ? 'bg-green-500 animate-pulse' : 'bg-red-500'"></span>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Bar -->
    <StatsBar
      :camera="showAllCams ? 'all' : selectedCam"
      :filter="activeFilter"
      :customFrom="activeFilter === 'custom' ? customFromISO : null"
      :customTo="activeFilter === 'custom' ? customToISO : null"
    />

    <!-- Timeline Scrubber -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200 dark:border-gray-700 mb-3 mt-3 min-h-[260px]">
      <div class="flex items-center gap-2 flex-wrap mb-2">
        <h2 class="text-base sm:text-lg font-semibold text-red-600">Timeline</h2>
        <div class="ml-auto flex items-center gap-2">
          <button @click="shiftDate(-1)" class="h-8 w-8 flex items-center justify-center rounded border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 text-sm transition">
            ◀
          </button>
          <input type="date" v-model="timelineDate"
                 class="h-8 px-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100" />
          <button @click="shiftDate(1)" class="h-8 w-8 flex items-center justify-center rounded border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 text-sm transition">
            ▶
          </button>
          <button @click="timelineDate = todayStr()"
                  class="h-8 px-2 rounded text-xs font-medium transition"
                  :class="timelineDate === todayStr()
                    ? 'bg-red-600 text-white'
                    : 'border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'">
            Today
          </button>
        </div>
      </div>
      <TimelineScrubber
        :date="timelineDate"
        :camera="showAllCams ? 'all' : selectedCam"
      />
    </div>

    <!-- Filter Row (for table & chart) -->
    <div class="flex items-center gap-2 flex-wrap mb-3">
      <select v-model="activeFilter"
              class="h-8 px-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100">
        <option value="day">Last 1 Day</option>
        <option value="week">Last 1 Week</option>
        <option value="month">Last 1 Month</option>
        <option value="3months">Last 3 Months</option>
        <option value="year">Last 1 Year</option>
        <option value="custom">Custom Range</option>
      </select>
      <template v-if="activeFilter === 'custom'">
        <input type="date" v-model="customFrom"
               class="h-8 px-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100" />
        <span class="text-sm text-gray-400">to</span>
        <input type="date" v-model="customTo"
               class="h-8 px-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100" />
      </template>

      <!-- Status filter -->
      <select v-model="filterStatus"
              class="h-8 px-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100">
        <option value="all">All Status</option>
        <option value="added">Detected</option>
        <option value="sold">Sold</option>
        <option value="restock">Restocked</option>
        <option value="missing">Missing</option>
      </select>

      <!-- Confidence filter -->
      <div class="flex items-center gap-1.5">
        <span class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">Conf ≥</span>
        <input type="range" min="0" max="99" step="1" v-model.number="minConfidence"
               class="w-20 h-1.5 accent-red-600 cursor-pointer" />
        <span class="text-xs font-medium w-8 text-gray-700 dark:text-gray-200">{{ minConfidence }}%</span>
        <button v-if="minConfidence > 0" @click="minConfidence = 0"
                class="text-xs text-gray-400 hover:text-red-500 leading-none">✕</button>
      </div>

      <!-- Cam toggle -->
      <div class="ml-auto flex items-center gap-2 select-none">
        <span class="text-sm font-medium" :class="!showAllCams ? 'text-red-600' : 'text-gray-400'">
          <span class="hidden sm:inline">Selected Cam</span><span class="sm:hidden">Cam</span>
        </span>
        <button @click="showAllCams = !showAllCams" role="switch" :aria-checked="showAllCams"
                class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none"
                :class="showAllCams ? 'bg-red-600' : 'bg-gray-300'">
          <span class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                :class="showAllCams ? 'translate-x-6' : 'translate-x-1'"></span>
        </button>
        <span class="text-sm font-medium" :class="showAllCams ? 'text-red-600' : 'text-gray-400'">All</span>
      </div>
    </div>

    <!-- Table + Chart -->
    <section class="grid grid-cols-1 xl:grid-cols-2 gap-3 items-stretch">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200 dark:border-gray-700 min-h-[400px]">
        <h2 class="text-base sm:text-lg font-semibold text-red-600 mb-2">Recent Events</h2>
        <EventTable
          :filter="activeFilter"
          :camera="showAllCams ? 'all' : selectedCam"
          :customFrom="activeFilter === 'custom' ? customFromISO : null"
          :customTo="activeFilter === 'custom' ? customToISO : null"
          :minConfidence="minConfidence"
          :filterStatus="filterStatus"
        />
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200 dark:border-gray-700 min-h-[400px]">
        <h2 class="text-base sm:text-lg font-semibold text-red-600 mb-2">Product Count Statistics</h2>
        <CountChart
          :filter="activeFilter"
          :camera="showAllCams ? 'all' : selectedCam"
          :customFrom="activeFilter === 'custom' ? customFromISO : null"
          :customTo="activeFilter === 'custom' ? customToISO : null"
          :darkMode="dark"
        />
      </div>
    </section>

    <!-- Customer Traffic (people / occupancy) -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-3 sm:p-4 flex flex-col border border-gray-200 dark:border-gray-700 mt-3 mb-3">
      <PeopleTrafficChart
        :filter="activeFilter"
        :camera="showAllCams ? 'all' : selectedCam"
        :customFrom="activeFilter === 'custom' ? customFromISO : null"
        :customTo="activeFilter === 'custom' ? customToISO : null"
        :darkMode="dark"
      />
    </div>

    <ToastNotif :toasts="toasts" />
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDarkMode } from '../useDarkMode.js'
import LivePlayer  from '../components/LivePlayer.vue'
import CountChart  from '../components/CountChart.vue'
import EventTable  from '../components/EventTable.vue'
import StatsBar    from '../components/StatsBar.vue'
import ToastNotif  from '../components/ToastNotif.vue'
import TimelineScrubber from '../components/TimelineScrubber.vue'
import PeopleTrafficChart from '../components/PeopleTrafficChart.vue'
import API from '../api'

const { dark, toggleDark } = useDarkMode()

const cameras = [
  { id: 'cam1', name: 'Sudirman', thumbnail: '/images/sudirman.jpg' },
]

const selectedCam  = ref('cam1')
const activeFilter = ref('month')
const showAllCams  = ref(false)
const customFrom   = ref('')
const customTo     = ref('')
const filterStatus = ref('all')
const minConfidence = ref(0)
const idleWarning  = ref(false)

// Timeline date (WIB)
function todayStr () {
  const d = new Date()
  const wib = new Date(d.getTime() + (d.getTimezoneOffset() + 7 * 60) * 60000)
  return `${wib.getFullYear()}-${String(wib.getMonth()+1).padStart(2,'0')}-${String(wib.getDate()).padStart(2,'0')}`
}
const timelineDate = ref(todayStr())
function shiftDate (delta) {
  const d = new Date(timelineDate.value + 'T00:00:00')
  d.setDate(d.getDate() + delta)
  timelineDate.value = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

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

// ── Idle timeout (1 hour) ─────────────────────────────────────────────────────
const IDLE_LIMIT_MS = 60 * 60 * 1000
const IDLE_WARN_MS  = 55 * 60 * 1000
let idleTimer = null
let warnTimer = null

function resetIdleTimer() {
  idleWarning.value = false
  clearTimeout(idleTimer); clearTimeout(warnTimer)
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

// ── Toast notifications ────────────────────────────────────────────────────────
const STATUS_LABELS = { added: 'Detected', sold: 'Sold', restock: 'Restocked' }
const toasts = ref([])
let toastIdCounter = 0
const toastWs = new WebSocket(`${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/events`)
toastWs.onmessage = (msg) => {
  const ev = JSON.parse(msg.data)
  const id = ++toastIdCounter
  toasts.value = [
    { id, brand: ev.product_brand || 'Unknown', product: ev.product_name || 'Unknown',
      event_type: ev.event_type, statusLabel: STATUS_LABELS[ev.event_type] || ev.event_type || '—' },
    ...toasts.value,
  ].slice(0, 3)
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 4000)
}

onUnmounted(() => {
  clearInterval(statusInterval)
  clearTimeout(idleTimer); clearTimeout(warnTimer)
  ACTIVITY_EVENTS.forEach(e => document.removeEventListener(e, resetIdleTimer))
  toastWs.close()
})
</script>
