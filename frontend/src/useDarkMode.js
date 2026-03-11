import { ref, watch } from 'vue'

// Singleton dark mode state shared across all components
const dark = ref(localStorage.getItem('birmas-dark') === '1')

// Sync to <html> class and localStorage immediately
watch(dark, (v) => {
  localStorage.setItem('birmas-dark', v ? '1' : '0')
  document.documentElement.classList.toggle('dark', v)
}, { immediate: true })

export function useDarkMode() {
  return { dark }
}
