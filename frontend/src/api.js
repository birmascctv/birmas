import axios from 'axios'

const API = axios.create({
  baseURL: '10.0.0.1:8000/api'  // droplet IP + backend port
})

export default API
