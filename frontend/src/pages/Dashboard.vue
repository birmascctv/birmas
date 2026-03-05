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
          <!-- Live feed only for selected camera -->
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
          </div>
        </div>
      </div>
    </section>

    <!-- Unified Filter -->
    <div class="flex items-center justify-between mb-3">
      <select v-model="activeFilter"
              class="w-40 h-7 px-2 py-0.5 border border-gray-300 rounded text-sm leading-tight bg-gray-100 text-gray-800">
        <option value="day">Last 1 Day</option>
        <option value="week">Last 1 Week</option>
        <option value="month">Last 1 Month</option>
        <option value="3months">Last 3 Months</option>
        <option value="year">Last 1 Year</option>
      </select>
      <button @click="showAllCams = !showAllCams"
              class="px-3 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-medium border border-red-700">
        {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
      </button>
    </div>

    <!-- Bottom Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-3 items-stretch">
      <!-- Events Table -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-200">
        <h2 class="text-lg font-semibold text-red-600 mb-2">Recent Events</h2>
        <EventTable :filter="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-200">
        <h2 class="text-lg font-semibold text-red-600 mb-2">Product Count Statistics</h2>
        <CountChart :range="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import LivePlayer from '../components/LivePlayer.vue'
import CountChart from '../components/CountChart.vue'
import EventTable from '../components/EventTable.vue'

const cameras = [
  { id: 'cam1', name: 'Tebet', thumbnail: '/images/tebet.jpg' },
  // Add more cameras later like:
  // { id: 'cam2', name: 'Kemang', thumbnail: '/images/kemang.jpg' },
  // { id: 'cam3', name: 'Senayan', thumbnail: '/images/senayan.jpg' },
]

const selectedCam = ref('cam1')
const activeFilter = ref('day')
const showAllCams = ref(false)

const router = useRouter()
const logout = () => {
  localStorage.removeItem('auth')
  router.push('/login')
}
</script>
