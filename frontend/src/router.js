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
  const tokenInSession = sessionStorage.getItem('auth_token')
  const tokenInLocal = localStorage.getItem('auth_token')
  const expiresAt = localStorage.getItem('auth_expires_at')

  // Purge any legacy demo or invalid token strings
  if (tokenInSession === 'undefined' || tokenInSession === 'demo_auth_token_preview') {
    sessionStorage.removeItem('auth_token')
  }
  if (tokenInLocal === 'undefined' || tokenInLocal === 'demo_auth_token_preview') {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_expires_at')
  }

  const activeSessionToken = sessionStorage.getItem('auth_token')
  const activeLocalToken = localStorage.getItem('auth_token')

  let isValid = false

  if (activeSessionToken) {
    // Session token is valid for the current tab lifetime
    isValid = true
  } else if (activeLocalToken) {
    // Local storage token must be checked against expiration
    if (expiresAt && Date.now() > parseInt(expiresAt, 10)) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_expires_at')
      isValid = false
    } else {
      isValid = true
    }
  }

  if (to.path.startsWith('/dashboard') && !isValid) {
    return '/login?timeout=1'
  }

  if (to.path === '/login' && isValid && !to.query.timeout) {
    return '/dashboard'
  }

  return true
})

export default router
