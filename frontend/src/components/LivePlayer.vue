<template>
  <div class="video-container">
    <iframe
      :src="webrtcUrl"
      allow="autoplay; fullscreen"
      class="video-player"
    ></iframe>
  </div>
</template>

<script setup>
const webrtcUrl = 'https://ubuntu-s-2vcpu-4gb-sgp1-01.tail79eba2.ts.net/cam1'
</script>

<style scoped>
.video-container {
  width: 100%;
  height: 100%;
}
.video-player {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
