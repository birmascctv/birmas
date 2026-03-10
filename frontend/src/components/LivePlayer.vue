<template>
  <video ref="v" class="video-player" controls autoplay muted playsinline></video>
</template>

<script setup>
import Hls from 'hls.js'
import { onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, required: true }
})

const v = ref(null)
let hlsInstance = null
let liveEdgeInterval = null

const loadStream = (url) => {
  if (!v.value) return
  if (hlsInstance) {
    hlsInstance.destroy()
    hlsInstance = null
  }
  if (liveEdgeInterval) {
    clearInterval(liveEdgeInterval)
    liveEdgeInterval = null
  }

  if (Hls.isSupported()) {
    hlsInstance = new Hls({
      lowLatencyMode: true,       // Enable LL-HLS (uses 200ms parts from MediaMTX)
      liveSyncDuration: 1,        // Target 1s behind live edge
      liveMaxLatencyDuration: 3,  // If >3s behind, jump to live edge
      maxBufferLength: 5,
      liveBackBufferLength: 2,
    })
    hlsInstance.loadSource(url)
    hlsInstance.attachMedia(v.value)

    // Periodically recover if player has drifted more than 3s behind live edge
    liveEdgeInterval = setInterval(() => {
      if (v.value && hlsInstance && hlsInstance.liveSyncPosition != null) {
        if (v.value.currentTime < hlsInstance.liveSyncPosition - 3) {
          v.value.currentTime = hlsInstance.liveSyncPosition
        }
      }
    }, 5000)
  } else {
    v.value.src = url
  }
}

onMounted(() => loadStream(props.src))
watch(() => props.src, (newSrc) => loadStream(newSrc))
onUnmounted(() => {
  if (liveEdgeInterval) clearInterval(liveEdgeInterval)
  if (hlsInstance) {
    hlsInstance.destroy()
    hlsInstance = null
  }
})
</script>

<style scoped>
.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
