import { createRouter, createWebHistory } from 'vue-router'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/dashboard', component: Dashboard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Route guard: block dashboard if not logged in
router.beforeEach((to, from, next) => {
  const isAuth =
    localStorage.getItem('auth') === 'true' ||
    sessionStorage.getItem('auth') === 'true'

  if (to.path.startsWith('/dashboard') && !isAuth) {
    next('/login')
  } else {
    next()
  }
})

export default router
