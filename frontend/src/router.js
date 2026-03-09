import { createRouter, createWebHistory } from 'vue-router'
// import Login from './pages/Login.vue'
// import Dashboard from './pages/Dashboard.vue'

const Login = () => import('./pages/Login.vue')
const Dashboard = () => import('./pages/Dashboard.vue')
const routes = [
  { path: '/', redirect: '/login' },   // 👈 default route
  { path: '/login', component: Login },
  { path: '/dashboard', component: Dashboard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from) => {
  const isAuth =
    localStorage.getItem('auth_token') ||
    sessionStorage.getItem('auth_token')

  if (to.path.startsWith('/dashboard') && !isAuth) {
    return '/login'
  }
  return true
})

export default router
