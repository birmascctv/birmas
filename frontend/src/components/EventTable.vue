<template>
  <table class="text-lg w-full border-collapse text-center">
    <thead>
      <tr>
        <th class="border px-3 py-2 bg-slate-100">Time</th>
        <th class="border px-3 py-2 bg-slate-100">Camera</th>
        <th class="border px-3 py-2 bg-slate-100">Label</th>
        <th class="border px-3 py-2 bg-slate-100">Conf</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="ev in filteredEvents" :key="ev.ts">
        <td class="border px-3 py-2">{{ new Date(ev.ts).toLocaleString() }}</td>
        <td class="border px-3 py-2">{{ ev.camera_id }}</td>
        <td class="border px-3 py-2">{{ ev.label }}</td>
        <td class="border px-3 py-2">{{ (ev.confidence*100).toFixed(1) }}%</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import API from '@/api.js'

const props = defineProps({
  filter: String,
  camera: String
})

const events = ref([])

onMounted(async () => {
  try {
    const params = props.camera === 'all' ? {} : { camera_id: props.camera }
    const res = await API.get('/events', { params })
    events.value = res.data
  } catch (err) {
    console.error("Error loading events:", err)
  }
})

const filteredEvents = computed(() => {
  if (props.filter === 'last25') return events.value.slice(-25)
  if (props.filter === 'last50') return events.value.slice(-50)
  if (props.filter === 'hour') {
    const cutoff = Date.now() - 60*60*1000
    return events.value.filter(ev => new Date(ev.ts).getTime() >= cutoff)
  }
  if (props.filter === 'today') {
    const today = new Date().toDateString()
    const todayEvents = events.value.filter(ev => new Date(ev.ts).toDateString() === today)
    return todayEvents.length > 50 ? todayEvents.filter((_, i) => i % 50 === 0) : todayEvents
  }
  return events.value
})
</script>
