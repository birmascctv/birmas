<template>
  <div class="dashboard bg-slate-100 min-h-screen px-16 py-8"> <!-- wide margins but slimmer -->

    <!-- Header -->
    <header class="mb-10">
      <h1 class="text-4xl font-extrabold text-indigo-900 tracking-wide">
        Birmas
      </h1>
    </header>

    <!-- Camera Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">

      <!-- Selected Camera -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col">
        <h2 class="text-2xl font-bold text-slate-800 mb-3">Selected Camera</h2>
        <select v-model="selectedCam" class="mb-3 p-2 border rounded text-base">
          <option value="cam">Camera</option>
        </select>
        <div class="relative aspect-video bg-black rounded-lg overflow-hidden">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Grid Cameras -->
      <div class="bg-white rounded-xl shadow p-6">
        <h2 class="text-2xl font-bold text-slate-800 mb-3">All Cameras</h2>
        <div class="grid grid-cols-3 gap-2">
          <!-- Only one real camera, rest placeholders -->
          <div class="relative aspect-video bg-black rounded overflow-hidden cursor-pointer"
               @click="selectedCam = 'cam'">
            <LivePlayer :src="`/stream/cam/index.m3u8`" />
            <span class="absolute bottom-2 left-2 bg-indigo-600 text-white text-xs px-2 py-0.5 rounded">
              Camera
            </span>
          </div>
          <div v-for="n in 8" :key="n" class="relative aspect-video bg-gray-200 rounded flex items-center justify-center text-slate-400">
            No Camera
          </div>
        </div>
      </div>
    </section>

    <!-- Bottom Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <!-- Events Table -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-2xl font-bold text-slate-800">Recent Events</h2>
          <button @click="showAllCams = !showAllCams"
                  class="px-3 py-1 rounded bg-indigo-100 hover:bg-indigo-200 text-indigo-800 text-sm font-medium">
            {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
          </button>
        </div>

        <!-- Unified Dropdown Filter -->
        <select v-model="activeFilter" class="mb-3 p-2 border rounded text-base">
          <option value="day">Last 1 Day</option>
          <option value="week">Last 1 Week</option>
          <option value="month">Last 1 Month</option>
          <option value="3months">Last 3 Months</option>
          <option value="year">Last 1 Year</option>
        </select>

        <div class="flex-1 overflow-y-auto text-base">
          <EventTable :filter="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
        </div>
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-2xl font-bold text-slate-800">Product Count Statistics</h2>
          <button @click="showAllCams = !showAllCams"
                  class="px-3 py-1 rounded bg-indigo-100 hover:bg-indigo-200 text-indigo-800 text-sm font-medium">
            {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
          </button>
        </div>

        <!-- Unified Dropdown Filter -->
        <select v-model="chartRange" class="mb-3 p-2 border rounded text-base">
          <option value="day">Last 1 Day</option>
          <option value="week">Last 1 Week</option>
          <option value="month">Last 1 Month</option>
          <option value="3months">Last 3 Months</option>
          <option value="year">Last 1 Year</option>
        </select>

        <div class="flex-1">
          <CountChart :range="chartRange" :camera="showAllCams ? 'all' : selectedCam" />
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import LivePlayer from '../components/LivePlayer.vue'
import CountChart from '../components/CountChart.vue'
import EventTable from '../components/EventTable.vue'

const selectedCam = ref('cam')   // simplified to just one camera
const activeFilter = ref('day')
const chartRange = ref('day')
const showAllCams = ref(false)
</script>
