<template>
  <div class="dashboard bg-slate-100 min-h-screen px-20 py-10"> <!-- wide margins -->

    <!-- Header -->
    <header class="mb-12">
      <h1 class="text-5xl font-extrabold text-indigo-900 tracking-wide">
        Birmas
      </h1>
    </header>

    <!-- Camera Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-12">

      <!-- Selected Camera -->
      <div class="bg-white rounded-xl shadow p-8 flex flex-col">
        <h2 class="text-3xl font-bold text-slate-800 mb-4">Selected Camera</h2>
        <select v-model="selectedCam" class="mb-4 p-3 border rounded text-lg">
          <option value="cam">Camera</option>
        </select>
        <div class="relative aspect-video bg-black rounded-lg overflow-hidden">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Grid Cameras -->
      <div class="bg-white rounded-xl shadow p-8">
        <h2 class="text-3xl font-bold text-slate-800 mb-4">All Cameras</h2>
        <div class="grid grid-cols-3 gap-3">
          <div class="relative aspect-video bg-black rounded overflow-hidden cursor-pointer"
               @click="selectedCam = 'cam'">
            <LivePlayer :src="`/stream/cam/index.m3u8`" />
            <span class="absolute bottom-2 left-2 bg-indigo-600 text-white text-sm px-2 py-0.5 rounded">
              Camera
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Bottom Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-10">
      <!-- Events Table -->
      <div class="bg-white rounded-xl shadow p-8 flex flex-col">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-3xl font-bold text-slate-800">Recent Events</h2>
          <button @click="showAllCams = !showAllCams"
                  class="px-3 py-1 rounded bg-indigo-100 hover:bg-indigo-200 text-indigo-800 font-medium">
            {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
          </button>
        </div>

        <!-- Dropdown Filter -->
        <select v-model="activeFilter" class="mb-4 p-3 border rounded text-lg">
          <option value="last25">Last 25 Events</option>
          <option value="last50">Last 50 Events</option>
          <option value="hour">Last 1 Hour</option>
          <option value="today">Today</option>
        </select>

        <div class="flex-1 overflow-y-auto text-lg">
          <EventTable :filter="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
        </div>
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-xl shadow p-8 flex flex-col">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-3xl font-bold text-slate-800">Product Count Statistics</h2>
          <button @click="showAllCams = !showAllCams"
                  class="px-3 py-1 rounded bg-indigo-100 hover:bg-indigo-200 text-indigo-800 font-medium">
            {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
          </button>
        </div>

        <!-- Dropdown Filter -->
        <select v-model="chartRange" class="mb-4 p-3 border rounded text-lg">
          <option value="day">Last 1 Day</option>
          <option value="week">Last 1 Week</option>
          <option value="month">Last 1 Month</option>
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

const selectedCam = ref('cam')   // simplified to just "cam"
const activeFilter = ref('last25')
const chartRange = ref('day')
const showAllCams = ref(false)
</script>
