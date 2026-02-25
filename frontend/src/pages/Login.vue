<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-900">
    <div class="bg-gray-800 p-6 rounded-lg shadow-sm w-80 border border-gray-700">
      <h2 class="text-lg font-semibold text-red-600 mb-4">Login</h2>
      <form @submit.prevent="login">
        <input v-model="username" type="text" placeholder="Username"
               class="w-full mb-3 h-8 px-2 py-1 border border-gray-600 rounded text-sm leading-tight bg-gray-700 text-white" />
        <input v-model="password" type="password" placeholder="Password"
               class="w-full mb-3 h-8 px-2 py-1 border border-gray-600 rounded text-sm leading-tight bg-gray-700 text-white" />

        <!-- Remember Me -->
        <label class="flex items-center gap-2 mb-3 text-sm text-gray-300">
          <input type="checkbox" v-model="rememberMe" />
          Remember me
        </label>

        <button type="submit"
                class="w-full bg-red-600 text-white py-2 rounded hover:bg-red-700">
          Login
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const router = useRouter()

const login = () => {
  const users = [
    { username: 'admin', password: 'password' },
    { username: 'eva', password: 'b1rm4s' }
  ]

  const match = users.find(
    u => u.username === username.value && u.password === password.value
  )

  if (match) {
    if (rememberMe.value) {
      localStorage.setItem('auth', 'true')
    } else {
      sessionStorage.setItem('auth', 'true')
    }
    router.push('/dashboard')
  } else {
    alert('Invalid credentials')
  }
}
</script>
