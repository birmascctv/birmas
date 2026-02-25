<template>
  <div class="dashboard bg-gray-900 min-h-screen px-10 py-5 text-white">

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
      <div class="bg-gray-800 rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-700">
        <h2 class="text-lg font-semibold text-red-600 mb-2">Selected Camera</h2>
        <select v-model="selectedCam"
                class="w-40 mb-2 h-7 px-2 py-0.5 border border-gray-600 rounded text-sm leading-tight bg-gray-700 text-white">
          <option v-for="n in 9" :key="n" :value="`cam${n}`">Cam {{n}}</option>
        </select>
        <div class="relative aspect-video bg-black rounded-md overflow-hidden flex-1">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Grid Cameras -->
      <div class="bg-gray-800 rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-700">
        <h2 class="text-lg font-semibold text-red-600 mb-2">All Cameras</h2>
        <div class="grid grid-cols-3 gap-2 flex-1">
          <div v-for="n in 9" :key="n"
               class="relative aspect-video rounded-md overflow-hidden cursor-pointer flex items-center justify-center border border-gray-700"
               :class="selectedCam === `cam${n}` ? 'bg-red-700 text-white' : 'bg-gray-700 text-gray-400'"
               @click="selectedCam = `cam${n}`">
            <span class="absolute bottom-2 left-2 text-xs font-medium px-2 py-0.5 rounded"
                  :class="selectedCam === `cam${n}` ? 'bg-red-600 text-white' : 'bg-gray-500 text-white'">
              Cam {{n}}
            </span>
            <LivePlayer v-if="selectedCam === `cam${n}`" :src="`/stream/cam${n}/index.m3u8`" />
          </div>
        </div>
      </div>
    </section>

    <!-- Unified Filter -->
    <div class="flex items-center justify-between mb-3">
      <select v-model="activeFilter"
              class="w-40 h-7 px-2 py-0.5 border border-gray-600 rounded text-sm leading-tight bg-gray-700 text-white">
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
      <div class="bg-gray-800 rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-700">
        <h2 class="text-lg font-semibold text-red-600 mb-2">Recent Events</h2>
        <EventTable :filter="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
      </div>

      <!-- Chart -->
      <div class="bg-gray-800 rounded-lg shadow-sm p-4 flex flex-col h-full border border-gray-700">
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

const selectedCam = ref('cam1')
const activeFilter = ref('day')
const showAllCams = ref(false)

const router = useRouter()
const logout = () => {
  localStorage.removeItem('auth')
  router.push('/login')
}
</script>
