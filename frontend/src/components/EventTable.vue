<template>
  <div class="flex-1">
    <table v-if="paginatedEvents.length" class="text-sm w-full border-collapse text-center">
      <thead>
        <tr>
          <th class="border px-3 py-2 bg-slate-100">Time</th>
          <th class="border px-3 py-2 bg-slate-100">Camera</th>
          <th class="border px-3 py-2 bg-slate-100">Label</th>
          <th class="border px-3 py-2 bg-slate-100">Conf</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ev in paginatedEvents" :key="ev.ts">
          <td class="border px-3 py-2">{{ new Date(ev.ts).toLocaleString() }}</td>
          <td class="border px-3 py-2">{{ ev.camera_id }}</td>
          <td class="border px-3 py-2">{{ ev.label }}</td>
          <td class="border px-3 py-2">{{ (ev.confidence*100).toFixed(1) }}%</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="text-center text-slate-400 py-10">No data available</div>

    <!-- Pagination -->
    <div class="flex justify-center gap-2 mt-3" v-if="totalPages > 1">
      <!-- Prev -->
      <button @click="currentPage = Math.max(1, currentPage - 1)"
              class="px-2 py-1 rounded border"
              :disabled="currentPage === 1">
        Prev
      </button>

      <!-- Dynamic pages -->
      <template v-for="n in pagesToShow" :key="n">
        <span v-if="n === '...'">...</span>
        <button v-else
                @click="currentPage = n"
                class="px-2 py-1 rounded border"
                :class="currentPage === n ? 'bg-indigo-600 text-white' : 'bg-white text-slate-700'">
          {{ n }}
        </button>
      </template>

      <!-- Next -->
      <button @click="currentPage = Math.min(totalPages, currentPage + 1)"
              class="px-2 py-1 rounded border"
              :disabled="currentPage === totalPages">
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import API from '@/api.js'

const props = defineProps({ filter: String, camera: String })
const events = ref([])
const currentPage = ref(1)
const pageSize = 25

const loadData = async () => {
  try {
    const params = props.camera === 'all' ? {} : { camera_id: props.camera }
    const res = await API.get('/events', { params })
    events.value = res.data
    currentPage.value = 1
  } catch (err) {
    console.error("Error loading events:", err)
    events.value = []
  }
}

onMounted(loadData)
watch(() => [props.filter, props.camera], loadData)

const filteredEvents = computed(() => {
  let data = events.value
  const now = Date.now()
  if (props.filter === 'day') data = data.filter(ev => new Date(ev.ts).getTime() >= now - 24*60*60*1000)
  else if (props.filter === 'week') data = data.filter(ev => new Date(ev.ts).getTime() >= now - 7*24*60*60*1000)
  else if (props.filter === 'month') data = data.filter(ev => new Date(ev.ts).getTime() >= now - 30*24*60*60*1000)
  else if (props.filter === '3months') data = data.filter(ev => new Date(ev.ts).getTime() >= now - 90*24*60*60*1000)
  else if (props.filter === 'year') data = data.filter(ev => new Date(ev.ts).getTime() >= now - 365*24*60*60*1000)
  return data
})

const totalPages = computed(() => Math.ceil(filteredEvents.value.length / pageSize))

const paginatedEvents = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredEvents.value.slice(start, start + pageSize)
})

const pagesToShow = computed(() => {
  const pages = []
  if (totalPages.value <= 5) {
    for (let i = 1; i <= totalPages.value; i++) pages.push(i)
  } else {
    if (currentPage.value <= 3) {
      pages.push(1, 2, 3, '...', totalPages.value)
    } else if (currentPage.value >= totalPages.value - 2) {
      pages.push(1, '...', totalPages.value - 2, totalPages.value - 1, totalPages.value)
    } else {
      pages.push(1, '...', currentPage.value - 1, currentPage.value, currentPage.value + 1, '...', totalPages.value)
    }
  }
  return pages
})
</script>
