<template>
  <video ref="videoEl" class="video-player" autoplay playsinline controls></video>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const videoEl = ref(null)

// MediaMTX WebRTC API endpoint
const webrtcApiUrl = 'https://ubuntu-s-2vcpu-4gb-sgp1-01.tail79eba2.ts.net/cam1/whep'

onMounted(async () => {
  const pc = new RTCPeerConnection()

  // attach remote stream to video element
  pc.ontrack = (event) => {
    videoEl.value.srcObject = event.streams[0]
  }

  // create offer
  const offer = await pc.createOffer()
  await pc.setLocalDescription(offer)

  // send offer to MediaMTX WHEP endpoint
  const resp = await fetch(webrtcApiUrl, {
    method: 'POST',
    body: offer.sdp,
    headers: { 'Content-Type': 'application/sdp' }
  })
  const answerSdp = await resp.text()

  // set remote description
  await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp })
})
</script>

<style scoped>
.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>
