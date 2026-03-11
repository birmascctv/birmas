<template>
  <div class="relative w-full h-full">
    <video ref="v" class="video-player" controls autoplay muted playsinline></video>

    <!-- LIVE badge — shown when stream is actively playing -->
    <div v-if="!isOffline"
         class="absolute top-2 left-2 flex items-center gap-1 bg-black bg-opacity-50 px-2 py-0.5 rounded text-white text-xs pointer-events-none">
      <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
      LIVE
    </div>

    <!-- Offline overlay — ONLY shown on actual fatal stream errors, not buffering -->
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
let hlsInstance = null
let liveEdgeInterval = null
let retryDelay = 3000

const loadStream = (url) => {
  if (!v.value) return

  // Clear offline state immediately — let HLS.js be the only one to set it
  isOffline.value = false

  if (hlsInstance) { hlsInstance.destroy(); hlsInstance = null }
  if (liveEdgeInterval) { clearInterval(liveEdgeInterval); liveEdgeInterval = null }

  if (!Hls.isSupported()) {
    v.value.src = url
    return
  }

  hlsInstance = new Hls({
    lowLatencyMode:         false,
    liveSyncDuration:       4,     // play 4s behind live (~2 segments)
    liveMaxLatencyDuration: 15,
    maxBufferLength:        10,
    liveBackBufferLength:   3,
    enableWorker:           true,
    fragLoadingMaxRetry:    4,
    manifestLoadingMaxRetry: 4,
    levelLoadingMaxRetry:   4,
  })
  hlsInstance.loadSource(url)
  hlsInstance.attachMedia(v.value)

  // Stream confirmed alive — clear offline overlay
  hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
    retryDelay = 3000
    isOffline.value = false
    v.value?.play().catch(() => {})
  })

  // Only fatal errors should show the offline overlay — NOT normal buffering/waiting
  hlsInstance.on(Hls.Events.ERROR, (_evt, data) => {
    if (!data.fatal) return   // non-fatal (e.g. brief 404 on a rolled-off segment) = ignore
    isOffline.value = true
    if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
      hlsInstance.recoverMediaError()
    } else {
      hlsInstance.destroy()
      hlsInstance = null
      setTimeout(() => loadStream(url), retryDelay)
      retryDelay = Math.min(retryDelay * 2, 30000)
    }
  })

  // Belt-and-suspenders: clear overlay as soon as video starts playing
  v.value.addEventListener('playing', () => { isOffline.value = false }, { once: false })

  liveEdgeInterval = setInterval(() => {
    if (v.value && hlsInstance && hlsInstance.liveSyncPosition != null) {
      if (v.value.currentTime < hlsInstance.liveSyncPosition - 20) {
        v.value.currentTime = hlsInstance.liveSyncPosition
      }
    }
  }, 15000)
}

onMounted(() => loadStream(props.src))
watch(() => props.src, (newSrc) => { retryDelay = 3000; loadStream(newSrc) })
onUnmounted(() => {
  if (liveEdgeInterval) clearInterval(liveEdgeInterval)
  if (hlsInstance) { hlsInstance.destroy(); hlsInstance = null }
})
</script>

<style scoped>
.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
