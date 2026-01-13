<template>
  <table>
    <thead><tr><th>Time</th><th>Camera</th><th>Label</th><th>Conf</th></tr></thead>
    <tbody><tr v-for="ev in events" :key="ev.ts">
      <td>{{ ev.ts }}</td><td>{{ ev.camera_id }}</td><td>{{ ev.label }}</td>
      <td>{{ (ev.confidence*100).toFixed(1) }}%</td>
    </tr></tbody>
  </table>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const events = ref([])
onMounted(async () => {
  // Replace with your droplet IP or domain
  const res = await fetch('http://localhost:8000/events?camera_id=cam1')
  events.value = await res.json()
})
</script>