<template>
  <div class="dashboard bg-stone-100 min-h-screen px-10 py-5">

    <!-- Header -->
    <header class="mb-6">
      <h1 class="text-2xl font-bold text-slate-700 tracking-wide">
        Birmas
      </h1>
    </header>

    <!-- Camera Section -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-5 items-stretch">
      <!-- Selected Camera -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-stone-200">
        <h2 class="text-lg font-semibold text-slate-700 mb-2">Selected Camera</h2>
        <select v-model="selectedCam" class="w-40 mb-2 h-7 px-2 py-0.5 border border-stone-300 rounded text-sm leading-tight bg-stone-50 text-slate-700">
          <option v-for="n in 9" :key="n" :value="`cam${n}`">Cam {{n}}</option>
        </select>
        <div class="relative aspect-video bg-black rounded-md overflow-hidden flex-1">
          <LivePlayer :src="`/stream/${selectedCam}/index.m3u8`" />
        </div>
      </div>

      <!-- Grid Cameras -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-stone-200">
        <h2 class="text-lg font-semibold text-slate-700 mb-2">All Cameras</h2>
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

    <!-- Bottom Section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-3 items-stretch">
      <!-- Events Table -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-stone-200">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-lg font-semibold text-slate-700">Recent Events</h2>
          <button @click="showAllCams = !showAllCams"
                  class="px-3 py-1 rounded bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-medium border border-amber-200">
            {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
          </button>
        </div>

        <select v-model="activeFilter" class="w-40 mb-2 h-7 px-2 py-0.5 border border-stone-300 rounded text-sm leading-tight bg-stone-50 text-slate-700">
          <option value="day">Last 1 Day</option>
          <option value="week">Last 1 Week</option>
          <option value="month">Last 1 Month</option>
          <option value="3months">Last 3 Months</option>
          <option value="year">Last 1 Year</option>
        </select>

        <EventTable :filter="activeFilter" :camera="showAllCams ? 'all' : selectedCam" />
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-lg shadow-sm p-4 flex flex-col h-full border border-stone-200">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-lg font-semibold text-slate-700">Product Count Statistics</h2>
          <button @click="showAllCams = !showAllCams"
                  class="px-3 py-1 rounded bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-medium border border-amber-200">
            {{ showAllCams ? 'Selected Cam Only' : 'All Cams' }}
          </button>
        </div>

        <select v-model="chartRange" class="w-40 mb-2 h-7 px-2 py-0.5 border border-stone-300 rounded text-sm leading-tight bg-stone-50 text-slate-700">
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
