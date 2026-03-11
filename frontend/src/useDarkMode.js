import { ref } from 'vue'

// Singleton: one shared ref across all components
const dark = ref(false)

function applyDark(v) {
  dark.value = v
  localStorage.setItem('birmas-dark', v ? '1' : '0')
  // Tailwind darkMode:'class' — add/remove 'dark' on <html>
  if (v) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// Apply stored preference on module load
applyDark(localStorage.getItem('birmas-dark') === '1')

// Synchronous toggle: ref + classList + localStorage all at once, no async watcher
function toggleDark() {
  applyDark(!dark.value)
}

export function useDarkMode() {
  return { dark, toggleDark }
}
