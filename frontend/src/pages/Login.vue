<template>
  <div class="flex items-center justify-center min-h-screen bg-stone-100">
    <div class="bg-white p-6 rounded-lg shadow-sm w-80 border border-stone-200">
      <h2 class="text-lg font-semibold text-amber-700 mb-4">Login</h2>
      <form @submit.prevent="login">
        <input v-model="username" type="text" placeholder="Username"
               class="w-full mb-3 h-8 px-2 py-1 border rounded text-sm leading-tight bg-stone-50 text-slate-700" />
        <input v-model="password" type="password" placeholder="Password"
               class="w-full mb-3 h-8 px-2 py-1 border rounded text-sm leading-tight bg-stone-50 text-slate-700" />

        <!-- Remember Me -->
        <label class="flex items-center gap-2 mb-3 text-sm text-slate-600">
          <input type="checkbox" v-model="rememberMe" />
          Remember me
        </label>

        <button type="submit"
                class="w-full bg-amber-600 text-white py-2 rounded hover:bg-amber-700">
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
  // Simple test user list
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
