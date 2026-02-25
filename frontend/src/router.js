import { createRouter, createWebHistory } from 'vue-router'
import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'

const routes = [
  { path: '/', redirect: '/login' },   // 👈 default route
  { path: '/login', component: Login },
  { path: '/dashboard', component: Dashboard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

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
