import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0', // Essential for Tailscale/Network access
    port: 5173,      // Matches your Funnel and Service config
    strictPort: true,
    proxy: {
      // Proxies API calls to your backend service
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
      // Proxies Camera Streams (HLS/Websocket)
      '/cam1': {
        target: 'http://localhost:8083',
        changeOrigin: true,
        secure: false,
        ws: true, // Enable websocket proxying for streams
      }
    }
  }
})