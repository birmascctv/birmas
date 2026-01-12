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
onMounted(() => {
  const ws = new WebSocket('ws://100.87.93.95:8000/ws/events')
  ws.onmessage = m => { const ev = JSON.parse(m.data); events.value.unshift(ev); if (events.value.length>50) events.value.pop() }
})
</script>