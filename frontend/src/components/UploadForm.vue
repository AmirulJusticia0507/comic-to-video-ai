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
const archive = ref(null)
const archiveInput = ref(null)
const importing = ref(false)
const success = ref('')

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

function onArchiveChange(event) {
  error.value = ''
  success.value = ''
  const selected = event.target.files?.[0] || null
  if (selected) {
    const name = selected.name.toLowerCase()
    if (!name.endsWith('.zip') && !name.endsWith('.rar')) {
      error.value = 'only ZIP and RAR archives are supported'
      archive.value = null
      return
    }
    if (selected.size > 200 * 1024 * 1024) {
      error.value = 'archive must be smaller than 200 MB'
      archive.value = null
      return
    }
  }
  archive.value = selected
}

async function importArchive() {
  if (!archive.value || importing.value) return
  importing.value = true
  error.value = ''
  success.value = ''
  try {
    const form = new FormData()
    form.append('project_id', props.projectId)
    form.append('archive', archive.value)
    const panels = await api('/panels/import-archive', { method: 'POST', body: form })
    success.value = `Imported ${panels.length} panel(s)`
    archive.value = null
    if (archiveInput.value) archiveInput.value.value = ''
    emit('uploaded', panels)
  } catch (err) {
    error.value = err.message
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <div class="surface p-5">
    <h3 class="mb-3 text-sm font-semibold text-white">Upload panel</h3>

    <div
      class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors"
      :class="dragOver ? 'border-violet-400 bg-violet-500/10' : 'border-white/15 bg-white/[0.03] hover:border-white/30'"
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
      class="field mt-3"
    />

    <p v-if="error" class="mt-2 text-sm text-red-500">{{ error }}</p>

    <button
      class="btn-primary mt-3 w-full"
      :disabled="!file || uploading"
      @click="submit"
    >
      {{ uploading ? 'Uploading...' : 'Upload Panel' }}
    </button>

    <div class="my-5 flex items-center gap-3 text-xs uppercase tracking-widest text-slate-600"><span class="h-px flex-1 bg-white/10"></span>atau<span class="h-px flex-1 bg-white/10"></span></div>

    <label class="block text-sm font-semibold text-white">Import banyak panel</label>
    <p class="mt-1 text-xs leading-5 text-slate-500">ZIP atau RAR, maks 200 MB. Maks 100 gambar, 20 MB per gambar, total 500 MB. Panel diurutkan berdasarkan nama file.</p>
    <input ref="archiveInput" type="file" accept=".zip,.rar,application/zip,application/vnd.rar" class="mt-3 block w-full text-sm text-slate-400 file:mr-3 file:rounded-lg file:border-0 file:bg-white/10 file:px-3 file:py-2 file:text-slate-200" @change="onArchiveChange" />
    <p v-if="success" class="mt-2 text-sm text-green-500">{{ success }}</p>
    <button class="btn-secondary mt-3 w-full" :disabled="!archive || importing" @click="importArchive">{{ importing ? 'Importing...' : 'Import archive' }}</button>
  </div>
</template>
