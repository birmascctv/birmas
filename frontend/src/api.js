import axios from 'axios'

const API = axios.create({
  baseURL: 'http://170.64.149.147:8000'
})

export default API
