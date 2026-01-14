import { defineConfig } from 'vite'
import vue from '@vue/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // This allows Tailscale to connect to the dev server
    allowedHosts: ['ubuntu-s-2vcpu-4gb-sgp1-01.tail79eba2.ts.net'],
    hmr: {
      clientPort: 443
    },
    proxy: {
      // Proxying API calls to FastAPI/Backend
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      // Proxying HLS stream to Media Server
      '/cam1': {
        target: 'http://127.0.0.1:8888',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})