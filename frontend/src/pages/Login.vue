<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-900 px-4">
    <div class="bg-gray-800 p-6 rounded-lg shadow-sm w-full max-w-sm border border-gray-700">
      <h2 class="text-lg font-semibold text-red-600 mb-1">Birmas</h2>
      <p class="text-xs text-gray-400 mb-4">Retail Intelligence Dashboard</p>

      <!-- Idle timeout notice -->
      <div v-if="timedOut"
           class="mb-3 bg-amber-900 bg-opacity-40 border border-amber-700 text-amber-300 text-xs px-3 py-2 rounded">
        Session expired due to inactivity. Please log in again.
      </div>

      <form @submit.prevent="login">
        <input v-model="username" type="text" placeholder="Username" autocomplete="username"
               class="w-full mb-3 h-9 px-3 border border-gray-600 rounded text-sm bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:border-red-500" />
        <input v-model="password" type="password" placeholder="Password" autocomplete="current-password"
               class="w-full mb-3 h-9 px-3 border border-gray-600 rounded text-sm bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:border-red-500" />

        <!-- Error message -->
        <p v-if="errorMsg" class="text-red-400 text-xs mb-3">{{ errorMsg }}</p>

        <label class="flex items-center gap-2 mb-4 text-sm text-gray-300 cursor-pointer">
          <input type="checkbox" v-model="rememberMe" class="accent-red-600" />
          Remember me
        </label>

        <button type="submit" :disabled="loading"
                class="w-full bg-red-600 text-white py-2 rounded hover:bg-red-700 disabled:opacity-50 text-sm font-medium transition-colors">
          {{ loading ? 'Logging in…' : 'Login' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import API from '../api'

const username   = ref('')
const password   = ref('')
const rememberMe = ref(false)
const errorMsg   = ref('')
const loading    = ref(false)
const timedOut   = ref(false)

const router = useRouter()
const route  = useRoute()

onMounted(() => {
  timedOut.value = route.query.timeout === '1'
})

const login = async () => {
  errorMsg.value = ''
  loading.value  = true
  try {
    const res   = await API.post('/users/login', { username: username.value, password: password.value })
    const token = res.data.access_token
    if (rememberMe.value) localStorage.setItem('auth_token', token)
    else sessionStorage.setItem('auth_token', token)
    router.push('/dashboard')
  } catch {
    errorMsg.value = 'Invalid username or password.'
  } finally {
    loading.value = false
  }
}
</script>
