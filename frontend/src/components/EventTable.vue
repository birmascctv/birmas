<template>
  <table>
    <thead>
      <tr>
        <th>Time</th>
        <th>Camera</th>
        <th>Label</th>
        <th>Conf</th>
      </tr>
    </thead>
    <tbody><tr v-for="ev in events" :key="ev.ts">
      <td>{{ new Date(ev.ts).toLocaleString }}</td>
      <td>{{ ev.camera_id }}</td>
      <td>{{ ev.label }}</td>
      <td>{{ (ev.confidence*100).toFixed(1) }}%</td>
    </tr></tbody>
  </table>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const events = ref([])
onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/events?camera_id=cam1')
    if (!res.ok) throw new Error("Failed to fetch events")
    events.value = await res.json()
  } catch (err) {
    console.error("Error loading events:", err)
  }
})
</script>

<style scoped>
table {
  border-collapse: collapse;
  width: 100%;
}
th, td {
  border: 1px solid #ccc;
  padding: 8px;
}
th {
  background: #f5f5f5;
}
</style>