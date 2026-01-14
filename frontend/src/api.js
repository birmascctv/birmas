import axios from 'axios'

const API = axios.create({
  baseURL: 'http://178.128.105.184:8000'
})

export default API
