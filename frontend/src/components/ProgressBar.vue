<script setup>
defineProps({
  progress: { type: Number, default: 0 },
})
</script>

<template>
  <div class="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
    <div
      class="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
      :style="{ width: `${Math.min(Math.max(progress, 0), 100)}%` }"
    ></div>
  </div>
</template>
