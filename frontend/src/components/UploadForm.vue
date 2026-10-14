<script setup>
import { ref } from 'vue'
import { api } from '../api/client'

const props = defineProps({
  projectId: { type: String, required: true },
  nextOrder: { type: Number, default: 0 },
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
    const presigned = await api('/uploads/presigned-url', {
      method: 'POST',
      body: { filename: file.value.name, content_type: file.value.type },
    })

    const uploadRes = await fetch(presigned.upload_url, {
      method: 'PUT',
      headers: { 'Content-Type': file.value.type },
      body: file.value,
    })
    if (!uploadRes.ok) throw new Error(`storage upload failed (${uploadRes.status})`)

    const panel = await api('/panels', {
      method: 'POST',
      body: {
        project_id: props.projectId,
        image_url: presigned.key,
        panel_order: props.nextOrder,
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
  <div class="rounded-lg border border-gray-200 bg-white p-4 shadow">
    <h3 class="mb-3 text-sm font-semibold text-gray-900">Upload Panel</h3>

    <div
      class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors"
      :class="dragOver ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'"
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
      <p v-if="!file" class="text-sm text-gray-500">
        Drag &amp; drop a comic panel here, or click to browse
      </p>
      <p v-else class="text-sm font-medium text-gray-900">{{ file.name }}</p>
      <p class="mt-1 text-xs text-gray-400">PNG, JPEG, or WebP — max 20 MB</p>
    </div>

    <input
      v-model="motionPrompt"
      type="text"
      placeholder="Motion prompt (optional), e.g. camera slowly zooms in"
      class="mt-3 w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none"
    />

    <p v-if="error" class="mt-2 text-sm text-red-500">{{ error }}</p>

    <button
      class="mt-3 w-full rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      :disabled="!file || uploading"
      @click="submit"
    >
      {{ uploading ? 'Uploading...' : 'Upload Panel' }}
    </button>
  </div>
</template>
