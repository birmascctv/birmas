<template>
  <div class="flex-1">
    <table v-if="paginatedEvents && paginatedEvents.length"
           class="text-sm w-full border-collapse text-center">
      <thead>
        <tr>
          <th class="border px-3 py-2 bg-slate-100">Time</th>
          <th class="border px-3 py-2 bg-slate-100">Camera</th>
          <th class="border px-3 py-2 bg-slate-100">Brand</th>
          <th class="border px-3 py-2 bg-slate-100">Product</th>
          <th class="border px-3 py-2 bg-slate-100">Conf</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ev in paginatedEvents" :key="ev.id">
          <td class="border px-3 py-2 text-gray-700">
            {{
              ev.ts
                ? new Date(ev.ts).toISOString().replace('T', ' ').split('.')[0]
                : '—'
            }}
          </td>

          <td class="border px-3 py-2">{{ ev.camera_id || '—' }}</td>
          <td class="border px-3 py-2">{{ ev.product_brand || '—' }}</td>
          <td class="border px-3 py-2">{{ ev.product_name || '—' }}</td>

          <td class="border px-3 py-2">
            {{
              ev.confidence !== undefined && ev.confidence !== null
                ? (Number(ev.confidence) * 100).toFixed(1) + '%'
                : '—'
            }}
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="text-center text-slate-400 py-10">No data available</div>

    <!-- Pagination -->
    <div class="flex justify-center gap-2 mt-3" v-if="totalPages > 1">
      <button @click="currentPage = Math.max(1, currentPage - 1)"
              class="px-2 py-1 rounded border"
              :disabled="currentPage === 1">
        Prev
      </button>

      <template v-for="n in pagesToShow" :key="n">
        <span v-if="n === '...'">...</span>
        <button v-else
                @click="currentPage = n"
                class="px-2 py-1 rounded border"
                :class="currentPage === n ? 'bg-red-600 text-white' : 'bg-white text-slate-700'">
          {{ n }}
        </button>
      </template>

      <button @click="currentPage = Math.min(totalPages, currentPage + 1)"
              class="px-2 py-1 rounded border"
              :disabled="currentPage === totalPages">
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import API from '../api'

const events = ref([])
const currentPage = ref(1)
const pageSize = 10

// Fetch events from backend
async function loadEvents() {
  try {
    const res = await API.get('/events?camera_id=cam1')
    console.log('Events response:', res.data)
    events.value = res.data
  } catch (err) {
    console.error('Error loading events:', err)
  }
}
loadEvents()

// Pagination
const totalPages = computed(() =>
  Math.ceil(events.value.length / pageSize)
)

const paginatedEvents = computed(() =>
  events.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize)
)
</script>
