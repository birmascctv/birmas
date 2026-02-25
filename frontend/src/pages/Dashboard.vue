<template>
  <div class="dashboard bg-slate-100 min-h-screen p-6">

    <!-- Header -->
    <header class="mb-10">
      <h1 class="text-5xl font-extrabold text-indigo-900 tracking-wide">
        Birmas
      </h1>
    </header>

    <!-- Camera Section (split half page each) -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">

      <!-- Main Selected Camera -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col">
        <h2 class="text-2xl font-semibold text-slate-700 mb-4">Selected Camera</h2>
        <select v-model="selectedCam" class="mb-4 p-3 border rounded text-lg">
          <option v-for="n in 9" :key="n" :value="`cam${n}`">Cam {{n}}</option>
        </select>
        <div class="relative aspect-video bg-black rounded-lg overflow-hidden">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Grid Cameras -->
      <div class="bg-white rounded-xl shadow p-6">
        <h2 class="text-2xl font-semibold text-slate-700 mb-4">All Cameras</h2>
        <div class="grid grid-cols-3 gap-3">
          <div v-for="n in 9" :key="n" class="relative aspect-video bg-black rounded overflow-hidden cursor-pointer"
               @click="selectedCam = `cam${n}`">
            <LivePlayer :src="`/stream/cam${n}/index.m3u8`" />
            <span class="absolute bottom-2 left-2 bg-indigo-600 text-white text-sm px-2 py-0.5 rounded">
              Cam {{n}}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Bottom Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <!-- Events Table with Dropdown Filter -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col">
        <h2 class="text-2xl font-semibold text-slate-700 mb-4">Recent Events</h2>

        <!-- Dropdown Filter -->
        <select v-model="activeFilter" class="mb-4 p-3 border rounded text-lg">
          <option value="last25">Last 25 Events</option>
          <option value="last50">Last 50 Events</option>
          <option value="hour">Last 1 Hour</option>
          <option value="today">Today</option>
        </select>

        <div class="flex-1 overflow-y-auto text-lg">
          <EventTable :filter="activeFilter" />
        </div>
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-xl shadow p-6 flex flex-col">
        <h2 class="text-2xl font-semibold text-slate-700 mb-4">Product Count Statistics</h2>
        <div class="flex-1">
          <CountChart />
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

const selectedCam = ref('cam1')
const activeFilter = ref('last25')
</script>
