<template>
  <div class="dashboard bg-slate-100 min-h-screen p-4">
    <!-- Header -->
    <header class="mb-4 rounded-lg bg-gradient-to-r from-indigo-600 to-blue-600 px-6 py-4 text-white shadow">
      <h1 class="text-2xl font-bold tracking-wide">
        📹 CCTV Dashboard
      </h1>
      <p class="text-sm text-indigo-100">
        Real-time monitoring and event analytics
      </p>
    </header>

    <!-- Live Player -->
    <section class="card">
      <h2 class="card-title">Live Camera Feed</h2>
      <LivePlayer />
    </section>

    <!-- Events Table -->
    <section class="card">
      <h2 class="card-title">Recent Events</h2>
      <EventTable />
    </section>

    <!-- Chart -->
    <section class="card">
      <h2 class="card-title">People Count Statistics</h2>
      <CountChart />
    </section>
  </div>
</template>

<script setup>
import LivePlayer from '../components/LivePlayer.vue'
import CountChart from '../components/CountChart.vue'
import EventTable from '../components/EventTable.vue'
</script>

<style scoped>
.dashboard {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b; /* slate-800 */
  margin-bottom: 12px;
}
</style>
