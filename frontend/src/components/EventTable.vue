<template>
  <div class="flex-1">
    <table v-if="paginatedEvents.length" class="text-sm w-full border-collapse text-center">
      <thead>
        <tr>
          <th class="border px-3 py-2 bg-gray-800 text-red-600">Time</th>
          <th class="border px-3 py-2 bg-gray-800 text-red-600">Camera</th>
          <th class="border px-3 py-2 bg-gray-800 text-red-600">Label</th>
          <th class="border px-3 py-2 bg-gray-800 text-red-600">Conf</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ev in paginatedEvents" :key="ev.ts">
          <!-- First column: lighter text for readability -->
          <td class="border px-3 py-2 text-gray-200">{{ new Date(ev.ts).toLocaleString() }}</td>
          <td class="border px-3 py-2 text-gray-300">{{ ev.camera_id }}</td>
          <td class="border px-3 py-2 text-gray-300">{{ ev.label }}</td>
          <td class="border px-3 py-2 text-gray-300">{{ (ev.confidence*100).toFixed(1) }}%</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="text-center text-gray-500 py-10">No data available</div>

    <!-- Pagination -->
    <div class="flex justify-center gap-2 mt-3" v-if="totalPages > 1">
      <button @click="currentPage = Math.max(1, currentPage - 1)"
              class="px-2 py-1 rounded border border-gray-600 bg-gray-700 text-white"
              :disabled="currentPage === 1">
        Prev
      </button>

      <template v-for="n in pagesToShow" :key="n">
        <span v-if="n === '...'">...</span>
        <button v-else
                @click="currentPage = n"
                class="px-2 py-1 rounded border border-gray-600"
                :class="currentPage === n ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-300'">
          {{ n }}
        </button>
      </template>

      <button @click="currentPage = Math.min(totalPages, currentPage + 1)"
              class="px-2 py-1 rounded border border-gray-600 bg-gray-700 text-white"
              :disabled="currentPage === totalPages">
        Next
      </button>
    </div>
  </div>
</template>
