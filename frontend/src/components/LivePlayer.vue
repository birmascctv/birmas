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

const loadStream = (url) => {
  if (!v.value) return
  if (hlsInstance) {
    hlsInstance.destroy()
    hlsInstance = null
  }
  if (Hls.isSupported()) {
    hlsInstance = new Hls()
    hlsInstance.loadSource(url)
    hlsInstance.attachMedia(v.value)
  } else {
    v.value.src = url
  }
}

onMounted(() => loadStream(props.src))
watch(() => props.src, (newSrc) => loadStream(newSrc))
onUnmounted(() => {
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
