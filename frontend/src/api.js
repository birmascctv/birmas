import axios from 'axios'

const API = axios.create({
  baseURL: 'http://10.0.0.1:8000/api'   // WireGuard IP + backend port
})

export default API
