<template>
  <div>
    <div class="toggle-buttons">
      <button @click="mode='hls'">Standard Mode (HLS)</button>
      <button @click="mode='webrtc'">Low Latency Mode (WebRTC)</button>
    </div>

    <!-- HLS Player -->
    <video
      v-if="mode==='hls'"
      ref="video"
      class="video-player"
      controls
      autoplay
      muted
      playsinline
    ></video>

    <!-- WebRTC Player -->
    <iframe
      v-if="mode==='webrtc'"
      :src="webrtcUrl"
      allow="autoplay; fullscreen"
      class="video-player"
    ></iframe>
  </div>
</template>

<script setup>
import Hls from 'hls.js'
import { onMounted, ref, watch } from 'vue'

const video = ref(null)
const mode = ref('hls') // default
const hlsUrl = 'http://100.87.93.95:8888/cam1/index.m3u8'
const webrtcUrl = 'http://100.87.93.95:8889/cam1'

function initHls() {
  if (video.value) {
    if (Hls.isSupported()) {
      const h = new Hls()
      h.loadSource(hlsUrl)
      h.attachMedia(video.value)
    } else {
      video.value.src = hlsUrl
    }
  }
}

onMounted(() => {
  if (mode.value==='hls') initHls()
})

watch(mode, (newMode) => {
  if (newMode==='hls') initHls()
})
</script>

<style scoped>
.toggle-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}
.toggle-buttons button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background-color: #007bff;
  color: white;
  cursor: pointer;
}
.toggle-buttons button:hover {
  background-color: #0056b3;
}
.video-player {
  width: 100%;
  height: 100%;
  border: none;
  object-fit: contain;
}
</style>
