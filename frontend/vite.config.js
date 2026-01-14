import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['ubuntu-s-2vcpu-4gb-sgp1-01.tail79eba2.ts.net'],
    hmr: {
      clientPort: 443
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/cam1': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true
      }
    }
  }
})