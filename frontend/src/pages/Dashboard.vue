<template>
  <div class="dashboard bg-slate-100 min-h-screen p-4">

    <!-- Header -->
    <header class="mb-6 flex items-center justify-between">
      <h1 class="text-4xl font-extrabold text-indigo-900 tracking-wide">
        Birmas
      </h1>
      <nav class="flex gap-4 text-lg font-semibold text-slate-700">
        <a href="#" class="hover:text-indigo-600">CCTV</a>
        <a href="#" class="hover:text-indigo-600">RFID</a>
      </nav>
    </header>

    <!-- Camera Section (split half page each) -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">

      <!-- Main Selected Camera -->
      <div class="bg-white rounded-xl shadow p-4 flex flex-col">
        <h2 class="text-xl font-semibold text-slate-700 mb-3">Selected Camera</h2>
        <select v-model="selectedCam" class="mb-3 p-2 border rounded text-lg">
          <option v-for="n in 9" :key="n" :value="`cam${n}`">Cam {{n}}</option>
        </select>
        <div class="relative aspect-video bg-black rounded-lg overflow-hidden">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Thumbnail Grid -->
      <div class="bg-white rounded-xl shadow p-4">
        <h2 class="text-xl font-semibold text-slate-700 mb-3">All Cameras</h2>
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
      <!-- Events Table with Filters -->
      <div class="bg-white rounded-xl shadow p-4 flex flex-col">
        <h2 class="text-xl font-semibold text-slate-700 mb-3">Recent Events</h2>

        <!-- Filters -->
        <div class="flex gap-2 mb-3">
          <button v-for="f in filters" :key="f.label"
                  @click="applyFilter(f.type)"
                  class="px-3 py-1 rounded bg-indigo-100 hover:bg-indigo-200 text-indigo-800 font-medium">
            {{ f.label }}
          </button>
        </div>

        <div class="flex-1 overflow-y-auto text-lg">
          <EventTable :filter="activeFilter" />
        </div>
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-xl shadow p-4 flex flex-col">
        <h2 class="text-xl font-semibold text-slate-700 mb-3">Product Count Statistics</h2>
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

// Filters for events
const filters = [
  { label: 'Last 25', type: 'last25' },
  { label: 'Last 50', type: 'last50' },
  { label: 'Last 1 Hour', type: 'hour' },
  { label: 'Today', type: 'today' }
]

const activeFilter = ref('last25')
const applyFilter = (type) => { activeFilter.value = type }
</script>
