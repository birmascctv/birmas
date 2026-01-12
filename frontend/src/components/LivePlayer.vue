<template><video ref="v" controls autoplay muted playsinline></video></template>
<script setup>
import Hls from 'hls.js'
import { onMounted, ref } from 'vue'
const v = ref(null)
const src = 'http://100.87.93.95:8888/cam1/index.m3u8'
onMounted(() => {
  if (Hls.isSupported()) { const h = new Hls(); h.loadSource(src); h.attachMedia(v.value) }
  else { v.value.src = src }
})
</script>

