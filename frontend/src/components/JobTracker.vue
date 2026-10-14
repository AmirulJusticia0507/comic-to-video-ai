<script setup>
import { onMounted } from 'vue'
import ProgressBar from './ProgressBar.vue'
import VideoPlayer from './VideoPlayer.vue'
import { useJobSocket } from '../composables/useJobSocket'

const props = defineProps({
  jobId: { type: String, required: true },
  panelImageUrl: { type: String, default: '' },
})

const { state, start } = useJobSocket(props.jobId)

onMounted(start)
</script>

<template>
  <div class="space-y-2">
    <ProgressBar :progress="state.progress" :status="state.status" />
    <p v-if="state.errorMessage" class="text-xs text-red-400">{{ state.errorMessage }}</p>
    <VideoPlayer v-if="state.videoUrl" :src="state.videoUrl" :poster="panelImageUrl" />
  </div>
</template>
