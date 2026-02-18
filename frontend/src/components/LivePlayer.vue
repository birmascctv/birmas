<template>
  <div>
    <div class="toggle-buttons">
      <button @click="useHls">Standard Mode (HLS)</button>
      <button @click="useWebrtc">Low Latency Mode (WebRTC)</button>
    </div>

    <!-- HLS Player -->
    <video
      v-if="mode === 'hls'"
      ref="video"
      class="video-player"
      controls
      autoplay
      muted
      playsinline
    ></video>

    <!-- WebRTC Player -->
    <iframe
      v-if="mode === 'webrtc'"
      :src="webrtcUrl"
      width="640"
      height="360"
      class="video-player"
    ></iframe>
  </div>
</template>

<script setup>
import Hls from 'hls.js'
import { onMounted, ref } from 'vue'

const video = ref(null)
const mode = ref('hls') // default mode
const hlsUrl = 'http://<tailscale-funnel-url>:8888/cam1/index.m3u8'
const webrtcUrl = 'http://<tailscale-funnel-url>:8889/cam1'

function useHls() {
  mode.value = 'hls'
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

function useWebrtc() {
  mode.value = 'webrtc'
}

onMounted(() => {
  useHls() // start with HLS by default
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
  transition: background-color 0.2s;
}

.toggle-buttons button:hover {
  background-color: #0056b3;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
