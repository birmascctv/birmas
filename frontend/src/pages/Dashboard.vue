<template>
  <div class="dashboard bg-slate-100 min-h-screen p-4">

    <!-- Header -->
    <header class="mb-4 rounded-xl bg-indigo-100 p-4 shadow">
      <h1 class="text-2xl font-bold text-indigo-900 flex items-center gap-2">
        📹 CCTV Dashboard
      </h1>
    </header>

    <!-- Camera Section -->
    <section class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">

      <!-- Main Selected Camera -->
      <div class="col-span-2 bg-white rounded-xl shadow p-4 flex flex-col">
        <h2 class="text-lg font-semibold text-slate-700 mb-2">Selected Camera</h2>
        <select v-model="selectedCam" class="mb-3 p-2 border rounded">
          <option v-for="n in 9" :key="n" :value="`cam${n}`">Cam {{n}}</option>
        </select>
        <div class="relative aspect-video bg-black rounded-lg overflow-hidden">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Thumbnail Grid -->
      <div class="bg-white rounded-xl shadow p-4">
        <h2 class="text-lg font-semibold text-slate-700 mb-2">All Cameras</h2>
        <div class="grid grid-cols-3 gap-2">
          <div v-for="n in 9" :key="n" class="relative aspect-video bg-black rounded overflow-hidden cursor-pointer"
               @click="selectedCam = `cam${n}`">
            <LivePlayer :src="`/stream/cam${n}/index.m3u8`" />
            <span class="absolute bottom-1 left-1 bg-indigo-600 text-white text-xs px-2 py-0.5 rounded">
              Cam {{n}}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Bottom Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Events Table -->
      <div class="bg-white rounded-xl shadow p-4 flex flex-col">
        <h2 class="text-lg font-semibold text-slate-700 mb-2">Recent Events</h2>
        <div class="flex-1 overflow-y-auto">
          <EventTable />
        </div>
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-xl shadow p-4 flex flex-col">
        <h2 class="text-lg font-semibold text-slate-700 mb-2">Product Count Statistics</h2>
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
</script>
