<template>
  <div class="dashboard bg-stone-100 min-h-screen px-10 py-5">

    <!-- Header -->
    <header class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-amber-700 tracking-wide">
        Birmas
      </h1>
      <button @click="logout"
              class="px-3 py-1 rounded bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium border border-amber-700">
        Logout
      </button>
    </header>

    <!-- Camera Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-5 items-stretch">
      <!-- Selected Camera -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-stone-200">
        <h2 class="text-lg font-semibold text-amber-700 mb-2">Selected Camera</h2>
        <select v-model="selectedCam" class="w-40 mb-2 h-7 px-2 py-0.5 border border-stone-300 rounded text-sm leading-tight bg-stone-50 text-slate-700">
          <option v-for="n in 9" :key="n" :value="`cam${n}`">Cam {{n}}</option>
        </select>
        <div class="relative aspect-video bg-black rounded-md overflow-hidden flex-1">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Grid Cameras -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-stone-200">
        <h2 class="text-lg font-semibold text-amber-700 mb-2">All Cameras</h2>
        <div class="grid grid-cols-3 gap-2 flex-1">
          <div v-for="n in 9" :key="n"
               class="relative aspect-video rounded-md overflow-hidden cursor-pointer flex items-center justify-center border border-stone-200"
               :class="selectedCam === `cam${n}` ? 'bg-amber-100 text-amber-800' : 'bg-stone-200 text-slate-500'"
               @click="selectedCam = `cam${n}`">
            <span class="absolute bottom-2 left-2 text-xs font-medium px-2 py-0.5 rounded"
                  :class="selectedCam === `cam${n}` ? 'bg-amber-600 text-white' : 'bg-slate-400 text-white'">
              Cam {{n}}
            </span>
            <LivePlayer v-if="selectedCam === `cam${n}`" :src="`/stream/cam${n}/index.m3u8`" />
          </div>
        </div>
      </div>
    </section>

    <!-- Unified Filter -->
    <div class="flex items-center justify-between mb-3">
      <select v-model="activeFilter" class="w-40 h-7 px-2 py-0.5 border border-stone-300 rounded text-sm leading-tight bg-stone-50 text-slate-700">
        <option value="day">Last 1 Day</option>
        <option value="week">Last 1 Week</option>
        <option value="month">Last 1 Month</option>
        <option value="3months">Last 3 Months</option>
        <option value="year">Last 1 Year</option>
      </select>
      <button @click="showAllCams = !showAllCams"
              class="px-3 py-1 rounded bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium border border-amber-700">
        {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
      </button>
    </div>

    <!-- Bottom Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-3 items-stretch">
      <!-- Events Table -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-stone-200">
        <h2 class="text-lg font-semibold text-amber-700 mb-2">Recent Events</h2>
        <EventTable :filter="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
      </div>

      <!-- Chart Section -->
      <div class="grid grid-cols-2 gap-3">
        <!-- Bar Chart -->
        <div class="h-64 bg-white rounded-lg shadow-sm p-4 flex flex-col border border-stone-200">
          <h2 class="text-lg font-semibold text-amber-700 mb-2">Event Frequency</h2>
          <CountChart type="bar" :range="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
        </div>

        <!-- Pie Chart -->
        <div class="h-64 bg-white rounded-lg shadow-sm p-4 flex flex-col border border-stone-200 items-center justify-center">
          <h2 class="text-lg font-semibold text-amber-700 mb-2">Event Distribution</h2>
          <CountChart type="pie" :range="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
        </div>
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
