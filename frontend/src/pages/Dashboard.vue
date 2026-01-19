<template>
  <div class="min-h-screen bg-gray-100 dark:bg-gray-900 p-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-semibold text-gray-800 dark:text-white">
        Admin Dashboard
      </h1>

      <input
        type="text"
        placeholder="Search events..."
        class="rounded-md w-64"
      />
    </div>

    <!-- Grid -->
    <div class="grid grid-cols-2 gap-3">
      <LivePlayer class="col-span-2" />
      <CountChart />
      <EventTable />
    </div>
  </div>
</template>
