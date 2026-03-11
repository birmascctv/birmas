<template>
  <div class="relative w-full h-full">
    <video ref="v" class="video-player" controls autoplay muted playsinline></video>

    <!-- LIVE badge -->
    <div v-if="!isOffline"
         class="absolute top-2 left-2 flex items-center gap-1 bg-black bg-opacity-50 px-2 py-0.5 rounded text-white text-xs pointer-events-none">
      <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
      LIVE
    </div>

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
let liveEdgeInterval = null
let retryDelay       = 3000

// Build direct mediamtx URL to bypass the Vite proxy.
// Using the proxy for long-lived HLS segment fetches can cause
// net::ERR_NETWORK_CHANGED when the Vite connection pool resets.
function directUrl(path) {
  // path is like "/stream/cam1/index.m3u8" → "/cam1/index.m3u8"
  const stripped = path.replace(/^\/stream/, '')
  return `http://${window.location.hostname}:8888${stripped}`
}

const loadStream = (src) => {
  if (!v.value) return
  isOffline.value = false

  if (hlsInstance)      { hlsInstance.destroy();      hlsInstance      = null }
  if (liveEdgeInterval) { clearInterval(liveEdgeInterval); liveEdgeInterval = null }

  const url = directUrl(src)

  if (!Hls.isSupported()) {
    v.value.src = url
    return
  }

  hlsInstance = new Hls({
    lowLatencyMode:              false,
    liveSyncDurationCount:       3,    // 3 segments behind live edge (~9s with 3s segs)
    liveMaxLatencyDurationCount: 8,    // jump forward if >8 segments behind
    maxBufferLength:             20,
    liveBackBufferLength:        3,
    enableWorker:                true,
    fragLoadingMaxRetry:         2,
    manifestLoadingMaxRetry:     6,
    levelLoadingMaxRetry:        6,
    // Faster retry on network errors (ERR_NETWORK_CHANGED)
    fragLoadingRetryDelay:       500,
    manifestLoadingRetryDelay:   500,
  })

  hlsInstance.loadSource(url)
  hlsInstance.attachMedia(v.value)

  hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
    retryDelay = 3000
    isOffline.value = false
    v.value?.play().catch(() => {})
  })

  hlsInstance.on(Hls.Events.ERROR, (_evt, data) => {
    // Segment 404: Pi reconnected → mediamtx has new session ID → reload immediately
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

    // Non-fatal: HLS.js will retry internally
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

  v.value.addEventListener('playing', () => { isOffline.value = false }, { once: false })

  // Jump to live edge if viewer drifted too far behind
  liveEdgeInterval = setInterval(() => {
    if (v.value && hlsInstance && hlsInstance.liveSyncPosition != null) {
      if (v.value.currentTime < hlsInstance.liveSyncPosition - 30) {
        v.value.currentTime = hlsInstance.liveSyncPosition
      }
    }
  }, 15000)
}

// Reload stream on network recovery (fixes net::ERR_NETWORK_CHANGED)
function onNetworkOnline() {
  if (props.src) {
    retryDelay = 3000
    loadStream(props.src)
  }
}

// Reload stream when tab becomes visible again after being hidden
function onVisibilityChange() {
  if (document.visibilityState === 'visible') {
    // If video is paused or buffering, reload
    if (v.value && (v.value.paused || v.value.readyState < 2)) {
      retryDelay = 3000
      loadStream(props.src)
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
  if (liveEdgeInterval) clearInterval(liveEdgeInterval)
  if (hlsInstance)      { hlsInstance.destroy(); hlsInstance = null }
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
