<script setup>
import { computed } from 'vue'

const props = defineProps({
  progress: { type: Number, default: 0 },
  status: { type: String, default: 'PENDING' },
})

const clamped = computed(() => Math.min(100, Math.max(0, props.progress)))

const barColor = computed(() => {
  if (props.status === 'FAILED') return 'bg-red-500'
  if (props.status === 'COMPLETED') return 'bg-green-500'
  return 'bg-indigo-500'
})

const label = computed(() => {
  if (props.status === 'FAILED') return 'Failed'
  if (props.status === 'COMPLETED') return 'Completed'
  if (props.status === 'PROCESSING') return `${clamped.value}%`
  return 'Pending'
})
</script>

<template>
  <div class="w-full">
    <div class="mb-1 flex items-center justify-between text-xs">
      <span class="font-medium uppercase tracking-wide text-gray-500">{{ status }}</span>
      <span class="text-gray-500">{{ label }}</span>
    </div>
    <div class="h-2 w-full overflow-hidden rounded-full bg-gray-200">
      <div
        class="h-full rounded-full transition-all duration-300"
        :class="barColor"
        :style="{ width: `${clamped}%` }"
      ></div>
    </div>
  </div>
</template>
