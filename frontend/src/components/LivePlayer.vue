<template>
  <video ref="v" class="video-player" controls autoplay muted playsinline></video>
</template>

<script setup>
import Hls from 'hls.js'
import { onMounted, ref, watch } from 'vue'

const props = defineProps({
  src: { type: String, required: true }
})

const v = ref(null)

const loadStream = (url) => {
  if (!v.value) return
  if (Hls.isSupported()) {
    const h = new Hls()
    h.loadSource(url)
    h.attachMedia(v.value)
  } else {
    v.value.src = url
  }
}

onMounted(() => loadStream(props.src))
watch(() => props.src, (newSrc) => loadStream(newSrc))
</script>

<style scoped>
.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
