<script setup>
import { ref } from 'vue'
import { api } from '../api/client'

const props = defineProps({
  projectId: { type: String, required: true },
})

const emit = defineEmits(['uploaded'])

const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/webp']
const MAX_SIZE_BYTES = 20 * 1024 * 1024

const file = ref(null)
const motionPrompt = ref('')
const uploading = ref(false)
const error = ref('')
const dragOver = ref(false)

function onFileChange(event) {
  error.value = ''
  const selected = event.target.files?.[0]
  if (selected) validateAndSet(selected)
}

function onDrop(event) {
  dragOver.value = false
  error.value = ''
  const selected = event.dataTransfer?.files?.[0]
  if (selected) validateAndSet(selected)
}

function validateAndSet(selected) {
  if (!ALLOWED_TYPES.includes(selected.type)) {
    error.value = 'only PNG, JPEG, or WebP images are allowed'
    return
  }
  if (selected.size > MAX_SIZE_BYTES) {
    error.value = 'image must be smaller than 20 MB'
    return
  }
  file.value = selected
}

async function submit() {
  if (!file.value || uploading.value) return
  uploading.value = true
  error.value = ''
  try {
    const { upload_url, key } = await api(`/api/v1/projects/${props.projectId}/panels/upload-url`, {
      method: 'POST',
      body: {
        content_type: file.value.type,
        panel_order: Date.now(),
        motion_prompt: motionPrompt.value || null,
      },
    })

    const uploadRes = await fetch(upload_url, {
      method: 'PUT',
      headers: { 'Content-Type': file.value.type },
      body: file.value,
    })
    if (!uploadRes.ok) throw new Error(`storage upload failed (${uploadRes.status})`)

    const panel = await api(`/api/v1/projects/${props.projectId}/panels`, {
      method: 'POST',
      body: {
        image_url: key,
        panel_order: Date.now(),
        motion_prompt: motionPrompt.value || null,
      },
    })
    emit('uploaded', panel)
    file.value = null
    motionPrompt.value = ''
  } catch (err) {
    error.value = err.message
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="rounded-lg border border-gray-800 bg-gray-900 p-4">
    <h3 class="mb-3 text-sm font-semibold text-gray-200">Upload Panel</h3>

    <div
      class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors"
      :class="dragOver ? 'border-indigo-500 bg-indigo-500/10' : 'border-gray-700 hover:border-gray-500'"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="onDrop"
      @click="$refs.fileInput.click()"
    >
      <input
        ref="fileInput"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        class="hidden"
        @change="onFileChange"
      />
      <p v-if="!file" class="text-sm text-gray-400">
        Drag &amp; drop a comic panel here, or click to browse
      </p>
      <p v-else class="text-sm font-medium text-gray-200">{{ file.name }}</p>
      <p class="mt-1 text-xs text-gray-500">PNG, JPEG, or WebP — max 20 MB</p>
    </div>

    <input
      v-model="motionPrompt"
      type="text"
      placeholder="Motion prompt (optional), e.g. camera slowly zooms in"
      class="mt-3 w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
    />

    <p v-if="error" class="mt-2 text-sm text-red-400">{{ error }}</p>

    <button
      class="mt-3 w-full rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
      :disabled="!file || uploading"
      @click="submit"
    >
      {{ uploading ? 'Uploading...' : 'Upload Panel' }}
    </button>
  </div>
</template>
