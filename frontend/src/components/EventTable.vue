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
      <td>{{ new Date(ev.ts).toLocaleString() }}</td>
      <td>{{ ev.camera_id }}</td>
      <td>{{ ev.label }}</td>
      <td>{{ (ev.confidence*100).toFixed(1) }}%</td>
    </tr></tbody>
  </table>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import API from '@/api.js' // Ensure you import your API instance

const events = ref([])

onMounted(async () => {
  try {
    // Axios simplifies the request:
    const res = await API.get('/events', { params: { camera_id: 'cam1' } })
    
    // Axios puts the parsed JSON body in res.data
    events.value = res.data 
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