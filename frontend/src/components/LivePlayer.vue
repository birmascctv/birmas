<script setup>
import { onMounted, ref } from 'vue'

const videoEl = ref(null)
const webrtcApiUrl = 'https://ubuntu-s-2vcpu-4gb-sgp1-01.tail79eba2.ts.net:8889/whep/cam1/'

onMounted(async () => {
  const pc = new RTCPeerConnection()

  pc.ontrack = (event) => {
    videoEl.value.srcObject = event.streams[0]
  }

  const offer = await pc.createOffer()
  await pc.setLocalDescription(offer)

  const resp = await fetch(webrtcApiUrl, {
    method: 'POST',
    body: offer.sdp,
    headers: { 'Content-Type': 'application/sdp' }
  })
  const answerSdp = await resp.text()

  await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp })
})
</script>
