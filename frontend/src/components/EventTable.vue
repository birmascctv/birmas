<template>
  <table class="text-base w-full border-collapse text-center">
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
import { ref, onMounted, computed, watch } from 'vue'
import API from '@/api.js'

const props = defineProps({
  filter: String,
  camera: String
})

const events = ref([])

const loadData = async () => {
  try {
    const params = props.camera === 'all' ? {} : { camera_id: props.camera }
    const res = await API.get('/events', { params })
    events.value = res.data
  } catch (err) {
    console.error("Error loading events:", err)
  }
}

onMounted(loadData)
watch(() => [props.filter, props.camera], loadData)

const filteredEvents = computed(() => {
  let data = events.value
  const now = Date.now()

  if (props.filter === 'day') {
    const cutoff = now - 24*60*60*1000
    data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
  } else if (props.filter === 'week') {
    const cutoff = now - 7*24*60*60*1000
    data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
  } else if (props.filter === 'month') {
    const cutoff = now - 30*24*60*60*1000
    data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
  } else if (props.filter === '3months') {
    const cutoff = now - 90*24*60*60*1000
    data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
  } else if (props.filter === 'year') {
    const cutoff = now - 365*24*60*60*1000
    data = data.filter(ev => new Date(ev.ts).getTime() >= cutoff)
  }

  return data
})
</script>
