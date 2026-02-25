import { createApp } from 'vue'
import App from './App.vue'       // Root component
import router from './router'     // Import router.js
import './style.css'              // Tailwind styles

const app = createApp(App)
app.use(router)                   // Register router
app.mount('#app')
