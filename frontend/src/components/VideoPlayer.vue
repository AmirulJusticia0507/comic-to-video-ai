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
    class="w-full rounded-lg bg-black"
  ></video>
</template>
