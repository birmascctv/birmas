<template>
  <div class="min-h-screen flex flex-col bg-stone-100 text-slate-700">
    <!-- Global Header -->
    <header class="bg-white shadow-sm border-b border-stone-200 px-6 py-3 flex items-center justify-between">
      <h1 class="text-xl font-bold tracking-wide">Birmas</h1>
      <nav class="flex gap-4 text-sm">
        <!-- Show logout only if authenticated -->
        <button v-if="isAuth" @click="logout"
                class="px-3 py-1 rounded bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200">
          Logout
        </button>
      </nav>
    </header>

    <!-- Main content -->
    <main class="flex-1 px-6 py-4">
      <router-view />
    </main>

    <!-- Global Footer -->
    <footer class="bg-white border-t border-stone-200 px-6 py-3 text-center text-xs text-slate-500">
      © {{ new Date().getFullYear() }} Birmas Surveillance Dashboard
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const isAuth =
  localStorage.getItem('auth') === 'true' ||
  sessionStorage.getItem('auth') === 'true'

const logout = () => {
  localStorage.removeItem('auth')
  sessionStorage.removeItem('auth')
  router.push('/login')
}
</script>
