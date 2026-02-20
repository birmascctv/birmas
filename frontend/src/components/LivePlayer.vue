#liveplayer.vue

<template>
  <video ref="v" class="video-player" controls autoplay muted playsinline></video>
</template>

<script setup>
import Hls from 'hls.js'
import { onMounted, ref } from 'vue'
const v = ref(null)
const src = '/stream/cam1/index.m3u8'

onMounted(() => {
  if (Hls.isSupported()) { const h = new Hls(); h.loadSource(src); h.attachMedia(v.value) }
  else { v.value.src = src }
})
</script>

<style scoped>
.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain; 
}
</style>