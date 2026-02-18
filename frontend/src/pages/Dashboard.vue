#dashboard.vue

<template>
  <div class="dashboard bg-slate-100 min-h-screen p-4">

    <!-- Header -->
    <header class="mb-4 rounded-xl bg-indigo-100 p-4 shadow">
      <h1 class="text-2xl font-bold text-indigo-900 flex items-center gap-2">
        📹 CCTV Dashboard
      </h1>
    </header>

    <!-- Live Video (centered, 2/3 width) -->
    <section class="bg-white rounded-xl shadow p-4 flex justify-center">
      <div class="w-full md:w-2/3">
        <h2 class="text-lg font-semibold text-slate-700 mb-3">
          Live Camera Feed
        </h2>

        <!-- 16:9 container -->
        <div class="relative aspect-video bg-black rounded-lg overflow-hidden">
          <LivePlayer />
        </div>
      </div>
    </section>

    <!-- Bottom section -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">

      <!-- Events Table -->
      <div class="bg-white rounded-xl shadow p-4 h-[420px] flex flex-col">
        <h2 class="text-lg font-semibold text-slate-700 mb-2">
          Recent Events
        </h2>

        <!-- Scroll only here -->
        <div class="flex-1 overflow-y-auto">
          <EventTable />
        </div>
      </div>

      <!-- Chart -->
      <div class="bg-white rounded-xl shadow p-4 h-[420px]">
        <h2 class="text-lg font-semibold text-slate-700 mb-2">
          Product Count Statistics
        </h2>
        <CountChart />
      </div>

    </section>

  </div>
</template>

<script setup>
import LivePlayer from '../components/LivePlayer.vue'
import CountChart from '../components/CountChart.vue'
import EventTable from '../components/EventTable.vue'
</script>

<style scoped>
.card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}

.card-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: #1e293b; /* slate-800 */
  margin-bottom: 12px;
}
</style>
