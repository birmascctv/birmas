<template>
  <div class="dashboard bg-slate-100 min-h-screen p-4">
    <!-- Header (Pastel) -->
    <header
      class="mb-4 rounded-lg bg-gradient-to-r from-sky-400 to-indigo-400 px-6 py-4 text-white shadow-sm"
    >
      <h1 class="text-2xl font-semibold tracking-wide">
        📹 CCTV Dashboard
      </h1>
      <p class="text-sm text-white/90">
        Real-time monitoring and event analytics
      </p>
    </header>

    <!-- Live Video (FULL WIDTH, 16:9) -->
    <section class="card">
      <h2 class="card-title">Live Camera Feed</h2>

      <!-- Aspect Ratio Wrapper -->
      <div class="relative w-full overflow-hidden rounded-lg bg-black aspect-video">
        <LivePlayer />
      </div>
    </section>

    <!-- Bottom: Table + Chart -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Events Table (scroll only here) -->
      <div class="card flex flex-col">
        <h2 class="card-title">Recent Events</h2>

        <!-- Scroll container -->
        <div class="flex-1 overflow-y-auto">
          <EventTable />
        </div>
      </div>

      <!-- Chart -->
      <div class="card">
        <h2 class="card-title">People Count Statistics</h2>
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
