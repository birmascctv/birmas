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
          <!-- First column: lighter text for readability -->
          <td class="border px-3 py-2 text-gray-700">{{ new Date(ev.ts).toLocaleString() }}</td>
          <td class="border px-3 py-2">{{ ev.camera_id }}</td>
          <td class="border px-3 py-2">{{ ev.label }}</td>
          <td class="border px-3 py-2">{{ (ev.confidence*100).toFixed(1) }}%</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="text-center text-slate-400 py-10">No data available</div>

    <!-- Pagination (unchanged) -->
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
                :class="currentPage === n ? 'bg-indigo-600 text-white' : 'bg-white text-slate-700'">
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
