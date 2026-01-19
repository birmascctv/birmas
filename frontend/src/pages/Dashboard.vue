<template>
  <div class="dashboard-wrapper">
    <!-- Header -->
    <div class="header">
      <h1 class="title">Admin Dashboard</h1>

      <!-- Tailwind forms plugin input -->
      <input
        type="text"
        placeholder="Search events..."
        class="rounded-md w-64"
      />
    </div>

    <!-- Original grid (UNCHANGED logic) -->
    <div class="dashboard">
      <LivePlayer />
      <CountChart />
      <EventTable />
    </div>
  </div>
</template>

<script setup>
import LivePlayer from '../components/LivePlayer.vue'
import CountChart from '../components/CountChart.vue'
import EventTable from '../components/EventTable.vue'
</script>

<style>
.dashboard-wrapper {
  padding: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dashboard {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
}
</style>
