import axios from 'axios'

const API = axios.create({
  baseURL: '/api'
})

API.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default API
