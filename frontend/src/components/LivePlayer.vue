<template>
  <div class="relative w-full h-full">
    <video ref="v" class="video-player" controls autoplay muted playsinline></video>

    <!-- Offline overlay -->
    <div v-if="isOffline"
         class="absolute inset-0 bg-black bg-opacity-80 flex flex-col items-center justify-center text-white text-sm gap-2 pointer-events-none">
      <svg class="w-8 h-8 opacity-60 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15 10l4.553-2.07A1 1 0 0121 8.82V15.18a1 1 0 01-1.447.89L15 14M3 8.82A1 1 0 014.447 7.93L13 12l-8.553 4.07A1 1 0 013 15.18V8.82z" />
      </svg>
      <span class="opacity-80">Stream unavailable — reconnecting…</span>
    </div>
  </div>
</template>

<script setup>
import Hls from 'hls.js'
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, required: true }
})

const v = ref(null)
const isOffline = ref(false)
let hlsInstance      = null
let watchdogInterval = null
let retryDelay       = 3000
let lastTime         = -1
let stuckCount       = 0
let userPaused       = false   // track if user intentionally paused

// Use the Vite proxy path so the browser doesn't need direct access to MediaMTX.
// Vite proxy: /stream/* → http://10.0.0.1:8888/*  (server-side)
function directUrl(path) {
  return path
}

function stopWatchdog() {
  if (watchdogInterval) { clearInterval(watchdogInterval); watchdogInterval = null }
}

const loadStream = (src) => {
  if (!v.value) return
  isOffline.value = false
  stuckCount = 0
  lastTime   = -1
  userPaused = false

  if (hlsInstance) { hlsInstance.destroy(); hlsInstance = null }
  stopWatchdog()

  const url = directUrl(src)

  if (!Hls.isSupported()) {
    v.value.src = url
    return
  }

hlsInstance = new Hls({
    lowLatencyMode:              true,
    liveSyncDuration:            2,     // Target 2 seconds behind real-time
    liveMaxLatencyDuration:      4,     // If delay exceeds 4 seconds, jump straight to the live edge!
    maxBufferLength:             2,     // Only buffer 2 seconds in RAM
    maxMaxBufferLength:          4,
    liveBackBufferLength:        0,     // Don't waste memory storing past frames
    enableWorker:                true,
    fragLoadingMaxRetry:         4,
    manifestLoadingMaxRetry:     8,
    levelLoadingMaxRetry:        8,
    fragLoadingRetryDelay:       300,
    manifestLoadingRetryDelay:   300,
    fragLoadingMaxRetryTimeout:  4000,
  })

  hlsInstance.loadSource(url)
  hlsInstance.attachMedia(v.value)

  hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
    retryDelay = 3000
    isOffline.value = false
    v.value?.play().catch(() => {})
  })

  hlsInstance.on(Hls.Events.ERROR, (_evt, data) => {
    // Segment 404: stream restarted → reload
    if (
      data.type    === Hls.ErrorTypes.NETWORK_ERROR &&
      data.details === Hls.ErrorDetails.FRAG_LOAD_ERROR &&
      (data.response?.code === 404 || data.networkDetails?.status === 404)
    ) {
      hlsInstance.destroy(); hlsInstance = null
      retryDelay = 3000
      setTimeout(() => loadStream(src), 1000)
      return
    }

    if (!data.fatal) return

    isOffline.value = true
    if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
      hlsInstance.recoverMediaError()
    } else {
      hlsInstance.destroy(); hlsInstance = null
      setTimeout(() => loadStream(src), retryDelay)
      retryDelay = Math.min(retryDelay * 2, 15000)
    }
  })

  // Stall watchdog: every 5s check if currentTime advanced.
  // If stuck 3 times in a row (15s stall) → full reload.
  watchdogInterval = setInterval(() => {
    if (!v.value || userPaused) return
    const cur = v.value.currentTime

    if (!v.value.paused && v.value.readyState >= 2) {
      if (Math.abs(cur - lastTime) < 0.1) {
        stuckCount++
        if (stuckCount >= 3) {
          // Video is not progressing — hard reload
          stuckCount = 0
          retryDelay = 3000
          loadStream(src)
          return
        }
        // Try jump-to-live first
        if (hlsInstance?.liveSyncPosition != null) {
          v.value.currentTime = hlsInstance.liveSyncPosition
          v.value.play().catch(() => {})
        }
      } else {
        stuckCount = 0
      }
    } else if (v.value.paused && !userPaused) {
      // Paused but user didn't pause — buffering stall
      stuckCount++
      if (stuckCount >= 3) {
        stuckCount = 0
        loadStream(src)
      }
    }
    lastTime = cur
  }, 5000)

  v.value.addEventListener('playing', () => { isOffline.value = false; stuckCount = 0 }, { once: false })
  v.value.addEventListener('pause',   () => { /* can't reliably distinguish user vs buffer pause here */ })
}

function onNetworkOnline() {
  if (props.src) { retryDelay = 3000; loadStream(props.src) }
}

function onVisibilityChange() {
  if (document.visibilityState === 'visible' && v.value) {
    if (v.value.paused || v.value.readyState < 2) {
      retryDelay = 3000; loadStream(props.src)
    }
  }
}

onMounted(() => {
  loadStream(props.src)
  window.addEventListener('online', onNetworkOnline)
  document.addEventListener('visibilitychange', onVisibilityChange)
})

watch(() => props.src, (newSrc) => { retryDelay = 3000; loadStream(newSrc) })

onUnmounted(() => {
  stopWatchdog()
  if (hlsInstance) { hlsInstance.destroy(); hlsInstance = null }
  window.removeEventListener('online', onNetworkOnline)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<style scoped>
.video-player {
  width:       100%;
  height:      100%;
  object-fit:  contain;
}
</style>
