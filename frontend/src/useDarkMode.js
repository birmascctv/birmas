import { ref, watch } from 'vue'

// Singleton dark mode state shared across all components
const dark = ref(localStorage.getItem('birmas-dark') === '1')

function applyDark(v) {
  localStorage.setItem('birmas-dark', v ? '1' : '0')
  document.documentElement.classList.toggle('dark', v)
}

// Apply immediately on load
applyDark(dark.value)

// Keep in sync reactively
watch(dark, applyDark)

// Explicit toggle — more reliable than dark = !dark in templates
function toggleDark() {
  dark.value = !dark.value
}

export function useDarkMode() {
  return { dark, toggleDark }
}
