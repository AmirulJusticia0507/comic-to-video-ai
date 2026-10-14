<script setup>
defineProps({
  src: { type: String, required: true },
})
</script>

<template>
  <video :src="src" controls class="w-full rounded-lg bg-black"></video>
</template>
