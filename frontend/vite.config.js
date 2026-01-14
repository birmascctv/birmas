import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({
    server: {
        host: '0.0.0.0',
        port: 5173,
        allowedHosts: ['ubuntu-s-2vcpu-4gb-sgp1-01.tail79eba2.ts.net'],
        hmr: {
            clientPort: 443
        }
    },
    plugins: [vue()]
})