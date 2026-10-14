<script setup>
defineProps({
  src: { type: String, required: true },
  poster: { type: String, default: '' },
})
</script>

<template>
  <video
    :src="src"
    :poster="poster || undefined"
    controls
    playsinline
    class="w-full rounded-2xl border border-white/10 bg-black shadow-2xl"
  ></video>
</template>
