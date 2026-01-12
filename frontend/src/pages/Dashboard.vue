<template>
  <div class="dashboard">
    <LivePlayer />
    <CountChart />
    <EventTable />
  </div>
</template>

<script setup>
import LivePlayer from '../components/LivePlayer.vue'
import CountChart from '../components/CountChart.vue'
import EventTable from '../components/EventTable.vue'
</script>

<style>
.dashboard { display: grid; grid-template-columns: 2fr 1fr; gap: 12px; }
</style>