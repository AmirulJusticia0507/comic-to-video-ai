<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { api } from '../api/client'
import ProgressBar from './ProgressBar.vue'
import VideoPlayer from './VideoPlayer.vue'
import { useJobSocket } from '../composables/useJobSocket'

const props = defineProps({
  jobId: { type: String, required: true },
  panelImageUrl: { type: String, default: '' },
})

const { state, start, disconnect } = useJobSocket(props.jobId)
const playUrl = ref('')

watch(
  () => [state.status, state.videoUrl],
  async ([status, videoUrl]) => {
    if (status !== 'COMPLETED' || !videoUrl || playUrl.value) return
    try {
      const data = await api(`/uploads/download-url?key=${encodeURIComponent(videoUrl)}`)
      playUrl.value = data.url
    } catch {
      playUrl.value = videoUrl
    }
  },
  { immediate: true },
)

onMounted(start)
onBeforeUnmount(disconnect)
</script>

<template>
  <div class="space-y-2">
    <ProgressBar :progress="state.progress" :status="state.status" />
    <p v-if="state.errorMessage" class="text-xs text-red-500">{{ state.errorMessage }}</p>
    <VideoPlayer v-if="playUrl" :src="playUrl" :poster="panelImageUrl" class="mt-2" />
  </div>
</template>
