<template>
  <div class="dashboard bg-slate-100 min-h-screen px-12 py-6">

    <!-- Header -->
    <header class="mb-8">
      <h1 class="text-3xl font-extrabold text-indigo-900 tracking-wide">
        Birmas
      </h1>
    </header>

    <!-- Camera Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
      <!-- Selected Camera -->
      <div class="bg-white rounded-xl shadow p-5 flex flex-col h-full">
        <h2 class="text-xl font-bold text-slate-800 mb-3">Selected Camera</h2>
        <select v-model="selectedCam" class="w-32 mb-3 p-2 border rounded text-sm">
          <option v-for="n in 9" :key="n" :value="`cam${n}`">Cam {{n}}</option>
        </select>
        <div class="relative aspect-video bg-black rounded-lg overflow-hidden">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Grid Cameras -->
      <div class="bg-white rounded-xl shadow p-5 flex flex-col h-full">
        <h2 class="text-xl font-bold text-slate-800 mb-3">All Cameras</h2>
        <div class="grid grid-cols-3 gap-2">
          <div v-for="n in 9" :key="n"
               class="relative aspect-video rounded overflow-hidden cursor-pointer flex items-center justify-center"
               :class="selectedCam === `cam${n}` ? 'bg-indigo-200 text-indigo-800' : 'bg-gray-200 text-slate-500'"
               @click="selectedCam = `cam${n}`">
            <span class="absolute bottom-2 left-2 text-xs font-medium px-2 py-0.5 rounded"
                  :class="selectedCam === `cam${n}` ? 'bg-indigo-600 text-white' : 'bg-slate-400 text-white'">
              Cam {{n}}
            </span>
            <LivePlayer v-if="selectedCam === `cam${n}`" :src="`/stream/cam${n}/index.m3u8`" />
          </div>
        </div>
      </div>
    </section>

    <!-- Bottom Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Events Table -->
      <div class="bg-white rounded-xl shadow p-5 flex flex-col h-full">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-xl font-bold text-slate-800">Recent Events</h2>
          <button @click="showAllCams = !showAllCams"
                  class="px-3 py-1 rounded bg-indigo-100 hover:bg-indigo-200 text-indigo-800 text-xs font-medium">
            {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
          </button>
        </div>

        <!-- Unified Dropdown Filter -->
        <select v-model="activeFilter" class="w-32 mb-3 p-2 border rounded text-sm">
          <option value="day">Last 1 Day</option>
          <option value="week">Last 1 Week</option>
          <option value="month">Last 1 Month</option>
          <option value="3months">Last 3 Months</option>
          <option value="year">Last 1 Year</option>
        </select>

        <EventTable :filter="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-xl shadow p-5 flex flex-col h-full">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-xl font-bold text-slate-800">Product Count Statistics</h2>
          <button @click="showAllCams = !showAllCams"
                  class="px-3 py-1 rounded bg-indigo-100 hover:bg-indigo-200 text-indigo-800 text-xs font-medium">
            {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
          </button>
        </div>

        <!-- Unified Dropdown Filter -->
        <select v-model="chartRange" class="w-32 mb-3 p-2 border rounded text-sm">
          <option value="day">Last 1 Day</option>
          <option value="week">Last 1 Week</option>
          <option value="month">Last 1 Month</option>
          <option value="3months">Last 3 Months</option>
          <option value="year">Last 1 Year</option>
        </select>

        <CountChart :range="chartRange" :camera="showAllCams ? 'all' : selectedCam" />
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import LivePlayer from '../components/LivePlayer.vue'
import CountChart from '../components/CountChart.vue'
import EventTable from '../components/EventTable.vue'

const selectedCam = ref('cam1')
const activeFilter = ref('day')
const chartRange = ref('day')
const showAllCams = ref(false)
</script>
