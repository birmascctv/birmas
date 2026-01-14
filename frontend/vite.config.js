import { defineConfig } from 'vite'
import vue from '@vue/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0', // Necessary for Tailscale to pick up the traffic
    port: 5173,
    proxy: {
      // 1. Backend API Proxy
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, '') // Only use this if your backend doesn't expect '/api' in the URL
      },
      // 2. HLS Stream Proxy
      '/cam1': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
      }
    }
  }
})