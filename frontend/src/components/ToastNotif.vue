<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 items-end pointer-events-none">
    <transition-group name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="pointer-events-auto flex items-start gap-3 bg-white border border-gray-200 shadow-lg rounded-lg px-4 py-3 min-w-[260px] max-w-xs"
      >
        <span
          class="mt-0.5 w-2.5 h-2.5 rounded-full flex-shrink-0"
          :class="dotClass(t.event_type)"
        ></span>
        <div class="flex-1 text-sm">
          <p class="font-semibold text-gray-800 leading-tight">{{ t.brand }} — {{ t.product }}</p>
          <p class="text-xs mt-0.5" :class="labelClass(t.event_type)">{{ t.statusLabel }}</p>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
const props = defineProps({
  toasts: { type: Array, default: () => [] }
})

const DOT_CLASSES = {
  added:   'bg-green-500',
  sold:    'bg-red-500',
  restock: 'bg-blue-500',
}
const LABEL_CLASSES = {
  added:   'text-green-600',
  sold:    'text-red-600',
  restock: 'text-blue-600',
}
function dotClass(t) { return DOT_CLASSES[t] || 'bg-gray-400' }
function labelClass(t) { return LABEL_CLASSES[t] || 'text-gray-500' }
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.4s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(60px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(60px);
}
</style>
