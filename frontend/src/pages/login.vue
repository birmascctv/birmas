<template>
  <div class="flex items-center justify-center min-h-screen bg-stone-100">
    <div class="bg-white p-6 rounded-lg shadow-sm w-80 border border-stone-200">
      <h2 class="text-lg font-semibold text-slate-700 mb-4">Login</h2>
      <form @submit.prevent="login">
        <input v-model="username" type="text" placeholder="Username"
               class="w-full mb-3 h-8 px-2 py-1 border rounded text-sm leading-tight bg-stone-50 text-slate-700" />
        <input v-model="password" type="password" placeholder="Password"
               class="w-full mb-3 h-8 px-2 py-1 border rounded text-sm leading-tight bg-stone-50 text-slate-700" />
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
const router = useRouter()

const login = () => {
  // Simple hardcoded authentication for demo
  if (username.value === 'admin' && password.value === 'password') {
    localStorage.setItem('auth', 'true')
    router.push('/dashboard')
  } else {
    alert('Invalid credentials')
  }
}
</script>
